
import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.logic_error import LogicError
from algosdk.constants import ZERO_ADDRESS

from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY,
    ERROR_CALLED_BY_NOT_CREATOR,
    ERROR_CALLED_BY_NOT_VAL_OWNER,
    ERROR_NOT_STATE_TEMPLATE_LOAD,
)
from smart_contracts.validator_ad.constants import STATE_TEMPLATE_LOADED
from tests.constants import ERROR_GLOBAL_STATE_MISMATCH, SKIP_SAME_AS_FOR_ALGO
from tests.utils import is_expected_logic_error
from tests.validator_ad.utils import POSSIBLE_STATES, ValidatorAd

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "TEMPLATE_LOAD"
TEST_ACTION_NAME = "template_load_end"

# ------- Tests -------
def test_action(
    validator_ad: ValidatorAd,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = validator_ad.get_global_state()

    # Action
    res = validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    gs_exp.state = STATE_TEMPLATE_LOADED
    assert validator_ad.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    assert validator_ad.app_box(BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY) == [
        bytes(len(validator_ad.template_delegator_contract)),
        True,
    ]

    return

def test_load_and_end(
    validator_ad: ValidatorAd,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    validator_ad.action(action_name="template_load_data", action_inputs=action_inputs)
    gs_start = validator_ad.get_global_state()

    # Action
    res = validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    gs_exp.state = STATE_TEMPLATE_LOADED
    assert validator_ad.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    assert validator_ad.app_box(BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY) == [
        validator_ad.template_delegator_contract,
        True,
    ]

    return

def test_wrong_owner(
    validator_ad: ValidatorAd,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.val_owner = ZERO_ADDRESS
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_CALLED_BY_NOT_VAL_OWNER, e)

    return

def test_wrong_caller(
    validator_ad: ValidatorAd,
    dispenser : AddressAndSigner,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None
    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        validator_ad.acc = dispenser
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_CALLED_BY_NOT_CREATOR, e)

    return

@pytest.mark.parametrize("init_state", [
    "CREATED",
    "TEMPLATE_LOAD",
    "TEMPLATE_LOADED",
    "SET",
    "READY",
    "NOT_READY",
    "NOT_LIVE",
])
def test_state(
    validator_ad: ValidatorAd,
    asset : int,
    init_state : POSSIBLE_STATES,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    validator_ad.initialize_state(target_state=init_state, action_inputs=action_inputs)

    # Action

    if init_state == "TEMPLATE_LOAD":
        # Action success
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

        # Check new state of ValidatorAd - should go to STATE_TEMPLATE_LOADED
        exp_state = STATE_TEMPLATE_LOADED
        gs_end = validator_ad.get_global_state()
        assert gs_end.state == exp_state
    else:
        # Action fail
        with pytest.raises(LogicError) as e:
            validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
        assert is_expected_logic_error(ERROR_NOT_STATE_TEMPLATE_LOAD, e)

    return
