# API Folder — Detailed Suggestions

Based on a line-by-line review of the `API/` folder (requesters, domain models, services, and clients).

---

## 1. Critical Bugs (Fix First)

| File | Issue | Suggestion |
|------|-------|------------|
| `LocatieService.py:38` | `update_locatie_by_uuid` parameter `bron_asset_uuid` is typed as `AssetDTO` but used as a `str`. | Fix the type hint to `str`, or accept both via overload. |

---

## 2. Design Pattern Violations

### 2.1 Dangerous module-level monkey-patch
`eminfra/EMInfraDomain.py:7-25` replaces `dataclasses._asdict_inner` globally.  
**Suggestion:** Remove the monkey-patch. Use a custom `asdict` implementation or a mixin class instead. If serialization control is required, implement it in `BaseDataclass` without mutating `dataclasses` internals.

### 2.2 Duplicated `_by_uuid` / by-object wrapper pattern
Every service duplicates methods that take a UUID directly and convenience wrappers that extract the UUID from an asset/object (e.g., `get_x_by_uuid` + `get_x`, `update_x_by_uuid` + `update_x`).  
**Suggestion:** Introduce a small filter/mixin or use a decorator to reduce the ~2x method proliferation across all service classes.

### 2.3 Duplicated pagination loops
Near-identical `while True` pagination logic is copy-pasted across `AssetService`, `ToezichterService`, `AssettypeService`, `EventService`, etc.  
**Suggestion:** Extract a shared cursor/offset pagination helper (e.g., `PaginatedIterator` or an internal generator) to avoid copy-paste and inconsistent cursor handling.

### 2.4 Duplicated error-handling template
`raise ProcessLookupError(response.content.decode("utf-8"))` + `logging.error(response)` is repeated in almost every API call.  
**Suggestion:** Add a single `_raise_for_status(self, response, method)` or similar to `AbstractRequester` / a mixin. Services will no longer need inline error handling.

---

## 3. Error Handling Inconsistencies

### 3.1 Wrong exception type
`ProcessLookupError` (an `OSError` subclass meant for `os.kill`) is used everywhere to signal HTTP/API failures.  
**Suggestion:** Create a domain-specific exception, e.g., `EMInfraAPIError(RuntimeError)` or `HTTPClientError(requests.HTTPError)`, or at least use `requests.HTTPError` with `response` attached.

### 3.2 Inconsistent logging
Some failing calls log before raising (e.g., `BestekService`, `GeometrieService`), while others do not (e.g., `ToezichterService.get_toezichter_by_uuid`, `AssetService.get_asset_by_uuid`).  
**Suggestion:** Make error handling uniform—either always log + raise, or delegate to a shared helper.

### 3.3 Inconsistent status codes
Some methods expect `200`, others expect `202`; there is no project-wide convention.  
**Suggestion:** Document the expected status code per operation type (GET -> 200, PUT -> 202, etc.) or make it configurable.

---

## 4. Naming & Conventions

### 4.1 Dutch/English mixing
Docstrings and comments are largely in Dutch (`Ophalen van het GeometrieKenmerk`, `Zoek actieve child-assets`), while method names and class names are English.  
**Suggestion:** Standardize on English for code, comments, and docstrings to keep the surface area consistent, especially since the domain objects (e.g., `Bestek`, `Beheerobject`) are already English-ish abstractions. Alternatively, if Dutch is preferred, rename methods and classes to Dutch for full consistency.

### 4.2 Shadowing built-ins
- `AssetService.py:396` uses parameter name `filter` (shadows built-in `filter`).
- `ToezichterService.py:97` uses parameter name `type` (shadows built-in `type`).  
**Suggestion:** Rename to `filter_`, `type_`, or use more descriptive names (`filter_dict`, `relatie_type`).

### 4.3 camelCase field names in dataclasses
`EMInfraDomain.py` uses `totalCount`, `createdOn`, `modifiedOn`, `akteBlad`, `code` etc. in dataclass fields while Python convention strongly prefers `snake_case`.  
**Suggestion:** Keep DTO fields internally consistent with JSON keys, but consider adding aliases or renaming to snake_case (`total_count`, `created_on`) and mapping to/from camelCase in `from_dict` / `asdict`.

### 4.4 `from_` inconsistency
`DTOList` uses `_from` while `QueryDTO` uses `from_` to work around the reserved word. The inconsistency is confusing.  
**Suggestion:** Use `from_` consistently everywhere, or use `offset` / `position` for pagination start to avoid the reserved-word workaround entirely.

### 4.5 Static-like methods called on instances
`AssetService.search_parent_asset_by_uuid:264` calls `BeheerobjectService.get_beheerobject(self, ...)` — passing `self` explicitly to a method that is not a classmethod/staticmethod. This is syntactically wrong (will raise `TypeError` at runtime).  
**Suggestion:** Ensure all cross-service calls use proper instance methods or classmethods.

---

## 5. Hardcoded Values

### 5.1 Hardcoded UUIDs as class constants
Several services use hardcoded kenmerktype UUIDs:
- `BestekService.BESTEKKOPPELING_UUID`
- `GeometrieService.GEOMETRIE_UUID`
- `LocatieService.LOCATIE_UUID`
- `ToezichterService.TOEZICHTER_UUID`
- `GraphService.DEFAULT_GRAPH_RELATIE_TYPES` (long list of UUIDs)  
**Suggestion:** Move these into a dedicated configuration mapping file (or `eminfra/Generic.py`) so they can be updated without touching service logic.

### 5.2 Hardcoded dictionary in `Generic.py`
The `RelatieEnum` → UUID mapping is hardcoded.  
**Suggestion:** If the set of relations grows or changes, this requires a code change. Load from a JSON/YAML resource file, or fetch dynamically from the API if available.

### 5.3 Hardcoded query sizes
Repeated `size=10`, `size=100`, `size=1000` across services.  
**Suggestion:** Define module-level constants with descriptive names (e.g., `DEFAULT_PAGE_SIZE = 100`, `LARGE_PAGE_SIZE = 1000`).

---

## 6. Type Hint Issues

### 6.1 Missing generic parameters
`list[str]` written as `[str]` in multiple places (`EMInfraDomain.py:211, 217, 277, 329`); `dict` used without parameters; `Generator` used without type parameters.  
**Suggestion:** Use proper generics (`list[str]`, `dict[str, Any]`, `Generator[AssetDTO, None, None]`) and enable `mypy --strict` or a similar linter.

### 6.2 Non-None defaults typed as optional
Several parameters have `= None` but are not union-hinted with `None`:
- `GraphService.get_graph_by_uuid`: `relatietypes: list = None` — missing `list[str] | None`.
- `BestekService.add_bestekkoppeling`: `asset: AssetDTO = None` without `| None`.
- `ToezichterService.search_toezichtgroep_lgc`: `type: ToezichtgroepTypeEnum = None` — parameter named `type` shadows built-in and is not union-hinted.
- `EMInfraDomain.py` `QueryDTO`, `SelectionDTO`, etc.: several optional defaults lack `| None`.  
**Suggestion:** Add `| None` to all optional defaults. Run a type checker to find all instances.

### 6.3 Incorrect type annotations
- `AssetService.get_objects_from_oslo_search_endpoint_gen`: `filter_dict: dict = '{}'` — default is a `str`, not a `dict`.
- `BestekService.change_bestekkoppelingen_by_uuid`: parameter typed as `[BestekKoppeling]` instead of `list[BestekKoppeling]`.  
**Suggestion:** Fix the annotation; also consider whether `filter_dict` should default to `{}` instead of `'{}'`.

---

## 7. Mutable / Problematic Default Arguments

### 7.1 `datetime.now()` evaluated at definition time
Default values in method signatures capture `datetime.datetime.now(...)` at import time:
- `BestekService.add_bestekkoppeling_by_uuid`
- `BestekService.add_bestekkoppeling`
- `BestekService.end_bestekkoppeling_by_uuid`
- `BestekService.end_bestekkoppeling`
- `BestekService.replace_bestekkoppeling_by_uuid`
- `BestekService.replace_bestekkoppeling`  
**Suggestion:** Use `None` as the sentinel default and call `datetime.datetime.now(datetime.timezone.utc)` inside the method body.

### 7.2 `from_dict` mutates input dict
`BaseDataclass.from_dict` modifies the input dict in place (`dict_[f'{k}_'] = ...; del dict_[k]`).  
**Suggestion:** Copy the input dict before mutating it (`dict_.copy()`), or use a comprehension to avoid side effects.

---

## 8. Requesters

### 8.1 `AbstractRequester` bases URL from `first_part_url + url`
In several clients (`EMSONClient`, `SNGatewayClient`, `Locatieservices2Client`, `FSClient`) the constructor appends a path fragment to `self.requester.first_part_url`.  
**Suggestion:** Make `first_part_url` truly immutable (e.g., store it as a private `_base_url` and strip the trailing slash). Appending to a public string is error-prone and makes retries reuse a mutated URL suffix.

### 8.2 `JWTRequester` checks module presence via `sys.modules`
`JWTRequester.__init__:21` checks `'cryptography' not in sys.modules`. This is brittle and can yield false positives/negatives.  
**Suggestion:** Use an explicit `try: import cryptography; except ImportError: raise ModuleNotFoundError(...)`.

### 8.3 `CookieRequester` and `CertRequester` inherit header mutation differently
Both mutate `kwargs['headers']` in similar but not identical ways. `CookieRequester` uses `kwargs.setdefault`, while `CertRequester` uses a more convoluted loop.  
**Suggestion:** Extract a shared `_apply_default_headers` helper or move the logic to `AbstractRequester._request_with_retries`.

### 8.4 `JWTRequester.generate_authentication_token` uses `random.choice`
Line 93 uses `choice(string.ascii_lowercase)` for `jti`. This is not cryptographically secure.  
**Suggestion:** Use `secrets.token_urlsafe(20)` instead of a random lowercase string.

### 8.5 `OneDriveClient` does not use `AbstractRequester`
`OneDriveClient` uses raw `requests.get/post/put` instead of the project's retry-enabled `AbstractRequester`.  
**Suggestion:** Either integrate `OneDriveClient` with `AbstractRequester` (if gecko is possible), or document why it intentionally bypasses the shared requester.

---

## 9. Other Issues

### 9.1 `BaseDataclass.asdict` shadowing
`BaseDataclass.asdict()` calls `asdict(self)` where `asdict` is the module-level alias for `dataclasses.asdict`. This is correct due to scoping, but the method name shadows the module-level alias and is fragile.  
**Suggestion:** Rename the instance method to `to_dict` and keep module-level `asdict` clean.

### 9.2 Dead code
- `EMInfraDomain.py:174-191` contains a large commented-out `__post_init__` block. **Remove it or extract it to a base mixin.**
- `GraphService.py` imports `AssetDTO` on line 3 but never uses it. **Remove the import.**

### 9.3 Missing `settings_path` / `cookie` validation
`RequesterFactory.create_requester` opens `settings_path` without checking if it exists, and `settings.json` is read with bare `json.load`.  
**Suggestion:** Add `Path(settings_path).exists()` guards and explicit error messages.

### 9.4 `query_dto_helpers.py` imports a top-level `QueryDTO` that is also defined locally in `EMSONClient.py`
`EMSONClient.Query` redefines a `BaseDataclass` when `eminfra/EMInfraDomain.py` already has a `QueryDTO`.  
**Suggestion:** Reuse `QueryDTO` from `EMInfraDomain.py` in `EMSONClient.py` instead of redefining `Query`.

### 9.5 `FSClient.download_layer_to_records` is a confusing generator
It uses `yield from` inside a loop where the loop itself is already being consumed as a generator. This makes the control flow hard to follow and the chunk remainder logic fragile.  
**Suggestion:** Refactor into a clean generator function, or consider using `ijson` / `jsonlines` for line-delimited JSON streaming.

---

## 10. Summary

| Priority | Count | Area |
|----------|-------|------|
| P0 | 4 | Bugs (infinite recursion, wrong variable, wrong type hints) |
| P1 | ~6 | Design duplication (pagination, error handling, by_uuid wrappers) |
| P2 | 8 | Hardcoded values, error types, type hint fixes |
| P3 | ~5 | Naming consistency, dead code, module-level monkey-patch |
| P4 | 4 | Requester improvements, module-level imports |

**Recommended refactoring order:**
1. Fix the 4 critical bugs.
2. Replace `ProcessLookupError` with a proper exception family.
3. Extract shared pagination and error-handling helpers.
4. Clean up hardcoded UUIDs / sizes.
5. Standardize naming conventions (Dutch vs English, snake_case fields).
6. Remove the module-level monkey-patch and dead code.

---

## 11. Additional Issues — Deep Review of `eminfra/` Services

### 11.1 Architectural / Coupling Issues

- **Tight coupling between services via direct method invocation**: `SchadebeheerderService` calls `KenmerkService.get(self, ...)` directly (`SchadebeheerderService.py:15`), passing `self` (a `SchadebeheerderService` instance) to `KenmerkService.get`, relying on duck-typing (both classes happen to have `self.requester`). This creates hidden, fragile coupling between services.
  - **Suggestion:** Extract a shared utility or base mixin for common kenmerk operations, or inject the dependency explicitly.

- **Cross-service static-like calls**: `AssetService.search_parent_asset_by_uuid:264` calls `BeheerobjectService.get_beheerobject(self, ...)`. `RelatieService.zoek_verweven_asset:160` calls `AssetService.get_asset_by_uuid(self, ...)`. Both bypass proper instance method semantics.
  - **Suggestion:** These should either be proper instance method calls (instantiate `BeheerobjectService` properly), or be moved to a coordinator/service layer that holds references to both services.

- **Local service instantiation inside methods**: `EigenschapService.get_eigenschappen` (line 110) imports and instantiates `KenmerkService` locally inside the method body. This hides the dependency, makes testing harder, and wastes resources on every call.
  - **Suggestion:** Move `KenmerkService` to the class-level dependency graph (e.g., inject via `__init__` or class attribute).

### 11.2 State Mutation & Side Effects

- **Generators mutate caller's `QueryDTO`**: Multiple generators mutate the input `QueryDTO` object for pagination state:
  - `ToezichterService.search_toezichtgroep_lgc` (line 196): `query_dto.from_ += query_dto.size`
  - `EventService.search_events_by_uuid_generator` (line 113)
  - `AgentService.search_betrokkenerelaties` (line 48)
  - `BeheerobjectService.search_beheerobjecten_generator` (line 42)
  - Because generators are lazy and may not be fully consumed, or may be re-used, mutating the input object breaks idempotency and causes state leakage across calls.
  - **Suggestion:** Pass `page_size` and `current_offset` as local variables in the generator, or use a dedicated pagination cursor/state object that is not shared with the caller.

- **`from_dict` mutates input dict in place**: `BaseDataclass.from_dict` does `dict_[f'{k}_'] = dict_[k]; del dict_[k]`. If the caller reuses the original dict, it will find mutated keys.
  - **Suggestion:** Copy the input dict before mutating (`dict_.copy()`).

### 11.3 Inconsistent HTTP Status Code Expectations

There is no uniform policy for expected status codes per HTTP verb:
- `GET` generally expects `200`, but `DocumentService.download_document` follows links with implicit assumption of `200`.
- `PUT` expects `202` in `DocumentService`, `BestekService`, `AssetService`.
- `POST` expects `200` in `AssetService.create_asset_by_uuid`, but `GraphService.get_graph_by_uuid` expects `201`.
- `GraphService.py:62` checks for `201` explicitly.
- **Suggestion:** Document the expected status code per operation type, or make it configurable per verb in `AbstractRequester`.

### 11.4 Response Handling Inconsistencies

- **Unsafe direct indexing into response JSON**: Many methods call `.json()` and immediately index `['data']` without checking if the key exists (e.g., `EigenschapService.py:21`, `KenmerkService.py:39`, `AssettypeService.py:44`, `BeheerobjectService.py:48`). If the API returns an error payload without a `data` key, a `KeyError` is raised instead of a meaningful API error.
  - **Suggestion:** Use `dict.get('data', [])` or add explicit validation before accessing nested keys. Raise a custom `EMInfraAPIError` when the response structure is unexpected.

- **`DocumentService.download_document` does `json.loads(response.content)`** instead of `response.json()` (line 30). This is inconsistent with the rest of the codebase and adds an unnecessary intermediate step.
  - **Suggestion:** Use `response.json()` consistently.

- **`remove_postit` returns the raw response object** (`PostitService.py:168`), while other `remove_*` methods return `response.json()` (parsed dict) or `None`. This inconsistency forces callers to handle two different return types for the same conceptual operation.
  - **Suggestion:** Standardize all `remove_*` methods to return `None` on success with a 2xx/202 status, or return the parsed JSON body consistently.

### 11.5 Security Issues

- **Path traversal risk in `DocumentService.download_document`**: The filename comes directly from `document.naam` (`DocumentService.py:25, 35`) and is written to disk with `open(f'{directory}/{file_name}', 'wb')`. If `document.naam` contains `../` sequences, the file could be written outside the intended directory.
  - `Path` is imported but not used; `os.path.join` or `pathlib.Path /` should be used for safe path construction.
  - **Suggestion:** Sanitize `file_name` (remove path separators), use `Path(directory) / file_name` and verify the resolved path stays within `directory`.

- **Sending literal `None` in JSON bodies**: Several methods include `None` values in JSON payloads (e.g., `PostitService.py:130` fallback). Python `json.dumps` converts `None` to `null`. If the backend does not expect `null` for optional fields, this could cause validation errors or, worse, unexpected state changes.
  - **Suggestion:** Use a helper that strips `None` values from dicts before serialization, or only include keys when values are not `None`.

### 11.6 Performance Concerns

- **`BeheerobjectService.create_beheerobject` fetches all beheerobjecttypes on every call** when `beheerobjecttype` is not provided (`BeheerobjectService.py:59` - `get_beheerobjecttypes()`). There is no caching. If the default type is static, this is an unnecessary network round-trip per creation.
  - **Suggestion:** Cache the list of types at module or class level, or require the caller to always provide the type.

- **`PostitService.edit_postit` always fetches the existing postit before editing** (`PostitService.py:125`), even if all three editable fields are explicitly provided. This means a partial-update always incurs a GET + PUT instead of just a PUT.
  - **Suggestion:** Skip the GET when all fields are provided, or accept an optional `merge_existing: bool = True` parameter.

### 11.7 Testability Concerns

- **No mapper/response_handler abstraction**: Almost every method does `response.json()` then list-comprehension into DTOs. Because `requester` is an opaque dependency, unit tests must mock HTTP responses with exact JSON shapes. There is no `response_handler` or `mapper` interface that could be stubbed independently.
  - **Suggestion:** Introduce a response-mapper layer or dependency-inject a `deserializer` function to make unit tests lighter.

- **Generators with hidden input mutation**: Because `QueryDTO` is mutated during pagination, tests cannot safely iterate the same generator twice, run two generators concurrently with the same `QueryDTO`, or assert on the original `QueryDTO` state after consumption.
  - **Suggestion:** Ensure generators are pure from the caller's perspective — the input object should not be mutated.

### 11.8 Import and Type Issues

- **`Generic.py:103` uses old-style return type `-> (str, str)`** instead of the modern `tuple[str, str]`. Old-style parenthesized expressions are parsed as grouped expressions, not tuple types, and confuse type checkers.
  - **Suggestion:** Change to `tuple[str, str]`.

- **Unnecessary imports**: `EigenschapService` imports `KenmerkTypeEnum` and `KenmerkType` from `EMInfraDomain` (lines 4-6). `KenmerkTypeEnum` is used only in `get_eigenschappen` (line 105), and `KenmerkType` is imported but never used.
  - **Suggestion:** Remove unused imports and move `KenmerkTypeEnum` to where it is actually needed.

- **`EigenschapService.get_eigenschappen` parameter `naam` shadows built-in**: The `naam` parameter declaration line shadows nothing, but the local usage is fine. However, `KenmerkService` also has `naam` parameters which is fine. Wait — actually `EigenschapService` fine. But `KenmerkService.get_kenmerken_by_uuid` signature `naam: str = ''` — empty string default for a filter is fine. No issue here.

- **`wkt_validator.py` catches `(ShapelyError, Exception)`**: `Exception` is a superclass of `ShapelyError`, so the `ShapelyError` catch is redundant. More importantly, catching `Exception` swallows `KeyboardInterrupt`, `SystemExit`, and unrelated runtime errors, making debugging silent failures very difficult.
  - **Suggestion:** Catch only the specific exceptions expected (`ValueError`, `WKTReadingError` or whatever Shapely raises for invalid WKT), and let everything else propagate.

### 11.9 Docstring and Naming Issues

- **Mismatched docstring type declarations**: 
  - `DocumentService.get_documents_by_uuid_generator` docstring declares `:type size: str` even though the parameter is `int` (DocumentService.py:97).
  - `DocumentService.get_documents_generator` docstring also declares `:type size: str` (DocumentService.py:124).
  - **Suggestion:** Fix the docstrings to match the actual type `int`.

- **Missing docstrings**: 
  - `BeheerobjectService.get_beheerobject` (`BeheerobjectService.py:10`) has no docstring.
  - `OnderdeelService.create_onderdeel` (`OnderdeelService.py:8`) has no docstring.
  - **Suggestion:** Add docstrings to public methods.

- **`EventService.search_events_generator` docstring duplicates the `by_uuid` variant verbatim** (`EventService.py:117-135`), including the note about `created_before`/`created_after` date precision, but does not document that `asset` can be `None`.
  - **Suggestion:** Rewrite the docstring to reflect the actual signature and parameters of `search_events_generator`.

- **`status` vs `actief` inconsistency**: `BeheerobjectService.update_beheerobject_status` uses a parameter named `status: bool`, while many other services use `actief`. This domain-verb inconsistency makes the API surface confusing.
  - **Suggestion:** Standardize on `actief` (or `is_actief`) for boolean enabled/disabled flags across all services, or add an explicit `status` mapping.

### 11.10 Python Best-Practice Violations

- **Old-style tuple return type**: `Generic.py:103` uses `-> (str, str)` instead of `-> tuple[str, str]`.
- **Unnecessary f-strings for simple values**: Frequent use of `f'{asset_uuid}'`, `f'{bron_asset.uuid}'`, `f'{rol}'` where plain values or `str()` conversion would suffice (e.g., `RelatieService.py:35-36`).
- **Direct dict access without guards**: `DocumentService.download_document` does `document.document['links'][0]['href']` without `.get()` or membership checks. If `links` is missing or empty, this crashes.
  - **Suggestion:** Add `.get('links', [])` and check length before indexing.
- **`PostitService.edit_postit`** uses `existing_postit.commentaar or commentaar` (line 155) which silently replaces falsy but valid values (like empty string `""`) with the new value. If a caller explicitly passes `commentaar=""` to clear a postit, the existing non-empty comment is preserved because `""` is falsy.
  - **Suggestion:** Use `if commentaar is not None` instead of truthiness checks.

- **`LocatieService.update_locatie_by_uuid` parameter type hint mismatch**: `bron_asset_uuid: AssetDTO` and `doel_asset_uuid: AssetDTO` are typed as full DTO objects, but are actually used as string UUIDs (interpolated as `f'{doel_asset_uuid}'`).
  - **Suggestion:** Change the type hint to `str | AssetDTO` or just `str`.

- **`ToezichterService.search_identiteit` has `actief: Optional[bool] = True`** (`ToezichterService.py:127`). `Optional[bool]` implies `None` is meaningful, yet `None` is never handled — the parameter is always coerced to a boolean filter or skipped.
  - **Suggestion:** Change to `actief: bool = True`, and only append the filter when `actief` is explicitly `True`. If `None` is a valid "don't filter" value, change the default to `None` and handle it explicitly.

- **`EigenschapService.get_eigenschappen` returns `Eigenschap | None`** but raises `ProcessLookupError` on error instead of returning `None` for API failures (line 120). The `None` in the type hint suggests a "not found" semantic, but `ProcessLookupError` is raised instead.
  - **Suggestion:** Distinguish between "not found" (return `None`) and "API error" (raise exception).

- **`BestekService.add_bestekkoppeling` parameter `asset: AssetDTO = None` without `| None`**: The type hint declares `AssetDTO` but the default is `None`.
  - **Suggestion:** Change to `AssetDTO | None`.

- **`GeometrieService.update_geometrie` signature mismatch**: The method accepts `asset: AssetDTO` and internally calls `get_geometrie_by_uuid(asset_uuid=asset)` where `asset_uuid` expects a `str`. The method also has `validate_wkt` but the internal implementation passes the DTO instead of `asset.uuid`.
  - **Suggestion:** Fix the internal method calls to use `asset.uuid` consistently.

### 11.11 `wkt_validator.py` Catching Bare `Exception`

- Line 18 catches `(ShapelyError, Exception)`. `Exception` is a broad catch that swallows `KeyboardInterrupt`, `SystemExit`, and any unrelated runtime errors.
  - **Suggestion:** Catch only the specific exceptions Shapely raises for invalid WKT (`WKTReadingError`, `GEOSException`).

### 11.12 `EMSONClient.Query` Duplicates `QueryDTO`

- `EMSONClient.py:10` defines a local `Query(BaseDataclass)` with `size`, `filters`, `orderByProperty`, `fromCursor`, when `eminfra/EMInfraDomain.py` already has a `QueryDTO` with `size`, `from_`, `selection`, `fromCursor`, `orderByProperty`.
  - **Suggestion:** Reuse `QueryDTO` from `EMInfraDomain.py`, or rename `QueryDTO` to match the EMSON endpoint's expected body shape.

### 11.13 `AbstractRequester` URL Mutation

- Several clients append path fragments to `self.requester.first_part_url` in their constructors (`EMSONClient`, `SNGatewayClient`, `Locatieservices2Client`, `FSClient`). This mutates a public string attribute, making retries reuse the mutated URL suffix.
  - **Suggestion:** Make `first_part_url` immutable by storing a private `_base_url` and composing the full URL in each request. Do not mutate `self.requester.first_part_url` after creation.

### 11.14 `RequesterFactory.create_requester` Path Validation

- `RequesterFactory.create_requester` opens `settings_path` with `open(settings_path)` without checking if the file exists first. For `JWT` and `CERT` authentication, this raises a raw `FileNotFoundError` without context.
  - **Suggestion:** Add `Path(settings_path).exists()` guards and explicit error messages before opening.
