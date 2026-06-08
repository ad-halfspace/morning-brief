# Morning Brief — Setup Guide

A daily orientation brief: calendar, tasks, feeds, run plan, and news, delivered as an iMessage + HTML email each weekday morning. Runs as a skill inside your existing Claude Code second brain.

---

## What it does

`/morning-brief` fans out across five phases:

| Phase | What it does | On by default |
|---|---|---|
| **scribbles** | Sweeps your Apple Note "Scribbles" and files new items as tasks/events/notes | Yes (needs Apple Notes MCP) |
| **briefing** | Calendar + tasks + email + Slack + upcoming events + project pulse + milestones | Always on |
| **research** | Pulls from a user-defined external research source | Off |
| **feeds** | Ingests newsletters/RSS from your feeds registry | Yes (needs feeds configured) |
| **news** | Scans a domain, syncs knowledge, drafts a daily post | Off |

Run manually any time (`/morning-brief`), or a single phase (`/morning-brief briefing`). The automation section below makes it fire automatically each weekday morning.

---

## Install the skills

Drop the three skill folders into your brain's `.claude/skills/`:

```
cp -r skills/morning-brief  /path/to/your/brain/.claude/skills/
cp -r skills/check          /path/to/your/brain/.claude/skills/
cp -r skills/scribbles      /path/to/your/brain/.claude/skills/
```

---

## MCPs to connect

Connect whichever apply to you. The briefing degrades gracefully for anything you skip.

### Work calendar, email, Teams (Microsoft 365)
- Install the Microsoft 365 MCP from the Claude Code MCP registry and authenticate with your work account.
- The skill uses: `outlook_calendar_search`, `outlook_email_search`, `chat_message_search`.

### Personal calendar
- Any MCP that exposes `personal-calendar__list_today`, `personal-calendar__list_upcoming`, `personal-calendar__search_events` will work.
- If you use a different MCP with different tool names, edit `skills/morning-brief/phases/briefing.md` to match.

### Strava (workout tracking)
- Available as a plugin in the Claude Code MCP registry. Install and authenticate.
- The briefing phase checks whether today's prescribed run was completed.

### Runna (training plan)
- If you use Runna, you need a Runna MCP that exposes `runna__list_today`. The briefing phase pairs today's Runna prescription with your Strava actuals.
- If you don't use Runna, skip it — remove the Runna/Strava pairing block from `skills/morning-brief/phases/briefing.md`.

### Apple Notes (Scribbles inbox)
- Create a note called **"Scribbles"** (case-sensitive) in Apple Notes. Dump quick captures there; the morning brief sweeps and files them.
- Install the `Read and Write Apple Notes` MCP from the Claude Code MCP registry.

### Scheduled-tasks (for automation)
- Available from the Claude Code MCP registry. Needed only if you want the brief to fire automatically.

---

## Brain files to create

The briefing phase reads a few files from `agent_brain/about_user/`. Create these before your first run:

### `agent_brain/about_user/feeds.md`
Your news feed registry. Start with a few sources:

```yaml
- name: TechCrunch AI
  type: scrape
  url: https://techcrunch.com/category/artificial-intelligence/
  tier: A
  cadence: daily
  bring_into_context: true
  auto_ingest: off
  notes: "Daily AI news — surface top 5 headlines."
```

Tiers: A = canonical (always fetch), B = breadth, C = deep/research. Full format reference in `skills/morning-brief/phases/feeds.md`.

Outlook-based newsletters work well — filter by sender and the M365 MCP fetches the latest matching email.

### `agent_brain/about_user/milestones.md`
Birthdays and one-time events. The briefing surfaces items inside their lead window ("ORDER — Mum's birthday in 8 days"). Start empty or disable with `milestones: false` in config.yaml.

### `agent_brain/about_user/project-pulse-rotation.md`
Create empty. The briefing maintains it automatically to rotate which project gets the spotlight each morning.

---

## Config flags

Add these to your `.claude/constitution/config.yaml`:

```yaml
# /morning-brief phase gates
feeds: true             # fetch newsletters/RSS
daily_research: false   # pull from a research source
news_scan: false        # scan domain + draft daily post
scribbles_inbox: true   # sweep Apple Note "Scribbles" each morning

# Briefing ritual blocks
project_pulse: true     # one active project gets the spotlight each morning
milestones: true        # surface upcoming birthdays + events
self_reflection: false  # surface reflection questions from /remsleep

# Light ritual flags
daily_curiosity: false
gratitude: false
habit_checkin: false
```

A full template is in `config.yaml.template`.

---

## Automation

### Requirements
- Claude Code desktop app running on your Mac.
- Mac must be **awake** at the trigger time (screen can be locked, sleep will kill it).
- `scheduled-tasks` MCP connected.

### Setup
Run `/schedule` in Claude Code:

> "Run /morning-brief every weekday at 07:20 and send me the result as an iMessage."

### iMessage delivery
- Install the `Read and Send iMessages` MCP from the registry.
- Your phone number goes in the scheduled task definition.

### HTML email delivery (optional)
`email-renderer/` contains a Python script that converts the markdown brief to a styled HTML email sent via Mail.app.

- `pip3 install markdown`
- Edit `email-renderer/send-mail.applescript` with your email address
- See `email-renderer/README.md` for full usage

---

## Running manually

```
/morning-brief              <- full brief
/morning-brief briefing     <- orientation only
/morning-brief feeds        <- pull newsletters only
/morning-brief scribbles    <- sweep Apple Notes inbox only
```

The first run windows from the last 7 days (no prior timestamp). After that each run windows from the previous one.

---

## Dependency map

```
/morning-brief
├── scribbles phase      <- Apple Notes MCP
├── briefing phase       <- /check skill
│   ├── calendar         <- M365 MCP + personal-calendar MCP
│   ├── tasks            <- agent_brain/tasks/
│   ├── email/Slack      <- M365 MCP
│   ├── milestones       <- agent_brain/about_user/milestones.md
│   └── project pulse    <- agent_brain/about_user/project-pulse-rotation.md
├── feeds phase          <- M365 MCP + WebFetch
│   └── feed registry    <- agent_brain/about_user/feeds.md
└── news phase (off)     <- feeds context + WebFetch
```
