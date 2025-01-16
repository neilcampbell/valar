
import copy
import dataclasses

import pytest
from algokit_utils.logic_error import LogicError

import tests.noticeboard.validator_ad_interface as va
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY,
    COMMISSION_MAX,
    ERROR_AD_FEE_ROUND_MIN_TOO_SMALL,
    ERROR_AD_FEE_ROUND_VAR_TOO_SMALL,
    ERROR_AD_FEE_SETUP_TOO_SMALL,
    ERROR_AD_MAX_DURATION_TOO_LONG,
    ERROR_AD_MIN_DURATION_TOO_SHORT,
    ERROR_AD_STAKE_MAX_TOO_LARGE,
    ERROR_AD_STAKE_MAX_TOO_SMALL,
    ERROR_APP_NOT_WITH_USER,
    ERROR_ASSET_NOT_ALLOWED,
    ERROR_COMMISSION_MAX,
    ERROR_COMMISSION_MIN,
    ERROR_NOT_STATE_SET,
    ERROR_RECEIVER,
    ERROR_USER_DOES_NOT_EXIST,
)
from tests.constants import (
    ERROR_GLOBAL_STATE_MISMATCH,
    SKIP_SAME_AS_FOR_ALGO,
    SKIP_SAME_AS_FOR_ASA,
)
from tests.noticeboard.utils import POSSIBLE_STATES, Noticeboard
from tests.utils import get_box, is_expected_logic_error

from .config import (
    DEFAULT_VALIDATOR_TERMS_PRICE,
    DEFAULT_VALIDATOR_TERMS_REQS,
    DEFAULT_VALIDATOR_TERMS_STAKE,
    DEFAULT_VALIDATOR_TERMS_TIME,
    DEFAULT_VALIDATOR_TERMS_WARN,
    ActionInputs,
)

# ------- Test constants -------
TEST_INITIAL_STATE = "SET"
TEST_VA_STATE = "CREATED"
TEST_ACTION_NAME = "ad_terms"

# ------- Tests -------
def test_action(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs(
        asset=asset,
    )
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    gs_start = noticeboard.get_global_state()
    gs_val_start = noticeboard.get_validator_ad_global_state(val_app_id)
    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)

    # Action
    res = noticeboard.validator_action(val_app_id, TEST_ACTION_NAME, action_inputs)

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    bal_end = noticeboard.app_available_balance(ALGO_ASA_ID)
    assert bal_start == bal_end

    # Check validator ad state
    gs_val_end = noticeboard.get_validator_ad_global_state(val_app_id)
    gs_val_exp = gs_val_start
    gs_val_exp.state = va.STATE_SET
    gs_val_exp.tc_sha256 = gs_start.tc_sha256
    gs_val_exp.terms_time = DEFAULT_VALIDATOR_TERMS_TIME
    terms_price = copy.deepcopy(DEFAULT_VALIDATOR_TERMS_PRICE)
    terms_price.commission = gs_start.noticeboard_fees.commission_min
    terms_price.fee_asset_id = asset
    gs_val_exp.terms_price = terms_price
    gs_val_exp.terms_stake = DEFAULT_VALIDATOR_TERMS_STAKE
    gs_val_exp.terms_reqs = DEFAULT_VALIDATOR_TERMS_REQS
    gs_val_exp.terms_warn = DEFAULT_VALIDATOR_TERMS_WARN
    gs_val_exp.cnt_asa = 0 if asset == ALGO_ASA_ID else 1
    assert dataclasses.asdict(gs_val_exp) == dataclasses.asdict(gs_val_end)

    # Check transfer of delegator template contract was successful
    box_name = BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY
    box_template_del = noticeboard.app_box(box_name)
    box_val_template_del = get_box(
        algorand_client=noticeboard.algorand_client,
        box_name=box_name,
        app_id=val_app_id,
    )
    assert box_val_template_del[1]
    assert box_val_template_del[0] == box_template_del[0]

    return

def test_user_does_not_exist(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)

    # Action fail
    with pytest.raises(LogicError) as e:
        noticeboard.validator_action(val_app_id, TEST_ACTION_NAME, action_inputs, noticeboard.dispenser)
    assert is_expected_logic_error(ERROR_USER_DOES_NOT_EXIST, e)

    return

def test_app_does_not_exist(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)

    # Action fail - index doesn't match
    with pytest.raises(LogicError) as e:
        action_inputs.val_app_idx = 99
        noticeboard.validator_action(val_app_id, TEST_ACTION_NAME, action_inputs)
    assert is_expected_logic_error(ERROR_APP_NOT_WITH_USER, e)
    action_inputs.val_app_idx = None # Reset

    # Action fail - app ID doesn't match
    with pytest.raises(LogicError) as e:
        action_inputs.val_app_id = 99
        noticeboard.validator_action(val_app_id, TEST_ACTION_NAME, action_inputs)
    assert is_expected_logic_error(ERROR_APP_NOT_WITH_USER, e)

    return

def test_wrong_receiver(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.receiver = noticeboard.dispenser.address
        noticeboard.validator_action(val_app_id, TEST_ACTION_NAME, action_inputs)
    assert is_expected_logic_error(ERROR_RECEIVER, e)

    return

def test_never_accepted_asset(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ASA) if asset == ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.asset = ALGO_ASA_ID
        noticeboard.validator_action(val_app_id, TEST_ACTION_NAME, action_inputs)
    assert is_expected_logic_error("check self.assets entry exists", e)

    return

def test_currently_unaccepted_asset(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)

    # Disable asset on Noticeboard
    ai_tmp = copy.deepcopy(action_inputs)
    ai_tmp.asset_info.accepted = False  # Disable asset
    ai_tmp.amount = 0  # To disable asset, there is no need to pay
    noticeboard.noticeboard_action("noticeboard_config_asset", ai_tmp)

    # Actions fail
    with pytest.raises(LogicError) as e:
        noticeboard.validator_action(val_app_id, TEST_ACTION_NAME, action_inputs)
    assert is_expected_logic_error(ERROR_ASSET_NOT_ALLOWED, e)

    return

def test_unacceptable_terms(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)

    # Actions fail
    # Terms Timing
    with pytest.raises(LogicError) as e:
        ai_tmp = copy.deepcopy(action_inputs)
        ai_tmp.terms_time.rounds_duration_min = ai_tmp.noticeboard_terms_timing.rounds_duration_min_min-1
        noticeboard.validator_action(val_app_id, TEST_ACTION_NAME, ai_tmp)
    assert is_expected_logic_error(ERROR_AD_MIN_DURATION_TOO_SHORT, e)

    with pytest.raises(LogicError) as e:
        ai_tmp = copy.deepcopy(action_inputs)
        ai_tmp.terms_time.rounds_duration_max = ai_tmp.noticeboard_terms_timing.rounds_duration_max_max+1
        noticeboard.validator_action(val_app_id, TEST_ACTION_NAME, ai_tmp)
    assert is_expected_logic_error(ERROR_AD_MAX_DURATION_TOO_LONG, e)

    # Terms Pricing
    with pytest.raises(LogicError) as e:
        ai_tmp = copy.deepcopy(action_inputs)
        ai_tmp.terms_price.commission = COMMISSION_MAX + 1
        noticeboard.validator_action(val_app_id, TEST_ACTION_NAME, ai_tmp)
    assert is_expected_logic_error(ERROR_COMMISSION_MAX, e)

    with pytest.raises(LogicError) as e:
        ai_tmp = copy.deepcopy(action_inputs)
        ai_tmp.terms_price.commission = ai_tmp.noticeboard_fees.commission_min-1
        noticeboard.validator_action(val_app_id, TEST_ACTION_NAME, ai_tmp)
    assert is_expected_logic_error(ERROR_COMMISSION_MIN, e)

    with pytest.raises(LogicError) as e:
        ai_tmp = copy.deepcopy(action_inputs)
        ai_tmp.terms_price.fee_round_min = noticeboard.app_get_asset_info(asset).fee_round_min_min-1
        noticeboard.validator_action(val_app_id, TEST_ACTION_NAME, ai_tmp)
    assert is_expected_logic_error(ERROR_AD_FEE_ROUND_MIN_TOO_SMALL, e)

    with pytest.raises(LogicError) as e:
        ai_tmp = copy.deepcopy(action_inputs)
        ai_tmp.terms_price.fee_round_var = noticeboard.app_get_asset_info(asset).fee_round_var_min-1
        noticeboard.validator_action(val_app_id, TEST_ACTION_NAME, ai_tmp)
    assert is_expected_logic_error(ERROR_AD_FEE_ROUND_VAR_TOO_SMALL, e)

    with pytest.raises(LogicError) as e:
        ai_tmp = copy.deepcopy(action_inputs)
        ai_tmp.terms_price.fee_setup = noticeboard.app_get_asset_info(asset).fee_setup_min-1
        noticeboard.validator_action(val_app_id, TEST_ACTION_NAME, ai_tmp)
    assert is_expected_logic_error(ERROR_AD_FEE_SETUP_TOO_SMALL, e)

    # Terms Stake
    with pytest.raises(LogicError) as e:
        ai_tmp = copy.deepcopy(action_inputs)
        ai_tmp.terms_stake.stake_max = ai_tmp.noticeboard_terms_node.stake_max_max+1
        noticeboard.validator_action(val_app_id, TEST_ACTION_NAME, ai_tmp)
    assert is_expected_logic_error(ERROR_AD_STAKE_MAX_TOO_LARGE, e)

    with pytest.raises(LogicError) as e:
        ai_tmp = copy.deepcopy(action_inputs)
        ai_tmp.terms_stake.stake_max = ai_tmp.noticeboard_terms_node.stake_max_min-1
        noticeboard.validator_action(val_app_id, TEST_ACTION_NAME, ai_tmp)
    assert is_expected_logic_error(ERROR_AD_STAKE_MAX_TOO_SMALL, e)

    return

@pytest.mark.parametrize("init_state", [
    "DEPLOYED",
    "SET",
    "SUSPENDED",
    "RETIRED",
])
def test_state(
    noticeboard: Noticeboard,
    asset : int,
    init_state : POSSIBLE_STATES,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    action_inputs.val_app_idx = 0
    noticeboard.initialize_state(target_state=init_state, action_inputs=action_inputs)

    if init_state == "SET":
        gs_start = noticeboard.get_global_state()

        # Action success
        val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
        res = noticeboard.validator_action(val_app_id, TEST_ACTION_NAME, action_inputs)
        assert res.confirmed_round

        # Check new state of Noticeboard - should not change
        exp_state = gs_start.state
        gs_end = noticeboard.get_global_state()
        assert gs_end.state == exp_state
    else:
        # Action fail
        with pytest.raises(LogicError) as e:
            noticeboard.validator_action(0, TEST_ACTION_NAME, action_inputs)
        assert is_expected_logic_error(ERROR_NOT_STATE_SET, e)

    return
