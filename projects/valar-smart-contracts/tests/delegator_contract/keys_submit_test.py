
import base64
from math import sqrt

import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.logic_error import LogicError
from algosdk.constants import ZERO_ADDRESS

from smart_contracts.artifacts.delegator_contract.client import EarningsDistributionAndMessage
from smart_contracts.delegator_contract.constants import (
    STATE_SUBMITTED,
)
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_CALLED_BY_NOT_CREATOR,
    ERROR_KEY_BENEFICIARY_MISMATCH,
    ERROR_KEY_SUBMIT_TOO_LATE,
    ERROR_VOTE_FIRST_ROUND_MISMATCH,
    ERROR_VOTE_LAST_ROUND_MISMATCH,
    MSG_CORE_KEYS_SUBMIT,
)
from tests.constants import ERROR_DELEGATOR_SETUP_FEE_NOT_REMAINING, ERROR_GLOBAL_STATE_MISMATCH, SKIP_SAME_AS_FOR_ALGO
from tests.delegator_contract.utils import DelegatorContract
from tests.utils import calc_earnings, is_expected_logic_error, wait_for_rounds

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "READY"
TEST_ACTION_NAME = "keys_submit"

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
    action_inputs.key_reg_vote_first = gs_start.round_start
    action_inputs.key_reg_vote_last = gs_start.round_end
    action_inputs.key_reg_vote_key_dilution = round(sqrt(gs_start.round_end-gs_start.round_start))

    # Action success
    res = delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    validator_earns, platforms_earns = calc_earnings(
       amount=action_inputs.delegation_terms_general.fee_setup,
       commission=action_inputs.delegation_terms_general.commission,
    )

    assert res.return_value == EarningsDistributionAndMessage(
        earnings_distribution=[validator_earns,platforms_earns,action_inputs.delegation_terms_general.fee_asset_id],
        del_manager=gs_start.del_manager,
        msg=list(MSG_CORE_KEYS_SUBMIT),
    )

    # Check contract state
    gs_exp = gs_start
    gs_exp.state = STATE_SUBMITTED
    gs_exp.sel_key = base64.b64decode(action_inputs.key_reg_selection)
    gs_exp.vote_key = base64.b64decode(action_inputs.key_reg_vote)
    gs_exp.state_proof_key = base64.b64decode(action_inputs.key_reg_state_proof)
    gs_exp.vote_key_dilution = action_inputs.key_reg_vote_key_dilution
    assert delegator_contract.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check if earnings were NOT distributed because calling apps are not existent
    assert delegator_contract.app_available_balance(asset) == \
        gs_start.delegation_terms_general.fee_setup + gs_start.fee_operational, \
        ERROR_DELEGATOR_SETUP_FEE_NOT_REMAINING

    return

def test_submit_too_late(
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
            gs_start.delegation_terms_general.rounds_setup + 1 \
            - current_round
        wait_for_rounds(
            algorand_client = delegator_contract.algorand_client,
            num_rounds = num_rounds,
            acc = delegator_contract.acc,
        )
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_KEY_SUBMIT_TOO_LATE, e)

    return

def test_wrong_key_parameters(
    delegator_contract: DelegatorContract,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Actions fail
    with pytest.raises(LogicError) as e:
        action_inputs.key_reg_sender = ZERO_ADDRESS
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_KEY_BENEFICIARY_MISMATCH, e)
    action_inputs.key_reg_sender = None # Rest to default

    with pytest.raises(LogicError) as e:
        action_inputs.key_reg_vote_first = 0
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_VOTE_FIRST_ROUND_MISMATCH, e)
    action_inputs.key_reg_vote_first = None # Rest to default

    with pytest.raises(LogicError) as e:
        action_inputs.key_reg_vote_last = 999_999_999
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_VOTE_LAST_ROUND_MISMATCH, e)
    action_inputs.key_reg_vote_last = None # Rest to default

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

