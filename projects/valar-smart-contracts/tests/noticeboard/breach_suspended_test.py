
import base64

import pytest
from algokit_utils.logic_error import LogicError
from algosdk.logic import get_application_address

import tests.validator_ad.delegator_contract_interface as dc
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    BOX_ASA_KEY_PREFIX,
    ERROR_APP_NOT_WITH_USER,
    ERROR_USER_DOES_NOT_EXIST,
    MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD,
    MSG_CORE_BREACH_SUSPENDED,
)
from tests.constants import (
    ERROR_GLOBAL_STATE_MISMATCH,
    SKIP_SAME_AS_FOR_ALGO,
)
from tests.noticeboard.utils import Noticeboard
from tests.utils import (
    available_balance,
    calc_earnings,
    calc_operational_fee,
    get_box,
    is_expected_logic_error,
)
from tests.validator_ad.client_helper import decode_asa_box

from .config import ActionInputs

# ------- Test constants -------
TEST_NB_STATE = "SET"
TEST_VA_STATE = "READY"
TEST_DC_STATE = "LIVE"
TEST_ACTION_NAME = "breach_suspended"

# ------- Tests -------
def test_action(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    del_app_id = noticeboard.initialize_delegator_contract_state(
        action_inputs=action_inputs,
        val_app_id=val_app_id,
        target_state=TEST_DC_STATE,
    )

    action_inputs.wait_until_suspended = True

    gs_start = noticeboard.get_global_state()
    gs_val_start = noticeboard.get_validator_ad_global_state(val_app_id)
    gs_del_start = noticeboard.get_delegator_global_state(del_app_id)

    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)
    bal_start_asset = noticeboard.app_available_balance(asset)
    bal_val_start = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=get_application_address(val_app_id),
        asset_id=asset,
    )
    bal_del_start = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=get_application_address(del_app_id),
        asset_id=asset,
    )

    del_user = noticeboard.del_managers[0].address
    del_user_info_start = noticeboard.app_get_user_info(del_user)

    val_user = noticeboard.val_owners[0].address
    val_user_info_start = noticeboard.app_get_user_info(val_user)

    # Action
    res = noticeboard.delegator_action(
        app_id=del_app_id,
        action_name=TEST_ACTION_NAME,
        action_inputs=action_inputs,
        val_app=val_app_id,
    )

    # Check return
    assert res.confirmed_round

    # Check notification message was sent
    assert base64.b64encode(MSG_CORE_BREACH_SUSPENDED).decode("utf-8") in str(res.abi_results[-1].tx_info)

    paid = calc_operational_fee(
        gs_del_start.delegation_terms_general.fee_round,
        res.confirmed_round,
        gs_del_start.round_start,
    )
    validator_earns, platforms_earns = calc_earnings(
        amount=paid,
        commission=gs_del_start.delegation_terms_general.commission,
    )

    # Check contract state
    gs_end = noticeboard.get_global_state()
    gs_exp = gs_start
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check balances
    bal_end = noticeboard.app_available_balance(ALGO_ASA_ID)
    bal_end_asset = noticeboard.app_available_balance(asset)
    bal_val_end = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=get_application_address(val_app_id),
        asset_id=asset,
    )
    bal_del_end = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=get_application_address(del_app_id),
        asset_id=asset,
    )

    prev_validator_earns, prev_platforms_earns = calc_earnings(
        amount=gs_del_start.delegation_terms_general.fee_setup,
        commission=gs_del_start.delegation_terms_general.commission,
    )

    if asset == ALGO_ASA_ID:
        # Platform's available ALGO balances increases for the earnings until the suspension breach
        # (other earnings have already been included in the balance fetch prior to the last call)
        assert bal_end == bal_start + platforms_earns
        assert bal_del_end == bal_del_start - paid
    else:
        assert bal_end == bal_start
        assert bal_end_asset == bal_start_asset + platforms_earns
        assert bal_del_end == bal_del_start - paid
    assert bal_val_end == bal_val_start + validator_earns

    # Check created delegator contract state
    gs_del_end = noticeboard.get_delegator_global_state(del_app_id)
    gs_del_exp = gs_del_start
    gs_del_exp.state = dc.STATE_ENDED_SUSPENDED
    gs_del_exp.round_claim_last = res.confirmed_round
    gs_del_exp.round_ended = res.confirmed_round
    assert gs_del_end == gs_del_exp

    # Check validator ad state
    gs_val_end = noticeboard.get_validator_ad_global_state(val_app_id)
    gs_val_exp = gs_val_start
    if asset == ALGO_ASA_ID:
        gs_val_exp.total_algo_earned = validator_earns + prev_validator_earns
        gs_val_exp.total_algo_fees_generated = platforms_earns + prev_platforms_earns
    else:
        box_name = BOX_ASA_KEY_PREFIX + asset.to_bytes(8, byteorder="big")
        box_contents_raw, box_exists = get_box(
            algorand_client=noticeboard.algorand_client,
            box_name=box_name,
            app_id=val_app_id,
        )
        assert box_exists
        validator_asa = decode_asa_box(box_contents_raw)
        assert validator_asa.total_earning == validator_earns + prev_validator_earns
        assert validator_asa.total_fees_generated == platforms_earns + prev_platforms_earns
    gs_val_exp.cnt_del = 0
    gs_val_exp.del_app_list = [0]*MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD
    assert gs_val_end == gs_val_exp

    # Delegator user does not change
    del_user_info = noticeboard.app_get_user_info(del_user)
    del_user_info_exp = del_user_info_start
    assert del_user_info == del_user_info_exp

    # Validator user does not change
    val_user_info = noticeboard.app_get_user_info(val_user)
    val_user_info_exp = val_user_info_start
    assert val_user_info == val_user_info_exp

    return

def test_del_manager_does_not_exist(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    del_app_id = noticeboard.initialize_delegator_contract_state(
        action_inputs=action_inputs,
        val_app_id=val_app_id,
        target_state=TEST_DC_STATE,
    )

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.del_manager = noticeboard.dispenser.address
        noticeboard.delegator_action(
            app_id=del_app_id,
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            val_app=val_app_id,
        )
    assert is_expected_logic_error(ERROR_USER_DOES_NOT_EXIST, e)

    return

def test_val_owner_does_not_exist(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    del_app_id = noticeboard.initialize_delegator_contract_state(
        action_inputs=action_inputs,
        val_app_id=val_app_id,
        target_state=TEST_DC_STATE,
    )

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.val_owner = noticeboard.dispenser.address
        noticeboard.delegator_action(
            app_id=del_app_id,
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            val_app=val_app_id,
        )
    assert is_expected_logic_error(ERROR_USER_DOES_NOT_EXIST, e)

    return

def test_wrong_indices(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    del_app_id = noticeboard.initialize_delegator_contract_state(
        action_inputs=action_inputs,
        val_app_id=val_app_id,
        target_state=TEST_DC_STATE,
    )

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.del_app_idx = 99
        noticeboard.delegator_action(
            app_id=del_app_id,
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            val_app=val_app_id,
        )

    assert is_expected_logic_error(ERROR_APP_NOT_WITH_USER, e)
    action_inputs.del_app_idx = None  # Reset

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.val_app_idx = 77
        noticeboard.delegator_action(
            app_id=del_app_id,
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            val_app=val_app_id,
        )

    assert is_expected_logic_error(ERROR_APP_NOT_WITH_USER, e)


    return

def test_action_w_partner(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    partner_address = noticeboard.partners[0].address
    action_inputs = ActionInputs(asset=asset, partner_address=partner_address)
    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    del_app_id = noticeboard.initialize_delegator_contract_state(
        action_inputs=action_inputs,
        val_app_id=val_app_id,
        target_state=TEST_DC_STATE,
    )

    action_inputs.wait_until_suspended = True

    gs_del_start = noticeboard.get_delegator_global_state(del_app_id)

    bal_par_start = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=partner_address,
        asset_id=asset,
    )

    # Action
    res = noticeboard.delegator_action(
        app_id=del_app_id,
        action_name=TEST_ACTION_NAME,
        action_inputs=action_inputs,
        val_app=val_app_id,
    )

    # Check return
    assert res.confirmed_round

    paid_partner = calc_operational_fee(
        gs_del_start.delegation_terms_general.fee_round_partner,
        res.confirmed_round,
        gs_del_start.round_start,
    )

    # Check balance of partner
    bal_par_end = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=partner_address,
        asset_id=asset,
    )

    assert bal_par_end == bal_par_start + paid_partner

    return
