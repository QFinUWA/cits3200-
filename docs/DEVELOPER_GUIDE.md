# Developer guide

Follow [Installation](INSTALLATION.md) first. Commands below assume an activated Python environment and the repository root as the working directory.

## Architecture and ownership of data

| Layer | Main files | Responsibility |
|---|---|---|
| Source adapters | `base_scrapers/<uni>.py` | Collect institution-specific staff and publications |
| Shared contract and cleaning | `core/schema.py`, `core/clean.py`, `core/titles.py` | Standardise records and titles |
| Supplementary retrieval | `info/` | Retrieve additional records through ORCID, Crossref and OpenAlex |
| Enrichment and screening | `enrichment/`, `screen.py` | Add journal/citation metadata and screen records |
| Export | `export.py` | Produce deduplicated university CSV/JSON tables |
| Storage | `models.py`, `load.py` | Define the SQLAlchemy model and build SQLite |
| Presentation | `app.py`, `site/`, `site/assets/app.js` | Public routes, API and browser interface |
| Administration | `admin.py`, `refresh_manager.py` | Excel changes, sessions, refresh orchestration and logs |

`run.py` performs collection, supplementary retrieval, cleaning, publication enrichment, ABDC matching, screening, optional Clarivate enrichment, SCImago enrichment, reviewed overrides, contract reporting and export. `load.py` is a separate database-building step.

The active website uses Researcher, Journal and Publication records. A Harvest model is defined, but the current loader leaves it unpopulated; consult exported harvest files for source dates. `RESEARCH_DB_PATH` changes the loader's target for staging; it does not relocate the database used by `app.py`, which reads `site/research.db`.

## Run the pipeline

Supported university codes: `adelaide`, `anu`, `monash`, `unimelb`, `unsw`, `uq`, `usyd`, `uwa`.

```bash
# One university, using cached responses when available
python run.py --uni usyd --skip-clarivate

# One university, bypassing collection caches
python run.py --uni usyd --refresh --skip-clarivate

# All discovered adapters, run sequentially
python run.py --all --skip-clarivate
```

Omit `--skip-clarivate` when using a working authorised key. All-source command-line collection reports failed sources at the end and returns a non-zero exit status if any source failed. Review its output before loading.

| Option | Purpose |
|---|---|
| `--uni CODE` | Run one adapter; specify it explicitly rather than relying on the UQ default |
| `--all` | Run all discovered adapters in separate child processes |
| `--refresh` | Bypass cached retrieval where the adapter supports it |
| `--skip-clarivate` | Omit Journal Citation Reports enrichment |
| `--no-supplementary` | Skip extra ORCID/Crossref/OpenAlex retrieval; subsequent DOI enrichment still runs |
| `--keep-empty-staff` | Retain staff with no exported publications; default behaviour drops them |
| `--ror VALUE` | Override the institution ROR for one university; not valid with `--all` |

Run `python run.py --help` for the current interface. Match the agreed staff-inclusion policy when preparing a release.

## Make a persistent correction

1. Locate the authoritative profile/publication and identify whether the issue is collection, identity, cleaning or enrichment.
2. Change the appropriate adapter/shared rule or reviewed CSV in `data/`. Existing files include staff additions/overrides/exclusions, publication exclusions/keep rules and university identity overrides; follow each file's existing schema.
3. For a verified UniMelb identity, use `data/unimelb_identity_overrides.csv`, retain the official profile/name and evidence URL, and set `review_decision` to `approved`. Review candidates first; listing a candidate alone does not approve it.
4. Add or adjust a targeted regression test when the change introduces a rule or fixes behaviour that can recur.
5. Regenerate affected exports, run validation, and inspect the diff.
6. Back up the current installation, rebuild, then confirm the public record and related exports.

Generated CSV edits alone are not persistent. Administrative database edits likewise need a pipeline/override counterpart. Preserve the raw `job_title` while changing the appropriate academic/admin title fields. Source-specific notes remain in [ANU notes](../README_ANU.md) and [Sydney notes](../README_USYD.md).

## Test a change

On Windows, switch Python's output to UTF-8 in the terminal before running tests or pipeline scripts. Several scripts print characters the default Windows console encoding cannot represent, and they stop with `UnicodeEncodeError: 'charmap' codec can't encode character ...`. Without this setting, six tests in `tests/test_merge_publications.py` fail for that reason alone. The setting lasts for that terminal session:

```powershell
$env:PYTHONIOENCODING = "utf-8"
```

Linux, macOS and Codespaces terminals already use UTF-8 and need no change.

Install testing dependencies separately:

```bash
python -m pip install pytest
python -m pytest tests/test_exported_data.py -q
python validate_data.py all
```

For a development database, build and test the storage/API layers:

```bash
python load.py
python -m pytest tests/test_database_load.py tests/test_site_api.py tests/test_universities_api.py -q
python -m pytest tests -q --ignore=tests/test_site_browser.py
```

Browser testing requires Playwright and its browser binary:

```bash
python -m pip install playwright
python -m playwright install chromium
python -m pytest tests/test_site_browser.py -q
```

On a supported Linux test host that needs browser system libraries, Playwright also provides `python -m playwright install --with-deps chromium`; this may require administrative package-install access. Use a development/test environment for these checks. Then perform the Chrome/Firefox checklist in [Test plan](TEST_PLAN.md).

Keep current results with the release evidence. Check failures **and skips**: database/API tests can skip without a built database, and browser tests can skip without Playwright. A data validator's non-zero exit is a separate result from pytest. Historical status tables in `TEST_PLAN.md` need to be dated and reconciled with the final execution; do not treat them as live status.

## Add or maintain an adapter

Implement `base_scrapers/<code>.py` with a `collect(...)` function returning `(records, pubs)` in the shape defined by `core/schema.py`. Supply `ROR` when relevant. Staff records use `name_clean` as the publication-link name; publication `name` must match it. Use the shared publication-type vocabulary and preserve source identifiers and links.

`run.py --all` discovers adapter modules automatically. The admin refresh list and website university labels are separately configured in `refresh_manager.py`, `app.py` and the frontend: review those when adding an institution. Add source fixtures and contract tests, confirm export/loader behaviour, and check the new institution through the website. `core.schema.validate()` returns reported problems; inspect them rather than assuming its call itself enforces every release check.

## API and administration reference

| Endpoint | Purpose |
|---|---|
| `GET /api/researchers` | Researcher data; filters `university`, `field`, `level`, `name` |
| `GET /api/universities` | University aggregates |
| `GET /api/researchers/<id>` | One researcher |
| `GET /api/researchers/<id>/publications` | Their publication records |
| `GET /downloads/<entity>.csv` | Public full export: `publications`, `researchers`, `journals` |
| `GET /api/admin/<entity>.xlsx` | Authenticated Excel download |
| `POST /api/admin/<entity>` | Authenticated upload, saved immediately; multipart field `file` |
| `GET /api/admin/refresh/status` | Authenticated current refresh status |
| `POST /api/admin/refresh` | Authenticated refresh; JSON `{"source":"usyd"}` or `{}` for all |

The API's university filter uses the stored university name, not the CLI adapter code. Spreadsheet uploads update existing IDs or insert blank-ID rows and are saved immediately; the admin page has no preview step. An upload is all-or-nothing: `admin.py` runs every row in one transaction and commits only if no row reports an error, so a sheet with one bad row changes nothing. It deliberately avoids a `SAVEPOINT` per row, because Python's `sqlite3` driver commits each savepoint as it is released. `admin.py` still accepts a `dry_run=1` query parameter that checks a sheet and saves nothing; the page no longer sends it. Journal-owned `quality_rank` and `sjr_quartile` propagate to associated publications. Deleting a spreadsheet row is not a database deletion operation.

## Refresh and runtime logs

The admin refresh uses `run.py --refresh`, writes `logs/refresh/<job_id>.log`, and saves the previous database as `backups/research-<job_id>.db`. After successful selected-source runs, it loads a staging database and replaces the live file. It stops on the first source failure; already generated CSVs may have changed even when the live database is retained. The usual cause of a source failing is a university's bot check: Melbourne, Western Australia, Monash and UNSW refuse automated requests some of the time. See "University sites that block automated requests" in the [Installation guide](INSTALLATION.md) for what each adapter does and how to collect around it.

The lock and status are held in one process, and the job uses a background thread. Deploy one web worker until job coordination is moved to shared durable storage. Finish a refresh before restarting the service. For a problem, collect its job ID, source, exit status and relevant log section; remove credentials if a provider response contains them.

Runtime refresh logs help maintain the application. The Git commit logs requested for Sprint 3 are a separate export described in [Handover](HANDOVER.md).

## Technical reference

- [Playwright browser installation and system dependencies](https://playwright.dev/python/docs/browsers)
