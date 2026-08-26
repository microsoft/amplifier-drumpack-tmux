---
pack_format: 1
# Progress narration per subcommand (drumpack-card.v1 rule 2, optional). Keyed
# by the subcommand the turn runs; the engine shows the phrase while it runs and
# narrates a generic phrase for anything not listed here. Owned by this pack,
# never hardcoded in the engine.
activity:
  socket: "Resolving the tmux socket…"
  sessions: "Looking at agent sessions…"
  attention: "Ranking where to look first…"
  read: "Reading session output…"
  triage: "Triaging the fleet…"
  interpret: "Interpreting a session…"
  send: "Sending input to an agent session…"
  create: "Starting a new session…"
  doctor: "Checking tmux readiness…"
  exit-code: "Checking a session's exit code…"
name: tmux-fleet
description: >
  The tmux fleet on this machine: which sessions exist, whether each is
  parked at a prompt right now, what harness is running in it, how long it
  has been quiet, its pane and scrollback, and -- only under an explicit
  per-invocation confirmation -- the ability to type into one or to start a
  new one. Two verbs read the fleet through the AI substrate (a fleet-wide
  triage and a single-session interpretation); every other verb is
  deterministic and needs no substrate at all. Poll-only: nothing here
  pushes. Both write verbs refuse without that confirmation, and there is no
  verb that kills or renames a session.
tools:
  - name: tmux-fleet
    bin: bin/tmux-fleet
    description: "Observe the local tmux fleet read-only (sessions, idleness, panes, scrollback), triage/interpret it through amplifier-agent, and -- only under an explicit per-invocation --confirmed -- send input or create a session. No verb kills or renames."
---

# Tools in this pack

One tool, `tmux-fleet`. It observes tmux sessions this pack did **not**
create and does not own, which is the fact that shapes every decision below.
One verb, `create`, adds a session of its own -- and everything about how it
is fenced follows from the same fact: the fleet it lands in belongs to
somebody else.

Run `tmux-fleet --help` for the complete, agent-facing listing (every verb,
its arguments, what it returns, and which verbs are model-backed), and
`tmux-fleet <verb> --help` for one verb. This card tells you what `--help`
cannot: the judgment and the safety context.

**What this pack assumes is on PATH beyond the engine's pinned base list:**
`tmux`. The tool is a tmux client and exits non-zero naming it when it is
absent -- it never degrades to a guess. It also carries a **pack-private
venv** (`.venv/` at the pack root) because its plumbing dependency,
[tmux-kit](https://github.com/bkrabach/tmux-kit), is not in the base list;
`bin/tmux-fleet` execs that interpreter rather than whatever `python3` the
turn PATH happens to resolve to. If the venv is missing the shim exits
non-zero and prints the one command that builds it. It will not build one
mid-turn: a tool that silently provisions itself is a fallback wearing a
helpful face.

**The AI substrate is a shared machine service, not a dependency of this
pack.** The two model-backed verbs (`triage`, `interpret`) execute through
`amplifier-agent`, which is expected already installed and configured on the
machine's PATH. Configure it once and every smart tool on the machine shares
it; the eight deterministic verbs need none of it and run with no substrate
configured at all. Invoked without a working `amplifier-agent`, a smart verb
**fails saying exactly that and how to configure it** -- never a silent
fallback to a deterministic approximation.

**Credentials:** none. This pack talks to the local tmux server over its own
socket as the invoking user. There is no token and nothing to rotate. It
reads no configuration file unless a deployment creates one -- see
[Advanced: choosing the tmux socket](#advanced-choosing-the-tmux-socket),
which normal use never needs.

## `tmux-fleet` -- fleet observation, and fenced input

Named `tmux-fleet`, **not** `tmux` or `fleet`. The engine refuses duplicate
tool names across packs, but it cannot know what the base PATH already holds
-- `tmux` itself is on that PATH, and shadowing it would be catastrophic and
silent. Prefixing away from an existing binary is the pack author's job, not
the loader's.

Ten verbs:

| Verb | What it answers |
|---|---|
| `socket` | Which tmux socket this tool reads, and on whose authority |
| `sessions` | Everything running, each with a short sliver and a prompt classification |
| `attention` | Where to look first, ordered -- a prior, not a verdict. **Deterministic.** |
| `read <session>` | What one session has actually been doing, with an honest bound |
| `triage` | Fleet-wide: what needs a human and why, structured. **Model-backed.** |
| `interpret <session>` | What this one session's state/output means, structured. **Model-backed.** |
| `send <session>` | Types into a session. **Refuses without `--confirmed`.** |
| `create <name>` | Starts a NEW detached session. **Refuses without `--confirmed`.** Refuses a name already in use. |
| `doctor` | Is tmux present and the socket reachable? Reports; a problem IS its success. |
| `exit-code <session>` | The exit status a finished session's process left behind |

**Run `socket` first whenever a fleet comes back empty.** "This machine has
no sessions" and "this tool is pointed at the wrong socket" look identical
from the outside, and `socket` is what tells them apart without running a
listing whose emptiness is the thing in doubt.

**stdout is always one JSON document.** Errors and refusals go to stderr and
never to stdout, and the exit code carries the distinction: `0` success, `2`
refusal (unconfirmed write, unknown session, argument over a cap), `1`
read/agent failure (no tmux, tmux errored, or the substrate a smart verb
needs was unavailable).

### Two verbs are model-backed; the other eight are not

Only `triage` and `interpret` run through the AI substrate. `triage` reads
the whole fleet and returns a structured judgment of what plausibly needs a
human and why; `interpret <session>` does the same for one session's state
and recent output. They exist because a mechanical last-line classification
cannot tell "wedged at an error" from "parked on purpose."

**`attention` is NOT model-backed -- it is deterministic.** It ranks where to
look first mechanically. Do not describe `attention` as an AI judgment, and
do not describe `triage`/`interpret` as if they ran with no substrate: when
the substrate is absent they fail loudly and name the remedy, and reporting
their absence as an empty or degraded result would erase exactly the signal
the fence exists to preserve.

### `at_prompt` is tri-state, and must stay tri-state

`"yes"` / `"no"` / `"uncertain"`. **Never treat it as a bool and never
collapse `"uncertain"` into `"no"`.** An empty or unreadable pane, or a
trailing bracketed note with no recognizable prompt token before it, comes
back `"uncertain"` **on purpose**. An honest "not sure" beats a confident
wrong answer; say so in whatever you report rather than picking a side.
`at_prompt_reason` explains every classification -- quote or summarize it
whenever you report an uncertain or surprising case.

This is a heuristic over the pane's last non-blank line, with known edges
that are documented rather than papered over:

- A **full-screen TUI** (vim, htop, a pager, an interactive menu picker)
  blocked waiting for a keypress is **not recognized** and comes back `"no"`
  even though it may badly need a human. This is the single biggest blind
  spot in the pack.
- A command's own output that happens to end in `$`, `#`, `%`, or `>` is a
  possible false positive.

It is still the right default signal. Just never treat `"no"` as certainty.

### A bracketed note at a prompt is intent, typed by a human

An operator types a `[note]` directly at a parked prompt and never presses
Enter -- the note IS the prompt line's content. Shapes seen in the wild:
`> [waiting on review]`, `[triage]> [done until Monday]`.

The classifier strips a trailing `[...]` before looking for a prompt token,
so `[triage]>` is still recognized as a prompt ending in `>`, and surfaces
the note in the `annotation` field. **A populated `annotation` means a human
parked this session deliberately and said why -- lead with that note; do not
re-derive intent by guessing at pane content.**

### `read --lines N` is history depth, not a total (the quirk that bites)

`read --lines N` is tmux's "N lines of history *before* the visible screen."
The visible screen always comes along. So a `--lines 5` read legitimately
returns far more than five lines, and **`lines_returned` must never be
compared against `history_lines_requested` to judge completeness.** Getting
back more than you asked for is normal and is not evidence of anything.

The honest test is against `history_size` (lines actually retained before the
visible screen), and the tool does it for you -- see completeness below.

### The default listing is a sliver -- read deep before characterizing

`sessions` captures a short sliver per session: enough to classify the last
line, **not** enough to know what a session has been doing. `read <session>
--lines N` accepts up to a bounded maximum (see `tmux-fleet read --help` for
the number). Asking for more than that maximum is **refused, not silently
capped** -- a caller who asked for more than they got must be told.

**Read deep before describing what a session is doing.**

### Never copy this tool's field names into anything a human reads

`at_prompt`, `last_line`, `idle_seconds`, `_completeness`, `bucket`, and every
other bare identifier in this card are internal plumbing for YOU to reason
with. They are not sentences. A field name pasted into a summary that reaches
a person is a debug leak, not a description.

Anything a human reads must be plain English describing what actually needs
them -- "the database migration session has been sitting at a shell prompt for
forty minutes with no new output" -- never a restated field name or a value
pasted out of JSON. If you catch a field name creeping into prose you are
about to write, stop and translate it first.

## Completeness honesty, as a convention this pack implements

Every list answers **"is this everything?"** in the response itself.

`sessions` and `attention` carry a `_completeness` block stating the session
count, that enumeration covers **every session on the socket this tool
actually read** (named verbatim, never "the default socket"), and --
explicitly -- what is **out of scope** rather than absent: sessions on
another socket (`--socket-dir`), under another user, or inside a container.
Those are invisible here and are *not* counted as zero.

**A socket that cannot be read is an error, never an empty fleet.** A listing
that fails to read raises rather than returning `0`; "there is nothing there"
and "I could not look" are different answers and must never render
identically. When a delegated read (such as harness labelling) fails, the
response says so in its own field with a reason -- rather than reporting every
session's harness as `unknown`, which would be indistinguishable from having
genuinely failed to recognize each one. If such a field is present, say the
labels are missing; do not report the fleet as unlabelled.

`read` carries `history_lines_requested`, `lines_returned`, `history_size`,
`pane_height`, and a `complete` flag that is true **only when the requested
depth reached the beginning of retained scrollback**. When it is false the
note names exactly how many lines lie beyond the window. **If `complete` is
false, say so in whatever you report.**

`attention` additionally states that its counts are computed over every
session **before any filter**, so the filtered view can always be compared
against the whole fleet, and it names its own blind spot (the full-screen TUI
case above) inside the block.

### The rollup is a triage order, not a verdict

`attention` ranks where to look first when there are many sessions and limited
time. It is a **prior**, never a conclusion about any one session. A session
ranked low can still need a human; a session ranked high may be one an
operator parked on purpose. Nothing in the rollup substitutes for actually
reading a session, and the ranking itself must never be reported as if it
settled whether a session needs a human.

## `create` -- the one verb that adds a session

```
tmux-fleet create <name> --cwd <dir> [--command <cmd>] --confirmed
```

Creates a **new detached session** with a working directory, and optionally
types an initial command into it. A session exists to do work, not to sit at
an empty prompt, so `--command` is the normal case rather than an extra.

**It refuses without `--confirmed`** -- the same per-invocation fence `send`
carries, for the same reason: this is the only verb that changes what the
fleet contains, and it lands in the owner's live working environment. There
is no session-wide unlock and no environment variable that turns it off.

### A name already in use is REFUSED -- creation is not idempotent

If a session by that name exists, `create` refuses. It does **not** attach to
it, reuse it, rename around it, or clobber it. This is a decision, not a
missing feature: silently handing back a session that merely shares a name
would mean returning work that may belong to somebody else as though this tool
had made it, and that is the one failure here with **no undo**.

The refusal is written to be acted on: it reports the existing session's
working directory, when it was created, when it last did anything, its harness
label, whether it is sitting at a prompt, and whether this pack's own audit
log has any record of creating it. **"No record" means no record -- it is NOT
proof the session belongs to someone else**; the log may have rotated or been
redirected. Say that distinction out loud when you report a collision.

What to do with a refusal: pick a different name, or decide deliberately to
use the existing session -- `read` it first, and `send --confirmed` if you
mean to type into it.

### Success is read back from tmux, not inferred from exit 0

After the spawn, the tool **re-enumerates and looks for the exact name**.
tmux can exit `0` and still have named the session something else, so an
unconfirmable create is reported as a failure rather than a success. If the
initial command could not be delivered (the shell never drew a prompt in
time, or the command was over the byte cap), the **session still exists** and
the response says plainly the command was not run. Report both halves;
"created" alone is not the whole answer in that case.

### It is rate-guarded, and there is no undo verb

A rolling guard, computed from this pack's own audit log, refuses past a
ceiling of creations per window. An agent retrying in a loop can create
sessions far faster than a human notices, and **this pack has no verb that
removes one**. There is deliberately no flag or environment variable that
raises the ceiling.

## `send` -- typing is not running

`send` types into a session and is fenced exactly like `create`: it
**refuses without `--confirmed`**, per invocation, with no session-wide or
environment unlock. Text is delivered as argv (never a shell string) and
named keys come from a closed allowlist; anything outside it is refused. The
snapshot returned after a successful send is taken immediately and is **not**
a completion signal -- a session that takes time to react will not have
reacted yet.

**Typing text into an input line is not the same as running it.** `--text`
alone types and does **not** submit: correct for filling a field you are not
ready to send, and catastrophic for a command -- the text sits on the input
line looking sent and prefixes whatever is typed next, fusing two commands
into one. A COMMAND therefore uses `--submit`, which types the text and
presses Enter once, in one call:

```
tmux-fleet send <session> --text 'make test' --submit --confirmed
```

The response reports the outcome by name -- `armed` (nothing executed),
`submitted` (the text was seen to land, then seen to go), or `uncertain` (an
Enter went out; the readback could not confirm the target took it). **Read
that outcome back and report it; never assume a `--text` alone ran, and never
render `armed` as "sent."**

## Negative space -- what this tool will not do, on purpose

- **It will never kill, rename, or respawn a session.** There is no such verb.
  This pack largely observes a fleet it did not create; those sessions belong
  to people and processes that did not ask it for lifecycle management. Do not
  look for a workaround -- this is a boundary, not a gap.
- **`create` only ever adds, and there is no verb that undoes it.** It cannot
  land on an existing session (a name collision refuses) and it cannot remove
  one. That asymmetry is deliberate and it has a real cost: a session this
  tool creates can only be torn down by a human. Both tmux incidents on the
  hosts this design came from were teardowns, which is why teardown stays a
  human action. Say so when you create something -- do not imply you can clean
  it up afterwards.
- **It will not send input without `--confirmed`.** Writes are deny-by-default.
  An unconfirmed keystroke into somebody else's session is indistinguishable
  from sabotage, so consent is required **per invocation** -- no session-wide
  unlock, no config flag, no environment variable that turns it off.
- **It will not prefix-match a session name.** tmux would happily resolve `db`
  to `db-migration`; this tool refuses an inexact name and lists what is
  actually present. Typing into the wrong session because a name was
  abbreviated is exactly the failure `--confirmed` exists to prevent.
- **It will not silently cap a read.** Over the ceiling is a refusal.
- **It does not push.** Everything is a poll. There is no watch mode, no
  subscription, and no event stream -- if you need to know whether something
  changed, poll again and compare.
- **It does not judge whether a session matters to a person.** Buckets and
  ordering are mechanical; the model-backed verbs advise, they do not decide.
  Whether a human should be interrupted is consumer policy and lives in the
  consumer's guidance, not in this tool.

## Every write attempt is written down

`send` and `create` each append one JSONL line per attempt -- **refused and
delivered both** -- to `~/.local/state/tmux-fleet/input-audit.jsonl` (override
with `TMUX_FLEET_AUDIT_LOG`). A refusal that left no trace would make the
deny-by-default fence unauditable. If the audit line cannot be written, the
attempt is refused rather than performed unrecorded.

That log is also load-bearing for `create`: its rate guard is computed from
it, and the "our records" line in a collision refusal is read out of it. A log
that has been rotated or redirected therefore makes the ownership question
unanswerable rather than answered "no" -- which is why the refusal says "no
record" and not "not ours."

## Advanced: choosing the tmux socket

**Skip this section unless a fleet came back empty that you know is not
empty.** The default is correct for an ordinary deployment, and nothing here
is part of normal onboarding or first use.

tmux servers are reached through a socket under a `TMUX_TMPDIR`-style
directory: the server lives at `<dir>/tmux-$UID/default`. Most machines only
ever use tmux's compiled-in default, `/tmp`. Some operators point their
interactive shell somewhere else (`~/.tmux` is the common choice, to keep
sockets out of a shared, world-writable `/tmp`).

This pack resolves that directory **explicitly**, in this order:

| Priority | Source |
|---|---|
| 1 | `--socket-dir DIR` on the invocation |
| 2 | `socket_dir` in `~/.config/tmux-fleet/config.json` (path overridable with `TMUX_FLEET_CONFIG`) |
| 3 | `TMUX_KIT_SOCKET_DIR` environment variable |
| 4 | tmux's system default, `/tmp` |

```json
{ "socket_dir": "~/.tmux" }
```

**The ambient `TMUX_TMPDIR` and `$TMUX` are deliberately NOT consulted.** This
is the one surprising thing in this section, and it is a decision rather than
an oversight. A tool that auto-detects the ambient environment works on the
box where it was written and silently reads a different fleet on the next one
-- and worse, it reads a *different* fleet under a service manager than in the
author's shell, because a service inherits no login shell environment. So the
tool obeys configuration only, and **reports** any ambient value it declined
to honor (with the exact setting that would adopt it). Ignoring is not hiding.

Every underlying tmux invocation names its socket with an explicit `-S`; the
`socket` block reports the resolved directory, the source that decided it,
and -- when a server is actually running -- tmux's own confirmation of the
socket path. The completeness scope names that directory verbatim; it never
says "the default socket." A configured value that is unusable (blank, a
relative path, wrong JSON type, malformed, or unreadable) is **refused, never
repaired**.

## When this tool cannot do what you were asked

**Say so, explicitly, and say what you tried.** Do not approximate, do not
substitute a different action, do not quietly skip a step and report success.
A clear "I could not do X because Y" is a useful result: it says exactly where
the tool surface is thin, which is information worth having. A silently
degraded result destroys that signal and is worse than a failure.
