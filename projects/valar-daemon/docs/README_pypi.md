# Valar Daemon

Congratulations, you have chosen to offer your node running services on one of the most decentralized staking platforms for Algorand — The Valar Peer-to-Peer Staking Platform.
Three steps are required to set up your node for Valar:
1. Run an Algorand participation node - [Section 1](#1_node).
2. Advertise your node on Valar - [Section 2](#2_advertisement).
3. Automate the servicing of users - [Section 3](#3_daemon).

These steps are described below.

*Please refer to [the Daemon's repository](https://github.com/ValarStaking/valar/tree/master/projects/valar-daemon) for the [changelog](https://github.com/ValarStaking/valar/blob/master/projects/valar-daemon/CHANGELOG.md), source code, tests, and a broader description of the Valar Daemon.*
*Additionally, you can find smart contract and user interface (UI) source code in [the master repository](https://github.com/ValarStaking/valar/tree/master).* 
*Furthermore, you can find answers to FAQ, the Valar platform's terms of usage, and other information at [stake.valar.solutions](https://stake.valar.solutions).*
*The Valar Daemon is provided under the [GNU Affero General Public License v3.0](https://choosealicense.com/licenses/gpl-3.0/).*

*Note that the terms "node runner" and "validator" are used interchangeably.*


<a id="1_node"></a>

## 1. Run an Algorand participation node

### Node runner responsibilities

As a node runner you form part of the backbone of the Algorand blockchain.

Your node will be participating in consensus, verifying transaction and proposing blocks. 
The larger the relative amount of stake that participates in consensus through your node, the more often it will be selected for proposing a block, according to the Algorand Pure Proof of Stake (PPoS) consensus mechanism.
This means that any downtime that your node may experience can negatively impact the network, those staking through you, and ultimately any of your earnings.

Run your node responsibly.

### Installing and setting up the node

The first step is to set up and run an Algorand participation node. The options for installing and configuring a node include:
- Applications with a graphical user interface (GUI) such as [Funk's Ultimate Node Controller (FUNC)](https://func.algo.xyz/) or [Aust One-Click Node (A1CN)](https://github.com/AustP/austs-one-click-node/releases).
- The command-line (CLI) one-stop-shop for Algorand node running [Nodekit](https://github.com/algorandfoundation/nodekit).
- A custom install with more flexibility according to [Algorand's developer guide](https://developer.algorand.org/docs/run-a-node/setup/install/).

It is recommended to enable automatic running of the node on startup since your machine may reboot unexpectedly, e.g., due to interrupted power supply.
The configuration of automatic startup varies between systems and installation approaches.
Check the specific guide that you followed for more details.


<a id="2_advertisement"></a>

## 2. Advertise your node on Valar

The next step in offering your node running service to others is to create an advertisement (ad) on the Valar Platform.

Go to [stake.valar.solutions](https://stake.valar.solutions), connect your wallet, and choose the option `Run a Node`.
You can then create an ad for your node, where you define the terms of your service.

Defining the terms of the ad includes defining your fees.
These consist of a setup fee - a one-time cost for preparing the node for a new user, and an operational fee, which is charged to the user according to their requested duration of staking.
You can define the operational fee as a flat fee and/or to be proportional to the user's requested maximum stake because of the potential additional burden on your node due to the higher stake.
You also select the currency of the fee payment.

As a responsible node runner, you can define the maximum limits on the ALGO amount that a user can stake on your node.
This way you can reject accepting larger stakes than your node can responsibly handle. 
If a user stakes more than the agreed limit, the service contract can get terminated.

Because users can involuntarily get their stakes increased above the agreed maximum as sending ALGO is permissionless, you can give them a certain number of warnings before terminating the contract due to the breached limits.
In case you charge according to the user's requested maximum stake, you can give them a buffer on top of their requested maximum stake so they are less likely to breach the limit.

You also set the time until when the users can stake with you as well as the minimum and maximum duration of staking.
Moreover, you define the setup time - the time in which you promise to respond to a user's request to stake via your node by generating and giving them the participation keys; and the confirmation time - the time in which the user should sign the generated keys and confirm the service contract.

You can use the Valar Daemon to automate the servicing of users — handling new user staking requests and managing ongoing collaborations. 
The ad requires you to enter a manager address, which the Valar Daemon will use when interacting with the platform. 
It is best to use another account with minimal funding (i.e. hot wallet) for the manager address, since the Valar Daemon needs signing right for this account.
As part of the ad management, you must also define how many users you accept on the node at a time.


<a id="3_daemon"></a>

## 3. Automate the servicing of users

As a node runner on the Valar Platform, you will be receiving staking requests in the form of new delegator contracts.
Each of these requires the generation of participation keys, monitoring to check that the contract's terms are met, and cleanup in case of termination or early ending.
The Valar Daemon automates these tasks for you.

### Install Python3.12 or grater

Running the Valar Daemon requires Python 3.12 or greater. You can follow a generic guide on how to install Python for your system, e.g., [the guide at Real Python](https://realpython.com/installing-python) covers the major operating systems.

While you can use a global instance of Python, it is recommended to use [a virtual environment](https://docs.python.org/3/library/venv.html) for easier maintenance.

### Install the Valar Daemon

You can install the Valar Daemon as a standalone package, including the required dependencies, using `pip install valar_daemon`.

More information about the package and previous versions can be found at [PyPI](https://pypi.org/project/valar_daemon/).

### Configure the Daemon

You need to configure the Valar Daemon before running it. 
This is done through a configuration file. 

#### Getting the configuration file

It is recommended that you make an additional directory (e.g. `mkdir ~/valar_daemon` and `cd mkdir ~/valar_daemon`) and download a template for the configuration.

You can copy the template of the configuration file to the current directory using `wget https://raw.githubusercontent.com/ValarStaking/valar/refs/heads/master/projects/valar-daemon/daemon.config`.

Alternatively, you can navigate to the [provided URL](https://github.com/ValarStaking/valar/blob/master/projects/valar-daemon/daemon.config) and copy-paste the template to an empty file named `daemon.config`.

#### Configuring the Daemon

In the config file, you should update the following parameters in accordance with your setup:
- The ID of your ad `validator_ad_id_list = [<validator_ad_id>]`.
- The mnemonic of your Validator Manager (hot wallet) `validator_manager_mnemonic = <validator_manager_mnemonic>`.
- The URL and port of Algod running on your node, `algod_config_server = <URL:port>`. You can find this in your node's files, for example, usually under `var/lib/algorand/algo.net` for Linux users. 
- The admin API token to access Algod on your node, `algod_config_token = <token>`. You can find this in your node's files, for example, usually under `var/lib/algorand/algo.admin.token` for Linux users.

The other parameters offer advanced features and you can read up more about these in [the daemon's repository](https://github.com/ValarStaking/valar/blob/master/projects/valar-daemon/README.md).

### Starting the Daemon

You can run the Valar Daemon using `python -m valar_daemon.run_daemon`, which will search for the configuration file `daemon.config` **in the current working directory** and create an output log directory `valar-daemon-log` in the same directory. 

Alternatively, you can point the Daemon to a specific config file and log directory using `python -m valar_daemon.run_daemon --config_path <config_path> --log_path <log_path>`, where the additional parameters are:
- `<config_path>`: the path to the configuration file `daemon.config`, including the file's name.
- `<log_path>`: the path to where the Valar Daemon can make a new directory and populate it with the log (about 1 MB in size), including the log directory's name.

### Verifying that the Valar Daemon functions correctly

The Valar Daemon's first task is to switch the corresponding ad's state to `READY`. 
You can verify that this step was carried out successfully by checking the state of the ad on [stake.valar.solutions/dashboard](https://stake.valar.solutions/dashboard).

Additionally, you can monitor the Valar Daemon's interaction with smart contracts and the status of miscellaneous tasks using its logs. 
These are described in more detail in [a later section](#logs).

### Running in the background without interruption

You can run the Daemon in the background and keep it running even after you close the terminal or SSH connection using:

- `nohup python -m valar_daemon.run_daemon &` for Linux/macOS 
- `pythonw -m valar_daemon.run_daemon` for Windows

To verify that the Daemon is running successfully, you can:
- Check the logs in `valar-daemon-log`.
- Search the running processes on your system for `valar_daemon.run_daemon` (Linux/macOS) or `Python` (Windows).

For example, on Linux you can search for the Valar Daemon process using `ps aux | grep "valar_daemon.run_daemon"` and gracefully terminate it with `kill <PID>`.
On Windows, you can find the process in cmd with `wmic process where "name='pythonw.exe'" get Commandline, ProcessId` (or `wmic process where "name='python.exe'" get Commandline, ProcessId` if you used `python` to start the daemon instead of `pythonw`) and terminate it with `taskkill /F /pid <PID>`.

One of the alternatives is to deploy a screen (`screen`), launch the Daemon inside the screen (`python -m valar_daemon.run_daemon`), and detach from the screen (`ctrl+a+d`) before closing the terminal or SSH connection. 
You can later get the screen's ID (`screen -ls`) and re-attach to it (`screen -x <screen_ID>`).

Additionally, you can follow [the below guide on setting up a system service or cron job](#autorun), which will periodically check that the Daemon is running and run it if it isn't.


## Additional considerations 

<a id="logs"></a>

### Monitoring the Valar Daemon

You can monitor the operation of the Valar Daemon through the logs that reside at the chosen path `<log_path>`. 
Logging is structured in five levels, whose combined size is limited to approximately 1 MB by default. 
Old entries will be overwritten once this size is reached and only the latest log information is kept. 
The five logging levels, organized according to ([according to Python.logging](https://docs.python.org/3/library/logging.html)), are described below.

| Level    |                                                        Description                                                          | Subdirectory  |
|----------|-----------------------------------------------------------------------------------------------------------------------------|---------------|
| Critical | The most critical errors, such as an unreachable network, preventing the Valar Daemon from interacting with the blockchain. | `50-critical` |
| Error    | Errors which impact a specific part of the Valar Daemon, such as the fetching of information for one smart contract.        | `40-error`    |
| Warning  | Indicators of potential concern, such as having zero ads associated with the Valar Daemon.                                  | `30-warning`  |
| Info     | Informative messages of general nature, such as information about the ending of a Delegator Contract.                       | `20-info`     |
| Debug    | Detailed messages about separate components of the Valar Daemon.                                                            | `10-debug`    |

Each logging level includes it's own messages and those of higher priority. 
For example, the log `50-critical/critical.log` includes only critical error messages, while `10-debug/debug.log` includes all logged events. 
It is recommended that you regularly check in on the error messages with warning priority or higher in order to detect any malfunctions. 
Note that logs get eventually overwritten due to their size limit, thus is recommended that you duplicate the log file if it seems to include potentially relevant information.

*Please refer to [the log message README](https://github.com/ValarStaking/valar/blob/master/projects/valar-daemon/docs/README_log_messages.md) for a list of expected log messages.*

<a id="autorun"></a>

### Automatically starting the Valar Daemon

Your node may suffer from power, connectivity, or other issues. 
While the Valar Damon has several built-in mechanisms to provide resilience in such circumstances, it does not automatically start up after it has been terminated. 
To achieve this, you can employ a job scheduler on your system. 

The procedure for setting up a system service on Linux, a cron job on Linux/macOS, or Task Scheduler on Windows are described below. 
Please first verify that the Valar Daemon runs on you machine using the preceding steps and **terminate any running instances** before continuing.

#### Using Systemd on Linux

After setting up the `valar-daemon` directory and Python within it, you can instruct the Linux system daemon to monitor the Valar Daemon and start it in case it is not running (after reboot and during normal system operation). 
You can create a file on the path `/etc/systemd/system/valar.service` and populate its contents according to the following template:  

```
[Unit]
Description=Valar Daemon
After=network.target

[Service]
Type=simple
Environment="ALGORAND_DATA=/var/lib/algorand"
WorkingDirectory=<path-to-valar-daemon>
ExecStart=<interpreter-path> -m valar_daemon.run_daemon
User=<username>
Group=<username>
Restart=always
RestartSec=30s
ProtectSystem=false

[Install]
WantedBy=multi-user.target
```

Reload the configuration using `systemctl daemon-reload`, enable the Valar Daemon service `systemctl enable valar.service`, and start it  `systemctl start valar.service`.



#### Using Cron on Linux/macOS

##### Obtaining and configuring the script for checking the status of the Valar Daemon

You can download from repository [a template bash script](https://github.com/ValarStaking/valar/blob/master/projects/valar-daemon/check_script.sh) that checks whether the Valar Daemon is running and, if it is not running, starts it. 
Navigate to a directory where you want to keep the script and download the provided bash script using

`wget https://raw.githubusercontent.com/ValarStaking/valar/refs/heads/master/projects/valar-daemon/check_script.sh`

Next, open the script and point it to the necessary locations on your system.
You can configure the script using an editor of your liking, for example, by using `nano check_script.sh` or `vim check_script.sh`.
There you can adjust the following parameters:
- `INTERPRETER_PATH`: Path to the Python interpreter that you have set up or the corresponding alias.
- `LOG_PATH`: Path to the directory where the Valar Daemon will place its log.
- `CONFIG_PATH`: Path to the `daemon.config` file.
Note that all paths should preferably be absolute, i.e. starting with `/`.

You can run the Valar Daemon using the script by issuing the command `/bin/bash <path>/check_script.sh`. 
You can verify that the Valar Daemon is working by checking that the debug log at `LOG_PATH` that you just configured is being written to. 
You can use `tail -10 <path>/10-debug/debug.log` to confirm that the timestamps of the logged messages are recent (several seconds, depending on the Daemon's configuration). 
Alternatively, you can observe the log in real-time using `watch -n 1 "tail -n 10 <path>/10-debug/debug.log`.

##### Setting up cron

Cron is a job scheduler, which you can configure to periodically run `check_script.sh`. 
Hence, cron will monitor the Valar Daemon's status and start the Daemon if needed. 
Start by issuing the command `crontab -e` to open cron's configuration. 
There, navigate to the bottom and add the following line 

`* * * * * /bin/bash <path>/check_script.sh >> <path>/cron.log 2>&1`,

where `<path>` is the path to where you placed `check_script.sh`. 
Save and exit the editor to have cron run `check_script.sh` with a one-minute period and log output to `cron.log`. 
While the Valar Daemon is configured to use its own log directory, cron's log will enable you to see if there are any overarching system issues. 

Check that cron is running using `systemctl status cron` and start it if needed with `systemctl start cron` (you may need admin privileges).
You can again verify that the Valar Daemon is running by checking the file `<path>/10-debug/debug.log`.

Once you have set up cron, you can reduce the period at which the Valar Daemon is monitored to save resources. 
For example, you can run the job at the beginning of every full hour by setting the initial parameters to `0 * * * *` (run each hour on the zeroth minute). 

It is recommended to monitor the status of your ads and your node in general, regardless of cron.

##### Additional troubleshooting

There are three basic steps for debugging possible issues with the bash script or cron:
- Try to execute the `check_script.sh` manually, without cron.
- Check the Valar Daemon's debug log `<path>/10-debug/debug.log`.
- Check the log of the job scheduled by cron `cron.log`.

In addition, you can check:
- That you successfully updated cron's configuration with `crontab -l`. 
- If cron is running using `systemctl status cron`.
- Cron's log with `grep CRON /var/log/syslog`.

#### Using Task Scheduler on Windows

With Task Scheduler you can run a program on different trigger events on Windows.
Type `Task Scheduler` in Windows search bar.
A new window will open.

Click on `Task Scheduler Library` and create a new folder.
Name the folder e.g. `MyTasks` and click on the created folder.
In the menu bar then click on  `Action` and then `Create Task...`.
A new window appears.
Give the task a name, e.g. `Valar Daemon`.
Under `Security options` in `General` select the `Run whether user is logged on or not`.
This will start the daemon even if you are not logged into the computer.
Admin rights are needed for this.

Go to `Triggers` and create a new trigger.
Choose `At startup` under `Begin the task`.
This is start the daemon when the computer is started.
Optionally add `Repeat task every` e.g. `15 min` for an indefinite duration to periodically check if the daemon is running and start it if it in case it is not.
Ensure the task is enabled and it does not expire or is stopped.

Go to `Actions` and create a new action.
As `Program/script` select `pythonw.exe` under the correct installation path.
You can find its installation path by opening `cmd` and run `python`, where you can then enter:
```
import os, sys
os.path.dirname(sys.executable)
```
The path to python will be displayed.

Under `Add arguments (optional)` add `-m valar_daemon.run_daemon --config_path "<absolute-path>\daemon.config" --log_path "<absolute-path>\valar-daemon-log"`

Go to `Conditions` and disable `Start the task only if the computer is on AC power` under `Power`.

Go to `Settings` and enable `Run task as soon as possible after a scheduled start is missed` and disable `Stop the task if it runs longer than`.
Ensure also that `Do not start a new instance` is selected under `If the task is already running, then the following rule applies:`.

Click `OK` when all info is entered.
Enter admin password if prompted.

To check if the Task Scheduler has been correctly set, restart your computer.
After restart, run `wmic process where "name='pythonw.exe'" get Commandline, ProcessId`.
There should be one task `pythonw  -m valar_daemon.run_daemon` with the paths that were configured.
You can also open again the Task Scheduler and navigate to `Task Scheduler Library > MyTasks > Valar Daemon` to see information about its last run time and last run results, which should be `The task is currently running.`.
