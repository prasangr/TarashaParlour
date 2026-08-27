"""Reads the palette straight out of index.html and asserts every text/background
pair used on a flat ground passes WCAG AA (4.5:1).  Run: python check_contrast.py"""
import re, sys, io

def luminance(hex_colour):
    h = hex_colour.lstrip('#')
    channels = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

def ratio(fg, bg):
    hi, lo = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)

def over(fg, bg, alpha):
    """fg laid over bg at `alpha` opacity."""
    f, b = fg.lstrip('#'), bg.lstrip('#')
    return '#' + ''.join('%02X' % round(int(f[i:i+2], 16) * alpha + int(b[i:i+2], 16) * (1 - alpha))
                         for i in (0, 2, 4))

css = io.open('index.html', encoding='utf-8').read()
t = dict(re.findall(r'--([\w-]+)\s*:\s*(#[0-9A-Fa-f]{6})', css))

# Every pair the page actually renders on a flat (non-photographic) ground.
# Text over photography is handled by scrims, not by these tokens.
grounds = [('ink', t['ink']), ('ink-2', t['ink-2']), ('ink-3', t['ink-3'])]
pairs = [(f'{name} on {gname}', t[name], ground)
         for gname, ground in grounds
         for name in ('muted', 'gold', 'gold-lt', 'ivory', 'neon')]
pairs += [
    ('ink on gold (buttons)',        t['ink'], t['gold']),
    ('ink on gold-lt (button hover)', t['ink'], t['gold-lt']),
    ('white on wa (WhatsApp)',       '#FFFFFF', t['wa']),
    ('white on wa-hi (hover)',       '#FFFFFF', t['wa-hi']),
    # footer fine print is the one place we dim the body colour
    ('footer fine print (muted @72%)', over(t['muted'], t['ink'], 0.72), t['ink']),
    # the savings chip: pink type on a translucent magenta pill over the ground
    ('savings chip text', '#FFB3DC', over(t['neon'], t['ink'], 0.15)),
    ('savings chip text on band', '#FFB3DC', over(t['neon'], t['ink-2'], 0.15)),
]

failures = []
for label, fg, bg in pairs:
    r = ratio(fg, bg)
    if r < 4.5:
        failures.append(f'  {r:5.2f}  {label}  ({fg} on {bg})')
    print(f'{r:5.2f}  {"ok  " if r >= 4.5 else "FAIL"}  {label}')

if failures:
    print('\nBelow WCAG AA (4.5:1):', file=sys.stderr)
    print('\n'.join(failures), file=sys.stderr)
    sys.exit(1)
print(f'\nAll {len(pairs)} pairs pass WCAG AA.')
