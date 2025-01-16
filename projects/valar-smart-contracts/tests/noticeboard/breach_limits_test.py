
import base64  # noqa: I001

import pytest
from algokit_utils import ABITransactionResponse
from algokit_utils.beta.composer import PayParams
from algokit_utils.logic_error import LogicError
from algosdk.logic import get_application_address

import tests.validator_ad.delegator_contract_interface as dc
from algokit_utils.beta.composer import AssetTransferParams
from smart_contracts.artifacts.noticeboard.client import ValidatorTermsGating
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    BOX_ASA_KEY_PREFIX,
    ERROR_APP_NOT_WITH_USER,
    ERROR_USER_DOES_NOT_EXIST,
    MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD,
    MSG_CORE_BREACH_LIMITS_ERROR,
)
from tests.conftest import TestConsts
from tests.constants import (
    ERROR_GLOBAL_STATE_MISMATCH,
    SKIP_NOT_APPLICABLE_TO_ALGO,
    SKIP_SAME_AS_FOR_ALGO,
)
from tests.noticeboard.utils import Noticeboard
from tests.utils import (
    available_balance,
    balance,
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
TEST_ACTION_NAME = "breach_limits"

# ------- Tests -------
def test_action(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs(asset=asset)

    asa_del_ben_bal = balance(
        noticeboard.algorand_client,
        noticeboard.del_managers[0].address,
        asset,
    )
    action_inputs.terms_reqs = ValidatorTermsGating(
        gating_asa_list=[(
                asset,
                round(asa_del_ben_bal/2),  # Set ASA breach limit to amount of del_beneficiary = del_managers[0] - something (because the fee is paid in same ASA)  # noqa: E501
            ), (0,0),
        ],
    )

    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    del_app_id = noticeboard.initialize_delegator_contract_state(
        action_inputs=action_inputs,
        val_app_id=val_app_id,
        target_state=TEST_DC_STATE,
    )

    gs_start = noticeboard.get_global_state()
    gs_val_start = noticeboard.get_validator_ad_global_state(val_app_id)
    gs_del_start = noticeboard.get_delegator_global_state(del_app_id)

    if asset != ALGO_ASA_ID:
        # Decrease ASA below the limit
        noticeboard.algorand_client.send.asset_transfer(
            AssetTransferParams(
                sender = gs_del_start.del_beneficiary,
                receiver = noticeboard.dispenser.address,
                amount = round(asa_del_ben_bal*2/3),
                asset_id=asset,
            )
        )
    else:
        # Increase ALGO above the limit
        noticeboard.algorand_client.send.payment(
            PayParams(
                sender = noticeboard.dispenser.address,
                receiver = gs_del_start.del_beneficiary,
                amount = round(gs_del_start.delegation_terms_balance.stake_max*2),
            )
        )

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

    # Top up delegator account to exceed max stake limit
    noticeboard.algorand_client.send.payment(
        PayParams(
            sender=noticeboard.dispenser.address,
            receiver=noticeboard.del_managers[0].address,
            amount=TestConsts.acc_dispenser_amt,
        )
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

    # Check notification message was sent
    assert base64.b64encode(MSG_CORE_BREACH_LIMITS_ERROR).decode("utf-8") in str(res.abi_results[-1].tx_info)

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

    assert bal_end_asset == bal_start_asset + platforms_earns
    assert bal_del_end == bal_del_start - paid
    if asset == ALGO_ASA_ID:
        assert bal_end == bal_start + platforms_earns
    else:
        # If payment is not in ALGO, the platform's ALGO balance mustn't change
        assert bal_end == bal_start
    assert bal_val_end == bal_val_start + validator_earns

    # Check created delegator contract state
    gs_del_end = noticeboard.get_delegator_global_state(del_app_id)
    gs_del_exp = gs_del_start
    gs_del_exp.state = dc.STATE_LIVE
    gs_del_exp.round_claim_last = res.confirmed_round
    gs_del_exp.cnt_breach_del = 1
    gs_del_exp.round_breach_last = res.confirmed_round
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

def test_max_breach(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs(asset=asset)

    asa_del_ben_bal = balance(
        noticeboard.algorand_client,
        noticeboard.del_managers[0].address,
        asset,
    )
    action_inputs.terms_reqs = ValidatorTermsGating(
        gating_asa_list=[(
                asset,
                round(asa_del_ben_bal/2),  # Set ASA breach limit to amount of del_beneficiary = del_managers[0] - something (because the fee is paid in same ASA)  # noqa: E501
            ), (0,0),
        ],
    )

    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    del_app_id = noticeboard.initialize_delegator_contract_state(
        action_inputs=action_inputs,
        val_app_id=val_app_id,
        target_state=TEST_DC_STATE,
    )

    gs_start = noticeboard.get_global_state()
    gs_val_start = noticeboard.get_validator_ad_global_state(val_app_id)
    gs_del_start = noticeboard.get_delegator_global_state(del_app_id)

    if asset != ALGO_ASA_ID:
        # Decrease ASA below the limit
        noticeboard.algorand_client.send.asset_transfer(
            AssetTransferParams(
                sender = gs_del_start.del_beneficiary,
                receiver = noticeboard.dispenser.address,
                amount = round(asa_del_ben_bal*2/3),
                asset_id=asset,
            )
        )
    else:
        # Increase ALGO above the limit
        noticeboard.algorand_client.send.payment(
            PayParams(
                sender = noticeboard.dispenser.address,
                receiver = gs_del_start.del_beneficiary,
                amount = round(gs_del_start.delegation_terms_balance.stake_max*2),
            )
        )

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

    # Top up delegator account to exceed max stake limit
    noticeboard.algorand_client.send.payment(
        PayParams(
            sender=noticeboard.dispenser.address,
            receiver=noticeboard.del_managers[0].address,
            amount=TestConsts.acc_dispenser_amt,
        )
    )

    # Action succeeds
    res : list[ABITransactionResponse] = []
    validator_earns = 0
    platforms_earns = 0
    for _ in range(gs_del_start.delegation_terms_balance.cnt_breach_del_max):
    # Action
        res.append(noticeboard.delegator_action(
            app_id=del_app_id,
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            val_app=val_app_id,
        ))

        # Check return
        assert res[-1].confirmed_round

        gs_del_new = noticeboard.get_delegator_global_state(del_app_id)
        round_start = gs_del_new.round_start if len(res) == 1 else res[-2].confirmed_round
        amount = calc_operational_fee(
            gs_del_new.delegation_terms_general.fee_round,
            res[-1].confirmed_round,
            round_start,
        )
        tmp_earn = calc_earnings(
            amount=amount,
            commission=gs_del_new.delegation_terms_general.commission,
        )
        validator_earns += tmp_earn[0]
        platforms_earns += tmp_earn[1]

    paid = validator_earns + platforms_earns

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
        assert bal_end == bal_start + platforms_earns
        assert bal_del_end == bal_del_start - paid
        assert bal_val_end == bal_val_start + validator_earns
    else:
        assert bal_end == bal_start
        assert bal_end_asset == bal_start_asset + platforms_earns
        assert bal_del_end == bal_del_start - paid
        assert bal_val_end == bal_val_start + validator_earns

    # Check created delegator contract state
    gs_del_end = noticeboard.get_delegator_global_state(del_app_id)
    gs_del_exp = gs_del_start
    gs_del_exp.state = dc.STATE_ENDED_LIMITS
    gs_del_exp.round_claim_last = res[-1].confirmed_round
    gs_del_exp.round_ended = res[-1].confirmed_round
    gs_del_exp.cnt_breach_del = gs_del_start.delegation_terms_balance.cnt_breach_del_max
    gs_del_exp.round_breach_last = res[-1].confirmed_round
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

def test_max_breach_on_asa_w_account_opted_out(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_NOT_APPLICABLE_TO_ALGO) if asset == ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)

    asa_del_ben_bal = balance(
        noticeboard.algorand_client,
        noticeboard.del_managers[0].address,
        asset,
    )
    action_inputs.terms_reqs = ValidatorTermsGating(
        gating_asa_list=[(
                asset,
                round(asa_del_ben_bal/2),  # Set ASA breach limit to amount of del_beneficiary = del_managers[0] - something (because the fee is paid in same ASA)  # noqa: E501
            ), (0,0),
        ],
    )

    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    del_app_id = noticeboard.initialize_delegator_contract_state(
        action_inputs=action_inputs,
        val_app_id=val_app_id,
        target_state=TEST_DC_STATE,
    )

    # Opt-out delegator beneficiary (which equals del_managers[0] by default) account of the ASA
    noticeboard.algorand_client.send.payment(
        AssetTransferParams(
            sender=noticeboard.del_managers[0].address,
            asset_id=asset,
            amount=0,
            receiver=noticeboard.dispenser.address,
            close_asset_to=noticeboard.dispenser.address,
        )
    )

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

    # Action succeeds
    res : list[ABITransactionResponse] = []
    validator_earns = 0
    platforms_earns = 0
    for _ in range(gs_del_start.delegation_terms_balance.cnt_breach_del_max):
    # Action
        res.append(noticeboard.delegator_action(
            app_id=del_app_id,
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            val_app=val_app_id,
        ))

        # Check return
        assert res[-1].confirmed_round

        gs_del_new = noticeboard.get_delegator_global_state(del_app_id)
        round_start = gs_del_new.round_start if len(res) == 1 else res[-2].confirmed_round
        amount = calc_operational_fee(
            gs_del_new.delegation_terms_general.fee_round,
            res[-1].confirmed_round,
            round_start,
        )
        tmp_earn = calc_earnings(
            amount=amount,
            commission=gs_del_new.delegation_terms_general.commission,
        )
        validator_earns += tmp_earn[0]
        platforms_earns += tmp_earn[1]

    paid = validator_earns + platforms_earns

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
        assert bal_end == bal_start + platforms_earns
        assert bal_del_end == bal_del_start - paid
        assert bal_val_end == bal_val_start + validator_earns
    else:
        assert bal_end == bal_start
        assert bal_end_asset == bal_start_asset + platforms_earns
        assert bal_del_end == bal_del_start - paid
        assert bal_val_end == bal_val_start + validator_earns

    # Check created delegator contract state
    gs_del_end = noticeboard.get_delegator_global_state(del_app_id)
    gs_del_exp = gs_del_start
    gs_del_exp.state = dc.STATE_ENDED_LIMITS
    gs_del_exp.round_claim_last = res[-1].confirmed_round
    gs_del_exp.round_ended = res[-1].confirmed_round
    gs_del_exp.cnt_breach_del = gs_del_start.delegation_terms_balance.cnt_breach_del_max
    gs_del_exp.round_breach_last = res[-1].confirmed_round
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

    # Opt-out delegator beneficiary (which equals del_managers[0] by default) account back to the ASA for the next tests
    noticeboard.algorand_client.send.payment(
        AssetTransferParams(
            sender=noticeboard.del_managers[0].address,
            asset_id=asset,
            amount=0,
            receiver=noticeboard.del_managers[0].address,
        )
    )
    noticeboard.algorand_client.send.payment(
        AssetTransferParams(
            sender=noticeboard.dispenser.address,
            asset_id=asset,
            amount=TestConsts.acc_dispenser_asa_amt,
            receiver=noticeboard.del_managers[0].address,
        )
    )

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

    # Setup
    partner_address = noticeboard.partners[0].address
    action_inputs = ActionInputs(asset=asset, partner_address=partner_address)

    asa_del_ben_bal = balance(
        noticeboard.algorand_client,
        noticeboard.del_managers[0].address,
        asset,
    )
    action_inputs.terms_reqs = ValidatorTermsGating(
        gating_asa_list=[(
                asset,
                round(asa_del_ben_bal/2),  # Set ASA breach limit to amount of del_beneficiary = del_managers[0] - something (because the fee is paid in same ASA)  # noqa: E501
            ), (0,0),
        ],
    )

    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    del_app_id = noticeboard.initialize_delegator_contract_state(
        action_inputs=action_inputs,
        val_app_id=val_app_id,
        target_state=TEST_DC_STATE,
    )

    gs_del_start = noticeboard.get_delegator_global_state(del_app_id)

    if asset != ALGO_ASA_ID:
        # Decrease ASA below the limit
        noticeboard.algorand_client.send.asset_transfer(
            AssetTransferParams(
                sender = gs_del_start.del_beneficiary,
                receiver = noticeboard.dispenser.address,
                amount = round(asa_del_ben_bal*2/3),
                asset_id=asset,
            )
        )
    else:
        # Increase ALGO above the limit
        noticeboard.algorand_client.send.payment(
            PayParams(
                sender = noticeboard.dispenser.address,
                receiver = gs_del_start.del_beneficiary,
                amount = round(gs_del_start.delegation_terms_balance.stake_max*2),
            )
        )

    bal_par_start = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=partner_address,
        asset_id=asset,
    )

    # Top up delegator account to exceed max stake limit
    noticeboard.algorand_client.send.payment(
        PayParams(
            sender=noticeboard.dispenser.address,
            receiver=noticeboard.del_managers[0].address,
            amount=TestConsts.acc_dispenser_amt,
        )
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
