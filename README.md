# Morning Brief — Setup Guide

This package gives you a daily orientation brief: calendar, tasks, feeds, run plan, and news, delivered as an iMessage + HTML email each weekday morning. It runs inside Claude Code's agentic harness ("brian") on your Mac.

---

## What it does

`/morning-brief` fans out across five phases:

| Phase | What it does | On by default |
|---|---|---|
| **scribbles** | Sweeps your Apple Note "Scribbles" and files new items as tasks/events/notes | Yes (needs Apple Notes) |
| **briefing** | Calendar + tasks + email + Slack + upcoming events + project pulse + milestones | Always on |
| **research** | Pulls from a user-defined external research source | Off — turn on if you have one |
| **feeds** | Ingests newsletters/RSS from your feeds registry | Yes (needs your feeds configured) |
| **news** | Scans a domain, syncs knowledge, drafts a daily post | Off — turn on if you want to post daily |

You can run it manually any time (`/morning-brief`), or run a single phase (`/morning-brief briefing`). The automation setup below makes it fire automatically at 07:20 on weekdays.

---

## Prerequisites

### 1. The "brian" harness

This skill lives inside the `brian` second-brain harness. You need the full harness installed (CLAUDE.md, `.claude/constitution/`, `agent_brain/` structure). If you don't have it yet, ask Amalie for the cowork plugin link — it sets up the whole harness in one step.

Once you have the harness, drop the three skill folders from this package into `.claude/skills/`:

```
cp -r skills/morning-brief  ~/.../brian/.claude/skills/
cp -r skills/check          ~/.../brian/.claude/skills/
cp -r skills/scribbles      ~/.../brian/.claude/skills/
```

### 2. Claude Code desktop app

You need the Claude Code desktop app running on your Mac — not just the CLI. The scheduled-task automation fires through it.

---

## MCPs you need to connect

The briefing phase pulls from several live sources. Connect whichever apply to you.

### Work calendar, email, Teams/Slack (Microsoft 365)
The briefing phase reads your Outlook calendar and inbox for context.
- Install the Microsoft 365 MCP from the Claude Code MCP registry.
- Authenticate with your work account.
- The MCP ID in Amalie's setup is `d1eec8bf-3d2e-4e47-be24-500ddad5ccea` (yours will differ — the skill just calls the tools by name, so any M365 MCP that exposes `outlook_calendar_search` and `outlook_email_search` works).

### Personal calendar (Google Calendar)
Amalie has a custom MCP that reads a Google Calendar ICS URL — ask her for the code directly, it's not in this repo.

It needs your private Google Calendar ICS URL (Google Calendar Settings > "Secret address in iCal format"). The tool names the briefing phase expects: `personal-calendar__list_today`, `personal-calendar__list_upcoming`, `personal-calendar__search_events`.

If you use a different calendar (iCloud, Fantastical, etc.) you can swap in a different MCP — just edit `phases/briefing.md` to match whatever tool names your MCP exposes.

### Runna (training plan)
If you use Runna for running training, Amalie has a custom MCP for it — ask her for the code, it's not in this repo. The briefing phase will pair today's Runna prescription with your Strava actuals.

If you don't use Runna: skip this entirely. The briefing phase degrades gracefully.

### Strava (workout tracking)
Available as a plugin in the Claude Code MCP registry.
- Install it and authenticate.
- The briefing phase checks Strava to confirm whether today's prescribed run was completed.
- If you don't use Strava: skip it.

### Apple Notes (Scribbles inbox)
The `scribbles` phase reads an Apple Note called **"Scribbles"** (case-sensitive).
- Create a note with that exact name in Apple Notes.
- Dump quick captures there throughout the day — tasks, events, random thoughts. The morning brief sweeps it and files things properly.
- The MCP is `Read and Write Apple Notes`, available from the Claude Code MCP registry.

### Scheduled-tasks (for automation)
If you want the brief to fire automatically each morning, you need the `scheduled-tasks` MCP.
- Available from the Claude Code MCP registry.
- After connecting it, run `/schedule` in claude Code to create the morning-brief scheduled task (see Automation section below).

---

## Brain files you need to set up

The briefing phase reads a few `agent_brain/about_user/` files. Create these before your first run:

### `agent_brain/about_user/feeds.md`
Your news feed registry. The `feeds` phase reads this to know what to fetch. Start with a few sources in this format:

```yaml
- name: TechCrunch AI
  type: scrape
  url: https://techcrunch.com/category/artificial-intelligence/
  tier: A
  cadence: daily
  bring_into_context: true
  auto_ingest: off
  notes: "Daily AI news — surface top 5 headlines filtered to your domain."
```

Tiers: A = canonical (always fetch), B = breadth, C = deep/research. The `feeds` phase is documented in `skills/morning-brief/phases/feeds.md`.

Outlook-based newsletters work well: filter by sender in Outlook and the MCP fetches the latest matching email. That's how Amalie's Berlingske, McKinsey, and Evolving AI Insights feeds work.

### `agent_brain/about_user/milestones.md`
Birthdays and one-time events you want advance notice for. The briefing phase surfaces items inside their lead window (e.g. "ORDER — Mum's birthday in 8 days"). If you don't want this, set `milestones: false` in config.yaml.

### `agent_brain/about_user/project-pulse-rotation.md`
Tracks which project got the spotlight today so it rotates across your active projects. Create it empty and the briefing phase will maintain it.

### `agent_brain/tasks/`
The task health section of the briefing reads your task files from here. Tasks are markdown files with frontmatter (`status:`, `priority:`, `due:`). If you have the task board set up, it reads from the same folder.

---

## Config flags

Edit `.claude/constitution/config.yaml` to turn phases on/off:

```yaml
# Phase gates
feeds: true             # fetch newsletters/RSS
daily_research: false   # pull from a research source (set up research.md first)
news_scan: false        # scan domain + draft daily post
scribbles_inbox: true   # sweep Apple Note "Scribbles" each morning

# Briefing ritual blocks
project_pulse: true     # one active project gets the spotlight each morning
milestones: true        # surface upcoming birthdays + events
self_reflection: false  # surface reflection questions from /remsleep

# Light ritual flags (all off = pure orientation brief)
daily_curiosity: false
gratitude: false
habit_checkin: false
```

---

## Automation: firing the brief automatically

### What you need
- Claude Code desktop app open and running on your Mac.
- Your Mac must be **awake** at the trigger time (screen can be locked, but the machine cannot be asleep or lid-closed without an external power source that keeps it alive).
- The `scheduled-tasks` MCP connected.

### Setting it up
Run `/schedule` in Claude Code and describe what you want:

> "Run /morning-brief every weekday at 07:20 Europe/Copenhagen and send me the result as an iMessage."

The skill will create the scheduled task via the `scheduled-tasks` MCP. You can check it with `mcp__scheduled-tasks__list_scheduled_tasks`.

### iMessage delivery
The scheduled task can send you a tight ~10-line iMessage summary plus a full HTML email. To enable iMessage:
- Install the `Read and Send iMessages` MCP from the registry.
- Your phone number goes in the scheduled task definition.

### Email delivery (optional)
Amalie's setup uses a custom Halfspace-branded HTML email renderer that converts the markdown brief to a styled HTML email and sends it via Mail.app + AppleScript. That code isn't in this repo — ask her if you want it.

This is optional. The iMessage summary is enough for most days.

---

## Optional: Task board

Amalie has a local task board app — a Python menubar app + local web server (port 3737) that gives a visual view of `agent_brain/tasks/`. The Claude Code assistant can also drive it (open task pages, update status) via HTTP. The code isn't in this repo; ask her if you want it.

The briefing works fine without the task board. It reads tasks directly from `agent_brain/tasks/` regardless.

---

## Running it manually

Once the skill is installed and MCPs are connected, just type:

```
/morning-brief
```

Or run a single phase:

```
/morning-brief briefing     <- just today's orientation
/morning-brief feeds        <- just pull newsletters
/morning-brief scribbles    <- just sweep the Apple Notes inbox
```

The first run will have no prior timestamp to window from (fallback: last 7 days) and no project-pulse history. After the first run, each subsequent run windows from the previous one.

---

## Dependency map (quick reference)

```
/morning-brief
├── scribbles phase      <- Apple Notes MCP
├── briefing phase       <- /check skill
│   ├── calendar         <- Outlook MCP + personal-calendar MCP
│   ├── tasks            <- agent_brain/tasks/ + task board (optional)
│   ├── email/Slack      <- Outlook MCP + Teams MCP
│   ├── milestones       <- agent_brain/about_user/milestones.md
│   └── project pulse    <- agent_brain/about_user/project-pulse-rotation.md
├── feeds phase          <- Outlook MCP + WebFetch (for scrape-type feeds)
│   └── feed registry    <- agent_brain/about_user/feeds.md
└── news phase (off)     <- feeds phase context + WebFetch
```

Strava + Runna are read inside the briefing phase alongside the calendar pull. They're optional — remove the pairing logic from `phases/briefing.md` if you don't use either.
