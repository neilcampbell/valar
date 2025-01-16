

from smart_contracts.artifacts.noticeboard.client import NoticeboardAssetInfo
from tests.noticeboard.utils import Noticeboard

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "SET"
TEST_ACTION_NAME = "get_noticeboard_asset"

# ------- Tests -------
def test_action(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    # Ensure contract is opted-in the asset that will be added
    noticeboard.noticeboard_action(action_name="noticeboard_optin_asa", action_inputs=action_inputs)
    action_inputs.asset_info = NoticeboardAssetInfo(
        accepted=True,
        fee_round_min_min=10,
        fee_round_var_min=23,
        fee_setup_min=412_002,
    )

    # Action
    res = noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    asset_info = noticeboard.app_get_asset_info(asset)
    assert res.return_value == asset_info

    return
