# OpenCode Lark/Feishu Integration Evaluation

Goal: decide whether an existing Feishu/Lark to OpenCode integration can replace further Python bridge expansion.

## Current Finding

As of this repo update, public search and local package probing did not confirm a maintained, ready-to-adopt `opencode-lark` package. The network-limited local `npm view opencode-lark` probe did not complete, so this is not a definitive absence claim.

Recommendation: **needs small-scale verification** before more bridge work. Search npm/GitHub again from the deployment server, then test any candidate in a throwaway Feishu app.

## Minimal Verification Commands

Run these from the deployment server or a network-enabled development machine:

```bash
npm view opencode-lark
npm search opencode lark feishu
npm search opencode feishu
```

If GitHub CLI is available:

```bash
gh search repos opencode-lark
gh search repos "opencode feishu"
gh search repos "opencode lark"
```

For any candidate package, verify in a throwaway directory:

```bash
mkdir -p /tmp/opencode-lark-check
cd /tmp/opencode-lark-check
npm init -y
npm install <candidate-package>
```

Record:

- package version and repository URL;
- runtime requirement, such as Node or Bun;
- whether it uses Feishu WebSocket, not webhook;
- whether it can send a normal Feishu text/card reply;
- how it maps Feishu chat/thread to OpenCode sessions;
- how it handles OpenCode permissions and approval prompts;
- whether it can work with `opencode serve` bound to `127.0.0.1`.

Do not migrate production traffic until these checks pass.

## Evaluation Checklist

1. **Package exists**: not confirmed.
2. **Install method**: not confirmed; likely npm/Bun/Node if community JS package exists.
3. **Feishu/Lark WebSocket support**: required; not confirmed.
4. **Feishu message to OpenCode**: required; not confirmed.
5. **OpenCode reply to Feishu**: required; not confirmed.
6. **Feishu card support**: useful; not mandatory if markdown works.
7. **Realtime update support**: optional; not needed for current RCA.
8. **Session/thread mapping**: required for practical use.
9. **Attachment support**: optional for current RCA.
10. **Bun/Node dependency**: acceptable only if it reduces bridge code enough.
11. **Permission confirmation support**: useful, but first version can require local handling.
12. **Maintenance status**: must be checked before adoption.
13. **Self-written code reduction**: would ideally replace Feishu Channel SDK wiring, retry/fallback code, and OpenCode HTTP client.
14. **Risks**: unstable package, incompatible OpenCode API, weak Feishu support, unclear security defaults, extra Node/Bun runtime, hard-to-debug production service.
15. **Conclusion**: not ready to adopt blindly; evaluate before adding more Python bridge features.

## If A Candidate Works

- Stop expanding `tools/feishu_opencode_bridge.py`.
- Keep the Python bridge as legacy fallback.
- Move workflow behavior into `AGENTS.md`, `.opencode/commands/`, `opencode.json`, and RCA tools.
- Keep Feishu user input natural language.

## If No Candidate Works

Keep the Python bridge stable and minimal. Do not add command routing. Consider OpenCode SDK only as a way to replace handwritten HTTP calls.

Search references:
- OpenCode docs: https://opencode.ai/docs/
- npm package search: https://www.npmjs.com/
- GitHub search: https://github.com/search
