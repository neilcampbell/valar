import dataclasses

from algosdk.abi import AddressType, ArrayStaticType, TupleType, UintType
from algosdk.constants import ZERO_ADDRESS

from smart_contracts.artifacts.delegator_contract.client import (
    DelegationTermsBalance,
    DelegationTermsGeneral,
    GlobalState,
)

DEFAULT_DELEGATION_TERMS_BALANCE = DelegationTermsBalance(
    stake_max = 0,
    cnt_breach_del_max = 0,
    rounds_breach = 0,
    gating_asa_list = [(0, 0), (0, 0)],
)

DEFAULT_DELEGATION_TERMS_GENERAL = DelegationTermsGeneral(
    commission = 0,
    fee_round = 0,
    fee_setup = 0,
    fee_asset_id = 0,
    partner_address = ZERO_ADDRESS,
    fee_round_partner = 0,
    fee_setup_partner = 0,
    rounds_setup = 0,
    rounds_confirm = 0,
)

@dataclasses.dataclass(kw_only=True)
class DelegatorContractGlobalState:
    cnt_breach_del: int = 0
    del_beneficiary: str = ZERO_ADDRESS
    del_manager: str = ZERO_ADDRESS
    delegation_terms_balance: DelegationTermsBalance = dataclasses.field(default_factory=lambda: DEFAULT_DELEGATION_TERMS_BALANCE)  # noqa: E501
    delegation_terms_general: DelegationTermsGeneral = dataclasses.field(default_factory=lambda: DEFAULT_DELEGATION_TERMS_GENERAL)  # noqa: E501
    fee_operational: int = 0
    fee_operational_partner: int = 0
    noticeboard_app_id: int = 0
    round_breach_last: int = 0
    round_claim_last: int = 0
    round_end: int = 0
    round_ended: int = 0
    round_expiry_soon_last: int = 0
    round_start: int = 0
    sel_key: bytes = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # noqa: E501
    state: bytes = b"\x00"
    state_proof_key: bytes = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # noqa: E501
    tc_sha256: bytes = bytes(32)
    validator_ad_app_id: int = 0
    vote_key: bytes = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # noqa: E501
    vote_key_dilution: int = 0

    @classmethod
    def from_global_state(cls, gs: GlobalState) -> "DelegatorContractGlobalState":
        return cls(
            cnt_breach_del = gs.cnt_breach_del,
            del_beneficiary = decode_abi_address(gs.del_beneficiary.as_bytes),
            del_manager = decode_abi_address(gs.del_manager.as_bytes),
            delegation_terms_balance = decode_delegation_terms_balance(gs.delegation_terms_balance.as_bytes),
            delegation_terms_general = decode_delegation_terms_general(gs.delegation_terms_general.as_bytes),
            fee_operational = gs.fee_operational,
            fee_operational_partner = gs.fee_operational_partner,
            noticeboard_app_id = gs.noticeboard_app_id,
            round_breach_last = gs.round_breach_last,
            round_claim_last = gs.round_claim_last,
            round_end = gs.round_end,
            round_ended = gs.round_ended,
            round_expiry_soon_last = gs.round_expiry_soon_last,
            round_start = gs.round_start,
            sel_key = gs.sel_key.as_bytes,
            state = gs.state.as_bytes,
            state_proof_key = gs.state_proof_key.as_bytes,
            tc_sha256 = gs.tc_sha256.as_bytes,
            validator_ad_app_id = gs.validator_ad_app_id,
            vote_key = gs.vote_key.as_bytes,
            vote_key_dilution = gs.vote_key_dilution,
        )

    @classmethod
    def with_defaults(cls) -> "DelegatorContractGlobalState":
        return cls()


def decode_delegation_terms_balance(data: bytes) -> DelegationTermsBalance:
    delegation_terms_balance_type = TupleType(
        [
            UintType(64),  # stake_max
            UintType(64),  # cnt_breach_del_max
            UintType(64),  # rounds_breach
            ArrayStaticType(ArrayStaticType(UintType(64), 2), 2),  # gating_asa_list
        ]
    )

    decoded_tuple = delegation_terms_balance_type.decode(data)

    delegation_terms_balance = DelegationTermsBalance(
        stake_max=decoded_tuple[0],
        cnt_breach_del_max=decoded_tuple[1],
        rounds_breach=decoded_tuple[2],
        gating_asa_list=[tuple(item) for item in decoded_tuple[3]],
    )

    return delegation_terms_balance

def decode_delegation_terms_general(data: bytes) -> DelegationTermsGeneral:
    delegation_terms_general_type = TupleType(
        [
            UintType(64),  # commission
            UintType(64),  # fee_round
            UintType(64),  # fee_setup
            UintType(64),  # fee_asset_id
            AddressType(),  # partner_address
            UintType(64),  # fee_round_partner
            UintType(64),  # fee_setup_partner
            UintType(64),  # rounds_setup
            UintType(64),  # rounds_confirm
        ]
    )

    decoded_tuple = delegation_terms_general_type.decode(data)

    delegation_terms_general = DelegationTermsGeneral(
        commission=decoded_tuple[0],
        fee_round=decoded_tuple[1],
        fee_setup=decoded_tuple[2],
        fee_asset_id=decoded_tuple[3],
        partner_address=decoded_tuple[4],
        fee_round_partner=decoded_tuple[5],
        fee_setup_partner=decoded_tuple[6],
        rounds_setup=decoded_tuple[7],
        rounds_confirm=decoded_tuple[8],
    )

    return delegation_terms_general


def decode_abi_address(data: bytes) -> str:
    return AddressType().decode(data)


