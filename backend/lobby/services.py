"""Business logic shared by the API views."""
from calendar import monthrange
from collections import defaultdict
from datetime import date

from django.db.models import Count, F, Q, Window
from django.db.models.functions import RowNumber

from .models import Casino, Game, GamePosition, Provider, ScrapeRun


class InvalidMonth(ValueError):
    pass


def month_bounds(month: str) -> tuple[date, date]:
    """'2026-08' -> (date(2026, 8, 1), last day of that month)."""
    try:
        year, mon = (int(p) for p in month.split("-"))
        first = date(year, mon, 1)
    except (ValueError, AttributeError):
        raise InvalidMonth(f"month must look like YYYY-MM, got {month!r}")
    if not 1 <= mon <= 12:
        raise InvalidMonth(f"month must look like YYYY-MM, got {month!r}")
    last_day = monthrange(year, mon)[1]  # e.g. 28/29 for Feb, 30 or 31 elsewhere
    last = date(year, mon, last_day)
    return first, last


def run_summary(month: str, geography_id: int | None = None) -> dict:
    """Headline KPIs for the Overview page."""
    first, last = month_bounds(month)
    runs = ScrapeRun.objects.filter(run_date__gte=first, run_date__lte=last)
    casinos = Casino.objects.filter(is_active=True)
    if geography_id:
        runs = runs.filter(casino__geography_id=geography_id)
        casinos = casinos.filter(geography_id=geography_id)

    agg = runs.aggregate(
        total=Count("id"),
        approved=Count("id", filter=Q(show_data=True)),
        failed=Count("id", filter=Q(status="failed")),
    )
    total, approved = agg["total"], agg["approved"]
    approval_rate = round(approved / total * 100, 1) if total else None

    return {
        "month": month,
        "geography_id": geography_id,
        "total_runs": total,
        "approved_runs": approved,
        "failed_runs": agg["failed"],
        "approval_rate_pct": approval_rate,
        "active_casinos": casinos.count(),
    }


def _counted_run_ids(geography_id: int, first: date, last: date):
    """
    Run ids that pass R1-R3 for a geography/month:
      R1 - show_data = True
      R2 - only the latest approved run per casino-day (highest started_at, then id)
      R3 - casino.is_active = True

    Implemented with a window function so "latest per casino-day" is computed by the
    database rather than in Python.
    """
    ranked = (
        ScrapeRun.objects.filter(
            show_data=True,
            casino__is_active=True,
            casino__geography_id=geography_id,
            run_date__gte=first,
            run_date__lte=last,
        )
        .annotate(
            rn=Window(
                expression=RowNumber(),
                partition_by=[F("casino_id"), F("run_date")],
                order_by=[F("started_at").desc(), F("id").desc()],
            )
        )
        .filter(rn=1)
        .values_list("id", flat=True)
    )
    return list(ranked)


def provider_market_share(geography_id: int, month: str) -> dict:
    """Provider Market Share for one geography/month. See CASE_STUDY.md -> "Metric
    definitions". A "listing" is a distinct (casino, game) pair seen in a counted run;
    NULL vs non-NULL overall_position is irrelevant here (see A7) - every tile counts."""
    first, last = month_bounds(month)
    run_ids = _counted_run_ids(geography_id, first, last)
    if not run_ids:
        return {"total_listings": 0, "results": []}

    # Materialise the distinct (casino, game) listings first. Doing the distinct and the
    # provider-level aggregation in the same queryset (.values(...).distinct().annotate())
    # does not compose the way it looks like it should in the Django ORM - the annotate
    # re-joins against the ungrouped rows and silently inflates every count. Two separate
    # steps keeps each one honest.
    listing_pairs = set(
        GamePosition.objects.filter(run_id__in=run_ids).values_list("run__casino_id", "game_id")
    )
    total_listings = len(listing_pairs)
    if not total_listings:
        return {"total_listings": 0, "results": []}

    game_ids = {game_id for _casino_id, game_id in listing_pairs}
    provider_by_game = dict(
        Game.objects.filter(id__in=game_ids).values_list("id", "provider_id")
    )
    provider_names = dict(Provider.objects.values_list("id", "name"))

    stats = defaultdict(lambda: {"games": set(), "casinos": set(), "listings": 0})
    for casino_id, game_id in listing_pairs:
        provider_id = provider_by_game[game_id]
        s = stats[provider_id]
        s["games"].add(game_id)
        s["casinos"].add(casino_id)
        s["listings"] += 1

    results = [
        {
            "provider_id": provider_id,
            "provider_name": provider_names[provider_id],
            "unique_games": len(s["games"]),
            "unique_casinos": len(s["casinos"]),
            "listings": s["listings"],
            "market_share_pct": round(s["listings"] / total_listings * 100, 2),
        }
        for provider_id, s in stats.items()
    ]
    results.sort(key=lambda r: (-r["market_share_pct"], r["provider_name"]))
    return {"total_listings": total_listings, "results": results}
