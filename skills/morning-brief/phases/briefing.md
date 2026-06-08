# briefing — quick orientation report

Compact (under 50 lines) report covering: schedule, urgent items, task health, remsleep follow-up, recent wiki changes (since last brief), upcoming (next 24h), plus chosen rituals.

Run on demand — the name reflects a typical use case (daily start-of-day), not a required cadence.

## Arguments

None.

## What to do

### 1. Gather

Invoke `/check` with no descriptor. The dispatcher fans out across every available template (status, tasks, calendar, slack, email — whichever are connected) in parallel and returns a merged report. Templates whose dependency is missing emit a one-line skip note; that's expected, not an error.

### 2. Remsleep follow-up

Check the latest `/remsleep` run (regardless of when it ran) by reading the most recent file in `artifacts/remsleep/`. If it exists:

- Surface the reflection questions in chat — render the full text + context + lean directly. The `agent_brain/about_user/reflections/questions.md` file is durable bookkeeping; the chat is the source of truth.
- Note any items flagged as "needs attention".

### 3. Recent wiki changes (since last brief)

Read entries from `artifacts/_changelog.md` newer than the last `/morning-brief` run timestamp (resolved by the dispatcher in step 2 of `SKILL.md`). Fallback: last 7 days if no prior run was logged. Summarize concisely — count + top themes, not a dump.

### 4. Upcoming (next 24h)

Check calendar for the next 24 hours. Flag meetings that need `/prep` or have no wiki context on attendees.

---

## Ritual blocks (active for Amalie's setup)

Two rituals are on: **project pulse**, **milestones**. Both fire when their config flag is `true`.

> Morning brief is pure orientation — no journal-style prompts. Removed 2026-05-20:
> - **Habit check-in** — cadence-table format wasn't useful. Habit pages still live in `agent_brain/about_user/habits/` for reference.
> - **Gratitude** — belongs in an evening ritual, not morning. No evening flow exists yet; re-enable on whichever skill owns that hook.
> - **Excitement** — briefly trialled as a forward-looking replacement for gratitude, then removed the same day. The morning brief should not prompt for journal entries at all.

### Ritual: Milestones (milestones: true)

Check `.claude/constitution/config.yaml`. If `milestones: true`:
- Read `agent_brain/about_user/milestones.md`.
- For every recurring entry, compute this year's instance (`MM-DD` → `YYYY-MM-DD`). For one-time entries, use the listed date directly. Skip rows where the date is `??` (unknown — flag in FYI once a week so they don't rot, but don't fire daily).
- For each dated entry, compute `days_until = entry_date − today`. If `0 <= days_until <= lead_days` (per row, defaulting from the lead-time table on the milestones page), surface it with a status tag:
  - **DAY-OF** (`days_until == 0`) — top of brief, never buried in FYI
  - **SEND TODAY** (`days_until <= 3` for flowers / express) — last-chance for same-day or 1-day delivery
  - **ORDER** (`days_until` inside lead window for the chosen action) — time to act
  - **PLAN** (`days_until` at the outer edge of the window) — prompt to confirm gift idea + add to shopping list
- Format each entry: `[STATUS] <person> — <type> in <N> days — <plan or "needs plan">`
- If nothing's in window: silent. Don't surface "no milestones today" — adds noise.

### Ritual: Project pulse (project_pulse: true)

Check `.claude/constitution/config.yaml`. If `project_pulse: true`:
- Pick one active project (rotate through them — track which was last surfaced in `agent_brain/about_user/project-pulse-rotation.md`).
- Rotation pool for Amalie:
  - Whichever client engagement she's currently staffed on (likely **Gro** once confirmed)
  - **AI-augmented consulting** (internal)
  - **Half marathon 2026**
  - **Spanish learning**
  - **Crochet — baby gifts**
- One-paragraph status: latest changelog entries touching this project, open tasks, anything blocked.
- Goal is one project gets daily mind-share without cycling through all of them.

---

## Output

Write a concise briefing (under 50 lines). Structure:

```
## Morning Brief — [date]

### Today's Schedule
[from /check calendar]

### Needs Attention
[urgent items from Slack, email, overdue tasks, remsleep "needs attention"]

### Tasks
[from /check tasks — P0/P1, overdue, stale]

### Milestones (if any in window)
- [STATUS] Person — type in N days — plan
- (omit section entirely if empty)

### Rituals
- Project pulse: [the one project in rotation today]

### FYI
[non-urgent updates, wiki changes]

### Upcoming (next 24h)
[preview of next 24h schedule, prep needed]
```

Keep it scannable. Bold the actions, not the context.
