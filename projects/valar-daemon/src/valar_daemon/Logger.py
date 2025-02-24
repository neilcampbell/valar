"""Abstraction of the Daemon's logging functionality.
"""
import os 
import yaml
import logging
import inspect
from pathlib import Path
from logging.handlers import RotatingFileHandler


class Logger():

    DEBGUG_LEVEL = 10
    INFO_LEVEL = 20
    WARNING_LEVEL = 30
    ERROR_LEVEL = 40
    CRITICAL_LEVEL = 50

    def __init__(
            self,
            log_dirpath: str,
            log_max_size_bytes: int,
            log_file_count: int,
            log_message_source_path: str=None,
        ):
        """Initialize logger, acting as a proxy for pre-defined messages and logs on different logging levels.

        Notes
        -----
        Creates a 5-level log, consisting of info, debug, warning, error, and critical.

        Parameters
        ----------
        log_dirpath : str
            Path to where the logs will be produced.
        log_max_size_bytes : int
            Maximal size of an individual file in bytes.
        log_file_count : int
            Number of log files per log level (5 levels in total).
        log_message_source_path : str, optional
            Path to the definitions of pre-defined log messages. Default is None (log in src/valar_daemon dir).
        """
        # Load in pre-defined messages
        if log_message_source_path is None:
            log_message_source_path = str(Path(Path(__file__).parent, 'log_messages_source.yaml'))
        log_messages = Logger._fetch_log_messages(log_message_source_path)
        self.log_messages = Logger._strip_trailing_newline(log_messages)

        # Make logger master directory
        Logger.try_to_make_directory(log_dirpath)

        # Make debug subdirectory and initialize debug logger
        debug_log_dirpath = Path(log_dirpath, f'{self.DEBGUG_LEVEL}-debug')
        Logger.try_to_make_directory(debug_log_dirpath)
        self.debug_logger = self.create_logger(
            debug_log_dirpath,
            'debug', 
            log_max_size_bytes,
            log_file_count - 1 # If greater than 0, log backups are added
        )

        # Make info subdirectory and initialize info logger
        info_log_dirpath = Path(log_dirpath, f'{self.INFO_LEVEL}-info')
        Logger.try_to_make_directory(info_log_dirpath)
        self.info_logger = self.create_logger(
            info_log_dirpath,
            'info', 
            log_max_size_bytes,
            log_file_count - 1 # If greater than 0, log backups are added
        )

        # Make warning subdirectory and initialize info warning
        warning_log_dirpath = Path(log_dirpath, f'{self.WARNING_LEVEL}-warning')
        Logger.try_to_make_directory(warning_log_dirpath)
        self.warning_logger = self.create_logger(
            warning_log_dirpath,
            'warning', 
            log_max_size_bytes,
            log_file_count - 1 # If greater than 0, log backups are added
        )

        # Make error subdirectory and initialize info error
        error_log_dirpath = Path(log_dirpath, f'{self.ERROR_LEVEL}-error')
        Logger.try_to_make_directory(error_log_dirpath)
        self.error_logger = self.create_logger(
            error_log_dirpath,
            'error', 
            log_max_size_bytes,
            log_file_count - 1 # If greater than 0, log backups are added
        )

        # Make critical subdirectory and initialize info critical
        critical_log_dirpath = Path(log_dirpath, f'{self.CRITICAL_LEVEL}-critical')
        Logger.try_to_make_directory(critical_log_dirpath)
        self.critical_logger = self.create_logger(
            critical_log_dirpath,
            'critical', 
            log_max_size_bytes,
            log_file_count - 1 # If greater than 0, log backups are added
        )

    ### Utilities ######################################################################################################

    @staticmethod
    def try_to_make_directory(dirpath: str):
        """Try to make a directory and any parents if these are missing.

        Parameters
        ----------
        dirpath : str
            Path to the directory that needs to be created.

        Raises
        ------
        e
            An error, except `FileExistsError`.
        """
        try:
            os.makedirs(dirpath)
        except FileExistsError as e:
            pass
        except Exception as e:
            raise e 

    @staticmethod
    def create_logger(
        log_dirpath: str,
        logname: str,
        log_max_size_bytes: int,
        log_file_count: int
    ) -> logging.Logger:
        """Create logger.

        Parameters
        ----------
        log_dirpath : str
            Path to where the logs will be produced.
        logname : str
            Name of the created log.
        log_max_size_bytes : int
            Maximal size of an individual file in bytes.
        log_file_count : int
            Number of log files per log level (5 levels in total).

        Returns
        -------
        logging.Logger
            The created logger.
        """
        # Create log file handler
        handler = RotatingFileHandler(
            Path(log_dirpath, f'{logname}.log'), 
            maxBytes=log_max_size_bytes, 
            backupCount=log_file_count
        )
        # Set logging level - allow the logging of everything
        handler.setLevel(logging.DEBUG)
        # Set up the prefix of each message
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        # Create logger
        logger = logging.getLogger(logname)
        # Set log level once more, this time for the logger
        logger.setLevel(logging.DEBUG)
        # Connect the log file handler to the logger 
        logger.addHandler(handler)
        return logger
        
    @staticmethod
    def _fetch_log_messages(log_message_source_path: str) -> dict:
        """Fetch the pre-defined log messages.

        Parameters
        ----------
        log_message_source_path : str
            Path to the definitions of pre-defined log messages.

        Returns
        -------
        dict
            Pre-defined log messages.
        """
        log_file = Path(log_message_source_path)
        with log_file.open("r") as f:
            return yaml.safe_load(f)
        
    @staticmethod
    def _strip_trailing_newline(log_messages: dict) -> dict:
        """Strip the pre-defined log messages of trailing `\n`, which are likely present, depending on user input.

        Parameters
        ----------
        log_messages : dict
            Pre-defined log messages.

        Returns
        -------
        dict
            Log messages without trailing `\n`
        """
        for _, value in log_messages.items():
            value['description'] = value['description'].rstrip("\n")
            value['message'] = value['message'].rstrip("\n")
        return log_messages

    @staticmethod
    def get_filename_and_lineno(call_stack_regression_levels: int=2) -> str:
        """Get the file name and line number string for prepending to log messages.

        Notes
        -----
        Calling through pre-defined messages requires 4-level regression and through the `info` etc. 2-level.
        Would be simpler to always call bottom-most caller (const. level), but it changes behavior when when debugging.

        Parameters
        ----------
        call_stack_regression_levels : int, optional
            Number of levels regresses on the call stack when lookin up the original file and line number, by default 2.

        Returns
        -------
        str
            Format accoring to: '<file>:<line>'
        """
        # caller_frame = inspect.currentframe().f_back.f_back
        caller_frame = inspect.stack()[call_stack_regression_levels]
        # filename = os.path.basename(caller_frame.f_code.co_filename)
        filename = os.path.basename(caller_frame.filename)
        # lineno = caller_frame.f_lineno
        lineno = caller_frame.lineno
        return f'{filename}:{lineno}'


    def _log(
            self, 
            level: int, 
            message: str, 
            **kwargs
        ):
        """Proxy for logging a message at the corresponding level.

        Parameters
        ----------
        level : int
            The logging level.
        message : str
            Logged message.
        """
        kwargs['call_stack_regression_levels'] = 5
        if level == self.DEBGUG_LEVEL:
            self.debug(message, **kwargs)
        elif level == self.INFO_LEVEL:
            self.info(message, **kwargs)
        elif level == self.WARNING_LEVEL:
            self.warning(message, **kwargs)
        elif level == self.ERROR_LEVEL:
            self.error(message, **kwargs)
        elif level == self.CRITICAL_LEVEL:
            self.critical(message, **kwargs)
        

    ### Generic messaging ##############################################################################################

    @staticmethod
    def prepend_filename_and_lineno_to_message(
        message: str,
        **kwargs
    ) -> str:
        """Prepend the name of the file and the file number where the logger was called.

        Parameters
        ----------
        message : str
            The logged message.

        Returns
        -------
        str
            Formatted message as: '<file and line> - <message>'.
        """
        return f'{Logger.get_filename_and_lineno(**kwargs)} - ' + message


    def debug(
            self, 
            message: str, 
            append_filename_and_lineno: bool=True, 
            **kwargs
        ):
        """Log a debug message.

        Parameters
        ----------
        message : str
            Logged message.
        append_filename_and_lineno : bool, optional
            Flag whether to append the file name and line number where the logger was called, by default True.
        """
        if append_filename_and_lineno:
            message = Logger.prepend_filename_and_lineno_to_message(message, **kwargs)
        self.debug_logger.debug(message)


    def info(
            self, 
            message: str, 
            append_filename_and_lineno: bool=True, 
            **kwargs
        ):
        """Log an info message.

        Parameters
        ----------
        message : str
            Logged message.
        append_filename_and_lineno : bool, optional
            Flag whether to append the file name and line number where the logger was called, by default True.
        """
        if append_filename_and_lineno:
            message = Logger.prepend_filename_and_lineno_to_message(message, **kwargs)
        self.debug_logger.info(message)
        self.info_logger.info(message)


    def warning(
            self, 
            message: str, 
            append_filename_and_lineno: bool=True, 
            **kwargs
        ):
        """Log a warning message.

        Parameters
        ----------
        message : str
            Logged message.
        append_filename_and_lineno : bool, optional
            Flag whether to append the file name and line number where the logger was called, by default True.
        """
        if append_filename_and_lineno:
            message = Logger.prepend_filename_and_lineno_to_message(message, **kwargs)
        self.debug_logger.warning(message)
        self.info_logger.warning(message)
        self.warning_logger.warning(message)


    def error(
            self, 
            message: str, 
            append_filename_and_lineno: bool=True, 
            **kwargs
        ):
        """Log an error message.

        Parameters
        ----------
        message : str
            Logged message.
        append_filename_and_lineno : bool, optional
            Flag whether to append the file name and line number where the logger was called, by default True.
        """
        if append_filename_and_lineno:
            message = Logger.prepend_filename_and_lineno_to_message(message, **kwargs)
        self.debug_logger.error(message)
        self.info_logger.error(message)
        self.warning_logger.error(message)
        self.error_logger.error(message)


    def critical(
            self, 
            message: str, 
            append_filename_and_lineno: bool=True, 
            **kwargs
        ):
        """Log a critical message.

        Parameters
        ----------
        message : str
            Logged message.
        append_filename_and_lineno : bool, optional
            Flag whether to append the file name and line number where the logger was called, by default True.
        """
        if append_filename_and_lineno:
            message = Logger.prepend_filename_and_lineno_to_message(message, **kwargs)
        self.debug_logger.critical(message)
        self.info_logger.critical(message)
        self.warning_logger.critical(message)
        self.error_logger.critical(message)
        self.critical_logger.critical(message)


    ### Pre-defined messaging ##########################################################################################

    # def specific_log_message(self, par1, par2):
    #     self._log(
    #         self.log_messages["specific-log-message"]["level"],
    #         self.log_messages["specific-log-message"]["message"].format(par1=par1, par2=par2)
    #     )


    ############################################################################
    ### Generic ################################################################
    ############################################################################

    def log_current_round(
        self,
        current_round: int
    ):
        self._log(
            self.log_messages["current_round"]["level"],
            self.log_messages["current_round"]["message"].format(current_round=current_round)
        )

    ############################################################################
    ### Daemon #################################################################
    ############################################################################

    def log_maintaining_valads(
        self,
        num_of_valads: int
    ):
        self._log(
            self.log_messages["maintaining_valads"]["level"],
            self.log_messages["maintaining_valads"]["message"].format(num_of_valads=num_of_valads)
        )

    def log_state_of_valad_with_id(
        self,
        app_id: int,
        state: bytes
    ):
        self._log(
            self.log_messages["state_of_valad_with_id"]["level"],
            self.log_messages["state_of_valad_with_id"]["message"].format(app_id=app_id, state=state)
        )

    def log_set_valad_ready_attribute_error(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["set_valad_ready_attribute_error"]["level"],
            self.log_messages["set_valad_ready_attribute_error"]["message"].format(app_id=app_id)
        )

    def log_maintaining_delcos(
        self,
        num_of_delcos: int
    ):
        self._log(
            self.log_messages["maintaining_delcos"]["level"],
            self.log_messages["maintaining_delcos"]["message"].format(num_of_delcos=num_of_delcos)
        )

    def log_unknown_delco_error(
        self,
        app_id: int,
        e: Exception
    ):
        self._log(
            self.log_messages["unknown_delco_error"]["level"],
            self.log_messages["unknown_delco_error"]["message"].format(app_id=app_id, e=e)
        )

    def log_removed_ended_or_deleted_delco(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["removed_ended_or_deleted_delco"]["level"],
            self.log_messages["removed_ended_or_deleted_delco"]["message"].format(app_id=app_id)
        )

    def log_state_of_delco_with_id(
        self,
        app_id: int,
        state: bytes
    ):
        self._log(
            self.log_messages["state_of_delco_with_id"]["level"],
            self.log_messages["state_of_delco_with_id"]["message"].format(app_id=app_id, state=state)
        )

    def log_unknown_delco_state(
        self,
        state: bytes
    ):
        self._log(
            self.log_messages["unknown_delco_state"]["level"],
            self.log_messages["unknown_delco_state"]["message"].format(state=state)
        )

    def log_delco_in_ready_handler(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["delco_in_ready_handler"]["level"],
            self.log_messages["delco_in_ready_handler"]["message"].format(app_id=app_id)
        )

    def log_urlerror_checking_partkey_generated(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["urlerror_checking_partkey_generated"]["level"],
            self.log_messages["urlerror_checking_partkey_generated"]["message"].format(app_id=app_id)
        )

    def log_partkeys_generated_for_delco(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["partkeys_generated_for_delco"]["level"],
            self.log_messages["partkeys_generated_for_delco"]["message"].format(app_id=app_id)
        )

    def log_delco_cannot_pay(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["delco_cannot_pay"]["level"],
            self.log_messages["delco_cannot_pay"]["message"].format(app_id=app_id)
        )

    def log_attributeerror_cannot_pay(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["attributeerror_cannot_pay"]["level"],
            self.log_messages["attributeerror_cannot_pay"]["message"].format(app_id=app_id)
        )

    def log_logicerror_cannot_pay(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["logicerror_cannot_pay"]["level"],
            self.log_messages["logicerror_cannot_pay"]["message"].format(app_id=app_id)
        )

    def log_httperror_cannot_pay(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["httperror_cannot_pay"]["level"],
            self.log_messages["httperror_cannot_pay"]["message"].format(app_id=app_id)
        )

    def log_partkeys_not_submitted(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["partkeys_not_submitted"]["level"],
            self.log_messages["partkeys_not_submitted"]["message"].format(app_id=app_id)
        )

    def log_attributeerror_partkeys_not_submitted(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["attributeerror_partkeys_not_submitted"]["level"],
            self.log_messages["attributeerror_partkeys_not_submitted"]["message"].format(app_id=app_id)
        )

    def log_logicerror_partkeys_not_submitted(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["logicerror_partkeys_not_submitted"]["level"],
            self.log_messages["logicerror_partkeys_not_submitted"]["message"].format(app_id=app_id)
        )

    def log_httperror_partkeys_not_submitted(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["httperror_partkeys_not_submitted"]["level"],
            self.log_messages["httperror_partkeys_not_submitted"]["message"].format(app_id=app_id)
        )

    def log_partkey_params_submitted(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["partkey_params_submitted"]["level"],
            self.log_messages["partkey_params_submitted"]["message"].format(app_id=app_id)
        )

    def log_attributeerror_partkey_submit(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["attributeerror_partkey_submit"]["level"],
            self.log_messages["attributeerror_partkey_submit"]["message"].format(app_id=app_id)
        )

    def log_urlerror_checking_partkey_pending(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["urlerror_checking_partkey_pending"]["level"],
            self.log_messages["urlerror_checking_partkey_pending"]["message"].format(app_id=app_id)
        )

    def log_partkey_generation_pending(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["partkey_generation_pending"]["level"],
            self.log_messages["partkey_generation_pending"]["message"].format(app_id=app_id)
        )

    def log_requested_partkey_generation(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["requested_partkey_generation"]["level"],
            self.log_messages["requested_partkey_generation"]["message"].format(app_id=app_id)
        )

    def log_partkey_generation_denied(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["partkey_generation_denied"]["level"],
            self.log_messages["partkey_generation_denied"]["message"].format(app_id=app_id)
        )

    def log_partkeys_not_confirmed(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["partkeys_not_confirmed"]["level"],
            self.log_messages["partkeys_not_confirmed"]["message"].format(app_id=app_id)
        )

    def log_attributeerror_partkeys_not_confirmed(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["attributeerror_partkeys_not_confirmed"]["level"],
            self.log_messages["attributeerror_partkeys_not_confirmed"]["message"].format(app_id=app_id)
        )

    def log_logicerror_partkeys_not_confirmed(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["logicerror_partkeys_not_confirmed"]["level"],
            self.log_messages["logicerror_partkeys_not_confirmed"]["message"].format(app_id=app_id)
        )

    def log_httperror_partkeys_not_confirmed(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["httperror_partkeys_not_confirmed"]["level"],
            self.log_messages["httperror_partkeys_not_confirmed"]["message"].format(app_id=app_id)
        )

    def log_delco_in_live_handler(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["delco_in_live_handler"]["level"],
            self.log_messages["delco_in_live_handler"]["message"].format(app_id=app_id)
        )

    def log_contract_expired(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["contract_expired"]["level"],
            self.log_messages["contract_expired"]["message"].format(app_id=app_id)
        )

    def log_expired_attribute_error(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["expired_attribute_error"]["level"],
            self.log_messages["expired_attribute_error"]["message"].format(app_id=app_id)
        )

    def log_tried_contract_expired(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["tried_contract_expired"]["level"],
            self.log_messages["tried_contract_expired"]["message"].format(app_id=app_id)
        )

    def log_httperror_contract_expired(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["httperror_contract_expired"]["level"],
            self.log_messages["httperror_contract_expired"]["message"].format(app_id=app_id)
        )

    def log_delco_expires_soon(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["delco_expires_soon"]["level"],
            self.log_messages["delco_expires_soon"]["message"].format(app_id=app_id)
        )

    def log_attributeerror_delco_expires_soon(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["attributeerror_delco_expires_soon"]["level"],
            self.log_messages["attributeerror_delco_expires_soon"]["message"].format(app_id=app_id)
        )

    def log_logicerror_delco_expires_soon(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["logicerror_delco_expires_soon"]["level"],
            self.log_messages["logicerror_delco_expires_soon"]["message"].format(app_id=app_id)
        )

    def log_httperror_delco_expires_soon(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["httperror_delco_expires_soon"]["level"],
            self.log_messages["httperror_delco_expires_soon"]["message"].format(app_id=app_id)
        )

    def log_gating_or_stake_limit_breached(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["gating_or_stake_limit_breached"]["level"],
            self.log_messages["gating_or_stake_limit_breached"]["message"].format(app_id=app_id)
        )

    def log_expired_attribute_error(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["expired_attribute_error"]["level"],
            self.log_messages["expired_attribute_error"]["message"].format(app_id=app_id)
        )

    def log_gating_or_stake_limit_breached(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["gating_or_stake_limit_breached"]["level"],
            self.log_messages["gating_or_stake_limit_breached"]["message"].format(app_id=app_id)
        )

    def log_gating_or_stake_limit_breached_attribute_error(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["gating_or_stake_limit_breached_attribute_error"]["level"],
            self.log_messages["gating_or_stake_limit_breached_attribute_error"]["message"].format(app_id=app_id)
        )

    def log_logicerror_gating_or_stake_limit_breached(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["logicerror_gating_or_stake_limit_breached"]["level"],
            self.log_messages["logicerror_gating_or_stake_limit_breached"]["message"].format(app_id=app_id)
        )

    def log_httperror_gating_or_stake_limit_breached(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["httperror_gating_or_stake_limit_breached"]["level"],
            self.log_messages["httperror_gating_or_stake_limit_breached"]["message"].format(app_id=app_id)
        )

    def log_delco_in_ended_handler(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["delco_in_ended_handler"]["level"],
            self.log_messages["delco_in_ended_handler"]["message"].format(app_id=app_id)
        )

    def log_scheduled_partkey_deletion_for_ended_or_deleted(
        self,
        app_id: int,
        scheduled_deletion: int,
        round_end: int
    ):
        self._log(
            self.log_messages["scheduled_partkey_deletion_for_ended_or_deleted"]["level"],
            self.log_messages["scheduled_partkey_deletion_for_ended_or_deleted"]["message"].format(
                app_id=app_id,
                scheduled_deletion=scheduled_deletion,
                round_end=round_end
            )
        )

    def log_no_partkeys_found_for_ended_or_deleted(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["no_partkeys_found_for_ended_or_deleted"]["level"],
            self.log_messages["no_partkeys_found_for_ended_or_deleted"]["message"].format(app_id=app_id)
        )

    def log_delco_in_deleted_handler(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["delco_in_deleted_handler"]["level"],
            self.log_messages["delco_in_deleted_handler"]["message"].format(app_id=app_id)
        )

    def log_num_of_valad_ids_found(
        self,
        num_of_valads: int
    ):
        self._log(
            self.log_messages["num_of_valad_ids_found"]["level"],
            self.log_messages["num_of_valad_ids_found"]["message"].format(num_of_valads=num_of_valads)
        )

    def log_num_of_valad_clients_connected(
        self,
        num_of_valads: int
    ):
        self._log(
            self.log_messages["num_of_valad_clients_connected"]["level"],
            self.log_messages["num_of_valad_clients_connected"]["message"].format(num_of_valads=num_of_valads)
        )

    def log_num_of_updated_valads(
        self,
        num_of_updated_valads:int,
        num_of_valads: int
    ):
        self._log(
            self.log_messages["num_of_updated_valads"]["level"],
            self.log_messages["num_of_updated_valads"]["message"].format(
                num_of_updated_valads=num_of_updated_valads, 
                num_of_valads=num_of_valads
            )
        )

    def log_zero_valad_clients(
        self,
        valad_id_list: list
    ):
        self._log(
            self.log_messages["zero_valad_clients"]["level"],
            self.log_messages["zero_valad_clients"]["message"].format(valad_id_list=valad_id_list)
        )

    def log_zero_valad_clients(
        self,
        valad_id_list: list
    ):
        self._log(
            self.log_messages["zero_valad_clients"]["level"],
            self.log_messages["zero_valad_clients"]["message"].format(valad_id_list=valad_id_list)
        )

    def log_num_of_connected_delcos(
        self,
        num_of_delcos: int
    ):
        self._log(
            self.log_messages["num_of_connected_delcos"]["level"],
            self.log_messages["num_of_connected_delcos"]["message"].format(num_of_delcos=num_of_delcos)
        )

    def log_num_of_delco_clients_connected(
        self,
        num_of_delcos: int
    ):
        self._log(
            self.log_messages["num_of_delco_clients_connected"]["level"],
            self.log_messages["num_of_delco_clients_connected"]["message"].format(num_of_delcos=num_of_delcos)
        )

    def log_num_of_updated_delcos(
        self,
        num_of_updated_delcos:int,
        num_of_delcos: int
    ):
        self._log(
            self.log_messages["num_of_updated_delcos"]["level"],
            self.log_messages["num_of_updated_delcos"]["message"].format(
                num_of_updated_delcos=num_of_updated_delcos, 
                num_of_delcos=num_of_delcos
            )
        )

    def log_algod_ok_continuing(
        self
    ):
        self._log(
            self.log_messages["algod_ok_continuing"]["level"],
            self.log_messages["algod_ok_continuing"]["message"]
        )

    def log_generic_contract_servicing_error(
        self,
        e: Exception
    ):
        self._log(
            self.log_messages["generic_contract_servicing_error"]["level"],
            self.log_messages["generic_contract_servicing_error"]["message"].format(e=e)
        )

    def log_generic_partkey_manager_error(
        self,
        e: Exception
    ):
        self._log(
            self.log_messages["generic_partkey_manager_error"]["level"],
            self.log_messages["generic_partkey_manager_error"]["message"].format(e=e)
        )

    def log_algod_error(
        self,
        msg: int
    ):
        self._log(
            self.log_messages["algod_error"]["level"],
            self.log_messages["algod_error"]["message"].format(msg=msg)
        )

    def log_single_loop_execution_time(
        self,
        duration_s: float
    ):
        self._log(
            self.log_messages["single_loop_execution_time"]["level"],
            self.log_messages["single_loop_execution_time"]["message"].format(duration_s=duration_s)
        )

    def log_targeted_sleep_duration(
        self,
        duration_s: float
    ):
        self._log(
            self.log_messages["targeted_sleep_duration"]["level"],
            self.log_messages["targeted_sleep_duration"]["message"].format(duration_s=duration_s)
        )

    def log_could_not_sleep(
        self,
        duration_s: float,
        e: Exception
    ):
        self._log(
            self.log_messages["could_not_sleep"]["level"],
            self.log_messages["could_not_sleep"]["message"].format(duration_s=duration_s, e=e)
        )

    def log_generic_claim_operational_fee_error(
        self,
        e: Exception
    ):
        self._log(
            self.log_messages["generic_claim_operational_fee_error"]["level"],
            self.log_messages["generic_claim_operational_fee_error"]["message"].format(e=e)
        )

    def log_attributeerror_claim_operational_fee(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["attributeerror_claim_operational_fee"]["level"],
            self.log_messages["attributeerror_claim_operational_fee"]["message"].format(app_id=app_id)
        )

    def log_unknownerror_claim_operational_fee(
        self,
        app_id: int,
        e: Exception
    ):
        self._log(
            self.log_messages["unknownerror_claim_operational_fee"]["level"],
            self.log_messages["unknownerror_claim_operational_fee"]["message"].format(app_id=app_id, e=e)
        )

    def log_calling_claim_operational_fee(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["calling_claim_operational_fee"]["level"],
            self.log_messages["calling_claim_operational_fee"]["message"].format(app_id=app_id)
        )

    def log_trying_to_claim_operational_fee(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["trying_to_claim_operational_fee"]["level"],
            self.log_messages["trying_to_claim_operational_fee"]["message"].format(app_id=app_id)
        )

    def log_successfully_claimed_operational_fee(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["successfully_claimed_operational_fee"]["level"],
            self.log_messages["successfully_claimed_operational_fee"]["message"].format(app_id=app_id)
        )

    def log_will_not_claim_operational_fee_of_not_live(
        self,
        app_id: int
    ):
        self._log(
            self.log_messages["will_not_claim_operational_fee_of_not_live"]["level"],
            self.log_messages["will_not_claim_operational_fee_of_not_live"]["message"].format(app_id=app_id)
        )


    ############################################################################
    ### AppWrapper #############################################################
    ############################################################################

    def log_app_create_urlerror(
        self,
        app_id: int,
        errno: int,
        strerror=str
    ):
        self._log(
            self.log_messages["app_create_urlerror"]["level"],
            self.log_messages["app_create_urlerror"]["message"].format(
                app_id=app_id,
                errno=errno,
                strerror=strerror
            )
        )

    def log_app_create_algohttperror(
        self,
        app_id: int,
        errno: int,
        strerror=str
    ):
        self._log(
            self.log_messages["app_create_algohttperror"]["level"],
            self.log_messages["app_create_algohttperror"]["message"].format(
                app_id=app_id,
                errno=errno,
                strerror=strerror
            )
        )

    def log_app_create_genericerror(
        self,
        app_id: float,
        e: Exception
    ):
        self._log(
            self.log_messages["app_create_genericerror"]["level"],
            self.log_messages["app_create_genericerror"]["message"].format(app_id=app_id, e=e)
        )

    def log_app_dynamic_update_genericerror(
        self,
        app_id: float,
        e: Exception
    ):
        self._log(
            self.log_messages["app_dynamic_update_genericerror"]["level"],
            self.log_messages["app_dynamic_update_genericerror"]["message"].format(app_id=app_id, e=e)
        )

    ############################################################################
    ### Partkeymanager #########################################################
    ############################################################################
    
    def log_partkey_generation_request(
        self,
        address: str,
        vote_first_valid: int,
        vote_last_valid: int
    ):
        self._log(
            self.log_messages["partkey_generation_request"]["level"],
            self.log_messages["partkey_generation_request"]["message"].format(
                address=address,
                vote_first_valid=vote_first_valid,
                vote_last_valid=vote_last_valid
            )
        )
    
    def log_generating_partkeys(
        self,
        address: str,
        vote_first_valid: int,
        vote_last_valid: int
    ):
        self._log(
            self.log_messages["generating_partkeys"]["level"],
            self.log_messages["generating_partkeys"]["message"].format(
                address=address,
                vote_first_valid=vote_first_valid,
                vote_last_valid=vote_last_valid
            )
        )

    def log_requested_partkey_in_past(
        self,
        num_of_keys: int
    ):
        self._log(
            self.log_messages["requested_partkey_in_past"]["level"],
            self.log_messages["requested_partkey_in_past"]["message"].format(num_of_keys=num_of_keys)
        )

    def log_pending_buffer_is_full(
        self,
        num_of_keys: int
    ):
        self._log(
            self.log_messages["pending_buffer_is_full"]["level"],
            self.log_messages["pending_buffer_is_full"]["message"].format(num_of_keys=num_of_keys)
        )

    def log_generated_buffer_is_full(
        self,
        num_of_keys: int
    ):
        self._log(
            self.log_messages["generated_buffer_is_full"]["level"],
            self.log_messages["generated_buffer_is_full"]["message"].format(num_of_keys=num_of_keys)
        )

    def log_requested_partkey_in_pending(
        self
    ):
        self._log(
            self.log_messages["requested_partkey_in_pending"]["level"],
            self.log_messages["requested_partkey_in_pending"]["message"]
        )

    def log_requested_partkey_in_generated(
        self
    ):
        self._log(
            self.log_messages["requested_partkey_in_generated"]["level"],
            self.log_messages["requested_partkey_in_generated"]["message"]
        )

    def log_partkey_generation_request_added(
        self
    ):
        self._log(
            self.log_messages["partkey_generation_request_added"]["level"],
            self.log_messages["partkey_generation_request_added"]["message"]
        )

    def log_generic_algod_error(
        self,
        e: Exception
    ):
        self._log(
            self.log_messages["generic_algod_error"]["level"],
            self.log_messages["generic_algod_error"]["message"].format(e=e)
        )
