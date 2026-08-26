# amplifier-drumpack-tmux

The [drumbeat](https://github.com/) drumpack for the
[tmux-fleet smart tool](https://github.com/bkrabach/amplifier-smart-tool-tmux):
the thin layer that puts `tmux-fleet` on a drumbeat automation's PATH with a
card that teaches an agent to use it well.

This pack ships exactly three things -- a card (`drumpack.md`), a launcher shim
(`bin/tmux-fleet`), and an automation exemplar (`automations/fleet-drill.md`).
Every capability lives in the smart tool; this pack is exposure, not capability
(see [`docs/VISION.md`](docs/VISION.md)).

## Layout

```
drumpack.md                 the card: frontmatter (machine surface) + the agent-facing manual
bin/tmux-fleet              the launcher shim: execs the pack-private venv's tmux-fleet
automations/fleet-drill.md  a working, disabled example automation
docs/VISION.md              the end-state this repo converges toward
```

## Install

The tool is **not vendored** -- it is a dependency installed into a
**pack-private virtualenv** (`.venv/` at the pack root). The shim execs that
interpreter and refuses, with the exact rebuild command, if it is missing. It
never provisions the venv for you mid-turn.

The smart tool's plumbing dependency (tmux-kit) is not on the engine's base
PATH, which is the whole reason for the private venv. Building it also pulls
the `amplifier-agent-py` SDK, but **not** the `amplifier-agent` engine binary:
that is a shared machine service you install once and every smart tool reuses.
The deterministic verbs need none of it; only `triage` and `interpret` do.

### Prerequisites

- [`uv`](https://docs.astral.sh/uv/) on PATH (builds the venv).
- `tmux` on PATH (the tool is a tmux client).
- `amplifier-agent` on PATH **only if** you want the model-backed verbs
  (`triage`, `interpret`); install it once with
  `uv tool install git+https://github.com/microsoft/amplifier-agent`, then
  `amplifier-agent auth`.

### Consumers

```sh
cd /path/to/amplifier-drumpack-tmux
uv venv .venv
uv pip install --python .venv/bin/python \
  git+https://github.com/bkrabach/amplifier-smart-tool-tmux
```

### Development (install the tool from a local checkout)

```sh
cd /path/to/amplifier-drumpack-tmux
uv venv .venv
uv pip install --python .venv/bin/python \
  git+file:///home/bkrabach/dev/drumbeat-team-ci/amplifier-smart-tool-tmux
```

Verify the shim resolves the tool:

```sh
bin/tmux-fleet --help      # complete, agent-facing verb listing
bin/tmux-fleet doctor      # is tmux present and the socket reachable?
```

`.venv/` is a build artifact and is git-ignored -- each checkout builds its own.

## Wire it into a drumbeat workspace

A workspace enables a pack by listing its directory in `drumpacks.txt` at the
workspace root (one path per line, relative to the workspace or absolute; blank
lines and `#` comments ignored). Add the line:

```
# drumpacks.txt
/path/to/amplifier-drumpack-tmux
```

or, if the pack sits beside your workspace, a relative path:

```
../amplifier-drumpack-tmux
```

That puts `bin/` on every turn's PATH and injects `drumpack.md` into any
automation that `requires: [tmux-fleet]`. Confirm the engine sees it:

```sh
drumbeat doctor --workspace /path/to/workspace   # -> "drumpacks: 1 declared in .../drumpacks.txt"
```

## The example automation

[`automations/fleet-drill.md`](automations/fleet-drill.md) is a read-only
"is the fleet observation path healthy?" drill that exercises `sessions` and
`read`. It ships **disabled** (`enabled: false`) like every exemplar and runs
`notify: urgent-only` -- it does its work quietly and pushes a notification
only when its final reply carries an `URGENT:` marker. Copy it into your
workspace's `automations/` and flip `enabled: true` once you have verified a
turn runs.

## What this pack will not do

- It carries **no logic** beyond environment bootstrap. Anything the tool can
  do, it does; this pack only exposes it.
- It never vendors or forks the smart tool -- it is a dependency.
- The write verbs (`send`, `create`) keep their per-invocation `--confirmed`
  fence; there is no pack-level unlock. No verb kills or renames a session.

See [`docs/VISION.md`](docs/VISION.md) for the full design.
