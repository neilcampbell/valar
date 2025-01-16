
from typing import Literal

from smart_contracts.artifacts.delegator_contract.client import DelegatorContractClient  # noqa: F401
from smart_contracts.delegator_contract.constants import (  # noqa: F401
    STATE_CREATED,
    STATE_ENDED_CANNOT_PAY,
    STATE_ENDED_EXPIRED,
    STATE_ENDED_LIMITS,
    STATE_ENDED_MASK,
    STATE_ENDED_NOT_CONFIRMED,
    STATE_ENDED_NOT_SUBMITTED,
    STATE_ENDED_SUSPENDED,
    STATE_ENDED_WITHDREW,
    STATE_LIVE,
    STATE_READY,
    STATE_SET,
    STATE_SUBMITTED,
)
from tests.delegator_contract.client_helper import DelegatorContractGlobalState  # noqa: F401
from tests.delegator_contract.utils import DelegatorContract  # noqa: F401

POSSIBLE_STATES = Literal[
    "START",
    "READY",
    "SUBMITTED",
    "ENDED_CANNOT_PAY",
    "ENDED_EXPIRED",
    "ENDED_LIMITS",
    "ENDED_NOT_CONFIRMED",
    "ENDED_NOT_SUBMITTED",
    "ENDED_SUSPENDED",
    "ENDED_WITHDREW",
    "LIVE",
]

EXTENDED_POSSIBLE_STATES_WITH_VIA = Literal[
    "ENDED_CANNOT_PAY_VIA_READY",
    "ENDED_CANNOT_PAY_VIA_LIVE",
    "DELETED_VIA_ENDED_EXPIRED",
    "DELETED_VIA_ENDED_LIMITS",
    "DELETED_VIA_ENDED_NOT_CONFIRMED",
    "DELETED_VIA_ENDED_NOT_SUBMITTED",
    "DELETED_VIA_ENDED_SUSPENDED",
    "DELETED_VIA_ENDED_WITHDREW",
    "DELETED_VIA_ENDED_CANNOT_PAY_VIA_READY",
    "DELETED_VIA_ENDED_CANNOT_PAY_VIA_LIVE",
]
