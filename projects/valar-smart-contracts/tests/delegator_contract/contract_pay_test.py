
import pytest
from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.composer import AssetTransferParams, OnlineKeyRegParams, PayParams
from algokit_utils.logic_error import LogicError
from algosdk.atomic_transaction_composer import (
    TransactionWithSigner,
)

from smart_contracts.delegator_contract.constants import (
    STATE_READY,
)
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_AMOUNT,
    ERROR_ASSET_ID,
    ERROR_CALLED_BY_NOT_CREATOR,
    ERROR_NOT_ELIGIBLE,
    ERROR_NOT_PAYMENT_OR_XFER,
    ERROR_RECEIVER,
)
from tests.conftest import TestConsts
from tests.constants import ERROR_GLOBAL_STATE_MISMATCH, SKIP_SAME_AS_FOR_ALGO, SKIP_SAME_AS_FOR_ASA
from tests.delegator_contract.utils import DelegatorContract
from tests.utils import is_expected_logic_error

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "SET"
TEST_ACTION_NAME = "contract_pay"

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

    # Action success
    res = delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    gs_exp.state = STATE_READY
    assert delegator_contract.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check if (available) balance is correct
    paid = action_inputs.delegation_terms_general.fee_setup + action_inputs.fee_operational
    assert delegator_contract.app_available_balance(asset) == paid

    return

def test_incorrect_balance(
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

    # Action fail
    with pytest.raises(LogicError) as e:
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_NOT_ELIGIBLE, e)

    return

def test_wrong_input_transaction(
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
        status = delegator_contract.algorand_client.client.algod.status()
        current_round = status["last-round"]
        txn = TransactionWithSigner(
            delegator_contract.algorand_client.transactions.online_key_reg(
                OnlineKeyRegParams(
                    sender = delegator_contract.acc.address,
                    vote_key = action_inputs.key_reg_vote,
                    selection_key = action_inputs.key_reg_selection,
                    state_proof_key = action_inputs.key_reg_state_proof,
                    vote_first = current_round,
                    vote_last = current_round + 42,
                    vote_key_dilution = 2,
                )
            ),
            signer=delegator_contract.acc.signer,
        )

        delegator_contract.delegator_contract_client.contract_pay(
            txn = txn,
            transaction_parameters = TransactionParameters(
                sender = delegator_contract.acc.address,
                signer = delegator_contract.acc.signer,
            ),
        )

    assert is_expected_logic_error(ERROR_NOT_PAYMENT_OR_XFER, e)

    return

def test_wrong_receiver(
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
        action_inputs.receiver = delegator_contract.acc.address
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_RECEIVER, e)

    return

def test_wrong_asset(
    delegator_contract: DelegatorContract,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ASA) if asset == ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    if asset != ALGO_ASA_ID:
        with pytest.raises(LogicError) as e:
            action_inputs.delegation_terms_general.fee_asset_id = ALGO_ASA_ID
            delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

        assert is_expected_logic_error(ERROR_ASSET_ID, e)

    return

def test_wrong_amount(
    delegator_contract: DelegatorContract,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.amount = 1
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_AMOUNT, e)

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

