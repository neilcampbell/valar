

import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.composer import AssetFreezeParams, AssetTransferParams, PayParams
from algokit_utils.logic_error import LogicError
from algosdk.atomic_transaction_composer import (
    TransactionWithSigner,
)

from smart_contracts.artifacts.delegator_contract.client import EarningsDistribution
from smart_contracts.delegator_contract.constants import (
    STATE_LIVE,
)
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_BALANCE_FROZEN,
    ERROR_CALLED_BY_NOT_CREATOR,
    ERROR_INSUFFICIENT_BALANCE,
    ERROR_OPERATION_FEE_ALREADY_CLAIMED_AT_ROUND,
)
from tests.constants import (
    ERROR_DELEGATOR_OPERATIONAL_FEE_NOT_REMAINING,
    ERROR_GLOBAL_STATE_MISMATCH,
    SKIP_NOT_APPLICABLE_TO_ALGO,
    SKIP_SAME_AS_FOR_ALGO,
)
from tests.delegator_contract.utils import DelegatorContract
from tests.utils import available_balance, calc_earnings, calc_operational_fee, is_expected_logic_error, wait_for_rounds

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "LIVE"
TEST_ACTION_NAME = "contract_claim"

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
    # Wait some rounds to have something to claim
    gs_start = delegator_contract.get_global_state()
    status = delegator_contract.algorand_client.client.algod.status()
    current_round = status["last-round"]
    num_rounds = gs_start.round_end - current_round - 11
    wait_for_rounds(
        algorand_client=delegator_contract.algorand_client,
        num_rounds=num_rounds,
        acc=delegator_contract.acc,
    )

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
       commission=gs_start.delegation_terms_general.commission,
    )

    assert res.return_value == EarningsDistribution(
        user=validator_earns,
        platform=platforms_earns,
        asset_id=action_inputs.delegation_terms_general.fee_asset_id,
    )

    # Check contract state
    gs_exp = gs_start
    gs_exp.state = STATE_LIVE
    gs_exp.round_claim_last = res.confirmed_round
    assert delegator_contract.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check if earnings were NOT distributed because calling apps are not existent
    assert delegator_contract.app_available_balance(asset) == \
        gs_start.fee_operational + gs_start.delegation_terms_general.fee_setup, \
        ERROR_DELEGATOR_OPERATIONAL_FEE_NOT_REMAINING

    return

def test_subsequent_multi_claim(
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
    first_claim_round = res.confirmed_round
    amount = calc_operational_fee(
        gs_start.delegation_terms_general.fee_round,
        first_claim_round,
        gs_start.round_start,
    )
    validator_earns, platforms_earns = calc_earnings(
       amount=amount,
       commission=gs_start.delegation_terms_general.commission,
    )

    assert res.return_value == EarningsDistribution(
        user=validator_earns,
        platform=platforms_earns,
        asset_id=action_inputs.delegation_terms_general.fee_asset_id,
    )

    # Wait some round before claiming again
    wait_rounds = 13
    gs_start = delegator_contract.get_global_state()
    status = delegator_contract.algorand_client.client.algod.status()
    current_round = status["last-round"]
    num_rounds = gs_start.round_end - current_round - wait_rounds
    wait_for_rounds(
        algorand_client=delegator_contract.algorand_client,
        num_rounds=num_rounds,
        acc=delegator_contract.acc,
    )

    # Action success
    res = delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    amount = calc_operational_fee(
        gs_start.delegation_terms_general.fee_round,
        res.confirmed_round,
        first_claim_round,
    )
    validator_earns, platforms_earns = calc_earnings(
       amount=amount,
       commission=gs_start.delegation_terms_general.commission,
    )

    assert res.return_value == EarningsDistribution(
        user=validator_earns,
        platform=platforms_earns,
        asset_id=action_inputs.delegation_terms_general.fee_asset_id,
    )

    # Check contract state
    gs_exp = gs_start
    gs_exp.state = STATE_LIVE
    gs_exp.round_claim_last = res.confirmed_round
    assert delegator_contract.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check if earnings were NOT distributed because calling apps are not existent
    assert delegator_contract.app_available_balance(asset) == \
        gs_start.fee_operational + gs_start.delegation_terms_general.fee_setup, \
        ERROR_DELEGATOR_OPERATIONAL_FEE_NOT_REMAINING

    return

def test_same_round_multi_claim(
    delegator_contract: DelegatorContract,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        # Increase fee for (potential) distribution of earnings
        sp = delegator_contract.algorand_client.client.algod.suggested_params()
        sp.fee = 3 * sp.min_fee
        sp.flat_fee = True
        # Add asset to the foreign asset array
        if action_inputs.delegation_terms_general.fee_asset_id != ALGO_ASA_ID:
            foreign_assets = [action_inputs.delegation_terms_general.fee_asset_id]
        else:
            foreign_assets = None

        # Create an atomic transaction composer to enforce all transactions within same block
        # In reality they could be independent
        composer = delegator_contract.delegator_contract_client.compose()

        # First claim
        composer.contract_claim(
            transaction_parameters = TransactionParameters(
                sender = delegator_contract.acc.address,
                signer = delegator_contract.acc.signer,
                suggested_params=sp,
                foreign_assets=foreign_assets,
                lease=bytes([0] * 31 + [1]),   # Needed to make transaction unique
            ),
        )

        # Random transaction
        txn = TransactionWithSigner(
            delegator_contract.algorand_client.transactions.payment(
                PayParams(
                    sender=delegator_contract.acc.address,
                    receiver=delegator_contract.acc.address,
                    amount=0,
                    extra_fee=0,
                )
            ),
            signer=delegator_contract.acc.signer,
        )
        composer.build().add_transaction(txn)

        # Second claim within the same block, which causes failure of whole group
        composer.contract_claim(
            transaction_parameters = TransactionParameters(
                sender = delegator_contract.acc.address,
                signer = delegator_contract.acc.signer,
                suggested_params=sp,
                foreign_assets=foreign_assets,
                lease=bytes([0] * 31 + [2]),   # Needed to make transaction unique
            ),
        )

        composer.execute()

    assert is_expected_logic_error(ERROR_OPERATION_FEE_ALREADY_CLAIMED_AT_ROUND, e)

    return

def test_claim_after_expiry(
    delegator_contract: DelegatorContract,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = delegator_contract.get_global_state()

    # Wait until contract expires
    gs_start = delegator_contract.get_global_state()
    status = delegator_contract.algorand_client.client.algod.status()
    current_round = status["last-round"]
    num_rounds = gs_start.round_end + 42 - current_round
    wait_for_rounds(
        algorand_client=delegator_contract.algorand_client,
        num_rounds=num_rounds,
        acc=delegator_contract.acc,
    )

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
       commission=gs_start.delegation_terms_general.commission,
    )

    assert res.return_value == EarningsDistribution(
        user=validator_earns,
        platform=platforms_earns,
        asset_id=action_inputs.delegation_terms_general.fee_asset_id,
    )

    # Check if earnings were NOT distributed because calling apps are not existent
    assert delegator_contract.app_available_balance(asset) == \
        gs_start.fee_operational + gs_start.delegation_terms_general.fee_setup, \
        ERROR_DELEGATOR_OPERATIONAL_FEE_NOT_REMAINING

    return

def test_claim_after_expiry_twice(
    delegator_contract: DelegatorContract,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = delegator_contract.get_global_state()

    # Wait until contract expires
    gs_start = delegator_contract.get_global_state()
    status = delegator_contract.algorand_client.client.algod.status()
    current_round = status["last-round"]
    num_rounds = gs_start.round_end + 42 - current_round
    wait_for_rounds(
        algorand_client=delegator_contract.algorand_client,
        num_rounds=num_rounds,
        acc=delegator_contract.acc,
    )

    # Claim first time after expiry
    delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Wait some round before claiming again
    wait_rounds = 13
    wait_for_rounds(
        algorand_client=delegator_contract.algorand_client,
        num_rounds=wait_rounds,
        acc=delegator_contract.acc,
    )

    # Action success
    res = delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    validator_earns = 0
    platforms_earns = 0

    assert res.return_value == EarningsDistribution(
        user=validator_earns,
        platform=platforms_earns,
        asset_id=action_inputs.delegation_terms_general.fee_asset_id,
    )

    # Check contract state
    gs_exp = gs_start
    gs_exp.state = STATE_LIVE
    gs_exp.round_claim_last = gs_start.round_end
    assert delegator_contract.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check if earnings were NOT distributed because calling apps are not existent
    assert delegator_contract.app_available_balance(asset) == \
        gs_start.fee_operational + gs_start.delegation_terms_general.fee_setup, \
        ERROR_DELEGATOR_OPERATIONAL_FEE_NOT_REMAINING

    return

def test_contract_frozen(
    delegator_contract: DelegatorContract,
    dispenser : AddressAndSigner,
    asset : int,
) -> None:

    pytest.skip(SKIP_NOT_APPLICABLE_TO_ALGO) if asset == ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    delegator_contract.algorand_client.send.asset_freeze(
        AssetFreezeParams(
            sender=dispenser.address,
            asset_id=asset,
            account=delegator_contract.delegator_contract_client.app_address,
            frozen=True,
            signer=dispenser.signer,
        )
    )

    # Action fail
    with pytest.raises(LogicError) as e:
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_BALANCE_FROZEN, e)

    return

def test_contract_clawed(
    delegator_contract: DelegatorContract,
    dispenser : AddressAndSigner,
    asset : int,
) -> None:

    pytest.skip(SKIP_NOT_APPLICABLE_TO_ALGO) if asset == ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs = delegator_contract.get_global_state()
    status = delegator_contract.algorand_client.client.algod.status()
    current_round = status["last-round"]

    # For the tests, the clawed amount must be larger than the sum of the setup fee, which has stayed at the contract
    # because Noticeboard and ValidatorAd apps are not existent in this test, and the amount that should be claimable
    # to the moment of transaction execution (which is after two blocks from the setup transaction due to transaction
    # for clawback and the call transaction, which are in two separate blocks).
    amt = gs.delegation_terms_general.fee_setup + calc_operational_fee(
        gs.delegation_terms_general.fee_round,
        gs.round_end,
        (current_round+2),
    ) + 1

    delegator_contract.algorand_client.send.asset_transfer(
        AssetTransferParams(
            sender=dispenser.address,
            asset_id=asset,
            amount=amt,
            receiver=dispenser.address,
            signer=dispenser.signer,
            clawback_target=delegator_contract.delegator_contract_client.app_address,
        )
    )

    # Action fail
    with pytest.raises(LogicError) as e:
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_INSUFFICIENT_BALANCE, e)

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
    partner : AddressAndSigner,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    action_inputs.delegation_terms_general.partner_address = partner.address
    action_inputs.delegation_terms_general.fee_round_partner = 543
    action_inputs.delegation_terms_general.fee_setup_partner = 278

    partner_bal_start = available_balance(
        algorand_client=delegator_contract.algorand_client,
        address=action_inputs.delegation_terms_general.partner_address,
        asset_id=asset,
    )

    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = delegator_contract.get_global_state()
    # Wait some rounds to have something to claim
    gs_start = delegator_contract.get_global_state()
    status = delegator_contract.algorand_client.client.algod.status()
    current_round = status["last-round"]
    num_rounds = gs_start.round_end - current_round - 11
    wait_for_rounds(
        algorand_client=delegator_contract.algorand_client,
        num_rounds=num_rounds,
        acc=delegator_contract.acc,
    )

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
       commission=gs_start.delegation_terms_general.commission,
    )
    amount_partner = calc_operational_fee(
        action_inputs.delegation_terms_general.fee_round_partner,
        res.confirmed_round,
        gs_start.round_start,
    )
    amount_partner_remain = gs_start.fee_operational_partner - amount_partner

    assert res.return_value == EarningsDistribution(
        user=validator_earns,
        platform=platforms_earns,
        asset_id=action_inputs.delegation_terms_general.fee_asset_id,
    )

    # Check contract state
    gs_exp = gs_start
    gs_exp.state = STATE_LIVE
    gs_exp.round_claim_last = res.confirmed_round
    assert delegator_contract.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check if partner fee was paid but earnings were NOT distributed because calling apps are not existent
    assert delegator_contract.app_available_balance(asset) == \
        amount_partner_remain + gs_start.fee_operational + gs_start.delegation_terms_general.fee_setup, \
        ERROR_DELEGATOR_OPERATIONAL_FEE_NOT_REMAINING

    # Check if partner received the partner fee
    partner_bal_end = available_balance(
        algorand_client=delegator_contract.algorand_client,
        address=action_inputs.delegation_terms_general.partner_address,
        asset_id=asset,
    )
    assert partner_bal_end == partner_bal_start + \
        amount_partner + action_inputs.delegation_terms_general.fee_setup_partner, \
        ERROR_DELEGATOR_OPERATIONAL_FEE_NOT_REMAINING

    return

def test_action_w_partner_closed_or_frozen(
    delegator_contract: DelegatorContract,
    partner : AddressAndSigner,
    dispenser : AddressAndSigner,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    action_inputs.delegation_terms_general.partner_address = partner.address
    action_inputs.delegation_terms_general.fee_round_partner = 543
    action_inputs.delegation_terms_general.fee_setup_partner = 278

    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = delegator_contract.get_global_state()
    # Wait some rounds to have something to claim
    gs_start = delegator_contract.get_global_state()
    status = delegator_contract.algorand_client.client.algod.status()
    current_round = status["last-round"]
    num_rounds = gs_start.round_end - current_round - 11
    wait_for_rounds(
        algorand_client=delegator_contract.algorand_client,
        num_rounds=num_rounds,
        acc=delegator_contract.acc,
    )

    if asset == ALGO_ASA_ID:
        delegator_contract.algorand_client.send.payment(
            PayParams(
                sender=partner.address,
                receiver=dispenser.address,
                amount=0,
                close_remainder_to=dispenser.address,
            )
        )
    else:
        delegator_contract.algorand_client.send.asset_freeze(
            AssetFreezeParams(
                sender=dispenser.address,
                asset_id=asset,
                account=partner.address,
                frozen=True,
                signer=dispenser.signer,
            )
        )

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
       commission=gs_start.delegation_terms_general.commission,
    )
    amount_partner_remain = gs_start.fee_operational_partner

    assert res.return_value == EarningsDistribution(
        user=validator_earns,
        platform=platforms_earns,
        asset_id=action_inputs.delegation_terms_general.fee_asset_id,
    )

    # Check contract state
    gs_exp = gs_start
    gs_exp.state = STATE_LIVE
    gs_exp.round_claim_last = res.confirmed_round
    assert delegator_contract.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check if partner fee was paid but earnings were NOT distributed because calling apps are not existent
    assert delegator_contract.app_available_balance(asset) == \
        amount_partner_remain + gs_start.fee_operational + gs_start.delegation_terms_general.fee_setup, \
        ERROR_DELEGATOR_OPERATIONAL_FEE_NOT_REMAINING

    return
