# Handover and submission

The Sprint 3 instructions supplied to the team require the final system as source and as an installation on the client's chosen platform, the client-required documentation including an installation guide and user guide, and a copy of the GitHub commit logs in the team's MS Teams directory. They also call for the final code copy in Teams where feasible. Individual reflection and SPARK+ are separate submissions.

## 1. Finalise the release

- Merge the reviewed code and documentation into the agreed release branch.
- Identify the master-data version and deliver its dictionary and supporting tables.
- Check the installation and user instructions on the actual client platform.
- Record the production handover details below and provide credentials separately.
- Confirm the exact submission locations and deadlines in the current unit instructions.

### Deployment record

Complete this record with the hosting owner when deployment is verified. Do not put passwords or API keys here.

| Detail | Value to record |
|---|---|
| Client website URL | Confirmed HTTPS address |
| Hosting platform and owner | Service/VM owner and maintenance contact |
| Release commit | Full Git commit SHA |
| Master dataset | Version/date and delivered filename |
| Service operation | Start/restart command or service name |
| Backups | Location, retention and last successful restore check |
| Administrator access | Who received access and date; credentials supplied separately |
| Handover check | Reviewer, date and recorded outcome |

## 2. Export authentic Git logs and matching source

Use a real Git clone or Codespace, not an extracted GitHub ZIP. After the final PR has merged, fetch the repository's branches and tags:

```bash
git fetch origin --tags '+refs/heads/*:refs/remotes/origin/*'
git rev-parse --is-shallow-repository
```

If the second command prints `true`, obtain the remaining history, then check again:

```bash
git fetch --unshallow origin
git fetch origin --tags '+refs/heads/*:refs/remotes/origin/*'
```

Run the exporter from the repository root:

```bash
python scripts/export_handover.py --ref origin/main --output ../cits3200-final-handover
```

If the agreed final branch is not `main`, replace `origin/main` with that branch. Choose a new output directory for each release. The script reads the selected committed version; it does not push, switch branches, modify project files or include uncommitted changes. It refuses shallow history and a selected commit missing the handover documentation.

| Output | Purpose |
|---|---|
| `commit_log.txt` | Full commit messages, authors, committers and dates reachable from the selected release |
| `all_branch_commit_log.txt` | History reachable from locally available branch, remote-tracking and tag refs |
| `refs.txt` | Ref names and SHAs available during export |
| `final_commit.txt` | Exact selected release SHA |
| `source.zip` | Tracked source at that same commit, with documentation |
| `working_tree_status.txt` | Shows whether local work differed from the exported commit |
| `manifest.json` | Export details, counts and checksums |
| `README.txt` | Contents and scope of the export |

The branch log covers fetched refs; deleted or inaccessible branches are not recoverable simply by running this command. Runtime data, secrets and other untracked files are not added to `git archive`. Deliver any agreed generated data separately, rather than assuming it is in the source ZIP. Git author information and commit messages are exported as recorded; the script does not invent or rewrite contributions.

## 3. Submit and verify

1. Open `commit_log.txt` and check that it includes the final documentation/code commit. Confirm `final_commit.txt` matches the agreed release.
2. Inspect `source.zip` and its documentation. Check that no credentials or unintended material have been tracked.
3. Upload the generated handover folder to the allocated Team 20 MS Teams location, together with the agreed master-data package and any separately requested client files.
4. Give the client the installation/user guides and confirmed website details through the team's agreed handover process.
5. Verify the uploaded files open and record completion. Complete reflection and SPARK+ separately.

The source archive, logs and client documentation should refer to the same final release. Generate them again if another PR is merged before submission.

## References

- [Git log documentation](https://git-scm.com/docs/git-log)
- [Git archive documentation](https://git-scm.com/docs/git-archive)
- [Public UWA Sprint 3 definition](https://teaching.csse.uwa.edu.au/units/CITS3200/project/Sprint3_Def.html); check against the current unit instructions.
