
import pytest
from algokit_utils.logic_error import LogicError

from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_CALLED_BY_NOT_PLA_MANAGER,
    ERROR_RECEIVER,
)
from tests.constants import ERROR_GLOBAL_STATE_MISMATCH, SKIP_SAME_AS_FOR_ALGO
from tests.noticeboard.utils import Noticeboard
from tests.utils import is_expected_logic_error

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "DEPLOYED"
TEST_ACTION_NAME = "noticeboard_key_reg"

# ------- Tests -------
def test_action(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    action_inputs.key_reg.vote_first = noticeboard.algorand_client.client.algod.status()["last-round"]
    action_inputs.key_reg.vote_last = action_inputs.key_reg.vote_first + 424242
    action_inputs.key_reg.vote_key_dilution = 4
    action_inputs.amount = 333_333
    action_inputs.key_reg.sender = noticeboard.noticeboard_client.app_address
    gs_start = noticeboard.get_global_state()
    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)

    # Action
    res = noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check account is online
    assert noticeboard.app_is_online()

    # Check account's key params
    assert noticeboard.app_key_params() == action_inputs.key_reg

    # Check if correct fee was paid with the key reg
    assert res.tx_info["inner-txns"][0]["txn"]["txn"]["fee"] == action_inputs.amount

    # Check available balance of the platform does not change
    bal_new = noticeboard.app_available_balance(ALGO_ASA_ID)
    assert bal_start == bal_new

    return

def test_wrong_receiver(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    action_inputs.key_reg.vote_first = noticeboard.algorand_client.client.algod.status()["last-round"]
    action_inputs.key_reg.vote_last = action_inputs.key_reg.vote_first + 424242
    action_inputs.key_reg.vote_key_dilution = 4
    action_inputs.key_reg.sender = noticeboard.noticeboard_client.app_address

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.receiver = noticeboard.dispenser.address
        noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_RECEIVER, e)

    return

def test_wrong_pla_manager(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    action_inputs.key_reg.vote_first = noticeboard.algorand_client.client.algod.status()["last-round"]
    action_inputs.key_reg.vote_last = action_inputs.key_reg.vote_first + 424242
    action_inputs.key_reg.vote_key_dilution = 4
    action_inputs.key_reg.sender = noticeboard.noticeboard_client.app_address

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
