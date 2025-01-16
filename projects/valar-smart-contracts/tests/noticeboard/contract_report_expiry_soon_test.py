
import base64

import pytest
from algokit_utils.logic_error import LogicError

from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_APP_NOT_WITH_USER,
    MSG_CORE_WILL_EXPIRE,
)
from tests.constants import (
    SKIP_SAME_AS_FOR_ALGO,
)
from tests.noticeboard.utils import Noticeboard
from tests.utils import is_expected_logic_error

from .config import ActionInputs

# ------- Test constants -------
TEST_NB_STATE = "SET"
TEST_VA_STATE = "READY"
TEST_DC_STATE = "LIVE"
TEST_ACTION_NAME = "contract_report_expiry_soon"

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

    gs_del_start = noticeboard.get_delegator_global_state(del_app_id)

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
    assert base64.b64decode(res.tx_info["inner-txns"][-1]["txn"]["txn"]["note"]) == MSG_CORE_WILL_EXPIRE

    # Check delegator contract state
    gs_del_end = noticeboard.get_delegator_global_state(del_app_id)
    gs_del_exp = gs_del_start
    gs_del_exp.round_expiry_soon_last = res.confirmed_round
    assert gs_del_end == gs_del_exp

    return

def test_action_twice(
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

    gs_del_start = noticeboard.get_delegator_global_state(del_app_id)

    # Action 1st
    res = noticeboard.delegator_action(
        app_id=del_app_id,
        action_name=TEST_ACTION_NAME,
        action_inputs=action_inputs,
        val_app=val_app_id,
    )

    # Action 2nd
    res = noticeboard.delegator_action(
        app_id=del_app_id,
        action_name=TEST_ACTION_NAME,
        action_inputs=action_inputs,
        val_app=val_app_id,
    )

    # Check return
    assert res.confirmed_round

    # Check notification message was sent
    assert base64.b64decode(res.tx_info["inner-txns"][-1]["txn"]["txn"]["note"]) == MSG_CORE_WILL_EXPIRE

    # Check delegator contract state
    gs_del_end = noticeboard.get_delegator_global_state(del_app_id)
    gs_del_exp = gs_del_start
    gs_del_exp.round_expiry_soon_last = res.confirmed_round
    assert gs_del_end == gs_del_exp

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

    return
