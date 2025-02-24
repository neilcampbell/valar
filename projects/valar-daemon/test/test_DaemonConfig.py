import pytest
from pathlib import Path

from valar_daemon.DaemonConfig import DaemonConfig

from test.utils import default_config_params, create_daemon_config_file


@pytest.fixture(scope='function')
def include_claim_period(request: pytest.FixtureRequest) -> bool:
    """Create a claim period indicator with a default value that can be overwritten.

    Parameters
    ----------
    request : pytest.FixtureRequest
        [param] An object bearing the requested claim period indicator value.

    Returns
    -------
    bool
        Indicator whether to include the claim period in the config file.
    """
    return getattr(request, "param", True)


@pytest.fixture(scope='function')
def daemon_config(
    tmp_path: Path,
    include_claim_period: bool
) -> DaemonConfig:
    """Create daemon config and initialize the corresponding object.

    Parameters
    ----------
    tmp_path : Path
        [fixture] Path to temporary directory, per test.
    include_claim_period : bool
        [fixture] Indicator whether to include the claim period in the config file.

    Return 
    ------
    DaemonConfig
        An initialized daemon config abstraction object.
    """
    # Create the temporary config
    create_daemon_config_file(
        tmp_path, 
        'daemon.config',
        default_config_params,
        include_claim_period
    )
    # Connect to temporary config
    daemon_config = DaemonConfig(tmp_path, 'daemon.config')
    return daemon_config


@pytest.mark.parametrize(
    "include_claim_period", 
    [True, False],
    indirect=["include_claim_period"]
)
def test_read_config(
    daemon_config: DaemonConfig,
    include_claim_period: bool,
):
    """Test the read_config method.

    Parameters
    ----------
    daemon_config : DaemonConfig
        [fixture] An initialized daemon config abstraction object.
    include_claim_period : bool
        [fixture] Indicator whether to include the claim period in the config file.
    """
    # Create the temporary config
    daemon_config.read_config()
    # Check parameters
    for key, value in default_config_params.items():
        if key == 'claim_period_h': 
            continue
        if key == 'claim_period_s' and not include_claim_period:
            value = 604800 # Seconds in a week
        assert getattr(daemon_config, key) == value


def test_write_config(tmp_path: Path, daemon_config: DaemonConfig):
    """Test writing config file.

    Notes
    -----
    Testing of the re-loaded parameters after writing a new file is conducted in `test_read_swap`.

    Parameters
    ----------
    tmp_path : Path
        [fixture] Path to temporary directory, per test.
    daemon_config : DaemonConfig
        [fixture] An initialized daemon config abstraction object.
    """
    # Populate the config parameters
    daemon_config.read_config()
    # Write config to new unique file for this test
    config_full_path = Path(tmp_path, 'config_write_test.config')
    daemon_config.write(str(config_full_path))
    # Check if file exists
    assert config_full_path.is_file()
    # Continue only if exists with checking the contents
    if config_full_path.is_file():
        with open(config_full_path, 'r') as f:
            content = f.read()
            for key, value in default_config_params.items():
                if key == 'claim_period_s': 
                    continue
                assert key in content
                assert str(value) in content


def test_create_swap(daemon_config: DaemonConfig):
    """Test the create_swap method.

    Parameters
    ----------
    daemon_config : DaemonConfig
        [fixture] An initialized daemon config abstraction object.
    """
    # Update object from file
    daemon_config.read_config()
    # Create swap file
    daemon_config.create_swap() 
    # Check file existence
    assert daemon_config.swap_full_path.is_file()


def test_read_swap(daemon_config: DaemonConfig):
    """Test the read_swap method.

    Parameters
    ----------
    daemon_config : DaemonConfig
        [fixture] An initialized daemon config abstraction object.
    """
    # Update object from file
    daemon_config.read_config()
    # Create swap file
    daemon_config.create_swap() 
    # Modify values before reading the swap file
    for key, value in default_config_params.items():
        if key == 'claim_period_h': 
            continue
        setattr(daemon_config, key, None)
    # Freshly populate parameters from swap file
    daemon_config.read_swap()
    # Check parameters
    for key, value in default_config_params.items():
        if key == 'claim_period_h': 
            continue
        assert getattr(daemon_config, key) == value


@pytest.mark.parametrize(
    "claim_period_h, expected_claim_period_s", 
    [
        (     0,      0),
        (     1,   3600),
        (    12,  43200),
        (    24,  86400),
        (    37, 133200),
        (    51, 183600),
        (   0.1,    360),
        (   1.2,   4320),
        (   2.4,   8640),
        (   3.7,  13320),
        (   5.1,  18360)
    ]
)
def test_convert_claim_period_from_hours_to_seconds(
    claim_period_h: int | float,
    expected_claim_period_s: int | float
):
    """Test the conversion from hours to seconds.

    Parameters
    ----------
    claim_period_h : int | float
        [param] Claim period in hours.
    expected_claim_period_s : int | float
        [param] Expected claim period in seconds.
    """
    result = DaemonConfig._convert_claim_period_from_hours_to_seconds(
        claim_period_h
    )
    assert type(result) is int
    assert result == expected_claim_period_s


@pytest.mark.parametrize(
    "claim_period_s, expected_claim_period_h", 
    [
       (  3600,  1),
       ( 43200, 12),
       ( 86400, 24),
       (133200, 37),
       (183600, 51),
       (     0,  1),
       (  3600,  1),
       (  7200,  2),
       ( 10800,  3),
       ( 18000,  5)
    ]
)
def test_convert_claim_period_from_seconds_to_hours_rounded(
    claim_period_s: int | float,
    expected_claim_period_h: int | float
):
    """Test the conversion from seconds to hours and the rounding / cutoff that is applied.

    Parameters
    ----------
    claim_period_s : int | float
        [param] Claim period in seconds.
    expected_claim_period_h : int | float
        [param] Expected claim period in hours.
    """
    result = DaemonConfig._convert_claim_period_from_seconds_to_hours_rounded(
        claim_period_s=claim_period_s
    )
    assert type(result) is int
    assert result == expected_claim_period_h
