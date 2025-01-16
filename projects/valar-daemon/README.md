# Valar Daemon

This project contains the Valar Daemon, which automates the servicing of staking requests and handling ongoing collaborations for [Valar](https://stake.valar.solutions) - a decentralized platform for connecting blockchain stakeholders (i.e. Delegators) to node runners (i.e. Validators) that offer direct participation in blockchain consensus, i.e. staking.
The Valar Daemon operates by periodically servicing the indicated Validator Ads and their Delegator Contracts in an infinite loop and sleeping when not busy.
The servicing consists of reporting if the node is ready for accepting new Delegators, generating participation keys for new Delegators, and monitoring compliance with the agreed contract terms.

This project contains the Daemon's source code, tests, and supporting material.

> **For Validators**: The `valar_daemon` package and the corresponding instructions for installing it, setting up a node, and running the Daemon can be found at [PyPI](https://pypi.org/project/valar_daemon/).


## Setup

### Pre-requisites

Running the Valar Daemon requires Python 3.12 or greater.
The dependencies for running, building, testing, and miscellaneous development can be installed from `pyproject.toml` using `poetry install --no-root` or simply `poetry install` if you want to install the Valar Daemon package, i.e. if you do not desire to run from source.

In addition, you should run a local Algorand network (i.e. a [localnet](https://developer.algorand.org/docs/get-details/algokit/features/localnet/)).

**Reminder:** check that you are not running an installed instance of the Valar Daemon (`pip freeze | grep valar`) in case you wish to amend and debug the source code.

### Run from source

The Daemon's source code resides in `./src/valar_daemon/`.
Its main dependencies are the compiled clients for the Valar Smart Contracts and the Algod REST API.
These are used to interact with the Valar Platform and to manage the node's participation keys, respectively.

The daemon can be run using `python -m valar_daemon.run_daemon --config_path <config_path> --log_path <log_path>`, where the additional parameters are:
- `<config_path>`: the path to the configuration file `daemon.config`, including the file's name.
- `<log_path>`: the path to where the Valar Daemon can make a new directory and populate it with the log (about 1 MB in size), including the log directory's name.

Running above from the base directory, where this `README.md` resides, will run the Valar Daemon according to the configuration indicated in `daemon.config` and output the log to the directory `./valar-daemon-log`.

### Configuration 

The Daemon is configured at runtime according to the file `daemon.config` or wherever `<config_path>` points to.
The exposed configuration settings are:

- `validator_ad_id_list`: A list of IDs of the Validator Ads that the Daemon should service.
- `validator_manager_mnemonic`: The mnemonic of the Validator Manager account (hot wallet).
- `algod_config_server`: The URL and port of the Algorand Daemon.
- `algod_config_token`: The admin token of the Algorand Daemon.
- `max_log_file_size_B`: The maximal size of a single log file.
- `num_of_log_files_per_level`: The number of files generated per log level.
- `loop_period_s`: The period at which the Daemon's master loop executes.

Note that the five log levels, described next, mean that the total size of the log directory is about `5*max_log_file_size_B*num_of_log_files_per_level`.

### Logs

The Valar Daemon can be monitored through the logs that reside at `valar-daemon-log` or the chosen path `<log_path>`.
Logging is structured in five levels, with their combined size limited to approximately 1 MB by default.
Old entries are overwritten once this size is reached and only the latest log information is kept.
The five logging levels are ([according to Python.logging](https://docs.python.org/3/library/logging.html)):

| Level    |                                                        Description                                                          | Subdirectory  |
|----------|-----------------------------------------------------------------------------------------------------------------------------|---------------|
| Critical | The most critical errors, such as an unreachable network, preventing the Valar Daemon from interacting with the blockchain. | `50-critical` |
| Error    | Errors which impact a specific part of the Valar Daemon, such as the fetching of information for one smart contract.        | `40-error`    |
| Warning  | Indicators of potential concern, such as having zero ads associated with the Valar Daemon.                                  | `30-warning`  |
| Info     | Informative messages of general nature, such as information about the ending of a Delegator Contract.                       | `20-info`     |
| Debug    | Detailed messages about separate components of the Valar Daemon.                                                            | `10-debug`    |

Each logging level includes its own messages and those of higher priority.
For example, the log `50-critical/critical.log` includes only critical error messages, while `10-debug/debug.log` includes all logged events.
A list of log messages is provided in [README_log_messages.md](./docs/README_log_messages.md).


## Test the Daemon

The `./test` directory includes the unit and integration tests of the Valar Daemon and its components.
This includes the testing of auxiliary functions, the interaction with the Algorand Daemon on the node, and the interaction with the Valar Smart Contracts.
Note that the tests rely on the `Noticeboard` utility function from the Smart Contract project in the master repository.
`Noticeboard` is only needed in the tests and it is not equivalent to `NoticeboardClient`, hence `Noticeboard` is not included in `./src/valar_daemon/`.

The directory `./test/test_journey` includes journey tests, where the Valar Daemon is spun up in a separate thread, while Delegator Contracts are created and different Delegator inputs are provided.
This enables testing of entire journeys from the contract start to its end.

The tests are built around the `pytest` module (configured in `pytest.ini`) and using `coverage` (configured in `.coveragerc`) to automatically generate reports on the extent of covered code in the tests.

To list the available tests, run `pytest --collect-only`

To execute the available tests, run `coverage run -m pytest`, followed by `coverage report` to generate the coverage report.
Additionally run `coverage html` to generate a detailed report accessible through `./test/coverage_report/ingex.html`.
