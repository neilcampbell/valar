
import base64

import pytest
from algokit_utils.logic_error import LogicError
from algosdk.logic import get_application_address

import tests.validator_ad.delegator_contract_interface as dc
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_APP_NOT_WITH_USER,
    ERROR_USER_DOES_NOT_EXIST,
    MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD,
    MBR_ACCOUNT,
    MSG_CORE_KEYS_NOT_SUBMITTED,
)
from tests.constants import (
    ERROR_GLOBAL_STATE_MISMATCH,
    SKIP_SAME_AS_FOR_ALGO,
)
from tests.noticeboard.utils import Noticeboard
from tests.utils import available_balance, calc_operational_fee, is_expected_logic_error

from .config import ActionInputs

# ------- Test constants -------
TEST_NB_STATE = "SET"
TEST_VA_STATE = "READY"
TEST_DC_STATE = "READY"
TEST_ACTION_NAME = "keys_not_submitted"

# ------- Tests -------
def test_action(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    del_app_id = noticeboard.initialize_delegator_contract_state(
        action_inputs=action_inputs,
        val_app_id=val_app_id,
        target_state=TEST_DC_STATE,
    )

    gs_start = noticeboard.get_global_state()
    gs_val_start = noticeboard.get_validator_ad_global_state(val_app_id)
    gs_del_start = noticeboard.get_delegator_global_state(del_app_id)

    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)
    bal_start_asset = noticeboard.app_available_balance(asset)
    bal_val_start = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=get_application_address(val_app_id),
        asset_id=asset,
    )
    bal_del_start = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=get_application_address(del_app_id),
        asset_id=asset,
    )
    del_manager_bal_start = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=noticeboard.del_managers[0].address,
        asset_id=asset,
    )

    del_user = noticeboard.del_managers[0].address
    del_user_info_start = noticeboard.app_get_user_info(del_user)

    val_user = noticeboard.val_owners[0].address
    val_user_info_start = noticeboard.app_get_user_info(val_user)

    # Action
    res = noticeboard.delegator_action(
        app_id=del_app_id,
        action_name=TEST_ACTION_NAME,
        action_inputs=action_inputs,
        val_app=val_app_id,
        action_account=noticeboard.dispenser,  # A 3rd party reports the keys haven't been submitted
    )

    # Check return
    assert res.confirmed_round

    # Check notification message was sent
    assert base64.b64decode(res.tx_info["inner-txns"][-1]["txn"]["txn"]["note"]) == MSG_CORE_KEYS_NOT_SUBMITTED

    # Check contract state
    gs_end = noticeboard.get_global_state()
    gs_exp = gs_start
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check balances
    bal_end = noticeboard.app_available_balance(ALGO_ASA_ID)
    bal_end_asset = noticeboard.app_available_balance(asset)
    bal_val_end = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=get_application_address(val_app_id),
        asset_id=asset,
    )
    bal_del_end = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=get_application_address(del_app_id),
        asset_id=asset,
    )
    del_manager_bal_end = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=noticeboard.del_managers[0].address,
        asset_id=asset,
    )

    returned_amount = gs_del_start.delegation_terms_general.fee_setup + \
        calc_operational_fee(
            gs_del_start.delegation_terms_general.fee_round,
            gs_del_start.round_end,
            gs_del_start.round_start,
        )

    if asset != ALGO_ASA_ID:
        assert bal_end_asset == bal_start_asset
        assert bal_del_end == bal_del_start - returned_amount
    else:
        assert bal_del_end == MBR_ACCOUNT
    assert bal_end == bal_start
    assert bal_val_end == bal_val_start

    assert del_manager_bal_end == del_manager_bal_start + returned_amount

    # Check created delegator contract state
    gs_del_end = noticeboard.get_delegator_global_state(del_app_id)
    gs_del_exp = gs_del_start
    gs_del_exp.state = dc.STATE_ENDED_NOT_SUBMITTED
    gs_del_exp.round_ended = res.confirmed_round
    assert gs_del_end == gs_del_exp

    # Check validator ad state
    gs_val_end = noticeboard.get_validator_ad_global_state(val_app_id)
    gs_val_exp = gs_val_start
    gs_val_exp.cnt_del = 0
    gs_val_exp.del_app_list = [0]*MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD
    assert gs_val_end == gs_val_exp

    # Check delegator user
    del_user_info = noticeboard.app_get_user_info(del_user)
    del_user_info_exp = del_user_info_start
    assert del_user_info == del_user_info_exp

    # Check validator user
    val_user_info = noticeboard.app_get_user_info(val_user)
    val_user_info_exp = val_user_info_start
    assert val_user_info == val_user_info_exp

    return

def test_del_manager_does_not_exist(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    del_app_id = noticeboard.initialize_delegator_contract_state(
        action_inputs=action_inputs,
        val_app_id=val_app_id,
        target_state=TEST_DC_STATE,
    )

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.del_manager = noticeboard.dispenser.address
        noticeboard.delegator_action(
            app_id=del_app_id,
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            val_app=val_app_id,
        )
    assert is_expected_logic_error(ERROR_USER_DOES_NOT_EXIST, e)

    return

def test_val_owner_does_not_exist(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    del_app_id = noticeboard.initialize_delegator_contract_state(
        action_inputs=action_inputs,
        val_app_id=val_app_id,
        target_state=TEST_DC_STATE,
    )

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.val_owner = noticeboard.dispenser.address
        noticeboard.delegator_action(
            app_id=del_app_id,
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            val_app=val_app_id,
        )
    assert is_expected_logic_error(ERROR_USER_DOES_NOT_EXIST, e)

    return

def test_wrong_indices(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    del_app_id = noticeboard.initialize_delegator_contract_state(
        action_inputs=action_inputs,
        val_app_id=val_app_id,
        target_state=TEST_DC_STATE,
    )

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.del_app_idx = 99
        noticeboard.delegator_action(
            app_id=del_app_id,
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            val_app=val_app_id,
        )

    assert is_expected_logic_error(ERROR_APP_NOT_WITH_USER, e)
    action_inputs.del_app_idx = None  # Reset

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.val_app_idx = 77
        noticeboard.delegator_action(
            app_id=del_app_id,
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            val_app=val_app_id,
        )

    assert is_expected_logic_error(ERROR_APP_NOT_WITH_USER, e)


    return

def test_action_w_partner(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    # Setup
    partner_address = noticeboard.partners[0].address
    action_inputs = ActionInputs(asset=asset, partner_address=partner_address)
    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    del_app_id = noticeboard.initialize_delegator_contract_state(
        action_inputs=action_inputs,
        val_app_id=val_app_id,
        target_state=TEST_DC_STATE,
    )

    bal_par_start = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=partner_address,
        asset_id=asset,
    )

    # Action
    res = noticeboard.delegator_action(
        app_id=del_app_id,
        action_name=TEST_ACTION_NAME,
        action_inputs=action_inputs,
        val_app=val_app_id,
        action_account=noticeboard.dispenser,  # A 3rd party reports the keys haven't been submitted
    )

    # Check return
    assert res.confirmed_round

    # Check balance of partner
    bal_par_end = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=partner_address,
        asset_id=asset,
    )
    # Nothing should have been earned
    assert bal_par_end == bal_par_start

    return
