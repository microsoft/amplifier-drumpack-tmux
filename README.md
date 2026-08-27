# amplifier-drumpack-tmux

The [drumbeat](https://github.com/) drumpack for the
[tmux-fleet smart tool](https://github.com/microsoft/amplifier-smart-tool-tmux):
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

The smart tool's dependencies -- the tmux-kit plumbing and the embedded
amplifier-agent engine -- are not on the engine's base PATH, which is the whole
reason for the private venv. Building the venv installs the engine
automatically (it is a regular dependency of the tool); the two model-backed
verbs (`triage`, `interpret`) import it in-process. There is no separate engine
binary and no shared machine service. The deterministic verbs need nothing
further; only `triage` and `interpret` need a provider (below).

### Prerequisites

- [`uv`](https://docs.astral.sh/uv/) on PATH (builds the venv).
- `tmux` on PATH (the tool is a tmux client).
- **Only for the model-backed verbs** (`triage`, `interpret`): build the venv
  with a **provider extra** so its SDK is present (e.g. `tmux-fleet[anthropic]`,
  or `[openai]` -- see the install commands below), and put that provider's
  **credentials in the environment** (`export ANTHROPIC_API_KEY=...`, or
  `OPENAI_API_KEY=...`). The tool stores none of its own. The eight
  deterministic verbs need no provider at all; a smart verb invoked without one
  fails loudly, naming the missing precondition (the provider extra is not
  installed, no provider is configured, or no credentials are in the
  environment).


### Consumers

```sh
cd /path/to/amplifier-drumpack-tmux
uv venv .venv
uv pip install --python .venv/bin/python \
  "tmux-fleet[anthropic] @ git+https://github.com/microsoft/amplifier-smart-tool-tmux"
```

The `[anthropic]` extra pulls that provider's SDK for the model-backed verbs;
use `[openai]` instead, or drop the extra (`"tmux-fleet @ git+..."`) if you only
want the deterministic verbs. The engine itself comes in regardless -- it is a
regular dependency of the tool.

### Development (install the tool from a local checkout)

```sh
cd /path/to/amplifier-drumpack-tmux
uv venv .venv
uv pip install --python .venv/bin/python \
  "tmux-fleet[anthropic] @ git+file:///path/to/amplifier-smart-tool-tmux"
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

## Contributing

> [!NOTE]
> This project is not currently accepting external contributions, but we're actively working toward opening this up. We value community input and look forward to collaborating in the future. For now, feel free to fork and experiment!

Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit [Contributor License Agreements](https://cla.opensource.microsoft.com).

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
