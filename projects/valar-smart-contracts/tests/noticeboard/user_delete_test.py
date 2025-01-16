
import itertools
from copy import deepcopy

import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.composer import PayParams
from algokit_utils.logic_error import LogicError
from algosdk.constants import ZERO_ADDRESS

from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    DLL_DEL,
    DLL_VAL,
    ERROR_USER_HAS_ACTIVE_CONTRACTS,
    MBR_USER_BOX,
)
from smart_contracts.noticeboard.constants import ROLE_DEL, ROLE_VAL
from tests.conftest import TestConsts
from tests.constants import (
    ERROR_GLOBAL_STATE_MISMATCH,
    SKIP_SAME_AS_FOR_ALGO,
    SKIP_SAME_AS_FOR_VAL,
)
from tests.noticeboard.client_helper import UserInfo, UsersDoubleLinkedList
from tests.noticeboard.utils import Noticeboard
from tests.utils import available_balance, is_expected_logic_error

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "SET"
TEST_ACTION_NAME = "user_delete"

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
    action_account = noticeboard.creator # Can be any account
    noticeboard.noticeboard_action(action_name="user_create",action_inputs=action_inputs,action_account=action_account)
    gs_start = noticeboard.get_global_state()
    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)
    user_bal_start = available_balance(noticeboard.algorand_client, action_account.address, ALGO_ASA_ID)

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
            cnt_users=0,
            user_first=ZERO_ADDRESS,
            user_last=ZERO_ADDRESS,
        )
    else:
        gs_exp.dll_del = UsersDoubleLinkedList(
            cnt_users=0,
            user_first=ZERO_ADDRESS,
            user_last=ZERO_ADDRESS,
        )
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check available balances
    bal_end = noticeboard.app_available_balance(ALGO_ASA_ID)
    assert bal_start == bal_end
    user_bal_end = available_balance(noticeboard.algorand_client, action_account.address, ALGO_ASA_ID)
    paid_fee = res.tx_info["txn"]["txn"]["fee"]
    assert user_bal_start == user_bal_end - MBR_USER_BOX + paid_fee

    # Check that the user box does not exist anymore
    user_box = noticeboard.app_user_box(action_account.address)
    assert not user_box[1]

    return


NUMBER_OF_ACCOUNTS = 3
def all_permutations(n: int) -> list[list[int]]:
    numbers = list(range(n))  # List of integers from 0 to n-1
    return list(itertools.permutations(numbers))

@pytest.fixture(scope="function", params=all_permutations(NUMBER_OF_ACCOUNTS))
def remove_sequence(request: pytest.FixtureRequest) -> list[int]:
    return request.param

def test_three_users(
    noticeboard: Noticeboard,
    asset : int,
    user_role: bytes,
    dispenser: AddressAndSigner,
    remove_sequence: list[int],
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None
    pytest.skip(SKIP_SAME_AS_FOR_VAL) if user_role != ROLE_VAL else None

    # Setup
    action_inputs = ActionInputs(asset=asset, user_role=user_role)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    accounts: list[AddressAndSigner] = []
    # Create accounts
    for _ in range(NUMBER_OF_ACCOUNTS):
        acc = noticeboard.algorand_client.account.random()
        noticeboard.algorand_client.send.payment(
            PayParams(
                sender=dispenser.address,
                receiver=acc.address,
                amount=TestConsts.acc_dispenser_amt,
            )
        )
        accounts.append(acc)

    # Create users on Noticeboard
    for account in accounts:
        noticeboard.noticeboard_action(action_name="user_create", action_inputs=action_inputs, action_account=account)

    gs_start = noticeboard.get_global_state()
    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)

    # Select order for deletion
    remaining = deepcopy(accounts)

    # Action
    for iter_idx, acc_idx in enumerate(remove_sequence):
        noticeboard.noticeboard_action(
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            action_account=accounts[acc_idx],
        )

        # Check contract state after each deletion
        gs_exp = gs_start
        # Check first and last pointers of the double linked list
        if iter_idx < len(accounts)-1:
            idx_first = int(min(remove_sequence[iter_idx+1:]))
            user_first = accounts[idx_first].address

            idx_last = int(max(remove_sequence[iter_idx+1:]))
            user_last = accounts[idx_last].address
        else:
            user_first = ZERO_ADDRESS
            user_last = ZERO_ADDRESS

        gs_exp.dll_val = UsersDoubleLinkedList(
            cnt_users=len(accounts) - (iter_idx+1),
            user_first=user_first,
            user_last=user_last,
        )
        gs_end = noticeboard.get_global_state()
        assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

        # Check available balances
        bal_end = noticeboard.app_available_balance(ALGO_ASA_ID)
        assert bal_start == bal_end

        # Check (remaining) users
        remaining = [acc for acc in remaining if acc.address != accounts[acc_idx].address]
        users_info = [noticeboard.app_get_user_info(acc.address) for acc in remaining]
        for idx, user_info in enumerate(users_info):
            # Check their connections
            prev_user = ZERO_ADDRESS if idx==0 else remaining[idx-1].address
            next_user = ZERO_ADDRESS if idx==len(remaining)-1 else remaining[idx+1].address

            assert user_info == UserInfo(
                role=user_role,
                dll_name=(DLL_DEL if user_role == ROLE_DEL else DLL_VAL),
                prev_user=prev_user,
                next_user=next_user,
            )

    return

def test_cannot_delete_active_user(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state="SET", action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state="READY")
    del_app_id = noticeboard.initialize_delegator_contract_state(  # noqa: F841
        action_inputs=action_inputs,
        val_app_id=val_app_id,
        target_state="READY",
    )

    # Action fail
    with pytest.raises(LogicError) as e:
        noticeboard.noticeboard_action(
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            action_account=noticeboard.del_managers[0],  # Default delegator was used to create a contract
        )
    assert is_expected_logic_error(ERROR_USER_HAS_ACTIVE_CONTRACTS, e)

    with pytest.raises(LogicError) as e:
        noticeboard.noticeboard_action(
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            action_account=noticeboard.val_owners[0],   # Default validator was used to create a contract
        )
    assert is_expected_logic_error(ERROR_USER_HAS_ACTIVE_CONTRACTS, e)
