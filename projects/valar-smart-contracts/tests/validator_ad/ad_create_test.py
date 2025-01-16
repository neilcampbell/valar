
from smart_contracts.validator_ad.constants import (
    STATE_CREATED,
)
from tests.constants import ERROR_GLOBAL_STATE_MISMATCH
from tests.validator_ad.utils import ValidatorAd

from .client_helper import ValidatorAdGlobalState
from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = None
TEST_ACTION_NAME = "ad_create"

# ------- Tests -------
def test_action(
    validator_ad: ValidatorAd,
) -> None:

    # Setup
    action_inputs = ActionInputs()

    # Action
    res = validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.return_value != 0, "App was not created."

    # Check contract state
    gs_exp = ValidatorAdGlobalState(
        val_owner = action_inputs.val_owner,
        state = STATE_CREATED,
    )
    assert validator_ad.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    return
