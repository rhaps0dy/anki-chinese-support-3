# Copyright © 2026
#
# This file is part of Chinese Support 3.
#
# Chinese Support 3 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Chinese Support 3 is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# Chinese Support 3.  If not, see <https://www.gnu.org/licenses/>.

"""Stroke order diagrams, generated from Hanzi Writer stroke data.

For each character an SVG is generated showing the character once per
stroke: every frame repeats the character with the strokes written so
far in the foreground colour and the remaining strokes in a faint
colour, together with an arrow indicating the direction of the stroke
that was just added.

The stroke data comes from the
[Hanzi Writer data](https://github.com/chanind/hanzi-writer-data)
project (itself derived from Make me a Hanzi). Data is looked up in
local directories (see `data_dirs()`) and, failing that, downloaded
from a CDN and cached locally.
"""

from json import dump, load
from math import ceil, hypot
from os import environ, makedirs
from os.path import dirname, exists, expanduser, join, realpath
from re import match
from urllib.parse import quote
from urllib.request import Request, urlopen

from .consts import HANZI_RANGE

TILE = 128
GAP = 8
STEP = TILE + GAP
TILES_PER_ROW = 8
ROW_WIDTH = (TILES_PER_ROW - 1) * STEP + TILE  # 1080
ARROW_LENGTH = 256

CDN_URL = 'https://cdn.jsdelivr.net/npm/hanzi-writer-data@2.0/{}.json'

# Fallback colours are chosen to be legible on both light and dark
# backgrounds; where `prefers-color-scheme` is honoured, they are
# overridden with better suited palettes.
SVG_STYLE = (
    '<style>'
    '.d{fill:#808080}'
    '.t{fill:#bfbfbf}'
    '.a{stroke:#d00000;fill:none}'
    '.g{stroke:#8c8c8c;fill:none}'
    '@media (prefers-color-scheme:dark){'
    '.d{fill:#e2e2e2}'
    '.t{fill:#4f4f4f}'
    '.g{stroke:#454545}'
    '}</style>'
)

GRID_FRAME = (
    '<g transform="translate({x}, {y})">'
    '<rect x="0" y="0" width="128" height="128" class="g" stroke-width="1"/>'
    '<line x1="64.0" y1="0" x2="64.0" y2="128" class="g" stroke-width="1"/>'
    '<line x1="0" y1="64.0" x2="128" y2="64.0" class="g" stroke-width="1"/>'
)

INNER_GROUP = '<g transform="translate(0, 112.5) scale(0.125, -0.125)">'

ARROW_LINE = (
    '<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"'
    ' class="a" stroke-width="16" marker-end="url(#arrow)"/>'
)


def _cache_dir():
    """Download cache lives in the user's cache home, not inside the addon."""

    base = environ.get('XDG_CACHE_HOME') or join(expanduser('~'), '.cache')
    return join(base, 'ChineseSupport3', 'hanzi')


def data_dirs():
    """Lookup order: explicit override, addon-bundled data, download cache."""

    dirs = []
    if environ.get('HANZI_WRITER_DATA'):
        dirs.append(environ['HANZI_WRITER_DATA'])
    dirs.append(join(dirname(realpath(__file__)), 'data', 'hanzi'))
    dirs.append(_cache_dir())
    return dirs


def load_data(char):
    """Return stroke data for a character, or None if unavailable."""

    filename = char + '.json'
    for d in data_dirs():
        path = join(d, filename)
        if exists(path):
            with open(path, encoding='utf-8') as f:
                return load(f)

    cache = join(_cache_dir(), filename)
    try:
        request = Request(CDN_URL.format(quote(char)))
        request.add_header('User-Agent', 'Mozilla/5.0')
        with urlopen(request, timeout=10) as response:
            data = load(response)
    except Exception:
        return None

    try:
        makedirs(dirname(cache), exist_ok=True)
        with open(cache, 'w', encoding='utf-8') as f:
            dump(data, f, ensure_ascii=False, separators=(',', ':'))
    except Exception:
        pass

    return data


def polyline_length(points):
    return sum(
        hypot(b[0] - a[0], b[1] - a[1])
        for a, b in zip(points, points[1:])
    )


def point_at(points, distance):
    """Point at an arc length along a polyline."""

    if distance <= 0:
        return points[0]
    remaining = distance
    for a, b in zip(points, points[1:]):
        length = hypot(b[0] - a[0], b[1] - a[1])
        if remaining <= length:
            t = remaining / length
            return (
                a[0] + t * (b[0] - a[0]),
                a[1] + t * (b[1] - a[1]),
            )
        remaining -= length
    return points[-1]


def number(n):
    if n == int(n):
        return str(int(n))
    return str(n)


def arrow(median):
    """Arrow along the final `ARROW_LENGTH` units of a stroke median."""

    length = polyline_length(median)
    tail = point_at(median, max(0, length - ARROW_LENGTH))
    tip = median[-1]
    return ARROW_LINE.format(
        x1=number(tail[0]),
        y1=number(tail[1]),
        x2=number(tip[0]),
        y2=number(tip[1]),
    )


def generate_svg(char, data):
    strokes = data['strokes']
    medians = data['medians']
    n = len(strokes)
    rows = max(1, ceil(n / TILES_PER_ROW))
    height = rows * STEP - GAP

    frames = []
    for i in range(n):
        x = (i % TILES_PER_ROW) * STEP
        y = (i // TILES_PER_ROW) * STEP
        paths = ''.join(
            '<path d="{}" class="{}"/>'.format(
                d, 'd' if j <= i else 't'
            )
            for j, d in enumerate(strokes)
        )
        frames.append(
            GRID_FRAME.format(x=x, y=y)
            + INNER_GROUP
            + paths
            + arrow(medians[i])
            + '</g></g>'
        )

    header = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"'
        ' viewBox="0 0 {width} {height}">'
        '<defs><marker id="arrow" markerWidth="2.4" markerHeight="2.4" refX="1.6"'
        ' refY="1.2" orient="auto"><path d="M0,0 L2.4,1.2 L0,2.4 Z"'
        ' fill="#d00000"/></marker></defs>'.format(width=ROW_WIDTH, height=height)
        + SVG_STYLE
    )

    return header + ''.join(frames) + '</svg>'


def unique_hanzi(hanzi):
    """Hanzi characters of a string, in order, without repetitions."""

    chars = []
    for char in hanzi:
        if match('[%s]' % HANZI_RANGE, char) and char not in chars:
            chars.append(char)
    return chars


def get_stroke_order_svg(hanzi):
    """Generate an SVG for each unique character in a word, or None."""

    svgs = []
    for char in unique_hanzi(hanzi):
        data = load_data(char)
        if not data:
            return None
        svgs.append(generate_svg(char, data))
    return svgs or None


def get_stroke_order(hanzi):
    """Write stroke order SVGs to the media folder and return html.

    Each unique character is represented by one image.
    """

    svgs = get_stroke_order_svg(hanzi)
    if not svgs:
        return ''

    from aqt import mw

    html = []
    for char, svg in zip(unique_hanzi(hanzi), svgs):
        filename = 'stroke_{}.svg'.format(hex(ord(char))[2:])
        path = join(mw.col.media.dir(), filename)
        if not exists(path):
            try:
                makedirs(dirname(path), exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(svg)
            except OSError:
                pass
        html.append(
            '<img class="stroke-order-img" src="{}">'.format(filename)
        )
    return ' '.join(html)
