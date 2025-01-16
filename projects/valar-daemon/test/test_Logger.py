import pytest
import inspect
from pathlib import Path

from valar_daemon.Logger import Logger


@pytest.fixture
def logger(tmp_path: Path) -> Logger:
    """Initialize Valar daemon logger.

    Parameters
    ----------
    tmp_path: Path
        Log output path.

    Returns
    -------
    Logger
        The logger.
    """
    return Logger(
        log_dirpath = tmp_path,
        log_max_size_bytes = 40*1024, # 40 kB
        log_file_count = 4 # Spawns a total of 5 logs (1 active, 4 past) -> 200 kB per level; 1 MB in total
    )


class TestLoggerMessaging():

    @staticmethod
    def test_predefined_messaging(logger):
        """Run over all pre-defined messages.
        """
        # Iterate over all log message abstractions
        for method_name in dir(logger):
            if method_name.startswith("log_"):
                method = getattr(logger, method_name)
                if callable(method):
                    # Inspect method signature
                    sig = inspect.signature(method)
                    # Generate a list of 0s matching the number of parameters
                    args = [0] * len(sig.parameters)
                    method(*args)  # Call the method with arguments set to 0
