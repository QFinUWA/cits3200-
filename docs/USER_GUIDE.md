# User guide

Use the website address supplied by the project team. Public browsing needs a web browser and no application account. For a local installation, use the address in the [Installation guide](INSTALLATION.md).

## Find a researcher

1. Open **Researchers**.
2. Choose **University**, **Field of Research** and **Level**, or enter part of a name in **Name**. Filters can be combined.
3. Choose a **Rank by** option: ABDC-ranked articles, A* articles, A articles or total publications.
4. Use column headings to sort, **Rows per page** and the page controls to browse, or **Reset** to clear the filters.
5. Select a researcher's name to open their publication list.

The researcher detail page provides the available profile/ORCID links, a publication search, an **Only show ABDC ranked** filter, and article links. Click a column heading to change the publication order.

## Compare universities

Open **Universities**, choose the metric in **Rank by**, then select **Update**. Available options include researcher counts, article counts, A*/A article counts, articles per researcher and available impact-factor averages. Select a university link to see its researchers.

## Download data

The **Download CSV** button on a researcher ranking or detail page exports its current filtered and sorted result set, including matching rows beyond the visible pagination page.

For complete database exports, use the download links on **Documentation**, or append these paths to the website address:

| Data | Download path |
|---|---|
| Publications | `/downloads/publications.csv` |
| Researchers | `/downloads/researchers.csv` |
| Journals | `/downloads/journals.csv` |
| Field definitions | `/downloads/data-dictionary.md` |

CSV files can be opened in Excel. For identifiers such as DOI, ORCID and ISSN, Excel's **Data → From Text/CSV** import lets you keep those columns as text. Do not sum researcher rows as if they were a list of distinct articles.

## Read the figures correctly

- A publication row counts towards one researcher. A co-authored article can appear for multiple included researchers.
- Historical publications are associated with the included current staff; they are not necessarily publications produced at the current institution.
- Blank indicators mean unavailable or unmatched data, not zero.
- `job_title` preserves the source title. `academic_level` and `academic_title` support comparison; `admin_title` records administrative roles separately.
- Citation indicators change when their source updates. Use the [Data dictionary](DATA_DICTIONARY.md) for definitions and the per-university harvest files for recorded collection dates.

## Administrator access

Open `/admin/login` and enter the password supplied by the maintainer. The **Data management** page provides Excel editing and source refresh. Use **Log out** when finished. Credentials should be handed over separately from the public documentation.

### Update existing records

1. Ask the maintainer to preserve a database backup and confirm that no refresh or rebuild is in progress.
2. Under **Edit data**, choose **Publications**, **Journals** or **Staff (researchers)**.
3. Select **Download Excel** and keep an unchanged copy of that workbook; it is your record of the values before the edit.
4. Edit the required fields. Keep column names and existing ID values intact.
5. Choose the edited `.xlsx` file and press **Upload**. There is no preview step: uploading saves the changes to the live database straight away.
6. Review the inserted, updated and skipped counts and any row errors. If rows report errors, correct them in the workbook and upload it again.
7. Check the affected website records and download a new workbook to confirm the saved values.

Important editing rules:

| Action | Behaviour |
|---|---|
| Edit an existing row | The dataset's ID selects the record to update |
| Leave an editable cell blank | Clears that field where allowed; a required field can produce an error |
| Remove a row from the workbook | Does not delete it from the database |
| Change grey context columns in Publications | Ignored; edit the linked Staff or Journals sheet instead |
| Change journal `quality_rank` or `sjr_quartile` | Updates the copied values on linked publications |
| Receive any row error | Rows without errors may already have been saved. Correct the listed rows and upload the workbook again |

Use a newly downloaded workbook after a database rebuild: numerical IDs can change. Do not reuse an old editing workbook against a new release.

### Add a record

Leave the new row's own ID blank. A new researcher needs a name and university; a new journal needs a journal name. A new publication needs a title and an existing `researcher_id`; any supplied `journal_id` must refer to an existing journal. Add missing staff/journals first, download their allocated IDs, then add linked publications. Check the result counts after each upload before making the next one.

### Keep corrections after refresh

Excel uploads edit the current database. A refresh rebuilds it from the generated CSVs. Ask the data maintainer to retain the same correction in the pipeline or reviewed override files so that it survives the next rebuild. The [Developer guide](DEVELOPER_GUIDE.md) explains this workflow.

### Refresh source data

1. Confirm with the maintainer that reference files, provider access, browser dependencies and backups are ready.
2. Under **Refresh source data**, select one university or **All universities**, then use the refresh button.
3. Monitor the source-by-source status. Fresh retrieval bypasses caches and may take substantially longer than loading the existing dataset.
4. After success, check the public pages and exports. If the job fails, give the maintainer its job ID and message.

The refresh keeps the existing live database until a replacement has been built successfully. Its database backup is recorded in the job status. Generated CSV files can already have changed before a later source fails. Avoid spreadsheet edits, another rebuild or a server restart during a refresh. A process restart interrupts this background job; the page is not a durable job-history system.

## Getting help

For a display problem, record the page, filters, expected result and browser. For a data correction, include the researcher/profile or article link and the field to change. For an administrator problem, include the job ID or upload error and contact the maintainer listed in the handover record.
