from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AvailableArea:
    area_no: str
    seat_grade_name: str
    real_seat_cnt: int


def find_available_areas(summary: list[dict], ignore_prefix: str = "4") -> list[AvailableArea]:
    """Return areas (sections) with remaining seats, excluding ones starting with ignore_prefix."""
    results = []
    for area in summary:
        area_no = area.get("areaNo")
        if area_no is None or str(area_no).startswith(ignore_prefix):
            continue
        try:
            cnt = int(area.get("realSeatCntlk", 0))
        except (TypeError, ValueError):
            cnt = 0
        if cnt > 0:
            results.append(
                AvailableArea(
                    area_no=area_no,
                    seat_grade_name=area.get("seatGradeName", ""),
                    real_seat_cnt=cnt,
                )
            )
    return results
