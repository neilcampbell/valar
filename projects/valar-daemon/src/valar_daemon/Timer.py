"""Timer definition for convenience and easier testing.
"""
import time


class Timer():
    """Timer definition for convenience and easier testing.

    Notes
    -----
    In seconds and based on Unix time.

    Parameters
    ----------
    period_s : int
        The timer's period in seconds.
    last_reset_time_s : int
        The last time that the timer was reset.
    """

    def __init__(
            self,
            period_s: int
        ) -> None:
        """Initialize new timer.

        Parameters
        ----------
        period_s : int
            The timer's period in seconds.
        """
        self.period_s = period_s
        self.last_reset_time_s = 0 # Always elapsed by default

    def reset_timer(self) -> None:
        """Reset the timer.
        """
        self.last_reset_time_s = time.time()

    def has_time_window_elapsed(self) -> bool:
        """Check if the time window has elapsed (if the time is up / if timer has finished).

        Returns
        -------
        bool
            True if elapsed (time is up / timer has finished).
        """
        return time.time() - self.last_reset_time_s > self.period_s
