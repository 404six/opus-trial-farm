# Opus Trial Farm

Automates Opus.pro trial-account creation and API-key extraction. Each generated account comes with **90 free credits** (~90 minutes of video processing) that can be used directly through the Opus REST API. Run the loop N times to get N keys.

## Features

- Undetected Chrome (SeleniumBase + `uc=True`) for headful signup
- Disposable email + OTP polling — Strategy pattern, plug any temp-mail provider
- In-browser Bearer/OrgID interceptor injected via CDP (no manual token capture)
- Direct API calls to `/api/api-keys` and `/api/org-credits` right after signup
- PAC-based proxy routing — only `*.opus.pro` traffic uses the proxy, everything else goes direct
- CDP-level blocklist for statics/fonts/media/analytics — minimal bandwidth per account

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate         # Windows
# source .venv/bin/activate    # Linux/macOS

pip install -r requirements.txt

cp .env.example .env           # fill in your proxy credentials
python main.py
```

Generated keys are appended to `OUTPUT_FILE` (default `opus_keys.txt`), one per line:

```
sk_live_xxxxxxxxxxxxxxxxxxxxxxxxx | 90min (5400 credits)
```

## Requirements

- Python 3.9+
- Google Chrome installed
- An HTTP proxy that accepts CONNECT + Basic auth (any residential/datacenter provider works — the local forwarder in `opus_farm/proxy.py` handles auth injection)

## Structure

```
.
├── main.py                     # loop entry point
├── config.py                   # env-backed constants
└── opus_farm/
    ├── proxy.py                # local authenticated TCP forwarder
    ├── browser.py              # SeleniumBase driver + PAC + CDP
    ├── scripts.py              # injected JS (interceptor + create-key)
    ├── automation.py           # end-to-end account flow
    └── email/                  # Strategy: temp-mail providers
        ├── base.py             # EmailProvider abstract
        └── darkemail.py        # DarkEmail concrete
```

## Adding a new email provider

Implement `EmailProvider` and swap it in `main.py`:

```python
# opus_farm/email/mymail.py
from .base import EmailProvider

class MyMailProvider(EmailProvider):
    def generate(self) -> str: ...
    def get_otp(self, email, tries=30): ...
```

```python
# main.py
from opus_farm.email.mymail import MyMailProvider
provider = MyMailProvider()
```

## How it works

1. Boots a local TCP proxy that injects `Proxy-Authorization` (Chrome `uc` mode does not accept auth extensions reliably)
2. Launches Chrome with a PAC URL routing only `*.opus.pro` through the local proxy
3. Blocks images, fonts, media, and analytics domains via `Network.setBlockedURLs`
4. Injects a JS interceptor before any page script — captures the Bearer token and Org ID from fetch/XHR/Worker traffic
5. Requests a disposable email, submits signup, polls the provider for the 6-digit OTP
6. Once the OAuth handshake completes, calls `POST /api/api-keys` and `GET /api/org-credits` from inside the browser session
7. Writes the key + credit balance to `OUTPUT_FILE`

## Disclaimer

Educational / research use only. Automating trial signups likely violates the Opus.pro Terms of Service. You are responsible for how you use this code.
