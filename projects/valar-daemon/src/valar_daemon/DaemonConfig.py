"""Class definition for managing daemon config.
"""
import configparser
from pathlib import Path


class DaemonConfig(object):
    """Config abstraction.

    Allows the creation, interpretation, and updating of a config file.

    Attributes
    ----------
    validator_ad_id_list : list
        Validator ad smart contract ID.
    validator_manager_mnemonic : str
        Validator mnemonic.
    algod_config_server : _type_, optional
        Algod URL.
    algod_config_token : str, optional
        Algod token.
    loop_period_s : int, optional
        Execution loop period in seconds, by default 3.
    claim_period_s : int, optional
        Earnings claim period in seconds.
    max_log_file_size_B : str, optional
        Maximal size of individual log files in bytes.
    num_of_log_files_per_level : str, optional
        Number of log files for each log level.
    config_path : Path
        The config file location.
    config_filename : str
        Name of the config file.
    config_full_path : Path
        Full path to the config, including the filename.
    swap_full_path : Path
        Full path to the swap, including the filename.

    Methods
    -------
    get_swap_filename
        Get the swap (temporary) filename.
    create_swap
        Copy the config to the same directory as a `.<...>.swp` file.
    read_config
        Read the configuration file, updating the class' parameters.
    read_swap
        Read swap file, updating the class' parameters.
    read
        Read daemon config file, updating the class' parameters.
    write
        Make config string and write it to a file.
    _convert_claim_period_from_hours_to_seconds
        Convert the claim period from hours to seconds.
    _convert_claim_period_from_seconds_to_hours_rounded
        Convert the claim period from seconds to hours and round the period.
    """


    def __init__(
        self,
        config_path: Path,
        config_filename: str
    ):
        """Make config object.

        Parameters
        ----------
        config_path : Path
            The config file location.
        config_filename : str
            Name of the config file.
        """
        # Configuration parameters
        self.validator_ad_id_list = None
        self.validator_manager_mnemonic = None
        self.algod_config_server = None
        self.algod_config_token = None
        self.loop_period_s = None
        self.claim_period_s = None
        self.config_path = config_path
        self.config_filename = config_filename
        self.config_full_path = Path(config_path, config_filename)
        self.swap_full_path = Path(config_path, self.get_swap_filename())

    
    def get_swap_filename(
        self
    ) -> str:
        """Get the swap (temporary) filename.

        Returns
        -------
        str
            Swap filename.
        """
        return f'.{self.config_filename}.swp'


    def create_swap(
        self
    ) -> None:
        """Copy the config to the same directory as a `.<...>.swp` file.
        """
        self.write(self.swap_full_path)
    

    def read_config(
        self
    ) -> None | str:
        """Read the configuration file, updating the class' parameters.

        Return
        ------
        None | str
            Warning message if applicable.
        """
        return self.read(self.config_full_path)


    def read_swap(
        self
    ) -> None | str:
        """Read swap file, updating the class' parameters.

        Return
        ------
        None | str
            Warning message if applicable.
        """
        return self.read(self.swap_full_path)


    def read(
        self,
        full_path: Path,
    ) -> None | str:
        """Read daemon config file, updating the class' parameters.

        Parameters
        ----------
        full_path : Path
            Path, including filename to the config file.

        Raises
        ------
        ValueError
            non-existent config.

        Return
        ------
        None | str
            Warning message if applicable.
        """
        # Catch non-existent file
        if not self.config_full_path.is_file():
            raise ValueError(f'Can\'t find the provided config file at {str(full_path)}')
        
        config_read_warning = None
        
        config = configparser.RawConfigParser(defaults=None, strict=False, allow_no_value=True)
        config.read(full_path)

        self.validator_manager_mnemonic = str(config.get('validator_config', 'validator_manager_mnemonic'))
        self.validator_ad_id_list = eval(config.get('validator_config', 'validator_ad_id_list'))

        self.algod_config_server = str(config.get('algo_client_config', 'algod_config_server'))
        self.algod_config_token = str(config.get('algo_client_config', 'algod_config_token'))

        self.max_log_file_size_B = int(eval(config.get('logging_config', 'max_log_file_size_B')))
        self.num_of_log_files_per_level = int(eval(config.get('logging_config', 'num_of_log_files_per_level')))

        self.loop_period_s = int(config.get('runtime_config', 'loop_period_s'))
        # Check claim period and set to 1 week if not yet defined
        if config.has_option('runtime_config', 'claim_period_h'):
            claim_period_h = int(config.get('runtime_config', 'claim_period_h'))
        else:
            claim_period_h = 168
            config_read_warning = 'Daemon config does not include the claim period - setting it to 1 week.'
        self.claim_period_s = self._convert_claim_period_from_hours_to_seconds(claim_period_h)

        return config_read_warning


    # def update_config(
    #     self,
    #     validator_ad_id_list: list,
    #     validator_manager_mnemonic: str,
    #     algod_config_server: str='http://localhost:4001',
    #     algod_config_token: str='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    #     loop_period_s: int=15,
    #     claim_period_s: int=86400,
    #     max_log_file_size_B: int=400*1024,
    #     num_of_log_files_per_level: int=3
    # ) -> None:
    #     """Update config parameters.

    #     Parameters
    #     ----------
    #     validator_ad_id_list : list
    #         Validator ad smart contract ID.
    #     validator_manager_mnemonic : str
    #         Validator mnemonic.
    #     algod_config_server : str, optional
    #         Algod URL, by default 'http://localhost:4001'.
    #     algod_config_token : str, optional
    #         Algod token, by default 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'.
    #     loop_period_s : int, optional
    #         Execution loop period in seconds, by default 15.
    #     claim_period_s : int, optional
    #         Earnings claim period in seconds, by default 86400 (24 hours).
    #     max_log_file_size_B : str, optional
    #         Maximal size of individual log files in bytes, by default 400*1024 (400 kB).
    #     num_of_log_files_per_level : str, optional
    #         Number of log files for each log level, by default 3.
    #     """
    #     self.validator_ad_id_list = validator_ad_id_list
    #     self.validator_manager_mnemonic = validator_manager_mnemonic
    #     self.algod_config_server = algod_config_server
    #     self.algod_config_token = algod_config_token
    #     self.loop_period_s = loop_period_s
    #     self.claim_period_s = claim_period_s
    #     self.max_log_file_size_B = max_log_file_size_B
    #     self.num_of_log_files_per_level = num_of_log_files_per_level


    def write(
        self,
        path_to_write: str,
    ) -> None:
        """Make config string and write it to a file.

        Parameters
        ----------
        path_to_write : str
            Full path including filename.
        """
        config_content_string = '\n' + \
        '[validator_config] #####################################################################################################' + '\n' + \
        '\n' + \
        f'validator_ad_id_list = {self.validator_ad_id_list}' + '\n' + \
        f'validator_manager_mnemonic = {self.validator_manager_mnemonic}' + '\n' + \
        '\n\n' + \
        '[algo_client_config] ###################################################################################################' + '\n' + \
        '\n' + \
        f'algod_config_server = {self.algod_config_server}' + '\n' + \
        f'algod_config_token = {self.algod_config_token}' + '\n' + \
        '\n\n' + \
        '[logging_config] #######################################################################################################' + '\n' + \
        '\n' + \
        f'max_log_file_size_B = {self.max_log_file_size_B}' + '\n' \
        f'num_of_log_files_per_level = {self.num_of_log_files_per_level}' + '\n' \
        '\n\n' + \
        '[runtime_config] #######################################################################################################' + '\n' + \
        '\n' + \
        f'loop_period_s = {self.loop_period_s}' + '\n' + \
        f'claim_period_h = {self._convert_claim_period_from_seconds_to_hours_rounded(self.claim_period_s)}' + '\n'

        with open(path_to_write, 'w') as f:
            f.write(config_content_string)


    @staticmethod
    def _convert_claim_period_from_hours_to_seconds(
        claim_period_h: int | float
    ) -> int:
        """Convert the claim period from hours to seconds.

        Parameters
        ----------
        claim_period_h : int | float
            Claim period in hours.

        Returns
        -------
        int
            Claim period in seconds.
        """
        return int(claim_period_h * 3600)


    @staticmethod
    def _convert_claim_period_from_seconds_to_hours_rounded(
        claim_period_s: int | float
    ) -> int:
        """Convert the claim period from seconds to hours and round the period.

        Parameters
        ----------
        claim_period_s : int | float
            Claim period in seconds.

        Returns
        -------
        int
            Claim period in hours.
        """
        return max(1, int(round(claim_period_s / 3600)))
    