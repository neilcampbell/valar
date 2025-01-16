


import pytest

from smart_contracts.helpers.constants import ALGO_ASA_ID
from tests.constants import SKIP_NOT_APPLICABLE_TO_ALGO
from tests.validator_ad.config import ActionInputs
from tests.validator_ad.utils import ValidatorAd

# ------- Test constants -------
TEST_INITIAL_STATE = "READY"
TEST_DELEGATOR_INITIAL_STATE = "LIVE"
TEST_ACTION_NAME = "get_validator_asa"

# ------- Tests -------
def test_action(
    validator_ad: ValidatorAd,
    asset : int,
) -> None:

    pytest.skip(SKIP_NOT_APPLICABLE_TO_ALGO) if asset == ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    app_id = validator_ad.initialize_delegator_state(
        action_inputs=action_inputs,
        target_state=TEST_DELEGATOR_INITIAL_STATE,
    )
    # Add expiry to test returning of non-zero values
    validator_ad.delegator_action(
        app_id=app_id,
        action_name="contract_expired",
        action_inputs=action_inputs,
    )

    # Action
    res = validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return of validator asa matches its box contents
    asa_info = validator_ad.app_asa_box(asset)
    assert vars(res.return_value) == vars(asa_info)

    return
