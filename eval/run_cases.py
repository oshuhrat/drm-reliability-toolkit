#!/usr/bin/env python3
"""Run every evaluation case through every method and save the raw responses.

Output layout (one run directory per date):

    eval/runs/<YYYY-MM-DD>[-mock]/
        manifest.json          # model, settings, prompt hashes, per-call metadata
        prompts/<method>.json  # exact system prompt and user template used
        <method>/<case_id>.md  # raw model response, nothing added

Calls are made one at a time, in a fixed order, with a pause between them.
Real API calls require ``--live``; ``--mock`` produces canned responses
without network access so the pipeline can be tested.

Examples:
    python eval/run_cases.py --mock
    python eval/run_cases.py --live --only case-01 case-10
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cases import DEFAULT_CASES_PATH, REPO_ROOT, Case, parse_cases, validate_cases  # noqa: E402

DEFAULT_CONFIG = Path(__file__).resolve().parent / "config.json"
DEFAULT_RUNS_ROOT = Path(__file__).resolve().parent / "runs"
EMPTY_MARKER = "<!-- empty response: see manifest.json for stop_reason -->\n"


def load_config(path: Path) -> dict:
    config = json.loads(path.read_text(encoding="utf-8"))
    required = ("model", "methods") if config.get("provider") == "opencode" else ("model", "max_tokens", "api_key_env", "methods")
    for key in required:
        if key not in config:
            raise SystemExit(f"Config {path} is missing '{key}'")
    return config


def strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[end + len("\n---\n"):].lstrip("\n")
    return text


def build_method_prompts(config: dict) -> dict[str, dict]:
    """Resolve each method's system prompt text and user template."""
    prompts = {}
    for name, spec in config["methods"].items():
        system = spec.get("system")
        if spec.get("system_file"):
            system = (REPO_ROOT / spec["system_file"]).read_text(encoding="utf-8")
            if spec.get("strip_frontmatter"):
                system = strip_frontmatter(system)
        template = spec["user_template"]
        if "{input}" not in template:
            raise SystemExit(f"user_template for method '{name}' has no {{input}} placeholder")
        prompts[name] = {
            "system": system,
            "system_file": spec.get("system_file"),
            "user_template": template,
        }
    return prompts


def sha256(text: str | None) -> str | None:
    return None if text is None else hashlib.sha256(text.encode("utf-8")).hexdigest()


def render_user(template: str, case: Case) -> str:
    # str.replace, not str.format: case inputs may contain braces.
    return template.replace("{input}", case.input)


# --- providers -----------------------------------------------------------------


def mock_call(method: str, case: Case, **_) -> dict:
    """Deterministic canned output. Not a model; for pipeline tests only."""
    if method == "drm":
        text = (
            "# DRM Audit Report\n\n"
            "## 1. Scope\n"
            f"- Material reviewed: mock input for {case.id}\n\n"
            "## 2. Executive summary\n"
            "- Mock finding. **[LIMIT]** This is a canned mock response.\n"
        )
    else:
        text = (
            f"Mock analysis of {case.id}.\n\n"
            "1. Mock observation about the supplied text.\n"
            "2. This is a canned mock response, not model output.\n"
        )
    return {
        "text": text,
        "response_model": "mock",
        "stop_reason": "end_turn",
        "usage": None,
    }


class AnthropicCaller:
    def __init__(self, config: dict):
        key = os.environ.get(config["api_key_env"])
        if not key:
            raise SystemExit(f"Environment variable {config['api_key_env']} is not set")
        try:
            import anthropic  # imported lazily so --mock needs no dependency
        except ImportError as exc:
            raise SystemExit("Live runs need the SDK: pip install anthropic") from exc
        self.config = config
        self.client = anthropic.Anthropic(api_key=key, max_retries=config.get("max_retries", 4))

    def __call__(self, method: str, case: Case, *, system: str | None, user: str) -> dict:
        params = {
            "model": self.config["model"],
            "max_tokens": self.config["max_tokens"],
            "messages": [{"role": "user", "content": user}],
        }
        if system:
            params["system"] = system
        if self.config.get("temperature") is not None:
            params["temperature"] = self.config["temperature"]
        if self.config.get("effort"):
            params["output_config"] = {"effort": self.config["effort"]}
        response = self.client.messages.create(**params)
        text = "".join(block.text for block in response.content if block.type == "text")
        usage = getattr(response, "usage", None)
        return {
            "text": text,
            "response_model": response.model,
            "stop_reason": response.stop_reason,
            "usage": {
                "input_tokens": getattr(usage, "input_tokens", None),
                "output_tokens": getattr(usage, "output_tokens", None),
            }
            if usage
            else None,
        }


class OpenCodeCaller:
    """`opencode run -m <provider/model>`; the system prompt goes in the message body."""

    def __init__(self, config: dict):
        self.config = config

    def __call__(self, method: str, case: Case, *, system: str | None, user: str) -> dict:
        from opencode_client import compose_prompt, run_opencode

        return run_opencode(
            self.config["model"],
            compose_prompt(system, user),
            binary=self.config.get("opencode_bin"),
            timeout=int(self.config.get("timeout_seconds", 600)),
        )


# --- main ----------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--mock", action="store_true", help="canned responses, no network")
    mode.add_argument("--live", action="store_true", help="call the real API (costs money)")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--methods", nargs="+", help="subset of methods from the config")
    parser.add_argument("--only", nargs="+", metavar="CASE_ID", help="subset of case ids, e.g. case-01")
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    parser.add_argument("--run-dir", type=Path, help="explicit run directory (overrides date naming)")
    parser.add_argument("--date", help="date label for the run directory (default: today, UTC)")
    parser.add_argument("--overwrite", action="store_true", help="re-run cases that already have output")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = load_config(args.config)
    prompts = build_method_prompts(config)

    cases = parse_cases(args.cases)
    problems = validate_cases(cases)
    if problems:
        raise SystemExit("Case file problems:\n  " + "\n  ".join(problems))
    if args.only:
        wanted = set(args.only)
        unknown = wanted - {c.id for c in cases}
        if unknown:
            raise SystemExit(f"Unknown case ids: {sorted(unknown)}")
        cases = [c for c in cases if c.id in wanted]

    methods = args.methods or list(prompts)
    unknown_methods = set(methods) - set(prompts)
    if unknown_methods:
        raise SystemExit(f"Unknown methods: {sorted(unknown_methods)}")

    date = args.date or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    run_dir = args.run_dir or args.runs_root / (f"{date}-mock" if args.mock else date)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(exist_ok=True)

    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"calls": []}
    manifest.update(
        {
            "mode": "mock" if args.mock else "live",
            "provider": "mock" if args.mock else config.get("provider", "anthropic"),
            "model": config["model"],
            "temperature": config.get("temperature"),
            "effort": config.get("effort"),
            "max_tokens": config.get("max_tokens"),
            "config_file": str(args.config),
            "cases_file": str(args.cases),
            "cases_sha256": sha256(Path(args.cases).read_text(encoding="utf-8")),
            "methods": {
                m: {
                    "system_file": prompts[m]["system_file"],
                    "system_sha256": sha256(prompts[m]["system"]),
                    "user_template_sha256": sha256(prompts[m]["user_template"]),
                }
                for m in methods
            },
        }
    )
    for m in methods:
        (run_dir / "prompts" / f"{m}.json").write_text(
            json.dumps(prompts[m], ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    if args.mock:
        caller = mock_call
    elif config.get("provider") == "opencode":
        caller = OpenCodeCaller(config)
    else:
        caller = AnthropicCaller(config)
    delay = 0.0 if args.mock else float(config.get("delay_seconds", 0))

    done = skipped = failed = 0
    first_call = True
    for case in cases:
        for method in methods:
            out_path = run_dir / method / f"{case.id}.md"
            if out_path.exists() and not args.overwrite:
                skipped += 1
                continue
            out_path.parent.mkdir(parents=True, exist_ok=True)
            if not first_call and delay:
                time.sleep(delay)
            first_call = False
            user = render_user(prompts[method]["user_template"], case)
            record = {
                "case_id": case.id,
                "method": method,
                "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "user_sha256": sha256(user),
            }
            try:
                result = caller(method, case, system=prompts[method]["system"], user=user)
            except Exception as exc:  # recorded and reported; the run continues
                record.update({"error": f"{type(exc).__name__}: {exc}"})
                failed += 1
                print(f"[error] {case.id} {method}: {record['error']}", file=sys.stderr)
            else:
                text = result.pop("text")
                out_path.write_text(text if text.strip() else EMPTY_MARKER, encoding="utf-8")
                record.update(result)
                if result.get("stop_reason") not in ("end_turn", None):
                    print(f"[warn] {case.id} {method}: stop_reason={result['stop_reason']}", file=sys.stderr)
                done += 1
                print(f"[ok] {case.id} {method}")
            record["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
            manifest["calls"].append(record)
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nRun directory: {run_dir}\n{done} written, {skipped} skipped (already present), {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
