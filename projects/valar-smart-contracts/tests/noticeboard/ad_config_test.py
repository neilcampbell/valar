
import pytest
from algokit_utils.logic_error import LogicError

import tests.noticeboard.validator_ad_interface as va
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_APP_NOT_WITH_USER,
    ERROR_USER_DOES_NOT_EXIST,
    MAXIMUM_NUMBER_OF_DELEGATORS_PER_NODE,
)
from tests.constants import (
    ERROR_GLOBAL_STATE_MISMATCH,
    SKIP_SAME_AS_FOR_ALGO,
)
from tests.noticeboard.utils import Noticeboard
from tests.utils import is_expected_logic_error

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "SET"
TEST_VA_STATE = "SET"
TEST_ACTION_NAME = "ad_config"

# ------- Tests -------
def test_action(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(
        asset=asset,
        val_manager=noticeboard.val_managers[0].address,
        live=True,
        cnt_del_max=2,
    )
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    gs_start = noticeboard.get_global_state()
    gs_val_start = noticeboard.get_validator_ad_global_state(val_app_id)
    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)

    # Action
    res = noticeboard.validator_action(val_app_id, TEST_ACTION_NAME, action_inputs)

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    bal_end = noticeboard.app_available_balance(ALGO_ASA_ID)
    assert bal_start == bal_end

    # Check validator ad state
    gs_val_end = noticeboard.get_validator_ad_global_state(val_app_id)
    gs_val_exp = gs_val_start
    gs_val_exp.state = va.STATE_NOT_READY
    gs_val_exp.val_manager = action_inputs.val_manager
    gs_val_exp.cnt_del_max = action_inputs.cnt_del_max
    assert gs_val_end == gs_val_exp

    return

def test_user_does_not_exist(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)

    # Action fail
    with pytest.raises(LogicError) as e:
        noticeboard.validator_action(val_app_id, TEST_ACTION_NAME, action_inputs, noticeboard.dispenser)
    assert is_expected_logic_error(ERROR_USER_DOES_NOT_EXIST, e)

    return

def test_app_does_not_exist(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)

    # Action fail - index doesn't match
    with pytest.raises(LogicError) as e:
        action_inputs.val_app_idx = 99
        noticeboard.validator_action(val_app_id, TEST_ACTION_NAME, action_inputs)
    assert is_expected_logic_error(ERROR_APP_NOT_WITH_USER, e)
    action_inputs.val_app_idx = None # Reset

    # Action fail - app ID doesn't match
    with pytest.raises(LogicError) as e:
        action_inputs.val_app_id = 99
        noticeboard.validator_action(val_app_id, TEST_ACTION_NAME, action_inputs)
    assert is_expected_logic_error(ERROR_APP_NOT_WITH_USER, e)

    return

def test_go_to_not_live_state(
    noticeboard: Noticeboard,
    asset : int,
) -> None:
    """
    This is test of initialize_validator_ad_state() call to get the validator ad to NOT_LIVE state.
    """

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    gs_start = noticeboard.get_global_state()
    gs_val_start = noticeboard.get_validator_ad_global_state(val_app_id)
    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)

    action_inputs.val_manager=noticeboard.val_managers[0].address

    # Action
    noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, app_id=val_app_id, target_state="NOT_LIVE")

    # Check contract state
    gs_exp = gs_start
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    bal_end = noticeboard.app_available_balance(ALGO_ASA_ID)
    assert bal_start == bal_end

    # Check validator ad state
    gs_val_end = noticeboard.get_validator_ad_global_state(val_app_id)
    gs_val_exp = gs_val_start
    gs_val_exp.state = va.STATE_NOT_LIVE
    gs_val_exp.cnt_del_max = MAXIMUM_NUMBER_OF_DELEGATORS_PER_NODE
    gs_val_exp.val_manager = action_inputs.val_manager
    assert gs_val_end == gs_val_exp

    return

def test_go_to_not_ready_state(
    noticeboard: Noticeboard,
    asset : int,
) -> None:
    """
    This is test of initialize_validator_ad_state() call to get the validator ad to NOT_READY state.
    """

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    gs_start = noticeboard.get_global_state()
    gs_val_start = noticeboard.get_validator_ad_global_state(val_app_id)
    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)

    action_inputs.val_manager=noticeboard.val_managers[0].address

    # Action
    noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, app_id=val_app_id, target_state="NOT_READY")

    # Check contract state
    gs_exp = gs_start
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    bal_end = noticeboard.app_available_balance(ALGO_ASA_ID)
    assert bal_start == bal_end

    # Check validator ad state
    gs_val_end = noticeboard.get_validator_ad_global_state(val_app_id)
    gs_val_exp = gs_val_start
    gs_val_exp.state = va.STATE_NOT_READY
    gs_val_exp.cnt_del_max = MAXIMUM_NUMBER_OF_DELEGATORS_PER_NODE
    gs_val_exp.val_manager = action_inputs.val_manager
    assert gs_val_end == gs_val_exp

    return
