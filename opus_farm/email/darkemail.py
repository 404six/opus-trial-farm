import re
import secrets
import time
from typing import Optional

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

    def get_otp(self, email: str, tries: int = 30) -> Optional[str]:
        for _ in range(tries):
            try:
                r = requests.get(self.API, params={"to": email}, headers=self.HEADERS, timeout=10)
                emails = r.json().get("emails", [])
                if emails:
                    m = re.search(r"\b\d{6}\b", emails[0].get("body", ""))
                    if m:
                        return m.group()
            except Exception:
                pass
            time.sleep(2)
        return None
