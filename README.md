# Researcher Productivity Analysis Tool

CITS3200 Professional Computing — Group 20

A Python data pipeline and Flask website for exploring the research output of accounting and finance academics at the eight Group of Eight universities. The site provides researcher rankings, university comparisons, publication details and data exports. Administrators can edit records through Excel and refresh source data.

## Documentation

| I want to… | Start here |
|---|---|
| Install and run the application | [Installation guide](docs/INSTALLATION.md) |
| Browse, filter, export or administer data | [User guide](docs/USER_GUIDE.md) |
| Maintain the code or update the pipeline | [Developer guide](docs/DEVELOPER_GUIDE.md) |
| Prepare the final code and Git logs | [Handover instructions](docs/HANDOVER.md) |
| Understand the exported fields | [Data dictionary](docs/DATA_DICTIONARY.md) |
| Run automated and manual checks | [Test plan](docs/TEST_PLAN.md) |

## Quick start

These commands are for a fresh checkout in Linux, macOS or Codespaces, using Python 3.12. Run them from the repository root. For Windows, see the installation guide.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`: set a new `SECRET_KEY` and `ADMIN_PASSWORD`. API keys are only needed when collecting or enriching data. Keep an existing `.env` when updating an installation.

Load the supplied exports and start the local development server:

```bash
python load.py
python -m flask --app app run --host 127.0.0.1 --port 5000
```

Open <http://127.0.0.1:5000>. In Codespaces, open port **5000** from the **Ports** tab. Stop the server with **Ctrl+C**. `load.py` rebuilds the database; preserve existing data before using it on an established installation.

## How the system works

University adapters collect staff and publications. Shared processing reconciles, cleans, screens and enriches records. `export.py` writes tables to `final output/<university>/`; `load.py` builds `site/research.db`; Flask serves the website and API.

| Area | Location |
|---|---|
| University collection | `base_scrapers/` |
| Shared processing and enrichment | `core/`, `info/`, `enrichment/`, `screen.py` |
| Exported data and database build | `final output/`, `export.py`, `load.py`, `models.py` |
| Website and administration | `app.py`, `admin.py`, `site/` |
| Refresh orchestration | `refresh_manager.py` |

A publication row represents one researcher–publication pair; co-authors can each have a row for the same paper. Missing indicators mean unavailable data. See the user guide and data dictionary for interpretation.

## Updating data

Fresh collection requires the reference datasets and provider configuration described in the installation guide. Example without Clarivate enrichment:

```bash
python run.py --uni usyd --skip-clarivate
```

Validate generated data before loading or releasing it. Administrator spreadsheet edits must also be retained in the pipeline or reviewed override files if they are to survive a rebuild. See the developer guide for the complete workflow.
