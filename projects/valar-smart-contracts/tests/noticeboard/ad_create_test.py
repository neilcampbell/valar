
import copy

import pytest
from algokit_utils.logic_error import LogicError

import tests.noticeboard.validator_ad_interface as va
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    DLL_VAL,
    ERROR_AD_CREATION_INCORRECT_PAY_AMOUNT,
    ERROR_NOT_STATE_SET,
    ERROR_RECEIVER,
    ERROR_USER_APP_LIST_INDEX_TAKEN,
    ERROR_USER_DOES_NOT_EXIST,
    ERROR_USER_NOT_VALIDATOR,
)
from smart_contracts.noticeboard.constants import ROLE_DEL, ROLE_VAL
from tests.constants import (
    ERROR_GLOBAL_STATE_MISMATCH,
    SKIP_SAME_AS_FOR_ALGO,
)
from tests.noticeboard.client_helper import UserInfo, UsersDoubleLinkedList
from tests.noticeboard.utils import POSSIBLE_STATES, Noticeboard
from tests.utils import is_expected_logic_error

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "SET"
TEST_ACTION_NAME = "ad_create"

# ------- Tests -------
def test_action(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    user_role = ROLE_VAL
    action_inputs = ActionInputs(asset=asset, user_role=user_role)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    action_account = noticeboard.val_owners[0]
    noticeboard.noticeboard_action(action_name="user_create", action_inputs=action_inputs,action_account=action_account)
    gs_start = noticeboard.get_global_state()
    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)

    # Action
    res = noticeboard.validator_action(
        0,
        action_name=TEST_ACTION_NAME,
        action_inputs=action_inputs,
        action_account=action_account,
    )

    # Check return
    val_app_id = res.return_value
    assert val_app_id != 0

    # Check contract state
    gs_exp = gs_start
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    bal_end = noticeboard.app_available_balance(ALGO_ASA_ID)
    assert bal_start + gs_start.noticeboard_fees.val_ad_creation == bal_end

    # Check created validator ad state
    gs_val_end = noticeboard.get_validator_ad_global_state(val_app_id)
    gs_val_exp = va.ValidatorAdGlobalState(
        noticeboard_app_id = noticeboard.noticeboard_client.app_id,
        val_owner = action_account.address,
        state=va.STATE_CREATED,
    )
    assert gs_val_end == gs_val_exp

    # Check user
    user_info = noticeboard.app_get_user_info(action_account.address)
    user_info_exp = UserInfo(
        role=ROLE_VAL,
        dll_name=DLL_VAL,
        app_ids=[val_app_id] + [0]*(len(UserInfo().app_ids)-1),
        cnt_app_ids=1,
    )
    assert user_info == user_info_exp

    return

def test_user_does_not_exist(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    user_role = ROLE_VAL
    action_inputs = ActionInputs(asset=asset, user_role=user_role)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    noticeboard.noticeboard_action(action_name="user_create", action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        noticeboard.validator_action(
            0,
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            action_account=noticeboard.dispenser,
        )
    assert is_expected_logic_error(ERROR_USER_DOES_NOT_EXIST, e)

    return

def test_user_not_validator(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    # Create a delegator user
    action_account = noticeboard.del_managers[0]
    action_inputs.user_role = ROLE_DEL
    noticeboard.noticeboard_action("user_create", action_inputs, action_account)

    # Action fail
    with pytest.raises(LogicError) as e:
        noticeboard.validator_action(
            0,
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            action_account=action_account,
        )
    assert is_expected_logic_error(ERROR_USER_NOT_VALIDATOR, e)

    return

def test_wrong_receiver(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    user_role = ROLE_VAL
    action_inputs = ActionInputs(asset=asset, user_role=user_role)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    action_account = noticeboard.val_owners[0]
    noticeboard.noticeboard_action(action_name="user_create", action_inputs=action_inputs,action_account=action_account)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.receiver = noticeboard.dispenser.address
        noticeboard.validator_action(0, action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_RECEIVER, e)

    return

def test_wrong_amount(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    user_role = ROLE_VAL
    action_inputs = ActionInputs(asset=asset, user_role=user_role)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    action_account = noticeboard.val_owners[0]
    noticeboard.noticeboard_action(action_name="user_create", action_inputs=action_inputs,action_account=action_account)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.amount = 111
        noticeboard.validator_action(0, action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_AD_CREATION_INCORRECT_PAY_AMOUNT, e)

    return

def test_create_validator_user_and_ad(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = noticeboard.get_global_state()
    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)

    # Action
    val_app_id = noticeboard.initialize_validator_ad_state(
        action_inputs=action_inputs,
        target_state="CREATED",
        create_new_validator=True,
    )
    action_account = noticeboard.val_owners[-1]

    # Check return
    assert val_app_id != 0

    # Check contract state
    gs_exp = gs_start
    gs_exp.dll_val = UsersDoubleLinkedList(
        cnt_users=1,
        user_first=action_account.address,
        user_last=action_account.address,
    )
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    bal_end = noticeboard.app_available_balance(ALGO_ASA_ID)
    assert bal_end == (
        bal_start +
        gs_start.noticeboard_fees.val_ad_creation +
        gs_start.noticeboard_fees.val_user_reg
    )

    # Check created validator ad state
    gs_val_end = noticeboard.get_validator_ad_global_state(val_app_id)
    gs_val_exp = va.ValidatorAdGlobalState(
        noticeboard_app_id = noticeboard.noticeboard_client.app_id,
        val_owner = action_account.address,
        state=va.STATE_CREATED,
    )
    assert gs_val_end == gs_val_exp

    # Check user
    user_info = noticeboard.app_get_user_info(action_account.address)
    user_info_exp = UserInfo(
        role=ROLE_VAL,
        dll_name=DLL_VAL,
        app_ids=[val_app_id] + [0]*(len(UserInfo().app_ids)-1),
        cnt_app_ids=1,
    )
    assert user_info == user_info_exp

    return

def test_create_n_ads_same_owner(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    num_ads = 3
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = noticeboard.get_global_state()
    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)

    # Action
    val_app_ids = []
    for val_ad_i in range(num_ads):
        val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state="CREATED")
        # Check return
        assert val_app_id != 0

        val_app_ids.append(val_app_id)

        # Check contract state
        gs_exp = copy.deepcopy(gs_start)
        gs_exp.dll_val = UsersDoubleLinkedList(
            cnt_users=1,
            user_first=noticeboard.val_owners[0].address,
            user_last=noticeboard.val_owners[0].address,
        )
        gs_end = noticeboard.get_global_state()
        assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

        bal_end = noticeboard.app_available_balance(ALGO_ASA_ID)
        assert bal_end == (
            bal_start +
            gs_start.noticeboard_fees.val_ad_creation*(val_ad_i+1) +
            gs_start.noticeboard_fees.val_user_reg
        )

        # Check created validator ad state
        gs_val_end = noticeboard.get_validator_ad_global_state(val_app_id)
        gs_val_exp = va.ValidatorAdGlobalState(
            noticeboard_app_id = noticeboard.noticeboard_client.app_id,
            val_owner = noticeboard.val_owners[0].address,
            state=va.STATE_CREATED,
        )
        assert gs_val_end == gs_val_exp

        # Check user
        user_info = noticeboard.app_get_user_info(noticeboard.val_owners[0].address)
        user_info_exp = UserInfo(
            role=ROLE_VAL,
            dll_name=DLL_VAL,
            app_ids=val_app_ids + [0]*(len(UserInfo().app_ids)-1-val_ad_i),
            cnt_app_ids=val_ad_i+1,
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
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    action_inputs.val_app_idx = 0
    noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state="CREATED")

    # Action fail
    with pytest.raises(LogicError) as e:
        noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state="CREATED")
    assert is_expected_logic_error(ERROR_USER_APP_LIST_INDEX_TAKEN, e)


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

        # Action success
        val_app_id = noticeboard.initialize_validator_ad_state(
            action_inputs=action_inputs,
            target_state="CREATED",
            create_new_validator=True,
        )
        assert val_app_id != 0

        # Check new state - should not change
        exp_state = gs_start.state
        gs_end = noticeboard.get_global_state()
        assert gs_end.state == exp_state
    else:
        # Action fail
        with pytest.raises(LogicError) as e:
            val_app_id = noticeboard.initialize_validator_ad_state(
                action_inputs=action_inputs,
                target_state="CREATED",
                create_new_validator=True,
            )
        assert is_expected_logic_error(ERROR_NOT_STATE_SET, e)

    return
