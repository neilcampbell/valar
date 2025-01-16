
# ------- Definition of constants -------
"""
Possible states of the contract:
    CREATED - validator ad has been created.
    TEMPLATE_LOAD - validator ad is getting loaded the delegator contract template.
    TEMPLATE_LOADED - validator ad ended loading of the delegator contract template.
    SET - initial terms of validator ad have been set.
    READY - validator ad manager is ready to accept new delegators.
    NOT_READY - validator ad manager is not ready to accept new delegators.
    NOT_LIVE - validator ad owner does not want to accept new delegators.
"""
STATE_NONE = b"\x00"
STATE_CREATED = b"\x01"
STATE_TEMPLATE_LOAD = b"\x02"
STATE_TEMPLATE_LOADED = b"\x03"
STATE_SET = b"\x04"
STATE_READY = b"\x05"
STATE_NOT_READY = b"\x06"
STATE_NOT_LIVE = b"\x07"
