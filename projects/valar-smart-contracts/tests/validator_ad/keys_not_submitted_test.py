
import pytest
from algokit_utils import LogicError
from algokit_utils.beta.account_manager import AddressAndSigner

import tests.validator_ad.delegator_contract_interface as dc
from smart_contracts.artifacts.validator_ad.client import Message
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_CALLED_BY_NOT_CREATOR,
    ERROR_DELEGATOR_DOES_NOT_EXIST_AT_VALIDATOR_AD,
    MSG_CORE_KEYS_NOT_SUBMITTED,
)
from tests.constants import ERROR_GLOBAL_STATE_MISMATCH, SKIP_SAME_AS_FOR_ALGO
from tests.utils import calc_earnings, is_expected_logic_error
from tests.validator_ad.client_helper import ValidatorASA
from tests.validator_ad.utils import ValidatorAd

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "READY"
TEST_DELEGATOR_INITIAL_STATE = "READY"
TEST_ACTION_NAME = "keys_not_submitted"

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

    gs_del_new = validator_ad.get_delegator_global_state(app_id)

    # Check return
    assert res.return_value == Message(
        del_manager=gs_del_new.del_manager,
        msg=list(MSG_CORE_KEYS_NOT_SUBMITTED),
    )

    # Check contract state
    gs_exp = gs_start
    gs_exp.cnt_del = 0
    gs_exp.del_app_list[0] = 0
    expected_earnings = calc_earnings(
        amount=0,
        commission=action_inputs.terms_price.commission,
    )
    if asset == ALGO_ASA_ID:
        gs_exp.total_algo_earned = expected_earnings[0]
        gs_exp.total_algo_fees_generated = expected_earnings[1]
    else:
        assert validator_ad.app_asa_box(asset) == ValidatorASA(
            total_earning=expected_earnings[0],
            total_fees_generated=expected_earnings[1],
        )
    assert validator_ad.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check delegator contract state
    assert gs_del_new.state == dc.STATE_ENDED_NOT_SUBMITTED

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
