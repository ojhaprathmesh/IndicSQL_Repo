# BharatQuery mobile app

This Expo / React Native app uses the IndicSQL FastAPI backend at `http://localhost:8000`.

## Run on an Android emulator

Start the backend from the repository root:

```powershell
python -m uvicorn indicsql.api.server:app --host 0.0.0.0 --port 8000
```

In another terminal:

```powershell
cd frontend\mobile
npm.cmd start
```

Open the project in Expo Go or an Android emulator. Android emulators use `10.0.2.2` to reach the host computer, which is the app's default API address. On the iOS simulator, the app defaults to `localhost`.

## Run on a physical phone

The phone and computer must be on the same network. Find the computer's local IPv4 address with `ipconfig`, then set the API URL before starting Expo. For example:

```powershell
$env:EXPO_PUBLIC_API_URL = "http://192.168.1.25:8000"
cd frontend\mobile
npm.cmd start
```

Replace `192.168.1.25` with the computer's actual local IP address. Keep the backend running with `--host 0.0.0.0`, and allow Python through the firewall on a trusted local network if prompted.

For production, configure an HTTPS backend URL rather than exposing the development HTTP service.
