
import pytest
from algokit_utils.beta.composer import AssetFreezeParams, AssetTransferParams, PayParams

from smart_contracts.artifacts.noticeboard.client import PartnerCommissions
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
)
from tests.constants import (
    SKIP_NOT_APPLICABLE_TO_ALGO,
)
from tests.noticeboard.utils import Noticeboard
from tests.utils import available_balance, balance

from .config import ActionInputs

# ------- Test constants -------
# More through test just to see if partner function works correctly - on any one action
TEST_NB_STATE = "SET"
TEST_VA_STATE = "READY"
TEST_DC_STATE = "SUBMITTED"
TEST_ACTION_NAME = "keys_confirm"

# ------- Tests -------
def test_action_w_partner(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    # Setup
    partner_address = noticeboard.partners[0].address
    action_inputs = ActionInputs(asset=asset, partner_address=partner_address)

    bal_par_start = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=partner_address,
        asset_id=asset,
    )

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

    paid_partner = gs_del_start.delegation_terms_general.fee_setup_partner

    # Check balance of partner
    bal_par_end = available_balance(
        algorand_client=noticeboard.algorand_client,
        address=partner_address,
        asset_id=asset,
    )
    # Partner should have earned the setup fee portion
    assert bal_par_end == bal_par_start + paid_partner

    return

def test_action_w_partner_frozen(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_NOT_APPLICABLE_TO_ALGO) if asset == ALGO_ASA_ID else None

    # Setup
    partner_address = noticeboard.partners[0].address
    action_inputs = ActionInputs(asset=asset, partner_address=partner_address)

    bal_par_start = balance(
        algorand_client=noticeboard.algorand_client,
        address=partner_address,
        asset_id=asset,
    )

    # Freeze partner
    noticeboard.algorand_client.send.asset_freeze(
        AssetFreezeParams(
            sender=noticeboard.dispenser.address,
            asset_id=asset,
            account=partner_address,
            frozen=True,
            signer=noticeboard.dispenser.signer,
        )
    )

    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    del_app_id = noticeboard.initialize_delegator_contract_state(
        action_inputs=action_inputs,
        val_app_id=val_app_id,
        target_state=TEST_DC_STATE,
    )

    # Action
    res = noticeboard.delegator_action(
        app_id=del_app_id,
        action_name=TEST_ACTION_NAME,
        action_inputs=action_inputs,
        val_app=val_app_id,
    )

    # Check return
    assert res.confirmed_round

    # Check balance of partner
    bal_par_end = balance(
        algorand_client=noticeboard.algorand_client,
        address=partner_address,
        asset_id=asset,
    )
    # Partner should not have earned anything because the partner is frozen
    assert bal_par_end == bal_par_start

    return

def test_action_w_partner_closed_out(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    # Setup
    partner_address = noticeboard.partners[0].address
    action_inputs = ActionInputs(asset=asset, partner_address=partner_address)
    action_inputs.partner_commissions = PartnerCommissions(
        commission_setup = 10**8,
        commission_operational = 10**8,
    )
    action_inputs.terms_price.fee_setup = 10**7  # Set large to see closed partner doesn't get fee even if it'd fund it

    if asset == ALGO_ASA_ID:
        noticeboard.algorand_client.send.payment(
            PayParams(
                sender=noticeboard.partners[0].address,
                signer=noticeboard.partners[0].signer,
                receiver=noticeboard.dispenser.address,
                amount=0,
                close_remainder_to=noticeboard.dispenser.address,
            )
        )
    else:
        noticeboard.algorand_client.send.payment(
            AssetTransferParams(
                sender=noticeboard.partners[0].address,
                signer=noticeboard.partners[0].signer,
                receiver=noticeboard.dispenser.address,
                amount=0,
                asset_id=asset,
                close_asset_to=noticeboard.dispenser.address,
            )
        )

    noticeboard.initialize_state(target_state=TEST_NB_STATE, action_inputs=action_inputs)
    val_app_id = noticeboard.initialize_validator_ad_state(action_inputs=action_inputs, target_state=TEST_VA_STATE)
    del_app_id = noticeboard.initialize_delegator_contract_state(
        action_inputs=action_inputs,
        val_app_id=val_app_id,
        target_state=TEST_DC_STATE,
    )

    # Action
    res = noticeboard.delegator_action(
        app_id=del_app_id,
        action_name=TEST_ACTION_NAME,
        action_inputs=action_inputs,
        val_app=val_app_id,
    )

    # Check return
    assert res.confirmed_round

    # Check balance of partner
    bal_par_end = balance(
        algorand_client=noticeboard.algorand_client,
        address=partner_address,
        asset_id=asset,
    )
    # Partner should have zero or non-existing balance
    if asset == ALGO_ASA_ID:
        assert bal_par_end == 0
    else:
        assert bal_par_end is None

    return
