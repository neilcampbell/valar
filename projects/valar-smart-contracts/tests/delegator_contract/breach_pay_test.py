

from typing import Literal

import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.composer import AssetFreezeParams, AssetTransferParams
from algokit_utils.logic_error import LogicError

from smart_contracts.artifacts.delegator_contract.client import Message
from smart_contracts.delegator_contract.constants import (
    STATE_ENDED_CANNOT_PAY,
)
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_ALGO_IS_PERMISSIONLESS,
    ERROR_BALANCE_FROZEN,
    ERROR_CALLED_BY_NOT_CREATOR,
    ERROR_ENOUGH_FUNDS_FOR_EARNED_OPERATIONAL_FEE,
    ERROR_ENOUGH_FUNDS_FOR_OPERATIONAL_FEE,
    ERROR_ENOUGH_FUNDS_FOR_SETUP_AND_OPERATIONAL_FEE,
    ERROR_INSUFFICIENT_BALANCE,
    MSG_CORE_BREACH_PAY,
)
from tests.constants import (
    ERROR_DELEGATOR_WRONG_EARNINGS_RETURNED,
    ERROR_GLOBAL_STATE_MISMATCH,
    ERROR_TEST_ERROR,
    SKIP_NOT_APPLICABLE_TO_ALGO,
)
from tests.delegator_contract.utils import POSSIBLE_STATES, DelegatorContract
from tests.utils import is_expected_logic_error, wait_for_rounds

from .config import ActionInputs

# ------- Test constants -------
TEST_ACTION_NAME = "breach_pay"

PAY_BREACH_SUBTYPE = Literal[
    "FROZEN",
    "CLAWED",
]

@pytest.fixture(scope="module", params=[
    "LIVE",
    "SUBMITTED",
    "READY",
])
def initial_state(request : pytest.FixtureRequest) -> POSSIBLE_STATES:
    return request.param

@pytest.fixture(scope="module", params=[
    "FROZEN",
    "CLAWED",
])
def pay_breach_type(request : pytest.FixtureRequest) -> PAY_BREACH_SUBTYPE:
    return request.param

# ------- Tests -------
def test_action(
    delegator_contract: DelegatorContract,
    asset : int,
    dispenser : AddressAndSigner,
    initial_state : POSSIBLE_STATES,
    pay_breach_type : PAY_BREACH_SUBTYPE,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=initial_state, action_inputs=action_inputs)
    gs_start = delegator_contract.get_global_state()

    if asset == ALGO_ASA_ID:
        # Action fail
        with pytest.raises(LogicError) as e:
            delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

        assert is_expected_logic_error(ERROR_ALGO_IS_PERMISSIONLESS, e)

    else:
        if pay_breach_type == "FROZEN":
            # Freeze contract account
            delegator_contract.algorand_client.send.asset_freeze(
                AssetFreezeParams(
                    sender=dispenser.address,
                    asset_id=asset,
                    account=delegator_contract.delegator_contract_client.app_address,
                    frozen=True,
                    signer=dispenser.signer,
                )
            )

        elif pay_breach_type == "CLAWED":
            # Claw back from contract account
            # For test simplicity, claw back the full amount
            amt = delegator_contract.app_available_balance(asset)

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
        else:
            raise Exception(ERROR_TEST_ERROR)

        # Action success
        res = delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

        # Check return
        assert res.return_value == Message(
            del_manager=gs_start.del_manager,
            msg=list(MSG_CORE_BREACH_PAY),
        ), ERROR_DELEGATOR_WRONG_EARNINGS_RETURNED

        # Check contract state
        gs_exp = gs_start
        gs_exp.state = STATE_ENDED_CANNOT_PAY
        gs_exp.round_ended = res.confirmed_round
        assert delegator_contract.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    return

def test_payment_possible(
    delegator_contract: DelegatorContract,
    asset : int,
    initial_state : POSSIBLE_STATES,
) -> None:
    """
    Test failure of reporting of payment breach if asset is not frozen or clawed.
    """

    pytest.skip(SKIP_NOT_APPLICABLE_TO_ALGO) if asset == ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=initial_state, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    if initial_state == "READY":
        assert is_expected_logic_error(ERROR_ENOUGH_FUNDS_FOR_SETUP_AND_OPERATIONAL_FEE, e)
    elif initial_state == "SUBMITTED":
        assert is_expected_logic_error(ERROR_ENOUGH_FUNDS_FOR_OPERATIONAL_FEE, e)
    elif initial_state == "LIVE":
        assert is_expected_logic_error(ERROR_ENOUGH_FUNDS_FOR_EARNED_OPERATIONAL_FEE, e)
    else:
        raise Exception(ERROR_TEST_ERROR)

    return

def test_after_expiry(
    delegator_contract: DelegatorContract,
    asset : int,
    dispenser : AddressAndSigner,
    pay_breach_type : PAY_BREACH_SUBTYPE,
) -> None:
    """
    Test reporting of payment breach after unsuccessful reporting of contract expiry due to frozen or clawed asset.
    """

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state="LIVE", action_inputs=action_inputs)

    if asset == ALGO_ASA_ID:
        # Action fail
        with pytest.raises(LogicError) as e:
            delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

        assert is_expected_logic_error(ERROR_ALGO_IS_PERMISSIONLESS, e)

    else:
        gs_start = delegator_contract.get_global_state()
        # Wait until contract expires
        status = delegator_contract.algorand_client.client.algod.status()
        current_round = status["last-round"]
        num_rounds = (gs_start.round_end+42) - current_round
        wait_for_rounds(
            algorand_client=delegator_contract.algorand_client,
            num_rounds=num_rounds,
            acc=delegator_contract.acc,
        )

        if pay_breach_type == "FROZEN":
            # Freeze contract account
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
                # Try to report expired
                delegator_contract.action(action_name="contract_expired", action_inputs=action_inputs)

            assert is_expected_logic_error(ERROR_BALANCE_FROZEN, e)

        elif pay_breach_type == "CLAWED":
            # Claw back from contract account
            # For test simplicity, claw back the full amount
            amt = delegator_contract.app_available_balance(asset)

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
                # Try to report expired
                delegator_contract.action(action_name="contract_expired", action_inputs=action_inputs)

            assert is_expected_logic_error(ERROR_INSUFFICIENT_BALANCE, e)

        else:
            raise Exception("Error in test!")

        # Action success
        res = delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

        # Check return
        assert res.return_value == Message(
            del_manager=gs_start.del_manager,
            msg=list(MSG_CORE_BREACH_PAY),
        ), ERROR_DELEGATOR_WRONG_EARNINGS_RETURNED

        # Check contract state
        gs_exp = gs_start
        gs_exp.state = STATE_ENDED_CANNOT_PAY
        gs_exp.round_ended = res.confirmed_round
        assert delegator_contract.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    return

def test_wrong_caller(
    delegator_contract: DelegatorContract,
    dispenser : AddressAndSigner,
    asset : int,
    initial_state : POSSIBLE_STATES,
    pay_breach_type : PAY_BREACH_SUBTYPE,
) -> None:

    pytest.skip(SKIP_NOT_APPLICABLE_TO_ALGO) if asset == ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=initial_state, action_inputs=action_inputs)

    if pay_breach_type == "FROZEN":
        # Freeze contract account
        delegator_contract.algorand_client.send.asset_freeze(
            AssetFreezeParams(
                sender=dispenser.address,
                asset_id=asset,
                account=delegator_contract.delegator_contract_client.app_address,
                frozen=True,
                signer=dispenser.signer,
            )
        )

    elif pay_breach_type == "CLAWED":
        # Claw back from contract account
        # For test simplicity, claw back the full amount
        amt = delegator_contract.app_available_balance(asset)

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
    else:
        raise Exception(ERROR_TEST_ERROR)

    # Action fail
    with pytest.raises(LogicError) as e:
        delegator_contract.acc = dispenser
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_CALLED_BY_NOT_CREATOR, e)

    return

def test_action_w_partner(
    delegator_contract: DelegatorContract,
    asset : int,
    del_manager: AddressAndSigner,
    dispenser : AddressAndSigner,
    partner : AddressAndSigner,
    initial_state : POSSIBLE_STATES,
    pay_breach_type : PAY_BREACH_SUBTYPE,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    action_inputs.del_manager = del_manager.address
    action_inputs.delegation_terms_general.partner_address = partner.address
    action_inputs.delegation_terms_general.fee_round_partner = 543
    action_inputs.delegation_terms_general.fee_setup_partner = 278
    delegator_contract.initialize_state(target_state=initial_state, action_inputs=action_inputs)
    gs_start = delegator_contract.get_global_state()

    if asset == ALGO_ASA_ID:
        # Action fail
        with pytest.raises(LogicError) as e:
            delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

        assert is_expected_logic_error(ERROR_ALGO_IS_PERMISSIONLESS, e)

    else:
        if pay_breach_type == "FROZEN":
            # Freeze contract account
            delegator_contract.algorand_client.send.asset_freeze(
                AssetFreezeParams(
                    sender=dispenser.address,
                    asset_id=asset,
                    account=delegator_contract.delegator_contract_client.app_address,
                    frozen=True,
                    signer=dispenser.signer,
                )
            )

        elif pay_breach_type == "CLAWED":
            # Claw back from contract account
            # For test simplicity, claw back the full amount
            amt = delegator_contract.app_available_balance(asset)

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
        else:
            raise Exception(ERROR_TEST_ERROR)

        # Action success
        res = delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

        # Check return
        assert res.return_value == Message(
            del_manager=gs_start.del_manager,
            msg=list(MSG_CORE_BREACH_PAY),
        ), ERROR_DELEGATOR_WRONG_EARNINGS_RETURNED

        # Check contract state
        gs_exp = gs_start
        gs_exp.state = STATE_ENDED_CANNOT_PAY
        gs_exp.round_ended = res.confirmed_round
        assert delegator_contract.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    return
