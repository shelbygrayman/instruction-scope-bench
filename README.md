# Instruction Scope Bench

Which AGENTS.md files reach Codex when a developer starts it in a monorepo? This benchmark checks the actual startup input rendered by Codex CLI 0.171.0. A fixed prompt mentions the API task in every case. Only the launch directory and the presence of an override change.

| Launch scenario | Markers observed |
| --- | --- |
| Repository root | Root |
| API directory | Root and API |
| Web sibling | Root and web |
| API directory with AGENTS.override.md | Root and API override |

All four cases matched expectations in three repetitions on a hosted macOS runner. [Inspect the first run and download its JSON report](https://github.com/shelbygrayman/instruction-scope-bench/actions/runs/45052540010).

## Reproduce

Requires Python 3.10+, Node 22, npm and Git. From this checkout:

```sh
npm install --prefix ./bench-tools @openai/codex@0.171.0
python3 scope.py --codex "$PWD/bench-tools/node_modules/.bin/codex" --repeat 3
```

Each trial writes fresh random markers into a temporary Git repository. The runner launches Codex from each directory with a clean Codex home and inspects the JSON returned by `codex debug prompt-input`. The report lists expected and observed marker names and wall time per invocation. Exit status 0 means all marker sets matched. A mismatch exits 1. A CLI launch or environment error fails the run separately.

The result covers project instructions at startup under default settings. Agent decisions, later file reads, custom fallback filenames and personal instructions are outside this benchmark. No model call or API key is needed.

To try a different layout, edit the fixture paths and expected marker lists in `scope.py`, then run the same command. To compare CLI releases, update the pinned version in the runner and installation command together and keep both JSON reports.
