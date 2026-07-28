import os

from dotenv import load_dotenv

load_dotenv()


def _required(key: str) -> str:
    v = os.getenv(key)
    if not v:
        raise RuntimeError(f"Missing env var: {key} (see .env.example)")
    return v


META_CHAVES = int(os.getenv("META_CHAVES", "5"))
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "opus_keys.txt")
HEADLESS = os.getenv("HEADLESS", "true").strip().lower() in ("1", "true", "yes", "on")

PROXY_HOST = _required("PROXY_HOST")
PROXY_PORT = int(_required("PROXY_PORT"))
PROXY_USER = _required("PROXY_USER")
PROXY_PASS = _required("PROXY_PASS")

BLOCKED_URLS = [
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp", "*.svg", "*.ico",
    "*.woff", "*.woff2", "*.ttf", "*.otf",
    "*.mp4", "*.webm", "*.m4a", "*.mp3",
    "*google-analytics*", "*googletagmanager*", "*google-tag*", "*doubleclick*",
    "*sentry.io*", "*mixpanel*", "*segment.io*", "*segment.com*",
    "*hotjar*", "*intercom*", "*posthog*", "*amplitude*",
    "*fullstory*", "*datadog*", "*newrelic*", "*bugsnag*",
    "*facebook.net*", "*fbcdn*", "*twitter.com/i/*", "*tiktok*",
]
