#!/usr/bin/env python3
"""Export recorded Git history and matching committed source for Sprint 3.

Uses Python's standard library and the installed Git executable. Run after
merging the handover files and fetching all available branches and tags.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile


REQUIRED_FILES = (
    "README.md",
    "app.py",
    "requirements.txt",
    "docs/INSTALLATION.md",
    "docs/USER_GUIDE.md",
    "docs/DEVELOPER_GUIDE.md",
    "docs/HANDOVER.md",
    "scripts/export_handover.py",
)
ARCHIVE_PREFIX = "cits3200-team20/"


class ExportError(Exception):
    """A condition that prevents a complete handover export."""


def git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "--no-pager", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise ExportError(message or f"Git returned exit status {result.returncode}")
    return result.stdout


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_text(path: Path, value: str) -> None:
    path.write_text(value, encoding="utf-8", newline="\n")


def export(repo: Path, ref: str, output: Path) -> tuple[str, int]:
    if not ref or ref.startswith("-"):
        raise ExportError("Supply a commit SHA or branch/tag name, such as origin/main.")

    root = Path(git(repo, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    if git(root, "rev-parse", "--is-shallow-repository").strip() == b"true":
        raise ExportError(
            "This clone has shallow history. Run 'git fetch --unshallow origin', "
            "fetch the required branches/tags, and retry."
        )
    commit = git(root, "rev-parse", "--verify", f"{ref}^{{commit}}").decode().strip()
    paths = set(git(root, "ls-tree", "-r", "--name-only", "-z", commit).split(b"\0"))
    missing = [name for name in REQUIRED_FILES if name.encode() not in paths]
    if missing:
        raise ExportError(
            "The selected commit is missing required project/handover files: "
            + ", ".join(missing)
            + ". Commit/merge the files, fetch, and select the final release."
        )

    output = output.expanduser().resolve()
    if output == root or root in output.parents:
        raise ExportError("Choose a new output directory outside the Git repository.")
    if output.exists():
        raise ExportError(f"Output already exists; choose a new directory: {output}")

    # Freeze the available refs before producing both the ref list and their log.
    refs = git(
        root, "for-each-ref", "--format=%(refname) %(objectname)",
        "refs/heads", "refs/remotes", "refs/tags",
    )
    ref_commits: set[str] = set()
    for line in refs.decode("utf-8", errors="replace").splitlines():
        _name, object_id = line.rsplit(" ", 1)
        # Some tags can point to trees/blobs rather than commits.
        try:
            ref_commits.add(
                git(root, "rev-parse", "--verify", f"{object_id}^{{commit}}").decode().strip()
            )
        except ExportError:
            continue
    all_commits = sorted(ref_commits)
    log_args = (
        "log", "--no-color", "--no-decorate", "--no-notes",
        "--no-show-signature", "--no-use-mailmap", "--encoding=UTF-8",
        "--date=iso-strict", "--format=fuller",
    )
    release_log = git(root, *log_args, commit, "--")
    branch_log = git(root, *log_args, *all_commits, "--") if all_commits else b""
    release_count = int(git(root, "rev-list", "--count", commit, "--"))
    branch_count = int(git(root, "rev-list", "--count", *all_commits, "--")) if all_commits else 0
    head = git(root, "rev-parse", "--verify", "HEAD").decode().strip()
    status = git(root, "status", "--short", "--untracked-files=normal").decode("utf-8", errors="replace")
    difference = git(root, "diff", "--no-ext-diff", "--name-status", commit, "--").decode("utf-8", errors="replace")

    # Refuse to overwrite any earlier export. A failed export has no manifest.
    output.mkdir(parents=True, exist_ok=False)
    try:
        (output / "commit_log.txt").write_bytes(release_log)
        (output / "all_branch_commit_log.txt").write_bytes(branch_log)
        (output / "refs.txt").write_bytes(refs)
        write_text(output / "final_commit.txt", commit + "\n")
        write_text(
            output / "working_tree_status.txt",
            f"Selected release: {commit}\nWorking checkout HEAD: {head}\n\n"
            "Git status relative to checkout HEAD (untracked names included):\n"
            + (status or "(clean)\n")
            + "\nTracked working files compared with selected release:\n"
            + (difference or "(no tracked differences)\n")
            + "\nThe source ZIP contains the selected commit only.\n",
        )
        git(
            root, "archive", "--format=zip", f"--prefix={ARCHIVE_PREFIX}",
            f"--output={output / 'source.zip'}", commit,
        )
        with zipfile.ZipFile(output / "source.zip") as archive:
            names = set(archive.namelist())
        missing_archive = [name for name in REQUIRED_FILES if ARCHIVE_PREFIX + name not in names]
        if missing_archive:
            raise ExportError(
                "Required files were excluded from the source archive: "
                + ", ".join(missing_archive)
                + ". Review the repository's archive/export-ignore attributes."
            )

        write_text(
            output / "README.txt",
            "CITS3200 Team 20 - final code and Git history\n\n"
            f"Selected ref: {ref}\nRelease commit: {commit}\n\n"
            "commit_log.txt: all ancestors of the selected release, including merges,\n"
            "with recorded author/committer identities, dates and complete messages.\n"
            "all_branch_commit_log.txt: history reachable from the available branch,\n"
            "remote-tracking and tag refs recorded in refs.txt. Deleted or inaccessible\n"
            "branches may be absent. A detached release still has its own commit log.\n"
            "source.zip: tracked source at the selected release, using git archive.\n"
            "Uncommitted/ignored runtime files and .git history are not added. Git\n"
            "attributes can exclude archive files or substitute archive placeholders.\n"
            "Supply agreed generated data and the deployment record separately.\n"
            "working_tree_status.txt: local checkout differences, not extra ZIP content.\n"
            "manifest.json: export time, commit counts, file sizes and SHA-256 hashes.\n\n"
            "No Git authors, messages or history were rewritten. This exporter does not\n"
            "fetch, push, deploy, or assert client acceptance. Inspect the archive and\n"
            "match the release SHA before uploading to the allocated Teams directory.\n",
        )
        files = {
            path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in sorted(output.iterdir()) if path.is_file()
        }
        manifest = {
            "project": "CITS3200 Team 20",
            "exported_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "selected_ref": ref,
            "release_commit": commit,
            "checkout_head": head,
            "git_version": git(root, "--version").decode().strip(),
            "shallow_repository": False,
            "release_commit_count": release_count,
            "available_refs_commit_count": branch_count,
            "working_tree_clean": not bool(status),
            "tracked_files_match_release": not bool(difference),
            "archive_prefix": ARCHIVE_PREFIX,
            "files": files,
        }
        write_text(output / "manifest.json", json.dumps(manifest, indent=2) + "\n")
    except Exception as error:
        raise ExportError(
            f"Export incomplete in {output}; do not submit it. "
            f"Fix the cause and choose a new output directory. Cause: {error}"
        ) from error
    return commit, release_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="origin/main", help="final release ref (default: origin/main)")
    parser.add_argument("--output", type=Path, required=True, help="new directory outside the repository")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Git checkout (default: current directory)")
    args = parser.parse_args()
    try:
        commit, count = export(args.repo, args.ref, args.output)
    except (ExportError, OSError, ValueError) as error:
        print(f"Handover export failed: {error}", file=sys.stderr)
        return 1
    print(f"Exported {count} release commits and matching source at {commit}")
    print(f"Output: {args.output.expanduser().resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
