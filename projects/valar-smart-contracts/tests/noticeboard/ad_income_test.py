
import pytest
from algokit_utils.beta.composer import AssetTransferParams, PayParams
from algokit_utils.logic_error import LogicError
from algosdk.logic import get_application_address

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
from tests.utils import available_balance, is_expected_logic_error

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "SET"
TEST_VA_STATE = "SET"
TEST_ACTION_NAME = "ad_income"

# ------- Tests -------
def test_action(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    # Send the ValidatorAd some asset that can be withdrawn
    val_app_address = get_application_address(val_app_id)
    amount = 735_864
    if asset != ALGO_ASA_ID:
        # Get some ASA
        noticeboard.algorand_client.send.asset_transfer(
            AssetTransferParams(
                sender=noticeboard.dispenser.address,
                receiver=val_app_address,
                amount=amount,
                asset_id=asset,
            )
        )
    else:
        noticeboard.algorand_client.send.payment(
            PayParams(
                sender=noticeboard.dispenser.address,
                receiver=val_app_address,
                amount=amount,
            )
        )
    gs_start = noticeboard.get_global_state()
    gs_val_start = noticeboard.get_validator_ad_global_state(val_app_id)
    val_bal_start = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=val_app_address,
        asset_id=asset,
    )
    val_owner_bal_start = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=noticeboard.val_owners[0].address,
        asset_id=asset,
    )
    bal_start = noticeboard.app_available_balance(asset)

    # Action
    res = noticeboard.validator_action(val_app_id, TEST_ACTION_NAME, action_inputs)

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check balances
    val_bal_end = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=val_app_address,
        asset_id=asset,
    )
    val_owner_bal_end = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=noticeboard.val_owners[0].address,
        asset_id=asset,
    )
    bal_end = noticeboard.app_available_balance(asset)
    assert val_bal_start == val_bal_end + amount
    paid_fee = res.tx_info["txn"]["txn"]["fee"] if asset == ALGO_ASA_ID else 0
    assert val_owner_bal_start + amount == val_owner_bal_end + paid_fee
    assert bal_start == bal_end

    # Check validator ad state
    gs_val_end = noticeboard.get_validator_ad_global_state(val_app_id)
    gs_val_exp = gs_val_start
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
