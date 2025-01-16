

import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.logic_error import LogicError

from smart_contracts.artifacts.delegator_contract.client import EarningsDistributionAndMessage
from smart_contracts.delegator_contract.constants import (
    STATE_ENDED_EXPIRED,
)
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_CALLED_BY_NOT_CREATOR,
    ERROR_NOT_YET_EXPIRED,
    ERROR_OPERATION_FEE_ALREADY_CLAIMED_AT_ROUND,
    MSG_CORE_CONTRACT_EXPIRED,
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
TEST_ACTION_NAME = "contract_expired"

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
        gs_start.round_end,
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
        msg=list(MSG_CORE_CONTRACT_EXPIRED),
    ), ERROR_DELEGATOR_WRONG_EARNINGS_RETURNED

    # Check contract state
    gs_exp = gs_start
    gs_exp.state = STATE_ENDED_EXPIRED
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

def test_too_early(
    delegator_contract: DelegatorContract,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    action_inputs.wait_until_expired = False

    # Action fail
    with pytest.raises(LogicError) as e:
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_NOT_YET_EXPIRED, e)

    return

def test_claim_and_expire(
    delegator_contract: DelegatorContract,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = delegator_contract.get_global_state()

    wait_for = 13
    wait_for_rounds(
        algorand_client=delegator_contract.algorand_client,
        num_rounds=wait_for,
        acc=delegator_contract.acc,
    )
    res_claim = delegator_contract.action(action_name="contract_claim", action_inputs=action_inputs)

    action_inputs.wait_until_expired = True # To be explicit

    # Action success
    res = delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    amount = calc_operational_fee(
        gs_start.delegation_terms_general.fee_round,
        gs_start.round_end,
        res_claim.confirmed_round,
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
        msg=list(MSG_CORE_CONTRACT_EXPIRED),
    ), ERROR_DELEGATOR_WRONG_EARNINGS_RETURNED

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

def test_claim_after_expiry_and_report_expire_later(
    delegator_contract: DelegatorContract,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Wait until contract expires and claim only afterwards
    gs_start = delegator_contract.get_global_state()
    status = delegator_contract.algorand_client.client.algod.status()
    current_round = status["last-round"]
    num_rounds = gs_start.round_end - current_round
    wait_for_rounds(
        algorand_client=delegator_contract.algorand_client,
        num_rounds=num_rounds,
        acc=delegator_contract.acc,
    )
    delegator_contract.action(action_name="contract_claim", action_inputs=action_inputs)

    # Wait some more before reporting expiry
    wait_for_rounds(
        algorand_client=delegator_contract.algorand_client,
        num_rounds=num_rounds,
        acc=delegator_contract.acc,
    )

    action_inputs.wait_until_expired = True # To be explicit

    # Action success
    res = delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    validator_earns = 0
    platforms_earns = 0

    assert res.return_value == EarningsDistributionAndMessage(
        earnings_distribution=[
            validator_earns,
            platforms_earns,
            action_inputs.delegation_terms_general.fee_asset_id,
        ],
        del_manager=gs_start.del_manager,
        msg=list(MSG_CORE_CONTRACT_EXPIRED),
    ), ERROR_DELEGATOR_WRONG_EARNINGS_RETURNED

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

def test_claim_and_expiry_edge(
    delegator_contract: DelegatorContract,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Wait until contract expires
    gs_start = delegator_contract.get_global_state()
    status = delegator_contract.algorand_client.client.algod.status()
    current_round = status["last-round"]
    num_rounds = (gs_start.round_end-1) - current_round
    wait_for_rounds(
        algorand_client=delegator_contract.algorand_client,
        num_rounds=num_rounds,
        acc=delegator_contract.acc,
    )

    action_inputs.wait_until_expired = True # To be explicit

    # Claim and expire in same block
    # Increase fee for (potential) distribution of earnings
    sp = delegator_contract.algorand_client.client.algod.suggested_params()
    sp.fee = 3 * sp.min_fee
    sp.flat_fee = True
    # Add asset to the foreign asset array
    if action_inputs.delegation_terms_general.fee_asset_id != ALGO_ASA_ID:
        foreign_assets = [action_inputs.delegation_terms_general.fee_asset_id]
    else:
        foreign_assets = None

    composer = delegator_contract.delegator_contract_client.compose()
    composer.contract_claim(
        transaction_parameters = TransactionParameters(
            sender = delegator_contract.acc.address,
            signer = delegator_contract.acc.signer,
            suggested_params=sp,
            foreign_assets=foreign_assets,
        ),
    )
    composer.contract_expired(
        transaction_parameters = TransactionParameters(
            sender = delegator_contract.acc.address,
            signer = delegator_contract.acc.signer,
            suggested_params=sp,
            foreign_assets=foreign_assets,
        ),
    )

    # Action fail
    with pytest.raises(LogicError) as e:
        composer.execute()

    assert is_expected_logic_error(ERROR_OPERATION_FEE_ALREADY_CLAIMED_AT_ROUND, e)

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

