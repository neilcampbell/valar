
# ------- Definition of constants -------
"""
Possible states of the contract:
    CREATED - contract has been created.
    LIVE - contract is live.
    READY - waiting for keys submission.
    SET - contract terms have been set.
    SUBMITTED - waiting for keys confirmation.
    ENDED_NOT_SUBMITTED - keys have not been submitted in time.
    ENDED_NOT_CONFIRMED - keys have not been confirmed in time.
    ENDED_LIMITS - maximum number of limit breach events has been reached.
    ENDED_WITHDREW - delegator withdrew from the contract prematurely.
    ENDED_EXPIRED - contract has expired.
    ENDED_SUSPENDED - delegator has been suspended by consensus.
    ENDED_CANNOT_PAY - delegator cannot pay the validator (as funds could have been frozen and/or clawed back).
"""
STATE_NONE = b"\x00"
STATE_CREATED = b"\x01"
STATE_SET = b"\x02"
STATE_READY = b"\x03"
STATE_SUBMITTED = b"\x04"
STATE_LIVE = b"\x05"
STATE_ENDED_NOT_SUBMITTED = b"\x10"
STATE_ENDED_NOT_CONFIRMED = b"\x11"
STATE_ENDED_LIMITS = b"\x12"
STATE_ENDED_WITHDREW = b"\x13"
STATE_ENDED_EXPIRED = b"\x14"
STATE_ENDED_SUSPENDED = b"\x15"
STATE_ENDED_CANNOT_PAY = b"\x16"
STATE_ENDED_MASK = b"\x10"
