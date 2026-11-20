# IndicSQL Studio Architecture

## Applications

IndicSQL Studio has two clients sharing the existing Python service:

- The existing Next.js web client remains in `frontend/`.
- The native mobile client lives in `mobile/` and is implemented with Flutter/Dart.

## Mobile layers

- **Presentation:** Responsive light-themed chat, saved conversation list, SQL workspace, schema browser, analytics, evaluation, pipeline trace, settings, and documentation screens. Chat uses the device speech recognizer and system TTS; dictated replies are spoken using the backend-detected language.
- **Application state:** The selected conversation, messages, loading/error states, and selected API endpoint are managed in the Flutter client.
- **API client:** Sends natural-language queries to `POST /query` with optional supported language overrides; loads schemas and evaluation data from `GET /schemas` and `GET /analytics`; validates and executes SQL through `POST /sql/inspect`; checks `GET /health`.
- **Local persistence:** SQLite stores conversations, ordered messages, titles, and timestamps on the device. It is not a shared server-side history service.

## Backend and data flow

The mobile app does not generate SQL or fabricate responses. A chat request is sent to the existing FastAPI service, which invokes the IndicSQL multi-agent pipeline and returns the generated SQL, actual sandbox result, verbalized response, and available audit trace. SQL submitted from the workspace goes through the backend's read-only SQL checks and bounded DuckDB sandbox.

The agent pipeline remains the source of language detection, schema linking, SQL synthesis, SQL safety, query execution, and answer verbalization. The DuckDB sandbox reads the registered NDAP Parquet data. Benchmark and failure views use the checked-in evaluation artifacts served by `/analytics`.

## Boundaries and limitations

- Conversation persistence is device-local; the backend currently has no conversation CRUD API.
- Language is detected automatically unless the user selects one of the backend-supported overrides (English, Hindi, Hinglish, Marathi, Bengali, Tamil, or Telugu).
- Evaluation dashboards display stored benchmark artifacts, not live runtime measurements.
- Semantic AI review, authentication, and cross-device conversation synchronization are not provided by the current service.
- Voice operations depend on the optional Sarvam API configuration.
