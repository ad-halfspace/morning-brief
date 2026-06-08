# halfspace-email-renderer

Halfspace-branded HTML email renderer + the two scheduled tasks that use it
(weekly-ahead and daily morning brief).

## What's in here

| Path | Purpose |
|---|---|
| `render.py` | Shared renderer: takes a markdown brief and outputs a Halfspace-styled HTML email |
| `scheduled-tasks/weekly-ahead-email.md` | The Sunday 07:00 weekly brief task definition |
| `scheduled-tasks/morning-brief.md` | The Mon–Fri 07:00 morning brief task definition (iMessage + email) |
| `launchd/com.amalie.morning-brief-wake.plist` | macOS LaunchAgent that wakes Claude.app before the in-app cron fires |

## What the renderer does

- Reads a markdown brief (e.g. the kind `/morning-brief` or the weekly-ahead
  task writes to `artifacts/`).
- Strips Obsidian `[[wikilinks]]` to bold labels.
- Wraps the content in a Halfspace-styled HTML shell: dark cover, dark closer,
  light editorial body between.
- Auto-numbers `## H2` sections, renders `### H3` as gray-outlined chip
  eyebrows, parses `## Today's Schedule` and `## Due-soon tasks` into
  structured time-aligned / priority-aligned tables.
- Inline-styles every element so Outlook can't strip the design.
- Inserts U+200B zero-width spaces inside times, dates, weekdays, months,
  phone numbers, ISO dates, slash-dates, and time-keywords so iOS Mail won't
  auto-link them.
- Embeds Britti Sans (Light/Regular/Medium/Semibold/Bold) as base64 OTF (≈ 500
  KB added) so Apple Mail picks up the real font. Outlook falls back to
  Helvetica/Inter.
- Mobile media queries collapse the layout at 600px viewport widths.

## Usage

```bash
python3 render.py \
  <PATH-TO-CLONE>/../../artifacts/briefs/2026-05-20.md \
  /tmp/morning-brief-2026-05-20.html \
  --title "Morning brief · Wed 20 May 2026" \
  --subtitle "DC pitch at noon, first Magalie 1:1 after, run pending." \
  --skip "Rituals" --skip "FYI" --skip "Upcoming"
```

Then send via Mail.app:

```bash
osascript <<APPLESCRIPT
tell application "Mail"
  set theBody to (read POSIX file "/tmp/morning-brief-2026-05-20.html" as «class utf8»)
  set newMessage to make new outgoing message with properties {subject:"Morning brief — Wed 20 May 2026", visible:false}
  tell newMessage
    set html content to theBody
    make new to recipient at end of to recipients with properties {address:"amalie.dam@halfspace.ai"}
  end tell
  send newMessage
end tell
APPLESCRIPT
```

### CLI flags

- `--title TEXT` — cover kicker (uppercase, small)
- `--subtitle TEXT` — cover headline (large)
- `--closer TEXT` — optional dark-closer one-liner at the bottom; omit for none
- `--skip "SectionName"` — repeatable. Case-insensitive partial match against
  H2 headings. The morning brief uses this to drop "Rituals", "FYI", "Upcoming".

## Prereqs

- Python 3.10+
- `python-markdown`: `pip3 install --user markdown`
- Britti Sans OTFs in any of these locations (script auto-discovers):
  - `<repo>/fonts/` (not checked in — gitignored)
  - `/tmp/design-pkg3/daily-brief/project/fonts/` (Anthropic design handoff)
  - `/tmp/design-pkg2/daily-brief/project/fonts/`

If no font folder is found the renderer falls through to the Inter / Söhne /
Helvetica fallback stack — Outlook will end up at Helvetica anyway.

## How the scheduled tasks use this

Both tasks live in `~/.claude/scheduled-tasks/` and are auto-fired by Claude
Code. They:

1. Run their respective brief generation (data pull, calendars, tasks, Strava
   reconciliation, etc.) and write a markdown brief to
   `artifacts/briefs/YYYY-MM-DD.md` (morning) or
   `artifacts/weekly/YYYY-MM-DD.md` (weekly).
2. Invoke `render.py` against that markdown with the right CLI flags.
3. Send via Mail.app `osascript` with `html content` (never `content` — Mail.app
   shows raw markdown otherwise).
4. Append to `artifacts/_changelog.md` and update
   `agent_brain/about_user/project-pulse-rotation.md`.

The morning brief also sends a tight ≈10-line iMessage in parallel, since the
phone glance is a different read shape than the desktop email.

## Schedule + autonomy

Both scheduled tasks live in Claude Code's in-app scheduler, which only fires
while `Claude.app` is open and the REPL is idle. To bridge that — so the
briefs arrive even when the laptop has been asleep — there's a two-layer wake:

1. **macOS LaunchAgent** at `launchd/com.amalie.morning-brief-wake.plist`
   fires at 06:55 on Sun + Mon–Fri (the days briefs are scheduled), running
   `/usr/bin/open -a Claude`. Opens the desktop app so its scheduler can pick
   up the pending cron.

   Install once:
   ```bash
   cp launchd/com.amalie.morning-brief-wake.plist ~/Library/LaunchAgents/
   launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.amalie.morning-brief-wake.plist
   ```

2. **macOS `pmset` schedule** wakes the laptop from sleep at 06:50 on the
   same days. Requires sudo (one-time):

   ```bash
   sudo pmset repeat wakeorpoweron MTWRFU 06:50:00
   ```

   Where `M T W R F` = Mon–Fri and `U` = Sunday. Saturday is omitted.

   Verify with `pmset -g sched`. `pmset` only supports one repeating wake
   schedule per type, so this command replaces any prior `pmset repeat`.

### Cron expressions

| Task | Cron | Effective fire (with jitter) |
|---|---|---|
| `morning-brief-imessage` | `0 7 * * 1-5` | Mon–Fri ~07:03 |
| `weekly-ahead-email` | `5 7 * * 0` | Sun ~07:10 |

Local time (Europe/Copenhagen). The in-app scheduler adds a few minutes of
deterministic jitter to balance fleet load.

## Brand notes

- Ink `#414141` (never pure black for text).
- Accent: `#0038FF` Halfspace Blue, used sparingly.
- Secondary accent: `#BFB799` sand, used for suggestion-bullets and bullet dots.
- High-stakes alert only: `#F85100` orange (P1 priority, DAY-OF status).
- 4 px radius everywhere (no full pills, no square corners).
- No drop shadows, gradients, glows. Hairlines and whitespace do the work.
- Stamps (uppercase eyebrow labels) at 0.12–0.16em letter-spacing, Medium 500
  weight.

These tokens map 1:1 onto Halfspace's `colors_and_type.css`. The renderer
inlines them so Outlook (which strips CSS variables) still gets the right look.

## Security

- No secrets in this repo.
- Markdown source paths are absolute on Amalie's machine but assume nothing
  about the contents — only the renderer cares.

## Related

- `~/brian/workspace/strava-mcp/` — Strava MCP, similar tooling pattern
- `~/brian/workspace/runna-mcp/` — Runna MCP
- `~/brian/workspace/personal-calendar-mcp/` — Personal calendar MCP
- `~/brian/workspace/meeting-recorder/` — Local meeting transcription
