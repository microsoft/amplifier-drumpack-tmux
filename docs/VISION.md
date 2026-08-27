# VISION

The desired end state this repo converges toward, written as though already true.
Never edited to record what shipped — status lives in the issue queue. Amendments
carry evidence and land in the dated changelog below. Governance: amend here
first → file work items against the amendment → execute.

## What this is

The drumbeat drumpack for the tmux-fleet smart tool: the thin layer that puts
`tmux-fleet` on a drumbeat automation's PATH with a card that teaches an agent
to use it well. An automation author adds one line to `drumpacks.txt` and their
scheduled agent can observe the machine's tmux fleet — and, under explicit
confirmation, act on it.

## Principles

### 1. Exposure, not capability

Every capability lives in the smart tool
([amplifier-smart-tool-tmux](https://github.com/microsoft/amplifier-smart-tool-tmux));
this pack ships a card, a launcher shim, and an automation exemplar — nothing
else. Logic found in this repo's `bin/` beyond environment bootstrap is a
defect: it is capability the tool's other consumers cannot reach.

### 2. Two contracts, honored exactly

The card conforms to drumbeat's `contracts/drumpack-card.v1.md`. The shim
invokes only what the tool's `contracts/cli.v1.md` freezes. When either
contract moves, this pack moves with it — it never reaches around a contract
into internals.

### 3. The card teaches what `--help` cannot

The card body is the agent-facing manual: verb semantics, the confirmation
fence, the socket discipline, completeness honesty, and the negative space
(no kill, no rename — ever). It is written to be read cold by an agent that
has never seen tmux.

### 4. Fail loud at the boundary

The shim refuses with the exact remedy when its environment is broken (missing
venv, missing tmux, missing tool) — it never silently provisions itself
mid-turn and never falls back to an ambient interpreter.

### 5. Nothing consumer-specific

Generic env names, generic XDG paths, no product vocabulary. Any drumbeat
workspace on any machine can adopt this pack unchanged.

## What this repo deliberately resists

- **Logic in the shim** — bootstrap only.
- **Vendoring or forking the smart tool** — it is a dependency.
- **Card content that duplicates `--help`** — the card carries judgment and
  safety context, not argument listings that will drift.
- **Write verbs without the per-invocation confirmation fence.**

## Changelog

- **2026-08-26** — Initial vision. The pack is the thin edge of the negotiated
  three-layer design: tmux-kit (mechanism) → tmux-fleet smart tool (judgment,
  on amplifier-agent) → this pack (exposure to drumbeat automations).
