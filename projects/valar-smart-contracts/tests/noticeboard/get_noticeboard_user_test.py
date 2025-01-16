

from smart_contracts.artifacts.noticeboard.client import UserInfo
from tests.noticeboard.utils import Noticeboard

from .config import ActionInputs

# ------- Test constants -------
TEST_NB_STATE = "SET"
TEST_VA_STATE = "READY"
TEST_DC_STATE = "LIVE"
TEST_ACTION_NAME = "get_noticeboard_user"

# ------- Tests -------
def test_action(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    del_app_id = noticeboard.initialize_delegator_contract_state(
        action_inputs=action_inputs,
        val_app_id=val_app_id,
        target_state=TEST_DC_STATE,
    )

    gs_val_start = noticeboard.get_validator_ad_global_state(val_app_id)
    gs_del_start = noticeboard.get_delegator_global_state(del_app_id)

    # Action
    action_inputs.user_to_get = gs_val_start.val_owner
    res = noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return of validator owner matches its box contents
    user_info = noticeboard.app_get_user_info(action_inputs.user_to_get)
    assert vars(res.return_value) == vars(UserInfo(
        role=list(user_info.role),
        dll_name=list(user_info.dll_name),
        prev_user=user_info.prev_user,
        next_user=user_info.next_user,
        app_ids=user_info.app_ids,
        cnt_app_ids=user_info.cnt_app_ids,
    ))

    # Action
    action_inputs.user_to_get = gs_del_start.del_manager
    res = noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return of delegator manager matches its box contents
    user_info = noticeboard.app_get_user_info(action_inputs.user_to_get)
    assert vars(res.return_value) == vars(UserInfo(
        role=list(user_info.role),
        dll_name=list(user_info.dll_name),
        prev_user=user_info.prev_user,
        next_user=user_info.next_user,
        app_ids=user_info.app_ids,
        cnt_app_ids=user_info.cnt_app_ids,
    ))

    return
