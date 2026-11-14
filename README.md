# AC Jetta Remake

Turn your phone into a wireless steering wheel and pedals for **Assetto Corsa**.

The phone shows a touch steering wheel, throttle, brake and buttons. Every
touch input travels over the local network to a small Python server on the
PC, which injects it into Windows as a virtual Xbox 360 controller — so the
game sees a real gamepad, no game mods needed.

```
Phone (touch UI) -- WebSocket, LAN :9999 --> PC server (Python)
    --> vgamepad / ViGEmBus --> virtual Xbox 360 controller --> Assetto Corsa
```

Built in the summer of 2026, before I started university. Code was written
with AI assistance (Gemini free tier); I specified the behaviour, tested and
debugged it over five days of iteration, and packaged the Android app myself
in Android Studio.

## What it does

- **Analog steering** — drag the on-screen wheel; the angle accumulates
  incrementally (atan2 delta, with ±180° wrap correction), up to 900° (1.25
  turns), and springs back towards centre on release.
- **Analog pedals** — throttle and brake drive the right and left triggers.
- **Buttons** — Start, RB / LB (shift up / down), A and Y, mapped to the
  matching Xbox buttons. Bind them inside Assetto Corsa's control settings
  (e.g. A as handbrake).
- **Disconnect safety lock** — if the phone drops, the server instantly
  zeroes the stick, triggers and all buttons, so the car never keeps a
  stuck throttle.
- **Auto-connect** — the client can sweep the LAN for the server, or you can
  type the PC's IP by hand.
- **Minimal protocol** — one comma-separated string per frame, e.g.
  `X:12345,T:180,B:0,BK:0,ST:0,RB:0,LB:0,A:0,Y:0`. No JSON, no per-frame
  logging on the hot path; malformed packets are silently dropped.

## Layout

```
server/server.py   PC side: WebSocket server (port 9999) + vgamepad injection (V23.2)
client/index.html  Phone side: the whole touch UI, plain HTML/CSS/JS (V25.0)
                   The Android APK is a WebView wrapper of this page (see Releases).
requirements.txt   Python dependencies
```

## Requirements

- Windows 10/11 PC (the virtual controller needs the ViGEmBus driver,
  which is Windows-only) with Python 3 installed.
- Android phone, or any phone browser, on the same LAN / hotspot as the PC.
- Assetto Corsa on the PC.

## Setup — PC

```powershell
pip install -r requirements.txt
python server\server.py
```

Installing `vgamepad` automatically runs the **ViGEmBus driver** installer:
accept the licence, click Install (admin approval needed), then Finish.
That driver is the part that makes Windows believe a real Xbox 360
controller is plugged in — without it, `vgamepad` cannot create the
gamepad object.

When the server starts it prints your PC's LAN IP. Keep that window open.

If the phone cannot connect:

- Make sure the phone and PC are on the same network (same Wi-Fi, or the
  phone's hotspot with the PC joined to it).
- Allow Python through Windows Firewall, or open TCP port 9999.
- If you see `OSError: ViGEmBus is not installed`, install the driver
  manually from the [ViGEmBus releases](https://github.com/nefarius/ViGEmBus/releases)
  and reboot, then start the server again.

## Setup — phone

**Option A — APK (easiest):** download the APK from
[Releases](../../releases), install it, open it, enter the PC's LAN IP
(or tap auto-connect), and drive.

**Option B — browser:** open `client/index.html` in the phone's browser
(same network as the PC), enter the PC's LAN IP, and drive. No install.

Note: auto-connect sweeps `192.168.1.1–254` only. If your network uses a
different subnet (e.g. a phone hotspot on `192.168.43.x`), enter the IP
shown by the server by hand.

Then, in Assetto Corsa, go to Settings → Controls and bind the virtual
controller's stick, triggers and buttons as you like.

## Known limitations

- The V23.2 server is **one-way**: it only receives input. The client page
  already has a dashboard (rev arc, shift light, gear, speed) and listens
  for telemetry, but this server never sends any — the dashboard stays at
  its default values. Reading Assetto Corsa's shared-memory telemetry is
  the obvious next step.
- `BK` (Back button) is always 0 — the page has no Back button. The server
  parses it fine; it just can never become 1.
- Windows-only, for the driver reason above.

## Licence

MIT — see [LICENSE](LICENSE).
