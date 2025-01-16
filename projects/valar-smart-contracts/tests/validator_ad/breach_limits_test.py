

import pytest
from algokit_utils import ABITransactionResponse, LogicError
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.composer import AssetTransferParams, PayParams

import tests.validator_ad.delegator_contract_interface as dc
from smart_contracts.artifacts.validator_ad.client import BreachLimitsReturn
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_CALLED_BY_NOT_CREATOR,
    ERROR_DELEGATOR_DOES_NOT_EXIST_AT_VALIDATOR_AD,
    MSG_CORE_BREACH_LIMITS_END,
    MSG_CORE_BREACH_LIMITS_ERROR,
)
from tests.conftest import TestConsts
from tests.constants import ERROR_GLOBAL_STATE_MISMATCH, SKIP_SAME_AS_FOR_ALGO
from tests.utils import balance, calc_earnings, calc_operational_fee, is_expected_logic_error
from tests.validator_ad.client_helper import ValidatorASA
from tests.validator_ad.utils import ValidatorAd

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "READY"
TEST_DELEGATOR_INITIAL_STATE = "LIVE"
TEST_ACTION_NAME = "breach_limits"

# ------- Tests -------
def test_action(
    validator_ad: ValidatorAd,
    asset : int,
    val_owner : AddressAndSigner,
    val_manager : AddressAndSigner,
    dispenser : AddressAndSigner,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    action_inputs.terms_reqs.gating_asa_list[0] = (
        asset,
        round(TestConsts.acc_dispenser_asa_amt / 2),
    )
    action_inputs.terms_reqs.gating_asa_list[1] = (
        asset,
        round(TestConsts.acc_dispenser_asa_amt / 3),
    )
    action_inputs.val_owner = val_owner.address
    action_inputs.val_manager = val_manager.address
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    app_id = validator_ad.initialize_delegator_state(
        action_inputs=action_inputs,
        target_state=TEST_DELEGATOR_INITIAL_STATE,
    )
    gs_start = validator_ad.get_global_state()
    gs_del_start = validator_ad.get_delegator_global_state(app_id)

    if asset != ALGO_ASA_ID:
        # Decrease ASA below the limit
        validator_ad.algorand_client.send.asset_transfer(
            AssetTransferParams(
                sender = validator_ad.del_beneficiary.address,
                signer = validator_ad.del_beneficiary.signer,
                receiver = dispenser.address,
                amount = round(gs_del_start.delegation_terms_balance.gating_asa_list[0][1]*4/3),
                asset_id=asset,
            )
        )
    else:
        # Increase ALGO above the limit
        validator_ad.algorand_client.send.payment(
            PayParams(
                sender = dispenser.address,
                signer = dispenser.signer,
                receiver = validator_ad.del_beneficiary.address,
                amount = round(gs_del_start.delegation_terms_balance.stake_max*2),
            )
        )

    # Action succeeds
    res = validator_ad.delegator_action(
        app_id=app_id,
        action_name=TEST_ACTION_NAME,
        action_inputs=action_inputs,
    )

    # Check return
    gs_del_new = validator_ad.get_delegator_global_state(app_id)
    amount = calc_operational_fee(
        gs_del_new.delegation_terms_general.fee_round,
        res.confirmed_round,
        gs_del_new.round_start,
    )
    validator_earns, platforms_earns = calc_earnings(
       amount=amount,
       commission=gs_del_new.delegation_terms_general.commission,
    )

    assert res.return_value == BreachLimitsReturn(
        max_breach_reached = False,
        earnings_distribution = [validator_earns, platforms_earns, asset],
        del_manager=gs_del_new.del_manager,
        msg=list(MSG_CORE_BREACH_LIMITS_ERROR),
    )

    # Check contract state
    gs_exp = gs_start
    setup_earnings = calc_earnings(
        amount=gs_del_new.delegation_terms_general.fee_setup,
        commission=gs_del_new.delegation_terms_general.commission,
    )
    expected_total_earnings = (
        setup_earnings[0] + validator_earns,
        setup_earnings[1] + platforms_earns,
    )
    if asset == ALGO_ASA_ID:
        gs_exp.total_algo_earned = expected_total_earnings[0]
        gs_exp.total_algo_fees_generated = expected_total_earnings[1]
    else:
        assert validator_ad.app_asa_box(asset) == ValidatorASA(
            total_earning=expected_total_earnings[0],
            total_fees_generated=expected_total_earnings[1],
        )
    gs_new = validator_ad.get_global_state()
    assert gs_new == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check delegator contract state
    assert gs_del_new.state == dc.STATE_LIVE

    return

def test_max_breach(
    validator_ad: ValidatorAd,
    asset : int,
    val_owner : AddressAndSigner,
    val_manager : AddressAndSigner,
    dispenser : AddressAndSigner,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    action_inputs.terms_reqs.gating_asa_list[0] = (
        asset,
        balance(
            validator_ad.algorand_client,
            dispenser.address,
            asset
        )*2,
    )
    action_inputs.terms_reqs.gating_asa_list[0] = (
        asset,
        round(TestConsts.acc_dispenser_asa_amt / 2),
    )
    action_inputs.terms_reqs.gating_asa_list[1] = (
        asset,
        round(TestConsts.acc_dispenser_asa_amt / 3),
    )
    action_inputs.val_owner = val_owner.address
    action_inputs.val_manager = val_manager.address
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    app_id = validator_ad.initialize_delegator_state(
        action_inputs=action_inputs,
        target_state=TEST_DELEGATOR_INITIAL_STATE,
    )
    gs_start = validator_ad.get_global_state()

    gs_del_start = validator_ad.get_delegator_global_state(app_id)

    if asset != ALGO_ASA_ID:
        # Decrease ASA below the limit
        validator_ad.algorand_client.send.asset_transfer(
            AssetTransferParams(
                sender = validator_ad.del_beneficiary.address,
                signer = validator_ad.del_beneficiary.signer,
                receiver = dispenser.address,
                amount = round(gs_del_start.delegation_terms_balance.gating_asa_list[0][1]*4/3),
                asset_id=asset,
            )
        )
    else:
        # Increase ALGO above the limit
        validator_ad.algorand_client.send.payment(
            PayParams(
                sender = dispenser.address,
                signer = dispenser.signer,
                receiver = validator_ad.del_beneficiary.address,
                amount = round(gs_del_start.delegation_terms_balance.stake_max*2),
            )
        )

    # Action succeeds
    res : list[ABITransactionResponse] = []
    validator_earns = []
    platforms_earns = []
    for _ in range(gs_del_start.delegation_terms_balance.cnt_breach_del_max):
        res.append(validator_ad.delegator_action(
            app_id=app_id,
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
        ))

        assert res[-1].confirmed_round

        gs_del_new = validator_ad.get_delegator_global_state(app_id)
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
        validator_earns.append(tmp_earn[0])
        platforms_earns.append(tmp_earn[1])

    # Check return
    assert res[-1].return_value == BreachLimitsReturn(
        max_breach_reached = True,
        earnings_distribution=[validator_earns[-1], platforms_earns[-1], asset],
        del_manager=gs_del_new.del_manager,
        msg=list(MSG_CORE_BREACH_LIMITS_END),
    )
    validator_earns = sum(validator_earns)
    platforms_earns = sum(platforms_earns)

    # Check contract state
    gs_exp = gs_start
    gs_exp.cnt_del = 0
    gs_exp.del_app_list[0] = 0
    setup_earnings = calc_earnings(
        amount=gs_del_new.delegation_terms_general.fee_setup,
        commission=gs_del_new.delegation_terms_general.commission,
    )
    expected_total_earnings = (
        setup_earnings[0] + validator_earns,
        setup_earnings[1] + platforms_earns,
    )
    if asset == ALGO_ASA_ID:
        gs_exp.total_algo_earned = expected_total_earnings[0]
        gs_exp.total_algo_fees_generated = expected_total_earnings[1]
    else:
        assert validator_ad.app_asa_box(asset) == ValidatorASA(
            total_earning=expected_total_earnings[0],
            total_fees_generated=expected_total_earnings[1],
        )

    gs_new = validator_ad.get_global_state()
    assert gs_new == gs_exp, ERROR_GLOBAL_STATE_MISMATCH
    assert app_id not in gs_new.del_app_list

    # Check delegator contract state
    assert gs_del_new.state == dc.STATE_ENDED_LIMITS

    return

def test_wrong_app(
    validator_ad : ValidatorAd,
    validator_ad_2 : ValidatorAd,
    val_owner : AddressAndSigner,
    val_manager : AddressAndSigner,
    dispenser : AddressAndSigner,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    action_inputs.val_owner = val_owner.address
    action_inputs.val_manager = val_manager.address
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    validator_ad_2.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    app_id_1 = validator_ad.initialize_delegator_state(  # noqa: F841
        action_inputs=action_inputs,
        target_state=TEST_DELEGATOR_INITIAL_STATE,
    )
    app_id_2 = validator_ad_2.initialize_delegator_state(
        action_inputs=action_inputs,
        target_state=TEST_DELEGATOR_INITIAL_STATE,
    )

    # Top up delegator account to exceed max stake limit
    validator_ad.algorand_client.send.payment(
        PayParams(
            sender=dispenser.address,
            receiver=validator_ad.del_beneficiary.address,
            amount=TestConsts.acc_dispenser_amt,
        )
    )

    # Action fail
    with pytest.raises(LogicError) as e:
        validator_ad.delegator_action(
            app_id=app_id_2,
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
        )
    assert is_expected_logic_error(ERROR_DELEGATOR_DOES_NOT_EXIST_AT_VALIDATOR_AD, e)

    return

def test_wrong_caller(
    validator_ad: ValidatorAd,
    dispenser : AddressAndSigner,
    val_owner : AddressAndSigner,
    val_manager : AddressAndSigner,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    action_inputs.terms_reqs.gating_asa_list[0] = (
        asset,
        balance(
            validator_ad.algorand_client,
            dispenser.address,
            asset
        )*2,
    )
    action_inputs.val_owner = val_owner.address
    action_inputs.val_manager = val_manager.address
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    app_id = validator_ad.initialize_delegator_state(
        action_inputs=action_inputs,
        target_state=TEST_DELEGATOR_INITIAL_STATE,
    )

    # Top up delegator account to exceed max stake limit
    validator_ad.algorand_client.send.payment(
        PayParams(
            sender=dispenser.address,
            receiver=validator_ad.del_beneficiary.address,
            amount=TestConsts.acc_dispenser_amt,
        )
    )

    # Action fail
    with pytest.raises(LogicError) as e:
        validator_ad.acc = dispenser
        validator_ad.delegator_action(
            app_id=app_id,
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
        )
    assert is_expected_logic_error(ERROR_CALLED_BY_NOT_CREATOR, e)

    return
