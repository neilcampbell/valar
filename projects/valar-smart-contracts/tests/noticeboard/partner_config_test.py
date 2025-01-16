
import pytest
from algokit_utils.logic_error import LogicError

from smart_contracts.artifacts.noticeboard.client import PartnerCommissions
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_CALLED_BY_NOT_PLA_MANAGER,
    ERROR_CALLED_FROM_STATE_RETIRED,
    ERROR_PARTNER_CREATION_FEE_NOT_PAID,
    ERROR_PARTNER_NOT_DELETED,
    ERROR_RECEIVER,
    MBR_PARTNER_BOX,
)
from tests.constants import (
    ERROR_GLOBAL_STATE_MISMATCH,
    SKIP_SAME_AS_FOR_ALGO,
)
from tests.noticeboard.utils import POSSIBLE_STATES, Noticeboard
from tests.utils import is_expected_logic_error

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "SET"
TEST_ACTION_NAME = "partner_config"

# ------- Tests -------
def test_action(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    partner_commissions = PartnerCommissions(
        commission_setup = 63_430,
        commission_operational = 312_449,
    )
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = noticeboard.get_global_state()
    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)

    partner_address = noticeboard.partners[0].address
    action_inputs.partner_address=partner_address
    action_inputs.partner_commissions=partner_commissions
    action_inputs.partner_delete=False

    # Action
    res = noticeboard.noticeboard_action(
        action_name=TEST_ACTION_NAME,
        action_inputs=action_inputs,
    )

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check available balances
    bal_end = noticeboard.app_available_balance(ALGO_ASA_ID)
    assert bal_start == bal_end

    # Check created partner
    partner_info = noticeboard.app_get_partner_commissions(partner_address)
    assert partner_info == partner_commissions

    return

def test_change_partner_commission(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    partner_commissions = PartnerCommissions(
        commission_setup = 63_430,
        commission_operational = 312_449,
    )
    action_inputs = ActionInputs(asset=asset)
    partner_address = noticeboard.partners[0].address
    action_inputs.partner_address=partner_address
    action_inputs.partner_commissions=partner_commissions
    action_inputs.partner_delete=False
    # Initialization to state "SET" creates also a partner if it specified
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = noticeboard.get_global_state()
    bal_start = noticeboard.app_balance(ALGO_ASA_ID)

    new_partner_commission = PartnerCommissions(
        commission_setup = 9_009,
        commission_operational = 444_449,
    )
    action_inputs.partner_commissions = new_partner_commission

    # Action
    res = noticeboard.noticeboard_action(
        action_name=TEST_ACTION_NAME,
        action_inputs=action_inputs,
    )

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check total ALGO balance hasn't changed
    bal_end = noticeboard.app_balance(ALGO_ASA_ID)
    assert bal_start == bal_end

    # Check created partner
    partner_info = noticeboard.app_get_partner_commissions(partner_address)
    assert partner_info == new_partner_commission

    return

def test_delete_partner(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    partner_commissions = PartnerCommissions(
        commission_setup = 63_430,
        commission_operational = 312_449,
    )
    action_inputs = ActionInputs(asset=asset)
    partner_address = noticeboard.partners[0].address
    action_inputs.partner_address=partner_address
    action_inputs.partner_commissions=partner_commissions
    action_inputs.partner_delete=False
    # Initialization to state "SET" creates also a partner if it specified
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    gs_start = noticeboard.get_global_state()
    bal_start = noticeboard.app_available_balance(ALGO_ASA_ID)

    action_inputs.partner_delete=True

    # Action
    res = noticeboard.noticeboard_action(
        action_name=TEST_ACTION_NAME,
        action_inputs=action_inputs,
    )

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check available ALGO balance has been released
    bal_end = noticeboard.app_available_balance(ALGO_ASA_ID)
    assert bal_start == bal_end - MBR_PARTNER_BOX

    # Check partner has been deleted
    partner_info = noticeboard.app_get_partner_commissions(partner_address)
    assert partner_info is None

    return

def test_wrong_receiver(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset, partner_address = noticeboard.partners[0].address)
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
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset, partner_address = noticeboard.partners[0].address)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.amount = 111
        noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_PARTNER_CREATION_FEE_NOT_PAID, e)

    return

def test_wrong_pla_manager(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset, partner_address = noticeboard.partners[0].address)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        # Switch sender not to be the platform manager
        noticeboard.noticeboard_action(
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            action_account=noticeboard.dispenser,
        )

    assert is_expected_logic_error(ERROR_CALLED_BY_NOT_PLA_MANAGER, e)

    return

def test_delete_deleted_partner(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset, partner_address = noticeboard.partners[0].address)
    # Initialization to state "SET" creates also a partner if it specified
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    action_inputs.partner_delete=True
    noticeboard.noticeboard_action(
        action_name=TEST_ACTION_NAME,
        action_inputs=action_inputs,
    )

    # Action fail
    with pytest.raises(LogicError) as e:
        noticeboard.noticeboard_action(
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
        )

    assert is_expected_logic_error(ERROR_PARTNER_NOT_DELETED, e)

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
    partner_commissions = PartnerCommissions(
        commission_setup = 63_430,
        commission_operational = 312_449,
    )
    partner_address = noticeboard.partners[0].address
    action_inputs.partner_address=partner_address
    action_inputs.partner_commissions=partner_commissions
    action_inputs.partner_delete=False

    noticeboard.initialize_state(target_state=init_state, action_inputs=action_inputs)

    if init_state != "RETIRED":
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
        assert is_expected_logic_error(ERROR_CALLED_FROM_STATE_RETIRED, e)

    return
