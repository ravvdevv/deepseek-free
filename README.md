# deepseek-free

<p align="center">
  <strong>Local OpenAI-compatible API proxy for DeepSeek Web Chat</strong>
</p>

<p align="center">
  <strong>Free DeepSeek API</strong> — run DeepSeek Web Chat like an API. No key, no signup, no cost.
</p>

<p align="center">
  <a href="https://github.com/ravvdevv/deepseek-free/blob/main/LICENSE"><img alt="License MIT" src="https://img.shields.io/badge/license-MIT-green.svg" /></a>
  <img alt="Node.js 18 plus" src="https://img.shields.io/badge/node-18%2B-339933.svg" />
  <img alt="No npm dependencies" src="https://img.shields.io/badge/dependencies-0-blue.svg" />
  <img alt="OpenAI compatible" src="https://img.shields.io/badge/OpenAI-compatible-111111.svg" />
</p>

<p align="center">
  <a href="#-quick-start">Quick start</a> •
  <a href="#-features">Features</a> •
  <a href="#-request-examples">Examples</a> •
  <a href="#-models">Models</a> •
  <a href="#-endpoints">Endpoints</a> •
  <a href="#-open-webui">Open WebUI</a>
</p>

## What is this?

DeepSeek Web Chat is free. But it lives in a browser tab — you can't point your code at it.

**deepseek-free turns that tab into an API.** Log in once, and any tool on your machine can send requests to DeepSeek at `http://localhost:9655`.

```text
your app  ──▶  deepseek-free  ──▶  DeepSeek Web Chat
             (localhost:9655)
```

## Why use it

| You want to | Do this |
| --- | --- |
| DeepSeek in an AI chat app | Point Open WebUI, LibreChat, or any chat UI at `http://localhost:9655/v1` |
| DeepSeek as a coding agent | Set `ANTHROPIC_BASE_URL=http://127.0.0.1:9655` and run Claude Code |
| DeepSeek in your own scripts | `npm start`, then `curl` the OpenAI endpoint |
| Free API in CI or on a VPS | Deploy headless — no browser on screen needed |

## How it works

It runs through your ordinary, already-logged-in DeepSeek account in a dedicated Chrome profile. The local server takes API requests and talks to DeepSeek Web itself through that saved browser session. **No DeepSeek API key. No npm dependencies.**

What you get: OpenAI Chat Completions, an Anthropic Messages shim, an OpenAI Responses shim, SSE streaming, reasoning output, tool calling, vision, one isolated session per agent, and automatic recovery from stale sessions.

> ⚠️ This is an experimental web-chat proxy. DeepSeek can change its internal web API without notice. For production use, the official paid DeepSeek API is the safer bet.

---

## Table of contents

- [What is this?](#what-is-this)
- [Why use it](#why-use-it)
- [How it works](#how-it-works)
- [What you get](#-what-you-get)
- [Features](#-features)
- [Quick start](#-quick-start)
- [Windows](#-windows)
- [Linux / Chromium](#-linux--chromium)
- [VPS / headless](#-vps--headless)
- [Persistent service on VPS (systemd)](#-persistent-service-on-vps-systemd)
- [Rootless Podman](#-rootless-podman)
- [Diagnostics / doctor](#-diagnostics--doctor)
- [Session reuse and chat resets](#-session-reuse-and-chat-resets)
- [Multi-account pool](#-multi-account-pool)
- [Console auth ideas](#-console-auth-ideas)
- [Verify it works](#-verify-it-works)
- [chatbot.py (quick test client)](#-chatbotpy-quick-test-client)
- [Request examples](#-request-examples)
  - [Chat Completions](#chat-completions)
  - [Reasoning](#reasoning)
  - [Web search](#web-search)
  - [Streaming](#streaming)
  - [Anthropic Messages API](#anthropic-messages-api)
  - [OpenAI Responses API](#openai-responses-api)
  - [Tool calling](#tool-calling)
- [Models](#-models)
- [Endpoints](#-endpoints)
- [Open WebUI](#-open-webui)
- [Refresh the login](#-refresh-the-login)
- [Tests](#-tests)
- [Project status](#-project-status)

---

## ✨ What you get

- Use DeepSeek Web as a local API endpoint.
- Plug DeepSeek into Open WebUI and other OpenAI-compatible clients.
- Get plain JSON responses or streaming SSE.
- Use reasoning models with a separate `reasoning_content` field.
- Work with an Anthropic Messages API shim for Claude Code / the Anthropic SDK.
- Use the OpenAI Responses API shim for newer OpenAI/Codex-style clients.
- Keep separate web sessions for different agents/users.

## 🚀 Features

- **OpenAI-compatible API:** `POST /v1/chat/completions`
- **Anthropic-compatible shim:** `POST /v1/messages`
- **OpenAI Responses shim:** `POST /v1/responses`
- **Streaming:** SSE chunks as well as ordinary non-stream JSON responses
- **Reasoning output:** separate `reasoning_content` for thinking models
- **Tool calling:** parses OpenAI tools, Anthropic tools, and Responses function tools
- **Model capabilities:** `GET /v1/model-capabilities` with alias → real web mode
- **Agent sessions:** one DeepSeek session per `user` / agent id
- **Session recovery:** automatic reset of stale chains/sessions
- **Zero dependencies:** Node.js 18+ for the proxy (Node.js 22+ for `npm run auth`), no npm dependencies

---

## ⚡ Quick start

```bash
git clone https://github.com/ravvdevv/deepseek-free.git
cd deepseek-free
npm run auth
npm start
```

`npm run auth` opens the auth menu:

1. pick option `1`;
2. log into DeepSeek in the dedicated Chrome profile;
3. send a short message like `ok`;
4. go back to the terminal and press Enter.

> `npm run auth` uses the WebSocket built into Node.js, so it needs
> Node.js 22+. The proxy itself runs on Node.js 18+; on an older Node, import a
> ready-made `deepseek-auth.json` with `npm run auth:import`.

`npm start` shows the launch menu:

- `1` — authenticate / refresh the DeepSeek login
- `2` — import an auth file / cookies
- `3` — show models and statuses
- `4` — start the proxy (default, Enter)
- `5` — exit

Settings can go into `.env` (template: `.env.example`); `npm start`,
`npm run auth`, and `npm run doctor` all read it themselves. Real environment
variables take precedence over `.env` values.

For headless/CI runs with no menu:

```bash
NON_INTERACTIVE=1 npm start
# or
SKIP_ACCOUNT_MENU=1 npm start
```

By default the server listens on:

```text
http://localhost:9655
```

By default the proxy is reachable only from this machine. To reach it over the
network, set an explicit bind address and a separate proxy key:

```bash
HOST=0.0.0.0 PROXY_API_KEY='replace-with-a-long-random-value' npm start
```

After that, pass the key as `Authorization: Bearer <key>` or
`x-api-key: <key>` (that is how the Anthropic SDK sends it). Without
`PROXY_API_KEY`, non-health endpoints stay unauthenticated, so do not
expose such an instance to the network.

Browser requests are allowed from loopback origins. If your UI runs on a
different address, add its exact origin as a comma-separated list, for example
`PROXY_CORS_ORIGINS=https://ui.example.com,http://192.168.1.20:3000`.

---

## 🪟 Windows

```powershell
git clone https://github.com/ravvdevv/deepseek-free.git
cd deepseek-free
npm run auth
npm start
```

If Chrome is installed somewhere non-standard, point at it explicitly:

```powershell
$env:CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
npm run auth
```

If Chrome cannot be found, `npm run auth` now prints ready-made instructions for Windows/macOS/Linux instead of a cryptic stack trace.

---

## 🐧 Linux / Chromium

```bash
git clone https://github.com/ravvdevv/deepseek-free.git
cd deepseek-free
CHROME_PATH=$(which chromium) npm run auth
npm start
```

If your Chromium binary has a different name:

```bash
CHROME_PATH=$(which chromium-browser) npm run auth
# or
CHROME_PATH=$(which google-chrome) npm run auth
```

---

## 🖥 VPS / headless

The most reliable flow with no Chrome on the server:

1. On your home PC, where you have a GUI/Chrome:

```bash
npm run auth
```

2. Copy `deepseek-auth.json` to the VPS:

```bash
scp deepseek-auth.json user@your-vps:/opt/deepseek-free/deepseek-auth.json
```

3. On the VPS, import/verify the file and set safe permissions:

```bash
cd /opt/deepseek-free
npm run auth:import -- --input ./deepseek-auth.json
npm run doctor -- --offline
```

4. Run the proxy without the interactive menu:

```bash
NON_INTERACTIVE=1 npm start
```

You can import not only a ready-made `deepseek-auth.json` but also a browser
cookie export:

```bash
DEEPSEEK_TOKEN="<token>" npm run auth:import -- --input ./cookies.json
```

> Important: `deepseek-auth.json` is access to your DeepSeek Web login. Do not commit it, do not publish it, and keep it with `0600` permissions.

---

## 🛠 Persistent service on VPS (systemd)

The container-free option: the proxy runs as a system service under a dedicated
user, restarts on failure, and starts with the server. Requires Node.js 18+
(`node` in `/usr/bin` or `/usr/local/bin`).

```bash
# 1. User and code
sudo useradd --system --home /opt/deepseek-free --shell /usr/sbin/nologin deepseek-free
sudo git clone https://github.com/ravvdevv/deepseek-free /opt/deepseek-free

# 2. Secrets: the auth file from `npm run auth` on your home PC plus a key for clients
sudo install -d -m 0750 -o root -g deepseek-free /etc/deepseek-free
sudo install -m 0600 -o deepseek-free -g deepseek-free ./deepseek-auth.json /etc/deepseek-free/deepseek-auth.json
openssl rand -hex 32 | sudo install -m 0600 -o deepseek-free -g deepseek-free /dev/stdin /etc/deepseek-free/proxy-api-key

# 3. Service
sudo cp /opt/deepseek-free/deploy/deepseek-free.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now deepseek-free

# 4. Verify
curl -fsS http://127.0.0.1:9655/readyz
sudo -u deepseek-free env DEEPSEEK_AUTH_PATH=/etc/deepseek-free/deepseek-auth.json node /opt/deepseek-free/scripts/doctor.js
journalctl -u deepseek-free -f
```

- The service listens only on `127.0.0.1:9655` and requires the key
  (`Authorization: Bearer <key>` or `x-api-key`). The key lives in
  `/etc/deepseek-free/proxy-api-key`.
- External access goes through an HTTPS reverse proxy (nginx/Caddy) or an SSH
  tunnel. If you need to bind the network directly, set `HOST=0.0.0.0` in
  `/etc/deepseek-free/env` (any `DEEPSEEK_*` settings go there too).
- Update: `cd /opt/deepseek-free && sudo git pull && sudo systemctl restart deepseek-free`.
- New DeepSeek login: install the file with the same command so owner and
  permissions are preserved, then restart the service:
  `sudo install -m 0600 -o deepseek-free -g deepseek-free ./deepseek-auth.json /etc/deepseek-free/deepseek-auth.json && sudo systemctl restart deepseek-free`.

---

## 🦭 Rootless Podman

The container is meant only for non-interactive proxy runs. Do the browser
authorization on the host with `npm run auth`: the auth scripts and
`deepseek-auth.json` are not copied into the image.

Run Podman as your regular user, without `sudo`.

1. Build the local image:

```bash
podman build --format docker --tag localhost/deepseek-free:local --file Containerfile .
```

2. Pass the DeepSeek auth and a separate proxy key through Podman secrets:

```bash
podman secret create --replace deepseek-auth ./deepseek-auth.json

printf 'Proxy API key: '
IFS= read -r -s PROXY_API_KEY
printf '\n'
printf '%s' "$PROXY_API_KEY" |
  podman secret create --replace deepseek-proxy-key -
```

Use a long random key. The value stays in the current shell's `PROXY_API_KEY`
variable so you can test the API; it never lands in the image or on Podman's
command line.

3. Run the container with minimal privileges:

```bash
podman run --detach \
  --name deepseek-free \
  --publish 127.0.0.1:9655:9655 \
  --secret deepseek-auth,target=deepseek-auth.json,uid=1000,gid=1000,mode=0400 \
  --secret deepseek-proxy-key,target=proxy-api-key,uid=1000,gid=1000,mode=0400 \
  --read-only \
  --cap-drop=ALL \
  --security-opt=no-new-privileges \
  localhost/deepseek-free:local
```

`NON_INTERACTIVE=1`, `HOST=0.0.0.0`, and the paths to both secrets are
pre-set inside the container. `REQUIRE_PROXY_API_KEY=1` stops the container from
starting if the key secret is missing or empty. On the host the port is
published only on `127.0.0.1`; do not drop that address without a separate
network firewall/access policy in place.

4. Check liveness, account readiness, and the protected endpoint:

```bash
podman healthcheck run deepseek-free
curl --fail http://127.0.0.1:9655/readyz
curl --fail \
  -H "Authorization: Bearer $PROXY_API_KEY" \
  http://127.0.0.1:9655/v1/models
```

The built-in healthcheck hits the local `/health` (is the process alive).
`--format docker` at build time is mandatory: in OCI format (Podman's default)
the `HEALTHCHECK` instruction is silently dropped.
`/readyz` additionally returns `503` if no DeepSeek auth account is currently
ready to serve requests. Container diagnostics:

```bash
podman logs deepseek-free
podman inspect --format '{{.State.Health.Status}}' deepseek-free
```

Stop and remove the container along with the stored Podman secrets:

```bash
podman stop deepseek-free
podman rm deepseek-free
podman secret rm deepseek-auth deepseek-proxy-key
unset PROXY_API_KEY
```

When rotating the auth file or the proxy key, replace the matching secret and
recreate the container so behaviour does not depend on the Podman version.

---

## 🩺 Diagnostics / doctor

```bash
npm run doctor
# without any network calls to DeepSeek:
npm run doctor -- --offline
```

`doctor` checks:

- whether `deepseek-auth.json` / `DEEPSEEK_AUTH_DIR` was found;
- whether the JSON is valid;
- whether `token`, `cookie`, and `wasmUrl` are present;
- whether file permissions are safe on macOS/Linux (`0600`);
- on a normal run, whether the DeepSeek PoW endpoint is reachable.

If you see `data.biz_data is null`, `fetch failed`, `401/403/429`, or Hermes/OpenCode does not list any models, run `npm run doctor` first.

---

## ♻️ Session reuse and chat resets

deepseek-free does not create a new DeepSeek chat for every HTTP request for
no reason. The logic is:

- one `x-agent-session`, `session`, or `user` → one DeepSeek chat session;
- if the session id already exists, the proxy reuses it and continues the chain via `parent_message_id`;
- agents (Hermes, Cline, Claude Code, OpenCode…) resend the whole history on every request. The proxy remembers which messages are already in the DeepSeek chat and sends **only the new ones** (tool results, the new question) plus a short reminder about the tool-call format. Previously the entire conversation (up to 80,000 characters) was resent at every step, chat context grew quadratically, and after a dozen steps DeepSeek started answering with empty content, saying "Content is too long", or stopped calling tools entirely (#23, #30);
- if the client changed the history (compressed/edited it), changed the system prompt, or changed the tool set, a new DeepSeek chat is opened with the full prompt;
- an auto-reset happens on TTL, a DeepSeek session error, an over-long message chain, or once the chat has accumulated more than `DEEPSEEK_MAX_SESSION_CHARS` characters (default 3 × `DEEPSEEK_MAX_PROMPT_CHARS`);
- concurrent requests from one agent (for example, background reviews in Hermes) are not mixed into the same chat: the second request is served in a separate temporary DeepSeek chat;
- local history is kept as a short context so a new DeepSeek session can continue the conversation.
- long agent requests are trimmed to `DEEPSEEK_MAX_PROMPT_CHARS` (default 80,000 characters) before being sent: the start of the task, fresh tool results, and the tool adapter are preserved;
- if the client already sent multi-turn history, the local recovery history is not added a second time;
- an empty answer is retried at most `DEEPSEEK_MAX_RETRIES` times (default 2), and the context shrinks on every retry.
- long generations (thinking) are not cut off by a timeout: the stream is bounded by an idle-without-data pause (`DEEPSEEK_STREAM_IDLE_TIMEOUT_MS`, default 60 s) and an overall `DEEPSEEK_STREAM_MAX_MS` limit (10 minutes).

Set an agent/session explicitly:

```bash
curl -X POST http://localhost:9655/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "x-agent-session: my-agent" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"Hello"}]}'
```

List active sessions:

```bash
curl http://localhost:9655/v1/sessions
```

Reset a single session:

```bash
curl -X POST "http://localhost:9655/reset-session?agent=my-agent"
```

Reset all sessions:

```bash
curl -X POST "http://localhost:9655/reset-session?agent=all"
```

Why chats still show up in DeepSeek Web: the proxy works through the internal
Web Chat API, and DeepSeek stores real chat sessions on its side. That is normal
for a web proxy. The point of session reuse is not to spawn new chats
unnecessarily and to reset carefully only when a chain has gone stale or broken.

---

## 👥 Multi-account pool

You can attach several auth files. The right model is a sticky account per
agent/session — the proxy does not switch accounts inside a live DeepSeek
session. If an account hits `401/403/429` and goes into cooldown, the session
is reset safely and the next request may move to a different available account.

Option 1 — a directory of auth files:

```bash
mkdir -p accounts
cp deepseek-auth-main.json accounts/main.json
cp deepseek-auth-backup.json accounts/backup.json
chmod 600 accounts/*.json
DEEPSEEK_AUTH_DIR=./accounts NON_INTERACTIVE=1 npm start
```

Option 2 — a list of files:

```bash
DEEPSEEK_AUTH_PATH="./accounts/main.json,./accounts/backup.json" NON_INTERACTIVE=1 npm start
```

How the pool behaves:

- a new agent/session gets an available account round-robin;
- the chosen account is pinned to the session (`sticky`);
- on `401`, `403`, `429` the account goes into cooldown and the request is retried on a different ready account;
- a DeepSeek "Too many messages" answer also counts as a rate limit: the account goes into a short cooldown (`DEEPSEEK_RATE_LIMIT_COOLDOWN_MS`, default 60 s); if there are no other accounts, the client gets `429` with `Retry-After`;
- if a session's sticky account is in cooldown, the old DeepSeek session is reset so we stop hammering a rate-limited/expired account;
- account status is visible in `/health` without auth file paths or file names;
- auth files must be stored with `0600` permissions.

Configure the cooldown:

```bash
DEEPSEEK_ACCOUNT_COOLDOWN_MS=600000 npm start
```

---

## 🔑 Console auth ideas

The password flow from PR #3 is doable, but it is safer not to store the
password and not to make it the default. A sane implementation:

1. `npm run auth:console` asks for email/phone and password through a hidden prompt.
2. The password is held only in process memory, never written to files/logs/history.
3. The script replays the web login flow via `fetch`/CDP: it gets the captcha/verify challenge, hands the link/code to the human, and waits for confirmation.
4. After a successful login only the standard-format `deepseek-auth.json` is saved.
5. If DeepSeek asks for captcha/2FA the script honestly says "open the link, complete the check, press Enter" instead of trying to bypass the protection.
6. For a VPS, `auth:console --no-save-password --output deepseek-auth.json` is the better mode.

Minimal safe MVP: console auth is interactive only, with no password in env. An acceptable automation option is `DEEPSEEK_EMAIL=... npm run auth:console`, but the password is still entered through a hidden prompt.

---

## ✅ Verify it works

```bash
curl http://localhost:9655/
curl http://localhost:9655/v1/models
curl http://localhost:9655/v1/model-capabilities
```

If everything is fine, `/health` returns the server status, the list of supported aliases, and `config_ready: true`.

`/health` returns a minimal `{status, service}` object for anonymous callers.
Send `Authorization: Bearer <key>` to get the full account pool and model list.

---

## 💬 chatbot.py (quick test client)

A stdlib-only Python client for checking that the proxy really works. No
`pip install` needed.

```bash
# interactive REPL
python chatbot.py

# one-shot smoke tests
python chatbot.py --once "Reply with exactly: SETUP OK"
python chatbot.py --no-stream --once "Name three prime numbers."
python chatbot.py --model deepseek-reasoner --once "Why is the sky blue?"
python chatbot.py --search --once "latest DeepSeek news"
python chatbot.py --session my-agent --system "You are terse."
```

It prints a readiness banner on start (status, auth check, ready accounts,
model list) and then streams tokens, rendering `reasoning_content` dimmed under
a `thinking:` label. Key flags: `--base-url`, `--api-key`, `--model`, `--search`,
`--session`, `--system`, `--no-stream`, `--once`. `OPENAI_BASE_URL` and
`OPENAI_API_KEY` are used as defaults.

In-REPL commands: `/help`, `/model <name>`, `/search`, `/stream`, `/clear`,
`/reset`, `/history`, `/quit`.

---

## 🧪 Request examples

### Chat Completions

```bash
curl -X POST http://localhost:9655/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "Hi! Answer in one sentence."}],
    "stream": false
  }'
```

### Reasoning

```bash
curl -X POST http://localhost:9655/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-reasoner",
    "messages": [{"role": "user", "content": "Answer briefly: why is the sky blue?"}],
    "stream": false
  }'
```

With `stream: true`, an ordinary answer (a request without `tools`) is handed to
the client as DeepSeek writes it: reasoning first, then text. If the request
contains `tools`, the answer may turn out to be a tool call, so the proxy waits
for the end and delivers it whole, and while it waits it sends an SSE comment
`: keep-alive` every `DEEPSEEK_STREAM_KEEPALIVE_MS` (10 s) so the client does
not drop the connection on a timeout. An error that happens after the stream
has started arrives as an `error` event inside the stream (the OpenAI and
Anthropic SDKs turn it into an exception); before the stream starts it is a
plain HTTP status.

For reasoning models the API returns the chain of thought separately from the
final answer:

- non-stream: `choices[0].message.reasoning_content`
- stream: `choices[0].delta.reasoning_content`
- usage: `usage.completion_tokens_details.reasoning_tokens`

`reasoning_tokens` is a rough estimate based on the extracted DeepSeek Web
`THINK` text, because the web stream does not report official per-reasoning
token usage.

### Web search

```bash
curl -X POST http://localhost:9655/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat-search",
    "messages": [{"role": "user", "content": "Find a recent fact about DeepSeek and answer briefly."}],
    "stream": false
  }'
```

### Streaming

```bash
curl -N -X POST http://localhost:9655/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "Write a short joke."}],
    "stream": true
  }'
```

### Anthropic Messages API

```bash
curl -X POST http://localhost:9655/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "max_tokens": 512,
    "messages": [{"role": "user", "content": "Reply with exactly OK"}],
    "stream": false
  }'
```

For Claude Code you can point the backend at it directly:

```bash
export ANTHROPIC_BASE_URL="http://127.0.0.1:9655"
export ANTHROPIC_AUTH_TOKEN="dummy-key"
export CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1
claude --model deepseek-chat
```

### OpenAI Responses API

```bash
curl -X POST http://localhost:9655/v1/responses \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "input": "Reply with exactly OK",
    "stream": false
  }'
```

### Tool calling

deepseek-free accepts:

- OpenAI `tools`;
- Anthropic `tools`;
- Responses API function tools.

The proxy asks DeepSeek to return a strict JSON tool call, but it also parses
fallback formats:

- `TOOL_CALL:`
- fenced JSON with an explicit `tool_call`, `tool_calls`, or `function_call` envelope
- `<​tool_call>...</tool_call>`
- DeepSeek DSML (`<｜DSML｜tool_calls>...`) and the web variant `<｜｜DSML｜｜ Tool Calls>`

Typical model mistakes are repaired while parsing: unescaped backslashes in
Windows paths (`"C:\git\src\index.ts"`) and real newlines inside string
arguments. Code blocks in another language (```` ```csharp ````,
```` ```python ````) are never treated as tool calls.

---

## 🧠 Models

`GET /v1/models` returns only the aliases that are currently verified and working through this proxy.

### Unified DeepSeek Web mode (since 2026-09-10)

On 10 September 2026 DeepSeek merged the "Fast", "Expert", and "Recognition"
web-chat modes into a single smart mode on the **DeepSeek-V4.1-Flash** model,
and on 14 September it retired V4 Pro. There is no model switcher left, only
"Deep thinking" (`thinking_enabled`) and "Search" (`search_enabled`) (#31).

So all aliases now send the same `model_type: "default"` to the Web API and
differ only in those two flags. The old names (`deepseek-expert`,
`deepseek-v4-pro`, …) are kept so client configs do not break, and they are
marked as `deprecated` in `/v1/model-capabilities`. If DeepSeek changes the
`model_type` value again, you can override it with `DEEPSEEK_MODEL_TYPE` (an
empty value means do not send the field).

### Working aliases

| Alias | Deep thinking | Web search | Comment |
| --- | --- | --- | --- |
| `deepseek-chat` | no | no | basic chat |
| `deepseek-default` | no | no | compatibility alias |
| `deepseek-v4-flash` | no | no | the official API name |
| `deepseek-v4.1-flash` | no | no | the current web-chat model |
| `deepseek-v3` | no | no | legacy alias |
| `deepseek-reasoner` | yes | no | `thinking_enabled=true` |
| `deepseek-r1` | yes | no | R1-compatible alias |
| `deepseek-chat-search` | no | yes | web search |
| `deepseek-default-search` | no | yes | web search alias |
| `deepseek-reasoner-search` | yes | yes | reasoning + search |
| `deepseek-r1-search` | yes | yes | R1-compatible + search |
| `deepseek-expert` | yes | no | legacy: "Expert" merged into the unified mode |
| `deepseek-v4-pro` | yes | no | legacy: V4 Pro retired, V4.1-Flash answers instead |
| `deepseek-expert-search` | yes | yes | legacy alias, now working |

### Images (verified against the live DeepSeek Web API)

On 7 October 2026, passing PNG/JPEG through `deepseek-vision` was verified
against the live DeepSeek Web API: multipart upload, file processing from
`PENDING` through `PARSING` to `SUCCESS`, the file ID reference in the
completion, and a visual answer with readable text, colours, and element
positions. Nearly square rectangles were called squares by the model, so shape
recognition accuracy needs to be checked for your particular task. Image
upload is enabled by default. To forbid sending images to DeepSeek, set
`DEEPSEEK_IMAGE_UPLOAD=0` explicitly:

```bash
DEEPSEEK_IMAGE_UPLOAD=0 npm start
```

- inline images are accepted: OpenAI `image_url` / Responses
  `input_image` with `data:image/...;base64,...` and Anthropic `image` with
  `source.type: "base64"` (including inside `tool_result`);
- `https://...` links are not downloaded (SSRF protection) — the model only
  sees the address;
- PNG, JPEG, WebP, and GIF are supported; other formats (for example SVG)
  stay a text marker;
- in an already-open chat only images from new messages are uploaded; into a
  new chat — the last `DEEPSEEK_MAX_IMAGES` (4) images of the conversation; a
  single image — up to `DEEPSEEK_MAX_IMAGE_BYTES` (7 MB), the whole request —
  up to 10 MB; already-uploaded images are not uploaded again (30 minute cache);
- if DeepSeek could not process an image, the request fails with
  `502 image_upload_failed` instead of a silent "blind" answer;
- with upload enabled `deepseek-vision` appears in `/v1/models` (it is the same
  unified mode).

With `DEEPSEEK_IMAGE_UPLOAD=0` images are replaced by a short marker
`[Image attached; not visible through this proxy]`; their bytes are not
uploaded to DeepSeek.

Full mapping:

```bash
curl http://localhost:9655/v1/model-capabilities
```

---

## 🔌 Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` or `/health` | proxy status |
| `GET` | `/v1/models` | list of working OpenAI-compatible aliases |
| `GET` | `/v1/model-capabilities` | full alias → real model → capabilities mapping |
| `POST` | `/v1/chat/completions` | OpenAI-compatible Chat Completions |
| `POST` | `/v1/messages` | Anthropic Messages API shim |
| `POST` | `/v1/responses` | OpenAI Responses API shim |
| `GET` | `/v1/sessions` | active local agent sessions |
| `POST` | `/reset-session?agent=<id>` | reset a single session |
| `POST` | `/reset-session?agent=all` | reset all sessions |

---

## 🖥 Open WebUI

Base URL for Open WebUI in Docker:

```text
http://host.docker.internal:9655/v1
```

For a local run without Docker:

```text
http://localhost:9655/v1
```

If `PROXY_API_KEY` is not set, the API key can be anything you like. If the key
is set, the client must send exactly that one — the proxy validates the bearer
token before allowing access to models, sessions, and completions.

---

## 🔐 Refresh the login

```bash
npm run auth
npm start
```

If DeepSeek started answering `401`, `403`, or asks for a new PoW/session — run
`npm run auth` again and refresh the saved browser session.

Local auth files must not end up on GitHub:

- `deepseek-auth.json`
- `.chrome-for-testing-profile-deepseek/`
- `.env`

They are already in `.gitignore`.

---

## 🧪 Tests

Syntax check, unit tests, and end-to-end tests against a local mock DeepSeek
server (no network and no account needed; `node --test` requires Node.js 18.13+):

```bash
npm test
```

Live smoke tests against a running local proxy (if `PROXY_API_KEY` is set it is
read from the environment):

```bash
BASE_URL=http://127.0.0.1:9655 MODEL=deepseek-chat npm run test:live
```

---

## 📌 Project status

deepseek-free is an experimental web-chat proxy for local use and
integrations. It depends on the current DeepSeek Web Chat contract, so when
DeepSeek changes things on their side the auth/session logic or the model
mapping may need an update.

If something stops working:

1. refresh the login with `npm run auth`;
2. check `/v1/model-capabilities`;
3. retry the request on a fresh session;
4. if the problem persists, DeepSeek probably changed its internal web API.

---

<p align="center">
  <strong>deepseek-free</strong> · <a href="https://github.com/ravvdevv/deepseek-free">GitHub</a>
</p>
