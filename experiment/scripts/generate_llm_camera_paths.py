from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_TASKS = Path("experiment/llm_camera/tasks/camera_tasks.json")
DEFAULT_PROMPT = Path("experiment/llm_camera/prompts/qwen_camera_prompt.md")
DEFAULT_OUT = Path("experiment/outputs/llm_camera/paths/llm")


def extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"No JSON object found in response: {text[:200]}")
    return json.loads(text[start : end + 1])


def call_openai_compatible(
    *,
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    temperature: float,
    timeout: int,
) -> str:
    endpoint = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You output strict JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API HTTP {exc.code}: {body}") from exc
    return data["choices"][0]["message"]["content"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate LLM camera trajectory JSON files from natural language tasks.")
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    parser.add_argument("--prompt-template", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"))
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL", "deepseek-chat"))
    parser.add_argument("--api-key-env", default="")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--dry-run", action="store_true", help="Write prompts only; do not call API.")
    args = parser.parse_args()

    data = json.loads(args.tasks.read_text(encoding="utf-8"))
    template = args.prompt_template.read_text(encoding="utf-8")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "prompts").mkdir(exist_ok=True)
    (args.out_dir / "raw").mkdir(exist_ok=True)

    api_key = os.environ.get(args.api_key_env, "")
    if not args.dry_run and not api_key:
        print(f"Missing API key. Set ${args.api_key_env} or run with --dry-run.", file=sys.stderr)
        sys.exit(2)

    manifest = []
    for task in data["tasks"]:
        prompt = template.replace("{{TASK_TEXT}}", task["text"])
        prompt_path = args.out_dir / "prompts" / f"{task['id']}.txt"
        prompt_path.write_text(prompt, encoding="utf-8")

        if args.dry_run:
            manifest.append({"task_id": task["id"], "source": "llm", "prompt": str(prompt_path), "status": "dry_run"})
            continue

        raw_text = call_openai_compatible(
            base_url=args.base_url,
            api_key=api_key,
            model=args.model,
            prompt=prompt,
            temperature=args.temperature,
            timeout=args.timeout,
        )
        raw_path = args.out_dir / "raw" / f"{task['id']}.txt"
        raw_path.write_text(raw_text, encoding="utf-8")

        params = extract_json(raw_text)
        params["source"] = "llm"
        params["task_id"] = task["id"]
        params["input_text"] = task["text"]
        out_path = args.out_dir / f"{task['id']}.json"
        out_path.write_text(json.dumps(params, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest.append({"task_id": task["id"], "path": str(out_path), "source": "llm", "raw": str(raw_path)})

    (args.out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote LLM manifest to {args.out_dir / 'manifest.json'}")


if __name__ == "__main__":
    main()
