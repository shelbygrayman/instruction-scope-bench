"""Check Codex startup instruction scope. Requires Python 3.10+, git and Codex 0.171.0."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import uuid

VERSION = "0.171.0"
PROMPT = "Describe the task in services/api/task.txt."
FILES = {"root": "AGENTS.md", "api": "services/api/AGENTS.md",
         "web": "services/web/AGENTS.md", "override": "services/api/AGENTS.override.md"}


def run(cwd, env, *args):
    return subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True,
                          timeout=45, check=True).stdout


def benchmark(binary, repeats):
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        repo = base / "repo"
        repo.mkdir()
        home = base / "codex"
        home.mkdir()
        env = dict(os.environ, CODEX_HOME=str(home))
        version = run(repo, env, binary, "--version").strip()
        if version.split()[-1] != VERSION:
            raise ValueError(f"Expected {VERSION}, got {version}")
        run(repo, env, "git", "init", "-q")
        for directory in ("services/api", "services/web"):
            (repo / directory).mkdir(parents=True)
        (repo / "services/api/task.txt").write_text("Summarize this fixture.")
        for trial in range(1, repeats + 1):
            markers = {key: uuid.uuid4().hex for key in FILES}
            (repo / FILES["override"]).unlink(missing_ok=True)
            for key in ("root", "api", "web"):
                (repo / FILES[key]).write_text(markers[key])
            for name, cwd, expected in [
                ("root", ".", ["root"]), ("nested", "services/api", ["root", "api"]),
                ("sibling", "services/web", ["root", "web"]),
                ("override", "services/api", ["root", "override"])]:
                if name == "override":
                    (repo / FILES[name]).write_text(markers[name])
                start = time.monotonic()
                data = json.loads(run(repo / cwd, env, binary, "debug", "prompt-input", PROMPT))
                trace = json.dumps(data)
                if PROMPT not in trace:
                    raise ValueError("Prompt missing from rendered input")
                observed = [key for key, marker in markers.items() if marker in trace]
                rows.append(dict(trial=trial, case=name, cwd=cwd, expected=expected,
                                 observed=observed, passed=set(expected) == set(observed),
                                 elapsed_ms=round((time.monotonic() - start) * 1000)))
    return dict(codex=version, results=rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--repeat", type=int, default=3)
    args = parser.parse_args()
    if args.repeat < 1:
        parser.error("--repeat must be positive")
    try:
        report = benchmark(args.codex, args.repeat)
    except subprocess.CalledProcessError as exc:
        parser.exit(2, f"{exc.cmd[0]} failed: {exc.stderr}\n")
    print(json.dumps(report, indent=2))
    raise SystemExit(int(any(not row["passed"] for row in report["results"])))
