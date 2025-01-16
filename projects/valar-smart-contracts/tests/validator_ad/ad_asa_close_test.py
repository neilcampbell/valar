
import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.composer import AssetTransferParams
from algokit_utils.logic_error import LogicError
from algosdk.constants import ZERO_ADDRESS

from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_ASA_NOT_STORED_AT_VALIDATOR_AD,
    ERROR_CALLED_BY_NOT_CREATOR,
    ERROR_CALLED_BY_NOT_VAL_OWNER,
    ERROR_CANNOT_REMOVE_ASA_WITH_ACTIVE_DELEGATORS,
)
from tests.conftest import TestConsts
from tests.constants import ERROR_GLOBAL_STATE_MISMATCH, SKIP_NOT_APPLICABLE_TO_ALGO, SKIP_SAME_AS_FOR_ALGO
from tests.utils import balance, is_expected_logic_error
from tests.validator_ad.utils import ValidatorAd

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "SET"
TEST_ACTION_NAME = "ad_asa_close"

# ------- Tests -------
def test_action(
    validator_ad: ValidatorAd,
    asset : int,
    dispenser: AddressAndSigner,
    val_owner : AddressAndSigner,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    action_inputs.val_owner = val_owner.address
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    if asset != ALGO_ASA_ID:
        # Continue setup

        # Fund validator ad with some asa
        validator_ad.algorand_client.send.asset_transfer(
            AssetTransferParams(
                sender=dispenser.address,
                receiver=validator_ad.validator_ad_client.app_address,
                amount=TestConsts.acc_dispenser_asa_amt,
                asset_id=asset,
            )
        )

        # val_owner opts into asa
        validator_ad.algorand_client.send.asset_transfer(
            AssetTransferParams(
                sender=val_owner.address,
                receiver=val_owner.address,
                amount=0,
                asset_id=asset,
                signer=val_owner.signer,
            )
        )

        # Check state before action
        gs_start = validator_ad.get_global_state()
        ad_asa_bal_start = validator_ad.app_balance(asset)
        val_owner_bal_start = balance(
            algorand_client=validator_ad.algorand_client,
            address=val_owner.address,
            asset_id=asset,
        )

        # Action succeeds
        res = validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

        # Check return
        assert res.confirmed_round

        # Check contract state
        gs_exp = gs_start
        gs_exp.cnt_asa = 0
        assert validator_ad.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

        assert not validator_ad.app_is_opted_in(asset)
        val_owner_bal_end = balance(
            algorand_client=validator_ad.algorand_client,
            address=val_owner.address,
            asset_id=asset,
        )
        assert val_owner_bal_end-val_owner_bal_start == ad_asa_bal_start

    else:
        # Action fails
        with pytest.raises(LogicError) as e:
            validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
        assert is_expected_logic_error(ERROR_ASA_NOT_STORED_AT_VALIDATOR_AD, e)

    return

def test_active_delegator(
    validator_ad: ValidatorAd,
    asset : int,
) -> None:

    pytest.skip(SKIP_NOT_APPLICABLE_TO_ALGO) if asset == ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    validator_ad.initialize_state(target_state="READY", action_inputs=action_inputs)

    res = validator_ad.action(action_name="contract_create", action_inputs=action_inputs)
    assert res.confirmed_round

    # Action fails
    with pytest.raises(LogicError) as e:
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_CANNOT_REMOVE_ASA_WITH_ACTIVE_DELEGATORS, e)

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

    pytest.skip(SKIP_NOT_APPLICABLE_TO_ALGO) if asset == ALGO_ASA_ID else None

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
