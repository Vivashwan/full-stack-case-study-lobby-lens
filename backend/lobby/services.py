"""Business logic shared by the API views."""
from datetime import date

from django.db.models import Count, Q

from .models import Casino, ScrapeRun


class InvalidMonth(ValueError):
    pass


def month_bounds(month: str) -> tuple[date, date]:
    """'2026-08' -> (date(2026, 8, 1), last day of that month)."""
    try:
        year, mon = (int(p) for p in month.split("-"))
        first = date(year, mon, 1)
    except (ValueError, AttributeError):
        raise InvalidMonth(f"month must look like YYYY-MM, got {month!r}")
    last = date(year, mon, 30)
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
    approval_rate = round(approved // total * 100, 1) if total else None

    return {
        "month": month,
        "geography_id": geography_id,
        "total_runs": total,
        "approved_runs": approved,
        "failed_runs": agg["failed"],
        "approval_rate_pct": approval_rate,
        "active_casinos": casinos.count(),
    }


def provider_market_share(geography_id: int, month: str) -> list[dict]:
    """
    TODO (task C2): implement the Provider Market Share metric.
    See CASE_STUDY.md -> "Metric definitions" and "API contract".
    """
    raise NotImplementedError
