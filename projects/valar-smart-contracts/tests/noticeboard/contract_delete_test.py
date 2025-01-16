
import pytest
from algokit_utils.logic_error import LogicError

from smart_contracts.artifacts.noticeboard.client import ContractDeleteReturn
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_APP_NOT_WITH_USER,
    ERROR_USER_DOES_NOT_EXIST,
    MBR_ACCOUNT,
)
from tests.constants import (
    ERROR_GLOBAL_STATE_MISMATCH,
    SKIP_SAME_AS_FOR_ALGO,
)
from tests.noticeboard.utils import Noticeboard
from tests.utils import calc_operational_fee, is_deleted, is_expected_logic_error

from .config import ActionInputs

# ------- Test constants -------
TEST_NB_STATE = "SET"
TEST_VA_STATE = "READY"
TEST_DC_STATE = "ENDED_EXPIRED"
TEST_ACTION_NAME = "contract_delete"

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

    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)
    bal_start_asset = noticeboard.app_available_balance(asset)

    del_user = noticeboard.del_managers[0].address
    del_user_info_start = noticeboard.app_get_user_info(del_user)

    # Action
    res = noticeboard.delegator_action(
        app_id=del_app_id,
        action_name=TEST_ACTION_NAME,
        action_inputs=action_inputs,
        val_app=val_app_id,
    )

    # Check return
    assert res.confirmed_round

    assert res.return_value == ContractDeleteReturn(
        remaining_balance=MBR_ACCOUNT if asset == ALGO_ASA_ID else 0,
        asset_id=asset,
    )

    # Check contract state
    gs_end = noticeboard.get_global_state()
    gs_exp = gs_start
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check balances
    bal_end = noticeboard.app_available_balance(ALGO_ASA_ID)
    bal_end_asset = noticeboard.app_available_balance(asset)
    if asset != ALGO_ASA_ID:
        assert bal_end == bal_start
        assert bal_end_asset == bal_start_asset
    else:
        assert bal_end == bal_start

    # Check delegator contract was deleted
    assert is_deleted(noticeboard.algorand_client, del_app_id)

    # Delegator user gets the app deleted from its list
    del_user_info = noticeboard.app_get_user_info(del_user)
    del_user_info_exp = del_user_info_start
    del_user_info_exp.cnt_app_ids = 0
    del_user_info_exp.app_ids = [0] * len(del_user_info_start.app_ids)
    assert del_user_info == del_user_info_exp

    return

def test_action_after_withdrew(
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
        target_state="ENDED_WITHDREW",
    )

    gs_start = noticeboard.get_global_state()
    gs_del_start = noticeboard.get_delegator_global_state(del_app_id)

    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)
    bal_start_asset = noticeboard.app_available_balance(asset)

    del_user = noticeboard.del_managers[0].address
    del_user_info_start = noticeboard.app_get_user_info(del_user)

    # Action
    res = noticeboard.delegator_action(
        app_id=del_app_id,
        action_name=TEST_ACTION_NAME,
        action_inputs=action_inputs,
        val_app=val_app_id,
    )

    # Check return
    assert res.confirmed_round

    unpaid = calc_operational_fee(
        gs_del_start.delegation_terms_general.fee_round,
        gs_del_start.round_end,
        (res.confirmed_round-1),
    )

    assert res.return_value == ContractDeleteReturn(
        remaining_balance=MBR_ACCOUNT+unpaid if asset == ALGO_ASA_ID else unpaid,
        asset_id=asset,
    )

    # Check contract state
    gs_end = noticeboard.get_global_state()
    gs_exp = gs_start
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check balances
    bal_end = noticeboard.app_available_balance(ALGO_ASA_ID)
    bal_end_asset = noticeboard.app_available_balance(asset)
    if asset != ALGO_ASA_ID:
        assert bal_end == bal_start
        assert bal_end_asset == bal_start_asset
    else:
        assert bal_end == bal_start

    # Check delegator contract was deleted
    assert is_deleted(noticeboard.algorand_client, del_app_id)

    # Delegator user gets the app deleted from its list
    del_user_info = noticeboard.app_get_user_info(del_user)
    del_user_info_exp = del_user_info_start
    del_user_info_exp.cnt_app_ids = 0
    del_user_info_exp.app_ids = [0] * len(del_user_info_start.app_ids)
    assert del_user_info == del_user_info_exp

    return

def test_action_another_option(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)

    gs_start = noticeboard.get_global_state()

    # Action
    del_app_id = noticeboard.initialize_delegator_contract_state(
        action_inputs=action_inputs,
        val_app_id=val_app_id,
        target_state="DELETED_VIA_ENDED_WITHDREW",
    )

    # Check contract state
    gs_end = noticeboard.get_global_state()
    gs_exp = gs_start
    gs_exp.dll_del = gs_end.dll_del # For simplicity
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check delegator contract was deleted
    assert is_deleted(noticeboard.algorand_client, del_app_id)

    # Delegator user gets the app deleted from its list
    del_user = noticeboard.del_managers[0].address
    del_user_info = noticeboard.app_get_user_info(del_user)
    assert del_user_info

    return

def test_sender_not_del_manager(
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
        noticeboard.delegator_action(
            app_id=del_app_id,
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            val_app=val_app_id,
            action_account=noticeboard.dispenser,
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

    return
