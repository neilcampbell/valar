
# ------- Definition of constants -------
"""
Possible states of the contract:
    DEPLOYED - noticeboard contract has been deployed.
    SET - noticeboard has been set.
    SUSPENDED - noticeboard has been temporarily suspended. No new ads or contracts can be opened or users registered.
    RETIRED - noticeboard has been permanently retired. No new ads or contracts can be opened or users registered.
"""
STATE_NONE = b"\x00"
STATE_DEPLOYED = b"\x01"
STATE_SET = b"\x02"
STATE_SUSPENDED = b"\x03"
STATE_RETIRED = b"\x04"

"""
Possible user roles (i.e. prefix for user's box at Noticeboard):
    ROLE_VAL - user is a validator.
    ROLE_DEL - user is a delegator.
"""
ROLE_VAL = b"val_"
ROLE_DEL = b"del_"
