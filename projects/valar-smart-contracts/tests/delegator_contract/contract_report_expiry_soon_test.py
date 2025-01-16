

import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.logic_error import LogicError

from smart_contracts.artifacts.delegator_contract.client import Message
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_ALREADY_EXPIRED,
    ERROR_CALLED_BY_NOT_CREATOR,
    ERROR_TOO_SOON_TO_REPORT_EXPIRY_SOON,
    ERROR_TOO_SOON_TO_REPORT_EXPIRY_SOON_AGAIN,
    MSG_CORE_WILL_EXPIRE,
)
from tests.constants import (
    ERROR_GLOBAL_STATE_MISMATCH,
    SKIP_SAME_AS_FOR_ALGO,
)
from tests.delegator_contract.utils import DelegatorContract
from tests.utils import is_expected_logic_error, wait_for_rounds

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "LIVE"
TEST_ACTION_NAME = "contract_report_expiry_soon"

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

    action_inputs.wait_expiry_report = True # To be explicit

    # Action success
    res = delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.return_value == Message(
        del_manager=gs_start.del_manager,
        msg=list(MSG_CORE_WILL_EXPIRE),
    )

    # Check contract state
    gs_exp = gs_start
    gs_exp.round_expiry_soon_last = res.confirmed_round
    assert delegator_contract.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    return

def test_report_too_soon_before_end(
    delegator_contract: DelegatorContract,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    action_inputs.wait_expiry_report = False

    # Action fail
    with pytest.raises(LogicError) as e:
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_TOO_SOON_TO_REPORT_EXPIRY_SOON, e)

    return

def test_report_too_late(
    delegator_contract: DelegatorContract,
    dispenser : AddressAndSigner,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    action_inputs.wait_expiry_report = False

    gs = delegator_contract.get_global_state()
    status = delegator_contract.algorand_client.client.algod.status()
    current_round = status["last-round"]
    num_rounds = gs.round_end - current_round
    wait_for_rounds(
        algorand_client=delegator_contract.algorand_client,
        num_rounds=num_rounds,
        acc=dispenser,
    )

    # Action fail
    with pytest.raises(LogicError) as e:
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_ALREADY_EXPIRED, e)

    return

def test_report_twice(
    delegator_contract: DelegatorContract,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = delegator_contract.get_global_state()

    action_inputs.wait_expiry_report = True # To be explicit

    # Report 1st time
    delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Action success
    res = delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.return_value == Message(
        del_manager=gs_start.del_manager,
        msg=list(MSG_CORE_WILL_EXPIRE),
    )

    # Check contract state
    gs_exp = gs_start
    gs_exp.round_expiry_soon_last = res.confirmed_round
    assert delegator_contract.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    return

def test_report_2nd_too_soon(
    delegator_contract: DelegatorContract,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    action_inputs.wait_expiry_report = True # To be explicit

    # Report 1st time
    delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.wait_expiry_report = False
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_TOO_SOON_TO_REPORT_EXPIRY_SOON_AGAIN, e)

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

