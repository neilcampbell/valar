#!/bin/bash
# Template for a script that checks if the Valar Daemon is running and starts it if not.
# Used in combination with cron, systemd, or other, to periodically monitor (and start) the Valar Daemon.

# Can be left as-is, unless the files were renamed
SCRIPT_NAME="valar_daemon.run_daemon"
CONFIG_NAME="daemon.config"

# Replace "..." in the below four parameters in accordance with your setup
INTERPRETER_PATH="..."              # ... -> Absolute path or alias to the configured interpreter.
LOG_PATH="..."                      # Absolute path to a directory where the Valar Daemon will place its logs.
CONFIG_PATH=".../$CONFIG_NAME"      # Absolute path to the config file `run_daemon.py` or equivalent.

# Checks if the daemon is running
if ! pgrep -f "$SCRIPT_NAME" > /dev/null; then
    # If not, start it
    $INTERPRETER_PATH -m $SCRIPT_NAME --config_path $CONFIG_PATH --log_path $LOG_PATH
fi
