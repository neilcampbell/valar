

import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.logic_error import LogicError
from algosdk.constants import ZERO_ADDRESS
from algosdk.error import AlgodHTTPError

from smart_contracts.artifacts.delegator_contract.client import ContractDeleteReturn
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_CALLED_BY_NOT_CREATOR,
    ERROR_NOT_MANAGER,
)
from tests.constants import SKIP_SAME_AS_FOR_ALGO
from tests.delegator_contract.utils import POSSIBLE_STATES, DelegatorContract
from tests.utils import is_expected_logic_error

from .config import ActionInputs

# ------- Test constants -------
TEST_ACTION_NAME = "contract_delete"

@pytest.fixture(scope="module", params=[
    # "ENDED_CANNOT_PAY",
    "ENDED_EXPIRED",
    # "ENDED_LIMITS",
    "ENDED_NOT_CONFIRMED",
    "ENDED_NOT_SUBMITTED",
    # "ENDED_SUSPENDED",
    "ENDED_WITHDREW",
])
def initial_state(request : pytest.FixtureRequest) -> POSSIBLE_STATES:
    return request.param

# ------- Tests -------
def test_action(
    delegator_contract: DelegatorContract,
    asset : int,
    initial_state : POSSIBLE_STATES,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=initial_state, action_inputs=action_inputs)
    bal = delegator_contract.app_available_balance(asset)

    # Action success
    res = delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.return_value == ContractDeleteReturn(
        remaining_balance=bal,
        asset_id=action_inputs.delegation_terms_general.fee_asset_id,
    ), "Expected different returned amount and its type."

    # Check contract was deleted
    with pytest.raises(AlgodHTTPError):
        app_id = delegator_contract.delegator_contract_client.app_id
        delegator_contract.algorand_client.client.algod.application_info(app_id)

    return

def test_wrong_manager(
    delegator_contract: DelegatorContract,
    asset : int,
    initial_state : POSSIBLE_STATES,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=initial_state, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.del_manager = ZERO_ADDRESS
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_NOT_MANAGER, e)

    return

def test_wrong_caller(
    delegator_contract: DelegatorContract,
    dispenser : AddressAndSigner,
    asset : int,
    initial_state : POSSIBLE_STATES,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.delegation_terms_general.fee_asset_id = asset
    delegator_contract.initialize_state(target_state=initial_state, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        delegator_contract.acc = dispenser
        delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_CALLED_BY_NOT_CREATOR, e)

    return

