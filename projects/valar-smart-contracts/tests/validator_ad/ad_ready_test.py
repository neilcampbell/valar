
import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.logic_error import LogicError
from algosdk.constants import ZERO_ADDRESS

from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_CALLED_BY_NOT_CREATOR,
    ERROR_CALLED_BY_NOT_VAL_MANAGER,
    ERROR_NOT_STATE_READY_OR_NOT_READY,
)
from smart_contracts.validator_ad.constants import (
    STATE_NOT_READY,
    STATE_READY,
)
from tests.constants import (
    ERROR_GLOBAL_STATE_MISMATCH,
    SKIP_SAME_AS_FOR_AD_READY,
    SKIP_SAME_AS_FOR_AD_STATE_READY,
    SKIP_SAME_AS_FOR_ALGO,
)
from tests.utils import is_expected_logic_error
from tests.validator_ad.utils import POSSIBLE_STATES, ValidatorAd

from .config import ActionInputs

# ------- Test constants -------
TEST_ACTION_NAME = "ad_ready"

@pytest.fixture(scope="module", params=[
    "READY",
    "NOT_READY",
])
def initial_state(request : pytest.FixtureRequest) -> str:
    return request.param

@pytest.fixture(scope="module", params=[
    True,
    False,
])
def is_ready(request : pytest.FixtureRequest) -> bool:
    return request.param
# ------- Tests -------
def test_action(
    validator_ad: ValidatorAd,
    asset : int,
    initial_state : str,
    is_ready : bool,  # noqa: FBT001
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    action_inputs.ready = is_ready
    validator_ad.initialize_state(target_state=initial_state, action_inputs=action_inputs)
    gs_start = validator_ad.get_global_state()

    # Action
    res = validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    gs_exp.state = STATE_NOT_READY if not is_ready else STATE_READY
    assert validator_ad.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

def test_wrong_manager(
    validator_ad: ValidatorAd,
    asset : int,
    is_ready : bool,  # noqa: FBT001
    initial_state : str,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None
    pytest.skip(SKIP_SAME_AS_FOR_AD_READY) if not is_ready else None
    pytest.skip(SKIP_SAME_AS_FOR_AD_STATE_READY) if initial_state == "NOT_READY" else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    action_inputs.ready = is_ready
    validator_ad.initialize_state(target_state=initial_state, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.val_manager = ZERO_ADDRESS
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_CALLED_BY_NOT_VAL_MANAGER, e)

    return

def test_wrong_caller(
    validator_ad: ValidatorAd,
    dispenser : AddressAndSigner,
    asset : int,
    is_ready : bool,  # noqa: FBT001
    initial_state : str,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None
    pytest.skip(SKIP_SAME_AS_FOR_AD_READY) if not is_ready else None
    pytest.skip(SKIP_SAME_AS_FOR_AD_STATE_READY) if initial_state == "NOT_READY" else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    action_inputs.ready = is_ready
    validator_ad.initialize_state(target_state=initial_state, action_inputs=action_inputs)

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
@pytest.mark.parametrize("ready", [True, False])
def test_state(
    validator_ad: ValidatorAd,
    asset : int,
    init_state : POSSIBLE_STATES,
    ready : bool,  # noqa: FBT001
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    action_inputs.ready = ready
    validator_ad.initialize_state(target_state=init_state, action_inputs=action_inputs)

    # Action

    if init_state in ["READY", "NOT_READY"]:
        # Action success
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

        # Check new state of ValidatorAd
        if ready:
            exp_state = STATE_READY
        else:
            exp_state = STATE_NOT_READY
        gs_end = validator_ad.get_global_state()
        assert gs_end.state == exp_state
    else:
        # Action fail
        with pytest.raises(LogicError) as e:
            validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
        assert is_expected_logic_error(ERROR_NOT_STATE_READY_OR_NOT_READY, e)

    return
