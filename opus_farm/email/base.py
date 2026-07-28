from abc import ABC, abstractmethod
from typing import Optional


class EmailProvider(ABC):
    """Strategy interface for temp-email providers."""

    @abstractmethod
    def generate(self) -> str:
        """Return a fresh, valid email address."""

    @abstractmethod
    def get_otp(self, email: str, tries: int = 30) -> Optional[str]:
        """Poll the inbox for a 6-digit OTP; return None on timeout."""
