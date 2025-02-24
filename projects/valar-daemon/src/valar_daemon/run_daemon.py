"""
Run the Valar Daemon. For more information see https://github.com/ValarStaking/valar.

Options:
  - `--config_path`,  Path to the config file. Defaults to `./daemon.config`.
  - `--log_path`,     Path to the log directory (created if does not exist). Defaults to `./valar-daemon-log`
"""
if __name__ == '__main__':

    import argparse
    from pathlib import Path
    from valar_daemon.Daemon import Daemon

    repo_link = 'https://github.com/ValarStaking/valar'
    parser = argparse.ArgumentParser(description=
        f"Run the Valar Daemon. For more information see {repo_link}."
    )
    parser.add_argument(
        '--config_path', type=str, required=False, 
        help='Path to the config file. Defaults to `./daemon.config`.',
        default=Path(Path.cwd(), 'daemon.config')
    )
    parser.add_argument(
        '--log_path', type=str, required=False, 
        help='Path to the log directory (created if does not exist). Defaults to `./valar-daemon-log`',
        default=Path(Path.cwd(), 'valar-daemon-log')
    )
    args = parser.parse_args()

    print(
        '\n'
        'Pointing the Valar Daemon to the following:\n'
        f'\t Config file at: {args.config_path}\n'
        f'\t Log directory at: {args.log_path}\n'
        '\n'
        'Starting Valar Daemon. Expect no further stdout stream - check the above log directory for feedback.'
        '\n'
    )

    daemon = Daemon(
        args.log_path,
        args.config_path
    )

    daemon.run()
