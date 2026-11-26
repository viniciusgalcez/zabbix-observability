#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testes offline da regra de união (Deps API + Banco)."""
from __future__ import annotations

import unittest

from sla_overlap_lib import (
    alarms_to_down_intervals,
    overlap_waste,
    parent_matches_union,
    sum_durations,
    union_duration,
    union_intervals,
)


class TestDepsOverlapScenario(unittest.TestCase):
    """API 1h; banco 40min dentro da API → união = 1h, não 1h40."""

    def setUp(self):
        self.api = (0, 3600)
        self.banco = (1200, 3600)  # 40 min sobrepostos

    def test_sum_is_wrong_for_app_sla(self):
        self.assertEqual(sum_durations([self.api, self.banco]), 6000)

    def test_union_is_correct_for_app_sla(self):
        self.assertEqual(union_duration([self.api, self.banco]), 3600)
        self.assertEqual(union_intervals([self.api, self.banco]), [(0, 3600)])

    def test_overlap_waste(self):
        self.assertEqual(overlap_waste([self.api, self.banco]), 2400)

    def test_parent_downtime_matches_union(self):
        self.assertTrue(parent_matches_union(3600, [self.api, self.banco]))
        self.assertFalse(parent_matches_union(6000, [self.api, self.banco]))


class TestAlarmsToIntervals(unittest.TestCase):
    def test_parent_timeline_union_semantics(self):
        # Filho API cai 10:00, sobe 11:00; Banco cai 10:20, sobe 11:00
        # Pai (Most critical) cai em 10:00 e sobe em 11:00
        t0 = 1_000_000
        api_alarms = [
            {"clock": str(t0), "value": "4"},
            {"clock": str(t0 + 3600), "value": "-1"},
        ]
        banco_alarms = [
            {"clock": str(t0 + 1200), "value": "4"},
            {"clock": str(t0 + 3600), "value": "-1"},
        ]
        parent_alarms = [
            {"clock": str(t0), "value": "4"},
            {"clock": str(t0 + 3600), "value": "-1"},
        ]
        api_i = alarms_to_down_intervals(api_alarms)
        banco_i = alarms_to_down_intervals(banco_alarms)
        parent_i = alarms_to_down_intervals(parent_alarms)
        self.assertEqual(union_duration(api_i + banco_i), union_duration(parent_i))
        self.assertTrue(parent_matches_union(union_duration(parent_i), api_i + banco_i))


class TestThreeFactors(unittest.TestCase):
    """API + Home + Banco: união de N fatores, não soma."""

    def test_three_overlapping_factors(self):
        api = (0, 3600)       # 1h
        home = (1800, 4200)   # overlap com API + estende 10 min
        banco = (2400, 6000)  # overlap + estende até 1h40 após início
        factors = [api, home, banco]
        self.assertEqual(union_duration(factors), 6000)  # 0..6000 = 1h40
        self.assertGreater(sum_durations(factors), 6000)
        self.assertTrue(parent_matches_union(6000, factors))


class TestAdjacentAndDisjoint(unittest.TestCase):
    def test_adjacent_merges(self):
        self.assertEqual(union_intervals([(0, 10), (10, 20)]), [(0, 20)])

    def test_disjoint_keeps_both(self):
        self.assertEqual(union_intervals([(0, 10), (20, 30)]), [(0, 10), (20, 30)])
        self.assertEqual(union_duration([(0, 10), (20, 30)]), 20)
        self.assertEqual(sum_durations([(0, 10), (20, 30)]), 20)


if __name__ == "__main__":
    unittest.main()
