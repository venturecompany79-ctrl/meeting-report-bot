# Notion Integration for Completed Meeting Reports

## Goal

After a meeting report is successfully generated and moved to the Google Drive DONE folder, create a corresponding sub-page under the Notion "Meeting-bot" page (`36767e678c5980988c0fd8835dd771ce`) containing:

1. The `.docx` report file embedded
2. A link to the source Drive folder
3. The report body rendered as Notion blocks

## Non-Goals

- Backfilling Notion for reports completed before this feature ships
- Two-way sync (editing the Notion page does not affect Drive)
- Notion → Drive direction (we only push to Notion)
- Replacing the existing email notification

## Architecture

New module: `src/notion_client.py`

Exposes a single function:

```python
def create_meeting_subpage(
    parent_page_id: str,
    meeting_name: str,
    drive_folder_url: str,
    docx_external_url: str,
    report_data: dict,
) -> str  # returns the new page URL
```

Internally uses Notion REST API v1 via `requests`. No new SDK dependency.

### Integration point in `main.py`

After the existing `drive.move_folder(fid, DONE_ID)` and before/around `send_completion_email`, add a Notion call inside its own `try/except`. Failure of Notion update must not abort the iteration.

```
move_folder → DONE
docx_drive_url = drive.share_anyone_with_link(docx_file_id)  # NEW
notion_url = notion_client.create_meeting_subpage(...)        # NEW, in try/except
send_completion_email(name, ..., drive_link, notion_url)      # extended
```

### Drive sharing change

The Notion `file` block requires a publicly accessible URL when using `type: "external"`. So the uploaded docx in DONE needs anyone-with-link reader permission. Adds one `permissions().create()` call to `DriveClient`.

This is a deliberate scope expansion the user approved verbally — the docx links become reachable by anyone with the URL.

## Data Flow

1. `generate_report()` returns `report_data` (dict from Gemini JSON output) — already in code
2. `build_docx()` writes the docx — already in code
3. `drive.upload_file()` uploads docx to the meeting folder — already in code, returns file ID
4. `drive.move_folder()` moves folder to DONE — already in code
5. **NEW**: grant anyone-with-link reader on the docx file; get a direct download URL
6. **NEW**: build Notion children blocks from `report_data` and create the sub-page
7. **NEW**: include the Notion page URL in the completion email body

## Block Rendering from `report_data`

`report_data` is a dict (Gemini's JSON output). The exact schema lives in `gemini_client.py` and `docx_builder.py`. `docx_builder.py` already knows how to walk this dict — `notion_client.py` will do the equivalent walk but emit Notion block JSON instead of `python-docx` calls.

Initial mapping (mirroring what `docx_builder.py` does):

- Section title → `heading_2`
- Sub-section title → `heading_3`
- Paragraph text → `paragraph`
- Bullet list items → `bulleted_list_item`

Unknown shapes fall back to a `paragraph` with `str(value)`. We do not try to replicate every docx formatting — Notion gets a readable, structured view, not a pixel match.

Notion API limits children blocks per `pages.create` request to 100. If the report exceeds 100 blocks (unlikely for typical meeting reports but possible), the first 100 go in the create call and the remainder are appended via `blocks.children.append`. This keeps the implementation simple while not crashing on long reports.

## Configuration

New env vars (added to GitHub Actions secrets and the workflow):

- `NOTION_TOKEN` — internal integration token
- `NOTION_PARENT_PAGE_ID` — `36767e678c5980988c0fd8835dd771ce`

The integration must be shared into the Meeting-bot page in the Notion UI by the user. This is a one-time manual setup step documented in the README.

## Error Handling

- Notion call wrapped in `try/except Exception`. On failure: print a warning with the traceback; do NOT move the folder to ERROR; do NOT abort the run; the email still goes out (without the Notion link).
- Reasoning: the report itself succeeded. Drive is the source of truth. Notion is a secondary surface, so a Notion outage or a malformed block should not corrupt the success state.
- Drive sharing permission call is also wrapped — if it fails, we skip the docx embed and still create the Notion page with just the folder link.

## Testing

Manual:
- Run locally against a test meeting folder with the prod Notion token
- Verify sub-page is created with all three sections
- Verify failure mode by temporarily setting an invalid `NOTION_TOKEN` — confirm the docx still lands in DONE and the email still arrives

No automated tests are added — the existing project has none, and one-shot integration with two external APIs is poorly served by mocks.

## Open Questions / Risks

- **anyone-with-link sharing**: user confirmed verbally this is acceptable. If they change their mind later, the docx embed can be removed and the page kept with link-only.
- **Notion rate limits**: 3 req/sec average. With one report per cron tick (hourly) this is a non-issue.
- **Report block volume**: typical reports under 100 blocks. Append-overflow path is implemented defensively but won't usually trigger.
