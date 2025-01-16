
import pytest
from algokit_utils.logic_error import LogicError
from algosdk.constants import ZERO_ADDRESS

from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    DLL_DEL,
    DLL_VAL,
    ERROR_NOT_STATE_SET,
    ERROR_RECEIVER,
    ERROR_UNKNOWN_USER_ROLE,
    ERROR_USER_ALREADY_EXISTS,
    ERROR_USER_REGISTRATION_FEE_NOT_PAID,
)
from smart_contracts.noticeboard.constants import ROLE_DEL, ROLE_VAL
from tests.constants import (
    ERROR_GLOBAL_STATE_MISMATCH,
    SKIP_SAME_AS_FOR_ALGO,
    SKIP_SAME_AS_FOR_VAL,
)
from tests.noticeboard.client_helper import UserInfo, UsersDoubleLinkedList
from tests.noticeboard.utils import POSSIBLE_STATES, Noticeboard
from tests.utils import is_expected_logic_error

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "SET"
TEST_ACTION_NAME = "user_create"

# ------- Test fixtures -------
@pytest.fixture(scope="function", params=[ROLE_VAL, ROLE_DEL])
def user_role(request: pytest.FixtureRequest) -> bytes:
    return request.param

# ------- Tests -------
def test_action(
    noticeboard: Noticeboard,
    asset : int,
    user_role: bytes,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset, user_role=user_role)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = noticeboard.get_global_state()
    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)

    action_account = noticeboard.creator # Can be any account

    # Action
    res = noticeboard.noticeboard_action(
        action_name=TEST_ACTION_NAME,
        action_inputs=action_inputs,
        action_account=action_account,
    )

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    if user_role == ROLE_VAL:
        gs_exp.dll_val = UsersDoubleLinkedList(
            cnt_users=1,
            user_first=action_account.address,
            user_last=action_account.address,
        )
    else:
        gs_exp.dll_del = UsersDoubleLinkedList(
            cnt_users=1,
            user_first=action_account.address,
            user_last=action_account.address,
        )
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check available balances
    bal_end = noticeboard.app_available_balance(ALGO_ASA_ID)
    user_reg_fee = action_inputs.noticeboard_fees.del_user_reg \
        if user_role == ROLE_DEL \
        else action_inputs.noticeboard_fees.val_user_reg
    assert bal_start + user_reg_fee == bal_end

    # Check created user
    user_info = noticeboard.app_get_user_info(action_account.address)
    assert user_info == UserInfo(
        role=user_role,
        dll_name=(DLL_DEL if user_role == ROLE_DEL else DLL_VAL),
    )

    return

def test_three_users(
    noticeboard: Noticeboard,
    asset : int,
    user_role: bytes,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None
    pytest.skip(SKIP_SAME_AS_FOR_VAL) if user_role != ROLE_VAL else None

    # Setup
    action_inputs = ActionInputs(asset=asset, user_role=user_role)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = noticeboard.get_global_state()
    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)

    accounts = [noticeboard.creator, noticeboard.dispenser, noticeboard.pla_manager] # Select three accounts

    # Action
    for account in accounts:
        noticeboard.noticeboard_action(
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            action_account=account,
        )

    # Check contract state
    gs_exp = gs_start
    if user_role == ROLE_VAL:
        gs_exp.dll_val = UsersDoubleLinkedList(
            cnt_users=len(accounts),
            user_first=accounts[0].address,
            user_last=accounts[-1].address,
        )
    else:
        gs_exp.dll_del = UsersDoubleLinkedList(
            cnt_users=len(accounts),
            user_first=accounts[0].address,
            user_last=accounts[-1].address,
        )
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check available balances
    bal_end = noticeboard.app_available_balance(ALGO_ASA_ID)
    assert bal_start + action_inputs.noticeboard_fees.val_user_reg*len(accounts) == bal_end

    # Check created users
    users_info = [noticeboard.app_get_user_info(account.address) for account in accounts]
    for idx, user_info in enumerate(users_info):
        assert user_info == UserInfo(
            role=user_role,
            dll_name=(DLL_DEL if user_role == ROLE_DEL else DLL_VAL),
            prev_user=ZERO_ADDRESS if idx==0 else accounts[idx-1].address,
            next_user=ZERO_ADDRESS if idx==len(accounts)-1 else accounts[idx+1].address,
        )

    return

def test_user_already_exists_same_role(
    noticeboard: Noticeboard,
    asset : int,
    user_role: bytes,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None
    pytest.skip(SKIP_SAME_AS_FOR_VAL) if user_role != ROLE_VAL else None

    # Setup
    action_inputs = ActionInputs(asset=asset, user_role=user_role)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_USER_ALREADY_EXISTS, e)

    return

def test_user_already_exists_different_role(
    noticeboard: Noticeboard,
    asset : int,
    user_role: bytes,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None
    pytest.skip(SKIP_SAME_AS_FOR_VAL) if user_role != ROLE_VAL else None

    # Setup
    action_inputs = ActionInputs(asset=asset, user_role=user_role)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.user_role = ROLE_DEL
        noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_USER_ALREADY_EXISTS, e)

    return

def test_unknown_role(
    noticeboard: Noticeboard,
    asset : int,
    user_role: bytes,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None
    pytest.skip(SKIP_SAME_AS_FOR_VAL) if user_role != ROLE_VAL else None

    # Setup
    action_inputs = ActionInputs(asset=asset, user_role=user_role)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.user_role = b"_XX_"
        noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    assert is_expected_logic_error(ERROR_UNKNOWN_USER_ROLE, e)

    return

def test_wrong_receiver(
    noticeboard: Noticeboard,
    asset : int,
    user_role: bytes,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None
    pytest.skip(SKIP_SAME_AS_FOR_VAL) if user_role != ROLE_VAL else None

    # Setup
    action_inputs = ActionInputs(asset=asset, user_role=user_role)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.receiver = noticeboard.dispenser.address
        noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_RECEIVER, e)

    return

def test_wrong_amount(
    noticeboard: Noticeboard,
    asset : int,
    user_role: bytes,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None
    pytest.skip(SKIP_SAME_AS_FOR_VAL) if user_role != ROLE_VAL else None

    # Setup
    action_inputs = ActionInputs(asset=asset, user_role=user_role)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.amount = 111
        noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_USER_REGISTRATION_FEE_NOT_PAID, e)

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
    action_inputs = ActionInputs(asset=asset, user_role=ROLE_VAL)
    noticeboard.initialize_state(target_state=init_state, action_inputs=action_inputs)

    if init_state == "SET":
        gs_start = noticeboard.get_global_state()

        # Action success
        res = noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
        assert res.confirmed_round

        # Check new state - should not change
        exp_state = gs_start.state
        gs_end = noticeboard.get_global_state()
        assert gs_end.state == exp_state
    else:
        # Action fail
        with pytest.raises(LogicError) as e:
            noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
        assert is_expected_logic_error(ERROR_NOT_STATE_SET, e)

    return
