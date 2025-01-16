

import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.logic_error import LogicError
from algosdk.constants import ZERO_ADDRESS

from smart_contracts.artifacts.delegator_contract.client import EarningsDistribution
from smart_contracts.delegator_contract.constants import (
    STATE_ENDED_WITHDREW,
)
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_ALREADY_EXPIRED,
    ERROR_CALLED_BY_NOT_CREATOR,
    ERROR_NOT_MANAGER,
)
from tests.constants import (
    ERROR_DELEGATOR_SETUP_FEE_NOT_REMAINING,
    ERROR_DELEGATOR_WRONG_EARNINGS_RETURNED,
    ERROR_GLOBAL_STATE_MISMATCH,
    SKIP_SAME_AS_FOR_ALGO,
)
from tests.delegator_contract.utils import DelegatorContract
from tests.utils import calc_earnings, calc_operational_fee, is_expected_logic_error, wait_for_rounds

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "LIVE"
TEST_ACTION_NAME = "contract_withdraw"

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

    action_inputs.wait_until_expired = True # To be explicit

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

    assert res.return_value == EarningsDistribution(
        user=validator_earns,
        platform=platforms_earns,
        asset_id=action_inputs.delegation_terms_general.fee_asset_id,
    ), ERROR_DELEGATOR_WRONG_EARNINGS_RETURNED

    # Check contract state
    gs_exp = gs_start
    gs_exp.state = STATE_ENDED_WITHDREW
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
    num_rounds = (gs_start.round_end-1) - current_round # Cannot withdraw on last round
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

