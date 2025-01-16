
import pytest
from algokit_utils.beta.composer import AssetTransferParams, PayParams
from algokit_utils.logic_error import LogicError

from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_CALLED_BY_NOT_PLA_MANAGER,
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
TEST_ACTION_NAME = "noticeboard_income"

# ------- Tests -------
def test_action(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    # Send the contract some asset that can be withdrawn
    amount = 735_864
    if asset != ALGO_ASA_ID:
        # Get some ASA
        noticeboard.algorand_client.send.asset_transfer(
            AssetTransferParams(
                sender=noticeboard.dispenser.address,
                receiver=noticeboard.noticeboard_client.app_address,
                amount=amount,
                asset_id=asset,
            )
        )
    else:
        noticeboard.algorand_client.send.payment(
            PayParams(
                sender=noticeboard.dispenser.address,
                receiver=noticeboard.noticeboard_client.app_address,
                amount=amount,
            )
        )

    gs_start = noticeboard.get_global_state()
    start_available_bal_contract = noticeboard.app_available_balance(asset)
    start_available_bal_pla_manager = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=gs_start.pla_manager,
        asset_id=asset,
    )

    # Action
    res = noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check available balances
    end_available_bal_contract = noticeboard.app_available_balance(asset)
    end_available_bal_pla_manager = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=gs_start.pla_manager,
        asset_id=asset,
    )
    assert end_available_bal_contract + amount == start_available_bal_contract
    assert end_available_bal_contract == 0
    if asset == ALGO_ASA_ID:
        paid_fee = res.tx_info["txn"]["txn"]["fee"]
        assert end_available_bal_pla_manager + paid_fee == start_available_bal_pla_manager + amount
    else:
        assert end_available_bal_pla_manager == start_available_bal_pla_manager + amount

    return

def test_wrong_pla_manager(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        # Switch sender not to be the platform manager
        noticeboard.noticeboard_action(
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            action_account=noticeboard.dispenser,
        )

    assert is_expected_logic_error(ERROR_CALLED_BY_NOT_PLA_MANAGER, e)

    return
