
from smart_contracts.delegator_contract.constants import (
    STATE_CREATED,
)
from tests.constants import ERROR_GLOBAL_STATE_MISMATCH
from tests.delegator_contract.utils import DelegatorContract

from .client_helper import DelegatorContractGlobalState
from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = None
TEST_ACTION_NAME = "contract_create"

# ------- Tests -------
def test_action(
    delegator_contract: DelegatorContract,
) -> None:

    # Setup
    action_inputs = ActionInputs()

    # Action
    res = delegator_contract.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.return_value != 0, "App was not created."

    # Check contract state
    gs_exp = DelegatorContractGlobalState(
        del_beneficiary = delegator_contract.del_beneficiary.address,
        del_manager = delegator_contract.del_manager.address,
        state = STATE_CREATED,
    )
    assert delegator_contract.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    return
