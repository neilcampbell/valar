
import pytest
from algokit_utils.logic_error import LogicError

from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY,
    ERROR_APP_NOT_WITH_USER,
    ERROR_USER_DOES_NOT_EXIST,
    MBR_ACCOUNT,
    MBR_NOTICEBOARD_VALIDATOR_AD_CONTRACT_INCREASE,
)
from tests.constants import (
    ERROR_GLOBAL_STATE_MISMATCH,
    SKIP_SAME_AS_FOR_ALGO,
)
from tests.noticeboard.utils import Noticeboard
from tests.utils import available_balance, calc_box_mbr, get_box, is_expected_logic_error

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "SET"
TEST_VA_STATE = "SET"
TEST_ACTION_NAME = "ad_delete"

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
    val_owner_bal_start = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=gs_val_start.val_owner,
        asset_id=ALGO_ASA_ID,
    )
    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)
    box_del = get_box(
        algorand_client=noticeboard.algorand_client,
        box_name=BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY,
        app_id=val_app_id,
    )
    box_del_size = len(box_del[0])

    # Action
    res = noticeboard.validator_action(val_app_id, TEST_ACTION_NAME, action_inputs)

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    val_owner_bal_end = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=gs_val_start.val_owner,
        asset_id=ALGO_ASA_ID,
    )
    bal_end = noticeboard.app_available_balance(ALGO_ASA_ID)
    paid_fee = 6_000 # Hardcoded it here but would need to take the sum of fees across the gtxn to make it general
    assert val_owner_bal_end + paid_fee == (
        val_owner_bal_start +
        calc_box_mbr(box_del_size, BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY) +
        MBR_NOTICEBOARD_VALIDATOR_AD_CONTRACT_INCREASE +
        MBR_ACCOUNT
    )
    assert bal_start == bal_end

    # Check validator ad state
    gs_val_end = noticeboard.get_validator_ad_global_state(val_app_id)
    gs_val_exp = None
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
