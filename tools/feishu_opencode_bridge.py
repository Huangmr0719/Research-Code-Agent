#!/usr/bin/env python3
"""Thin Feishu long-connection bridge to a local OpenCode server.

The bridge does not parse commands or decide user intent. It accepts Feishu
messages from whitelisted open_id values, deduplicates message_id values in
SQLite, forwards plain text to OpenCode, and sends OpenCode's answer back to
Feishu in text chunks.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional


DEFAULT_OPENCODE_URL = "http://127.0.0.1:4096"
DEFAULT_ACK = "收到，处理中。"
DEFAULT_BUSY = "当前会话已有任务处理中，请稍后再试。"
DEFAULT_UNAVAILABLE = "OpenCode 调用失败，请查看 bridge 日志。"
DEFAULT_SYSTEM_PROMPT = (
    "你是 Research-Code-Agent 远程助手。你运行在用户的科研代码服务器上。"
    "你只根据当前项目文件和用户消息工作；不要编造执行结果。"
    "所有长时间实验必须通过 tools/run_with_feishu_notify.sh 执行。"
)


@dataclass(frozen=True)
class BridgeConfig:
    app_id: str
    app_secret: str
    allowed_open_ids: set[str]
    opencode_base_url: str
    opencode_password: str
    project_dir: str
    db_path: str
    timeout_seconds: int
    chunk_chars: int
    ack_text: str
    busy_text: str
    unavailable_text: str
    system_prompt: str
    opencode_agent: str
    opencode_model_provider: str
    opencode_model_id: str


class BridgeError(RuntimeError):
    pass


def load_env_file(path: str) -> None:
    env_path = Path(path)
    if not env_path.exists():
        raise BridgeError(f"env file not found: {path}")
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise BridgeError(f"{name} must be an integer") from exc


def load_config() -> BridgeConfig:
    allowed = {
        item.strip()
        for item in os.environ.get("FEISHU_ALLOWED_OPEN_IDS", "").split(",")
        if item.strip()
    }
    config = BridgeConfig(
        app_id=os.environ.get("FEISHU_APP_ID", ""),
        app_secret=os.environ.get("FEISHU_APP_SECRET", ""),
        allowed_open_ids=allowed,
        opencode_base_url=os.environ.get("OPENCODE_BASE_URL", DEFAULT_OPENCODE_URL).rstrip("/"),
        opencode_password=os.environ.get("OPENCODE_SERVER_PASSWORD", ""),
        project_dir=os.environ.get("RCA_PROJECT_DIR", os.getcwd()),
        db_path=os.environ.get("RCA_BRIDGE_DB", "logs/feishu_opencode_bridge.sqlite3"),
        timeout_seconds=env_int("RCA_BRIDGE_TIMEOUT_SECONDS", 600),
        chunk_chars=env_int("RCA_BRIDGE_CHUNK_CHARS", 2500),
        ack_text=os.environ.get("RCA_BRIDGE_ACK_TEXT", DEFAULT_ACK),
        busy_text=os.environ.get("RCA_BRIDGE_BUSY_TEXT", DEFAULT_BUSY),
        unavailable_text=os.environ.get("RCA_BRIDGE_UNAVAILABLE_TEXT", DEFAULT_UNAVAILABLE),
        system_prompt=os.environ.get("RCA_BRIDGE_SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT),
        opencode_agent=os.environ.get("OPENCODE_AGENT", ""),
        opencode_model_provider=os.environ.get("OPENCODE_MODEL_PROVIDER", ""),
        opencode_model_id=os.environ.get("OPENCODE_MODEL_ID", ""),
    )
    missing = []
    if not config.app_id:
        missing.append("FEISHU_APP_ID")
    if not config.app_secret:
        missing.append("FEISHU_APP_SECRET")
    if not config.allowed_open_ids:
        missing.append("FEISHU_ALLOWED_OPEN_IDS")
    if not config.opencode_base_url.startswith("http://127.0.0.1:"):
        missing.append("OPENCODE_BASE_URL must use http://127.0.0.1:<port>")
    if missing:
        raise BridgeError("missing or invalid config: " + ", ".join(missing))
    return config


class MessageStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_messages (
                    message_id TEXT PRIMARY KEY,
                    chat_id TEXT NOT NULL,
                    open_id TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                )
                """
            )

    def claim_message(self, message_id: str, chat_id: str, open_id: str) -> bool:
        with self._lock, self._connect() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO processed_messages(message_id, chat_id, open_id, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (message_id, chat_id, open_id, int(time.time())),
                )
                return True
            except sqlite3.IntegrityError:
                return False


class OpenCodeClient:
    def __init__(self, config: BridgeConfig):
        self.config = config

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.opencode_password:
            headers["Authorization"] = f"Bearer {self.config.opencode_password}"
            headers["X-OpenCode-Server-Password"] = self.config.opencode_password
        return headers

    def _request(self, method: str, path: str, payload: Optional[dict[str, Any]] = None) -> Any:
        url = self.config.opencode_base_url + path
        data = None
        headers = self._headers()
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as resp:
                body = resp.read()
                if not body:
                    return None
                return json.loads(body.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", "replace")
            raise BridgeError(f"OpenCode HTTP {exc.code}: {details}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise BridgeError(f"OpenCode request failed: {exc}") from exc

    def validate_doc(self) -> None:
        doc = self._request("GET", "/doc")
        paths = doc.get("paths", {}) if isinstance(doc, dict) else {}
        required = [
            "/api/session",
            "/api/session/{sessionID}/prompt",
            "/api/session/{sessionID}/wait",
            "/api/session/{sessionID}/message",
        ]
        missing = [path for path in required if path not in paths]
        if missing:
            raise BridgeError("OpenCode /doc missing required paths: " + ", ".join(missing))

    def run(self, user_text: str, feishu_context: dict[str, str]) -> str:
        session = self._create_session(feishu_context)
        session_id = session["id"]
        prompt = self._build_prompt(user_text, feishu_context)
        self._send_prompt(session_id, prompt)
        self._wait(session_id)
        return self._collect_output(session_id)

    def _create_session(self, feishu_context: dict[str, str]) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "location": {"directory": self.config.project_dir},
            "agent": self.config.opencode_agent or None,
            "model": (
                {
                    "providerID": self.config.opencode_model_provider,
                    "id": self.config.opencode_model_id,
                }
                if self.config.opencode_model_provider and self.config.opencode_model_id
                else None
            ),
        }
        payload = {key: value for key, value in payload.items() if value is not None}
        data = self._request("POST", "/api/session", payload)
        try:
            return data["data"]
        except (TypeError, KeyError) as exc:
            raise BridgeError(f"unexpected OpenCode session response: {data!r}") from exc

    def _build_prompt(self, user_text: str, feishu_context: dict[str, str]) -> str:
        context = "\n".join(
            [
                "Feishu remote request:",
                f"- open_id: {feishu_context.get('open_id', 'unknown')}",
                f"- chat_id: {feishu_context.get('chat_id', 'unknown')}",
                f"- message_id: {feishu_context.get('message_id', 'unknown')}",
                "",
                "User message:",
                user_text,
            ]
        )
        return context

    def _send_prompt(self, session_id: str, prompt: str) -> None:
        payload: dict[str, Any] = {
            "prompt": {"text": prompt},
            "delivery": "queue",
            "resume": True,
        }
        if self.config.system_prompt:
            # The v2 prompt API does not expose a system field; prepend a clear
            # behavior note. Security must still come from opencode.json and OS permissions.
            payload["prompt"]["text"] = self.config.system_prompt + "\n\n" + prompt
        self._request("POST", f"/api/session/{session_id}/prompt", payload)

    def _wait(self, session_id: str) -> None:
        self._request("POST", f"/api/session/{session_id}/wait")

    def _collect_output(self, session_id: str) -> str:
        data = self._request("GET", f"/api/session/{session_id}/message?order=asc&limit=50")
        messages = data.get("data", []) if isinstance(data, dict) else []
        texts: list[str] = []
        for item in messages:
            message = item.get("info", item) if isinstance(item, dict) else {}
            parts = item.get("parts", []) if isinstance(item, dict) else []
            if message.get("role") != "assistant":
                continue
            for part in parts:
                if isinstance(part, dict) and part.get("type") == "text" and part.get("text"):
                    texts.append(part["text"])
        output = "\n\n".join(texts).strip()
        return output or "OpenCode 已完成，但未返回文本输出。"


class ChatLockRegistry:
    def __init__(self) -> None:
        self._global = threading.Lock()
        self._locks: dict[str, threading.Lock] = {}

    def acquire(self, chat_id: str) -> Optional[threading.Lock]:
        with self._global:
            lock = self._locks.setdefault(chat_id, threading.Lock())
        if not lock.acquire(blocking=False):
            return None
        return lock


def chunk_text(text: str, chunk_chars: int) -> list[str]:
    text = text.strip() or "(empty)"
    if chunk_chars <= 0:
        chunk_chars = 2500
    chunks: list[str] = []
    current = ""
    for line in text.splitlines():
        candidate = line if not current else current + "\n" + line
        if len(candidate) <= chunk_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        while len(line) > chunk_chars:
            chunks.append(line[:chunk_chars])
            line = line[chunk_chars:]
        current = line
    if current:
        chunks.append(current)
    return chunks or ["(empty)"]


def parse_feishu_text(content: str) -> str:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return content.strip()
    if isinstance(parsed, dict):
        return str(parsed.get("text", "")).strip()
    return str(parsed).strip()


class BridgeApp:
    def __init__(self, config: BridgeConfig, sender: Callable[[str, str], None]):
        self.config = config
        self.sender = sender
        self.store = MessageStore(config.db_path)
        self.chat_locks = ChatLockRegistry()
        self.opencode = OpenCodeClient(config)

    def handle_message(self, event: Any) -> None:
        message = event.event.message
        sender_id = event.event.sender.sender_id
        open_id = getattr(sender_id, "open_id", "") or ""
        chat_id = message.chat_id
        message_id = message.message_id

        if open_id not in self.config.allowed_open_ids:
            print(f"ignored message from non-whitelisted open_id={open_id}", file=sys.stderr)
            return
        if message.message_type != "text":
            self._safe_send(message_id, "当前原型只支持文本消息。")
            return
        if not self.store.claim_message(message_id, chat_id, open_id):
            print(f"deduplicated message_id={message_id}", file=sys.stderr)
            return

        lock = self.chat_locks.acquire(chat_id)
        if lock is None:
            self._safe_send(message_id, self.config.busy_text)
            return

        if not self._safe_send(message_id, self.config.ack_text):
            lock.release()
            return
        thread = threading.Thread(
            target=self._process_message,
            args=(lock, message_id, chat_id, open_id, parse_feishu_text(message.content)),
            daemon=True,
        )
        thread.start()

    def _safe_send(self, message_id: str, text: str) -> bool:
        try:
            self.sender(message_id, text)
            return True
        except Exception as exc:  # noqa: BLE001 - Feishu delivery failure should not crash callbacks.
            print(f"Feishu reply failed for message_id={message_id}: {exc}", file=sys.stderr)
            return False

    def _process_message(
        self,
        lock: threading.Lock,
        message_id: str,
        chat_id: str,
        open_id: str,
        text: str,
    ) -> None:
        try:
            result = self.opencode.run(
                text,
                {"message_id": message_id, "chat_id": chat_id, "open_id": open_id},
            )
            for index, chunk in enumerate(chunk_text(result, self.config.chunk_chars), start=1):
                prefix = f"[{index}] " if index > 1 else ""
                self._safe_send(message_id, prefix + chunk)
        except Exception as exc:  # noqa: BLE001 - bridge must report failures to Feishu.
            print("bridge processing failed:", exc, file=sys.stderr)
            traceback.print_exc()
            self._safe_send(message_id, self.config.unavailable_text)
        finally:
            lock.release()


def make_feishu_sender(client: Any) -> Callable[[str, str], None]:
    from lark_oapi.api.im.v1 import ReplyMessageRequest, ReplyMessageRequestBody

    def send(message_id: str, text: str) -> None:
        body = ReplyMessageRequestBody.builder().msg_type("text").content(
            json.dumps({"text": text}, ensure_ascii=False)
        ).build()
        request = ReplyMessageRequest.builder().message_id(message_id).request_body(body).build()
        response = client.im.v1.message.reply(request)
        if not response.success():
            raise BridgeError(f"Feishu reply failed: {response.code} {response.msg}")

    return send


def start_feishu_bridge(config: BridgeConfig) -> None:
    try:
        import lark_oapi as lark
        from lark_oapi.api.im.v1 import P2ImMessageReceiveV1
    except ImportError as exc:
        raise BridgeError("missing dependency: install lark-oapi for Feishu long connection") from exc

    client = lark.Client.builder().app_id(config.app_id).app_secret(config.app_secret).build()
    app = BridgeApp(config, make_feishu_sender(client))
    app.opencode.validate_doc()

    def on_message(data: Any) -> None:
        app.handle_message(data)

    builder = lark.EventDispatcherHandler.builder("", "")
    register = builder.register_p2_im_message_receive_v1
    try:
        builder = register(on_message)
    except TypeError:
        builder = register(P2ImMessageReceiveV1, on_message)
    event_handler = builder.build()
    ws_client = lark.ws.Client(
        config.app_id,
        config.app_secret,
        event_handler=event_handler,
        log_level=lark.LogLevel.INFO,
    )
    ws_client.start()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Feishu long-connection bridge to local OpenCode")
    parser.add_argument("--env-file", help="load environment variables from a file")
    parser.add_argument("--check", action="store_true", help="validate config, sqlite, and OpenCode /doc")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        if args.env_file:
            load_env_file(args.env_file)
        config = load_config()
        if args.check:
            MessageStore(config.db_path)
            OpenCodeClient(config).validate_doc()
            print("bridge configuration check passed")
            return 0
        start_feishu_bridge(config)
        return 0
    except BridgeError as exc:
        print(f"feishu_opencode_bridge: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
