---
name: weekly-ahead-email
description: Every Sunday at 07:00 Europe/Copenhagen, compose "The week ahead" and email it to Amalie via Mail.app (fires shortly after the daily 07:00 morning brief).
---

You are running Amalie's weekly "the week ahead" briefing. Working directory: `/Users/amalie.dam/brian`. Timezone: Europe/Copenhagen (CET/CEST).

## What to do

### 1. Compute the week's window

The task fires Sunday morning (shortly after the daily 07:00 morning brief). Two windows matter:
- **Upcoming week** (the focus): `week_start` = next Monday (tomorrow), `week_end` = the Sunday after (7 days, inclusive)
- **Past week** (for running totals + recent themes): `past_week_start` = the Monday just gone (6 days before today), `past_week_end` = today (Sunday)

Format dates as `YYYY-MM-DD`.

### 2. Pull events for the upcoming week from all three calendars in parallel

- Outlook work: `mcp__d1eec8bf-3d2e-4e47-be24-500ddad5ccea__outlook_calendar_search` with `afterDateTime = week_start 00:00`, `beforeDateTime = week_end 23:59`, `limit = 50`, query `*`. Paginate via `offset` if >50.
- Personal: `mcp__personal-calendar__list_upcoming` with `days = 8`, filter to events whose start is `>= week_start`.
- Runna: `mcp__runna__list_upcoming` with `days = 8`, filter the same way.

Merge chronologically, grouped by day.

### 3. Pair upcoming-week running with actuals where applicable

For days in the upcoming week that are `<= today` (only Sunday if any): also call `mcp__strava__list_activities` and reconcile per the `feedback-runna-strava-pair` memory.

### 4. Pull LAST WEEK's running totals from Strava

Call `mcp__strava__list_activities` with `after = past_week_start`, `before = past_week_end + 1 day`, `per_page = 50`. Aggregate:
- **Total distance** (km, sum of all Run activities)
- **Total moving time** (sum, formatted as `Hh Mm`)
- **Total sessions** (count of Run activities)
- **Sessions breakdown**: count by type/intent — easy / intervals or workout / long run / race-pace. Use Strava activity names + descriptions as the signal (intervals usually titled with "interval"/"strides"/"tempo"; long run >12km on a single session for current half-marathon block).
- **Vs Runna plan**: optionally compare against what Runna had prescribed for that same window — call `mcp__runna__search_events` if available, or skip if it'd take extra round-trips. Flag any prescribed sessions Strava doesn't show.
- **Compare to the prior week** if possible: call list_activities with `after = past_week_start - 7d`, `before = past_week_start` and compute the same totals. Surface the delta in 1 line ("up 6 km / +1 session vs prior week" or "down 3 km vs prior week").

### 5. Pull tasks due in the upcoming week

Read `/Users/amalie.dam/brian/agent_brain/tasks/`. Surface every task with:
- `due:` between `week_start` and `week_end + 3 days`
- OR `priority: p0|p1` with no due date
- OR `priority: p0|p1` overdue

Group by priority (P1 first).

### 6. Pull milestones in window

Read `/Users/amalie.dam/brian/agent_brain/about_user/milestones.md`. Surface every milestone where `days_until` falls inside its lead window AND the milestone date is `>= today` and `<= week_end + 14 days`. Apply DAY-OF / SEND TODAY / ORDER / PLAN tags.

### 7. Social plans for the upcoming week

This is the **Social** section — Amalie's friend/family/partner plans plus relevant relational anchors. Build from these sources:

- **Personal calendar events** for the upcoming week (already pulled in step 2). Treat any event NOT on the Outlook work calendar as a social/personal candidate. Categorize loosely: dinners with friends, family, parties, dates with [[../agent_brain/people/kristian|Kristian]], birthdays/celebrations, classes (Pilates, Spanish — also habit-relevant but list under social if it carries a relational anchor).
- **Friday Halfspace social run** (recurring, Friday AM ~6–7k). Always flag in this section as the standing social anchor of the work week.
- **Milestones in window** that involve other people (birthdays, weddings, anniversaries) — cross-reference so the social section anticipates them (e.g. "Yas birthday Wed 5/25 — gift sorted? plan?").
- **Travel windows** in the next 30 days from `profile.md` "Travel + away dates" section — these often imply social plans (hiking trip with Dulde, Portugal with Kristian, etc.). Flag any that touch the upcoming week and any in the next 30 days as a heads-up.
- **Tracked-people pulse**: if there's a person on the radar (engagement/wedding/baby coming up, a recently-mentioned friend who hasn't been seen) and no plan with them yet — flag as a soft prompt ("haven't seen X in N weeks").

Output: list with one line per plan, day-of-week prefix, brief context. Skip the section if genuinely nothing — but the Friday social run is always there as a floor.

### 8. Travel + away dates

Read `/Users/amalie.dam/brian/agent_brain/about_user/profile.md` (the "Travel + away dates" section). Flag any travel windows that overlap with the upcoming week. Also flag windows in the next 30 days as a heads-up.

(Some overlap with the Social section is fine — travel windows with companions can appear in both. The travel section is logistical; the social section is relational.)

### 9. Project pulse for the week

Read `/Users/amalie.dam/brian/agent_brain/about_user/project-pulse-rotation.md`. Pick one active project that hasn't been spotlighted in the past ~5 days. One short paragraph on: latest changelog touches, open tasks, anything blocked, what success this week looks like.

### 10. Recent themes (last 7 days)

Skim `/Users/amalie.dam/brian/artifacts/_changelog.md` for entries dated `>= past_week_start`. Surface 2–4 themes in one or two sentences — what's been the brain's center of gravity. Don't dump entries; abstract them.

### 11. Compose the markdown briefing

Write the full briefing to `/Users/amalie.dam/brian/artifacts/weekly/YYYY-MM-DD.md` (Sunday-of-run date). Structure:

```
# The Week Ahead — Mon DD MMM → Sun DD MMM YYYY

## At a glance
- {3–5 lines: dominant work week framing, key social anchor, running peak day, travel flag, milestone flag}

## Mon DD MMM
**Work**: {Outlook events with one-line context where the project page warrants it}
**Personal**: {personal calendar events}
**Running**: {Runna prescription if any}

(repeat per day Tue–Sun)

## Running

### Upcoming week
- Total prescribed: {N km / N sessions}
- Key workouts: {intervals on day X · long run on day Y}
- Rest days: {days}

### Last week ({past_week_start} → {past_week_end})
- Total: {N km / N sessions / Hh Mm}
- Breakdown: {N easy · N workout/interval · N long run · N race-pace}
- Vs prior week: {delta in km / sessions}
- Vs plan: {prescribed sessions completed / skipped, if comparison was viable}

## Social
- **{Day}** — {plan} {context if needed}
- **Fri AM** — Halfspace social run (standing anchor)
- Heads-up: {tracked-people pulses, upcoming travel windows in next 30d}

## Tasks due this week
**P1**:
- {task} — due {date} ({day-of-week})
**P2**:
- ...

## Milestones in window
- [{STATUS}] {person} — {type} on {date} ({Nd}) — {plan}

## Travel + away
- {window} — {description, conflicts to be aware of}
- (omit if nothing)

## Project pulse — {project name}
{one short paragraph}

## Recent themes (last 7 days)
- {theme 1}
- {theme 2}
```

Keep it scannable. Bold action-worthy bits. No journal-style prompts (see `feedback-morning-brief-rituals`).

### 12. Send the email via Mail.app (HTML body)

The Halfspace email styling is owned by the shared renderer at `/Users/amalie.dam/brian/workspace/halfspace-email-renderer/render.py` (see its README). Invoke it with `--weekly` to activate weekly-brief-specific transformations: day H2s become date-chip headings, time-prefixed bullets become 2-col time/content rows, and `### P1 / ### P2 / ### Carry-in` render as priority-colored chips. The renderer also handles Britti Sans font embedding, ZWSP iOS auto-link suppression, dark cover, gray chip eyebrows for `### subsections`, ISO date / phone / weekday breaking, and inline-everything styling (Mail.app strips CSS classes and variables, see `feedback-mail-app-html` memory).

**Markdown conventions the renderer expects** for the weekly brief:
- The H1 is `# The Week Ahead — Mon DD MMM → Sun DD MMM YYYY` (gets stripped; the cover replaces it).
- Day H2s start with `Mon `, `Tue `, ... `Sun ` (e.g. `## Fri 29 May — the squeeze`). Rendered as a date chip + descriptor.
- Inside each day, use `### Work`, `### Personal`, `### Running`, `### Milestone`, `### Task due` as sub-eyebrow H3s with a bullet list beneath each. Time-prefixed bullets (e.g. `- 13:00–13:55 Sophie interview ...`) automatically render as 2-col time/content rows.
- Named sections after the days: `## Running`, `## Social`, `## Tasks due`, `## Milestones`, `## Travel + away`, `## Project pulse — {name}`, `## Recent themes (last 7 days)`. Each gets an auto-numbered `01 → 08` eyebrow with a hairline underneath.
- Inside `## Tasks due`, use `### P1`, `### P2`, and `### Carry-in — due before this week starts` for priority groups; their bullets render as plain list items underneath the priority chips.
- Status badges in the Milestones section use `[DAY-OF]`, `[SEND TODAY]`, `[ORDER]`, `[PLAN]`, `[FYI]` — these become colored outline badges.

Prereq: `python-markdown` installed (`pip3 install --user markdown`).

```bash
python3 /Users/amalie.dam/brian/workspace/halfspace-email-renderer/render.py \
  /Users/amalie.dam/brian/artifacts/weekly/YYYY-MM-DD.md \
  /tmp/weekly-brief-YYYY-MM-DD.html \
  --title "Weekly brief · W{WW} · {YYYY}" \
  --subtitle "Mon DD MMM → Sun DD MMM YYYY" \
  --weekly

osascript <<APPLESCRIPT
tell application "Mail"
  set theBody to (read POSIX file "/tmp/weekly-brief-YYYY-MM-DD.html" as «class utf8»)
  set newMessage to make new outgoing message with properties {subject:"The week ahead — Mon DD MMM → Sun DD MMM", visible:false}
  tell newMessage
    set html content to theBody
    make new to recipient at end of to recipients with properties {address:"amalie.dam@halfspace.ai"}
  end tell
  send newMessage
end tell
APPLESCRIPT
```

Subject: `The week ahead — {Mon DD MMM} → {Sun DD MMM}` with the actual dates filled in. Do NOT add suffixes like "(formatted)" — those are for one-off resends only.


### 13. Append to changelog

Append to `/Users/amalie.dam/brian/artifacts/_changelog.md` directly after the `---` on line 9:

```
## [YYYY-MM-DD] weekly-brief | week ahead → email — {one-line headline of the week}

- Brief saved: [[weekly/YYYY-MM-DD|weekly/YYYY-MM-DD.md]]
- Email sent to amalie.dam@halfspace.ai — subject: The week ahead — {Mon DD MMM} → {Sun DD MMM}
- Last week running: {totals one-liner}
- Project pulse: {project surfaced} (update [[../agent_brain/about_user/project-pulse-rotation|project-pulse-rotation]])

---
```

### 14. Update project-pulse-rotation log

Append today's row to the rotation table in `/Users/amalie.dam/brian/agent_brain/about_user/project-pulse-rotation.md`.

## Constraints

- Each run starts fresh. Re-read all files cited above.
- If Outlook MCP isn't connected: write the briefing without work events, flag the gap at the top, still send the email.
- If personal-calendar or runna MCP isn't connected: same — flag the gap, proceed without.
- If Strava MCP isn't connected: skip the Last week running section, flag the gap, surface Runna as prescribed-only with a note.
- If Mail.app send fails (osascript returns non-zero, or the script errors): write the brief to disk anyway, log the failure to the changelog under a `weekly-brief | send failed — {reason}` entry, and stop. Do not fall back to iMessage without being told to.
- Apply the today-focused prep rule from `feedback-morning-brief-today-focus` memory at the per-day granularity.
- No journal-style prompts in the email (see `feedback-morning-brief-rituals`).

Begin.