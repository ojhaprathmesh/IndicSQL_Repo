# IndicSQL Project Audit

## Existing architecture

- **Backend:** Python 3.10+ and FastAPI in `indicsql/api/server.py`.
- **Query workflow:** The existing pipeline runs language/script detection, schema linking, SQL synthesis, safety validation, DuckDB execution, and response verbalization.
- **Data:** NDAP-style Parquet stores are mounted in the DuckDB sandbox. The schema catalog exposes the available tables and columns.
- **Existing API:** `GET /health`, `GET /schemas`, `GET /analytics`, `POST /query`, `POST /sql/inspect`, and optional Sarvam-backed voice endpoints.
- **Evaluation artifacts:** Benchmark reports, model comparison data, benchmark queries, and failure traces are stored in the repository and served by `/analytics`.
- **Existing clients:** A Next.js web client is present. It is being preserved; the mobile client is a separate Flutter application.

## Working functionality verified before mobile implementation

- `/health`, `/schemas`, `/analytics`, and read-only SQL inspection are implemented in the FastAPI service.
- The SQL inspection endpoint validates the submitted statement and executes it through the existing bounded DuckDB sandbox.
- The `/query` endpoint calls the real IndicSQL pipeline and returns generated SQL, execution results, verbalized output, and audit trace.
- Focused API tests passed. The full Python suite currently has 12 failures in existing benchmark, pipeline, and temporal/data regression tests; these were present before the mobile work.

## Incomplete or unavailable capabilities

- The backend accepts a `session_id` in a query request, but does not persist conversations or use that identifier to restore context.
- `/query` detects language automatically or accepts a validated override for English, Hindi, Hinglish, Marathi, Bengali, Tamil, or Telugu.
- There is no backend API for conversation CRUD, authentication, or centralized query history.
- Analytics are repository evaluation artifacts, not live production telemetry.
- SQL inspection is read-only and bounded; semantic SQL review is not an available model/API feature.
- Sarvam voice routes require `SARVAM_API_KEY`.
- Flutter stable and Android SDK tooling have been installed in the development environment; the Android Studio Java runtime is available for builds.

## Mobile implementation

The mobile app is a Flutter/Dart client that reuses the existing FastAPI contracts. Conversation history and messages are stored persistently on-device in SQLite; queries, schemas, SQL inspection, and evaluation data continue to use the real backend endpoints. It does not duplicate model inference or database execution in the client. The chat supports native speech dictation, automatic response playback in the backend-detected language, and per-answer playback. Flutter analysis and focused client/store tests pass.

## Remaining requirements and known limits

- Configure `SARVAM_API_KEY` to enable the optional voice API.
- The backend currently owns no cross-device conversation store; mobile conversation persistence is local to the device.
- Mobile speech transcription uses the phone's configured speech-recognition service. Sarvam's server-side audio auto-detection requires `SARVAM_API_KEY`, which is not configured in this environment.
- The release APK builds successfully; an emulator or physical Android device was not available for an on-device launch smoke test. iOS builds require macOS/Xcode.
- Existing Python test failures should be diagnosed separately from the mobile client unless a mobile-related change reproduces them.
