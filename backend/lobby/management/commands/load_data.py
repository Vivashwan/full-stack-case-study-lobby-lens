"""
python manage.py load_data            -> wipes the lobby tables and loads backend/data/*.csv
python manage.py load_data --path X   -> load from another folder
"""
import csv
from datetime import date, datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from lobby.models import Casino, Game, GamePosition, Geography, Operator, Provider, ScrapeRun

BATCH = 5000


def _bool(v):
    return str(v).strip().lower() == "true"


def _int_or_none(v):
    return int(v) if v not in ("", None) else None


def _rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        yield from csv.DictReader(f)


class Command(BaseCommand):
    help = "Load the case-study dataset from CSV files."

    def add_arguments(self, parser):
        parser.add_argument("--path", default=str(Path(settings.BASE_DIR) / "data"))

    @transaction.atomic
    def handle(self, *args, **opts):
        d = Path(opts["path"])
        for model in (GamePosition, ScrapeRun, Game, Casino, Provider, Operator, Geography):
            model.objects.all().delete()

        Geography.objects.bulk_create(
            Geography(id=int(r["id"]), name=r["name"], country_code=r["country_code"])
            for r in _rows(d / "geographies.csv")
        )
        Operator.objects.bulk_create(
            Operator(id=int(r["id"]), name=r["name"]) for r in _rows(d / "operators.csv")
        )
        # NOTE: names are loaded exactly as they appear in the file.
        Provider.objects.bulk_create(
            Provider(id=int(r["id"]), name=r["name"]) for r in _rows(d / "providers.csv")
        )
        Game.objects.bulk_create(
            Game(
                id=int(r["id"]),
                name=r["name"],
                provider_id=int(r["provider_id"]),
                game_type=r["game_type"],
                release_date=date.fromisoformat(r["release_date"]) if r["release_date"] else None,
            )
            for r in _rows(d / "games.csv")
        )
        Casino.objects.bulk_create(
            Casino(
                id=int(r["id"]),
                operator_id=int(r["operator_id"]),
                geography_id=int(r["geography_id"]),
                name=r["name"],
                is_active=_bool(r["is_active"]),
            )
            for r in _rows(d / "casinos.csv")
        )
        ScrapeRun.objects.bulk_create(
            (
                ScrapeRun(
                    id=int(r["id"]),
                    casino_id=int(r["casino_id"]),
                    run_date=date.fromisoformat(r["run_date"]),
                    started_at=datetime.fromisoformat(r["started_at"]),
                    status=r["status"],
                    show_data=_bool(r["show_data"]),
                    tiles_found=int(r["tiles_found"]),
                )
                for r in _rows(d / "scrape_runs.csv")
            ),
            batch_size=BATCH,
        )
        GamePosition.objects.bulk_create(
            (
                GamePosition(
                    id=int(r["id"]),
                    run_id=int(r["run_id"]),
                    game_id=int(r["game_id"]),
                    section_name=r["section_name"],
                    position_in_section=int(r["position_in_section"]),
                    overall_position=_int_or_none(r["overall_position"]),
                )
                for r in _rows(d / "game_positions.csv")
            ),
            batch_size=BATCH,
        )

        self.stdout.write(self.style.SUCCESS(
            f"Loaded {Casino.objects.count()} casinos, {Game.objects.count()} games, "
            f"{ScrapeRun.objects.count()} runs, {GamePosition.objects.count()} positions."
        ))
