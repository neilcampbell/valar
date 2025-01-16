

import pytest
from algokit_utils import LogicError
from algokit_utils.beta.account_manager import AddressAndSigner

import tests.validator_ad.delegator_contract_interface as dc
from smart_contracts.artifacts.validator_ad.client import Message
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_CALLED_BY_NOT_CREATOR,
    ERROR_DELEGATOR_DOES_NOT_EXIST_AT_VALIDATOR_AD,
    MSG_CORE_CONTRACT_EXPIRED,
)
from tests.constants import ERROR_GLOBAL_STATE_MISMATCH, SKIP_SAME_AS_FOR_ALGO
from tests.utils import calc_earnings, calc_operational_fee, is_expected_logic_error
from tests.validator_ad.client_helper import ValidatorASA
from tests.validator_ad.utils import ValidatorAd

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "READY"
TEST_DELEGATOR_INITIAL_STATE = "LIVE"
TEST_ACTION_NAME = "contract_expired"

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
    gs_del_new = validator_ad.get_delegator_global_state(app_id)
    amount = calc_operational_fee(
        gs_del_new.delegation_terms_general.fee_round,
        res.confirmed_round,
        gs_del_new.round_start,
    )
    validator_earns, platforms_earns = calc_earnings(
       amount=amount,
       commission=gs_del_new.delegation_terms_general.commission,
    )

    assert res.return_value == Message(
        del_manager=gs_del_new.del_manager,
        msg=list(MSG_CORE_CONTRACT_EXPIRED),
    )

    # Check contract state
    gs_exp = gs_start
    gs_exp.cnt_del = 0
    gs_exp.del_app_list[0] = 0
    setup_earnings = calc_earnings(
        amount=gs_del_new.delegation_terms_general.fee_setup,
        commission=gs_del_new.delegation_terms_general.commission,
    )
    expected_total_earnings = (
        setup_earnings[0] + validator_earns,
        setup_earnings[1] + platforms_earns,
    )
    if asset == ALGO_ASA_ID:
        gs_exp.total_algo_earned = expected_total_earnings[0]
        gs_exp.total_algo_fees_generated = expected_total_earnings[1]
    else:
        assert validator_ad.app_asa_box(asset) == ValidatorASA(
            total_earning=expected_total_earnings[0],
            total_fees_generated=expected_total_earnings[1],
        )
    gs_new = validator_ad.get_global_state()
    assert gs_new == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check delegator contract state
    assert gs_del_new.state == dc.STATE_ENDED_EXPIRED

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
