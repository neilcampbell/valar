

import pytest
from algokit_utils import LogicError
from algokit_utils.beta.account_manager import AddressAndSigner

from smart_contracts.artifacts.validator_ad.client import Message
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_CALLED_BY_NOT_CREATOR,
    MSG_CORE_WILL_EXPIRE,
)
from tests.constants import SKIP_SAME_AS_FOR_ALGO
from tests.utils import is_expected_logic_error
from tests.validator_ad.utils import ValidatorAd

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "READY"
TEST_DELEGATOR_INITIAL_STATE = "LIVE"
TEST_ACTION_NAME = "contract_report_expiry_soon"

# ------- Tests -------
def test_action(
    validator_ad: ValidatorAd,
    asset : int,
    val_owner : AddressAndSigner,
    val_manager : AddressAndSigner,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    action_inputs.val_owner = val_owner.address
    action_inputs.val_manager = val_manager.address
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    app_id = validator_ad.initialize_delegator_state(
        action_inputs=action_inputs,
        target_state=TEST_DELEGATOR_INITIAL_STATE,
    )
    gs_del_start = validator_ad.get_delegator_global_state(app_id)

    action_inputs.wait_expiry_report = True # To be explicit

    # Action succeeds
    res = validator_ad.delegator_action(
        app_id=app_id,
        action_name=TEST_ACTION_NAME,
        action_inputs=action_inputs,
    )

    # Check return
    assert res.return_value == Message(
        del_manager=gs_del_start.del_manager,
        msg=list(MSG_CORE_WILL_EXPIRE),
    )

    return

def test_wrong_caller(
    validator_ad: ValidatorAd,
    dispenser : AddressAndSigner,
    val_owner : AddressAndSigner,
    val_manager : AddressAndSigner,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    action_inputs.val_owner = val_owner.address
    action_inputs.val_manager = val_manager.address
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    app_id = validator_ad.initialize_delegator_state(
        action_inputs=action_inputs,
        target_state=TEST_DELEGATOR_INITIAL_STATE,
    )

    # Action fail
    with pytest.raises(LogicError) as e:
        validator_ad.acc = dispenser
        validator_ad.delegator_action(
            app_id=app_id,
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
        )
    assert is_expected_logic_error(ERROR_CALLED_BY_NOT_CREATOR, e)

    return
