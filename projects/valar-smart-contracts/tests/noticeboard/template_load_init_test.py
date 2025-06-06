
import pytest
from algokit_utils.logic_error import LogicError

from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY,
    ERROR_CALLED_BY_NOT_PLA_MANAGER,
    ERROR_NOT_STATE_DEPLOYED,
    ERROR_UNEXPECTED_TEMPLATE_NAME,
)
from tests.constants import ERROR_GLOBAL_STATE_MISMATCH, ERROR_MBR_INCORRECTLY_SPENT, SKIP_SAME_AS_FOR_ALGO
from tests.noticeboard.utils import POSSIBLE_STATES, Noticeboard
from tests.utils import is_expected_logic_error

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "DEPLOYED"
TEST_ACTION_NAME = "template_load_init"

# ------- Tests -------
def test_action(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.template_name = BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY
    action_inputs.template_size = 4242
    # Note: Platform manager is the creator
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = noticeboard.get_global_state()

    # Action
    res = noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    assert noticeboard.app_box(action_inputs.template_name) == [
        bytes(action_inputs.template_size),
        True,
    ]

    end_available_bal = noticeboard.app_available_balance(ALGO_ASA_ID)
    assert end_available_bal == 0, ERROR_MBR_INCORRECTLY_SPENT

    return

def test_wrong_pla_manager(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.template_name = BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY
    action_inputs.template_size = 4242
    # Note: The creator is the platform manager
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

def test_unexpected_box_name(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.template_name = b"_"
    action_inputs.template_size = 4242
    # Note: The creator is the platform manager
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_UNEXPECTED_TEMPLATE_NAME, e)

    return

@pytest.mark.parametrize("init_state", [
    "DEPLOYED",
    "SET",
    "SUSPENDED",
    "RETIRED",
])
def test_state(
    noticeboard: Noticeboard,
    asset : int,
    init_state : POSSIBLE_STATES,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=init_state, action_inputs=action_inputs)

    if init_state == "DEPLOYED":
        action_inputs.template_name = BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY
        action_inputs.template_size = 4242
        gs_start = noticeboard.get_global_state()

        # Action success
        res = noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
        assert res.confirmed_round

        # Check new state - should not change
        exp_state = gs_start.state
        gs_end = noticeboard.get_global_state()
        assert gs_end.state == exp_state
    else:
        # Action fail
        with pytest.raises(LogicError) as e:
            noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
        assert is_expected_logic_error(ERROR_NOT_STATE_DEPLOYED, e)

    return
