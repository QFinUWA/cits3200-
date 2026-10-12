"""Admin spreadsheet upload is all-or-nothing - CITS3200 Group 20.

    python load.py                       # builds site/research.db
    python -m pytest tests/test_admin_upload.py -q

Every test works on a temporary COPY of site/research.db, opened the same way
app.py opens the real one. The real database is never written. Skips when
site/research.db has not been built.
"""

import io
import shutil
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DB = ROOT / "site" / "research.db"

pytestmark = pytest.mark.skipif(
    not DB.exists(), reason="site/research.db not built; run python load.py first")

openpyxl = pytest.importorskip("openpyxl")


class _NoRefresh:
    def snapshot(self):
        return {"state": "idle"}


@pytest.fixture
def site(tmp_path, monkeypatch):
    """(client, path of the temporary database copy)"""
    from flask import Flask
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from admin import make_admin_bp

    monkeypatch.setenv("ADMIN_PASSWORD", "secret")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    copy = tmp_path / "research.db"
    shutil.copy(DB, copy)
    engine = create_engine(f"sqlite:///{copy}", connect_args={"check_same_thread": False})
    app = Flask(__name__)
    app.register_blueprint(make_admin_bp(sessionmaker(bind=engine), refresh_manager=_NoRefresh()))
    app.testing = True
    client = app.test_client()
    client.post("/admin/login", data={"password": "secret"})
    yield client, copy
    engine.dispose()


def _value(db, sql):
    con = sqlite3.connect(db)
    try:
        return con.execute(sql).fetchone()[0]
    finally:
        con.close()


def _blank_admin_ids(db, n):
    con = sqlite3.connect(db)
    try:
        return [r[0] for r in con.execute(
            "select researcher_id from researcher where admin_title is null "
            f"order by researcher_id limit {n}")]
    finally:
        con.close()


def _upload(client, data):
    r = client.post("/api/admin/researchers",
                    data={"file": (io.BytesIO(data), "researchers.xlsx")},
                    content_type="multipart/form-data")
    return r.get_json()


def _workbook(client, edit):
    """The researchers export with `edit(ws, columns, row_of)` applied."""
    wb = openpyxl.load_workbook(io.BytesIO(client.get("/api/admin/researchers.xlsx").data))
    ws = wb.active
    col = {c.value: i + 1 for i, c in enumerate(ws[1])}
    row_of = {ws.cell(row=r, column=col["researcher_id"]).value: r
              for r in range(2, ws.max_row + 1)}
    edit(ws, col, row_of)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _admin_title(db, rid):
    return _value(db, f"select admin_title from researcher where researcher_id={rid}")


def test_a_clean_upload_is_saved(site):
    client, db = site
    rid, = _blank_admin_ids(db, 1)

    def edit(ws, col, row_of):
        ws.cell(row=row_of[rid], column=col["admin_title"]).value = "Test Role"

    result = _upload(client, _workbook(client, edit))
    assert result["updated"] == 1 and result["errors"] == []
    assert _admin_title(db, rid) == "Test Role"


def test_one_bad_row_means_nothing_is_saved(site):
    """A good edit on an early row, and a later row whose id does not exist.
    Each row used to sit in its own SAVEPOINT, which sqlite3 committed on
    release, so the good row stayed saved while the page said "no rows were
    saved"."""
    client, db = site
    first, second = _blank_admin_ids(db, 2)

    def edit(ws, col, row_of):
        ws.cell(row=row_of[first], column=col["admin_title"]).value = "Test Role"
        ws.cell(row=row_of[second], column=col["admin_title"]).value = "Other Role"
        ws.cell(row=ws.max_row, column=col["researcher_id"]).value = 99999999

    result = _upload(client, _workbook(client, edit))
    assert len(result["errors"]) == 1, result
    assert _admin_title(db, first) is None
    assert _admin_title(db, second) is None


def test_a_bad_row_in_the_middle_does_not_save_the_rows_after_it(site):
    client, db = site
    rid = _blank_admin_ids(db, 1)[0]

    def edit(ws, col, row_of):
        ws.cell(row=2, column=col["researcher_id"]).value = 99999999      # first data row is bad
        ws.cell(row=row_of[rid], column=col["admin_title"]).value = "Test Role"

    result = _upload(client, _workbook(client, edit))
    assert result["errors"], result
    assert _admin_title(db, rid) is None


def test_after_a_failed_upload_the_corrected_sheet_saves(site):
    client, db = site
    rid, = _blank_admin_ids(db, 1)

    def bad(ws, col, row_of):
        ws.cell(row=row_of[rid], column=col["admin_title"]).value = "Test Role"
        ws.cell(row=ws.max_row, column=col["researcher_id"]).value = 99999999

    def good(ws, col, row_of):
        ws.cell(row=row_of[rid], column=col["admin_title"]).value = "Test Role"

    assert _upload(client, _workbook(client, bad))["errors"]
    result = _upload(client, _workbook(client, good))
    assert result["errors"] == [] and result["updated"] == 1
    assert _admin_title(db, rid) == "Test Role"
