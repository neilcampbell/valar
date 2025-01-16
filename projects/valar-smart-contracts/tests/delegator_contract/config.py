import copy
import dataclasses
from hashlib import sha256

from algosdk.constants import ZERO_ADDRESS

from smart_contracts.artifacts.delegator_contract.client import (
    DelegationTermsBalance,
    DelegationTermsGeneral,
)
from smart_contracts.delegator_contract.constants import (
    STATE_NONE,
)
from tests.utils import calc_operational_fee

DEFAULT_ROUNDS = 49

DEFAULT_SETUP_DELEGATION_TERMS_GENERAL = DelegationTermsGeneral(
    commission=100_000,
    fee_round=2_000,
    fee_setup=115,
    fee_asset_id=0,
    partner_address=ZERO_ADDRESS,
    fee_round_partner=0,
    fee_setup_partner=0,
    rounds_setup=21,
    rounds_confirm=32,
)

DEFAULT_SETUP_DELEGATION_TERMS_BALANCE = DelegationTermsBalance(
    stake_max=1_000_000_000_000,
    cnt_breach_del_max=3,
    rounds_breach=10,
    gating_asa_list=[(0,0), (0,0)],
)

DEFAULT_FEE_OPERATIONAL = calc_operational_fee(
    DEFAULT_SETUP_DELEGATION_TERMS_GENERAL.fee_round,
    DEFAULT_ROUNDS,
    0,
)

# ------- Data classes -------
@dataclasses.dataclass(kw_only=True)
class ActionInputs:

    tc_sha256 : bytes = dataclasses.field(default_factory=lambda: sha256(b"Test").digest())
    del_manager: str | None = None
    del_beneficiary: str | None = None

    noticeboard_app_id: int = 0

    delegation_terms_general: DelegationTermsGeneral = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_SETUP_DELEGATION_TERMS_GENERAL))  # noqa: E501
    delegation_terms_balance: DelegationTermsBalance = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_SETUP_DELEGATION_TERMS_BALANCE))  # noqa: E501

    rounds_duration: int = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_ROUNDS))

    fee_operational: int = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_FEE_OPERATIONAL))

    amount: int | None = None

    state: bytes = STATE_NONE

    key_reg_vote_first: int | None = None
    key_reg_vote_last: int | None = None
    key_reg_vote_key_dilution: int | None = None
    key_reg_selection: str | None = "TyPKJHa8IcFFwJ0xvx4/uUeGgVk4pp8r90S5J/xya4M="
    key_reg_vote: str | None = "CrPTVLdfR0z5U5Vx2MbcY8pMM8MDq7uSmKL8YJgGwuw="
    key_reg_state_proof: str | None = "wcT8pSuOGU84gHJr67NiasgsMpr5pFir6wnzYCmEddnsp5Ys7mh9zWZ6jJJY7VK8jM3FsBoEnHFboYci8VbNpQ=="  # noqa: E501
    key_reg_sender: str | None = None

    receiver : str | None = None

    wait_until_limit_breach : bool = True

    wait_until_keys_not_submitted : bool = True
    wait_until_keys_not_confirmed : bool = True
    wait_until_expired : bool = True

    wait_expiry_report : bool = True
    before_expiry: int = 7
    report_period: int = 3

    key_reg_before_confirm: bool = True
    key_reg_fee: int | None = None
    key_reg_atomically: bool = False

    wait_until_suspended: bool = False
