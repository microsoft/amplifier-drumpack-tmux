---
automation:
  name: Fleet Observation Drill
  # Ships DISABLED, like every exemplar. Flip to true once you have verified a
  # turn actually runs against your workspace (drumbeat doctor -> the pack is
  # declared; bin/tmux-fleet --help works on the turn PATH).
  enabled: false
  trigger:
    type: schedule
    # A quiet heartbeat. `every N minutes` is recomputed on each evaluation.
    expression: every 30 minutes
  # `urgent-only`: the drill does its work and stays quiet -- nothing is pushed
  # unless the agent's final reply opens with an `URGENT: <reason>` marker. A
  # healthy fleet-observation path is not news; a BROKEN one is. This is the
  # "notify-quiet" shape: the judgment turn still runs, only the push is
  # withheld.
  notify: urgent-only
  # This automation needs this pack's tool on PATH. The engine aborts loudly at
  # the requirements gate unless `amplifier-drumpack-tmux` is listed in the
  # workspace's drumpacks.txt, so a copied-but-unwired drill fails visibly
  # rather than running toolless.
  requires:
    - tmux-fleet
  # Steps are structured frontmatter data (contracts/automation-file.v1.md): an
  # ordered list, each with an `id` (identity in run records), a `prompt` (the
  # whole behavior), and an optional `label`. The body below is for humans and
  # is never parsed for execution. This drill is READ-ONLY: it exercises the
  # `sessions` and `read` verbs and never sends input or creates a session.
  steps:
    - id: resolve-socket
      label: Confirm which fleet we are looking at
      prompt: |-
        Run `tmux-fleet socket` and, in one plain sentence, state which tmux
        socket this drill is reading and on whose authority (the resolved
        directory and the source that decided it). If the tool reports an
        ambient value it declined to honor, mention it. Do NOT paste the tool's
        raw field names into your reply -- describe it in plain English.

        If `socket` cannot run at all (for example the pack-private venv is
        missing, or `tmux` is absent), STOP here and begin your reply with
        `URGENT: ` followed by the exact remedy the tool or shim printed -- a
        drill that cannot even see the fleet is the one thing worth a push.
    - id: list-sessions
      label: Observe the fleet read-only
      prompt: |-
        Run `tmux-fleet sessions`. Report, in plain English:

        - How many sessions exist on the socket named in the previous step, and
          that this count is every session on THAT socket -- not every session
          on the machine (other sockets, other users, and containers are out of
          scope, not zero).
        - Any session whose prompt state came back "uncertain": name it and
          quote the reason. Never collapse "uncertain" into "not waiting" -- an
          honest "not sure" is the point.
        - Any session carrying a human-typed bracketed note: lead with that
          note; it means an operator parked the session deliberately and said
          why.

        A socket that could not be READ is an error, not an empty fleet. If the
        response says the fleet could not be read (rather than that it is
        genuinely empty), begin your reply with `URGENT: ` and say so.
    - id: read-deep
      label: Read one session deeply and honour the completeness bound
      prompt: |-
        Pick the session that most plausibly wants a human (a non-empty
        bracketed note, or an "uncertain"/quiet-at-a-prompt state). If there is
        genuinely nothing running, say so plainly and skip to the verdict.

        Otherwise run `tmux-fleet read <session>` with a generous history depth
        and summarise what that session has actually been doing in two or three
        plain sentences. Do NOT judge completeness by comparing how many lines
        you asked for against how many you got back -- getting more than you
        asked for is normal. Use the tool's own `complete` signal instead: if it
        reports the read did not reach the beginning of retained scrollback, say
        so and say how much lies beyond the window.
    - id: verdict
      label: Emit the quiet health verdict
      prompt: |-
        Emit one final message: the fleet-observation path is healthy, plus the
        one-line fleet summary from the previous steps. Keep it plain English --
        no tool field names.

        Prepend `URGENT: <reason>` ONLY if an earlier step already found the
        observation path itself broken (venv/tmux missing, or a socket that
        could not be read). A busy fleet, an idle fleet, or a session parked on
        purpose is NOT urgent -- this drill checks that the eyes work, it does
        not decide whether any session deserves a human. That judgment is
        consumer policy and lives elsewhere.
---

A read-only heartbeat that confirms the tmux-fleet observation path is healthy:
it resolves the socket, lists the fleet, and reads one session deeply, honouring
the tool's tri-state prompt classification and completeness bounds. It runs
`notify: urgent-only`, so it stays silent unless it cannot see the fleet at all
-- the one condition worth waking someone for. It sends no input and creates no
session. Every step lives in the frontmatter `steps:` list above; this body is a
human-facing description only.
