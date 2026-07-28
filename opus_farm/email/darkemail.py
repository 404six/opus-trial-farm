import re
import secrets
import time
from typing import Callable, Optional

import requests

from .base import EmailProvider


class DarkEmailProvider(EmailProvider):
    API = "https://www.darkemail.school/api/emails"
    HEADERS = {
        "referer": "https://www.darkemail.school/",
        "user-agent": "Mozilla/5.0",
    }

    def generate(self) -> str:
        return f"user-{secrets.token_hex(4)}-{secrets.token_hex(4)}@darkemail.school"

    def get_otp(
        self,
        email: str,
        timeout: int = 60,
        on_stalled: Optional[Callable[[], bool]] = None,
    ) -> Optional[str]:
        start = time.time()
        check_at = 15
        checked = False

        while True:
            elapsed = time.time() - start
            if elapsed >= timeout:
                return None
            try:
                r = requests.get(self.API, params={"to": email}, headers=self.HEADERS, timeout=10)
                emails = r.json().get("emails", [])
                if emails:
                    m = re.search(r"\b\d{6}\b", emails[0].get("body", ""))
                    if m:
                        return m.group()
            except Exception:
                pass
            if on_stalled and not checked and elapsed >= check_at:
                checked = True
                try:
                    if not on_stalled():
                        timeout = min(timeout, elapsed + 15)
                except Exception:
                    pass
            time.sleep(1)
