

import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.composer import AssetTransferParams, PayParams
from algokit_utils.logic_error import LogicError

from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_ENOUGH_FUNDS_FOR_EARNED_OPERATIONAL_FEE,
    ERROR_ENOUGH_FUNDS_FOR_OPERATIONAL_FEE,
    ERROR_ENOUGH_FUNDS_FOR_SETUP_AND_OPERATIONAL_FEE,
    ERROR_NOT_ENDED_STATE,
    ERROR_NOT_STATE_CREATED,
    ERROR_NOT_STATE_LIVE,
    ERROR_NOT_STATE_LIVE_OR_SUBMITTED_OR_READY,
    ERROR_NOT_STATE_READY,
    ERROR_NOT_STATE_SET,
    ERROR_NOT_STATE_SUBMITTED,
    MBR_ACCOUNT,
)
from tests.conftest import TestConsts
from tests.constants import SKIP_NOT_APPLICABLE_TO_ALGO, SKIP_SAME_AS_FOR_ALGO, SKIP_SAME_AS_FOR_ASA
from tests.delegator_contract.utils import POSSIBLE_ACTIONS, DelegatorContract
from tests.utils import is_expected_logic_error

from .config import ActionInputs

# ------- Test constants -------

ERROR_ACTION_TO_STATE_MAP = {
    # "contract_create": ,
    "contract_setup": [ERROR_NOT_STATE_CREATED],
    "contract_pay" : [ERROR_NOT_STATE_SET],
    "keys_confirm" : [ERROR_NOT_STATE_SUBMITTED],
    "keys_not_confirmed" : [ERROR_NOT_STATE_SUBMITTED],
    "keys_not_submitted" : [ERROR_NOT_STATE_READY],
    "keys_submit" : [ERROR_NOT_STATE_READY],
    "breach_limits" : [ERROR_NOT_STATE_LIVE],
    "breach_pay" : [ERROR_NOT_STATE_LIVE_OR_SUBMITTED_OR_READY],
    "breach_suspended" : [ERROR_NOT_STATE_LIVE],
    "contract_claim" : [ERROR_NOT_STATE_LIVE],
    "contract_expired" : [ERROR_NOT_STATE_LIVE],
    "contract_withdraw" : [ERROR_NOT_STATE_LIVE],
    "contract_report_expiry_soon" : [ERROR_NOT_STATE_LIVE],
    "contract_delete" : [ERROR_NOT_ENDED_STATE],
}

@pytest.fixture(scope="module", params=[
    # "contract_create",
    "contract_setup",
    "contract_pay",
    "keys_confirm",
    "keys_not_confirmed",
    "keys_not_submitted",
    "keys_submit",
    "breach_limits",
    "breach_pay",
    "breach_suspended",
    "contract_claim",
    "contract_expired",
    "contract_withdraw",
    "contract_delete",
    "contract_report_expiry_soon",
])
def action_name(request : pytest.FixtureRequest) -> POSSIBLE_ACTIONS:
    return request.param

# ------- Tests -------
def test_state_created(
    delegator_contract: DelegatorContract,
    asset : int,
    action_name : POSSIBLE_ACTIONS,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.key_reg_before_confirm = False  # Otherwise keys_confirm fails because no info to fetch for key reg
    delegator_contract.initialize_state(target_state="CREATED", action_inputs=action_inputs)

    if action_name != "contract_setup":
        # Fund contract with MBR
        amount = MBR_ACCOUNT
        delegator_contract.algorand_client.send.payment(
            PayParams(
                sender = delegator_contract.acc.address,
                signer = delegator_contract.acc.signer,
                receiver = delegator_contract.delegator_contract_client.app_address,
                amount = amount,
            )
        )
        with pytest.raises(LogicError) as e:
            delegator_contract.action(action_name=action_name, action_inputs=action_inputs)
        assert any(is_expected_logic_error(state, e) for state in ERROR_ACTION_TO_STATE_MAP[action_name])

    else:
        # Action success
        res = delegator_contract.action(action_name=action_name, action_inputs=action_inputs)
        assert res.confirmed_round

    return

def test_state_set(
    delegator_contract: DelegatorContract,
    asset : int,
    action_name : POSSIBLE_ACTIONS,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.key_reg_before_confirm = False  # Otherwise keys_confirm fails because no info to fetch for key reg
    delegator_contract.initialize_state(target_state="SET", action_inputs=action_inputs)

    if action_name != "contract_pay":
        with pytest.raises(LogicError) as e:
            delegator_contract.action(action_name=action_name, action_inputs=action_inputs)
        assert any(is_expected_logic_error(state, e) for state in ERROR_ACTION_TO_STATE_MAP[action_name])

    else:
        # Action success
        res = delegator_contract.action(action_name=action_name, action_inputs=action_inputs)
        assert res.confirmed_round

    return

def test_state_ready(
    delegator_contract: DelegatorContract,
    asset : int,
    action_name : POSSIBLE_ACTIONS,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ASA) if asset == ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    action_inputs.key_reg_before_confirm = False  # Otherwise keys_confirm fails because no info to fetch for key reg
    delegator_contract.initialize_state(target_state="READY", action_inputs=action_inputs)

    if action_name not in ["keys_not_submitted", "keys_submit", "breach_pay"]:
        with pytest.raises(LogicError) as e:
            delegator_contract.action(action_name=action_name, action_inputs=action_inputs)
        assert any(is_expected_logic_error(state, e) for state in ERROR_ACTION_TO_STATE_MAP[action_name])

    elif action_name == "breach_pay":
        # For simplicity because automatic clawback has not be enabled for breach_pay action
        with pytest.raises(LogicError) as e:
            delegator_contract.action(action_name=action_name, action_inputs=action_inputs)
        assert is_expected_logic_error(ERROR_ENOUGH_FUNDS_FOR_SETUP_AND_OPERATIONAL_FEE, e)

    else:
        # Action success
        res = delegator_contract.action(action_name=action_name, action_inputs=action_inputs)
        assert res.confirmed_round

    return

def test_state_submitted(
    delegator_contract: DelegatorContract,
    asset : int,
    action_name : POSSIBLE_ACTIONS,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ASA) if asset == ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state="SUBMITTED", action_inputs=action_inputs)

    if action_name not in ["keys_confirm", "keys_not_confirmed", "breach_pay"]:
        with pytest.raises(LogicError) as e:
            delegator_contract.action(action_name=action_name, action_inputs=action_inputs)
        assert any(is_expected_logic_error(state, e) for state in ERROR_ACTION_TO_STATE_MAP[action_name])

    elif action_name == "breach_pay":
        # For simplicity because automatic clawback has not be enabled for breach_pay action
        with pytest.raises(LogicError) as e:
            delegator_contract.action(action_name=action_name, action_inputs=action_inputs)
        assert is_expected_logic_error(ERROR_ENOUGH_FUNDS_FOR_OPERATIONAL_FEE, e)

    else:
        # Action success
        res = delegator_contract.action(action_name=action_name, action_inputs=action_inputs)
        assert res.confirmed_round

    return

def test_state_live(
    delegator_contract: DelegatorContract,
    dispenser : AddressAndSigner,
    asset : int,
    action_name : POSSIBLE_ACTIONS,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    if action_name == "breach_limits":
        action_inputs.delegation_terms_balance.gating_asa_list[0]=(
            asset,
            round(TestConsts.acc_dispenser_asa_amt),
        )
    delegator_contract.initialize_state(target_state="LIVE", action_inputs=action_inputs)
    if action_name == "breach_limits":
        pytest.skip(SKIP_SAME_AS_FOR_ASA) if asset == ALGO_ASA_ID else None
        # Decrease ASA below the limit
        delegator_contract.algorand_client.send.asset_transfer(
            AssetTransferParams(
                sender = delegator_contract.del_beneficiary.address,
                signer = delegator_contract.del_beneficiary.signer,
                receiver = dispenser.address,
                amount = round(action_inputs.delegation_terms_balance.gating_asa_list[0][1]/2),
                asset_id=asset,
            )
        )

    if action_name not in [
        "breach_limits",
        "breach_pay",
        "breach_suspended",
        "contract_claim",
        "contract_expired",
        "contract_withdraw",
        "contract_report_expiry_soon",
    ]:
        pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

        with pytest.raises(LogicError) as e:
            delegator_contract.action(action_name=action_name, action_inputs=action_inputs)
        assert any(is_expected_logic_error(state, e) for state in ERROR_ACTION_TO_STATE_MAP[action_name])

    elif action_name == "breach_pay":
        pytest.skip(SKIP_NOT_APPLICABLE_TO_ALGO) if asset == ALGO_ASA_ID else None
        # For simplicity because automatic clawback has not be enabled for breach_pay action
        with pytest.raises(LogicError) as e:
            delegator_contract.action(action_name=action_name, action_inputs=action_inputs)
        assert is_expected_logic_error(ERROR_ENOUGH_FUNDS_FOR_EARNED_OPERATIONAL_FEE, e)

    else:
        if action_name == "breach_suspended":
            action_inputs.wait_until_suspended = True
            pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

        # Action success
        res = delegator_contract.action(action_name=action_name, action_inputs=action_inputs)
        assert res.confirmed_round

    return
