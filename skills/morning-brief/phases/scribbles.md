# scribbles — Apple Note inbox sweep

Sweep the Apple Note "Scribbles" for new items and file them as tasks/events/notes before the briefing renders. Lets newly captured items show up in the same morning's task list and calendar.

## Arguments

None.

## What to do

Invoke `/scribbles` with no argument. The skill reads the Apple Note `Scribbles`, diffs against `artifacts/scribbles/last-snapshot.md`, classifies new items, and files them.

When fired from this phase, `/scribbles` runs in **quiet mode**: if N = 0 new items, it emits no section at all. If N > 0, it surfaces a single line per filed item under a `### Scribbles inbox` header in the briefing output.

## Why this phase runs first

Phase order is `scribbles → briefing → research → feeds → news`. Items captured in Scribbles overnight get filed as tasks *before* the briefing's `/check tasks` step, so they appear in today's task health view rather than being invisible until tomorrow.

## Output

If N == 0: nothing rendered.

If N > 0:

```
### Scribbles inbox (N new)
- Filed [[task-slug]] — {summary} (P{n}, due {date or —})
- Logged to scratch: {pure-note text}
- Skipped: {ambiguous text} — reason
```

Concise; the user can `/scribbles` directly to see the full report.
