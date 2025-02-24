"""Various constants.
"""

### Daemon-specific

"""
Delegator contract ready sub-state constants, indicating:

NOT_SUBMITTED   - Time for submitting the partkeys according to the validator ad's terms is up.
REQUEST_DENIED  - Requesting partkey generation was not succesfull.
BREACH_LIMITS   - Limits breached.
BREACH_PAY      - Payment breached.
UNKNOWN_ERROR   - An unknown error occurred while submitting partkeys.
URL_ERROR       - A known URL error (no. 111 or -2) occurred while submitting partkeys.
REQUESTED       - Partkey generation was requested.
PENDING         - Partkey generation is pending.
SUBMITTED       - Partkeys were submitted and may update the contract state.
"""
DELCO_READY_STATUS_NOT_SUBMITTED    = -6
DELCO_READY_STATUS_REQUEST_DENIED   = -5
DELCO_READY_STATUS_BREACH_LIMITS    = -4
DELCO_READY_STATUS_BREACH_PAY       = -3
DELCO_READY_STATUS_UNKNOWN_ERROR    = -2
DELCO_READY_STATUS_URL_ERROR        = -1
DELCO_READY_STATUS_REQUESTED        =  0
DELCO_READY_STATUS_PENDING          =  1
DELCO_READY_STATUS_SUBMITTED        =  2

"""
Delegator contract live sub-state constants, indicating:

EXPIRED         - Contract has expired.
EXPIRES_SOON    - Contract is expiring soon.
BREACH_LIMITS   - Limits breached.
BREACH_PAY      - Payment breached.
NO_CHANGE       - Nothing to do, all good.
"""
DELCO_LIVE_STATUS_EXPIRED           = -4
DELCO_LIVE_STATUS_EXPIRES_SOON      = -3
DELCO_LIVE_STATUS_BREACH_LIMITS     = -2
DELCO_LIVE_STATUS_BREACH_PAY        = -1
DELCO_LIVE_STATUS_NO_CHANGE         =  0

"""
Validator ad not ready sub-state constants, indicating:

VALAD_NOT_READY_STATUS_NO_CHANGE        - No change needed, no error recorded.
VALAD_NOT_READY_STATUS_CHANGE_OK        - Switch from not ready to ready successful.
VALAD_NOT_READY_STATUS_ATTRIBUTE_ERROR  - AttributeError during switch, likely due to broken algod connection.
"""
VALAD_NOT_READY_STATUS_NO_CHANGE =           1
VALAD_NOT_READY_STATUS_CHANGE_OK =           0
VALAD_NOT_READY_STATUS_ATTRIBUTE_ERROR =    -1


"""
Claim validator earnings (and platform/partner commission) indicator:

CLAIM_OPERATIONAL_FEE_ERROR        - An error was encountered (e.g., Algod offline).
CLAIM_OPERATIONAL_FEE_SUCCESS      - Claimed successfully.
CLAIM_OPERATIONAL_FEE_NOT_LIVE     - Delegator contract is not live - will not try to claim.
"""
CLAIM_OPERATIONAL_FEE_ERROR =      -1
CLAIM_OPERATIONAL_FEE_SUCCESS =     0
CLAIM_OPERATIONAL_FEE_NOT_LIVE =    1

### From the smart contracts

ZERO_ADDRESS = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ"
"""str: algorand encoded address of 32 zero bytes"""

ROLE_VAL = b"val_"
ROLE_DEL = b"del_"
"""
Possible user roles (i.e. prefix for user's box at Noticeboard):
    ROLE_VAL - user is a validator.
    ROLE_DEL - user is a delegator.
"""

BOX_ASA_KEY_PREFIX = b"asa_"
"""
BOX_ASA_KEY_PREFIX : bytes
    Prefix for the boxes of ASA at ValidatorAd.
"""

ALGO_ASA_ID = 0
"""ID of Algo ASA."""

"""
Possible states of the contract:
    CREATED - validator ad has been created.
    TEMPLATE_LOAD - validator ad is getting loaded the delegator contract template.
    TEMPLATE_LOADED - validator ad ended loading of the delegator contract template.
    SET - initial terms of validator ad have been set.
    READY - validator ad manager is ready to accept new delegators.
    NOT_READY - validator ad manager is not ready to accept new delegators.
    NOT_LIVE - validator ad owner does not want to accept new delegators.
    DELETED - fetching the state of a connected client raises a 'non-existent' error.
"""
VALAD_STATE_NONE = b"\x00"
VALAD_STATE_CREATED = b"\x01"
VALAD_STATE_TEMPLATE_LOAD = b"\x02"
VALAD_STATE_TEMPLATE_LOADED = b"\x03"
VALAD_STATE_SET = b"\x04"
VALAD_STATE_READY = b"\x05"
VALAD_STATE_NOT_READY = b"\x06"
VALAD_STATE_NOT_LIVE = b"\x07"
VALAD_STATE_DELETED_MASK = b"\x20"

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
    ENDED_UPTIME - validator has breach the agreed uptime guarantee.
    ENDED_CANNOT_PAY - delegator cannot pay the validator (as funds could have been frozen and/or clawed back).
    DELETED - fetching the state of a connected client raises a 'non-existent' error.
"""
DELCO_STATE_NONE = b"\x00"
DELCO_STATE_CREATED = b"\x01"
DELCO_STATE_SET = b"\x02"
DELCO_STATE_READY = b"\x03"
DELCO_STATE_SUBMITTED = b"\x04"
DELCO_STATE_LIVE = b"\x05"
DELCO_STATE_ENDED_NOT_SUBMITTED = b"\x10"
DELCO_STATE_ENDED_NOT_CONFIRMED = b"\x11"
DELCO_STATE_ENDED_LIMITS = b"\x12"
DELCO_STATE_ENDED_WITHDREW = b"\x13"
DELCO_STATE_ENDED_EXPIRED = b"\x14"
DELCO_STATE_ENDED_UPTIME = b"\x15"
DELCO_STATE_ENDED_CANNOT_PAY = b"\x16"
DELCO_STATE_ENDED_MASK = b"\x10"
DELCO_STATE_DELETED_MASK = b"\x20"
