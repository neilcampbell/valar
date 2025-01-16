
import copy

import pytest
from algokit_utils.logic_error import LogicError
from algosdk.atomic_transaction_composer import (
    AtomicTransactionResponse,
)

import tests.validator_ad.delegator_contract_interface as dc
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    DLL_DEL,
    DLL_VAL,
    ERROR_NOT_STATE_SET,
    ERROR_RECEIVER,
    ERROR_TERMS_AND_CONDITIONS_DONT_MATCH,
    ERROR_USER_APP_LIST_INDEX_TAKEN,
    ERROR_USER_DOES_NOT_EXIST,
    ERROR_USER_NOT_DELEGATOR,
    ERROR_VALIDATOR_AD_DOES_NOT_COMPLY_WITH_TC,
    MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD,
)
from smart_contracts.noticeboard.constants import ROLE_DEL, ROLE_VAL
from tests.conftest import TestConsts
from tests.constants import (
    ERROR_GLOBAL_STATE_MISMATCH,
    SKIP_SAME_AS_FOR_ALGO,
)
from tests.noticeboard.client_helper import UserInfo, UsersDoubleLinkedList
from tests.noticeboard.utils import POSSIBLE_STATES, Noticeboard
from tests.utils import calc_fees_partner, is_expected_logic_error

from .config import (
    DEFAULT_CREATED_DELEGATION_TERMS_BALANCE,
    DEFAULT_CREATED_DELEGATION_TERMS_GENERAL,
    DEFAULT_FEE_ROUND,
    DEFAULT_TC_SHA256,
    ActionInputs,
)

# ------- Test constants -------
TEST_NB_STATE = "SET"
TEST_VA_STATE = "READY"
TEST_DC_STATE = "READY"
TEST_ACTION_NAME = "contract_create"

# ------- Tests -------
def test_action(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    # Create a delegator user
    action_account = noticeboard.del_managers[0]
    action_inputs.user_role = ROLE_DEL
    noticeboard.noticeboard_action("user_create", action_inputs, action_account)
    gs_start = noticeboard.get_global_state()
    gs_val_start = noticeboard.get_validator_ad_global_state(val_app_id)
    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)

    action_inputs.rounds_duration = 55

    # Action
    res: AtomicTransactionResponse = noticeboard.delegator_action(
        app_id=0,
        action_name=TEST_ACTION_NAME,
        action_inputs=action_inputs,
        val_app=val_app_id,
        action_account=action_account,
    )

    # Check return
    del_app_id = res.abi_results[1].return_value
    assert del_app_id != 0

    # Check contract state
    gs_exp = gs_start
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    bal_end = noticeboard.app_available_balance(ALGO_ASA_ID)
    assert bal_start + gs_start.noticeboard_fees.del_contract_creation == bal_end

    # Check created delegator contract state
    gs_del_end = noticeboard.get_delegator_global_state(del_app_id)
    delegation_terms_balance = copy.deepcopy(DEFAULT_CREATED_DELEGATION_TERMS_BALANCE)
    delegation_terms_general = copy.deepcopy(DEFAULT_CREATED_DELEGATION_TERMS_GENERAL)
    delegation_terms_general.fee_asset_id = asset
    gs_del_exp = dc.DelegatorContractGlobalState(
        del_beneficiary = action_account.address,
        del_manager = action_account.address,
        delegation_terms_balance = delegation_terms_balance,
        delegation_terms_general = delegation_terms_general,
        noticeboard_app_id = noticeboard.noticeboard_client.app_id,
        validator_ad_app_id = val_app_id,
        state=dc.STATE_READY,
        tc_sha256=DEFAULT_TC_SHA256,
        round_start=res.confirmed_round,
        round_claim_last=res.confirmed_round,
        round_end=res.confirmed_round + action_inputs.rounds_duration,
    )
    assert gs_del_end == gs_del_exp

    # Check created validator ad state
    gs_val_end = noticeboard.get_validator_ad_global_state(val_app_id)
    gs_val_exp = gs_val_start
    gs_val_exp.cnt_del = 1
    gs_val_exp.del_app_list = [del_app_id] + [0]*(MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD-1)
    assert gs_val_end == gs_val_exp

    # Check delegator
    del_user_info = noticeboard.app_get_user_info(action_account.address)
    del_user_info_exp = UserInfo(
        role=ROLE_DEL,
        dll_name=DLL_DEL,
        app_ids=[del_app_id] + [0]*(len(UserInfo().app_ids)-1),
        cnt_app_ids=1,
    )
    assert del_user_info == del_user_info_exp

    # Check validator
    val_user_info = noticeboard.app_get_user_info(noticeboard.val_owners[0].address)
    val_user_info_exp = UserInfo(
        role=ROLE_VAL,
        dll_name=DLL_VAL,
        app_ids=[val_app_id] + [0]*(len(UserInfo().app_ids)-1),
        cnt_app_ids=1,
    )
    assert val_user_info == val_user_info_exp

    return

def test_user_does_not_exist(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    # Create a delegator user
    action_account = noticeboard.del_managers[0]
    action_inputs.user_role = ROLE_DEL
    noticeboard.noticeboard_action("user_create", action_inputs, action_account)

    # Action fail
    with pytest.raises(LogicError) as e:
        noticeboard.delegator_action(
            app_id=0,
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            val_app=val_app_id,
            action_account=noticeboard.dispenser,
        )
    assert is_expected_logic_error(ERROR_USER_DOES_NOT_EXIST, e)

    return

def test_user_not_delegator(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    # Create a validator user
    action_account = noticeboard.val_managers[0]
    action_inputs.user_role = ROLE_VAL
    noticeboard.noticeboard_action("user_create", action_inputs, action_account)

    # Action fail
    with pytest.raises(LogicError) as e:
        noticeboard.delegator_action(
            app_id=0,
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            val_app=val_app_id,
            action_account=action_account,
        )
    assert is_expected_logic_error(ERROR_USER_NOT_DELEGATOR, e)

    return

def test_wrong_receiver(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    user_role = ROLE_DEL
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    # Create a delegator user
    action_account = noticeboard.del_managers[0]
    action_inputs.user_role = user_role
    noticeboard.noticeboard_action("user_create", action_inputs, action_account)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.receiver = noticeboard.dispenser.address
        noticeboard.delegator_action(
            app_id=0,
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            val_app=val_app_id,
            action_account=action_account,
        )

    assert is_expected_logic_error(ERROR_RECEIVER, e)

    return

def test_wrong_mbr_amount(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    user_role = ROLE_DEL
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    # Create a delegator user
    action_account = noticeboard.del_managers[0]
    action_inputs.user_role = user_role
    noticeboard.noticeboard_action("user_create", action_inputs, action_account)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.amount = 111
        noticeboard.delegator_action(
            app_id=0,
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            val_app=val_app_id,
            action_account=action_account,
        )

    assert "opcodes=gtxns Amount; ==; assert" in str(e.value)

    return

def test_create_delegator_user_and_contract(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)

    gs_val_start = noticeboard.get_validator_ad_global_state(val_app_id)
    gs_start = noticeboard.get_global_state()
    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)

    # Action
    action_inputs.rounds_duration = 55
    action_inputs.del_beneficiary = noticeboard.del_beneficiaries[0].address
    del_app_id = noticeboard.initialize_delegator_contract_state(
        action_inputs=action_inputs,
        val_app_id=val_app_id,
        target_state=TEST_DC_STATE,
        create_new_delegator=True,
    )
    action_account = noticeboard.del_managers[-1]

    # Check return
    assert del_app_id != 0
    last_round = noticeboard.algorand_client.client.algod.status()["last-round"]

    # Check contract state
    gs_exp = gs_start
    gs_exp.dll_del = UsersDoubleLinkedList(
        cnt_users=1,
        user_first=action_account.address,
        user_last=action_account.address,
    )
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    bal_end = noticeboard.app_available_balance(ALGO_ASA_ID)
    assert bal_end == (
        bal_start +
        gs_start.noticeboard_fees.del_contract_creation +
        gs_start.noticeboard_fees.del_user_reg
    )

    # Check created delegator contract state
    gs_del_end = noticeboard.get_delegator_global_state(del_app_id)
    gs_del_exp = dc.DelegatorContractGlobalState(
        del_beneficiary = action_inputs.del_beneficiary,
        del_manager = action_account.address,
        delegation_terms_balance = copy.deepcopy(DEFAULT_CREATED_DELEGATION_TERMS_BALANCE),
        delegation_terms_general = copy.deepcopy(DEFAULT_CREATED_DELEGATION_TERMS_GENERAL),
        noticeboard_app_id = noticeboard.noticeboard_client.app_id,
        validator_ad_app_id = val_app_id,
        state=dc.STATE_READY,
        round_start=last_round,
        round_claim_last=last_round,
        round_end=last_round + action_inputs.rounds_duration,
    )
    gs_del_exp.tc_sha256 = DEFAULT_TC_SHA256
    assert gs_del_end == gs_del_exp

    # Check created validator ad state
    gs_val_end = noticeboard.get_validator_ad_global_state(val_app_id)
    gs_val_exp = gs_val_start
    gs_val_exp.cnt_del = 1
    gs_val_exp.del_app_list = [del_app_id] + [0]*(MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD-1)
    assert gs_val_end == gs_val_exp

    # Check user
    user_info = noticeboard.app_get_user_info(action_account.address)
    user_info_exp = UserInfo(
        role=ROLE_DEL,
        dll_name=DLL_DEL,
        app_ids=[del_app_id] + [0]*(len(UserInfo().app_ids)-1),
        cnt_app_ids=1,
    )
    assert user_info == user_info_exp

    return

def test_create_n_contracts_same_owner_on_same_ad(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    num_contracts = 3
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)

    gs_val_start = noticeboard.get_validator_ad_global_state(val_app_id)
    gs_start = noticeboard.get_global_state()
    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)

    # Action
    del_app_ids = []
    for del_i in range(num_contracts):
        action_inputs.rounds_duration = 55
        action_inputs.del_beneficiary = noticeboard.del_beneficiaries[0].address
        del_app_id = noticeboard.initialize_delegator_contract_state(action_inputs=action_inputs,val_app_id=val_app_id)

        del_app_ids.append(del_app_id)

        # Check return
        assert del_app_id != 0
        last_round = noticeboard.algorand_client.client.algod.status()["last-round"]

        # Check contract state
        gs_exp = copy.deepcopy(gs_start)
        gs_exp.dll_del = UsersDoubleLinkedList(
            cnt_users=1,
            user_first=noticeboard.del_managers[0].address,
            user_last=noticeboard.del_managers[0].address,
        )
        gs_end = noticeboard.get_global_state()
        assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

        bal_end = noticeboard.app_available_balance(ALGO_ASA_ID)
        assert bal_end == (
            bal_start +
            gs_start.noticeboard_fees.del_contract_creation*(del_i+1) +
            gs_start.noticeboard_fees.del_user_reg
        )

        # Check created delegator contract state
        gs_del_end = noticeboard.get_delegator_global_state(del_app_id)
        gs_del_exp = dc.DelegatorContractGlobalState(
            del_beneficiary = action_inputs.del_beneficiary,
            del_manager = noticeboard.del_managers[0].address,
            delegation_terms_balance = DEFAULT_CREATED_DELEGATION_TERMS_BALANCE,
            delegation_terms_general = DEFAULT_CREATED_DELEGATION_TERMS_GENERAL,
            noticeboard_app_id = noticeboard.noticeboard_client.app_id,
            validator_ad_app_id = val_app_id,
            state=dc.STATE_READY,
            round_start=last_round,
            round_claim_last=last_round,
            round_end=last_round + action_inputs.rounds_duration,
        )
        gs_del_exp.tc_sha256 = DEFAULT_TC_SHA256
        assert gs_del_end == gs_del_exp

        # Check validator ad state
        gs_val_end = noticeboard.get_validator_ad_global_state(val_app_id)
        gs_val_exp = gs_val_start
        gs_val_exp.cnt_del = del_i+1
        gs_val_exp.del_app_list = del_app_ids + [0]*(MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD-1-del_i)
        assert gs_val_end == gs_val_exp

        # Check delegator
        user_info = noticeboard.app_get_user_info(noticeboard.del_managers[0].address)
        user_info_exp = UserInfo(
            role=ROLE_DEL,
            dll_name=DLL_DEL,
            app_ids=del_app_ids + [0]*(len(UserInfo().app_ids)-1-del_i),
            cnt_app_ids=del_i+1,
        )
        assert user_info == user_info_exp

        # Check validator
        user_info = noticeboard.app_get_user_info(noticeboard.val_owners[0].address)
        user_info_exp = UserInfo(
            role=ROLE_VAL,
            dll_name=DLL_VAL,
            app_ids=[val_app_id] + [0]*(len(UserInfo().app_ids)-1),
            cnt_app_ids=1,
        )
        assert user_info == user_info_exp

    return

def test_occupied_index(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    action_inputs.del_app_idx = 0
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    noticeboard.initialize_delegator_contract_state(action_inputs=action_inputs,val_app_id=val_app_id)

    # Action fail
    with pytest.raises(LogicError) as e:
        noticeboard.initialize_delegator_contract_state(action_inputs=action_inputs,val_app_id=val_app_id)

    assert is_expected_logic_error(ERROR_USER_APP_LIST_INDEX_TAKEN, e)


    return

def test_not_updated_tcs(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)

    # Change platform's terms and conditions
    action_inputs.tc_sha256 = bytes([0x44]*32)
    noticeboard.noticeboard_action(
        action_name="noticeboard_set",
        action_inputs=action_inputs,
    )

    # Action fail
    with pytest.raises(LogicError) as e:
        del_app_id = noticeboard.initialize_delegator_contract_state(  # noqa: F841
            action_inputs=action_inputs,
            val_app_id=val_app_id,
            target_state=TEST_DC_STATE,
            create_new_delegator=True,
        )

    assert is_expected_logic_error(ERROR_VALIDATOR_AD_DOES_NOT_COMPLY_WITH_TC, e)

    return

def test_not_matching_tcs(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.del_sha256 = bytes([0x99]*32)
        del_app_id = noticeboard.initialize_delegator_contract_state(  # noqa: F841
            action_inputs=action_inputs,
            val_app_id=val_app_id,
            target_state=TEST_DC_STATE,
            create_new_delegator=True,
        )

    assert is_expected_logic_error(ERROR_TERMS_AND_CONDITIONS_DONT_MATCH, e)

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

    gs_val_start = noticeboard.get_validator_ad_global_state(val_app_id)
    gs_start = noticeboard.get_global_state()
    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)

    # Action
    action_inputs.rounds_duration = 55
    action_inputs.del_beneficiary = noticeboard.del_beneficiaries[0].address
    del_app_id = noticeboard.initialize_delegator_contract_state(
        action_inputs=action_inputs,
        val_app_id=val_app_id,
        target_state=TEST_DC_STATE,
        create_new_delegator=True,
    )
    action_account = noticeboard.del_managers[-1]

    # Check return
    assert del_app_id != 0
    last_round = noticeboard.algorand_client.client.algod.status()["last-round"]

    # Check contract state
    gs_exp = gs_start
    gs_exp.dll_del = UsersDoubleLinkedList(
        cnt_users=1,
        user_first=action_account.address,
        user_last=action_account.address,
    )
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    bal_end = noticeboard.app_available_balance(ALGO_ASA_ID)
    assert bal_end == (
        bal_start +
        gs_start.noticeboard_fees.del_contract_creation +
        gs_start.noticeboard_fees.del_user_reg
    )

    # Check created delegator contract state
    gs_del_end = noticeboard.get_delegator_global_state(del_app_id)
    delegation_terms_general = copy.deepcopy(DEFAULT_CREATED_DELEGATION_TERMS_GENERAL)
    delegation_terms_general.partner_address = partner_address
    fee_setup = action_inputs.terms_price.fee_setup
    fee_round = DEFAULT_FEE_ROUND
    fee_setup_partner, fee_round_partner = calc_fees_partner(action_inputs.partner_commissions, fee_setup, fee_round)
    delegation_terms_general.fee_setup_partner = fee_setup_partner
    delegation_terms_general.fee_round_partner = fee_round_partner
    gs_del_exp = dc.DelegatorContractGlobalState(
        del_beneficiary = action_inputs.del_beneficiary,
        del_manager = action_account.address,
        delegation_terms_balance = copy.deepcopy(DEFAULT_CREATED_DELEGATION_TERMS_BALANCE),
        delegation_terms_general = delegation_terms_general,
        noticeboard_app_id = noticeboard.noticeboard_client.app_id,
        validator_ad_app_id = val_app_id,
        state=dc.STATE_READY,
        round_start=last_round,
        round_claim_last=last_round,
        round_end=last_round + action_inputs.rounds_duration,
    )
    gs_del_exp.tc_sha256 = DEFAULT_TC_SHA256
    assert gs_del_end == gs_del_exp

    # Check created validator ad state
    gs_val_end = noticeboard.get_validator_ad_global_state(val_app_id)
    gs_val_exp = gs_val_start
    gs_val_exp.cnt_del = 1
    gs_val_exp.del_app_list = [del_app_id] + [0]*(MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD-1)
    assert gs_val_end == gs_val_exp

    # Check user
    user_info = noticeboard.app_get_user_info(action_account.address)
    user_info_exp = UserInfo(
        role=ROLE_DEL,
        dll_name=DLL_DEL,
        app_ids=[del_app_id] + [0]*(len(UserInfo().app_ids)-1),
        cnt_app_ids=1,
    )
    assert user_info == user_info_exp

    return

def test_w_gating(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs(asset=asset)
    action_inputs.terms_reqs.gating_asa_list[0] = (
        asset,
        round(TestConsts.acc_dispenser_asa_amt / 2),
    )
    action_inputs.terms_reqs.gating_asa_list[1] = (
        asset,
        round(TestConsts.acc_dispenser_asa_amt / 3),
    )
    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    # Create a delegator user
    action_account = noticeboard.del_managers[0]
    action_inputs.user_role = ROLE_DEL
    noticeboard.noticeboard_action("user_create", action_inputs, action_account)
    gs_start = noticeboard.get_global_state()
    gs_val_start = noticeboard.get_validator_ad_global_state(val_app_id)
    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)

    action_inputs.rounds_duration = 55

    # Action
    res: AtomicTransactionResponse = noticeboard.delegator_action(
        app_id=0,
        action_name=TEST_ACTION_NAME,
        action_inputs=action_inputs,
        val_app=val_app_id,
        action_account=action_account,
    )

    # Check return
    del_app_id = res.abi_results[1].return_value
    assert del_app_id != 0

    # Check contract state
    gs_exp = gs_start
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    bal_end = noticeboard.app_available_balance(ALGO_ASA_ID)
    assert bal_start + gs_start.noticeboard_fees.del_contract_creation == bal_end

    # Check created delegator contract state
    gs_del_end = noticeboard.get_delegator_global_state(del_app_id)
    delegation_terms_balance = copy.deepcopy(DEFAULT_CREATED_DELEGATION_TERMS_BALANCE)
    delegation_terms_balance.gating_asa_list = action_inputs.terms_reqs.gating_asa_list
    delegation_terms_general = copy.deepcopy(DEFAULT_CREATED_DELEGATION_TERMS_GENERAL)
    delegation_terms_general.fee_asset_id = asset
    gs_del_exp = dc.DelegatorContractGlobalState(
        del_beneficiary = action_account.address,
        del_manager = action_account.address,
        delegation_terms_balance = delegation_terms_balance,
        delegation_terms_general = delegation_terms_general,
        noticeboard_app_id = noticeboard.noticeboard_client.app_id,
        validator_ad_app_id = val_app_id,
        state=dc.STATE_READY,
        tc_sha256=DEFAULT_TC_SHA256,
        round_start=res.confirmed_round,
        round_claim_last=res.confirmed_round,
        round_end=res.confirmed_round + action_inputs.rounds_duration,
    )
    assert gs_del_end == gs_del_exp

    # Check created validator ad state
    gs_val_end = noticeboard.get_validator_ad_global_state(val_app_id)
    gs_val_exp = gs_val_start
    gs_val_exp.cnt_del = 1
    gs_val_exp.del_app_list = [del_app_id] + [0]*(MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD-1)
    assert gs_val_end == gs_val_exp

    # Check delegator
    del_user_info = noticeboard.app_get_user_info(action_account.address)
    del_user_info_exp = UserInfo(
        role=ROLE_DEL,
        dll_name=DLL_DEL,
        app_ids=[del_app_id] + [0]*(len(UserInfo().app_ids)-1),
        cnt_app_ids=1,
    )
    assert del_user_info == del_user_info_exp

    # Check validator
    val_user_info = noticeboard.app_get_user_info(noticeboard.val_owners[0].address)
    val_user_info_exp = UserInfo(
        role=ROLE_VAL,
        dll_name=DLL_VAL,
        app_ids=[val_app_id] + [0]*(len(UserInfo().app_ids)-1),
        cnt_app_ids=1,
    )
    assert val_user_info == val_user_info_exp

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
    noticeboard.initialize_state(target_state=init_state, action_inputs=action_inputs)

    if init_state == "SET":
        gs_start = noticeboard.get_global_state()

        val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)

        # Action success
        noticeboard.initialize_delegator_contract_state(action_inputs=action_inputs,val_app_id=val_app_id)

        # Check new state - should not change
        exp_state = gs_start.state
        gs_end = noticeboard.get_global_state()
        assert gs_end.state == exp_state
    else:
        # Action fail
        with pytest.raises(LogicError) as e:
            noticeboard.initialize_delegator_contract_state(action_inputs=action_inputs,val_app_id=0)
        assert is_expected_logic_error(ERROR_NOT_STATE_SET, e)

    return
