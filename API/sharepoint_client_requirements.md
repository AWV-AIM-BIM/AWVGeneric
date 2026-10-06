# SharePoint Client Requirements

This document lists every capability the new SharePoint client must provide to fully replace the existing Google Drive upload/download layer. Each requirement is derived from the current `scripts/ops/gdrive_upload.py`, `scripts/ops/drive_sync_gate.py`, `outputs/ms_graph_upload.py`, and `outputs/report_routes.py` modules.

---

## 1. Authentication & Credential Management

1. **OAuth 2.0 device/browser login flow** (`first_login`) — interactive login via browser, persisting a token for future sessions.
2. **Token persistence and auto-refresh** (`_load_credentials`) — load a stored credential/token, detect expiry, and refresh automatically using a refresh token.
3. **Service/client factory** (`_build_service`) — construct an authenticated Microsoft Graph API client (or authenticated HTTP session) from the persisted token.

## 2. Folder Resolution & Creation

4. **Get or create a single folder by name** (`_get_or_create_folder`) — find an existing folder by name under a parent (by `drive_id` / site / parent folder id), or create it if missing.
5. **Resolve a nested folder path** (`_get_or_create_folder_path`) — given a path like `RSA/RSA_OneDrive`, walk segments and create each missing parent folder, returning the final folder identifier.

## 3. Listing & Lookup

6. **List children of a folder** (`_list_children`) — enumerate all immediate child items (folders and files) within a given remote folder/drive-id, with pagination.
7. **Find a child by name** (`_find_child_by_name`) — locate a single child item (file or folder) by name within a parent folder.

## 4. Download (SharePoint → Local Mirror)

8. **Clear local mirror target** (`_clear_local_mirror_target`) — remove all contents of a local folder before downloading, while **preserving** local-only control folders (`archief`, `archivedreports`, `staged_summaries`, `logs`).
9. **Download a single file** (`_download_file`) — download a single file by its item-id into a local path, with resumable/streaming capability.
10. **Recursively download a folder tree** (`_download_tree`) — walk a remote folder tree and mirror all files into a local directory.
11. **Skip temporary/lock workbooks on download** (`_is_temporary_workbook`, `_is_safe_component_name`, `_is_expected_root_folder_name`) — skip `_tmp_` suffixed temporary workbooks, `~$` lock-prefix files, `.lock` suffixed files, unsafe path-like or control-character names, and unexpected root-level folders/files that do not match the bucket pattern (`0000-0099`) or `Overzicht`.
12. **Public download mirror** (`sync_drive_to_local`) — high-level function: resolve/ensure a remote folder path, clear the local mirror target, download the full tree, return success/failure.

## 5. Upload (Local Mirror → SharePoint)

13. **Upload or update a single file once** (`_upload_or_update_file_once`) — create a new file or update an existing one in a target folder, replacing a conflicting folder with file deletion when names collide.
14. **Upload or update a single file with retries** (`_upload_or_update_file`) — wrap single-file upload with retry logic on transient errors, building a fresh upload session per attempt.
15. **Recursively sync a local directory to SharePoint** (`_sync_local_dir_to_drive`) — mirror an entire local directory tree to a remote folder: create missing folders, upload new files, update changed files, and **delete** remote-only files/folders that no longer exist locally. Returns counts of (uploaded, updated, errors).
16. **Public upload mirror** (`sync_local_to_drive`) — high-level function: authenticate, ensure remote folder path, run `_sync_local_dir_to_drive`, log summary, return success/failure.
17. **Legacy top-level upload** (`upload_folder_to_drive`) — upload only top-level files matching a set of extensions (e.g. `.xlsx`), skipping root-level files and temporary workbooks.

## 6. Deletion

18. **Delete a file/folder recursively** (`_delete_drive_item_recursive`) — delete an item and, if it is a folder, delete all its contents first.

## 7. Local Mirror Validation

19. **Discover expected report buckets** (`_discover_expected_buckets`) — scan the `Reports/` and `ArchivedReports/` directories for `Report####` files to compute the expected set of bucket folder names (`0000-0099`, etc.).
20. **Validate local mirror layout** (`validate_local_mirror`) — check that the local mirror contains at minimum: an `Overzicht` folder (case-insensitive, created if missing), an `Overzicht/[RSA] Overzicht rapporten.xlsx` workbook, a `logs` folder (created if missing), all expected bucket folders (created if missing), and at least one bucket folder. Returns `(bool, reason)`.

## 8. Run Log Management

21. **Write a dated run log entry** (`write_daily_run_log`) — append a timestamped status line (e.g. `POST_RUN_UPLOAD_START`, `POST_RUN_UPLOAD_DONE`, `POST_RUN_UPLOAD_FAILED`) into a `logs/run_YYYYMMDD.log` file inside the local folder.
22. **Prune old daily run logs** (`prune_daily_run_logs`) — keep only the newest N daily run log files (default 14) under `local_folder/logs`.

## 9. Temporary File & Skip Filters

23. **Detect temporary/lock workbooks** (`_is_temporary_workbook`) — return `True` for any filename containing `_tmp_`, starting with `~$`, or ending with `.lock`.
24. **Check should-skip names** (`_should_skip`) — return `True` for folder/file names that should never be mirrored (`archief`, `archivedreports`, `staged_summaries`, `logs`).
25. **Validate safe component name** (`_is_safe_name`) — reject names containing `/` or `\`, empty names, `.`, `..`, or control characters.
26. **Check expected root folder name** (`_is_expected_root_folder_name`) — return `True` for `overzicht` (case-insensitive) or names matching `\d{4}-\d{4}`.

## 10. Retry & Error Handling

27. **Retryable error detection** (`_is_retryable_drive_error`) — classify a given exception as transient/retryable (timeouts, connection errors, HTTP 408/429/5xx, rate-limit/quota keywords).
28. **Retry decorator** (`_retry_on_drive_error`) — retry a wrapped API call with exponential backoff (base delay 2s, max delay 120s, max retries 5) on retryable errors, using a shared configurable set of retry parameters.

## 11. CLI Interface

29. **Command-line interface** (`_main`) — argparse-based CLI with subcommands mirroring the original:
   - `login` — perform one-time browser login and persist token.
   - `sync-down` — mirror a SharePoint folder to a local folder.
   - `sync-up` — mirror a local folder to a SharePoint folder.
   - `upload` — legacy top-level file upload with filterable extensions.

## 12. Pipeline State Integration

30. **External orchestrator polling gate** (`DailyDriveSyncGate`) — observe an external pipeline-state store (SQLite) for `sharepoint_download` and `sharepoint_upload` phases/statuses to coordinate when report execution may proceed.
31. **Upload-after-run hook** (`upload_after_run`) — callable attached to `ReportLoopRunner.on_run_complete`; sets pipeline-state phase to `sharepoint_upload`, uploads the local mirror via `sync_local_to_drive`, and updates pipeline-state to `completed` or `failed` accordingly.

## 13. Microsoft Graph Uploader Abstraction

32. **Graph upload target dataclass** (`GraphUploadTarget`) — holds a `drive_id` and `folder_path` identifying a SharePoint/OneDrive destination.
33. **Single-file Microsoft Graph uploader** (`MsGraphUploader.upload_file`) — upload a single local file to a `GraphUploadTarget` via the Microsoft Graph API. (Originally a placeholder in `outputs/ms_graph_upload.py`; needs full implementation.)

## 14. Cross-Module Compatibility

34. **SharePoint URL generation** (`report_sharepoint_url` in `outputs/report_routes.py`) — generate a SharePoint URL for a report workbook given its report number and filename. Already partly defined; the SharePoint client must be consistent with this URL scheme.
35. **Bucket-name consistency** (`report_bucket_name`) — the bucket folder naming convention (`<start>-<end>`, e.g. `0000-0099`) must be shared between the client and `report_routes.py`.
36. **Settings/config schema** — new `sharepoint_sync` settings block in `settings_sample.json` (and runtime config loader in `main.py`) to replace the current `drive_sync` / `google_api` keys, including:
   - `enabled` (bool)
   - `sync_after` (HH:MM:SS)
   - `poll_after` (HH:MM:SS)
   - `poll_deadline` (HH:MM:SS)
   - `sharepoint_folder` (remote folder/site path)
   - `credentials_path` (SharePoint/Graph OAuth credentials)
   - `local_folder` (local mirror path)
   - `token_path` (persisted token path)

## 15. Test Compatibility

37. **Testable internal functions** — the internal helper functions (`_list_children`, `_download_tree`, `_sync_local_dir_to_drive`, `_get_or_create_folder_path`, `validate_local_mirror`, `_discover_expected_buckets`, `_is_temporary_workbook`, `_should_skip`) must remain importable and individually testable so the existing unit tests in `UnitTests/test_gdrive_upload.py` and `UnitTests/test_gdrive_sync_logs_preserved.py` can be adapted with minimal friction.
