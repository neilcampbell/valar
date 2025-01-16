
import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.composer import PayParams
from algokit_utils.logic_error import LogicError
from algosdk.constants import ZERO_ADDRESS

from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_AD_END_IS_IN_PAST,
    ERROR_AD_TERMS_MBR,
    ERROR_CALLED_BY_NOT_CREATOR,
    ERROR_CALLED_BY_NOT_VAL_OWNER,
    ERROR_RECEIVER,
    ERROR_TERM_DURATION_MIN_LARGER_THAN_MAX,
    ERROR_TERMS_MIN_DURATION_SETUP_CONFIRM,
    MBR_AD_TERMS,
)
from smart_contracts.validator_ad.constants import (
    STATE_SET,
)
from tests.conftest import TestConsts
from tests.constants import ERROR_GLOBAL_STATE_MISMATCH, SKIP_NOT_APPLICABLE_TO_ALGO, SKIP_SAME_AS_FOR_ALGO
from tests.utils import is_expected_logic_error
from tests.validator_ad.client_helper import ValidatorASA
from tests.validator_ad.utils import POSSIBLE_STATES, ValidatorAd

from .config import DEFAULT_VALIDATOR_TERMS_TIME, ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "TEMPLATE_LOADED"
TEST_ACTION_NAME = "ad_terms"

# ------- Tests -------
def test_action(
    validator_ad: ValidatorAd,
    asset : int,
) -> None:

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
    gs_exp.state = STATE_SET
    gs_exp.tc_sha256 = action_inputs.tc_sha256
    gs_exp.terms_time = action_inputs.terms_time
    gs_exp.terms_price = action_inputs.terms_price
    gs_exp.terms_stake = action_inputs.terms_stake
    gs_exp.terms_reqs = action_inputs.terms_reqs
    gs_exp.terms_warn = action_inputs.terms_warn

    if asset != ALGO_ASA_ID:
        # A new (first) ASA was added
        gs_exp.cnt_asa = 1
    assert validator_ad.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # If asset ID is not zero (i.e. ALGO), check if contract opted-in to it and created a box.
    if asset != ALGO_ASA_ID:
        assert validator_ad.app_is_opted_in(asset)
        assert validator_ad.app_asa_box(asset) == ValidatorASA(
            total_earning=0,
            total_fees_generated=0,
        )

def test_ad_terms_again_same_asa(
    validator_ad: ValidatorAd,
    asset : int,
) -> None:

    pytest.skip(SKIP_NOT_APPLICABLE_TO_ALGO) if asset == ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action
    res = validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    gs_start = validator_ad.get_global_state()

    # Check return
    assert res.confirmed_round

    # Action
    res = validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    # Only one ASA was added
    gs_exp.cnt_asa = 1
    assert validator_ad.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

def test_ad_terms_again_2nd_asa(
    validator_ad: ValidatorAd,
    asset : int,
    asa_2 : int,
) -> None:

    pytest.skip(SKIP_NOT_APPLICABLE_TO_ALGO) if asset == ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action
    res = validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    gs_start = validator_ad.get_global_state()
    action_inputs.terms_price.fee_asset_id = asa_2

    # Action
    res = validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    gs_exp.terms_price.fee_asset_id = asa_2
    # Two difference ASAs were added
    gs_exp.cnt_asa = 2
    assert validator_ad.get_global_state() == gs_exp, ERROR_GLOBAL_STATE_MISMATCH
    assert all(validator_ad.app_is_opted_in(a) for a in [asset, asa_2])
    assert all(
        validator_ad.app_asa_box(a) == ValidatorASA(
            total_earning=0,
            total_fees_generated=0,
        ) for a in [asset, asa_2]
    )


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

def test_wrong_input_terms(
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
        action_inputs.terms_time.rounds_confirm = \
            action_inputs.terms_time.rounds_duration_min - \
            action_inputs.terms_time.rounds_setup + 1
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_TERMS_MIN_DURATION_SETUP_CONFIRM, e)
    action_inputs.terms_time.rounds_confirm = \
        DEFAULT_VALIDATOR_TERMS_TIME.rounds_confirm # Rest to default

    with pytest.raises(LogicError) as e:
        action_inputs.terms_time.rounds_duration_max = \
            action_inputs.terms_time.rounds_duration_min - 1
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_TERM_DURATION_MIN_LARGER_THAN_MAX, e)
    action_inputs.terms_time.rounds_duration_max = \
        DEFAULT_VALIDATOR_TERMS_TIME.rounds_duration_max # Rest to default

    with pytest.raises(LogicError) as e:
        action_inputs.terms_time.round_max_end = validator_ad.algorand_client.client.algod.status()["last-round"] - 1
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_AD_END_IS_IN_PAST, e)
    action_inputs.terms_time.round_max_end = \
        DEFAULT_VALIDATOR_TERMS_TIME.round_max_end # Rest to default

    return

def test_wrong_receiver(
    validator_ad: ValidatorAd,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.receiver = validator_ad.acc.address
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_RECEIVER, e)

    return

def test_wrong_mbr_amount(
    validator_ad: ValidatorAd,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.ad_terms_mbr = MBR_AD_TERMS - 1
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_AD_TERMS_MBR, e)

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
    dispenser : AddressAndSigner,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    validator_ad.initialize_state(target_state=init_state, action_inputs=action_inputs)

    gs_start = validator_ad.get_global_state()

    if init_state == "CREATED":
        # Contract must be funded
        validator_ad.algorand_client.send.payment(
            PayParams(
                sender=dispenser.address,
                receiver=validator_ad.validator_ad_client.app_address,
                amount=TestConsts.acc_dispenser_amt,
            )
        )

    # Action success
    validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check new state of ValidatorAd
    if init_state == "TEMPLATE_LOADED":
        exp_state = STATE_SET
    else:
        exp_state = gs_start.state
    gs_end = validator_ad.get_global_state()
    assert gs_end.state == exp_state

    return
