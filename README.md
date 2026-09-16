# LobbyLens

Take-home case study for the **Full Stack Developer** role at IGamingCompass.
**Start with [`CASE_STUDY.md`](CASE_STUDY.md).**

```
backend/       Django 5.2 + Django REST Framework API  (Python 3.11+)
frontend/      React 18 + Vite                         (Node 18+)
db/            SQL files for Part B
backend/data/  the dataset (CSV), loaded by `manage.py load_data`
```

Nothing else to install: the database is a local **SQLite** file (`backend/db.sqlite3`)
that Django creates for you. No Docker, no database server.

## 1. Backend + database

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate           # creates backend/db.sqlite3
python manage.py load_data         # ~5 s, loads ~110k rows (run again any time to reset the data)
python manage.py runserver         # http://localhost:8000/api/geographies/
python manage.py test lobby        # some tests fail on purpose, see CASE_STUDY.md
```

Useful: `SQL_DEBUG=1 python manage.py runserver` prints every SQL query
(Windows PowerShell: `$env:SQL_DEBUG="1"` first; cmd: `set SQL_DEBUG=1`).

## 2. Querying the database

The tables are `geography`, `operator`, `casino`, `provider`, `game`, `scrape_run` and
`game_position`. Any of these works:

- **The included helper** (only needs Python), from `backend/`:

  ```bash
  python run_sql.py ../db/provider_market_share.sql
  python run_sql.py -c "SELECT COUNT(*) FROM scrape_run"
  ```

- A GUI such as [DB Browser for SQLite](https://sqlitebrowser.org/) or DBeaver: open `backend/db.sqlite3`.
- The `sqlite3` command-line tool, if you have it: `python manage.py dbshell`.

SQLite notes: booleans are stored as `1`/`0`, dates and timestamps as ISO text
(`'2026-08-01'`, `'2026-08-01 06:30:00'`), and window functions are supported.
Your SQLite version is printed at the top of every `run_sql.py` run (3.25 or newer needed).

## 3. Frontend

```bash
cd frontend
npm install
npm run dev                        # http://localhost:5173  (proxies /api to :8000)
```

## API (existing)

| Endpoint | Notes |
|---|---|
| `GET /api/geographies/` | all geographies |
| `GET /api/casinos/?geography=<id>&is_active=true\|false&page=<n>` | paginated, 20 per page |
| `GET /api/summary/?month=YYYY-MM[&geography=<id>]` | KPI cards on the Overview page |
| `GET /api/provider-market-share/?geography=<id>&month=YYYY-MM` | **you build this (C2)** |
