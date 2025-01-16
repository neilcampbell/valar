
import pytest
from algokit_utils import LogicError
from algokit_utils.beta.account_manager import AddressAndSigner

import tests.validator_ad.delegator_contract_interface as dc
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_CALLED_BY_NOT_CREATOR,
    ERROR_DELEGATOR_DOES_NOT_EXIST_AT_VALIDATOR_AD,
)
from tests.constants import ERROR_GLOBAL_STATE_MISMATCH, SKIP_SAME_AS_FOR_ALGO
from tests.utils import is_expected_logic_error
from tests.validator_ad.utils import ValidatorAd

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "READY"
TEST_DELEGATOR_INITIAL_STATE = "SUBMITTED"
TEST_ACTION_NAME = "keys_confirm"

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
    gs_start = validator_ad.get_global_state()

    # Action succeeds
    res = validator_ad.delegator_action(
        app_id=app_id,
        action_name=TEST_ACTION_NAME,
        action_inputs=action_inputs,
    )

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    assert validator_ad.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check delegator contract state
    gs_del_new = validator_ad.get_delegator_global_state(app_id)
    assert gs_del_new.state == dc.STATE_LIVE

    return

def test_wrong_app(
    validator_ad : ValidatorAd,
    validator_ad_2 : ValidatorAd,
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
    validator_ad_2.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    app_id_1 = validator_ad.initialize_delegator_state(  # noqa: F841
        action_inputs=action_inputs,
        target_state=TEST_DELEGATOR_INITIAL_STATE,
    )
    app_id_2 = validator_ad_2.initialize_delegator_state(
        action_inputs=action_inputs,
        target_state=TEST_DELEGATOR_INITIAL_STATE,
    )

    # Action fail
    with pytest.raises(LogicError) as e:
        validator_ad.delegator_action(
            app_id=app_id_2,
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
        )
    assert is_expected_logic_error(ERROR_DELEGATOR_DOES_NOT_EXIST_AT_VALIDATOR_AD, e)

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
