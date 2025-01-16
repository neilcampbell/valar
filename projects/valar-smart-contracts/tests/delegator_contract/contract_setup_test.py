
from hashlib import sha256

import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.logic_error import LogicError

from smart_contracts.delegator_contract.constants import (
    STATE_SET,
)
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_CALLED_BY_NOT_CREATOR,
)
from tests.constants import ERROR_GLOBAL_STATE_MISMATCH, SKIP_SAME_AS_FOR_ALGO
from tests.delegator_contract.utils import DelegatorContract
from tests.utils import calc_operational_fee, is_expected_logic_error

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "CREATED"
TEST_ACTION_NAME = "contract_setup"

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

    # Action
    res = delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    gs_exp.state = STATE_SET
    gs_exp.delegation_terms_balance = action_inputs.delegation_terms_balance
    gs_exp.delegation_terms_general = action_inputs.delegation_terms_general
    gs_exp.round_start = res.confirmed_round
    gs_exp.round_end = res.confirmed_round + action_inputs.rounds_duration
    gs_exp.round_claim_last = res.confirmed_round
    gs_exp.fee_operational = calc_operational_fee(
        action_inputs.delegation_terms_general.fee_round,
        gs_exp.round_end,
        gs_exp.round_start,
    )
    gs_exp.tc_sha256 = sha256(b"Test").digest()
    assert delegator_contract.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # If asset ID is not zero (i.e. ALGO), check if contract opted-in to it.
    if asset != ALGO_ASA_ID:
        assert delegator_contract.app_is_opted_in(asset)

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
    dispenser : AddressAndSigner,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    action_inputs.delegation_terms_general.partner_address = dispenser.address
    action_inputs.delegation_terms_general.fee_round_partner = 543
    action_inputs.delegation_terms_general.fee_setup_partner = 278
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = delegator_contract.get_global_state()

    # Action
    res = delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    gs_exp.state = STATE_SET
    gs_exp.delegation_terms_balance = action_inputs.delegation_terms_balance
    gs_exp.delegation_terms_general = action_inputs.delegation_terms_general
    gs_exp.round_start = res.confirmed_round
    gs_exp.round_end = res.confirmed_round + action_inputs.rounds_duration
    gs_exp.round_claim_last = res.confirmed_round
    gs_exp.fee_operational = calc_operational_fee(
        action_inputs.delegation_terms_general.fee_round,
        gs_exp.round_end,
        gs_exp.round_start,
    )
    gs_exp.fee_operational_partner = calc_operational_fee(
        action_inputs.delegation_terms_general.fee_round_partner,
        gs_exp.round_end,
        gs_exp.round_start,
    )
    gs_exp.tc_sha256 = sha256(b"Test").digest()
    assert delegator_contract.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # If asset ID is not zero (i.e. ALGO), check if contract opted-in to it.
    if asset != ALGO_ASA_ID:
        assert delegator_contract.app_is_opted_in(asset)
