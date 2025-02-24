"""Various utility functions, including interaction with the Valar Smart Contracts.
"""
import base64
import struct
import dataclasses

from algosdk.error import AlgodHTTPError
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils import TransactionParameters, ABITransactionResponse
from algokit_utils.network_clients import AlgoClientConfig, AlgoClientConfigs
from algosdk.abi import AddressType, ArrayStaticType, ByteType, TupleType, UintType

from valar_daemon.NoticeboardClient import NoticeboardClient, KeyRegTxnInfo
from valar_daemon.DelegatorContractClient import (
    DelegationTermsBalance,
    DelegationTermsGeneral,
    GlobalState as DelcoGlobalState
)
from valar_daemon.ValidatorAdClient import ValidatorTermsTiming
from valar_daemon.constants import *



### Misc utilities #####################################################################################################

def get_algorand_client(
    algod_config_server: str,
    algod_config_token: str
) -> AlgorandClient:
    """Get an algorand client from the provided configuration.

    Parameters
    ----------
    algod_config_server : str
        Algod URL.
    algod_config_token : str
        Algod token.

    Returns
    -------
    AlgorandClient
        Configured Algorand client without timeout.
    """
    algod_config = AlgoClientConfig(
        server=algod_config_server,
        token=algod_config_token
    )
    indexer_config = AlgoClientConfig(
        server='http://localhost:8980',
        token='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    )
    kmd_config = AlgoClientConfig(
        server='http://localhost:4002',
        token='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    )
    algorand_client = AlgorandClient(
        AlgoClientConfigs(
            algod_config=algod_config,
            indexer_config=indexer_config,
            kmd_config=kmd_config,
        )
    )
    algorand_client.set_suggested_params_timeout(0)
    return algorand_client


def decode_uint64_list(
    data: bytes
) -> list:
    """Decode a string of bytes.

    Args:
        data (bytes): String of bytes.

    Returns:
        list: Decoded bytes.
    """
    # Determine the number of uint64 values in the bytes object
    num_uint64 = len(data) // 8

    # Unpack the bytes object into a list of uint64 values (big-endian)
    int_list = list(struct.unpack(f">{num_uint64}Q", data))

    return int_list


@dataclasses.dataclass()
class User:
    role: bytes
    address: str

    def to_box_name(self) -> bytes:
        return self.role + AddressType().encode(self.address)


# @dataclasses.dataclass()
# class SecurityDeposit:
#     blocked: int = 0
#     total: int = 0

#     @classmethod
#     def from_bytes(cls, data: bytes) -> "SecurityDeposit":
#         data_type = TupleType(
#             [
#                 UintType(64),   # blocked
#                 UintType(64),   # total
#             ]
#         )
#         decoded_tuple = data_type.decode(data)

#         return SecurityDeposit(
#             blocked=decoded_tuple[0],
#             total=decoded_tuple[1],
#         )



### Delegator contract client helpers ##################################################################################

from typing import Tuple, List
def get_delco_fee_and_gating_asa_id(
    global_state_raw: DelcoGlobalState
) -> Tuple[int, List[int]]:
    """Get the fee and gating ASA IDs by interpreting the delco global state.

    Notes
    -----
    Algo ASA is added by default, since it is staked.
    The payment ASA is also included in the gating ASA list.

    Parameters
    ----------
    global_state_raw : DelcoGlobalState
        Uninterpreted delco global state.

    Returns
    -------
    Tuple[int, List[int]]
    """
    global_state = DelegatorContractGlobalState.from_global_state(global_state_raw)
    gating_asa_id_list = [ALGO_ASA_ID] # By defaults, since ALGO is the one staked
    for asa in global_state.delegation_terms_balance.gating_asa_list:
        if asa[0] != ALGO_ASA_ID:
            gating_asa_id_list.append(asa[0]) # Add up to 4 additional ASAs
    return (
        global_state.delegation_terms_general.fee_asset_id,
        gating_asa_id_list
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


def decode_abi_address(data: bytes) -> str:
    return AddressType().decode(data)


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
    def from_global_state(cls, gs: DelcoGlobalState) -> "DelegatorContractGlobalState":
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



### Validator ad client helpers ########################################################################################

DEFAULT_VALIDATOR_TERMS_TIME = ValidatorTermsTiming(
    rounds_setup = 0,
    rounds_confirm = 0,
    rounds_duration_min = 0,
    rounds_duration_max = 0,
    round_max_end = 0,
)


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



### Valar Smart Contract interface #####################################################################################


@dataclasses.dataclass()
class UserInfo:
    """
    UserInfo(): Creates a new object with user info with all values initialized to zero by default.
    """
    role: bytes = b""
    dll_name: bytes = b""

    prev_user: str = ZERO_ADDRESS
    next_user: str = ZERO_ADDRESS

    app_ids: list[int] = dataclasses.field(default_factory=lambda: [0] * 110)
    cnt_app_ids: int = 0

    @classmethod
    def from_bytes(cls, data: bytes) -> "UserInfo":
        data_type = TupleType(
            [
                ArrayStaticType(ByteType(), 4),    # role
                ArrayStaticType(ByteType(), 8),    # dll_name
                AddressType(),   # prev_user
                AddressType(),   # next_user
                ArrayStaticType(UintType(64), 110),   # app_ids
                UintType(64),   # cnt_app_ids
            ]
        )
        decoded_tuple = data_type.decode(data)

        return UserInfo(
            role=bytes(decoded_tuple[0]),
            dll_name=bytes(decoded_tuple[1]),
            prev_user=decoded_tuple[2],
            next_user=decoded_tuple[3],
            app_ids= decoded_tuple[4],
            cnt_app_ids=decoded_tuple[5],
        )

    def get_free_app_idx(self) -> int | None:
        return self.get_app_idx(0)

    def get_app_idx(self, app_id: int) -> int | None:
        try:
            val_app_idx = self.app_ids.index(app_id)
        except ValueError:
            val_app_idx = None
        return val_app_idx
    

def app_get_user_info(
    algorand_client,
    noticeboard_app_id,
    user: str,
) -> UserInfo | None:
    box_raw = app_user_box(
        algorand_client,
        noticeboard_app_id,
        user
    )
    if box_raw[1]:
        user_info = UserInfo.from_bytes(box_raw[0])
    else:
        user_info = None
    return user_info


def app_user_box(
    algorand_client,
    noticeboard_app_id,
    user: str,
) -> tuple[bytes, bool]:
    box_name = AddressType().encode(user)
    box_raw = app_box(
        algorand_client,
        noticeboard_app_id,
        box_name=box_name
    )
    return box_raw


def app_box(
    algorand_client,
    noticeboard_app_id,
    box_name: bytes,
) -> tuple[bytes, bool]:
    return get_box(
        algorand_client=algorand_client,
        box_name=box_name,
        app_id=noticeboard_app_id
    )


def get_box(
    algorand_client : AlgorandClient,
    box_name : bytes,
    app_id : int,
) -> tuple[bytes, bool]:

    exists = False
    box_raw = b""

    try:
        box_raw = algorand_client.client.algod.application_box_by_name(
            application_id=app_id,
            box_name=box_name,
        )
        box_raw = base64.b64decode(box_raw["value"])
        exists = True
    except AlgodHTTPError:
        pass
    except Exception as e:
        print(e)

    return [box_raw, exists]


def get_val_and_del_app_idx(
    algorand_client: AlgorandClient,
    noticeboard_app_id: int,
    valown_address: str,
    delman_address: str,
    valad_id: int,
    delco_id: int
) -> Tuple[int, int]:
    """Get the app indexes at which valad and delco are stored for the corresponding valown and delman.

    Parameters
    ----------
    algorand_client : AlgorandClient
        Algorand client.
    noticeboard_app_id : int
        Noticeboard ID.
    valown_address : str
        Validator owner address.
    delman_address : str
        Delegator manager address.
    valad_id : int
        Validator ad ID.
    delco_id : int
        Delegator contract ID.

    Returns
    -------
    Tuple[int, int]
        Valad and delco indexes.
    """
    # Get index in validator's list at which the validator ad is stored
    valown_user_info = app_get_user_info(
        algorand_client,
        noticeboard_app_id,
        valown_address
    )
    val_app_idx = valown_user_info.get_app_idx(valad_id)
    # Get index in delegator's list at which the delegator contract is stored
    delman_user_info = app_get_user_info(
        algorand_client,
        noticeboard_app_id,
        delman_address
    )
    del_app_idx = delman_user_info.get_app_idx(delco_id)
    return (val_app_idx, del_app_idx)


def valown_and_delman_boxes(
    valown_address: str,
    delman_address: str
) -> List[Tuple[int, bytes]]:
    """Prepare for box fetching from the noticeboard for the validator owner and delegator manager.

    Parameters
    ----------
    valown_address : str
        Validator owner address.
    delman_address : str
        Delegator manager address.

    Returns
    -------
    List[Tuple[int, bytes]]
        Valown and delman box.
    """
    return[
        (0,  AddressType().encode(valown_address)),
        (0,  AddressType().encode(delman_address))
    ]


def set_valad_ready(
    algorand_client: AlgorandClient,
    valown_address: str,
    valad_id: int,
    valman: AddressAndSigner,
    noticeboard_client: NoticeboardClient,
) -> ABITransactionResponse[None]:
    """Set validator ad to ready.

    Parameters
    ----------
    algorand_client : AlgorandClient
        Algorand client.
    valown_address : str
        Validator ad owner address.
    delman_address : str
        Delegator manager address.
    valad_id : int
        Validator ad app id.
    delco_id : int
        Delegator contract app id.
    fee_asset_id : int
        ID of the asset user for payments.
    valman : AddressAndSigner
        Validator manager address and signer.
    noticeboard_client : NoticeboardClient
        Noticeboard client.
    """

    boxes_user = [
        (0,  AddressType().encode(valown_address)),
    ]

    # Get index of app in user's list
    user_info = app_get_user_info(
        algorand_client,
        noticeboard_client.app_id,
        valown_address
    )
    val_app_idx = user_info.get_app_idx(valad_id)

    # Increase fee for inner txns for ad_ready.
    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 2 * sp.min_fee
    sp.flat_fee = True

    return noticeboard_client.ad_ready(
        val_owner=valown_address,
        val_app=valad_id,
        val_app_idx=val_app_idx,
        ready=True,
        transaction_parameters = TransactionParameters(
            sender = valman.address,
            signer = valman.signer,
            suggested_params=sp,
            boxes=boxes_user
        ),
    )


def report_delco_breach_pay(
    algorand_client: AlgorandClient,
    valown_address: str,
    delman_address: str,
    valad_id: int,
    delco_id: int,
    fee_asset_id: int,
    valman: AddressAndSigner,
    noticeboard_client: NoticeboardClient
) -> ABITransactionResponse[None]:
    """Report that the delegator contract can not transfer payment funds to validator ad.

    Parameters
    ----------
    algorand_client : AlgorandClient
        Algorand client.
    valown_address : str
        Validator ad owner address.
    delman_address : str
        Delegator manager address.
    valad_id : int
        Validator ad app id.
    delco_id : int
        Delegator contract app id.
    fee_asset_id : int
        ID of the asset user for payments.
    valman : AddressAndSigner
        Validator manager address and signer.
    noticeboard_client : NoticeboardClient
        Noticeboard client.

    Returns
    -------
    ABITransactionResponse[None]
    """
    boxes = valown_and_delman_boxes(
        valown_address=valown_address,
        delman_address=delman_address
    )

    val_app_idx, del_app_idx = get_val_and_del_app_idx(
        algorand_client=algorand_client,
        noticeboard_app_id=noticeboard_client.app_id,
        valown_address=valown_address,
        delman_address=delman_address,
        valad_id=valad_id,
        delco_id=delco_id
    )

    # Add asset to the foreign asset array and box array
    if fee_asset_id != ALGO_ASA_ID:
        foreign_assets = [fee_asset_id]
        boxes_asset = [(valad_id, BOX_ASA_KEY_PREFIX + fee_asset_id.to_bytes(8, byteorder="big"))]
        boxes += boxes_asset
    else:
        foreign_assets = None

    # Increase fee for forwarding the call to validator ad (1) and then delegator contract (1),
    # as well as for (potential) distribution of earnings (2), (potential) payout of partner fee (1),
    # and (potential) notification message (1).
    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 7 * sp.min_fee
    sp.flat_fee = True

    return noticeboard_client.breach_pay(
        del_manager=delman_address,
        del_app=delco_id,
        del_app_idx=del_app_idx,
        val_owner=valown_address,
        val_app=valad_id,
        val_app_idx=val_app_idx,
        transaction_parameters = TransactionParameters(
            sender=valman.address,
            signer=valman.signer,
            suggested_params=sp,
            foreign_assets=foreign_assets,
            accounts=[delman_address],
            boxes=boxes
        ),
    )


def submit_partkeys(
    algorand_client: AlgorandClient,
    valown_address: str,
    delman_address: str,
    delben_address: str,
    partner_address: str,
    valad_id: int,
    delco_id: int,
    fee_asset_id: int,
    valman: AddressAndSigner,
    noticeboard_client: NoticeboardClient,
    vote_first: int,
    vote_last: int,
    vote_key_dilution: int,
    vote_pk: str,
    selection_pk: str,
    state_proof_pk: str
) -> ABITransactionResponse[None]:
    """Submit participation keys.

    Parameters
    ----------
    algorand_client : AlgorandClient
        Algorand client.
    valown_address : str
        Validator ad owner address.
    delman_address : str
        Delegator manager address.
    delben_address : str
        Delegator beneficiary address.
    partner_address : str
        Address of partner for commissions.
    valad_id : int
        Validator ad app id.
    delco_id : int
        Delegator contract app id.
    fee_asset_id : int
        ID of the asset user for payments.
    valman : AddressAndSigner
        Validator manager address and signer.
    noticeboard_client : NoticeboardClient
        Noticeboard client.
    vote_first : int
        First round when keys are valid.
    vote_last : int
        Last round when keys are valid.
    vote_key_dilution : int
        Vote key dilution.
    vote_pk : str
        Vote parameter of participation keys.
    selection_pk : str
        Selection parameter of participation keys.
    state_proof_pk : str
        State proof parameter of participation keys.

    Returns
    -------
    ABITransactionResponse[None]
    """
    boxes = valown_and_delman_boxes(
        valown_address=valown_address,
        delman_address=delman_address
    )

    val_app_idx, del_app_idx = get_val_and_del_app_idx(
        algorand_client=algorand_client,
        noticeboard_app_id=noticeboard_client.app_id,
        valown_address=valown_address,
        delman_address=delman_address,
        valad_id=valad_id,
        delco_id=delco_id
    )

    # Add asset to the foreign asset array and box array
    if fee_asset_id != ALGO_ASA_ID:
        foreign_assets = [fee_asset_id]
        boxes_asset = [(valad_id, BOX_ASA_KEY_PREFIX + fee_asset_id.to_bytes(8, byteorder="big"))]
        boxes += boxes_asset
    else:
        foreign_assets = None

    # Add foreign addresses (add manager even if equal to beneficiary)
    foreign_accounts = [partner_address, delman_address]

    # Increase fee for forwarding the call to validator ad (1) and then delegator contract (1),
    # as well as distribution of earnings to the validator ad (1) and noticeboard (1),
    # (potential) payout of partner fee (1), and (potential) notification message (1).
    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 7 * sp.min_fee
    sp.flat_fee = True

    return noticeboard_client.keys_submit(
        del_manager=delman_address,
        del_app=delco_id,
        del_app_idx=del_app_idx,
        val_owner=valown_address,
        val_app=valad_id,
        val_app_idx=val_app_idx,
        key_reg_txn_info = KeyRegTxnInfo(
            vote_first=vote_first,
            vote_last=vote_last,
            vote_key_dilution=vote_key_dilution,
            vote_pk=base64.b64decode(vote_pk),
            selection_pk=base64.b64decode(selection_pk),
            state_proof_pk=base64.b64decode(state_proof_pk),
            sender=delben_address,
        ),
        transaction_parameters = TransactionParameters(
            sender=valman.address,
            signer=valman.signer,
            suggested_params=sp,
            foreign_assets=foreign_assets,
            accounts=foreign_accounts,
            boxes=boxes,
        )
    )


def report_partkeys_not_submitted(
    algorand_client: AlgorandClient,
    valown_address: str,
    delman_address: str,
    # partner_address: str,
    valad_id: int,
    delco_id: int,
    fee_asset_id: int,
    valman: AddressAndSigner,
    noticeboard_client: NoticeboardClient
) -> ABITransactionResponse[None]:
    """Report that the validator manager has not submitted the partkeys on time.

    Parameters
    ----------
    algorand_client : AlgorandClient
        Algorand client.
    valown_address : str
        Validator ad owner address.
    delman_address : str
        Delegator manager address.
    # partner_address : str
    #     Address of partner for commissions.
    valad_id : int
        Validator ad app id.
    delco_id : int
        Delegator contract app id.
    fee_asset_id : int
        ID of the asset user for payments.
    valman : AddressAndSigner
        Validator manager address and signer.
    noticeboard_client : NoticeboardClient
        Noticeboard client.

    Returns
    -------
    ABITransactionResponse[None]
    """    
    boxes = valown_and_delman_boxes(
        valown_address=valown_address,
        delman_address=delman_address
    )

    val_app_idx, del_app_idx = get_val_and_del_app_idx(
        algorand_client=algorand_client,
        noticeboard_app_id=noticeboard_client.app_id,
        valown_address=valown_address,
        delman_address=delman_address,
        valad_id=valad_id,
        delco_id=delco_id
    )

    # Add asset to the foreign asset array and box array
    if fee_asset_id != ALGO_ASA_ID:
        foreign_assets = [fee_asset_id]
    else:
        foreign_assets = None

    # Increase fee for forwarding the call to validator ad (1) and then delegator contract (1),
    # plus the try for return of deposit to the delegator.
    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 5 * sp.min_fee
    sp.flat_fee = True

    # foreign_accounts = [partner_address, delman_address]
    foreign_accounts = [delman_address]

    return noticeboard_client.keys_not_submitted(
        del_manager=delman_address,
        del_app=delco_id,
        del_app_idx=del_app_idx,
        val_owner=valown_address,
        val_app=valad_id,
        val_app_idx=val_app_idx,
        transaction_parameters = TransactionParameters(
            sender = valman.address,
            signer = valman.signer,
            suggested_params=sp,
            foreign_assets=foreign_assets,
            accounts=foreign_accounts,
            boxes=boxes,
        ),
    )


def report_unconfirmed_partkeys(
    algorand_client: AlgorandClient,
    valown_address: str,
    delman_address: str,
    partner_address: str,
    valad_id: int,
    delco_id: int,
    fee_asset_id: int,
    valman: AddressAndSigner,
    noticeboard_client: NoticeboardClient
) -> ABITransactionResponse[None]:
    """Report that the delegator beneficiary has not confirmed the partkeys on time.

    Parameters
    ----------
    algorand_client : AlgorandClient
        Algorand client.
    valown_address : str
        Validator ad owner address.
    delman_address : str
        Delegator manager address.
    partner_address : str
        Address of partner for commissions.
    valad_id : int
        Validator ad app id.
    delco_id : int
        Delegator contract app id.
    fee_asset_id : int
        ID of the asset user for payments.
    valman : AddressAndSigner
        Validator manager address and signer.
    noticeboard_client : NoticeboardClient
        Noticeboard client.

    Returns
    -------
    ABITransactionResponse[None]
    """    
    boxes = valown_and_delman_boxes(
        valown_address=valown_address,
        delman_address=delman_address
    )

    val_app_idx, del_app_idx = get_val_and_del_app_idx(
        algorand_client=algorand_client,
        noticeboard_app_id=noticeboard_client.app_id,
        valown_address=valown_address,
        delman_address=delman_address,
        valad_id=valad_id,
        delco_id=delco_id
    )

    # Add asset to the foreign asset array and box array
    if fee_asset_id != ALGO_ASA_ID:
        foreign_assets = [fee_asset_id]
    else:
        foreign_assets = None

    # Increase fee for forwarding the call to validator ad (1) and then delegator contract (1),
    # plus the try for return of deposit to the delegator.
    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 6 * sp.min_fee
    sp.flat_fee = True

    foreign_accounts = [partner_address, delman_address]

    return noticeboard_client.keys_not_confirmed(
        del_manager=delman_address,
        del_app=delco_id,
        del_app_idx=del_app_idx,
        val_owner=valown_address,
        val_app=valad_id,
        val_app_idx=val_app_idx,
        transaction_parameters = TransactionParameters(
            sender = valman.address,
            signer = valman.signer,
            suggested_params=sp,
            accounts=foreign_accounts,
            foreign_assets=foreign_assets,
            boxes=boxes
        ),
    )


def report_contract_expired(
    algorand_client: AlgorandClient,
    valown_address: str,
    delman_address: str,
    partner_address: str,
    valad_id: int,
    delco_id: int,
    fee_asset_id: int,
    valman: AddressAndSigner,
    noticeboard_client: NoticeboardClient
) -> ABITransactionResponse[None]:
    """Report that the delegator contract has expired (ended due to completion).

    Parameters
    ----------
    algorand_client : AlgorandClient
        Algorand client.
    valown_address : str
        Validator ad owner address.
    delman_address : str
        Delegator manager address.
    partner_address : str
        Address of partner for commissions.
    valad_id : int
        Validator ad app id.
    delco_id : int
        Delegator contract app id.
    fee_asset_id : int
        ID of the asset user for payments.
    valman : AddressAndSigner
        Validator manager address and signer.
    noticeboard_client : NoticeboardClient
        Noticeboard client.

    Returns
    -------
    ABITransactionResponse[None]
    """    
    boxes = valown_and_delman_boxes(
        valown_address=valown_address,
        delman_address=delman_address
    )

    val_app_idx, del_app_idx = get_val_and_del_app_idx(
        algorand_client=algorand_client,
        noticeboard_app_id=noticeboard_client.app_id,
        valown_address=valown_address,
        delman_address=delman_address,
        valad_id=valad_id,
        delco_id=delco_id
    )

    # Add asset to the foreign asset array and box array
    if fee_asset_id != ALGO_ASA_ID:
        foreign_assets = [fee_asset_id]
        boxes_asset = [(valad_id, BOX_ASA_KEY_PREFIX + fee_asset_id.to_bytes(8, byteorder="big"))]
        boxes += boxes_asset
    else:
        foreign_assets = None

    # Add partners and delegator manager to foreign addresses
    foreign_accounts = [partner_address, delman_address]

    # Increase fee for forwarding the call to validator ad (1) and then delegator contract (1),
    # as well as for (potential) distribution of earnings (2), (potential) payout of partner fee (1),
    # and (potential) notification message (1).
    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 7 * sp.min_fee
    sp.flat_fee = True

    return noticeboard_client.contract_expired(
        del_manager=delman_address,
        del_app=delco_id,
        del_app_idx=del_app_idx,
        val_owner=valown_address,
        val_app=valad_id,
        val_app_idx=val_app_idx,
        transaction_parameters = TransactionParameters(
            sender=valman.address,
            signer=valman.signer,
            suggested_params=sp,
            foreign_assets=foreign_assets,
            accounts=foreign_accounts,
            boxes=boxes,
        ),
    )


def report_delben_breach_limits(
    algorand_client: AlgorandClient,
    valown_address: str,
    delman_address: str,
    delben_address: str,
    partner_address: str,
    valad_id: int,
    delco_id: int,
    fee_asset_id: int,
    gating_asa_id_list: List[int],
    valman: AddressAndSigner,
    noticeboard_client: NoticeboardClient
) -> ABITransactionResponse[None]:
    """Report that the delegator beneficiary breached the max stake or one of the possible min gating ASA limits.

    Parameters
    ----------
    algorand_client : AlgorandClient
        Algorand client.
    valown_address : str
        Validator ad owner address.
    delman_address : str
        Delegator manager address.
    delben_address : str
        Delegator beneficiary address.
    partner_address : str
        Address of partner for commissions.
    valad_id : int
        Validator ad app id.
    delco_id : int
        Delegator contract app id.
    fee_asset_id : int
        ID of the asset user for payments.
    gating_asa_id_list : int
        IDs of assets (ASAs) usdeg for gating.
    valman : AddressAndSigner
        Validator manager address and signer.
    noticeboard_client : NoticeboardClient
        Noticeboard client.

    Returns
    -------
    ABITransactionResponse[None]
    """        
    boxes = valown_and_delman_boxes(
        valown_address=valown_address,
        delman_address=delman_address
    )

    val_app_idx, del_app_idx = get_val_and_del_app_idx(
        algorand_client=algorand_client,
        noticeboard_app_id=noticeboard_client.app_id,
        valown_address=valown_address,
        delman_address=delman_address,
        valad_id=valad_id,
        delco_id=delco_id
    )

    foreign_assets = [asa_id for asa_id in gating_asa_id_list if asa_id != ALGO_ASA_ID]
    
    if fee_asset_id != ALGO_ASA_ID:
        foreign_assets.append(fee_asset_id)

    if fee_asset_id != ALGO_ASA_ID:
        boxes_asset = [(valad_id, BOX_ASA_KEY_PREFIX + fee_asset_id.to_bytes(8, byteorder="big"))]
        boxes += boxes_asset

    # Add delegator manager account and delegator beneficiary account to the foreign account array
    foreign_accounts = [delben_address, delman_address, partner_address]

    # Increase fee for forwarding the call to validator ad (1) and then delegator contract (1),
    # as well as for (potential) distribution of earnings (2), (potential) note sending (1), and
    # the gas app call (1), the actual app call (1), (potential) payout of partner fee (1),
    # and (potential) notification message (1).
    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 9 * sp.min_fee
    sp.flat_fee = True

    return noticeboard_client.compose(
    ).gas(
        transaction_parameters=TransactionParameters(
            sender = valman.address,
            signer = valman.signer,
            foreign_assets=foreign_assets,
            accounts=foreign_accounts,
            foreign_apps=[valad_id, delco_id]
        ),
    ).breach_limits(
        del_manager=delman_address,
        del_app=delco_id,
        del_app_idx=del_app_idx,
        val_owner=valown_address,
        val_app=valad_id,
        val_app_idx=val_app_idx,
        transaction_parameters = TransactionParameters(
            sender = valman.address,
            signer = valman.signer,
            suggested_params=sp,
            boxes=boxes,
        ),
    ).execute()


def report_contract_expiry_soon(
    algorand_client: AlgorandClient,
    valown_address: str,
    delman_address: str,
    valad_id: int,
    delco_id: int,
    valman: AddressAndSigner,
    noticeboard_client: NoticeboardClient
) -> ABITransactionResponse[None]:
    """Report to the delegator manager that the delegator contract is about to expire.

    Parameters
    ----------
    algorand_client : AlgorandClient
        Algorand client.
    valown_address : str
        Validator ad owner address.
    delman_address : str
        Delegator manager address.
    valad_id : int
        Validator ad app id.
    delco_id : int
        Delegator contract app id.
    valman : AddressAndSigner
        Validator manager address and signer.
    noticeboard_client : NoticeboardClient
        Noticeboard client.

    Returns
    -------
    ABITransactionResponse[None]
    """        
    boxes = valown_and_delman_boxes(
        valown_address=valown_address,
        delman_address=delman_address
    )

    val_app_idx, del_app_idx = get_val_and_del_app_idx(
        algorand_client=algorand_client,
        noticeboard_app_id=noticeboard_client.app_id,
        valown_address=valown_address,
        delman_address=delman_address,
        valad_id=valad_id,
        delco_id=delco_id
    )

    # Add delegator manager account to the foreign account array
    foreign_accounts = [delman_address]

    # Increase fee for forwarding the call to validator ad (1), and delegator contract (1),
    # as well as for (potential) notification message (1), and the app call (1).
    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 4 * sp.min_fee
    sp.flat_fee = True

    return noticeboard_client.contract_report_expiry_soon(
        del_manager=delman_address,
        del_app=delco_id,
        del_app_idx=del_app_idx,
        val_owner=valown_address,
        val_app=valad_id,
        val_app_idx=val_app_idx,
        transaction_parameters = TransactionParameters(
            sender = valman.address,
            signer = valman.signer,
            suggested_params=sp,
            accounts=foreign_accounts,
            boxes=boxes,
        ),
    )


def claim_used_up_operational_fee(
    algorand_client: AlgorandClient,
    valown_address: str,
    delman_address: str,
    partner_address: str,
    valad_id: int,
    delco_id: int,
    fee_asset_id: int,
    valman: AddressAndSigner,
    noticeboard_client: NoticeboardClient
) -> ABITransactionResponse[None]:
    """Transfer used up operational fee from delegator contract to the corresponding validator ad.

    Notes
    -----
    Automatically deducts commission and transfers it to the noticeboard and partner (if applicable).

    Parameters
    ----------
    algorand_client : AlgorandClient
        Algorand client.
    valown_address : str
        Validator ad owner address.
    delman_address : str
        Delegator manager address.
    partner_address : str
        Address of partner for commissions.
    valad_id : int
        Validator ad app id.
    delco_id : int
        Delegator contract app id.
    fee_asset_id : int
        ID of the asset user for payments.
    valman : AddressAndSigner
        Validator manager address and signer.
    noticeboard_client : NoticeboardClient
        Noticeboard client.

    Returns
    -------
    ABITransactionResponse[None]
    """        
    boxes = valown_and_delman_boxes(
        valown_address=valown_address,
        delman_address=delman_address
    )

    val_app_idx, del_app_idx = get_val_and_del_app_idx(
        algorand_client=algorand_client,
        noticeboard_app_id=noticeboard_client.app_id,
        valown_address=valown_address,
        delman_address=delman_address,
        valad_id=valad_id,
        delco_id=delco_id
    )

    # Add asset to the foreign asset array and box array
    if fee_asset_id != ALGO_ASA_ID:
        foreign_assets = [fee_asset_id]
        boxes_asset = [(valad_id, BOX_ASA_KEY_PREFIX + fee_asset_id.to_bytes(8, byteorder="big"))]
        boxes += boxes_asset
    else:
        foreign_assets = None

    # Add foreign addresses (add manager even if equal to beneficiary)
    foreign_accounts = [partner_address, delman_address]

    # Increase fee for forwarding the call to validator ad (1) and then delegator contract (1),
    # as well as for (potential) distribution of earnings (2),
    # and (potential) payout of partner fee (1).
    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 6 * sp.min_fee
    sp.flat_fee = True

    return noticeboard_client.contract_claim(
        del_manager=delman_address,
        del_app=delco_id,
        del_app_idx=del_app_idx,
        val_owner=valown_address,
        val_app=valad_id,
        val_app_idx=val_app_idx,
        transaction_parameters = TransactionParameters(
            sender = valman.address,
            signer = valman.signer,
            suggested_params=sp,
            foreign_assets=foreign_assets,
            accounts=foreign_accounts,
            boxes=boxes,
        ),
    )
