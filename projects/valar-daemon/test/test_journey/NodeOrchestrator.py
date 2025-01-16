import os
import threading
from typing import Tuple
from pathlib import Path
# from multiprocessing import Process

from algosdk import mnemonic
from algokit_utils.beta.account_manager import AddressAndSigner

from valar_daemon.Daemon import Daemon
from valar_daemon.DaemonConfig import DaemonConfig


def prep_daemon_config(
    valman: AddressAndSigner, 
    valad_id: int,
    daemon_loop_period_s: float,
    config_path: Path=None
) -> Tuple[Path, str]:
    """Prepare daemon config file.

    Parameters
    ----------
    valman : AddressAndSigner
        Validator manager.
    valad_id : int
        Validator ad app ID.
    daemon_loop_period_s : float
        Daemon period of app / partkey maintenance.
    config_path : Path, optional
        Path to where the config is stored, default is None (see internal logic).

    Returns
    -------
    Tuple[Path, str]
        Path to the config and the config name.
    """
    # Make and route to tmp if needed
    if config_path is None:
        config_path = Path(Path(__file__).parent, 'tmp')
        try: os.makedirs(str(config_path))
        except: pass
    config_name = 'daemon.config'
    # Initialize
    daemon_config = DaemonConfig(
        config_path,
        config_name
    )
    # Obtain manager mnemonic
    mne = mnemonic.from_private_key(valman.signer.private_key)
    # Populate
    daemon_config.update_config(
        validator_ad_id_list=[valad_id],
        validator_manager_mnemonic=mne,
        loop_period_s=daemon_loop_period_s
    )
    # Write to file
    daemon_config.write_config()
    return config_path, config_name


class NodeOrchestrator():

    def __init__(
            self, 
            actions: list, 
            valman: AddressAndSigner,
            valad_id: int, 
            daemon_loop_period_s: float,
            config_path: Path
        ):
        """Initialize node orchestrator for starting/stopping the daemon and its algod service.

        Parameters
        ----------
        actions : list
            Actions that the orchestrator will take.
        valman : AddressAndSigner
            Validator manager.
        valad_id : int
            Validator ad app ID.
        daemon_loop_period_s : float
            Daemon period of app / partkey maintenance.
        config_path : Path
            Path to where the config is stored (normally `tmp_path` fixture).
        """
        self.actions = actions
        self.daemon_thread = None
        self.daemon = None
        self.config_path, self.config_name = prep_daemon_config(
            valman=valman,
            valad_id=valad_id,
            daemon_loop_period_s=daemon_loop_period_s,
            config_path=config_path
        )

    def refresh(self, last_round: int) -> int:
        """Take action if needed.

        Parameters
        ----------
        last_round : int
            The last round number in relative terms, since the beginning of the test.

        Returns
        -------
        int
            Indicator of additional actions pending (0 - empty, 1 - more actions pending).
        """
        if len(self.actions) > 0: # Actions pending
            next_action = self.actions[0]
            if next_action[0] <= last_round: # Should take action now
                # Turn daemon on/off
                if next_action[1] & 1 << 7:
                    print('Start daemon')
                    self.start_daemon_thread()
                else:
                    print('Stop daemon')
                    self.stop_daemon_thread()
                # Turn algod on/off
                if next_action[1] & 1 << 0:
                    print('Enable Algod')
                    self.enable_algod()
                else:
                    print('Disable Algod')
                    self.disable_algod()
                self.actions.pop(0)
            return 1
        return 0

    def enable_algod(self):
        """Enable the daemon's algod by pointing it to the correct address. 
        """
        if self.daemon is not None:
            self.daemon.algorand_client.client.algod.algod_address = self.daemon_algod_address

    def disable_algod(self):
        """Disable the daemon's algod by pointing it to an incorrect address. 
        """
        if self.daemon is not None:
            self.daemon.algorand_client.client.algod.algod_address = "https://some.cloud"

    def start_daemon_thread(self):
        """Start up the daemon's thread.
        """
        # Initialize the daemon
        self.daemon = Daemon(
            str(Path(self.config_path)),
            str(Path(self.config_path, self.config_name))
        )
        # Save correct algod address for later manipulation
        self.daemon_algod_address = self.daemon.algorand_client.client.algod.algod_address
        # Run the daemon
        self.daemon_thread = threading.Thread(
            target=self.daemon.run
        )
        # self.daemon_thread = Process(
        #     target=self.daemon.run
        # )
        self.daemon_thread.start()

    def stop_daemon_thread(self):
        """Stop the daemon's thread.
        """
        # if self.daemon is not None:
        #     self.daemon.stop()                # Soft stop
        # if self.daemon_thread is not None:
        #     # self.daemon_thread.terminate()  # Hard stop
        #     self.daemon_thread.join()         # Soft stop
        self.daemon.stop()          # Soft stop
        self.daemon_thread.join()   # Soft stop
        self.daemon = None
        self.daemon_thread = None
