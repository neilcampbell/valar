
import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.logic_error import LogicError
from algosdk.constants import ZERO_ADDRESS

from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_CALLED_BY_NOT_CREATOR,
    ERROR_CALLED_BY_NOT_VAL_OWNER,
    ERROR_CALLED_FROM_STATE_CREATED_TEMPLATE_LOAD_OR_TEMPLATE_LOADED,
    ERROR_NO_MEMORY_FOR_MORE_DELEGATORS,
    MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD,
)
from smart_contracts.validator_ad.constants import (
    STATE_NOT_LIVE,
    STATE_NOT_READY,
)
from tests.constants import ERROR_GLOBAL_STATE_MISMATCH, SKIP_SAME_AS_FOR_AD_LIVE, SKIP_SAME_AS_FOR_ALGO
from tests.utils import is_expected_logic_error
from tests.validator_ad.utils import POSSIBLE_STATES, ValidatorAd

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "SET"
TEST_ACTION_NAME = "ad_config"

@pytest.fixture(scope="module", params=[
    True,
    False,
])
def is_live(request : pytest.FixtureRequest) -> bool:
    return request.param

# ------- Tests -------
def test_action(
    validator_ad: ValidatorAd,
    asset : int,
    is_live : bool,  # noqa: FBT001
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    action_inputs.live = is_live
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = validator_ad.get_global_state()

    # Action
    res = validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    gs_exp.state = STATE_NOT_READY if is_live else STATE_NOT_LIVE
    gs_exp.val_manager = action_inputs.val_manager
    gs_exp.cnt_del_max = action_inputs.cnt_del_max
    assert validator_ad.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

def test_wrong_owner(
    validator_ad: ValidatorAd,
    asset : int,
    is_live : bool,  # noqa: FBT001
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None
    pytest.skip(SKIP_SAME_AS_FOR_AD_LIVE) if not is_live else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    action_inputs.live = is_live
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.val_owner = ZERO_ADDRESS
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_CALLED_BY_NOT_VAL_OWNER, e)

    return

def test_accepting_too_many_delegators(
    validator_ad: ValidatorAd,
    asset : int,
    is_live : bool,  # noqa: FBT001
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None
    pytest.skip(SKIP_SAME_AS_FOR_AD_LIVE) if not is_live else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    action_inputs.live = is_live
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action success
    action_inputs.cnt_del_max = MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD
    validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.cnt_del_max = MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD + 1
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_NO_MEMORY_FOR_MORE_DELEGATORS, e)

    return

def test_wrong_caller(
    validator_ad: ValidatorAd,
    dispenser : AddressAndSigner,
    asset : int,
    is_live : bool,  # noqa: FBT001
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None
    pytest.skip(SKIP_SAME_AS_FOR_AD_LIVE) if not is_live else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    action_inputs.live = is_live
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
@pytest.mark.parametrize("live", [True, False])
def test_state(
    validator_ad: ValidatorAd,
    asset : int,
    init_state : POSSIBLE_STATES,
    live : bool,  # noqa: FBT001
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    action_inputs.live = live
    validator_ad.initialize_state(target_state=init_state, action_inputs=action_inputs)

    # Action

    if init_state not in ["CREATED", "TEMPLATE_LOAD", "TEMPLATE_LOADED"]:
        # Action success
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

        # Check new state of ValidatorAd
        if live:
            exp_state = STATE_NOT_READY
        else:
            exp_state = STATE_NOT_LIVE
        gs_end = validator_ad.get_global_state()
        assert gs_end.state == exp_state
    else:
        # Action fail
        with pytest.raises(LogicError) as e:
            validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
        assert is_expected_logic_error(ERROR_CALLED_FROM_STATE_CREATED_TEMPLATE_LOAD_OR_TEMPLATE_LOADED, e)

    return
