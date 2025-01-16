import copy
import dataclasses
from hashlib import sha256

from algosdk.constants import ZERO_ADDRESS

from smart_contracts.artifacts.validator_ad.client import (
    PartnerCommissions,
    ValidatorSelfDisclosure,
    ValidatorTermsGating,
    ValidatorTermsPricing,
    ValidatorTermsStakeLimits,
    ValidatorTermsTiming,
    ValidatorTermsWarnings,
)
from smart_contracts.delegator_contract.constants import (
    STATE_NONE,
)

DEFAULT_VALIDATOR_TERMS_TIME = ValidatorTermsTiming(
    rounds_setup = 11,
    rounds_confirm = 22,
    rounds_duration_min = 43,
    rounds_duration_max = 64,
    round_max_end = 999_999_999,
)

DEFAULT_VALIDATOR_TERMS_PRICE = ValidatorTermsPricing(
    commission = 100_000,
    fee_round_min = 2,
    fee_round_var = 11,
    fee_setup = 115,
    fee_asset_id = 0,
)

DEFAULT_VALIDATOR_TERMS_STAKE = ValidatorTermsStakeLimits(
    stake_max = 11_111_111_111_000_000,
    stake_gratis = 85_000,
)

DEFAULT_VALIDATOR_TERMS_REQS = ValidatorTermsGating(
    gating_asa_list = [(0, 0), (0, 0)],
)

DEFAULT_VALIDATOR_TERMS_WARN = ValidatorTermsWarnings(
    cnt_warning_max = 3,
    rounds_warning = 10,
)

DEFAULT_VALIDATOR_SELF_DISCLOSURE = ValidatorSelfDisclosure(
    name = b"Silvio M".ljust(30, b" "),
    https = b"google.com".ljust(60, b" "),
    country_code = b"CH",
    hw_cat = 999_999_999,
    node_version = b"3.25.0-future".ljust(20, b" "),
)

DEFAULT_PARTNER_COMMISSIONS = PartnerCommissions(
    commission_setup = 0,
    commission_operational = 0,
)

# ------- Data classes -------
@dataclasses.dataclass(kw_only=True)
class ActionInputs:

    # ------- For validator ad -------

    val_manager: str | None = "E7B5AJ4UV3RSZCP3D5KUR5MEQCWI4OWNJI7YTTLWST63FHOQ2CZHWJUQYQ"
    val_owner: str | None = "VRQRBYXOOZHPGAMGGT4LKFG35IZK7AWVEHQIGRMXUCFIKE5CSXKST265RY"

    ad_terms_mbr: int | None = None

    noticeboard_app_id: int = 0

    tc_sha256: bytes = dataclasses.field(default_factory=lambda: sha256(b"Test").digest())

    state: bytes = STATE_NONE

    live: bool | None = None
    cnt_del_max: int = 3

    ready: bool | None = None

    val_info: ValidatorSelfDisclosure = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_VALIDATOR_SELF_DISCLOSURE))  # noqa: E501

    terms_time: ValidatorTermsTiming = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_VALIDATOR_TERMS_TIME))  # noqa: E501
    terms_price: ValidatorTermsPricing = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_VALIDATOR_TERMS_PRICE))  # noqa: E501
    terms_stake: ValidatorTermsStakeLimits = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_VALIDATOR_TERMS_STAKE))  # noqa: E501
    terms_reqs: ValidatorTermsGating = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_VALIDATOR_TERMS_REQS))  # noqa: E501
    terms_warn: ValidatorTermsWarnings = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_VALIDATOR_TERMS_WARN))  # noqa: E501

    income_asset_id : int | None = None

    receiver : str | None = None

    template_size : int | None = None
    template_box_mbr_amount : int | None = None
    template_box_mbr_receiver : str | None = None

    template_test_data_chunk : bytes | None = None
    template_test_offset : int | None = None

    # ------- For delegator contract -------

    del_contract_creation_mbr_amount : int | None = None
    del_contract_creation_mbr_receiver : str | None = None
    del_contract_creation_fee_receiver : str | None = None
    del_contract_creation_fee_amount : int | None = None

    del_stake_max : int | None = None

    del_manager: str | None = None
    del_beneficiary: str | None = None

    rounds_duration: int = 49

    partner_address: str = ZERO_ADDRESS
    partner_commissions: PartnerCommissions = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_PARTNER_COMMISSIONS))  # noqa: E501

    state_del: bytes = STATE_NONE

    key_reg_vote_first: int | None = None
    key_reg_vote_last: int | None = None
    key_reg_vote_key_dilution: int | None = None
    key_reg_selection: str | None = "TyPKJHa8IcFFwJ0xvx4/uUeGgVk4pp8r90S5J/xya4M="
    key_reg_vote: str | None = "CrPTVLdfR0z5U5Vx2MbcY8pMM8MDq7uSmKL8YJgGwuw="
    key_reg_state_proof: str | None = "wcT8pSuOGU84gHJr67NiasgsMpr5pFir6wnzYCmEddnsp5Ys7mh9zWZ6jJJY7VK8jM3FsBoEnHFboYci8VbNpQ=="  # noqa: E501
    key_reg_sender: str | None = None

    updating : bool = False

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
