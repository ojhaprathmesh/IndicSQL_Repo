# IndicSQL Studio Mobile

Native Flutter client for the existing IndicSQL FastAPI backend. It includes a
multilingual data chat, generated-SQL review and execution, live schema browsing,
backend-provided analytics, and on-device conversation history.

## Requirements

- Flutter stable and Dart SDK (the project constraint is declared in `pubspec.yaml`)
- Android Studio with Android SDK and an emulator, or a connected Android device
- Python backend installed and configured from the repository root

The mobile app uses Flutter/Dart; Node.js is not required.

## Run locally on Windows

If Puro is not installed:

```powershell
winget install --id pingbird.Puro --exact
puro use stable
puro flutter doctor
puro flutter doctor --android-licenses
```

If Flutter cannot locate the Java runtime bundled with Android Studio, set it for
the current PowerShell session before building:

```powershell
$env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
$env:Path = "$env:JAVA_HOME\bin;$env:Path"
```

Start the backend from the repository root in a separate terminal:

```powershell
uv run uvicorn indicsql.api.server:app --reload --host 0.0.0.0 --port 8000
```

Then start the mobile app:

```powershell
Set-Location mobile
puro flutter pub get
puro flutter run
```

The Android emulator uses `http://10.0.2.2:8000` by default. For a USB-connected
phone, run `adb reverse tcp:8000 tcp:8000`, then open **Settings → FastAPI base URL**
and enter `http://127.0.0.1:8000`. For Wi-Fi, enter the development computer's LAN
IP (such as `http://192.168.1.25:8000`); the phone and computer must be on the same
network, and the backend must listen on `0.0.0.0`. Local HTTP is enabled for
development; configure HTTPS for non-local use.

Conversations are stored in the app's private SQLite database on the device.
Questions and SQL requests go to the configured backend; conversation history is
not uploaded or synchronized.

## Voice

Tap the microphone to dictate, review the transcript, then send it. **Auto-detect**
uses the phone's default speech-recognition locale; after transcription, IndicSQL
detects the transcript language (or honors a selected language) and automatically
speaks replies to dictated questions using the corresponding installed system
text-to-speech voice. Assistant replies to typed questions can also be played with
the **Listen** action.

The phone's recognition service must support the selected language. Install any
missing recognition/TTS languages in Android's speech and text-to-speech settings.
The backend's Sarvam voice endpoints can detect language directly from audio, but
they require `SARVAM_API_KEY`; the mobile client currently uses the phone's native
speech-recognition service instead.

## Validation and release

```powershell
puro flutter analyze
puro flutter test
puro flutter build apk --release
```

The APK is written to
`build\app\outputs\flutter-apk\app-release.apk`.
