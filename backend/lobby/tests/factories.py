"""Tiny helpers for building test data. Use them in your own tests too."""
from datetime import date, datetime, time

from lobby.models import Casino, Game, GamePosition, Geography, Operator, Provider, ScrapeRun


def geography(name="Testland", code="TL"):
    return Geography.objects.create(name=name, country_code=code)


def casino(geo, name="Test Casino", is_active=True, operator=None):
    operator = operator or Operator.objects.create(name=f"{name} Ltd")
    return Casino.objects.create(operator=operator, geography=geo, name=name, is_active=is_active)


def provider(name="Test Studio"):
    return Provider.objects.create(name=name)


def game(prov, name="Test Game", game_type="slots"):
    return Game.objects.create(name=name, provider=prov, game_type=game_type, release_date=date(2025, 1, 1))


def run(cas, run_date, *, show_data=True, status="success", hour=6, games=()):
    """Create a ScrapeRun and one GamePosition per game in `games` (all in one section)."""
    r = ScrapeRun.objects.create(
        casino=cas,
        run_date=run_date,
        started_at=datetime.combine(run_date, time(hour, 0)),
        status=status,
        show_data=show_data,
        tiles_found=len(games),
    )
    for i, g in enumerate(games, start=1):
        GamePosition.objects.create(
            run=r, game=g, section_name="Popular", position_in_section=i,
            overall_position=i if i <= 5 else None,
        )
    return r
