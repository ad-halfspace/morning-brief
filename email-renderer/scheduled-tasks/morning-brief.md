---
name: morning-brief-imessage
description: Run /morning-brief at 07:00 Europe/Copenhagen on weekdays (Mon-Fri) and send a tight ~10-line summary to Amalie via iMessage + a Halfspace-styled email.
---

You are running Amalie's morning brief automation. The working directory is `/Users/amalie.dam/brian`. Today is whatever today actually is (CET/CEST, Europe/Copenhagen).

## What to do

1. **Run the briefing phase of `/morning-brief`** — read `/Users/amalie.dam/brian/.claude/skills/morning-brief/phases/briefing.md` and follow it. Run the `briefing` phase plus a **lightweight feeds pull** (see step 4b below). Skip the full feeds phase (no raw/ staging, no auto-ingest) — only fetch the newest issue of each active feed for inline surface. Skip research + news entirely. Active rituals are `project_pulse` and `milestones` only (no journal prompts — see `.claude/constitution/config.yaml`).

2. **Pull today's calendar from all three sources in parallel**:
   - Outlook (work): `mcp__d1eec8bf-3d2e-4e47-be24-500ddad5ccea__outlook_calendar_search`, afterDateTime = today 00:00 local, beforeDateTime = today 23:59 local
   - Personal: `mcp__personal-calendar__list_today`
   - Running plan: `mcp__runna__list_today`
   Merge into a single chronological schedule. For each event with attendees or a related project, look up the relevant wiki context before composing the iMessage.

   **Fill the working day (09:00–17:00) with suggestion bullets**: real events come from calendars; everything between them — and the leading/trailing gaps to the 09:00 and 17:00 working-day boundaries — should be filled with an italic-only bullet using the same `HH:MM–HH:MM — content` time-range format. The renderer interleaves them in the schedule view with a muted "suggestion" style; real events stay bold.

   Rules:
   - Use real event bullets `- **HH:MM–HH:MM** <content>` for things on calendars.
   - Use suggestion bullets `- *HH:MM–HH:MM — <content>*` (full italics, including the time) for every working-hours gap ≥ 15 min, including the pre-first-event and post-last-event blocks within the 09:00–17:00 window.
   - **Suggestions must be WORK activities only — never private logistics** (gift planning, ticket purchases, errands, personal sourcing). See `feedback-morning-brief-work-only-suggestions` memory. If no specific work task slots in, default to: research a topic adjacent to active engagements, upskilling / course work, AI-augmented consulting (internal), synthesis or writing from prior meetings, prep for upcoming meetings. Personal logistics belongs in due-soon tasks or post-17:00 — not in working-day gaps.
   - Suggestions must be context-informed: next meeting's prep, today's open P0/P1 work tasks, what's fresh from yesterday, what unblocks something downstream. Avoid generic fluff like "check email."
   - Skip gaps shorter than 15 min entirely — no filler.

   Example structure:
   ```
   ## Today's Schedule

   - *09:00–10:51 — Quiet block, last Deliver + close rehearsal pass.*
   - **10:51–11:30** Block (Accenture-organized, tentative) — placeholder.
   - *11:30–12:00 — Final slide-7 sync with Rasmus & Isabel.*
   - **12:00–12:45** Danish Crown pitch (P0). ...
   - *12:45–13:30 — Decompress, grab lunch, glance Magalie's wiki.*
   - **13:30–13:55** Magalie 1:1.
   - *13:55–17:00 — Summer-party game format draft, DC follow-up notes, agent SDK upskilling block.*
   ```

3. **Pair Runna with Strava** (see `feedback-runna-strava-pair` memory). For every Runna prescription today, also call `mcp__strava__list_activities` with `after = today's date` and reconcile:
   - Run is prescribed AND a matching Strava activity exists → report as completed (e.g. "8.08km Easy ✓ done 5:07/km").
   - Prescribed, slot not yet passed, no Strava activity → report as prescribed.
   - Prescribed, slot passed, no Strava activity → flag the gap honestly ("Runna prescribed Xkm this morning — no Strava activity yet").
   - Strava activity without a Runna match → still surface (Friday social run, etc.).
   Never surface a Runna line standalone.

4. **Pull due-soon tasks** — read `/Users/amalie.dam/brian/agent_brain/tasks/`. Surface anything with `due:` in the next 10 days OR `priority: p0|p1` overdue. Skip the rest.

4b. **Lightweight feeds pull** — read `/Users/amalie.dam/brian/agent_brain/about_user/feeds.md`. Pull each active feed in parallel via `outlook_email_search` / `WebFetch`.

> ⚠️ **HARD RULE — DO NOT VIOLATE:** Never call `mcp__d1eec8bf-*__read_resource` on Outlook email bodies in this scheduled task. **No exceptions, no "just this once for richness."** Body reads have been measured at ~30K tokens each (Berlingske HTML is ~60KB raw); calling `read_resource` even twice has reproducibly cut the session off before the brief is written or sent (diagnosed 2026-05-21 via two failed test fires). The model's prior of "read the source for richness" must be overridden here. Use ONLY the `summary` field returned by `outlook_email_search` — those snippets are 150-200 chars and are explicitly designed for this kind of inline use. **If you find yourself reaching for `read_resource` on a mail URI, STOP — that is the failure mode. The brief MUST land daily; partial richness is worse than thin but reliable.** This rule is also captured in memory: `feedback-scheduled-task-budget`.

   Feeds to pull:
   - **Berlingske Morgen** (Outlook, daily — two issues): `outlook_email_search` query `"Berlingske"`, window today 00:00 → 12:00 local. Both *Dagens overblik* (~07:14, general news) and *Business-overblik* (~07:49, business + markets) should be in the inbox by ~08:15. Use the `summary` field from each result.
   - **Evolving AI Insights** (Outlook, ~2×/week): `outlook_email_search` query `"Evolving AI Insights"`, past 7d. Use `summary` field.
   - **BCG Weekly Brief** (Outlook, weekly): `outlook_email_search` query `"Weekly Brief:"`, past 7d. Use `summary` field.
   - **McKinsey newsletter** (Outlook, cadence TBD): `outlook_email_search` query `"McKinsey"`, past 7d. Use `summary` field. (First delivery still pending as of 2026-05-21 — once it lands, update feeds.md with the exact sender + newsletter name and refine the query.)
   - **TechCrunch AI** (scrape, daily): `WebFetch` on `https://techcrunch.com/category/artificial-intelligence/` with this prompt: *"Give me the top 4 most recent AI headlines + one tight sentence per headline. Focus on frontier-lab moves (Anthropic, OpenAI, Google, Meta, xAI), enterprise AI adoption, agentic AI, vendor positioning, M&A. Skip celebrity AI, opinion, no-stake product launches. Format: just the 4 headline + sentence pairs, no preamble."* — WebFetch's response is already summarised; surface it as-is or lightly trimmed.

   Compose per feed:
   - **H3 sub-section** per feed/issue: `### Feed name — *one-line headline of the issue*` (do NOT include tier or date in the heading; the tier lives in feeds.md, the date is implicit).
   - **1-3 short bullets** under each — drawn from the summary snippet (or WebFetch response) through Amalie's lens (general business, geopolitics, AI, McKinsey/BCG/Bain/Deloitte/Accenture reports — see feeds.md Source priorities + Standing interests). Surface named actors, numbers when present in the snippet, and the strategic implication for Halfspace consulting if obvious. Don't fabricate detail not in the snippet — depth comes later when Amalie opens the brief and asks for an expansion.
   - Two Berlingske entries get two sub-sections (one per issue).
   - **Drop empty feeds entirely** — if a feed has no issue in window, omit it from the brief.
   - **Do not stage to `raw/`** — this is inline surface only.

   If Amalie wants a rich version of a feed later, she opens the brief in Claude and says "expand the feeds" — that's the conversational path where `read_resource` body reads are safe.

5. **Pull milestones in window** — read `/Users/amalie.dam/brian/agent_brain/about_user/milestones.md` and apply the lead-window rules from the Milestones ritual in `briefing.md`. Surface DAY-OF / SEND TODAY / ORDER / PLAN entries only.

6. **Write the full brief to disk** — save the complete briefing to `/Users/amalie.dam/brian/artifacts/briefs/YYYY-MM-DD.md` (use today's date). This is the source of truth — Amalie can open it in Claude to read the detail. Section order:
   1. **Today's Schedule** — merged calendars, real events bold, work-only suggestion italics in gaps (see suggestion rule above)
   2. **Due-soon tasks (≤10d)** — see task-section format below
   3. **Feeds** — H3 sub-section per active feed, 1-3 short bullets each (see step 4b — body reads are forbidden in auto-fire; depth comes via on-demand "expand the feeds" in conversation). Tasks come before Feeds so the action-oriented part of the brief leads.
   4. **Milestones** — only entries in lead window (omit section if empty)
   5. **Rituals — Project pulse** — one project from rotation
   6. **FYI** — non-urgent updates, wiki changes, running status
   7. **Upcoming (next 24h)** — preview

   **Do not** include a "Needs Attention" section — it overlaps with Due-soon tasks. Anything truly urgent that's not a task (urgent email, slack escalation, remsleep "needs attention" flag) belongs at the top of FYI.

   **Task section format — MUST follow this shape or the renderer's priority-aligned table won't fire** (see `feedback-brief-task-section-format` memory):
   - Header: `## Due-soon tasks` (optional parenthetical like `(≤10d)` after).
   - Each bullet: `**slug** (P{n}, due YYYY-MM-DD, Nd) — description`. Bold slug, literal `due YYYY-MM-DD`, explicit `Nd` days-until count, em-dash before description. No wikilinks — the slug pill renders from the bold span.

7. **Compose a tight iMessage summary** (~10 lines, fits in 1-2 bubbles). Format exactly like this:

```
☀️ Morning brief — {weekday} {YYYY-MM-DD}

📅 Today
• {HH:MM} {meeting title} — {one-line prep note}
• {HH:MM} {meeting title} — {one-line prep note}
(skip section if no meetings)

🏃 Running
• {Runna prescription + Strava status — one line, e.g. "8km Easy + Strides prescribed 07:33 — pending" or "✓ 8.08km @ 5:07/km logged"}
(skip section if no Runna prescription AND no Strava activity expected)

⚡ Due soon
• {task} (P{n}, {N}d)
• {task} (P{n}, {N}d)
(skip section if none in 10d)

📰 Feeds
• {feed name}: {1-line takeaway through Amalie's lens}
(include 1-2 lines max — only the highest-signal items; skip section if no issues today)

🎁 Milestones
• [{STATUS}] {person} — {type} in {N}d — {plan}
(skip section if window empty)
```

Rules for the summary:
- No emojis beyond the five section headers above.
- Each line one item, ≤80 chars where possible.
- Prep notes: name the single most important thing for that meeting (e.g. "loop Rasmus on slide-7 changes before start" or "first 1:1 — Magalie's 'what they care about' is still blank").
- **Do not include a "Full brief" / "artifacts path" footer line.** The brief still lives on disk at `artifacts/briefs/YYYY-MM-DD.md` for Amalie to open in Claude — but the iMessage stays clean and ends at the last data section.
- For the Running line at 07:00, the run typically hasn't happened yet — say "prescribed HH:MM — pending" if so. The next morning's brief will pick up the actuals.
- If there are no meetings, no running, no due-soon tasks, and no milestones in window, still send the iMessage with just the date header line. Don't suppress.

8. **Send the iMessage** via `mcp__Read_and_Send_iMessages__send_imessage`:
   - `recipient`: `+4541109080`
   - `message`: the tight summary you just composed.

9. **Send the Halfspace-styled email** — the iMessage is the glance-on-phone version; the email is the readable-on-desktop version with the same content as the markdown brief. Reuses the shared renderer at `/Users/amalie.dam/brian/workspace/halfspace-email-renderer/render.py` (see its README for what it does).

   Compose a one-line cover subtitle (the day's headline). No closer block — the morning brief stays light. Skip the source markdown's "Rituals", "FYI", and "Upcoming" sections (they're in the markdown for archival but not worth surfacing in the email).

   ```bash
   python3 /Users/amalie.dam/brian/workspace/halfspace-email-renderer/render.py \
     /Users/amalie.dam/brian/artifacts/briefs/YYYY-MM-DD.md \
     /tmp/morning-brief-YYYY-MM-DD.html \
     --title "Morning brief · {Weekday} {DD} {Mon} {YYYY}" \
     --subtitle "{one-line headline of the day}" \
     --skip "Rituals" --skip "FYI" --skip "Upcoming"

   osascript <<APPLESCRIPT
   tell application "Mail"
     set theBody to (read POSIX file "/tmp/morning-brief-YYYY-MM-DD.html" as «class utf8»)
     set newMessage to make new outgoing message with properties {subject:"Morning brief — {Weekday} {DD} {Mon} {YYYY}", visible:false}
     tell newMessage
       set html content to theBody
       make new to recipient at end of to recipients with properties {address:"amalie.dam@halfspace.ai"}
     end tell
     send newMessage
   end tell
   APPLESCRIPT
   ```

   Same brand guarantees as the weekly brief: Britti Sans embedded for Apple Mail, gray-outlined chip eyebrows for sub-sections, dark cover + closer, real `<table>` layouts so Outlook renders correctly, zero-width spaces inside times + dates to defeat iOS auto-link detection. See `feedback-mail-app-html` memory for the underlying delivery rule.

10. **Append to changelog** at `/Users/amalie.dam/brian/artifacts/_changelog.md` (insert directly after the `---` on line 9 — i.e. as the newest entry). Use this format:

```
## [YYYY-MM-DD] morning-brief | briefing → iMessage + email at 07:00 — {one-line headline of the day's main thing}

- Brief saved: [[briefs/YYYY-MM-DD|briefs/YYYY-MM-DD.md]]
- iMessage sent to +45 41 10 90 80 — {section counts: e.g. "3 events, run pending, 2 due-soon tasks, 1 milestone ORDER"}
- Email sent to amalie.dam@halfspace.ai — subject: Morning brief — {Weekday} {DD} {Mon} {YYYY}
- Project pulse: {project surfaced today} (update [[../agent_brain/about_user/project-pulse-rotation|project-pulse-rotation]])

---
```

11. **Update project-pulse-rotation log** at `/Users/amalie.dam/brian/agent_brain/about_user/project-pulse-rotation.md` — append today's row to the rotation table.

## Constraints

- Each run starts fresh. Re-read all files cited above; don't assume any state from prior runs.
- Don't reintroduce removed rituals (no gratitude prompt, no habit check-in, no "excited about" prompt). See `feedback-morning-brief-rituals` memory.
- Always cross-reference Runna prescriptions with Strava. See `feedback-runna-strava-pair` memory.
- If Outlook MCP isn't connected: send a one-line iMessage saying "Morning brief failed: Outlook MCP unavailable. Check connection." Don't proceed silently.
- If iMessage MCP isn't connected: log to changelog with `iMessage send failed — MCP unavailable` and stop. Don't loop.
- Apply the today-focused prep rule (see `feedback-morning-brief-today-focus` memory).

Begin.