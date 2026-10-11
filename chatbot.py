#!/usr/bin/env python3
"""chatbot.py - interactive smoke-test client for deepseek-free.

Standard library only, no pip install required.

    python chatbot.py
    python chatbot.py --model deepseek-reasoner --system "You are terse."
    python chatbot.py --once "Reply with exactly: SETUP OK"
    python chatbot.py --search "latest DeepSeek news"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import NoReturn

DEFAULT_BASE_URL = "http://127.0.0.1:9655/v1"
DEFAULT_MODEL = "deepseek-chat"
SEARCH_MODELS = {"deepseek-chat-search", "deepseek-default-search",
                 "deepseek-reasoner-search", "deepseek-r1-search", "deepseek-expert-search"}

RESET = "\033[0m"
DIM = "\033[2m"
BOLD = "\033[1m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
RED = "\033[31m"


class Tty:
    """Colors only when stdout is a real terminal and NO_COLOR is unset."""

    def __init__(self, enabled: bool) -> None:
        self.on = enabled

    def __call__(self, code: str, text: str) -> str:
        return f"{code}{text}{RESET}" if self.on else text


def die(message: str, code: int = 1) -> NoReturn:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def fail_on_http_error(exc: urllib.error.HTTPError, url: str) -> NoReturn:
    """Render a proxy error body (JSON or plain text) and exit."""
    detail = exc.read().decode(errors="replace")
    try:
        detail = json.dumps(json.loads(detail), ensure_ascii=False)
    except ValueError:
        pass
    die(f"HTTP {exc.code} {exc.reason}\n  {url}\n  {detail[:600]}", 2)


def check_health(base_url: str, api_key: str, tty: Tty) -> dict:
    """GET /health (full detail when an api key is set) and print a readiness banner."""
    root = base_url[: -len("/v1")] if base_url.rstrip("/").endswith("/v1") else base_url.rstrip("/")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    auth = tty(DIM, "unauthenticated (details redacted)")
    try:
        with urllib.request.urlopen(
            urllib.request.Request(f"{root}/health", headers=headers), timeout=10
        ) as resp:
            health = json.load(resp)
        if api_key and health.get("models"):
            auth = tty(GREEN, "auth ok")
    except urllib.error.HTTPError:
        return {"status": "unknown"}
    except urllib.error.URLError as exc:
        die(tty(RED, f"Proxy is not reachable at {root} ({exc.reason})")
            + "\n  Start it with:  NON_INTERACTIVE=1 npm start", 2)

    if api_key and not health.get("models"):
        auth = tty(RED, "AUTH FAILED")

    accounts = health.get("accounts") or []
    ready = sum(1 for a in accounts if a.get("ready"))
    models = ", ".join(health.get("models") or []) or "(hidden - no api key)"

    print(tty(BOLD, "deepseek-free"), tty(DIM, root))
    print(f"  status   {health.get('status', '?')}   {auth}")
    if accounts:
        print(f"  accounts {ready}/{len(accounts)} ready"
              f"   config_ready={health.get('config_ready')}")
    else:
        print(tty(YELLOW, "  accounts unknown - set an api key for full diagnostics"))
    print(f"  models   {tty(DIM, models)}")
    return health


def sse_events(resp):
    """Yield parsed JSON objects from an SSE stream, skipping keep-alive comments."""
    for raw in resp:
        line = raw.decode(errors="replace").rstrip("\n")
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if not payload or payload == "[DONE]":
            if payload == "[DONE]":
                return
            continue
        try:
            yield json.loads(payload)
        except ValueError:
            continue


def ask(base_url: str, api_key: str, model: str, session: str,
        messages: list[dict], stream: bool, tty: Tty) -> tuple[str, str]:
    """Send one chat completion. Returns (content, reasoning)."""
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if session:
        headers["x-agent-session"] = session

    url = f"{base_url}/chat/completions"
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers,
                                 method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=300)
    except urllib.error.HTTPError as exc:
        fail_on_http_error(exc, url)

    if not stream:
        data = json.load(resp)
        if "error" in data:
            die(tty(RED, "error") + f"  {data['error']}", 2)
        message = (data.get("choices") or [{}])[0].get("message") or {}
        content = message.get("content") or ""
        reasoning = message.get("reasoning_content") or ""
        usage = data.get("usage") or {}
        if content:
            print(content)
        if usage:
            print(tty(DIM, f"[{usage.get('total_tokens', '?')} tokens]"))
        return content, reasoning

    content_parts: list[str] = []
    reasoning_parts: list[str] = []
    in_reasoning = False
    finish = None
    usage = {}

    for event in sse_events(resp):
        if "error" in event:
            err = event["error"]
            message = err.get("message") if isinstance(err, dict) else str(err)
            print()
            die(tty(RED, "stream error") + f"  {message}", 2)

        choice = (event.get("choices") or [{}])[0]
        delta = choice.get("delta") or {}

        thought = delta.get("reasoning_content")
        if thought:
            if not in_reasoning:
                sys.stdout.write(tty(DIM, "thinking: "))
                sys.stdout.flush()
                in_reasoning = True
            reasoning_parts.append(thought)
            sys.stdout.write(tty(DIM, thought))
            sys.stdout.flush()
            continue

        piece = delta.get("content")
        if piece:
            if in_reasoning and not content_parts:
                sys.stdout.write("\n" + tty(BOLD, "answer:   "))
                sys.stdout.flush()
                in_reasoning = False
            content_parts.append(piece)
            sys.stdout.write(piece)
            sys.stdout.flush()

        for call in delta.get("tool_calls") or []:
            fn = call.get("function") or {}
            print(tty(CYAN, f"\n[tool] {fn.get('name')}({fn.get('arguments', '')})"))

        if choice.get("finish_reason"):
            finish = choice["finish_reason"]

    if in_reasoning:
        sys.stdout.write("\n" + tty(BOLD, "answer:   "))
    if not content_parts and not reasoning_parts:
        sys.stdout.write(tty(YELLOW, "[empty response]"))
    sys.stdout.write("\n")
    sys.stdout.flush()

    total = (usage or {}).get("total_tokens")
    meta = f"[{total} tokens]" if total else ""
    if finish:
        meta = f"{meta} finish={finish}".strip()
    if meta:
        print(tty(DIM, meta))
    return "".join(content_parts), "".join(reasoning_parts)


HELP = """
/help              show this help
/model <name>      switch model (current: {model})
/search            toggle web search on/off
/stream            toggle streaming on/off
/clear             clear the conversation history
/reset             reset this session on the proxy
/history           show the current session id and message count
/quit              exit
""".strip()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Interactive smoke-test client for deepseek-free",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Standard library")[0],
    )
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL", DEFAULT_BASE_URL),
                        help=f"proxy base url (default: {DEFAULT_BASE_URL})")
    parser.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY", "burat"),
                        help="proxy api key (default: $OPENAI_API_KEY or 'burat')")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"model alias (default: {DEFAULT_MODEL})")
    parser.add_argument("--session", default=None, help="x-agent-session id (enables proxy-side session reuse)")
    parser.add_argument("--system", default=None, help="system prompt")
    parser.add_argument("--no-stream", action="store_true", help="disable streaming")
    parser.add_argument("--search", action="store_true", help="use a web-search model")
    parser.add_argument("--once", nargs="?", const="Reply with exactly: SETUP OK", default=None,
                        metavar="PROMPT", help="send a single prompt and exit")
    args = parser.parse_args()

    c = Tty(sys.stdout.isatty() and not os.environ.get("NO_COLOR"))
    base_url = args.base_url.rstrip("/")
    if not base_url.endswith("/v1"):
        base_url = f"{base_url}/v1"

    model = args.model
    if args.search:
        model = "deepseek-chat-search"
    search_on = model in SEARCH_MODELS
    stream = not args.no_stream

    health = check_health(base_url, args.api_key, c)
    if health.get("config_ready") is False:
        print(c(YELLOW, "  warning: config_ready is false - run: npm run doctor"))
    elif health.get("accounts") and not any(a.get("ready") for a in health["accounts"]):
        print(c(YELLOW, "  warning: no account is ready - run: npm run auth"))

    messages: list[dict] = []
    if args.system:
        messages.append({"role": "system", "content": args.system})

    session = args.session
    prompt_text = args.once if args.once is not None else None

    if prompt_text is not None:
        messages.append({"role": "user", "content": prompt_text})
        ask(base_url, args.api_key, model, session, messages, stream, c)
        return 0

    print(c(DIM, "  /help for commands, Ctrl+C or /quit to exit\n"))
    while True:
        try:
            line = input(c(CYAN, "you> ")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if not line:
            continue

        if line.startswith("/"):
            parts = line[1:].split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1].strip() if len(parts) > 1 else ""

            if cmd in ("quit", "exit", "q"):
                return 0
            if cmd == "help":
                print(HELP.format(model=model))
                continue
            if cmd == "model":
                model = arg or model
                search_on = model in SEARCH_MODELS
                print(c(DIM, f"  model = {model}"))
                continue
            if cmd == "search":
                search_on = not search_on
                if search_on and model not in SEARCH_MODELS:
                    model = "deepseek-chat-search"
                elif not search_on and model in SEARCH_MODELS:
                    model = "deepseek-reasoner" if "reasoner" in model else "deepseek-chat"
                print(c(DIM, f"  search = {search_on}, model = {model}"))
                continue
            if cmd == "stream":
                stream = not stream
                print(c(DIM, f"  stream = {stream}"))
                continue
            if cmd == "clear":
                messages = [{"role": m["role"], "content": m["content"]}
                            for m in messages if m["role"] == "system"]
                print(c(DIM, "  history cleared (proxy session kept)"))
                continue
            if cmd == "reset":
                root = base_url[: -len("/v1")]
                agent = session or "all"
                try:
                    with urllib.request.urlopen(f"{root}/reset-session?agent={agent}",
                                                timeout=15) as resp:
                        print(c(GREEN, f"  proxy session reset: {json.load(resp)}"))
                except urllib.error.URLError as exc:
                    print(c(RED, f"  reset failed: {exc.reason}"))
                continue
            if cmd == "history":
                turns = sum(1 for m in messages if m["role"] != "system")
                print(c(DIM, f"  session={session or '(auto)'}  turns={turns}  model={model}"))
                continue
            print(c(RED, f"  unknown command /{cmd} - try /help"))
            continue

        messages.append({"role": "user", "content": line})
        try:
            content, _ = ask(base_url, args.api_key, model, session, messages, stream, c)
        except SystemExit:
            messages.pop()
            continue
        if content:
            messages.append({"role": "assistant", "content": content})


if __name__ == "__main__":
    sys.exit(main())
