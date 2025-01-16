
import pytest
from algokit_utils.logic_error import LogicError

import tests.noticeboard.validator_ad_interface as va
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_APP_NOT_WITH_USER,
    ERROR_USER_DOES_NOT_EXIST,
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
TEST_VA_STATE = "NOT_READY"
TEST_ACTION_NAME = "ad_ready"

# ------- Tests -------
def test_action(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    gs_start = noticeboard.get_global_state()
    gs_val_start = noticeboard.get_validator_ad_global_state(val_app_id)
    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)

    action_inputs.ready = True

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
    gs_val_exp.state = va.STATE_READY
    assert gs_val_end == gs_val_exp

    return

def test_not_ready_from_ready(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    target_state = "READY"
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=target_state)
    gs_start = noticeboard.get_global_state()
    gs_val_start = noticeboard.get_validator_ad_global_state(val_app_id)
    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)

    action_inputs.ready = False

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
    assert gs_val_end == gs_val_exp

    return

def test_wrong_pla_manager(
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
    assert "inner tx 0 failed: logic eval error: assert " in str(e.value)

    return

def test_val_owner_does_not_exist(
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
        action_inputs.val_owner = noticeboard.dispenser.address
        noticeboard.validator_action(val_app_id, TEST_ACTION_NAME, action_inputs)
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
