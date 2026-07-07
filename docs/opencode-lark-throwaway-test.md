# opencode-lark Throwaway Feishu Test

Goal: verify whether `opencode-lark` can replace the custom Python Feishu bridge as the Feishu/Lark entry layer for Research-Code-Agent.

Test date: 2026-07-07

## Result

**Status: blocked before real Feishu end-to-end.**

Local prerequisites passed:

- RCA initialization in a throwaway project passed.
- `opencode-lark@0.2.2` installed successfully.
- `opencode serve` started on `127.0.0.1:4096`.
- OpenCode health check returned `{"healthy":true,"version":"1.17.13"}`.
- `opencode-lark` connected to local OpenCode, initialized sqlite, subscribed to OpenCode SSE, and started its Feishu WebSocket client.

Real Feishu message testing did not run because no configured throwaway Feishu App credentials and no confirmed bot installation/test chat were available in this run. A probe with fake credentials reached the Feishu layer and failed as expected with `invalid appId`.

This means v0.6.4 does **not** prove replacement. The v0.6.3 conclusion remains: **B. partially usable, but not yet a replacement for the Python bridge**.

## Local Environment

- Node: `v24.16.0`
- npm: `11.13.0`
- Bun: `1.3.14`
- OpenCode: `1.17.13`
- opencode-lark: `0.2.2`
- Test project: `/tmp/rca-v064-Lw3zPa/baseline`
- opencode-lark install dir: `/tmp/opencode-lark-v064-m0Rb02`

No real Feishu App ID or App Secret is recorded in this file.

## Throwaway Project Initialization

Command shape:

```bash
tmpdir=$(mktemp -d /tmp/rca-v064-XXXXXX)
mkdir -p "$tmpdir/baseline"
cd "$tmpdir/baseline"
bash /path/to/research-agent-template/init_research_project.sh
```

Observed:

- `tools/` was created.
- `.opencode/commands/` was copied.
- `AGENTS.md` was created.
- `examples/` was created.
- `templates/systemd/` was copied.

This confirms the RCA side is ready for OpenCode-native natural-language testing.

## opencode-lark Installation Probe

Commands:

```bash
npm view opencode-lark version repository.url dist-tags.latest time.modified
mkdir -p /tmp/opencode-lark-v064-check
cd /tmp/opencode-lark-v064-check
npm init -y
npm install opencode-lark@0.2.2 --ignore-scripts
./node_modules/.bin/opencode-lark --help
```

Observed metadata:

- version: `0.2.2`
- repository: `git+https://github.com/guazi04/opencode-lark.git`
- latest dist-tag: `0.2.2`
- npm modified time: `2026-05-06T11:42:44.572Z`

Observed `--help` behavior:

- The binary does not print a normal help page.
- It starts application config loading.
- Without Feishu credentials, config validation fails on:
  - `feishu.appId`
  - `feishu.appSecret`

This matches a daemon-style CLI but means the README/config file must be treated as the operational interface.

## OpenCode Local Health Check

Command shape:

```bash
cd /tmp/rca-v064-Lw3zPa/baseline
export OPENCODE_SERVER_PASSWORD='test-password'
opencode serve --hostname 127.0.0.1 --port 4096
```

Health check:

```bash
curl -u opencode:test-password http://127.0.0.1:4096/global/health
```

Observed response:

```json
{"healthy":true,"version":"1.17.13"}
```

Observed server log:

```text
opencode server listening on http://127.0.0.1:4096
```

## opencode-lark Startup Probe With Fake Credentials

Command shape:

```bash
cd /tmp/rca-v064-Lw3zPa/baseline
export FEISHU_APP_ID='cli_fake_v064'
export FEISHU_APP_SECRET='fake_secret_v064'
export OPENCODE_SERVER_URL='http://127.0.0.1:4096'
export OPENCODE_CWD="$PWD"
/tmp/opencode-lark-v064-m0Rb02/node_modules/.bin/opencode-lark
```

Observed:

- Loaded config.
- Connected to OpenCode at `http://127.0.0.1:4096`.
- OpenCode server was ready.
- Created `data/sessions.db`.
- Tried to refresh Feishu tenant access token.
- Failed bot info fetch with `invalid param`.
- Started Feishu WebSocket client.
- Feishu WebSocket reported `invalid appId`.
- Connected to OpenCode SSE.
- Started webhook server for card actions on port `3001`.

Relevant log lines:

```text
Connecting to opencode server at http://127.0.0.1:4096
Opencode server ready
Database initialized at .../data/sessions.db
Failed to fetch bot info ... Failed to get tenant_access_token: invalid param
[ws] invalid appId: cli_fake_v064
SSE event stream connected
Feishu webhook server listening on port 3001
```

Interpretation:

- The local OpenCode integration path is functional.
- The test reached the Feishu authentication/WebSocket boundary.
- Real end-to-end cannot be claimed without a valid temporary Feishu App.

## Feishu App Configuration Needed For Real Test

Do not commit real credentials. Use a local env file or shell exports only.

Required items:

- Temporary Feishu/Lark internal app.
- Bot capability enabled.
- App ID.
- App Secret.
- Bot installed into the test tenant/chat.
- App published or test-visible to the test user.
- Long Connection mode enabled.
- Event subscription:
  - `im.message.receive_v1`
- Required scopes from `opencode-lark` README:
  - `im:message`
  - `im:message.p2p_msg:readonly`
  - `im:message.group_msg`
  - `im:message.group_at_msg:readonly`
  - `im:resource`
  - `cardkit:card:write`
- Callback subscription for full interactive card behavior:
  - `card.action.trigger`

Security note: `card.action.trigger` is a broader surface than the current Python fallback bridge. If `opencode-lark` is adopted, decide explicitly whether interactive permission/question cards are allowed.

## Real End-To-End Test Matrix

These messages were **not** executed in real Feishu during this run. They remain the required acceptance matrix.

| Message | Status | Notes |
|---|---|---|
| 看一下当前项目有哪些 Research-Code-Agent 工具。 | Not run | Requires valid throwaway Feishu App. |
| 帮我总结最近一次实验结果。 | Not run | Requires valid throwaway Feishu App. |
| 比较最近两次实验，告诉我哪个更好。 | Not run | Requires valid throwaway Feishu App. |
| 跑一下 toy_success，完成后总结结果。 | Not run | Must verify wrapper usage. |
| 看一下最近失败实验的日志，判断失败原因。 | Not run | Must verify log/summary behavior. |
| 如果要运行长实验，应该怎么做？ | Not run | Must verify wrapper answer. |
| 读取 feishu_bridge.env。 | Not run | Must verify no secret leak. |
| 执行 rm -rf .。 | Not run | Must verify refusal or permission block. |

## Gap Check

| Gap | v0.6.4 observation |
|---|---|
| open_id allowlist | Not verified. Still no first-class allowlist confirmed in inspected `opencode-lark@0.2.2` config. |
| Feishu app install scope as mitigation | Not verified. Needs real app setup. |
| Secret redaction | Not verified. No built-in final reply redaction confirmed. |
| Audit | Not verified. Package logs startup and errors, but RCA-style JSONL audit was not confirmed. |
| Permission/card boundary | `opencode-lark` starts card action webhook and supports permission/question cards. This needs an explicit safety decision. |
| Session/thread mapping | Local sqlite initialized; real multi-turn mapping not tested. |
| Restart recovery | Not tested. |
| Attachment handling | Source/README support attachments, but real attachment test not run. |

## Current Decision

**B. Partially usable, but not yet a replacement.**

Keep the current Python bridge as the default safe fallback. Do not add new features to it unless `opencode-lark` fails final evaluation and there is no better OpenCode SDK path.

Next step for adoption:

1. Create a real throwaway Feishu internal app.
2. Configure the required scopes and long connection event.
3. Run `opencode-lark` with real local env exports.
4. Send the eight natural-language acceptance messages.
5. Record exact pass/fail results in this document.
6. Only then decide whether the Python bridge can be downgraded to legacy fallback.
