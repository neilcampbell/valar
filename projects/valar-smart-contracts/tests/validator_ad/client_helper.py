import copy
import dataclasses

from algosdk.abi import ArrayStaticType, ByteType, TupleType, UintType
from algosdk.constants import ZERO_ADDRESS

from smart_contracts.artifacts.validator_ad.client import (
    GlobalState,
    ValidatorSelfDisclosure,
    ValidatorTermsGating,
    ValidatorTermsPricing,
    ValidatorTermsStakeLimits,
    ValidatorTermsTiming,
    ValidatorTermsWarnings,
)
from tests.delegator_contract.client_helper import (
    decode_abi_address,
)

DEFAULT_VALIDATOR_TERMS_TIME = ValidatorTermsTiming(
    rounds_setup = 0,
    rounds_confirm = 0,
    rounds_duration_min = 0,
    rounds_duration_max = 0,
    round_max_end = 0,
)

DEFAULT_VALIDATOR_TERMS_PRICE = ValidatorTermsPricing(
    commission = 0,
    fee_round_min = 0,
    fee_round_var = 0,
    fee_setup = 0,
    fee_asset_id = 0,
)

DEFAULT_VALIDATOR_TERMS_STAKE = ValidatorTermsStakeLimits(
    stake_max = 0,
    stake_gratis = 0,
)

DEFAULT_VALIDATOR_TERMS_REQS = ValidatorTermsGating(
    gating_asa_list = [(0, 0), (0, 0)],
)

DEFAULT_VALIDATOR_TERMS_WARN = ValidatorTermsWarnings(
    cnt_warning_max = 0,
    rounds_warning = 0,
)

DEFAULT_VALIDATOR_SELF_DISCLOSURE = ValidatorSelfDisclosure(
    name = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",  # noqa: E501
    https = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",  # noqa: E501
    country_code = b"\x00\x00",
    hw_cat = 0,
    node_version = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
)

@dataclasses.dataclass(kw_only=True)
class ValidatorAdGlobalState:
    noticeboard_app_id: int = 0

    tc_sha256: bytes = bytes(32)

    terms_time: ValidatorTermsTiming = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_VALIDATOR_TERMS_TIME))  # noqa: E501
    terms_price: ValidatorTermsPricing = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_VALIDATOR_TERMS_PRICE))  # noqa: E501
    terms_stake: ValidatorTermsStakeLimits = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_VALIDATOR_TERMS_STAKE))  # noqa: E501
    terms_reqs: ValidatorTermsGating = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_VALIDATOR_TERMS_REQS))  # noqa: E501
    terms_warn: ValidatorTermsWarnings = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_VALIDATOR_TERMS_WARN))  # noqa: E501

    val_owner: str = ZERO_ADDRESS
    val_manager: str = ZERO_ADDRESS

    val_info: ValidatorSelfDisclosure = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_VALIDATOR_SELF_DISCLOSURE))  # noqa: E501

    state: bytes = b"\x00"

    cnt_del: int = 0
    cnt_del_max: int = 0

    del_app_list: list[int, int, int, int, int, int, int, int, int, int, int, int, int, int] = dataclasses.field(default_factory=lambda: copy.deepcopy([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))  # noqa: E501

    total_algo_earned: int = 0
    total_algo_fees_generated: int = 0

    cnt_asa: int = 0

    @classmethod
    def from_global_state(cls, gs: GlobalState) -> "ValidatorAdGlobalState":
        return cls(
            noticeboard_app_id = gs.noticeboard_app_id,

            tc_sha256 = gs.tc_sha256.as_bytes,

            terms_time = decode_validator_terms_time(gs.terms_time.as_bytes),
            terms_price = decode_validator_terms_price(gs.terms_price.as_bytes),
            terms_stake = decode_validator_terms_stake(gs.terms_stake.as_bytes),
            terms_reqs = decode_validator_terms_reqs(gs.terms_reqs.as_bytes),
            terms_warn = decode_validator_terms_warn(gs.terms_warn.as_bytes),

            val_owner = decode_abi_address(gs.val_owner.as_bytes),
            val_manager = decode_abi_address(gs.val_manager.as_bytes),

            val_info = decode_val_info(gs.val_info.as_bytes),

            state = gs.state.as_bytes,

            cnt_del = gs.cnt_del,
            cnt_del_max = gs.cnt_del_max,

            del_app_list = decode_del_app_list(gs.del_app_list.as_bytes),

            total_algo_earned = gs.total_algo_earned,
            total_algo_fees_generated = gs.total_algo_fees_generated,

            cnt_asa = gs.cnt_asa,
        )

    @classmethod
    def with_defaults(cls) -> "ValidatorAdGlobalState":
        return cls()

@dataclasses.dataclass(kw_only=True)
class ValidatorASA:
    total_earning: int = 0
    total_fees_generated: int = 0

def decode_val_info(data: bytes) -> ValidatorSelfDisclosure:
    val_info_type = TupleType(
        [
            ArrayStaticType(ByteType(), 30),  # name
            ArrayStaticType(ByteType(), 60),  # https
            ArrayStaticType(ByteType(), 2),  # country_code
            UintType(64),  # hw_cat
            ArrayStaticType(ByteType(), 20),  # node_version
        ]
    )

    decoded_tuple = val_info_type.decode(data)

    delegation_terms_balance = ValidatorSelfDisclosure(
        name = bytes(decoded_tuple[0]),
        https = bytes(decoded_tuple[1]),
        country_code = bytes(decoded_tuple[2]),
        hw_cat = decoded_tuple[3],
        node_version = bytes(decoded_tuple[4]),
    )

    return delegation_terms_balance

def decode_del_app_list(data: bytes) -> tuple[int, int, int, int, int, int, int, int, int, int, int, int, int, int]:
    del_app_list_type = ArrayStaticType(UintType(64), 14)

    del_app_list = del_app_list_type.decode(data)

    return del_app_list

def decode_asa_box(data: bytes) -> ValidatorASA:
    validator_asa_type = ArrayStaticType(UintType(64), 2)

    box_contents = validator_asa_type.decode(data)

    asa_box = ValidatorASA(
        total_earning=box_contents[0],
        total_fees_generated=box_contents[1],
    )

    return asa_box


def decode_validator_terms_time(data: bytes) -> ValidatorTermsTiming:
    data_type = TupleType(
        [
            UintType(64),  # rounds_setup
            UintType(64),  # rounds_confirm
            UintType(64),  # rounds_duration_min
            UintType(64),  # rounds_duration_max
            UintType(64),  # round_max_end
        ]
    )

    decoded_tuple = data_type.decode(data)

    decoded_data = ValidatorTermsTiming(
        rounds_setup = decoded_tuple[0],
        rounds_confirm = decoded_tuple[1],
        rounds_duration_min = decoded_tuple[2],
        rounds_duration_max = decoded_tuple[3],
        round_max_end = decoded_tuple[4],
    )

    return decoded_data

def decode_validator_terms_price(data: bytes) -> ValidatorTermsPricing:
    data_type = TupleType(
        [
            UintType(64),  # commission
            UintType(64),  # fee_round_min
            UintType(64),  # fee_round_var
            UintType(64),  # fee_setup
            UintType(64),  # fee_asset_id
        ]
    )

    decoded_tuple = data_type.decode(data)

    decoded_data = ValidatorTermsPricing(
        commission = decoded_tuple[0],
        fee_round_min = decoded_tuple[1],
        fee_round_var = decoded_tuple[2],
        fee_setup = decoded_tuple[3],
        fee_asset_id = decoded_tuple[4],
    )

    return decoded_data

def decode_validator_terms_stake(data: bytes) -> ValidatorTermsStakeLimits:
    data_type = TupleType(
        [
            UintType(64),  # stake_max
            UintType(64),  # stake_gratis
        ]
    )

    decoded_tuple = data_type.decode(data)

    decoded_data = ValidatorTermsStakeLimits(
        stake_max = decoded_tuple[0],
        stake_gratis = decoded_tuple[1],
    )

    return decoded_data

def decode_validator_terms_reqs(data: bytes) -> ValidatorTermsGating:
    data_type = TupleType(
        [
            ArrayStaticType(ArrayStaticType(UintType(64), 2), 2),  # gating_asa_list
        ]
    )

    decoded_tuple = data_type.decode(data)

    decoded_data = ValidatorTermsGating(
        gating_asa_list=[tuple(item) for item in decoded_tuple[0]],
    )

    return decoded_data

def decode_validator_terms_warn(data: bytes) -> ValidatorTermsWarnings:
    data_type = TupleType(
        [
            UintType(64),  # cnt_warning_max
            UintType(64),  # rounds_warning
        ]
    )

    decoded_tuple = data_type.decode(data)

    decoded_data = ValidatorTermsWarnings(
        cnt_warning_max = decoded_tuple[0],
        rounds_warning = decoded_tuple[1],
    )

    return decoded_data
