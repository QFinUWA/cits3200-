# Installation guide

This guide covers running the existing dataset locally, enabling fresh data collection, and preparing a hosted installation. Run commands from the repository root: the folder containing `app.py`, `load.py` and `requirements.txt`.

## 1. Requirements

- Python **3.12** and pip; this is the version used for the documented local checks.
- Git and access to the project repository, or an extracted source release.
- The supplied `final output/` folders to run the website with the existing dataset.
- Network access to install dependencies. Fresh collection also needs access to university websites and metadata providers.

Use the repository's **Code** menu to clone it or open a Codespace. A downloaded source ZIP can run the application, but does not contain the Git history needed for the submission logs.

## 2. Create the Python environment

### Linux, macOS or Codespaces

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, use `.\.venv\Scripts\python.exe` instead of `python` in subsequent commands; changing system execution policy is unnecessary.

## 3. Configure the environment

For a new installation, copy `.env.example` to `.env`. Keep an existing `.env` when upgrading.

Linux/macOS/Codespaces:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Edit the file in your editor:

| Variable | Use |
|---|---|
| `SECRET_KEY` | Set a long, randomly generated value for administrator sessions |
| `ADMIN_PASSWORD` | Set the administrator password; deliver it separately from documentation |
| `OPENALEX_API_KEY` | Provider key for collection/enrichment; unnecessary for browsing the supplied dataset |
| `CLARIVATE_API_KEY` | Authorised Journal Citation Reports API key, if that enrichment is used |
| `CONTACT_EMAIL` | Optional maintainer contact used in requests to metadata providers |

Generate a session secret locally:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the generated value into `SECRET_KEY`. Replace the sample admin password. Leave unused provider keys empty instead of treating the sample text as credentials. `.env` is excluded from Git; do not put real credentials in the README or submission ZIP.

## 4. Build and start the website

For a fresh installation using the supplied exports:

```bash
python load.py
python -m flask --app app run --host 127.0.0.1 --port 5000
```

The loader reads the university folders under `final output/` and builds `site/research.db`. No fresh scrape or provider keys are needed for this step. The loader **rebuilds** the tables, so use the backup procedure below before rebuilding an established installation.

Open <http://127.0.0.1:5000>. In Codespaces, use **Ports → 5000 → Open in Browser**; keep the forwarded port private for development. A Codespace is a development environment, not the final client hosting arrangement. Stop the server with **Ctrl+C**.

Check the home page, Researchers, Universities and Documentation. Download a CSV, then open `/admin/login` and sign in with your configured password. See [User guide](USER_GUIDE.md) for the controls.

## 5. Enable fresh collection

`run.py` and the administrator refresh read these reference inputs at the configured paths:

| Path | Required format |
|---|---|
| `data/ABDC-JQL-2025-v1-260326.xlsx` | Workbook containing sheet `2025 JQL`; configuration uses `header=7` and column `2025 rating` |
| `data/scimagojr 2025.csv` | SCImago reference export expected by `enrichment/scimago.py` |

Both files are tracked in the repository, so a clone and the handover source ZIP already contain them; there is nothing to obtain for the 2025 editions. To move to a newer edition, get it from its provider, place it in `data/`, update the file name and settings in `core/config.py`, and verify its columns before running enrichment.

Some university collection uses Selenium and Chrome/Chromium. Install a compatible browser and its operating-system dependencies on the collection host. `selenium` and `webdriver-manager` are in `requirements.txt`; installing these Python packages alone does not install a working browser. Driver download and provider access must work on that host.

Run one source before attempting all sources:

```bash
python run.py --uni usyd --skip-clarivate
```

This uses cached responses where available. Add `--refresh` for a fresh collection. Omit `--skip-clarivate` only when a working, authorised Clarivate key is configured. See [Developer guide](DEVELOPER_GUIDE.md) for validation and all-university commands.

The administrator refresh automatically skips Clarivate when its key is empty or a recognised placeholder. It still needs the other reference files and collection dependencies.

### University sites that block automated requests

Four of the eight universities put a bot check in front of the pages the pipeline reads. A check lets some requests through and refuses others, so the same collection can succeed one day and fail the next. It tends to be stricter for requests from cloud or data-centre addresses than from a home or office connection.

| University | What is protected | What the pipeline does |
|---|---|---|
| Melbourne | The Faculty of Business and Economics staff list (Cloudflare) | Without `--refresh`, falls back to the last saved copy and prints a warning. With `--refresh`, the run fails rather than pass off an old copy as fresh |
| Western Australia | The research repository (Cloudflare) | The same as Melbourne |
| Monash | The staff directory accepts only a real browser; the research portal refuses requests that arrive too fast | Loads the directory in Chrome through Selenium; retries the portal and falls back to saved pages |
| UNSW | The staff search behind the directory page (Cloudflare) | Loads the list in Chrome through Selenium and saves it to `cache/unsw_roster.json`; later runs reuse the saved list unless `--refresh` is given |

Queensland, Sydney, ANU and Adelaide have not blocked collection.

What this means in practice:

- **The administrator refresh always collects with `--refresh` and stops at the first university that fails**, leaving the live database unchanged. On a hosted server a blocked Melbourne or Western Australia request is therefore enough to stop a refresh of all universities. Refresh those universities one at a time, or collect from the command line.
- **From the command line, run without `--refresh` to accept saved copies** for a blocked university: `python run.py --uni unimelb --skip-clarivate`. The data is then only as recent as the last collection that got through.
- **If a university is blocked, try again later or from a different network.** Do not try to defeat the check.
- **The website does not collect anything while serving pages.** Browsing, downloads and Excel editing are unaffected, so a server can host the site while collection is done on another machine and the resulting `final output/` is loaded with `load.py`.
- Western Australia's repository offers an API to authorised users; requesting a key from the university is the dependable long-term route for that source.

## 6. Host the application

The exact platform, domain and maintenance owner must be recorded for the agreed deployment. The following is a **Linux deployment starting point**, not a claim that hosting is already configured.

Install Gunicorn into the application's virtual environment, then run it from the repository root:

```bash
python -m pip install gunicorn
gunicorn --workers 1 --threads 4 --bind 127.0.0.1:8000 --access-logfile - --error-logfile - app:app
```

Use one worker because the current refresh lock and status are process-local. Put a reverse proxy such as Nginx in front of the loopback service, configure the actual domain and HTTPS, and supervise the process with the host's service manager. The service must use the project's virtual environment and repository working directory. Gunicorn is for Unix-like hosts; choose an appropriate WSGI server if the agreed host is Windows.

Keep the project data persistent and writable by the service account: `site/research.db`, its adjacent staging-file location, `final output/`, `cache/`, `logs/` and `backups/`. Refresh runs as the application account and needs the same browser, reference files and provider configuration as command-line collection. Do not run the Flask development server as the production service.

Record the final URL, service/start command, restart procedure, backup location and maintenance owner in [Handover instructions](HANDOVER.md). Verify public browsing, downloads, login, a controlled refresh and recovery on the actual host.

## 7. Backup and restore

Before a manual rebuild or administrator upload:

1. Arrange a maintenance window and stop the web service after any refresh finishes.
2. Copy `site/research.db` to a dated backup outside the public `site/` folder.
3. Preserve the matching `final output/` folders, reviewed files in `data/` and source commit.
4. Restart the service when the maintenance action is complete and check the website.

For restoration, stop the service and any refresh, preserve the current database for diagnosis, restore the selected backup to `site/research.db`, then restart and check the pages and downloads. Restore matching CSV/override files as well when returning to a previous full data release. Never copy over an active database as an informal restore procedure.

Administrator refresh creates its own database backup in `backups/`; administrator Excel uploads and a direct `load.py` command do **not** create that backup for you.

## Troubleshooting

| Symptom | Action |
|---|---|
| `No module named ...` | Activate `.venv` and install `requirements.txt` with that environment's Python |
| Missing tables or empty installation | Confirm `final output/` exists and run `load.py` from the repository root |
| Port 5000 is busy | Stop the older server, or select `--port 5001` and open/forward that port |
| Admin login does not work | Check `ADMIN_PASSWORD` in `.env` and restart the application |
| Reference file not found | Check the exact names and editions in section 5 |
| Refresh stops | Read the job status and `logs/refresh/<job_id>.log`; correct the cause before rerunning. If the log shows a verification page or HTTP 403 for Melbourne, Western Australia, Monash or UNSW, see "University sites that block automated requests" in section 5 |
| `UnicodeEncodeError: 'charmap' codec can't encode character ...` on Windows | Run `$env:PYTHONIOENCODING = "utf-8"` in that PowerShell window, then repeat the command. The administrator refresh sets this itself |

## Technical references

- [Python virtual environments](https://docs.python.org/3/library/venv.html)
- [Flask production deployment with Gunicorn](https://flask.palletsprojects.com/en/stable/deploying/gunicorn/)
- [GitHub Codespaces port forwarding](https://docs.github.com/en/codespaces/developing-in-a-codespace/forwarding-ports-in-your-codespace)
