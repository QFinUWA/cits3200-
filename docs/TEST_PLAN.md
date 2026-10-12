# Test plan

CITS3200 Group 20. Owner: Zarin. Status tables last updated 12 October 2026.

This says what we test, how, and who signs it off, and it maps onto the four
tests in `Project_Acceptance_Tests.docx`.

## How to run everything

```
python -m pytest tests -q                    # unit and integration tests
python -m pytest tests/test_exported_data.py -q     # the exported CSVs, per university
python load.py                               # rebuild site/research.db from final output
python -m pytest tests/test_database_load.py -q     # the load step lost nothing
python -m pytest tests/test_site_api.py -q          # the API against the real data
python -m pytest tests/test_site_browser.py -q      # the pages in a real browser
python validate_data.py all                  # the deep report a person reads
python app.py                                # then the manual checklist below
```

On Windows, run `$env:PYTHONIOENCODING = "utf-8"` in the terminal first.
Without it six tests in `tests/test_merge_publications.py` fail on an emoji
the default console encoding cannot print (issue 3 below).

The browser tests need `pip install playwright` and `playwright install
chromium`; they skip themselves when it is not installed. The database tests
and the API tests skip when `site/research.db` has not been built. So a plain
checkout still runs green.

Run one university with `-k`, for example
`python -m pytest tests/test_exported_data.py -q -k unsw`.

`validate_data.py` exits non-zero when a university fails, so it can be the
gate on a data PR. `tests/test_site_api.py` skips itself when the database has
not been built, so it never fails for someone who has only cloned the repo.

## What is automated

| Area | Where | Covers |
|---|---|---|
| Adapters and parsing | `tests/test_*_adapter.py`, `test_*_scraper*.py` | each university's own markup |
| Cleaning and exclusions | `tests/test_publication_exclusions.py`, `test_unsw_review_fixes.py` | HTML in titles, malformed DOIs, reviewed namesake papers |
| Export and dedup | `tests/test_export*.py` | duplicates, near-duplicates, ISSN format, column types |
| Discipline screen | `tests/test_screen.py` | wrong-ORCID researchers |
| Exported tables | `validate_data.py` | structure, values, ISSNs, duplicates, links between tables, coverage floors |
| Exported tables, per university | `tests/test_exported_data.py` | columns, vocabularies, DOI and ISSN format, levels, joins between the three files, duplicates, and the cross-university checks the merge depends on |
| The load into the database | `tests/test_database_load.py` | nothing dropped between CSV and database, no orphan rows, no duplicate researchers or journals |
| Website API and counts | `tests/test_site_api.py` | filters, deep links, counts matching the database, academic levels |
| The pages in a browser | `tests/test_site_browser.py` | filters, combined filters, reset, search, sorting, page size, pager, CSV download, metric re-sort, no script errors |

## What is manual

`tests/test_site_browser.py` drives Chromium, so the checklist below is now
about the things a script cannot judge: how it looks, Firefox, and phone
width. Do it before each client demo and record the result at the bottom.

**Researchers page**

- [ ] The page loads with no console errors (F12, Console tab)
- [ ] University, Field of Research, Level and Rows per page each change the table
- [ ] Two filters together narrow the result rather than replacing it
- [ ] Typing a name filters, and clearing it restores the full list
- [ ] Every column header sorts, and clicking twice reverses it
- [ ] Shift-clicking a second header adds a secondary sort
- [ ] The pager moves between pages and the "Showing x of y" count is right
- [ ] Reset clears every filter
- [ ] Download CSV opens a file with the rows currently shown

**Universities page**

- [ ] All eight universities appear
- [ ] Changing the metric and pressing Update re-sorts the table
- [ ] The columns change to match the chosen metric
- [ ] The university code links through to that university's researchers

**Individual researcher page**

- [ ] Opens from a name on the researchers page
- [ ] The publication count matches the number the researchers page showed
- [ ] The search box and the ABDC-only toggle filter the publication list
- [ ] DOI links open the right paper
- [ ] A researcher with no publications shows the explanatory card, not an empty table

**Home and documentation**

- [ ] The eight cards link to the right filtered lists
- [ ] The numbers on the cards match the universities page
- [ ] The documentation page loads and the data dictionary downloads

**Also check**

- [ ] The site is usable at phone width
- [ ] No sample-data banner appears anywhere

## Mapping to the acceptance tests

| Acceptance test | How it is tested | Status on 12 October |
|---|---|---|
| A: all 8 universities scraped | `validate_data.py all`, `test_exported_data.py` | `test_exported_data.py` passes for all eight. `validate_data.py all` reports one failure, on one Monash row (issue 2) |
| B: academic levels mapped | `test_academic_levels_are_A_to_E`, `test_every_researcher_has_an_academic_level` | Passing: all 521 researchers have a level |
| C: website works | `test_site_browser.py` plus the checklist above | The API tests pass. The browser tests were **not run** for this update because Playwright was not installed on the machine used (issue 4). The wrong-rows fault they caught on 29 September has since been fixed |
| D: no duplicate publications | `test_no_duplicate_publications`, `test_a_doi_is_one_paper` | Passing |

## Known open issues

Measured on 12 October with `python -m pytest tests -q`: 1,006 passed, 1 failed,
1 skipped (with the Windows setting above; 7 failed without it).

| # | Issue | Owner |
|---|---|---|
| 1 | `test_doi_status_follows_the_cached_crossref_record` fails for one ANU paper. Isabel Wang's Journal of Business Ethics article (`10.1007/s10551-026-06277-w`) is exported as `forthcoming`, but the journal has since placed it in volume 208, issue 2, so Crossref now implies `published`. Fix: rerun ANU, then remove her row from the `FORTHCOMING` list in `tests/test_anu_final_data.py`. The result depends on the Crossref record saved in each machine's HTTP cache, so this test can pass on one machine and fail on another | ANU |
| 2 | `validate_data.py all` exits non-zero for Monash on one row. The 341-author paper "Nonstandard Errors" has its author list cut short by Monash's page, ending in "320 others", so the list and `author_count` cannot agree | Monash |
| 3 | `tests/test_merge_publications.py` (six tests) fails on Windows on an emoji the console cannot encode. Passes with `PYTHONIOENCODING=utf-8`; the setting is documented in the developer and installation guides. The script itself still crashes the same way when run directly without it | whoever owns merge_publications.py |
| 4 | The browser tests skip silently wherever Playwright is not installed, so a green run does not show they were exercised. Check the skip count | everyone |

Not a fault, but worth knowing: Andrew Terry is listed at both UNSW and USyd
because he is employed at both, and Lisa Powell at Adelaide and at Monash are
two different people. `test_no_researcher_appears_at_two_universities` allows
both by name.

### Resolved since 29 September

| Was | Now |
|---|---|
| 32 researchers had no academic level | None. Titles are read from more places, `data/staff_overrides.csv` fills the rest, and teaching-focused staff, research students and two staff with no academic rank are no longer in the dataset |
| UWA wrote publication statuses outside the agreed set | Every row is `published` or `forthcoming` |
| Adelaide had 1 publication with no year, ANU 3 | No publication is missing a year |
| USyd listed Peter Wolnizer's "Enabling accountability in museums" twice | One copy; the second is in `data/publication_exclusions.csv` |
| Roger Simnett was counted at both UNSW and Monash | Monash only, through `data/staff_exclusions.csv` |
| The researchers page drew whichever answer arrived last | It ignores answers that are not for the latest filter change |
| Three Monash test files stopped `pytest tests` from starting | `selenium` is in `requirements.txt` |

## Sign-off log

| Date | What was tested | By | Result |
|---|---|---|---|
| 22 Sep | Acceptance C and D, Chrome, whole site against real data | Zarin | C passed; D passed on 5 researchers |
| 29 Sep | All four layers, 192 tests, UNSW output rebuilt first | Zarin | 18 failures, all listed above: 16 data and API, 2 browser. UNSW passes its own 16 data tests |
| | | | |
