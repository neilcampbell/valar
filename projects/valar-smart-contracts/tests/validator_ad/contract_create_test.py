
import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.composer import PayParams
from algokit_utils.logic_error import LogicError
from algosdk.logic import get_application_address

import tests.validator_ad.delegator_contract_interface as dc
from smart_contracts.artifacts.validator_ad.client import PartnerCommissions
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_AMOUNT,
    ERROR_CALLED_BY_NOT_CREATOR,
    ERROR_DELEGATION_ENDS_TOO_LATE,
    ERROR_DELEGATION_PERIOD_TOO_LONG,
    ERROR_DELEGATION_PERIOD_TOO_SHORT,
    ERROR_DELEGATOR_LIST_FULL,
    ERROR_NOT_STATE_READY,
    ERROR_RECEIVER,
    ERROR_REQUESTED_MAX_STAKE_TOO_HIGH,
    ERROR_VALIDATOR_FULL,
    MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD,
    MBR_ACCOUNT,
    MBR_VALIDATOR_AD_DELEGATOR_CONTRACT_INCREASE,
)
from tests.constants import ERROR_GLOBAL_STATE_MISMATCH, SKIP_SAME_AS_FOR_ALGO
from tests.utils import (
    available_balance,
    balance,
    calc_fee_round,
    calc_fees_partner,
    calc_operational_fee,
    calc_stake_max,
    is_expected_logic_error,
    wait_for_rounds,
)
from tests.validator_ad.utils import POSSIBLE_STATES, ValidatorAd

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "READY"
TEST_ACTION_NAME = "contract_create"

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
    del_ben_start = balance(
        algorand_client=validator_ad.algorand_client,
        address=validator_ad.del_beneficiary.address,
        asset_id=ALGO_ASA_ID,
    )
    del_stake_max = del_ben_start

    # Action
    res = validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    gs_new = validator_ad.get_global_state()
    # Check if a delegator contract was created
    assert gs_new.del_app_list[0] != 0

    # Check return
    del_app_id = res.abi_results[1].return_value
    assert del_app_id != 0

    # Check contract state
    gs_exp = gs_start
    gs_exp.del_app_list[0] = gs_new.del_app_list[0]
    gs_exp.cnt_del = 1
    assert gs_new == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check delegator contract state
    gs_del_new = validator_ad.get_delegator_global_state(gs_new.del_app_list[0])
    assert gs_del_new.state == dc.STATE_READY
    assert gs_del_new.delegation_terms_balance.stake_max == calc_stake_max(
        del_stake_max,
        gs_start.terms_stake.stake_max,
        gs_start.terms_stake.stake_gratis,
    )
    assert gs_del_new.delegation_terms_general.fee_round == calc_fee_round(
        del_stake_max,
        gs_start.terms_price.fee_round_min,
        gs_start.terms_price.fee_round_var,
    )

    return

@pytest.mark.parametrize("fee_round_min, fee_round_var, del_stake_max, stake_gratis", [
    (543, 83*10**3, 10**(6+1), 661_000),
    (10_123, 83*10**3, 10**(6+6), 661_000),
    (1, 1, 10**(9+6), 661_000),
    (10**6, 10**6, 10**(9+6), 661_000),
    (10**6, 10**6, 10**(6), 661_000),
    (1, 1, 10**(6), 661_000),
])
def test_different_stakes_and_terms(
    validator_ad: ValidatorAd,
    asset : int,
    fee_round_min: int,
    fee_round_var: int,
    del_stake_max: int,
    stake_gratis: int,
    dispenser : AddressAndSigner,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    action_inputs.terms_price.fee_round_min = fee_round_min
    action_inputs.terms_price.fee_round_var = fee_round_var

    del_ben_prestart = balance(
        algorand_client=validator_ad.algorand_client,
        address=validator_ad.del_beneficiary.address,
        asset_id=ALGO_ASA_ID,
    )
    to_fund = del_stake_max - del_ben_prestart
    # Increase ALGO to a max stake
    validator_ad.algorand_client.send.payment(
        PayParams(
            sender = dispenser.address,
            signer = dispenser.signer,
            receiver = validator_ad.del_beneficiary.address,
            amount = to_fund if to_fund > 0 else 0,
        )
    )
    del_ben_start = balance(
        algorand_client=validator_ad.algorand_client,
        address=validator_ad.del_beneficiary.address,
        asset_id=ALGO_ASA_ID,
    )

    action_inputs.terms_stake.stake_gratis = stake_gratis
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = validator_ad.get_global_state()

    # Action
    res = validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    gs_new = validator_ad.get_global_state()
    # Check if a delegator contract was created
    assert gs_new.del_app_list[0] != 0

    # Check return
    del_app_id = res.abi_results[1].return_value
    assert del_app_id != 0

    # Check contract state
    gs_exp = gs_start
    gs_exp.del_app_list[0] = gs_new.del_app_list[0]
    gs_exp.cnt_del = 1
    assert gs_new == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check delegator contract state
    gs_del_new = validator_ad.get_delegator_global_state(gs_new.del_app_list[0])
    assert gs_del_new.state == dc.STATE_READY
    assert gs_del_new.delegation_terms_balance.stake_max == calc_stake_max(
        del_ben_start,
        gs_start.terms_stake.stake_max,
        gs_start.terms_stake.stake_gratis,
    )
    assert gs_del_new.delegation_terms_general.fee_round == calc_fee_round(
        del_ben_start,
        gs_start.terms_price.fee_round_min,
        gs_start.terms_price.fee_round_var,
    )

    # Clean test by returning ALGO
    validator_ad.algorand_client.send.payment(
        PayParams(
            sender = validator_ad.del_beneficiary.address,
            signer = validator_ad.del_beneficiary.signer,
            receiver = dispenser.address,
            amount = to_fund if to_fund > 0 else 0,
        )
    )

    return

def test_max_stake_too_high(
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
        action_inputs.del_stake_max = action_inputs.terms_stake.stake_max + 1
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_REQUESTED_MAX_STAKE_TOO_HIGH, e)

    return

def test_wrong_duration(
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
        action_inputs.rounds_duration = action_inputs.terms_time.rounds_duration_min - 1
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_DELEGATION_PERIOD_TOO_SHORT, e)

    with pytest.raises(LogicError) as e:
        action_inputs.rounds_duration = action_inputs.terms_time.rounds_duration_max + 1
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_DELEGATION_PERIOD_TOO_LONG, e)

    return

def test_would_end_after_deadline(
    validator_ad: ValidatorAd,
    asset : int,
    dispenser: AddressAndSigner,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    action_inputs.terms_time.round_max_end = validator_ad.algorand_client.client.algod.status()["last-round"] + 100
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    gs = validator_ad.get_global_state()
    num_rounds = gs.terms_time.round_max_end - validator_ad.algorand_client.client.algod.status()["last-round"]
    wait_for_rounds(
        validator_ad.algorand_client,
        num_rounds,
        dispenser,
    )

    # Action fail
    with pytest.raises(LogicError) as e:
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_DELEGATION_ENDS_TOO_LATE, e)

    return

def test_wrong_receiver(
    validator_ad: ValidatorAd,
    dispenser : AddressAndSigner,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Need to pre-fund contract
    validator_ad.algorand_client.send.payment(
        PayParams(
            sender=dispenser.address,
            receiver=validator_ad.validator_ad_client.app_address,
            amount=1_000_000,
            signer=dispenser.signer,
        )
    )

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.del_contract_creation_mbr_receiver = validator_ad.acc.address
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_RECEIVER, e)
    action_inputs.del_contract_creation_mbr_receiver = None # Rest to default

    with pytest.raises(LogicError) as e:
        action_inputs.del_contract_creation_fee_receiver = validator_ad.acc.address
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_RECEIVER, e)
    action_inputs.del_contract_creation_fee_receiver = None # Rest to default

    return

def test_wrong_mbr_amount(
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
        action_inputs.del_contract_creation_mbr_amount = MBR_VALIDATOR_AD_DELEGATOR_CONTRACT_INCREASE-1
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_AMOUNT, e)
    action_inputs.del_contract_creation_mbr_amount = None # Rest to default

    return

def test_too_many_delegators_to_store(
    validator_ad: ValidatorAd,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    action_inputs.cnt_del_max = MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    for _ in range(MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD):
        res = validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
        assert res.confirmed_round

    gs_new = validator_ad.get_global_state()
    assert gs_new.cnt_del == MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD

    # Action fail
    with pytest.raises(LogicError) as e:
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_DELEGATOR_LIST_FULL, e)

    return

def test_no_free_space_for_delegator(
    validator_ad: ValidatorAd,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = validator_ad.get_global_state()

    for _ in range(gs_start.cnt_del_max):
        res = validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
        assert res.confirmed_round

    gs_new = validator_ad.get_global_state()
    assert gs_new.cnt_del == gs_new.cnt_del_max

    # Action fail
    with pytest.raises(LogicError) as e:
       validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_VALIDATOR_FULL, e)
    action_inputs.del_contract_creation_mbr_amount = None # Rest to default

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

def test_action_w_partner(
    validator_ad: ValidatorAd,
    partner: AddressAndSigner,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    del_ben_start = balance(
        algorand_client=validator_ad.algorand_client,
        address=validator_ad.del_beneficiary.address,
        asset_id=ALGO_ASA_ID,
    )
    del_stake_max = del_ben_start
    action_inputs.partner_address = partner.address
    action_inputs.partner_commissions = PartnerCommissions(
        commission_setup = 58_020,
        commission_operational = 12_345,
    )
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = validator_ad.get_global_state()

    # Action
    res = validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    gs_new = validator_ad.get_global_state()
    # Check if a delegator contract was created
    del_app_id = gs_new.del_app_list[0]
    assert del_app_id != 0

    # Check return
    del_app_id = res.abi_results[1].return_value
    assert del_app_id != 0

    # Check contract state
    gs_exp = gs_start
    gs_exp.del_app_list[0] = del_app_id
    gs_exp.cnt_del = 1
    assert gs_new == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check delegator contract state
    gs_del_new = validator_ad.get_delegator_global_state(del_app_id)
    assert gs_del_new.state == dc.STATE_READY
    assert gs_del_new.delegation_terms_balance.stake_max == calc_stake_max(
        del_stake_max,
        gs_start.terms_stake.stake_max,
        gs_start.terms_stake.stake_gratis,
    )
    fee_setup = action_inputs.terms_price.fee_setup
    assert gs_del_new.delegation_terms_general.fee_setup == fee_setup
    fee_round = calc_fee_round(
        del_stake_max,
        gs_start.terms_price.fee_round_min,
        gs_start.terms_price.fee_round_var,
    )
    assert gs_del_new.delegation_terms_general.fee_round == fee_round
    fee_setup_partner, fee_round_partner = calc_fees_partner(action_inputs.partner_commissions, fee_setup, fee_round)
    assert gs_del_new.delegation_terms_general.fee_setup_partner == fee_setup_partner
    assert gs_del_new.delegation_terms_general.fee_round_partner == fee_round_partner

    # Check balance of delegator contract
    bal_del_end = available_balance(
        algorand_client=validator_ad.algorand_client,
        address=get_application_address(del_app_id),
        asset_id=asset,
    )
    rounds_duration = action_inputs.rounds_duration
    fee_operational = calc_operational_fee(fee_round, rounds_duration, 0)
    fee_operational_partner = calc_operational_fee(fee_round_partner, rounds_duration, 0)
    assert bal_del_end == (fee_setup + fee_setup_partner + fee_operational + fee_operational_partner) + (0 if asset != ALGO_ASA_ID else MBR_ACCOUNT)  # noqa: E501

    return

@pytest.mark.parametrize("fee_round_min, fee_round_var, del_stake_max, stake_gratis, partner_commissions", [
    (543, 83*10**3, 10**(6+1), 661_000, (58_200, 123_321)),
    (10_123, 83*10**3, 10**(6+6), 10_000, (10_000, 10_000)),
    (1, 1, 10**(9+6), 661_000, (1_000_000, 1_000_000)),
    (10**6, 10**6, 10**(9+6), 661_000, (1_000_000, 1_000_000)),
    (10**6, 10**6, 10**(6), 661_000, (1, 1)),
    (1, 1, 10**(6), 661_000, (1, 1)),
])
def test_w_partner_different_stakes_and_terms(
    validator_ad: ValidatorAd,
    asset : int,
    fee_round_min: int,
    fee_round_var: int,
    del_stake_max: int,
    partner_commissions: int,
    stake_gratis: int,
    partner: AddressAndSigner,
    dispenser: AddressAndSigner,
) -> None:

    # Setup
    action_inputs = ActionInputs()
    action_inputs.terms_price.fee_asset_id = asset
    action_inputs.terms_price.fee_round_min = fee_round_min
    action_inputs.terms_price.fee_round_var = fee_round_var

    del_ben_prestart = balance(
        algorand_client=validator_ad.algorand_client,
        address=validator_ad.del_beneficiary.address,
        asset_id=ALGO_ASA_ID,
    )
    to_fund = del_stake_max - del_ben_prestart
    # Increase ALGO to a max stake
    validator_ad.algorand_client.send.payment(
        PayParams(
            sender = dispenser.address,
            signer = dispenser.signer,
            receiver = validator_ad.del_beneficiary.address,
            amount = to_fund if to_fund > 0 else 0,
        )
    )
    del_ben_start = balance(
        algorand_client=validator_ad.algorand_client,
        address=validator_ad.del_beneficiary.address,
        asset_id=ALGO_ASA_ID,
    )

    action_inputs.terms_stake.stake_gratis = stake_gratis
    action_inputs.partner_address = partner.address
    action_inputs.partner_commissions = PartnerCommissions(
        commission_setup = partner_commissions[0],
        commission_operational = partner_commissions[1],
    )
    validator_ad.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = validator_ad.get_global_state()

    # Action
    res = validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    gs_new = validator_ad.get_global_state()
    # Check if a delegator contract was created
    del_app_id = gs_new.del_app_list[0]
    assert del_app_id != 0

    # Check return
    del_app_id = res.abi_results[1].return_value
    assert del_app_id != 0

    # Check contract state
    gs_exp = gs_start
    gs_exp.del_app_list[0] = del_app_id
    gs_exp.cnt_del = 1
    assert gs_new == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check delegator contract state
    gs_del_new = validator_ad.get_delegator_global_state(del_app_id)
    assert gs_del_new.state == dc.STATE_READY
    assert gs_del_new.delegation_terms_balance.stake_max == calc_stake_max(
        del_ben_start,
        gs_start.terms_stake.stake_max,
        gs_start.terms_stake.stake_gratis,
    )
    fee_setup = action_inputs.terms_price.fee_setup
    assert gs_del_new.delegation_terms_general.fee_setup == fee_setup
    fee_round = calc_fee_round(
        del_ben_start,
        gs_start.terms_price.fee_round_min,
        gs_start.terms_price.fee_round_var,
    )
    assert gs_del_new.delegation_terms_general.fee_round == fee_round
    fee_setup_partner, fee_round_partner = calc_fees_partner(action_inputs.partner_commissions, fee_setup, fee_round)
    assert gs_del_new.delegation_terms_general.fee_setup_partner == fee_setup_partner
    assert gs_del_new.delegation_terms_general.fee_round_partner == fee_round_partner

    # Check balance of delegator contract
    bal_del_end = available_balance(
        algorand_client=validator_ad.algorand_client,
        address=get_application_address(del_app_id),
        asset_id=asset,
    )
    rounds_duration = action_inputs.rounds_duration
    fee_operational = calc_operational_fee(fee_round, rounds_duration, 0)
    fee_operational_partner = calc_operational_fee(fee_round_partner, rounds_duration, 0)
    assert bal_del_end == (fee_setup + fee_setup_partner + fee_operational + fee_operational_partner) + (0 if asset != ALGO_ASA_ID else MBR_ACCOUNT)  # noqa: E501

    # Clean test by returning ALGO
    validator_ad.algorand_client.send.payment(
        PayParams(
            sender = validator_ad.del_beneficiary.address,
            signer = validator_ad.del_beneficiary.signer,
            receiver = dispenser.address,
            amount = to_fund if to_fund > 0 else 0,
        )
    )

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

    if init_state == "READY":
        gs_start = validator_ad.get_global_state()

        # Action success
        validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

        # Check new state of ValidatorAd - should not change
        exp_state = gs_start.state
        gs_end = validator_ad.get_global_state()
        assert gs_end.state == exp_state
    else:
        # Action fail
        with pytest.raises(LogicError) as e:
            validator_ad.action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
        assert is_expected_logic_error(ERROR_NOT_STATE_READY, e)

    return
