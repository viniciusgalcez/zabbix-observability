#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Funções puras para indisponibilidade com sobreposição.

Regra correta para SLA de aplicação composta (ex.: Deps API + Banco):
  downtime = UNIÃO dos intervalos dos componentes
  NÃO = soma das durações

Exemplo:
  API  [0, 3600]   (1h)
  Banco[1200, 3600] (40min dentro da API)
  soma  = 6000s (errado para a app)
  união = 3600s (correto — a app já estava fora)
"""
from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

Interval = Tuple[int, int]  # [start, end) em epoch seconds


def normalize_intervals(intervals: Iterable[Interval]) -> List[Interval]:
    """Descarta intervalos vazios/invertidos e ordena por início."""
    out: List[Interval] = []
    for start, end in intervals:
        s, e = int(start), int(end)
        if e > s:
            out.append((s, e))
    out.sort(key=lambda x: x[0])
    return out


def sum_durations(intervals: Iterable[Interval]) -> int:
    """Soma bruta das durações (conta sobreposição duas vezes)."""
    return sum(e - s for s, e in normalize_intervals(intervals))


def union_intervals(intervals: Iterable[Interval]) -> List[Interval]:
    """Mescla intervalos sobrepostos/adjacentes em uma união mínima."""
    norm = normalize_intervals(intervals)
    if not norm:
        return []
    merged: List[Interval] = [norm[0]]
    for s, e in norm[1:]:
        ps, pe = merged[-1]
        if s <= pe:
            merged[-1] = (ps, max(pe, e))
        else:
            merged.append((s, e))
    return merged


def union_duration(intervals: Iterable[Interval]) -> int:
    """Duração da união (sobreposição contada uma vez)."""
    return sum(e - s for s, e in union_intervals(intervals))


def overlap_waste(intervals: Iterable[Interval]) -> int:
    """Quanto a soma bruta exagera em relação à união."""
    return sum_durations(intervals) - union_duration(intervals)


def alarms_to_down_intervals(
    alarms: Sequence[dict],
    *,
    ok_value: int = -1,
    period_from: int | None = None,
    period_to: int | None = None,
) -> List[Interval]:
    """
    Converte status_timeline.alarms do Zabbix em intervalos de problem.

    alarms: lista de {"clock": "...", "value": "..."} ordenável por clock.
    value == ok_value (-1) = OK; qualquer outro = problema.
    """
    if not alarms:
        return []
    events = sorted(
        ((int(a["clock"]), int(a["value"])) for a in alarms),
        key=lambda x: x[0],
    )
    intervals: List[Interval] = []
    down_since: int | None = None
    for clock, value in events:
        if value != ok_value and down_since is None:
            down_since = clock
        elif value == ok_value and down_since is not None:
            intervals.append((down_since, clock))
            down_since = None
    if down_since is not None and period_to is not None:
        intervals.append((down_since, period_to))

    if period_from is None and period_to is None:
        return intervals

    clipped: List[Interval] = []
    for s, e in intervals:
        cs = s if period_from is None else max(s, period_from)
        ce = e if period_to is None else min(e, period_to)
        if ce > cs:
            clipped.append((cs, ce))
    return clipped


def parent_matches_union(
    parent_downtime: int,
    child_intervals: Iterable[Interval],
    *,
    tolerance_sec: int = 2,
) -> bool:
    """True se o downtime do pai ≈ união dos filhos (tolerância de clock)."""
    expected = union_duration(child_intervals)
    return abs(int(parent_downtime) - expected) <= tolerance_sec
