"""Scoring tiers for Grid Escape."""

from grid_escape.grids import get_optimal_steps


def compute_tier(grid_id: str, steps: int) -> str:
    """Compute tier from actual steps vs optimal.

    Tier thresholds:
    - diff <= 0  -> PERFECT
    - diff <= 2  -> EXCELLENT
    - diff <= 5  -> GOOD
    - diff <= 10 -> COMPLETED
    - diff > 10  -> OVERMOVED
    """
    optimal = get_optimal_steps(grid_id)
    diff = steps - optimal
    if diff <= 0:
        return "PERFECT"
    elif diff <= 2:
        return "EXCELLENT"
    elif diff <= 5:
        return "GOOD"
    elif diff <= 10:
        return "COMPLETED"
    else:
        return "OVERMOVED"
