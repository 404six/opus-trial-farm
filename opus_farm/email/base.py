from abc import ABC, abstractmethod
from typing import Callable, Optional


class EmailProvider(ABC):
    """Strategy interface for temp-email providers."""

    @abstractmethod
    def generate(self) -> str:
        """Return a fresh, valid email address."""

    @abstractmethod
    def get_otp(
        self,
        email: str,
        tries: int = 60,
        on_stalled: Optional[Callable[[], None]] = None,
    ) -> Optional[str]:
        """Poll the inbox for a 6-digit OTP.

        If ``on_stalled`` is provided, it is invoked once, halfway through the
        polling window, if no OTP has been received yet. Concrete providers may
        use it to signal the caller (e.g. click a Resend button).
        """
