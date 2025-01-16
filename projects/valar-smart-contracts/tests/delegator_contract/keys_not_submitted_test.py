

import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.logic_error import LogicError

from smart_contracts.artifacts.delegator_contract.client import Message
from smart_contracts.delegator_contract.constants import (
    STATE_ENDED_NOT_SUBMITTED,
)
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_CALLED_BY_NOT_CREATOR,
    ERROR_REPORT_NOT_SUBMITTED_TOO_EARLY,
    MSG_CORE_KEYS_NOT_SUBMITTED,
)
from tests.constants import ERROR_GLOBAL_STATE_MISMATCH, SKIP_SAME_AS_FOR_ALGO
from tests.delegator_contract.utils import DelegatorContract, available_balance
from tests.utils import is_expected_logic_error

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "READY"
TEST_ACTION_NAME = "keys_not_submitted"

# ------- Tests -------
def test_action(
    delegator_contract: DelegatorContract,
    del_manager: AddressAndSigner,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    action_inputs.del_manager = del_manager.address
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = delegator_contract.get_global_state()
    del_manager_bal_start = available_balance(
        algorand_client=delegator_contract.algorand_client,
        address=action_inputs.del_manager,
        asset_id=asset,
    )

    action_inputs.wait_until_keys_not_submitted = True # To be explicit

    # Action success
    res = delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.return_value == Message(
        del_manager=gs_start.del_manager,
        msg=list(MSG_CORE_KEYS_NOT_SUBMITTED),
    )

    # Check contract state
    gs_exp = gs_start
    gs_exp.state = STATE_ENDED_NOT_SUBMITTED
    gs_exp.round_ended = res.confirmed_round
    assert delegator_contract.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check if setup and operational fee was returned to delegator manager account
    assert delegator_contract.app_available_balance(asset) == 0, \
        "Contract should have zero available balance."
    del_manager_bal_end = available_balance(
        algorand_client=delegator_contract.algorand_client,
        address=action_inputs.del_manager,
        asset_id=asset,
    )

    assert del_manager_bal_end == del_manager_bal_start + \
        gs_start.fee_operational + gs_start.delegation_terms_general.fee_setup
        # There is no need to count fee paid in this test even if ALGO_ASSET_ID is used
        # because the call is done by the default account (creator) and manager address
        # simply passed as an input

    return

def test_report_too_early(
    delegator_contract: DelegatorContract,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    action_inputs.wait_until_keys_not_submitted = False

    # Action fail
    with pytest.raises(LogicError) as e:
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_REPORT_NOT_SUBMITTED_TOO_EARLY, e)

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

def test_action_w_partner(
    delegator_contract: DelegatorContract,
    del_manager: AddressAndSigner,
    partner : AddressAndSigner,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    action_inputs.del_manager = del_manager.address
    action_inputs.delegation_terms_general.partner_address = partner.address
    action_inputs.delegation_terms_general.fee_round_partner = 543
    action_inputs.delegation_terms_general.fee_setup_partner = 278
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = delegator_contract.get_global_state()
    del_manager_bal_start = available_balance(
        algorand_client=delegator_contract.algorand_client,
        address=action_inputs.del_manager,
        asset_id=asset,
    )

    action_inputs.wait_until_keys_not_submitted = True # To be explicit

    # Action success
    res = delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.return_value == Message(
        del_manager=gs_start.del_manager,
        msg=list(MSG_CORE_KEYS_NOT_SUBMITTED),
    )

    # Check contract state
    gs_exp = gs_start
    gs_exp.state = STATE_ENDED_NOT_SUBMITTED
    gs_exp.round_ended = res.confirmed_round
    assert delegator_contract.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check if setup and operational fee was returned to delegator manager account
    assert delegator_contract.app_available_balance(asset) == 0, \
        "Contract should have zero available balance."
    del_manager_bal_end = available_balance(
        algorand_client=delegator_contract.algorand_client,
        address=action_inputs.del_manager,
        asset_id=asset,
    )

    assert del_manager_bal_end == del_manager_bal_start + \
        gs_start.fee_operational + gs_start.delegation_terms_general.fee_setup + \
        gs_start.fee_operational_partner + gs_start.delegation_terms_general.fee_setup_partner
        # There is no need to count fee paid in this test even if ALGO_ASSET_ID is used
        # because the call is done by the default account (creator) and manager address
        # simply passed as an input

    return
