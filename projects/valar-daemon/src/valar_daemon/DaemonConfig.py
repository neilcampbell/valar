"""Class definition for managing daemon config.
"""
import shutil
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
        Algod URL, by default 'http://localhost:4001'.
    algod_config_token : str, optional
        Algod token, by default 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'.
    # indexer_config_server : _type_, optional
    #     Indexer URL, by default 'http://localhost:8980'.
    # indexer_config_token : str, optional
    #     Indexer token, by default 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'.
    # kmd_config_server : _type_, optional
    #     KMD URL, by default 'http://localhost:4002'.
    # kmd_config_token : str, optional
    #     KMD token, by default 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'.
    loop_period_s : int, optional
        Execution loop period in seconds, by default 3.
    # logging_level : str, optional
    #     Logging amount / level, by default 'DEBUG'.
    max_log_file_size_B : str, optional
        Maximal size of individual log files in bytes, by default 40*1024 (40 kB).
    num_of_log_files_per_level : str, optional
        Number of log files for each log level, by default 5.
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
    get_swap_filemane
        Get the swap (temporary) filename.
    create_swap
        Copy the config to the same directory as a `.<...>.swp` file.
    read_config
        Read the configuration file, updating the class' parameters.
    read_swap
        Read swap file, updating the class' parameters.
    read
        Read daemon config file, updating the class' parameters.
    update_config
        Update config parameters.
    write_config
        Make config string and write it to a file.
    """


    def __init__(
        self,
        config_path: Path,
        config_filename: str,
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
        # self.indexer_config_server = None
        # self.indexer_config_token = None
        # self.kmd_config_server = None
        # self.kmd_config_token = None
        self.loop_period_s = None
        # self.logging_level = None
        # File paths and names
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
        shutil.copy(
            self.config_full_path, 
            self.swap_full_path
        )
    

    def read_config(
        self
    ) -> None:
        """Read the configuration file, updating the class' parameters.
        """
        self.read(self.config_full_path)


    def read_swap(
        self
    ):
        """Read swap file, updating the class' parameters.
        """
        self.read(self.swap_full_path)


    def read(
        self,
        full_path: Path,
    ) -> None:
        """Read daemon config file, updating the class' parameters.

        Parameters
        ----------
        full_path : Path
            Path, including filename to the config file.

        Raises
        ------
        ValueError
            non-existent config.
        """
        # Catch non-existent file
        if not self.config_full_path.is_file():
            raise ValueError(f'Can\'t find the provided config file at {str(full_path)}')
        
        config = configparser.RawConfigParser(defaults=None, strict=False, allow_no_value=True)
        config.read(full_path)

        self.validator_manager_mnemonic = str(config.get('validator_config', 'validator_manager_mnemonic'))
        self.validator_ad_id_list = eval(config.get('validator_config', 'validator_ad_id_list'))

        self.algod_config_server =   str(config.get('algo_client_config', 'algod_config_server'))
        self.algod_config_token =    str(config.get('algo_client_config', 'algod_config_token'))
        # self.indexer_config_server = str(config.get('algo_client_config', 'indexer_config_server'))
        # self.indexer_config_token =  str(config.get('algo_client_config', 'indexer_config_token'))
        # self.kmd_config_server =     str(config.get('algo_client_config', 'kmd_config_server'))
        # self.kmd_config_token =      str(config.get('algo_client_config', 'kmd_config_token'))

        # self.loop_period_s = float(config.get('daemon_config', 'loop_period_s'))
        # self.logging_level = str(config.get('daemon_config', 'logging_level')).upper()

        self.max_log_file_size_B = int(eval(config.get('logging_config', 'max_log_file_size_B')))
        self.num_of_log_files_per_level = int(eval(config.get('logging_config', 'num_of_log_files_per_level')))

        self.loop_period_s = float(config.get('runtime_config', 'loop_period_s'))


    def update_config(
        self,
        validator_ad_id_list: list,
        validator_manager_mnemonic: str,
        algod_config_server: str='http://localhost:4001',
        algod_config_token: str='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
        # indexer_config_server: str='http://localhost:8980',
        # indexer_config_token: str='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
        # kmd_config_server: str='http://localhost:4002',
        # kmd_config_token: str='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
        loop_period_s: int=15,
        # logging_level: str='DEBUG'
        max_log_file_size_B: int=40*1024,
        num_of_log_files_per_level: int=3
    ) -> None:
        """Update config parameters.

        Parameters
        ----------
        validator_ad_id_list : list
            Validator ad smart contract ID.
        validator_manager_mnemonic : str
            Validator mnemonic.
        algod_config_server : _type_, optional
            Algod URL, by default 'http://localhost:4001'.
        algod_config_token : str, optional
            Algod token, by default 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'.
        # indexer_config_server : _type_, optional
        #     Indexer URL, by default 'http://localhost:8980'.
        # indexer_config_token : str, optional
        #     Indexer token, by default 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'.
        # kmd_config_server : _type_, optional
        #     KMD URL, by default 'http://localhost:4002'.
        # kmd_config_token : str, optional
        #     KMD token, by default 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'.
        loop_period_s : int, optional
            Execution loop period in seconds, by default 15.
        # logging_level : str, optional
        #     Logging amount / level, by default 'DEBUG'.
        max_log_file_size_B : str, optional
            Maximal size of individual log files in bytes, by default 40*1024 (40 kB).
        num_of_log_files_per_level : str, optional
            Number of log files for each log level, by default 3.
        """
        self.validator_ad_id_list = validator_ad_id_list
        self.validator_manager_mnemonic = validator_manager_mnemonic
        self.algod_config_server = algod_config_server
        self.algod_config_token = algod_config_token
        # self.indexer_config_server = indexer_config_server
        # self.indexer_config_token = indexer_config_token
        # self.kmd_config_server = kmd_config_server
        # self.kmd_config_token = kmd_config_token
        self.loop_period_s = loop_period_s
        # self.logging_level = logging_level
        self.max_log_file_size_B = max_log_file_size_B
        self.num_of_log_files_per_level = num_of_log_files_per_level


    def write_config(
        self,
    ) -> None:
        """Make config string and write it to a file.
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
        f'loop_period_s = {self.loop_period_s}' + '\n'

        with open(self.config_full_path, 'w') as f:
            f.write(config_content_string)
