"""
LobbyLens data model - a heavily simplified slice of the IGamingCompass warehouse.

Every day a scraper opens each casino's lobby page and records which game tiles it
finds, in which section, and in what order. One visit = one ScrapeRun. Each tile it
found = one GamePosition.
"""
from django.db import models


class Geography(models.Model):
    """A regulated market. Usually a country, sometimes a state/province."""

    name = models.CharField(max_length=100)
    country_code = models.CharField(max_length=2)  # ISO-3166 alpha-2

    class Meta:
        db_table = "geography"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Operator(models.Model):
    """A company that runs one or more casino brands."""

    name = models.CharField(max_length=100)

    class Meta:
        db_table = "operator"

    def __str__(self):
        return self.name


class Casino(models.Model):
    """One operator in one geography (e.g. "Luckbridge UK")."""

    operator = models.ForeignKey(Operator, on_delete=models.PROTECT, related_name="casinos")
    geography = models.ForeignKey(Geography, on_delete=models.PROTECT, related_name="casinos")
    name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "casino"

    def __str__(self):
        return self.name


class Provider(models.Model):
    """A game studio."""

    name = models.CharField(max_length=100)

    class Meta:
        db_table = "provider"

    def __str__(self):
        return self.name


class Game(models.Model):
    GAME_TYPES = [("slots", "Slots"), ("live", "Live"), ("table", "Table")]

    name = models.CharField(max_length=150)
    provider = models.ForeignKey(Provider, on_delete=models.PROTECT, related_name="games")
    game_type = models.CharField(max_length=10, choices=GAME_TYPES)
    release_date = models.DateField(null=True)

    class Meta:
        db_table = "game"

    def __str__(self):
        return self.name


class ScrapeRun(models.Model):
    """One scraper visit to one casino's lobby."""

    STATUSES = [("success", "Success"), ("failed", "Failed")]

    casino = models.ForeignKey(Casino, on_delete=models.CASCADE, related_name="runs")
    run_date = models.DateField()
    started_at = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUSES)
    # Approval gate: True only when a reviewer has confirmed the run's data is fit to
    # show clients. A run can be status="success" and still show_data=False.
    show_data = models.BooleanField(default=False)
    tiles_found = models.IntegerField(default=0)

    class Meta:
        db_table = "scrape_run"
        indexes = [
            # Speeds up the "counted runs" access path (R1-R3 + date range): for a
            # given casino, seek straight to the run_date range and show_data value
            # instead of scanning every run of that casino. See db/slow_query.sql
            # and ANSWERS.md -> B2.
            models.Index(fields=["casino", "run_date", "show_data"], name="scraperun_casino_date_show_idx"),
        ]


class GamePosition(models.Model):
    """One game tile found on the lobby page during a run."""

    run = models.ForeignKey(ScrapeRun, on_delete=models.CASCADE, related_name="positions")
    game = models.ForeignKey(Game, on_delete=models.PROTECT, related_name="positions")
    section_name = models.CharField(max_length=100)
    # 1-based order of the tile inside its section (carousel)
    position_in_section = models.IntegerField()
    # 1-based order among tiles a player can see WITHOUT scrolling any carousel.
    # NULL = the tile exists but is off-screen until the player scrolls.
    overall_position = models.IntegerField(null=True)

    class Meta:
        db_table = "game_position"
