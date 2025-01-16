

import pytest
from algokit_utils import ABITransactionResponse
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.composer import AssetTransferParams, PayParams
from algokit_utils.logic_error import LogicError

from smart_contracts.artifacts.delegator_contract.client import BreachLimitsReturn
from smart_contracts.delegator_contract.constants import (
    STATE_ENDED_LIMITS,
    STATE_LIVE,
)
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_ALREADY_EXPIRED,
    ERROR_CALLED_BY_NOT_CREATOR,
    ERROR_IS_STILL_ELIGIBLE,
    ERROR_LIMIT_BREACH_TOO_EARLY,
    MSG_CORE_BREACH_LIMITS_END,
    MSG_CORE_BREACH_LIMITS_ERROR,
)
from tests.conftest import TestConsts
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
TEST_ACTION_NAME = "breach_limits"

# ------- Tests -------
def test_action(
    delegator_contract: DelegatorContract,
    dispenser: AddressAndSigner,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    action_inputs.delegation_terms_balance.gating_asa_list[0] = (
        asset,
        round(TestConsts.acc_dispenser_asa_amt / 2),
    )
    action_inputs.delegation_terms_balance.gating_asa_list[1] = (
        asset,
        round(TestConsts.acc_dispenser_asa_amt / 3),
    )
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = delegator_contract.get_global_state()

    if asset != ALGO_ASA_ID:
        # Decrease ASA below the limit
        delegator_contract.algorand_client.send.asset_transfer(
            AssetTransferParams(
                sender = delegator_contract.del_beneficiary.address,
                signer = delegator_contract.del_beneficiary.signer,
                receiver = dispenser.address,
                amount = round(action_inputs.delegation_terms_balance.gating_asa_list[0][1]*4/3),
                asset_id=asset,
            )
        )
    else:
        # Increase ALGO above the limit
        delegator_contract.algorand_client.send.payment(
            PayParams(
                sender = dispenser.address,
                signer = dispenser.signer,
                receiver = delegator_contract.del_beneficiary.address,
                amount = round(action_inputs.delegation_terms_balance.stake_max*2),
            )
        )

    action_inputs.wait_until_limit_breach = True # To be explicit

    # Action success
    res = delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    amount = calc_operational_fee(
        gs_start.delegation_terms_general.fee_round,
        res.confirmed_round,
        gs_start.round_start
    )
    validator_earns, platforms_earns = calc_earnings(
       amount=amount,
       commission=action_inputs.delegation_terms_general.commission,
    )

    assert res.return_value == BreachLimitsReturn(
        max_breach_reached=False, # First limit breach
        earnings_distribution=[
            validator_earns,
            platforms_earns,
            action_inputs.delegation_terms_general.fee_asset_id,
        ],
        del_manager=gs_start.del_manager,
        msg=list(MSG_CORE_BREACH_LIMITS_ERROR),
    ), ERROR_DELEGATOR_WRONG_EARNINGS_RETURNED

    # Check contract state
    gs_exp = gs_start
    gs_exp.state = STATE_LIVE
    gs_exp.cnt_breach_del = 1
    gs_exp.round_claim_last = res.confirmed_round
    gs_exp.round_breach_last = res.confirmed_round
    assert delegator_contract.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check if earnings were NOT distributed because calling apps are not existent
    assert delegator_contract.app_available_balance(asset) == \
        gs_start.delegation_terms_general.fee_setup + \
        calc_operational_fee(
            gs_start.delegation_terms_general.fee_round,
            gs_start.round_end,
            gs_start.round_start
        ), \
        ERROR_DELEGATOR_SETUP_FEE_NOT_REMAINING

    return

def test_max_breach(
    delegator_contract: DelegatorContract,
    dispenser: AddressAndSigner,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    action_inputs.delegation_terms_balance.gating_asa_list[0] = (
        asset,
        round(TestConsts.acc_dispenser_asa_amt / 2),
    )
    action_inputs.delegation_terms_balance.gating_asa_list[1] = (
        asset,
        round(TestConsts.acc_dispenser_asa_amt / 3),
    )
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = delegator_contract.get_global_state()

    if asset != ALGO_ASA_ID:
        # Decrease ASA below the limit
        delegator_contract.algorand_client.send.asset_transfer(
            AssetTransferParams(
                sender = delegator_contract.del_beneficiary.address,
                signer = delegator_contract.del_beneficiary.signer,
                receiver = dispenser.address,
                amount = round(action_inputs.delegation_terms_balance.gating_asa_list[0][1]*4/3),
                asset_id=asset,
            )
        )
    else:
        # Increase ALGO above the limit
        delegator_contract.algorand_client.send.payment(
            PayParams(
                sender = dispenser.address,
                signer = dispenser.signer,
                receiver = delegator_contract.del_beneficiary.address,
                amount = round(action_inputs.delegation_terms_balance.stake_max*2),
            )
        )

    action_inputs.wait_until_limit_breach = True # To be explicit

    # Action success
    res : list[ABITransactionResponse] = []
    for _ in range(gs_start.delegation_terms_balance.cnt_breach_del_max):
        res.append(delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs))

    # Check return
    amount = calc_operational_fee(
        gs_start.delegation_terms_general.fee_round,
        res[-1].confirmed_round,
        res[-2].confirmed_round,
    )
    validator_earns, platforms_earns = calc_earnings(
       amount=amount,
       commission=action_inputs.delegation_terms_general.commission,
    )

    assert res[-1].return_value == BreachLimitsReturn(
        max_breach_reached=True, # Maximum limit breach events have been reached
        earnings_distribution=[
            validator_earns,
            platforms_earns,
            action_inputs.delegation_terms_general.fee_asset_id,
        ],
        del_manager=gs_start.del_manager,
        msg=list(MSG_CORE_BREACH_LIMITS_END),
    ), ERROR_DELEGATOR_WRONG_EARNINGS_RETURNED

    # Check contract state
    gs_exp = gs_start
    gs_exp.state = STATE_ENDED_LIMITS
    gs_exp.cnt_breach_del = gs_start.delegation_terms_balance.cnt_breach_del_max
    gs_exp.round_claim_last = res[-1].confirmed_round
    gs_exp.round_breach_last = res[-1].confirmed_round
    gs_exp.round_ended = res[-1].confirmed_round
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

def test_already_expired(
    delegator_contract: DelegatorContract,
    dispenser: AddressAndSigner,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    action_inputs.delegation_terms_balance.gating_asa_list[0] = (
        asset,
        round(TestConsts.acc_dispenser_asa_amt / 2),
    )
    action_inputs.delegation_terms_balance.gating_asa_list[1] = (
        asset,
        round(TestConsts.acc_dispenser_asa_amt / 3),
    )
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = delegator_contract.get_global_state()

    if asset != ALGO_ASA_ID:
        # Decrease ASA below the limit
        delegator_contract.algorand_client.send.asset_transfer(
            AssetTransferParams(
                sender = delegator_contract.del_beneficiary.address,
                signer = delegator_contract.del_beneficiary.signer,
                receiver = dispenser.address,
                amount = round(action_inputs.delegation_terms_balance.gating_asa_list[0][1]*4/3),
                asset_id=asset,
            )
        )
    else:
        # Increase ALGO above the limit
        delegator_contract.algorand_client.send.payment(
            PayParams(
                sender = dispenser.address,
                signer = dispenser.signer,
                receiver = delegator_contract.del_beneficiary.address,
                amount = round(action_inputs.delegation_terms_balance.stake_max*2),
            )
        )

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

def test_breach_too_soon(
    delegator_contract: DelegatorContract,
    dispenser: AddressAndSigner,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    action_inputs.delegation_terms_balance.gating_asa_list[0] = (
        asset,
        round(TestConsts.acc_dispenser_asa_amt / 2),
    )
    action_inputs.delegation_terms_balance.gating_asa_list[1] = (
        asset,
        round(TestConsts.acc_dispenser_asa_amt / 3),
    )
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    if asset != ALGO_ASA_ID:
        # Decrease ASA below the limit
        delegator_contract.algorand_client.send.asset_transfer(
            AssetTransferParams(
                sender = delegator_contract.del_beneficiary.address,
                signer = delegator_contract.del_beneficiary.signer,
                receiver = dispenser.address,
                amount = round(action_inputs.delegation_terms_balance.gating_asa_list[0][1]*4/3),
                asset_id=asset,
            )
        )
    else:
        # Increase ALGO above the limit
        delegator_contract.algorand_client.send.payment(
            PayParams(
                sender = dispenser.address,
                signer = dispenser.signer,
                receiver = delegator_contract.del_beneficiary.address,
                amount = round(action_inputs.delegation_terms_balance.stake_max*2),
            )
        )

    action_inputs.wait_until_limit_breach = False

    # Action fail
    with pytest.raises(LogicError) as e:
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_LIMIT_BREACH_TOO_EARLY, e)

    return

def test_no_amount_breach(
    delegator_contract: DelegatorContract,
    dispenser: AddressAndSigner,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    action_inputs.delegation_terms_balance.gating_asa_list[0] = (
        asset,
        round(TestConsts.acc_dispenser_asa_amt / 2),
    )
    action_inputs.delegation_terms_balance.gating_asa_list[1] = (
        asset,
        round(TestConsts.acc_dispenser_asa_amt / 3),
    )
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_IS_STILL_ELIGIBLE, e)

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
    action_inputs.delegation_terms_balance.gating_asa_list[0] = (
        asset,
        round(TestConsts.acc_dispenser_asa_amt / 2),
    )
    action_inputs.delegation_terms_balance.gating_asa_list[1] = (
        asset,
        round(TestConsts.acc_dispenser_asa_amt / 3),
    )
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        delegator_contract.acc = dispenser
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_CALLED_BY_NOT_CREATOR, e)

    return

