# AWVGeneric — API Folder Summary

The `API` folder is the core SDK layer of AWVGeneric. It provides HTTP clients, authentication strategies, shared enums, domain models (DTOs), and service classes that wrap the EM-Infra REST API and related Flemish government services.

## Top-level structure

```
API/
├── AbstractRequester.py       # Base `requests.Session` with URL prefix and retry logic
├── RequesterFactory.py        # Factory for authenticated requesters (JWT, CERT, COOKIE)
├── Enums.py                   # Environment and AuthType enums
├── CookieRequester.py         # Cookie-based auth (Davie, ServiceNow Gateway)
├── JWTRequester.py            # JWT/OAuth2 auth via Flemish Authenticatie (RSA private key)
├── CertRequester.py           # Mutual TLS client certificate auth
├── EMSONClient.py             # EMSON OTL asset/relatie search client (cursor paging)
├── SNGatewayClient.py         # ServiceNow Gateway asset-filter CRUD
├── OneDriveClient.py          # Microsoft OneDrive Graph API client (MSAL)
├── Locatieservices2Client.py  # Location-services puntlocatie lookups (XY / wegsegment)
├── Locatieservices2Domain.py  # Dataclass models for location-service responses
├── FSClient.py                # FeatureServer GeoJSON downloader (streaming)
├── settings_loader.py         # Utility to load local `settings.json`
└── eminfra/                   # EM-Infra domain models + service layer
    ├── __init__.py            # Empty
    ├── EMInfraClient.py       # Facade wiring all sub-services together
    ├── EMInfraDomain.py       # ~935 lines: BaseDataclass, enums, DTOs
    ├── AssetService.py        # Asset CRUD, tree traversal, search generators
    ├── RelatieService.py      # Asset relation management (create, search, remove)
    ├── Generic.py             # RelatieEnum → (kenmerktype_id, relatietype_id) UUID mapping
    ├── BestekService.py       # Contract/bestek koppeling management (add, end, replace, adjust dates)
    ├── DocumentService.py     # Document upload/download/mgmt on assets
    ├── EigenschapService.py   # Eigenschap (property) read/update/search
    ├── KenmerkService.py      # Kenmerk (attribute) read/update/add on assets/assettypes
    ├── LocatieService.py      # Locatie (WKT / relatie-based) update on assets
    ├── GeometrieService.py    # Geometrie (WKT geometry log) CRUD on assets
    ├── ToezichterService.py   # Toezichter (supervisor) and toezichtGroep management
    ├── AgentService.py        # Agent and betrokkenerelatie CRUD
    ├── PostitService.py       # Post-it note CRUD on assets
    ├── BeheerobjectService.py # Beheerobject CRUD, tree reorganization, asset removal
    ├── OnderdeelService.py    # Onderdeel creation
    ├── AssettypeService.py    # Assettype search, list, legacy/OTL filtering
    ├── GraphService.py        # Asset graph extraction by UUID/depth/relatietypes
    ├── FeedService.py         # Feedproxy page retrieval
    ├── EventService.py        # Event and eventcontext search (audit/historiek)
    ├── SchadebeheerderService.py # Schadebeheerder (damage manager) management
    └── wkt_validator.py       # Shapely-based WKT geometry validation
```

## Requesters (HTTP clients + auth)

### `AbstractRequester.py`
- Extends `requests.Session`.
- Adds `first_part_url` prefix and retry logic (configurable `retries`, default 3).
- All HTTP verbs (`get`, `post`, `put`, `patch`, `delete`) go through `_request_with_retries`.
- Retries on non-2xx responses and `RequestException`; raises `RuntimeError` after exhaustion.
- `_get_error_details_from_response` tries JSON `message` field, falls back to UTF-8 content decode.

### `Enums.py`
- `Environment`: `PRD`, `DEV`, `TEI`, `AIM`.
- `AuthType`: `JWT`, `CERT`, `COOKIE`.

### `RequesterFactory.py`
- `create_requester(auth_type, env, settings_path, cookie)` → `AbstractRequester`.
- Maps `Environment` → base URL (`services.apps.mow.vlaanderen.be/` variants).
- Reads `settings.json` for JWT/CERT credentials.
- `COOKIE` mode does **not** read settings; requires a raw `cookie` string and strips `services.` from the URL prefix.

### `CookieRequester.py`
- Sets `Cookie: acm-awv={cookie}` header.
- Overrides all HTTP verbs to inject `accept: application/json` and `Content-Type: application/vnd.awv.eminfra.v1+json`.

### `JWTRequester.py`
- Authenticates against `https://authenticatie.vlaanderen.be/op`.
- Generates RS256 JWT assertion from a private key file (read as JWK via `pyjwt.algorithms.RSAAlgorithm.from_jwk`).
- Exchanges assertion for OAuth2 access token (`grant_type=client_credentials`, scope `awv_toep_services`).
- Caches token until near expiry (`expires = requested_at + expires_in - 1 minute`).
- Injects `Authorization: Bearer <token>` header on every request.
- Strips `Content-Type` when `files` are in kwargs (for multipart uploads).

### `CertRequester.py`
- Validates `cert_path` and `key_path` existence.
- Passes `cert=(cert_path, key_path)` to `requests` on every verb.
- Injects `accept: application/json` and `Content-Type: application/vnd.awv.eminfra.v1+json`.

## Top-level API clients

### `EMSONClient.py`
- Endpoint: `emson/`.
- `get_asset_by_uuid(uuid)` → single asset dict.
- `get_assets()` → cursor-paged generator of all assets.
- `get_assetrelatie_by_uuid(uuid)` → single assetrelatie dict.
- `get_assets_by_filter(filter, size, order_by_property)` → POST `api/otl/assets/search` cursor-paged generator.
- `get_assetrelaties_by_filter(filter, size, order_by_property)` → POST `api/otl/assetrelaties/search` cursor-paged generator.
- Uses `Query` dataclass (`size`, `filters`, `orderByProperty`, `fromCursor`).

### `SNGatewayClient.py`
- Endpoint: `sngateway/`.
- `get_all_asset_filters()` → `rest/eminfra/asset-filter` GET.
- `add_new_asset_filter(uri, enabled)` → POST.
- `modify_asset_filter(id, uri, enabled)` → PUT.
- `enable_asset_filter(uri)` / `disable_asset_filter(uri)` → idempotent helpers.

### `OneDriveClient.py`
- Uses `msal` + `requests` (not the internal `AbstractRequester`).
- Token persistence to JSON file; interactive login + silent refresh.
- Endpoints: Microsoft Graph `v1.0/me/drive/...`.
- `list_root_files()`, `download_file_by_name(filename, save_path)`, `upload_file(local_path, onedrive_path)`.
- `list_folder_files()` and `delete_file()` are `NotImplementedError`.

### `Locatieservices2Client.py`
- Endpoint: `locatieservices2/`.
- `zoek_puntlocatie_via_xy(x, y, zoekafstand)` → `WegsegmentPuntLocatie`.
- `zoek_puntlocatie_via_wegsegment(ident8, opschrift, afstand)` → `WegsegmentPuntLocatie`.

### `Locatieservices2Domain.py`
- `BaseDataclass` (duplicated from `EMInfraDomain`): custom `_asdict_inner` monkey-patch, `from_dict`, `_fix_enums`, `_fix_nested_classes`, `_fix_nested_list_classes`, `RESERVED_WORD_LIST = ('from_', '_next')`.
- DTOs: `WegsegmentId`, `JSONGeom`, `Wegnummer`, `Referentiepunt`, `RelatievePositie`, `WegsegmentPuntLocatie`.
- `WegsegmenttypeEnum`: `WEGSEGMENTPUNTLOCATIE`.

### `FSClient.py`
- Endpoint: `geolatte-nosqlfs/cert/api/databases/featureserver/`.
- `download_layer(layer, file_path)` → streaming download with `tqdm` progress bar.
- `download_layer_to_records(layer, chunk_size)` → generator yielding newline-delimited JSON records with `tqdm` record counter.
- `_process_chunk(chunk_rest, pbar)` → splits chunk on `\n`, yields lines, keeps remainder.

### `settings_loader.py`
- `load_settings(settings_path=None)` → loads `./settings.json` by default.
- Raises `FileNotFoundError` with guidance to copy `settings.example.json`.

## `eminfra/` subpackage

### `EMInfraClient.py`
- Facade: instantiates 17 sub-services and exposes `get_oef_schema_as_json(name)`.
- All sub-services share one `RequesterFactory.create_requester(...)` instance; URL prefix is `eminfra/`.

### `EMInfraDomain.py` (~935 lines)
**Base infrastructure:**
- Monkey-patches `dataclasses._asdict_inner` to respect `__dict_factory_override__` (supports reserved words, enum serialization).
- `BaseDataclass`: `asdict()`, `json()`, `from_dict()`, `_fix_enums`, `_fix_nested_classes`, `_fix_nested_list_classes`, `__str__`.
- `RESERVED_WORD_LIST = ('from_', '_next')` — strips trailing underscore for JSON.

**Enums:**
- `OperatorEnum`: EQ, CONTAINS, GT, GTE, LT, LTE, IN, STARTS_WITH, INTERSECTS.
- `LogicalOpEnum`: AND, OR.
- `PagingModeEnum`: OFFSET, CURSOR.
- `DirectionEnum`: ASC, DESC.
- `GeometryNiveau`: MIN_1, NUL, PLUS_1.
- `GeometryBron`: MANUEEL, MEETTOESTEL, OVERERVING.
- `GeometryNauwkeurigheid`: _5 through _200.
- `KenmerkTypeEnum`: HEEFTBIJLAGEBRON, GEOMETRIE, AGENTS, LOCATIE, BESTEK, HOORTBIJ, VOEDT, etc.
- `RelatieEnum`: Full set of onderdeel URIs (BEVESTIGING, VOEDT, HOORTBIJ, GEMIGREERDNAAR, SluitAanOp, etc.).
- `BestekKoppelingStatusEnum`: ACTIEF, INACTIEF, TOEKOMSTIG.
- `BestekCategorieEnum`: WERKBESTEK, AANLEVERBESTEK.
- `SubCategorieEnum`: ONDERHOUD, INVESTERING, ONDERHOUD_EN_INVESTERING.
- `DocumentCategorieEnum`: ~25 values (ASBUILT_DOSSIER, FOTO, ELEKTRISCH_SCHEMA, etc.).
- `ProvincieEnum`: ANTWERPEN, WEST_VLAANDEREN, OOST_VLAANDEREN, VLAAMS_BRABANT, LIMBURG, BRUSSEL.
- `ToezichtgroepTypeEnum`: INTERN, EXTERN.
- `AssetDTOToestand`: IN_ONTWERP, GEPLAND, GEANNULEERD, IN_OPBOUW, IN_GEBRUIK, VERWIJDERD, OVERGEDRAGEN, UIT_GEBRUIK.
- `ObjectType`: INSTALLATIE, ONDERDEEL, BEHEEROBJECT, EIGENSCHAP, KENMERKTYPE.
- `BoomstructuurAssetTypeEnum`: ASSET, BEHEEROBJECT.
- `ApplicationEnum`: EM_INFRA, ELISA_INFRA.

**Key DTOs:**
- `Link`, `ResourceRefDTO`, `DTOList`, `AssettypeDTO`, `AssettypeDTOList`, `TermDTO`, `ExpressionDTO`, `SelectionDTO`, `ExpansionsDTO`, `QueryDTO`.
- `BestekRef`, `BestekKoppeling`, `EventType`, `EventContext`, `Event`.
- `InfraObjectDTO`, `AssetDTO`, `BeheerobjectDTO`, `BeheerobjectTypeDTO`.
- `DocumentDTO`, `AssetDocumentDTO`, `RelatieTypeDTO`, `RelatieTypeDTOList`, `PostitDTO`.
- `AgentDTO`, `BetrokkenerelatieDTO`, `IdentiteitKenmerk`, `ToezichtgroepDTO`, `SchadebeheerderKenmerk`.
- `KenmerkTypeDTO`, `KenmerkType`, `AssetTypeKenmerkTypeDTO`, `AssetTypeKenmerkTypeAddDTO`.
- `Eigenschap`, `EigenschapValueDTO`, `EigenschapValueUpdateDTO`.
- `LocatieKenmerk`, `ElektrischAansluitpuntKenmerk`, `GeometryLog`, `GeometrieKenmerk`.
- `ToezichterKenmerk`, `ToezichtKenmerkUpdateDTO`.
- `AssetRelatieDTO`, `GraphLinks`, `Graph`.

**Helper function:**
- `construct_naampad(asset)` → builds slash-separated path from asset up through parent chain.

### `AssetService.py`
- `get_asset_by_uuid(asset_uuid)` → `AssetDTO`.
- `_update_asset(asset, naam, actief, toestand, commentaar)` → PUT with partial merge.
- `update_asset_by_uuid`, `update_asset`, `update_toestand_by_uuid`, `update_toestand`, `update_commentaar_by_uuid`, `update_commentaar`.
- `activeer_asset` / `deactiveer_asset` (by UUID or AssetDTO).
- `_search_assets_helper_generator(query_dto)` → offset-paged generator.
- `search_assets_generator(query_dto, actief)` → optional active filter appended.
- `search_asset_by_name_generator(asset_name, exact_search)` → EQ or CONTAINS.
- `search_child_assets_by_uuid_generator(asset_uuid, recursive)` → depth-first generator.
- `search_parent_asset_by_uuid(asset_uuid, recursive, return_all_parents)` → walks `parent` chain, resolves `InfraObjectDTO` or `BeheerobjectDTO`.
- `create_asset_by_uuid_and_relatie(asset_uuid, naam, assettype, relatie)` → single POST creating asset + relation.
- `create_asset_by_uuid(parent_asset_uuid, naam, assettype, parent_assettype)` → POST to `assets/{uuid}/assets`.
- `get_assets_by_filter_gen(filter, size)` → delegating generator for Oslo search.
- `get_objects_from_oslo_search_endpoint_gen(url_part, filter_dict, size, expansions_fields)` → cursor-paged Oslo endpoint generator.

### `RelatieService.py`
- `search_relaties_generator(asset_uuid, kenmerktype_id, relatietype_id)` → `RelatieTypeDTO` generator.
- `create_assetrelatie(bron_asset, doel_asset, relatie)` → POST `core/api/assetrelaties`.
- `get_assetrelatie(assetrelatie_uuid)` → GET.
- `search_assetrelaties(bron_asset_uuid, doel_asset_uuid, relatie)` → QueryDTO-based search, returns list.
- `search_assetrelatie_otl(bron_asset_uuid, doel_asset_uuid)` → raw `@graph` dicts.
- `search_assets_via_relatie(asset_uuid, relatie)` → list of `AssetDTO`.
- `remove_relatie(bron_asset_uuid, doel_asset_uuid, relatie)` → PUT `ops/remove`.
- `zoek_verweven_asset(bron_asset_uuid)` → follows `GemigreerdNaar` relatie to OTL asset.

### `Generic.py`
- `get_kenmerktype_and_relatietype_id(relatie: RelatieEnum)` → `(str, str)`.
- Hardcoded mapping of 20+ `RelatieEnum` values to their `kenmerktype_uuid` and `relatietype_uuid` UUIDs.

### `BestekService.py`
- `BESTEKKOPPELING_UUID = 'ee2e627e-bb79-47aa-956a-ea167d20acbd'`.
- `get_bestekkoppeling_by_uuid`, `get_bestekkoppeling` → list of `BestekKoppeling`.
- `get_bestekref(eDelta_dossiernummer, eDelta_besteknummer)` → single `BestekRef` via search.
- `change_bestekkoppelingen_by_uuid(asset_uuid, bestekkoppelingen)` → PUT full list.
- `adjust_date_bestekkoppeling_by_uuid` → modifies start/end dates in place.
- `end_bestekkoppeling_by_uuid` → sets eindDatum to now (default), adds dummy start if missing.
- `add_bestekkoppeling_by_uuid` → adds new koppeling if not already present.
- `replace_bestekkoppeling_by_uuid` → end existing + add new atomically.

### `DocumentService.py`
- `download_document(document, directory)` → follows link chain to download PDF.
- `_create_document(file_path)` → uploads to `dms/api/documenten` → `DocumentDTO`.
- `upload_document(asset_uuid, file_path, documentcategorie, omschrijving)` → uploads doc + bulk-create on asset.
- `get_documents_by_uuid_generator(asset_uuid, size, categorie)` → offset-paged generator of `AssetDocumentDTO`.
- `_bulk_create(asset_uuid, file_name, documentcategorie, omschrijving, document)` → POST `bulk-create`.
- `remove_document(asset_uuid, document)` → PUT `ops/delete`.

### `EigenschapService.py`
- `get_all_eigenschappen_as_text_generator(size)` → paginated raw string list.
- `search_eigenschappen(eigenschap_naam, uri)` → query-based search.
- `update_eigenschap_by_uuid(asset_uuid, eigenschap, kenmerktype)` → PATCH with `EigenschapValueDTO` or `EigenschapValueUpdateDTO`.
- `list_eigenschap(kenmerktype_id)` → list of `Eigenschap`.
- `get_eigenschappen(asset_uuid, kenmerktype)` → single or `None`.
- `search_eigenschapwaarden` / `get_eigenschapwaarden` → eigenschapwaarden lookups.

### `KenmerkService.py`
- `get(asset, kenmerk_uuid)` / `put(asset, kenmerk_uuid, payload)` → raw GET/PUT on kenmerk.
- `get_kenmerktype_by_uuid(assettype_uuid)` → list of `AssetTypeKenmerkTypeDTO`.
- `get_kenmerktype_by_naam(naam)` → single `KenmerkTypeDTO` via search.
- `add_kenmerk_to_assettype(assettype_uuid, kenmerktype_uuid)` → POST.
- `update_kenmerk_by_uuid` / `update_kenmerk` → PUT.
- `get_kenmerken_by_uuid(asset_uuid, naam)` → list of `KenmerkType`, optional name filter by `KenmerkTypeEnum`.
- `get_kenmerk_hoortbij_by_uuid` → shortcut for `HEEFTBIJHORENDEASSETS`.

### `LocatieService.py`
- `LOCATIE_UUID = '80052ed4-2f91-400c-8cba-57624653db11'`.
- `get_locatie_by_uuid` / `get_locatie` → `LocatieKenmerk`.
- `update_locatie_by_uuid` / `update_locatie` → WKT or relatie-based PUT.

### `GeometrieService.py`
- `GEOMETRIE_UUID = 'aabe29e0-9303-45f1-839e-159d70ec2859'`.
- `get_geometrie_by_uuid` / `get_geometrie` → `GeometrieKenmerk`.
- `delete_geometrie_by_uuid` / `delete_geometrie` → DELETE log.
- `add_geometrie_by_uuid` / `add_geometrie` → POST new WKT log entry.
- `update_geometrie_by_uuid` / `update_geometrie` → get + delete + add (replace).

### `ToezichterService.py`
- `TOEZICHTER_UUID = 'f0166ba2-757c-4cf3-bf71-2e4fdff43fa3'`.
- `get_toezichter_by_uuid` / `get_toezichter` → `ToezichterKenmerk`.
- `update_toezichtkenmerk(asset_uuid, toezichtkenmerkupdate)` → PUT with optional toezichter + toezichtGroep.
- `add_toezichter` → deprecated, both mandatory.
- `get_identiteit(toezichter_uuid)` → `IdentiteitKenmerk` from `identiteit/api`.
- `get_toezichtgroep(toezichtgroep_uuid)` → `ToezichtgroepDTO`.
- `search_toezichtgroep_lgc(naam, type)` → offset-paged generator.
- `search_identiteit(naam, bron, actief)` → multi-part CONTAINS search on name fields.

### `AgentService.py`
- `search_agent(naam, ovocode, actief)` → paginated generator of `AgentDTO`.
- `search_betrokkenerelaties(query_dto)` → paginated generator of `BetrokkenerelatieDTO`.
- `add_betrokkenerelatie(asset, agent_uuid, rol)` → POST `core/api/betrokkenerelaties`.
- `remove_betrokkenerelatie(betrokkenerelatie_uuid)` → DELETE.

### `PostitService.py`
- `search_postits_generator(asset_uuid, start_datum, eind_datum)` → optional date-filtered generator.
- `get_postit(asset_uuid, postit_uuid)` → single `PostitDTO`.
- `add_postit(asset_uuid, commentaar, start_datum, eind_datum)` → POST.
- `edit_postit(asset_uuid, postit_uuid, commentaar, start_datum, eind_datum)` → PUT, preserves existing values for omitted params.
- `remove_postit(asset_uuid, postit_uuid)` → PUT `ops/remove`.

### `BeheerobjectService.py`
- `get_beheerobject(beheerobject_uuid)` → `BeheerobjectDTO`.
- `search_beheerobjecten_generator(naam, beheerobjecttype, actief, operator)` → paginated.
- `get_beheerobjecttypes()` → list of `BeheerobjectTypeDTO`.
- `create_beheerobject(naam, beheerobjecttype)` → defaults to `INSTAL (Beheerobject)`.
- `wijzig_boomstructuur_by_uuid` / `wijzig_boomstructuur` → `ops/reorganize` PUT.
- `update_beheerobject_status(beheerObject, status)` → PUT.
- `remove_asset_from_parent_by_uuid` / `remove_asset_from_parent` → `ops/remove`.

### `OnderdeelService.py`
- `create_onderdeel(naam, type_uuid)` → POST `core/api/onderdelen`.

### `AssettypeService.py`
- `get_assettype(assettype_uuid)` → `AssettypeDTO`.
- `search_assettype(uri)` → exact URI search.
- `get_all_assettypes_generator(size)` → paginated.
- `get_all_legacy_assettypes_generator(size)` → filters `korteUri.startswith('lgc:')`.
- `get_all_otl_assettypes_generator(size)` → filters out URIs containing `:`.

### `GraphService.py`
- `DEFAULT_GRAPH_RELATIE_TYPES` → 23 hardcoded relatietype UUIDs.
- `get_graph_by_uuid(asset_uuid, depth, relatietypes, actief)` → POST `core/api/assets/graph` → `Graph`.
- `get_graph(asset, depth, relatietypes, actief)` → convenience wrapper.

### `FeedService.py`
- `get_feedproxy_page(feed_name, page_num, page_size)` → `feedproxy/feed/{name}/{page}/{size}` → `FeedPage`.

### `EventService.py`
- `get_all_eventtypes_generator()` → `core/api/events/eventtypes`.
- `search_eventcontexts_generator(omschrijving)` → cursor search on eventcontexts.
- `search_events_by_uuid_generator(asset_uuid, created_after, created_before, created_by, event_type, event_context)` → rich filter search.
- `search_events_generator(asset, ...)` → wrapper passing `asset.uuid`.

### `SchadebeheerderService.py`
- `SCHADEBEHEERDER_UUID = 'd911dc02-f214-4f64-9c46-720dbdeb0d02'`.
- `get_schadebeheerder` / `get_schadebeheerder_by_uuid` → `SchadebeheerderKenmerk | None`.
- `get_schadebeheerder_by_name(name)` → `core/api/beheerders/search`.
- `add_schadebeheerder_by_uuid` / `add_schadebeheerder` → PUT via `KenmerkService.update_kenmerk_by_uuid`.

### `wkt_validator.py`
- `is_valid_wkt(wkt_string)` → `shapely.wkt.loads` + `geom.is_valid`.

## Design notes

- **Service classes** follow a uniform pattern: `__init__(self, requester)` stores the requester, methods come in `_by_uuid` and `by_asset` pairs.
- **Pagination** is mostly cursor-based or offset-based via generators; no shared pagination helper exists.
- **Error handling**: non-2xx responses consistently raise `ProcessLookupError(response.content.decode("utf-8"))`.
- **Domain model**: `BaseDataclass` is duplicated between `EMInfraDomain.py` and `Locatieservices2Domain.py`.
- **Naming**: DTOs use camelCase field names mapped from JSON; `from_` is used to avoid the Python reserved word `from`.
- **Hardcoded UUIDs**: Several services use hardcoded kenmerktype UUIDs (e.g., `LOCATIE_UUID`, `GEOMETRIE_UUID`, `TOEZICHTER_UUID`, `BESTEKKOPPELING_UUID`, `SCHADEBEHEERDER_UUID`).

## `utils/` folder

Shared helper modules used across the project (primarily by `UseCases/` and `API/eminfra/`).

### `date_helpers.py`
- `get_winter_summer_time_interval(date, timezone='Europe/Brussels')` → `1` (winter) or `2` (summer) using `pytz`.
- `validate_dates(start_datetime, end_datetime)` → validates at least one date is provided and that start < end; raises `ValueError` otherwise.
- `format_datetime(datetime)` → formats to `'%Y-%m-%dT%H:%M:%S.000+0X:00'` where `X` is `1` or `2` based on DST.

### `eigenschap_helpers.py`
- `validate_ean(ean)` → validates an 18-digit Belgian EAN number (must start with `54`) using the Cypher checksum algorithm (`(3 * even + odd + check_digit) % 10 == 0`).

### `locatieservice_helpers.py`
- `convert_ident8(ident8, direction='P')` → converts short road notation (e.g., `N8`) to long 8-character ident8 (e.g., `N0080001`), handling letter suffixes (`a`→901, ..., `z`→926) and direction (`P`→`1`, `N`→`2`).

### `query_dto_helpers.py`
- `add_expression(query_dto, property_name, operator, date_value)` → helper to append a date-formatted `ExpressionDTO` to a query.
- `build_query_search_dnblaagspanning(eanNummer, assettype_uuid)` → pre-built `QueryDTO` filtering by EAN eigenschap, assettype, and actief.
- `build_query_search_energiemeter(energiemeter_naam, assettype_uuid)` → pre-built `QueryDTO` filtering by naam, assettype, and actief.
- `build_query_search_assettype(assettype_uuid)` → pre-built `QueryDTO` filtering by assettype UUID and actief.

### `spatial.py`
- `load_gemeente_to_gdf(path, crs, target_crs)` → loads municipality GeoJSON into a `geopandas.GeoDataFrame` with safe WKT parsing.
- `point_in_polygons(point_wkt, gdf, col)` → checks if a WKT `Point` lies inside polygons in the GeoDataFrame; returns the value of `col` from the first hit or `None`.

### `wkt_geometry_helpers.py`
- `format_locatie_kenmerk_lgc_2_wkt(locatie)` → converts a `LocatieKenmerk`'s `punt` location to `POINT Z(x y z)` WKT.
- `parse_coordinates(wkt_geom)` → extracts integer `[x, y, z]` from a `POINT Z(...)` WKT string; returns `None` for NaN.
- `coordinates_2_wkt(coords)` → converts 2–4 coordinate values to `POINT Z(...)` WKT.
- `geometries_are_identical(wkt_geom1, wkt_geom2)` → compares two Point WKTs by parsed coordinates.
- `get_euclidean_distance_wkt(wkt1, wkt2)` → Euclidean distance between two Point WKTs.
- `get_euclidean_distance_coordinates(x1, y1, x2, y2)` → Euclidean distance between two coordinate pairs.
- `generate_osm_link(wkt_str, crs_input, crs_output, osm_zoom)` → converts WKT to lat/lon and returns an OpenStreetMap URL; returns `None` on geometry errors.

### `toezichter_helpers.py`
- `get_toezichter_naam(eminfra_client, asset)` → fetches the full name (`voornaam + naam`) of the toezichter assigned to an asset by chaining `EMInfraClient` calls.
