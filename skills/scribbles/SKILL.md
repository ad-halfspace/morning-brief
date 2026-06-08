---
name: scribbles
description: "Sweep the Apple Note \"Scribbles\" (case-sensitive) for new items captured since the last run, classify each as task/event/note, and file them into the brain. Fires automatically at the start of /morning-brief; can also be run on demand."
---

# /scribbles — Apple Note "Scribbles" inbox sweep

Treat the Apple Note named `Scribbles` (capital S — Apple Notes is case-sensitive) as a freeform inbox. Each line is a captured thought. The skill reads the note, diffs against the last snapshot, classifies new items, and files them.

**Argument**: optional note name (default `Scribbles`). Example: `/scribbles MyOtherNote`.

## Procedure

### 1. Read the note

Call `mcp__Read_and_Write_Apple_Notes__get_note_content` with `note_name` = the argument or `Scribbles`. If the call errors with "Invalid index", the name is wrong or case mismatched — list notes via `mcp__Read_and_Write_Apple_Notes__list_notes` (limit ~300) and ask the user which one to use, then proceed.

### 2. Parse the items

The result is HTML. Extract each `<li>...</li>` body, trim whitespace, drop empty entries. The result is a list of raw item strings.

If the note has no `<li>` items (different structure), fall back to: take all non-empty lines from the visible text, skip the title line.

### 3. Diff against snapshot

Read `artifacts/scribbles/last-snapshot.md`. The body is one item-string per line (after a `---` separator below the frontmatter).

- **New items** = items in current parse that are not in snapshot (exact string match after trim).
- **First run** = if no snapshot file exists, treat *all* items as new.

If no new items, log a one-liner ("Scribbles: no new items since {last_run}") and stop.

### 4. Classify each new item

For each new item, pick one of these classes using context cues. Be generous with judgement — the user is writing shorthand.

| Class | Cues | Action |
|---|---|---|
| **task — clear** | Imperative verb (buy, book, call, design, fix, send, draft) or matches obvious patterns ("Buy X", "Book Y", "X tshirt" with a known context) | Create task file directly. |
| **event** | Has a date + time + party-size pattern, e.g. "Sexy fish (June 25, 4 people, 19:00)" | Surface to user — usually wants a task (book it) plus optionally a calendar event. Ask which. |
| **pure note** | A reflection, a phrase, an idea with no actionable verb | Append to `agent_brain/about_user/scratch.md` (create if missing) with date prefix. |
| **ambiguous** | Can't tell | Batch into a single user prompt at the end. |

Cross-reference the brain when classifying:
- If the item mentions a known event/trip (check personal calendar for keyword hits) → link the task to that event and set the due date to a sensible lead time (default 4 weeks before for procurement/design tasks, 1 week for bookings).
- If the item mentions a known project (check `agent_brain/projects/` + `agent_brain/references/`) → set `project:` accordingly.
- Honour known patterns from prior sweeps (see § Domain shortcuts).

### 5. Create the artifacts

For each classified item:

- **Task**: write a task file at `agent_brain/tasks/{slug}.md` using the format from `/create-task` (frontmatter: type/summary/status/priority/due/owner/project/category/source/created/updated/tags). Set `source: scribbles-note`. Include an "Open questions" section with the obvious unknowns.
- **Event**: ask the user once whether to create just a task, just a calendar event, or both. Then act.
- **Pure note**: append to `agent_brain/about_user/scratch.md` as `- [YYYY-MM-DD] {text}`.

Do not duplicate: before creating a task, check `agent_brain/tasks/` for a slug collision and bail with a one-line note if so.

### 6. Update the snapshot

Overwrite `artifacts/scribbles/last-snapshot.md` with:

```
---
last_run: YYYY-MM-DD
note_name: Scribbles
item_count: N
---

<one item-string per line, all current items from the note>
```

The snapshot is the full current state, not a delta. This makes diffing on the next run a simple set-difference.

### 7. Offer to clear processed lines (optional)

After filing, if anything was processed, ask the user: "Clear the processed lines from the Apple Note?" If yes, call `mcp__Read_and_Write_Apple_Notes__update_note_content` with the note's content minus the processed `<li>` entries. If no, leave the note untouched — duplicates are blocked by step 5's slug check anyway.

Default to **leaving the note untouched** unless the user opts in.

### 8. Update tracking

Append to `artifacts/_changelog.md`:

```
## [YYYY-MM-DD] scribbles | Swept N item(s): {brief summary}
```

### 9. Report

```
## Scribbles sweep — YYYY-MM-DD

**New items**: N
**Filed**:
- [[task-slug-1]] — {summary}
- [[task-slug-2]] — {summary}
- scratch.md: {pure-note text}
**Skipped** (ambiguous): {if any, listed with rationale}
**Snapshot**: refreshed (item_count = M)
```

## Domain shortcuts

These shortcuts encode patterns Amalie has confirmed. Add to this section as new patterns emerge.

- **"hut girl summer"** in an item → hiking-trip merch context. Link to the next "Hiking med girlies" calendar event; due = trip_date − 4 weeks.
- **"DHL"** + tshirt/merch → DHL Stafetten (annual Copenhagen relay, late August). Project: `halfspace`. Due = relay_date − 3 weeks. Confirm the year's exact date with the user if not in calendar.
- **Restaurant + date + party-size** → personal booking. P1, due ~1 week from capture. Always ask about calendar event creation.
- **Gift idea for a person** (pattern: `<Name> gave: <item>`, `<Name>: <item>` as gift idea, `gift for <Name>: <item>`) → append to the recipient's page in `agent_brain/people/<slug>.md` under a `## Gift / activity ideas for <name>` section (create if missing). If the recipient is a child of someone tracked (e.g., Oskar = Ida2's son), the slot lives on the parent's page with a section header naming the child. Never put non-crochet gifts on `projects/crochet-baby-gifts/` — that project is crochet-only. See [[../../../agent_brain/about_user/personal-infrastructure|personal-infrastructure]] for the "gift ideas per person" architecture.

## Notes

- Apple Notes is case-sensitive. Always read with the exact title; if unsure, list and confirm.
- Don't auto-clear the note. Amalie's pattern is to iterate on captured items; clearing destroys the audit trail.
- When invoked from `/morning-brief`, run silently if there are no new items (no section, no skipped section). When invoked directly, always print the report header even if N = 0.
- For ambiguous items, batch them into one prompt at the end of the run with multi-select — never block sweep progress on per-item Q&A.
