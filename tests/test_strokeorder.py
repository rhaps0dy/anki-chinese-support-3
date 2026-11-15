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

from re import findall

from chinese.strokeorder import (
    generate_svg,
    get_stroke_order,
    load_data,
    point_at,
    polyline_length,
    unique_hanzi,
)
from tests import Base

DATA = {
    'strokes': ['M 0 0 L 1024 0 Z', 'M 100 100 L 900 900 Z'],
    'medians': [[[0, 0], [512, 512], [1024, 0]], [[100, 100], [900, 900]]],
}


class UniqueHanzi(Base):
    def test_mixed(self):
        self.assertEqual(unique_hanzi('你好，你'), ['你', '好'])

    def test_repeats(self):
        self.assertEqual(unique_hanzi('妈妈'), ['妈'])


class PointAt(Base):
    def test_start(self):
        self.assertEqual(point_at([(0, 0), (10, 0)], 0), (0, 0))

    def test_end(self):
        self.assertEqual(point_at([(0, 0), (10, 0)], 10), (10, 0))

    def test_middle(self):
        self.assertEqual(point_at([(0, 0), (10, 0)], 5), (5.0, 0))

    def test_beyond(self):
        self.assertEqual(point_at([(0, 0), (10, 0)], 100), (10, 0))

    def test_length(self):
        self.assertEqual(polyline_length([(0, 0), (3, 4)]), 5.0)


class GenerateSvg(Base):
    def setUp(self):
        self.svg = generate_svg('一', DATA)

    def test_dimensions(self):
        self.assertIn('width="1080"', self.svg)
        self.assertIn('height="128"', self.svg)

    def test_two_frames(self):
        self.assertEqual(len(findall(r'translate\(\d+, \d+\)', self.svg)), 2)

    def test_done_then_todo(self):
        done = findall(r'class="(d|t)"', self.svg)
        self.assertEqual(done, ['d', 't', 'd', 'd'])

    def test_arrow_tail_is_last_256_units(self):
        for i, m in enumerate(DATA['medians']):
            expected = point_at(m, max(0, polyline_length(m) - 256))
            arrow = findall(r'<line x1="([-0-9.e]+)" y1="([-0-9.e]+)" x2="{}" y2="{}"'.format(int(m[-1][0]), int(m[-1][1])), self.svg)
            self.assertEqual(len(arrow), 1, 'one arrow per stroke')
            self.assertEqual(float(arrow[0][0]), expected[0])
            self.assertEqual(float(arrow[0][1]), expected[1])

    def test_style(self):
        self.assertIn('prefers-color-scheme:dark', self.svg)


class LoadData(Base):
    def test_cached_or_none(self):
        result = load_data('⺁')
        self.assertIn(result, (None, dict))


class GetStrokeOrder(Base):
    def test_no_hanzi(self):
        self.assertEqual(get_stroke_order('abc'), '')
