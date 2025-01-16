import pytest
from pathlib import Path

from valar_daemon.DaemonConfig import DaemonConfig


# Testing values that are not part of the default localnet config
config_params = {
    "validator_ad_id_list": [9999, 8888, 7777],
    "validator_manager_mnemonic": "xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz",
    "algod_config_server": "http://testnet.algod.server:1234",
    "algod_config_token": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    # "indexer_config_server": "http://indexer.test.server:5678",
    # "indexer_config_token": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    # "kmd_config_server": "http://kmd.test.server:9012",
    # "kmd_config_token": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
    "loop_period_s": 99,
    "max_log_file_size_B": 40*1024,
    "num_of_log_files_per_level": 3,
}


@pytest.fixture
def config_setup(tmp_path):
    """Fixture to set up the DaemonConfig object and related files for testing. Executed per test function (default).
    """
    # Setup
    config_filename = "daemon.config"
    config_path = tmp_path
    config_full_path = Path(tmp_path, config_filename)
    daemon_config = DaemonConfig(config_path, config_filename)

    yield daemon_config, config_full_path


def test_update_config(config_setup):
    """Test the update_config method.
    """
    daemon_config, _ = config_setup
    daemon_config.update_config(**config_params)

    for key, value in config_params.items():
        assert getattr(daemon_config, key) == value


def test_write_config(config_setup):
    """Test the write_config method.
    """

    daemon_config, config_full_path = config_setup
    daemon_config.update_config(**config_params)
    daemon_config.write_config()

    assert config_full_path.is_file()
    with open(config_full_path, 'r') as f:
        content = f.read()
        assert "validator_ad_id_list" in content
        assert str(config_params["validator_ad_id_list"]) in content


def test_read_config(config_setup):
    """Test the read_config method.
    """
    daemon_config, _ = config_setup
    daemon_config.update_config(**config_params)
    daemon_config.write_config()

    # Modify some values before reading the config back
    daemon_config.validator_ad_id_list = []
    daemon_config.read_config()

    for key, value in config_params.items():
        assert getattr(daemon_config, key) == value


def test_read_config_error(config_setup):
    """Test the read_config method.
    """
    daemon_config, _ = config_setup
    daemon_config.update_config(**config_params)

    # Modify some values before reading the config back
    daemon_config.validator_ad_id_list = []

    with pytest.raises(ValueError):
        daemon_config.read_config()


def test_create_swap(config_setup):
    """Test the create_swap method.
    """
    daemon_config, _ = config_setup
    daemon_config.update_config(**config_params)
    daemon_config.write_config()

    daemon_config.create_swap()
    assert daemon_config.swap_full_path.is_file()


def test_read_swap(config_setup):
    """Test the read_swap method.
    """
    daemon_config, _ = config_setup
    daemon_config.update_config(**config_params)
    daemon_config.write_config()
    daemon_config.create_swap()

    # Modify some values before reading the swap file
    daemon_config.validator_ad_id_list = []
    daemon_config.read_swap()

    for key, value in config_params.items():
        assert getattr(daemon_config, key) == value
