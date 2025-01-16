

import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.logic_error import LogicError

from smart_contracts.artifacts.delegator_contract.client import EarningsDistributionAndMessage
from smart_contracts.delegator_contract.constants import (
    STATE_ENDED_SUSPENDED,
)
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_ACCOUNT_HAS_NOT_BEEN_SUSPENDED,
    ERROR_ALREADY_EXPIRED,
    ERROR_CALLED_BY_NOT_CREATOR,
    MSG_CORE_BREACH_SUSPENDED,
)
from tests.constants import (
    ERROR_DELEGATOR_SETUP_FEE_NOT_REMAINING,
    ERROR_DELEGATOR_WRONG_EARNINGS_RETURNED,
    ERROR_GLOBAL_STATE_MISMATCH,
    SKIP_SAME_AS_FOR_ALGO,
)
from tests.delegator_contract.utils import DelegatorContract
from tests.utils import calc_earnings, calc_operational_fee, is_expected_logic_error, wait_for_rounds

from .config import DEFAULT_SETUP_DELEGATION_TERMS_GENERAL, ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "LIVE"
TEST_ACTION_NAME = "breach_suspended"

# ------- Tests -------
def test_action(
    delegator_contract: DelegatorContract,
    dispenser : AddressAndSigner,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    # Set long enough duration for this test for the beneficiary account to be able to get suspended before contract end
    action_inputs.rounds_duration = 10_000
    action_inputs.fee_operational = calc_operational_fee(
        DEFAULT_SETUP_DELEGATION_TERMS_GENERAL.fee_round,
        action_inputs.rounds_duration,
        0,
    )
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = delegator_contract.get_global_state()

    action_inputs.wait_until_suspended = True

    # Action success
    res = delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    amount = calc_operational_fee(
        gs_start.delegation_terms_general.fee_round,
        res.confirmed_round,
        gs_start.round_start,
    )
    validator_earns, platforms_earns = calc_earnings(
       amount=amount,
       commission=action_inputs.delegation_terms_general.commission,
    )

    assert res.return_value == EarningsDistributionAndMessage(
        earnings_distribution=[
            validator_earns,
            platforms_earns,
            action_inputs.delegation_terms_general.fee_asset_id,
        ],
        del_manager=gs_start.del_manager,
        msg=list(MSG_CORE_BREACH_SUSPENDED),
    ), ERROR_DELEGATOR_WRONG_EARNINGS_RETURNED

    # Check contract state
    gs_exp = gs_start
    gs_exp.state = STATE_ENDED_SUSPENDED
    gs_exp.round_ended = res.confirmed_round
    gs_exp.round_claim_last = res.confirmed_round
    assert delegator_contract.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check if earnings were NOT distributed because calling apps are not existent
    assert delegator_contract.app_available_balance(asset) == \
        gs_start.delegation_terms_general.fee_setup + \
        calc_operational_fee(
            gs_start.delegation_terms_general.fee_round,
            gs_start.round_end,
            gs_start.round_start,
        ), \
        ERROR_DELEGATOR_SETUP_FEE_NOT_REMAINING

    return

def test_not_suspended(
    delegator_contract: DelegatorContract,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    action_inputs.wait_until_suspended = False  # Do not suspend beneficiary

    # Action fail
    with pytest.raises(LogicError) as e:
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_ACCOUNT_HAS_NOT_BEEN_SUSPENDED, e)

    return

def test_already_expired(
    delegator_contract: DelegatorContract,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Wait until contract expires
    gs_start = delegator_contract.get_global_state()
    status = delegator_contract.algorand_client.client.algod.status()
    current_round = status["last-round"]
    num_rounds = (gs_start.round_end-1) - current_round # Cannot breach on last round
    wait_for_rounds(
        algorand_client=delegator_contract.algorand_client,
        num_rounds=num_rounds,
        acc=delegator_contract.acc,
    )

    # Action fail
    with pytest.raises(LogicError) as e:
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_ALREADY_EXPIRED, e)

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

