
import copy

import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.logic_error import LogicError
from algosdk.constants import ZERO_ADDRESS

from smart_contracts.delegator_contract.constants import (
    STATE_LIVE,
)
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_ACCOUNT_HAS_NOT_REGISTERED_FOR_SUSPENSION_TRACKING,
    ERROR_CALLED_BY_NOT_CREATOR,
    ERROR_KEY_CONFIRM_TOO_LATE,
    ERROR_NOT_MANAGER,
)
from tests.constants import ERROR_GLOBAL_STATE_MISMATCH, SKIP_SAME_AS_FOR_ALGO
from tests.delegator_contract.utils import DelegatorContract
from tests.utils import is_account_tracked, is_expected_logic_error, wait_for_rounds

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "SUBMITTED"
TEST_ACTION_NAME = "keys_confirm"

# ------- Tests -------
def test_action(
    delegator_contract: DelegatorContract,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = delegator_contract.get_global_state()

    # Action success
    res = delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    gs_exp.state = STATE_LIVE
    gs_exp.round_breach_last = res.confirmed_round
    gs_exp.cnt_breach_del = 0
    assert delegator_contract.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check if (available) balance is correct
    assert delegator_contract.app_available_balance(asset) == \
        action_inputs.delegation_terms_general.fee_setup + action_inputs.fee_operational, \
        "Contract should have the sum of setup fee and operational fee remaining because" + \
        "there is no validator app which could claim the setup fee."

    # Check account beneficiary has registered for network incentives, i.e. is tracked by suspension mechanism
    is_tracked = is_account_tracked(
        delegator_contract.algorand_client,
        gs_start.del_beneficiary,
    )
    assert is_tracked

    return

def test_not_tracked(
    delegator_contract: DelegatorContract,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail - not registering at all
    with pytest.raises(LogicError) as e:
        ai = copy.deepcopy(action_inputs)
        ai.key_reg_before_confirm = False
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=ai)
    assert is_expected_logic_error(ERROR_ACCOUNT_HAS_NOT_REGISTERED_FOR_SUSPENSION_TRACKING, e)

    # Action fail - too low fee
    with pytest.raises(LogicError) as e:
        ai = copy.deepcopy(action_inputs)
        ai.key_reg_fee = 2_345
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=ai)
    assert is_expected_logic_error(ERROR_ACCOUNT_HAS_NOT_REGISTERED_FOR_SUSPENSION_TRACKING, e)

    return

def test_wrong_manager(
    delegator_contract: DelegatorContract,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.del_manager = ZERO_ADDRESS
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_NOT_MANAGER, e)

    return

def test_confirm_too_late(
    delegator_contract: DelegatorContract,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = delegator_contract.get_global_state()

    # Action fail
    with pytest.raises(LogicError) as e:
        status = delegator_contract.algorand_client.client.algod.status()
        current_round = status["last-round"]
        num_rounds = \
            gs_start.round_start + \
            gs_start.delegation_terms_general.rounds_setup + \
            gs_start.delegation_terms_general.rounds_confirm + 1 \
            - current_round
        wait_for_rounds(
            algorand_client = delegator_contract.algorand_client,
            num_rounds = num_rounds,
            acc = delegator_contract.acc,
        )
        action_inputs.key_reg_before_confirm = False  # Because account can't be marked online for past, must skip it
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_KEY_CONFIRM_TOO_LATE, e)

    return

def test_wrong_caller(
    delegator_contract: DelegatorContract,
    dispenser : AddressAndSigner,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        delegator_contract.acc = dispenser
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_CALLED_BY_NOT_CREATOR, e)

    return
