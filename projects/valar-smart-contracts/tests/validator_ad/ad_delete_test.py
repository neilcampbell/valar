
import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.logic_error import LogicError
from algosdk.constants import ZERO_ADDRESS
from algosdk.error import AlgodHTTPError

from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_CALLED_BY_NOT_CREATOR,
    ERROR_CALLED_BY_NOT_VAL_OWNER,
    ERROR_DELETE_ACTIVE_DELEGATORS,
    ERROR_DELETE_ASA_REMAIN,
)
from tests.constants import (
    SKIP_NOT_APPLICABLE_TO_ALGO,
    SKIP_SAME_AS_FOR_ALGO,
)
from tests.utils import is_expected_logic_error
from tests.validator_ad.utils import ValidatorAd

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "NOT_READY"
TEST_ACTION_NAME = "ad_delete"

# ------- Tests -------
def test_action(
    validator_ad: ValidatorAd,
    val_owner: AddressAndSigner,
    val_manager: AddressAndSigner,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    action_inputs.val_owner = val_owner.address
    action_inputs.val_manager = val_manager.address
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    if asset != ALGO_ASA_ID:
        # Before ad deletion, all ASAs must be removed
        validator_ad.action(action_name="ad_asa_close", action_inputs=action_inputs)

    # Withdraw any ALGO balance
    action_inputs.income_asset_id = ALGO_ASA_ID
    validator_ad.action(action_name="ad_income", action_inputs=action_inputs)

    # Action
    res = validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.confirmed_round

   # Check contract was deleted
    with pytest.raises(AlgodHTTPError):
        app_id = validator_ad.validator_ad_client.app_id
        validator_ad.algorand_client.client.algod.application_info(app_id)

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

def test_active_delegator(
    validator_ad: ValidatorAd,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    validator_ad.initialize_state(target_state="READY", action_inputs=action_inputs)
    app_id = validator_ad.initialize_delegator_state(  # noqa: F841
        action_inputs=action_inputs,
        target_state="READY",
    )
    validator_ad.initialize_state(target_state="NOT_READY", action_inputs=action_inputs) # Not needed

    # Action fail
    with pytest.raises(LogicError) as e:
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_DELETE_ACTIVE_DELEGATORS, e)

    return

def test_asa_remain(
    validator_ad: ValidatorAd,
    asset : int,
) -> None:

    pytest.skip(SKIP_NOT_APPLICABLE_TO_ALGO) if asset == ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    validator_ad.initialize_state(target_state="READY", action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_DELETE_ASA_REMAIN, e)

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
