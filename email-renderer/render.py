#!/usr/bin/env python3
"""
Halfspace-themed email renderer for Brian-generated briefs.

Takes a markdown brief (the kind /morning-brief or /weekly-ahead-email writes to
artifacts/) and renders it as a styled HTML email that follows Halfspace brand
guidelines (Britti Sans, ink #414141, gray-outlined sub-section chips, dark
cover + closer, 4px radius, no shadows, table-based layout for Outlook).

Usage:
    python3 render.py <input.md> <output.html> [--title TEXT] [--closer TEXT]

Notes
- Fonts (Britti Sans Light/Regular/Medium/Semibold/Bold) are base64-embedded so
  Apple Mail picks them up. Outlook strips them; falls back to Helvetica.
- Every layout uses real <table> markup, not CSS grid — works in Outlook for
  Mac/Windows as well as Mail.app/Gmail/iOS.
- iOS Mail auto-link detection on times + dates is defeated by inserting U+200B
  inside the patterns.
"""

import argparse
import base64
import pathlib
import re
import sys

import markdown


# ---------- Halfspace brand tokens ----------
FONT_STACK = "'Britti Sans','Inter','Söhne','Helvetica Neue',Helvetica,Arial,sans-serif"
INK = '#414141'
INK_DARK = '#1A1A1A'
MUTE = '#6E6E6E'
FAINT = '#9A9A9A'
BLUE = '#0038FF'
SAND = '#BFB799'
SAND_NUM = '#8A8050'
ORANGE = '#F85100'
STROKE = '#D9D9D9'
BG = '#FFFFFF'
BG_ALT = '#F2F2F2'

THIS_DIR = pathlib.Path(__file__).parent
FONT_DIR = THIS_DIR / 'fonts'

# Fall back to a project that ships the OTFs if a local fonts/ folder is missing.
_FONT_DIR_CANDIDATES = [
    FONT_DIR,
    pathlib.Path('/tmp/design-pkg3/daily-brief/project/fonts'),
    pathlib.Path('/tmp/design-pkg2/daily-brief/project/fonts'),
]


def _font_dir() -> pathlib.Path | None:
    for d in _FONT_DIR_CANDIDATES:
        if d.exists() and any(d.glob('Britti-Sans-*.otf')):
            return d
    return None


def _embedded_font_faces() -> str:
    d = _font_dir()
    if d is None:
        return ''
    weights = [
        ('Britti-Sans-Light.otf', 300),
        ('Britti-Sans-Regular.otf', 400),
        ('Britti-Sans-Medium.otf', 500),
        ('Britti-Sans-Semibold.otf', 600),
        ('Britti-Sans-Bold.otf', 700),
    ]
    blocks = []
    for fname, weight in weights:
        p = d / fname
        if not p.exists():
            continue
        b64 = base64.b64encode(p.read_bytes()).decode('ascii')
        blocks.append(
            f"@font-face{{font-family:'Britti Sans';"
            f"src:url(data:font/otf;base64,{b64}) format('opentype');"
            f"font-weight:{weight};font-style:normal;font-display:swap}}"
        )
    return '\n'.join(blocks)


# ---------- transformations ----------

def _chip_label(text: str) -> str:
    """Halfspace gray-outlined chip used for every sub-section eyebrow."""
    return (
        f'<span style="display:inline-block;padding:3px 9px;border:1px solid {STROKE};'
        f'color:{MUTE};background:transparent;border-radius:4px;font-size:10px;'
        f'letter-spacing:.12em;text-transform:uppercase;font-weight:500;font-family:{FONT_STACK};">'
        f'{text}</span>'
    )


def _strip_wikilinks(src: str) -> str:
    """Obsidian [[path|label]] → bold label."""
    def repl(m):
        inner = m.group(1)
        label = inner.split('|', 1)[1] if '|' in inner else inner.split('/')[-1]
        return f'**{label}**'
    return re.sub(r'\[\[([^\]]+)\]\]', repl, src)


def _break_ios_autodetect(html: str) -> str:
    """Insert U+200B inside times/dates/phones so iOS Mail won't auto-link them."""
    WEEKDAYS_FULL = 'Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday'
    WEEKDAYS_ABBR = 'Mon|Tue|Wed|Thu|Fri|Sat|Sun'
    MONTHS_FULL = ('January|February|March|April|May|June|July|August|September|'
                   'October|November|December')
    MONTHS_ABBR = 'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec'
    TIME_KEYWORDS = ('tomorrow', 'tonight', 'afternoon', 'morning', 'evening',
                     'midweek', 'midnight', 'noon', 'midday', 'today',
                     'yesterday', 'weekend')

    TIME_RE = re.compile(r'(?<![\d.\-])(\d{1,2}):(\d{2})(?!\d)')
    ISO_DATE_RE = re.compile(r'\b(\d{4})-(\d{2})-(\d{2})\b')
    # Match phone-like sequences: optional + and country code, then 7+ digits with separators
    PHONE_RE = re.compile(r'(?<![\d])(\+?\d{1,3}[\s\-.]\d{2,3}(?:[\s\-.]\d{2,4}){1,4})(?![\d])')
    # "in N days" / "in N hours" / "in N weeks" / "N days ago" / "in N min"
    RELATIVE_RE = re.compile(
        r'\b(in)\s+(\d+)\s+(seconds?|minutes?|min|mins|hours?|hrs?|days?|weeks?|months?|years?)\b',
        re.I,
    )
    AT_TIME_RE = re.compile(r'\b(at)\s+(\d{1,2}(?::\d{2})?(?:\s?[ap]m)?|noon|midnight|midday)\b', re.I)

    def in_text(text: str) -> str:
        # HH:MM → HH​:MM
        text = TIME_RE.sub(lambda m: f'{m.group(1)}​:{m.group(2)}', text)
        # YYYY-MM-DD → break each dash
        text = ISO_DATE_RE.sub(lambda m: f'{m.group(1)}​-{m.group(2)}​-{m.group(3)}', text)
        # M/D dates
        text = re.sub(r'(\d{1,2})/(\d{1,2})', r'\1​/\2', text)
        # Phone numbers: insert ZWSP after first digit group
        text = PHONE_RE.sub(lambda m: re.sub(r'(\d)([\s\-.])(\d)', r'\1​\2​\3', m.group(0), count=1), text)
        # "in N days" → break "in"
        text = RELATIVE_RE.sub(lambda m: f'{m.group(1)[:1]}​{m.group(1)[1:]} {m.group(2)} {m.group(3)}', text)
        # "at TIME" → break "at" so iOS doesn't latch onto it
        text = AT_TIME_RE.sub(lambda m: f'a​t {m.group(2)}', text)
        # Weekday/month name → split after first 2 letters
        for pattern in (WEEKDAYS_FULL, WEEKDAYS_ABBR, MONTHS_FULL, MONTHS_ABBR):
            text = re.sub(
                rf'\b({pattern})(?![​])\b',
                lambda m: m.group(1)[:2] + '​' + m.group(1)[2:] if len(m.group(1)) > 2 else m.group(1),
                text,
                flags=re.IGNORECASE,
            )
        for kw in TIME_KEYWORDS:
            text = re.sub(
                rf'\b({kw})\b',
                lambda m: m.group(1)[:2] + '​' + m.group(1)[2:] if len(m.group(1)) > 2 else m.group(1) + '​',
                text,
                flags=re.IGNORECASE,
            )
        return text

    parts = re.split(r'(<[^>]+>)', html)
    return ''.join(p if p.startswith('<') else in_text(p) for p in parts)


def _style_inline_pills(html: str) -> str:
    """Inline-style any leftover [DAY-OF] [ORDER] etc. status badges."""
    BADGE_MAP = {
        'DAY-OF': ORANGE, 'SEND TODAY': ORANGE,
        'ORDER': SAND_NUM, 'PLAN': INK, 'FYI': MUTE,
    }

    def badge(m):
        t = m.group(1)
        c = BADGE_MAP.get(t, MUTE)
        return (f'<span style="display:inline-block;font-size:10px;letter-spacing:.12em;'
                f'text-transform:uppercase;padding:2px 7px;border:1px solid {c};color:{c};'
                f'border-radius:4px;margin-right:5px;font-weight:500;font-family:{FONT_STACK};">'
                f'{t}</span>')

    return re.sub(r'\[(DAY-OF|SEND TODAY|ORDER|PLAN|FYI)\]', badge, html)


def _style_code_inline(html: str) -> str:
    """All <code> → gray-bg inline span (Outlook-safe styling)."""
    return re.sub(
        r'<code\b[^>]*>([^<]+)</code>',
        rf'<span style="font-family:inherit;background:{BG_ALT};border:1px solid {STROKE};'
        rf'border-radius:3px;padding:1px 6px;font-size:13px;word-break:break-all;">\1</span>',
        html,
    )


def _number_sections(html: str) -> str:
    """Wrap each <h2> in a styled section heading with 01/02/03 number prefix."""
    section_idx = [0]

    def style_h2(m):
        section_idx[0] += 1
        num = f'{section_idx[0]:02d}'
        # Strip trailing parentheticals from H2 titles ("Milestones (in lead window)" → "Milestones")
        title = re.sub(r'\s*\([^)]*\)\s*$', '', m.group(1)).strip()
        return (
            f'<div style="margin:32px 0 16px;padding-bottom:10px;border-bottom:1px solid {STROKE};font-family:{FONT_STACK};">'
            f'<div style="font-size:10px;letter-spacing:.16em;text-transform:uppercase;'
            f'color:{MUTE};font-weight:500;margin-bottom:6px;font-family:{FONT_STACK};">→ {num}</div>'
            f'<div style="font-size:26px;font-weight:500;letter-spacing:-0.01em;line-height:1.1;color:{INK_DARK};font-family:{FONT_STACK};">{title}</div>'
            f'</div>'
        )

    return re.sub(r'<h2>([^<]+)</h2>', style_h2, html)


def _style_h3_as_chip(html: str) -> str:
    """### sub-headings render as gray chips."""
    def style(m):
        return f'<div style="margin:18px 0 8px;font-family:{FONT_STACK};">{_chip_label(m.group(1).strip())}</div>'
    return re.sub(r'<h3>([^<]+)</h3>', style, html)


def _style_priority_h3(html: str) -> str:
    """### P1 / ### P2 / ### Carry-in render as priority-colored chips."""
    def style(m):
        text = m.group(1).strip()
        text_upper = text.upper()
        if text_upper == 'P1' or text_upper.startswith('P1 '):
            color = ORANGE
        elif text_upper == 'P2' or text_upper.startswith('P2 '):
            color = BLUE
        elif 'CARRY' in text_upper:
            color = MUTE
        else:
            return m.group(0)
        return (
            f'<div style="margin:22px 0 10px;font-family:{FONT_STACK};">'
            f'<span style="display:inline-block;padding:3px 10px;border:1px solid {color};'
            f'color:{color};background:transparent;border-radius:4px;font-size:10.5px;'
            f'letter-spacing:.12em;text-transform:uppercase;font-weight:500;font-family:{FONT_STACK};">'
            f'{text}</span>'
            f'</div>'
        )
    return re.sub(r'<h3>([^<]+)</h3>', style, html)


# Day H2 markers — used in the weekly brief
DAY_PREFIX_RE = re.compile(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b')


def _render_day_h2s(html: str) -> str:
    """## Mon DD MMM — title rows become day-card headings (chip + name + descriptor)."""
    def style(m):
        title = m.group(1).strip()
        if not DAY_PREFIX_RE.match(title):
            return m.group(0)
        # Split day prefix from rest
        parts = title.split(' ', 1)
        dayname = parts[0]
        rest = parts[1] if len(parts) > 1 else ''
        return (
            f'<div style="margin:26px 0 12px;padding:0 0 8px;border-bottom:1px solid {STROKE};font-family:{FONT_STACK};">'
            f'<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
            f'<td valign="middle" style="font:800 11px/1 {FONT_STACK};letter-spacing:.12em;text-transform:uppercase;'
            f'color:#FFFFFF;background:{INK_DARK};padding:5px 10px 4px;border-radius:3px;">{dayname}</td>'
            f'<td valign="middle" style="padding-left:12px;font:500 18px/1.2 {FONT_STACK};letter-spacing:-0.005em;color:{INK_DARK};">{rest}</td>'
            f'</tr></table>'
            f'</div>'
        )
    return re.sub(r'<h2>([^<]+)</h2>', style, html)


def _render_blk_lists(html: str) -> str:
    """Each ### chip eyebrow followed by a <ul> in the weekly day-by-day section
    becomes a tighter time-aligned block. Detects `HH:MM-HH:MM rest` bullets and
    renders them as 2-col time+content rows."""
    TIME_BULLET = re.compile(
        r'^(\d{1,2}:\d{2}(?:[–\-]\d{1,2}:\d{2})?)\s+(.*)$', re.S,
    )

    def style_ul(m):
        items_html = m.group(1)
        items = re.findall(r'<li>(.*?)</li>', items_html, re.S)
        rendered = []
        for item in items:
            stripped = item.strip()
            tm = TIME_BULLET.match(re.sub(r'<[^>]+>', '', stripped))
            if tm:
                # Find the time text in the original (with any HTML)
                t = tm.group(1)
                rest = stripped[len(t):].strip()
                rest = re.sub(r'^\s*[—–-]\s*', '', rest)
                rendered.append(
                    f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
                    f'style="margin:0 0 6px;font-family:{FONT_STACK};"><tr>'
                    f'<td valign="top" width="88" style="padding:2px 12px 2px 0;font-size:12.5px;color:{FAINT};'
                    f'font-variant-numeric:tabular-nums;font-family:{FONT_STACK};">{t}</td>'
                    f'<td valign="top" style="font-size:14.5px;line-height:1.5;color:{INK};font-family:{FONT_STACK};">{rest}</td>'
                    f'</tr></table>'
                )
            else:
                rendered.append(
                    f'<div style="margin:6px 0;font-size:14.5px;line-height:1.5;color:{INK};font-family:{FONT_STACK};">{stripped}</div>'
                )
        return ''.join(rendered)

    return re.sub(r'<ul>(.*?)</ul>', style_ul, html, flags=re.S)


def _render_schedule_section(html: str) -> str:
    """Find a '## Today's Schedule' section's <ul> and rewrite as a structured
    time-aligned table. Two bullet kinds:
      - Real events: `<li><strong>HH:MM–HH:MM</strong> content</li>`
      - Suggestions: `<li><em>HH:MM–HH:MM — content</em></li>`
    Both render with the same time | content layout. Suggestions are italic +
    muted + sand-bordered so they read as "soft" between-meeting fill."""
    pattern = re.compile(
        r'(<h2>Today\'s Schedule</h2>\s*)<ul>(.*?)</ul>',
        re.S | re.I,
    )
    TIME_HEAD = re.compile(r'^(\d{1,2}:\d{2}(?:[–\-]\d{1,2}:\d{2})?)\s*[—\-–]?\s*(.*)$', re.S)

    def repl(m):
        items_html = m.group(2)
        rows = []
        for li_match in re.finditer(r'<li>(.*?)</li>', items_html, re.S):
            inner = li_match.group(1).strip()
            # Detect kind
            strong_match = re.match(r'<strong>([^<]+)</strong>(.*)', inner, re.S)
            em_match = re.match(r'<em>(.*?)</em>\s*$', inner, re.S)
            if strong_match:
                time = strong_match.group(1).strip()
                rest = strong_match.group(2).strip()
                rest = re.sub(r'^\s*[—–-]\s*', '', rest)
                row = (
                    f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
                    f'style="margin:0 0 12px;font-family:{FONT_STACK};"><tr>'
                    f'<td valign="top" width="92" style="padding:2px 14px 0 0;font-size:12px;color:{FAINT};'
                    f'font-variant-numeric:tabular-nums;font-family:{FONT_STACK};">{time}</td>'
                    f'<td valign="top" style="font-size:14.5px;line-height:1.5;color:{INK};font-family:{FONT_STACK};">{rest}</td>'
                    f'</tr></table>'
                )
                rows.append(row)
            elif em_match:
                # Suggestion bullet — content starts with HH:MM
                content = em_match.group(1).strip()
                t = TIME_HEAD.match(content)
                if t:
                    time = t.group(1).strip()
                    text = t.group(2).strip()
                else:
                    time = ''
                    text = content
                row = (
                    f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
                    f'style="margin:0 0 12px;font-family:{FONT_STACK};"><tr>'
                    f'<td valign="top" width="92" style="padding:2px 14px 0 0;font-size:12px;color:{SAND_NUM};'
                    f'font-variant-numeric:tabular-nums;font-family:{FONT_STACK};">{time}</td>'
                    f'<td valign="top" style="padding:2px 0 2px 12px;border-left:2px solid {SAND};'
                    f'font-size:13.5px;line-height:1.45;color:{MUTE};font-style:italic;font-family:{FONT_STACK};">{text}</td>'
                    f'</tr></table>'
                )
                rows.append(row)
        return m.group(1) + ''.join(rows)

    return pattern.sub(repl, html)


def _render_tasks_section(html: str) -> str:
    """Find a '## Due-soon tasks*' section and rewrite as structured task rows."""
    pattern = re.compile(
        r'(<h2>Due-soon tasks[^<]*</h2>\s*)<ul>(.*?)</ul>',
        re.S | re.I,
    )

    def repl(m):
        items_html = m.group(2)
        rows = []
        for idx, li_match in enumerate(re.finditer(r'<li>(.*?)</li>', items_html, re.S)):
            inner = li_match.group(1).strip()
            # Pattern: <strong>slug</strong> (P1, due YYYY-MM-DD, Nd) — description
            mm = re.match(
                r'<strong>([^<]+)</strong>\s*\(([^,)]+),\s*due\s+([^,)]+),\s*(-?\d+d)\)\s*[—\-–]?\s*(.*)',
                inner, re.S,
            )
            if not mm:
                rows.append(f'<li style="margin:6px 0;font-size:14px;color:{INK};">{inner}</li>')
                continue
            slug, prio, due, days, desc = mm.group(1), mm.group(2).strip(), mm.group(3).strip(), mm.group(4), mm.group(5).strip()
            prio_color = ORANGE if prio.upper() == 'P1' else BLUE if prio.upper() == 'P2' else MUTE
            # Overdue (negative days-until) reads as "Nd overdue" in the priority color, not a bare "-Nd".
            if days.startswith('-'):
                days_label, days_color = f'{days[1:]} overdue', ORANGE
            else:
                days_label, days_color = days, FAINT
            top_border = f'border-top:1px solid {STROKE};' if idx > 0 else ''
            row = (
                f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
                f'style="margin:0 0 12px;{top_border}font-family:{FONT_STACK};"><tr>'
                f'<td valign="top" width="40" style="padding:14px 8px 14px 0;font-size:11px;letter-spacing:.14em;'
                f'text-transform:uppercase;color:{prio_color};font-weight:500;font-family:{FONT_STACK};">{prio}</td>'
                f'<td valign="top" style="padding:14px 8px 14px 0;font-family:{FONT_STACK};">'
                f'<div style="font-size:14px;color:{INK_DARK};font-weight:500;margin-bottom:4px;">'
                f'<span style="font-family:inherit;background:{BG_ALT};border:1px solid {STROKE};'
                f'border-radius:3px;padding:1px 6px;font-size:13px;word-break:break-all;">{slug}</span>'
                f'</div>'
                f'<div style="font-size:13.5px;line-height:1.45;color:{MUTE};">{desc}</div>'
                f'</td>'
                f'<td valign="top" width="84" align="right" style="padding:14px 0;font-size:12px;'
                f'color:{INK};font-variant-numeric:tabular-nums;font-family:{FONT_STACK};">{due}<br>'
                f'<span style="color:{days_color};font-size:11px;">{days_label}</span></td>'
                f'</tr></table>'
            )
            rows.append(row)
        return m.group(1) + ''.join(rows)

    return pattern.sub(repl, html)


def _style_paragraphs_and_lists(html: str) -> str:
    """Inline styles on p, ul, ol, li, strong, em, blockquote."""
    html = re.sub(
        r'<p>',
        f'<p style="margin:7px 0;color:{INK};font-size:14.5px;line-height:1.55;font-family:{FONT_STACK};font-style:normal;">',
        html,
    )
    html = re.sub(
        r'<ul>',
        f'<ul style="margin:8px 0;padding-left:20px;list-style:disc;font-family:{FONT_STACK};">',
        html,
    )
    html = re.sub(
        r'<ol>',
        f'<ol style="margin:8px 0;padding-left:20px;list-style:decimal;font-family:{FONT_STACK};">',
        html,
    )
    html = re.sub(
        r'<li>',
        f'<li style="margin:6px 0;font-size:14.5px;line-height:1.5;color:{INK};font-family:{FONT_STACK};">',
        html,
    )
    html = re.sub(
        r'<strong>',
        f'<strong style="color:{INK_DARK};font-weight:600;">',
        html,
    )
    html = re.sub(
        r'<blockquote>',
        f'<blockquote style="margin:10px 0;padding:10px 14px;background:{BG_ALT};'
        f'border-left:3px solid {STROKE};color:{MUTE};font-size:13px;line-height:1.5;'
        f'border-radius:0 4px 4px 0;font-style:normal;">',
        html,
    )
    return html


def _strip_frontmatter(src: str) -> str:
    """Drop leading YAML frontmatter (between --- delimiters at top of file)."""
    return re.sub(r'\A---\n.*?\n---\n+', '', src, count=1, flags=re.S)


def _drop_sections(src: str, names: list[str]) -> str:
    """Remove ## sections whose heading matches any name in `names` (case-insensitive,
    partial match — 'rituals' matches '## Rituals', '## Recent themes' is unaffected)."""
    if not names:
        return src
    pattern = re.compile(
        r'^##\s+(' + '|'.join(re.escape(n) for n in names) + r').*?\n(.*?)(?=^##\s|\Z)',
        flags=re.M | re.S | re.I,
    )
    return pattern.sub('', src)


def render(md_text: str, *, title: str, subtitle: str = '', closer: str = '',
           skip_sections: list[str] | None = None, weekly: bool = False) -> str:
    """Render markdown brief into a Halfspace-styled HTML email.

    `weekly=True` activates weekly-brief-specific transformations:
    - Day H2s (## Mon DD MMM …) render as day-card headings (chip + title)
    - Time-prefixed bullets render as 2-col time+content rows
    - ### P1 / ### P2 / ### Carry-in render as priority-colored chips
    """
    src = _strip_frontmatter(md_text)
    src = _strip_wikilinks(src)
    if skip_sections:
        src = _drop_sections(src, skip_sections)
    # Drop the markdown's own h1 (we replace it with the cover)
    src = re.sub(r'^#\s+.*\n', '', src, count=1, flags=re.M)
    body = markdown.markdown(src, extensions=['extra', 'sane_lists'])

    body = _style_code_inline(body)
    body = _style_inline_pills(body)
    body = _render_schedule_section(body)
    body = _render_tasks_section(body)
    if weekly:
        # Run priority H3 styling before generic chip so P1/P2/Carry-in get color
        body = _style_priority_h3(body)
        # Day H2s become date-chip headings; non-day H2s flow to _number_sections
        body = _render_day_h2s(body)
        # Time-prefixed bullets become 2-col rows
        body = _render_blk_lists(body)
    body = _style_h3_as_chip(body)
    body = _number_sections(body)
    body = _style_paragraphs_and_lists(body)
    body = re.sub(r'<hr\s*/?>', '', body)
    body = _break_ios_autodetect(body)
    # Run the same break pass on cover/closer text strings (they bypass the body pipeline)
    title = _break_ios_autodetect(title)
    subtitle = _break_ios_autodetect(subtitle)
    closer = _break_ios_autodetect(closer)

    font_face_css = _embedded_font_faces()

    # Cover (dark) + content + closer (dark)
    cover = (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'bgcolor="#000000" style="background:#000000;color:#FFFFFF;">'
        f'<tr><td bgcolor="#000000" style="background:#000000;color:#FFFFFF;padding:28px 14px 36px;font-family:{FONT_STACK};">'
        f'<div style="display:block;border-bottom:1px solid #2A2A2A;padding-bottom:14px;font-size:13px;color:#FFFFFF;letter-spacing:.02em;">'
        f'<b style="font-weight:500;">Halfspace<sup style="font-size:.55em;opacity:.7;">®</sup></b>'
        f'<span style="opacity:.5;margin:0 8px;">→</span>'
        f'<span style="color:#B8B8B8;">Part of Accenture</span>'
        f'</div>'
        f'<div style="margin-top:20px;font-size:13px;color:#B8B8B8;letter-spacing:.12em;text-transform:uppercase;">'
        f'<span style="color:#FFFFFF;">→</span>&nbsp;&nbsp;{title}'
        f'</div>'
        f'<h1 style="margin:24px 0 0;font-size:42px;line-height:0.95;letter-spacing:-0.015em;font-weight:500;color:#FFFFFF;">'
        f'{subtitle if subtitle else title}'
        f'</h1>'
        f'</td></tr></table>'
    )

    closer_block = ''
    if closer:
        closer_block = (
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
            f'bgcolor="#000000" style="background:#000000;color:#FFFFFF;">'
            f'<tr><td bgcolor="#000000" style="background:#000000;color:#FFFFFF;padding:40px 14px;font-family:{FONT_STACK};">'
            f'<div style="font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#888;font-weight:500;">'
            f'→ One line</div>'
            f'<h2 style="margin:14px 0 0;font-size:26px;font-weight:500;letter-spacing:-0.015em;line-height:0.95;color:#FFFFFF;max-width:22ch;">'
            f'{closer}</h2>'
            f'</td></tr></table>'
        )

    css = f"""
    <style>
      {font_face_css}
      body, table, td, th, tr, p, h1, h2, h3, h4, h5, h6, div, span, a, b, i, em, strong, ul, ol, li, code, dl, dt, dd, article, section, header, footer, blockquote {{
        font-family: {FONT_STACK} !important;
      }}
      body {{ margin:0; padding:0; background:{BG}; color:{INK}; font-size:14.5px; line-height:1.55; font-weight:300; }}
      .container {{ max-width:760px; margin:0 auto; }}
      a[x-apple-data-detectors], a[x-apple-data-detectors] *, a[href^="tel:"], a[href^="tel:"] * {{
        color: inherit !important; text-decoration: none !important;
      }}
      @media only screen and (max-width: 600px) {{
        body {{ font-size:14px !important; }}
        .container {{ padding:0 16px !important; }}
      }}
    </style>
    """

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="format-detection" content="telephone=no,date=no,address=no,email=no,url=no">
<meta name="x-apple-disable-message-reformatting">
<title>{title}</title>
{css}
</head>
<body>
<div class="container">
{cover}
<div style="padding:16px 14px 24px;">
{body}
</div>
{closer_block}
</div>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description='Render a Brian brief as a Halfspace-styled HTML email.')
    parser.add_argument('input', type=pathlib.Path, help='Input markdown file')
    parser.add_argument('output', type=pathlib.Path, help='Output HTML file')
    parser.add_argument('--title', default='Morning brief', help='Cover kicker text')
    parser.add_argument('--subtitle', default='', help='Cover headline (overrides title for h1)')
    parser.add_argument('--closer', default='', help='Optional dark-closer one-liner')
    parser.add_argument('--skip', action='append', default=[],
                        help='H2 section heading to omit (repeatable). Case-insensitive partial match.')
    parser.add_argument('--weekly', action='store_true',
                        help='Activate weekly-brief transformations (day-card H2s, time-row bullets, P1/P2 chips).')
    args = parser.parse_args()

    md = args.input.read_text()
    html = render(md, title=args.title, subtitle=args.subtitle, closer=args.closer,
                  skip_sections=args.skip, weekly=args.weekly)
    args.output.write_text(html)
    print(f'wrote: {args.output} ({len(html)} bytes)')


if __name__ == '__main__':
    main()
