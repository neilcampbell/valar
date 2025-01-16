
from typing import Literal

from smart_contracts.artifacts.validator_ad.client import ValidatorAdClient  # noqa: F401
from smart_contracts.validator_ad.constants import (  # noqa: F401
    STATE_CREATED,
    STATE_NOT_LIVE,
    STATE_NOT_READY,
    STATE_READY,
    STATE_SET,
    STATE_TEMPLATE_LOAD,
    STATE_TEMPLATE_LOADED,
)
from tests.validator_ad.client_helper import ValidatorAdGlobalState  # noqa: F401
from tests.validator_ad.utils import ValidatorAd  # noqa: F401

POSSIBLE_STATES = Literal[
    "START",
    "CREATED",
    "SET",
    "READY",
    "NOT_READY",
    "NOT_LIVE",
]
