# pyright: reportMissingModuleSource=false
import typing as t

from algopy import (
    Account,
    Bytes,
    Global,
    UInt64,
    arc4,
    itxn,
    op,
    subroutine,
)

from smart_contracts.helpers.constants import COMMISSION_MAX, FROM_BASE_TO_MILLI_MULTIPLIER

# ------- Definition of types -------

Sha256: t.TypeAlias = arc4.StaticArray[arc4.Byte, t.Literal[32]]
"""
Sha256 : arc4.StaticArray[arc4.Byte, t.Literal[32]]
    Result of hash function SHA 256.
"""

SelPk: t.TypeAlias = arc4.StaticArray[arc4.Byte, t.Literal[32]]
"""
SelPk : arc4.StaticArray[arc4.Byte, t.Literal[32]]
    Selection public key of a participation key.
"""

VotePk: t.TypeAlias = arc4.StaticArray[arc4.Byte, t.Literal[32]]
"""
VotePk : arc4.StaticArray[arc4.Byte, t.Literal[32]]
    Vote public key of a participation key.
"""

StateProofPk: t.TypeAlias = arc4.StaticArray[arc4.Byte, t.Literal[64]]
"""
StateProofPk : arc4.StaticArray[arc4.Byte, t.Literal[64]]
    State proof public key of a participation key.
"""

TxId: t.TypeAlias = arc4.StaticArray[arc4.Byte, t.Literal[32]]
"""
TxId : arc4.StaticArray[arc4.Byte, t.Literal[32]]
    Transaction ID.
"""

DelAppList: t.TypeAlias = arc4.StaticArray[arc4.UInt64, t.Literal[14]]
"""
DelAppList : arc4.StaticArray[arc4.UInt64, t.Literal[14]]
    List of app IDs of active delegator contracts of a validator ad.
    Length MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD.
"""

CountryCode : t.TypeAlias = arc4.StaticArray[arc4.Byte, t.Literal[2]]
"""
CountryCode : arc4.StaticArray[arc4.Byte, t.Literal[2]]
    Two-letter country code of node location.
"""

ValName : t.TypeAlias = arc4.StaticArray[arc4.Byte, t.Literal[30]]
"""
ValName : arc4.StaticArray[arc4.Byte, t.Literal[30]]
    Self-given name of validator.
"""

ValHTTPS : t.TypeAlias = arc4.StaticArray[arc4.Byte, t.Literal[60]]
"""
ValHTTPS : arc4.StaticArray[arc4.Byte, t.Literal[60]]
    Self-given https link to validator's website (without https://)
    Due to space limits, tiny URLs should be used.
"""

AlgodVersion : t.TypeAlias = arc4.StaticArray[arc4.Byte, t.Literal[20]]
"""
AlgodVersion : arc4.StaticArray[arc4.Byte, t.Literal[20]]
    Self-reported algod version that node is operating.
"""

NoticeboardAppList : t.TypeAlias = arc4.StaticArray[arc4.UInt64, t.Literal[110]]
"""
NoticeboardAppList : arc4.StaticArray[arc4.UInt64, t.Literal[110]]
    Holds list of app IDs for either delegator contracts of a delegator manager or validator ads of a validator owner.
"""

NotificationMessage: t.TypeAlias = arc4.StaticArray[arc4.Byte, t.Literal[100]]
"""
NotificationMessage : arc4.StaticArray[arc4.Byte, t.Literal[100]]
    For holding notification message.
"""

# ------- Definition of structs -------

class AsaReq(arc4.Struct):
    """
    Holds information about the minimum balance requirement for a specific ASA ID as defined by the validator.

    Fields
    ------
    id : arc4.UInt64
        ASA ID of the asset to check.
    min : arc4.UInt64
        Minimum balance requirement for the ASA ID in its base units.
    """

    id : arc4.UInt64
    min : arc4.UInt64

GatingASAList: t.TypeAlias = arc4.StaticArray[AsaReq, t.Literal[2]]
"""
GatingASAList: t.TypeAlias = arc4.StaticArray[AsaReq, t.Literal[2]]
    List of AsaReq elements, defining which ASA IDs delegator beneficiary must hold and their minimum amounts.
"""

class EarningsDistribution(arc4.Struct):
    """
    Holds the distribution of earnings between user and the platform.

    Fields
    ------
    user : arc4.UInt64
        Amount of user earnings minus the commission of the platform.
    platform : arc4.UInt64
        Amount of platform earnings from the commission.
    asset_id : arc4.UInt64
        ID of the asset of the earnings.
        Equals 0 for ALGO or to the ASA ID used.
    """

    user : arc4.UInt64
    platform : arc4.UInt64
    asset_id : arc4.UInt64

class BreachLimitsReturn(arc4.Struct):
    """
    Structure that includes return value for breach_limits method of DelegatorContract.

    Fields
    ------
    max_breach_reached : arc4.Bool
        Boolean denoting if maximum number of breaches has already been reached (True) or not (False).
    earnings_distribution : EarningsDistribution
        Amount of earnings of the validator which equal any unclaimed operational fee minus platform commission,
        amount of platform earnings from the commission, and
        the asset in which the earnings are denoted.
    del_manager : arc4.Address
        Address of delegator manager.
    msg : Message
        Notification message about the action.
    """

    max_breach_reached : arc4.Bool
    earnings_distribution : EarningsDistribution
    del_manager : arc4.Address
    msg : NotificationMessage

class ContractDeleteReturn(arc4.Struct):
    """
    Structure that includes return value for contract_delete method of DelegatorContract.

    Fields
    ------
    remaining_balance : arc4.UInt64
        Balance of the fee asset that remained in the contract.
    asset_id : arc4.UInt64
        Asset ID of the remaining balance.
    """

    remaining_balance : arc4.UInt64
    asset_id : arc4.UInt64

class KeyRegTxnInfo(arc4.Struct):
    """
    All relevant parameters of a key registration transaction.

    Fields
    ------
    vote_first : arc4.UInt64
        First round of validity of a participation key.
    vote_last : arc4.UInt64
        Last round of validity of a participation key.
    vote_key_dilution : arc4.UInt64
        Vote key dilution parameter of a participation key.
    vote_pk : VotePk
        Vote public key of a participation key.
    selection_pk : SelPk
        Selection public key of a participation key.
    state_proof_pk : StateProofPk
        State proof public key of a participation key.
    sender : arc4.Address
        Sender of the key registration transaction.
    """

    vote_first : arc4.UInt64
    vote_last : arc4.UInt64
    vote_key_dilution : arc4.UInt64
    vote_pk : VotePk
    selection_pk : SelPk
    state_proof_pk : StateProofPk
    sender : arc4.Address

class DelegationTermsGeneral(arc4.Struct):
    """
    Holds information about the terms for delegation agreed with the validator.
    These terms are supplemented with the terms about delegator beneficiary balance requirements.
    These terms are agreed by the validator owner based on the ValidatorTerms defined at the validator ad.
    These terms are agreed by delegator at the creation of the delegator contract.

    Fields
    ------
    commission : arc4.UInt64
        Relative commission on any earning.
        It gets deducted from the earning and is paid to the platform.
        The value is represented in ppm.
        The maximum is 1_000_000.

    fee_round : arc4.UInt64
        Agreed costs for operating the validator per block round.
        The value is expressed in milli base units of `fee_asset_id` asset per block round.
    fee_setup : arc4.UInt64
        Agreed costs for setting up the validator, i.e. generating and submitting the participation keys.
        The value is expressed in base units of `fee_asset_id` asset.
    fee_asset_id : arc4.UInt64
        ID of the asset used as means of payment for the validator fees (i.e. fee_round and fee_setup).
        Equals 0 for ALGO or to the ASA ID used.

    partner_address : arc4.Address
        Address of the partner that collects the partner convenience fees.
        If there is no partner, set it to Global.zero_address.
    fee_round_partner : arc4.UInt64
        Agreed fee charged for convenience by the partner per block round of operation.
        The value is expressed in milli base units of `fee_asset_id` asset per block round.
    fee_setup_partner : arc4.UInt64
        Agreed fee charged for convenience by the partner for the set up.
        The value is expressed in base units of `fee_asset_id` asset.

    rounds_setup : arc4.UInt64
        Number of rounds after contract start, in which the validator manager should submit the participation keys.
    rounds_confirm : arc4.UInt64
        The delegator manager must confirm the keys at the latest by rounds_setup + rounds_confirm after contract start.
        The keys must first be submitted.
    """
    commission : arc4.UInt64

    fee_round : arc4.UInt64
    fee_setup : arc4.UInt64
    fee_asset_id : arc4.UInt64

    partner_address : arc4.Address
    fee_round_partner : arc4.UInt64
    fee_setup_partner : arc4.UInt64

    rounds_setup : arc4.UInt64
    rounds_confirm : arc4.UInt64

class DelegationTermsBalance(arc4.Struct):
    """
    Holds information about the delegator beneficiary balance requirements agreed with the validator.
    These terms are supplemented by the general terms.
    These terms are agreed by the validator owner based on the ValidatorTerms defined at the validator ad.
    These terms are agreed by delegator at the creation of the delegator contract.

    Fields
    ------
    stake_max : arc4.UInt64
        Maximum ALGO balance that delegator beneficiary should have in its wallet at any time while contract is active.
        If breaching this limit is detected, it results in a delegator's limit breach event.
        The value is expressed in microALGO.

    cnt_breach_del_max : arc4.UInt64
        Maximum allowed number of delegator's breach events before the contract ends.

    rounds_breach : arc4.UInt64
        Minimum number of rounds between two stake- or asa-limit breach events to consider them as separate.

    gating_asa_list : GatingASAList
        List of AsaReq elements, defining which ASA IDs delegator beneficiary must hold and their minimum amounts.
        If breaching any of these limits is detected, it results in a delegator's limit breach event.
        A single breach event is considered even if multiple limits are breached simultaneously.
    """

    stake_max : arc4.UInt64

    cnt_breach_del_max : arc4.UInt64

    rounds_breach : arc4.UInt64

    gating_asa_list : GatingASAList

class ValidatorTermsTiming(arc4.Struct):
    """
    Holds information about the timing terms for delegation offered by the validator.
    These terms are agreed by the validator owner when set at the validator ad.

    Fields
    ------
    rounds_setup : arc4.UInt64
        Number of rounds after contract start, in which the validator manager should submit the participation keys.
    rounds_confirm : arc4.UInt64
        The delegator manager must confirm the keys at the latest by rounds_setup + rounds_confirm after contract start.
        The keys must first be submitted.
    rounds_duration_min : arc4.UInt64
        Minimum number of rounds the validator requires the delegation to last.
        Must be larger than the sum of rounds_setup and rounds_confirm.
    rounds_duration_max : arc4.UInt64
        Maximum number of rounds the validator allows the delegation to last.
        Must be larger or equal to rounds_duration_min.
    round_max_end : arc4.UInt64
        Round number by which the contracts must end by the latest.
    """

    rounds_setup : arc4.UInt64
    rounds_confirm : arc4.UInt64
    rounds_duration_min : arc4.UInt64
    rounds_duration_max : arc4.UInt64
    round_max_end : arc4.UInt64

class ValidatorTermsPricing(arc4.Struct):
    """
    Holds information about the pricing terms for delegation offered by the validator.
    These terms are agreed by the validator owner when set at the validator ad.

    Fields
    ------
    commission : arc4.UInt64
        Relative commission on any earning.
        It gets deducted from the earning and is paid to the platform.
        The value is represented in ppm.
        The maximum is 1_000_000.

    fee_round_min : arc4.UInt64
        Agreed minimal costs for operating the validator per block round.
        The value is expressed in milli base units of `fee_asset_id` asset per block round.
    fee_round_var : arc4.UInt64
        Agreed variable costs for operating the validator per block round and per max stake amount.
        The value is expressed in nano base units of `fee_asset_id` asset per block round
        and per FROM_BASE_TO_MICRO_MULTIPLIER microALGO, i.e. per 1 ALGO, of stake_max.
        The delegator's fee_round is determined as: max(fee_round_min, fee_round_var * stake_max).
    fee_setup : arc4.UInt64
        Agreed costs for setting up the validator, i.e. generating and submitting the participation keys.
        The value is expressed in base units of `fee_asset_id` asset.
    fee_asset_id : arc4.UInt64
        ID of the asset used as means of payment for the validator fees (i.e. fee_round and fee_setup).
        Equals 0 for ALGO or to the ASA ID used.
    """

    commission : arc4.UInt64

    fee_round_min : arc4.UInt64
    fee_round_var : arc4.UInt64
    fee_setup : arc4.UInt64
    fee_asset_id : arc4.UInt64

class ValidatorTermsStakeLimits(arc4.Struct):
    """
    Holds information about the terms w.r.t. the limits on stake amount for delegation offered by the validator.
    These terms are agreed by the validator owner when set at the validator ad.

    Fields
    ------
    stake_max : arc4.UInt64
        Maximum ALGO amount that any delegator can stake.
        The value is expressed in microALGO.
    stake_gratis : arc4.UInt64
        Gratis stake (in ppm) above the maximum stake requested by the delegator.
        This acts as a free buffer added to the requested maximum stake.
        It enables a better user experience for delegators because they can get more Algorand in their account without
        their consent or intent since sending of Algorand to accounts is completely permissionless.
        The agreed maximum stake for a contract is limited to stake_max even if the sum of the gratis
        stake and the requested maximum stake would exceed the maximum allowed stake.
        The value is represented in ppm. The maximum is 1_000_000.
    """

    stake_max : arc4.UInt64
    stake_gratis : arc4.UInt64

class ValidatorTermsGating(arc4.Struct):
    """
    Holds information about the delegator beneficiary balance requirements to use this validator.
    These terms are agreed by the validator owner when set at the validator ad.

    Fields
    ------
    gating_asa_list : GatingASAList
        List of AsaReq elements, defining which ASA IDs delegator beneficiary must hold and their minimum amounts.
        If breaching any of these limits is detected, it results in a delegator's limit breach event.
        A single breach event is considered even if multiple limits are breached simultaneously.
    """

    gating_asa_list : GatingASAList

class ValidatorTermsWarnings(arc4.Struct):
    """
    Holds information about the terms w.r.t. to the warning system for delegation offered by the validator.
    These terms are agreed by the validator owner when set at the validator ad.

    Fields
    ------
    cnt_warning_max : arc4.UInt64
        Maximum number of warnings given to the delegator for their mistakes w.r.t. their stake or gating token balance
        before the contract ends.

    rounds_warning : arc4.UInt64
        Maximum time for the delegator to correct a mistake in their stake or gating token balance before another
        warning is given for the same mistake.

    """

    cnt_warning_max : arc4.UInt64

    rounds_warning : arc4.UInt64

class ValidatorSelfDisclosure(arc4.Struct):
    """
    Holds information about the validator owner as disclosed by oneself.
    The information is not and cannot be verified!
    Users need to exercise caution and verify it themselves.

    Fields
    ------
    name : ValName
        Self-given name of validator.
    https : ValHTTPS
        Self-given https link to validator's website.

    country_code : CountryCode
        Reported country location of the node.
    hw_cat : arc4.UInt64
        Reported hardware category.
    node_version : AlgodVersion
        Reported algod node version.

    """

    name : ValName
    https : ValHTTPS

    country_code : CountryCode
    hw_cat : arc4.UInt64
    node_version : AlgodVersion

class ValidatorASA(arc4.Struct):
    """
    Holds information about the earnings of validator ad for an ASA.

    Fields
    ------
    total_earning : arc4.UInt64
        Total earnings of validator ad for the ASA.
    total_fees_generated : arc4.UInt64
        Total fees generated by the validator ad for the ASA.

    """

    total_earning : arc4.UInt64
    total_fees_generated : arc4.UInt64

UserRole: t.TypeAlias = arc4.StaticArray[arc4.Byte, t.Literal[4]]
"""
UserRole : arc4.StaticArray[arc4.Byte, t.Literal[4]]
    Role of a user.
    Can be either ROLE_VAL or ROLE_DEL.
"""

DllName: t.TypeAlias = arc4.StaticArray[arc4.Byte, t.Literal[8]]
"""
DllName : arc4.StaticArray[arc4.Byte, t.Literal[8]]
    Name of the double linked list to which the user belongs to.
    Can be either DLL_VAL or DLL_DEL.
"""

class UserInfo(arc4.Struct):
    """
    Holds information about a platform user, either validator or delegator.

    Fields
    ------
    role : UserRole
        Role of the user.
    dll_name : DllName
        Name of the double linked list to which the user belongs to.

    prev_user : arc4.Address
        Address of previous user in linked list.
    next_user : arc4.Address
        Address of next user in linked list.

    app_ids : NoticeboardAppList
        List of app IDs of delegator contract (in case the user is delegator manager)
        or validator ad (in case of validator owner).
        If entry equals UInt64(0), the entry is empty.
    cnt_app_ids : arc4.UInt64
        Counter of app IDs in the list.
        Use of this counter is redundant because empty entries are marked with UInt64(0).
    """

    role : UserRole
    dll_name : DllName

    prev_user : arc4.Address
    next_user : arc4.Address

    app_ids : NoticeboardAppList
    cnt_app_ids : arc4.UInt64

class UsersDoubleLinkedList(arc4.Struct):
    """
    Holds information relevant to the linked list of user boxes.

    Fields
    ------
    cnt_users :  arc4.UInt64
        Counter of users on the platform.
    user_first :  arc4.Address
        Address of the first user in the linked list.
    user_last :  arc4.Address
        Address of the last user in the linked list.
    """

    cnt_users :  arc4.UInt64
    user_first :  arc4.Address
    user_last :  arc4.Address

class NoticeboardFees(arc4.Struct):
    """
    Holds information about fees charged by the noticeboard.

    Fields
    ------
    commission_min : arc4.UInt64
        Minimum relative commission that can be applied to validator ads.
        The value is represented in ppm. The maximum is 1_000_000.
    val_user_reg : arc4.UInt64
        ALGO fee charged at registration of a new validator user.
        The value is expressed in microALGO.
    del_user_reg : arc4.UInt64
        ALGO fee charged at registration of a new delegator user.
        The value is expressed in microALGO.
    val_ad_creation : arc4.UInt64
        ALGO fee charged at creation of a new validator ad.
        The value is expressed in microALGO.
    del_contract_creation : arc4.UInt64
        ALGO fee charged at creation of a new delegator contract.
        The value is expressed in microALGO.
    """

    commission_min : arc4.UInt64
    val_user_reg : arc4.UInt64
    del_user_reg : arc4.UInt64
    val_ad_creation : arc4.UInt64
    del_contract_creation : arc4.UInt64

class NoticeboardTermsTiming(arc4.Struct):
    """
    Holds information about the Noticeboard's limits on timing terms for validator ads,
    and for notification's for reporting.

    Fields
    ------
    rounds_duration_min_min : arc4.UInt64
        Minimum number for the minimum number of rounds the validator can require the delegation to last.
        This is too prevent having short keys, which can cause stake to fluctuate frequently.
    rounds_duration_max_max : arc4.UInt64
        Maximum number for the maximum number of rounds the validator can allow the delegation to last.
        Must be larger or equal to rounds_duration_min_min.
        This is too prevent having long keys, which can be dangerous for the network.

    before_expiry: UInt64
        How many rounds before contract end can the report be made.
    report_period: UInt64
        How frequently can the report be made.
    """

    rounds_duration_min_min : arc4.UInt64
    rounds_duration_max_max : arc4.UInt64

    before_expiry : arc4.UInt64
    report_period : arc4.UInt64


class NoticeboardTermsNodeLimits(arc4.Struct):
    """
    Holds information about the Noticeboard's limits on node and related stake limit terms for validator ads.

    Fields
    ------
    stake_max_max : arc4.UInt64
        Maximum on the maximum ALGO amount that any delegator can stake.
        The value is expressed in microALGO.
        This is to mitigate stake aggregation on a node.
    stake_max_min : arc4.UInt64
        Minimum on the maximum ALGO amount that any validator must be able to accept.
        The value is expressed in microALGO.
        This is to be able to require all nodes to have sufficient performance to accept delegators with any stake.
    cnt_del_max_max : arc4.UInt64
        Maximum on the maximum number of delegators a validator is allowed by the noticeboard to accept.
        This is to mitigate too many delegators on a single node.
    """

    stake_max_max : arc4.UInt64
    stake_max_min : arc4.UInt64
    cnt_del_max_max : arc4.UInt64

class NoticeboardAssetInfo(arc4.Struct):
    """
    Holds information about a payment asset (ASA_ID or 0 for ALGO) on the noticeboard, i.e. if it is accepted as a
    payment at the platform (True) or not (False), and its minimum pricing limits.

    Fields
    ------
    accepted : arc4.Bool
        Holds information if an asset (ASA_ID or 0 for ALGO) is accepted as a payment at (True) or not (False).
    fee_round_min_min : arc4.UInt64
        Minimum on the minimal costs for operating the validator per block round.
        The value is expressed in milli base units of `fee_asset_id` asset per block round.
    fee_round_var_min : arc4.UInt64
        Minimum on the variable costs for operating the validator per block round and per max stake amount.
        The value is expressed in nano base units of `fee_asset_id` asset per block round
        and per FROM_BASE_TO_MICRO_MULTIPLIER microALGO, i.e. per 1 ALGO, of stake_max.
    fee_setup_min : arc4.UInt64
        Minimum on the costs for setting up the validator, i.e. generating and submitting the participation keys.
        The value is expressed in base units of `fee_asset_id` asset.
    """

    accepted : arc4.Bool
    fee_round_min_min : arc4.UInt64
    fee_round_var_min : arc4.UInt64
    fee_setup_min : arc4.UInt64

class PartnerCommissions(arc4.Struct):
    """
    Holds information about a platform's partner commissions.

    Fields
    ------
    commission_setup : arc4.UInt64
        Partner's convenience fee for contract setup, i.e. relative commission, charged on top of validator price
        for setting up the contract (i.e. the setup fee).
        The value is represented in ppm.
    commission_operational : arc4.UInt64
        Partner's convenience fee for contract operation, i.e. relative commission, charged on top of validator price
        for operation (i.e. the operational fee).
        The value is represented in ppm.
    """
    commission_setup : arc4.UInt64
    commission_operational : arc4.UInt64

# --------- Function returns with messages ---------
class EarningsDistributionAndMessage(arc4.Struct):
    """
    Fields
    ------
    earnings_distribution : EarningsDistribution
        Amount of earnings of the validator which equal the setup fee minus platform commission,
        amount of platform earnings from the commission, and
        the asset in which the earnings are denoted.
    del_manager : arc4.Address
        Address of delegator manager.
    msg : Message
        Notification message about the action.
    """
    earnings_distribution : EarningsDistribution
    del_manager : arc4.Address
    msg : NotificationMessage

class Message(arc4.Struct):
    """
    Fields
    ------
    del_manager : arc4.Address
        Address of delegator manager.
    msg : NotificationMessage
        Notification message about the action.
    """
    del_manager : arc4.Address
    msg : NotificationMessage


# ------- Functions -------
@subroutine
def calc_fee_operational(
    fee_round: UInt64,
    round_end: UInt64,
    round_start: UInt64,
) -> UInt64:
    """
    Calculates the operational fee between an end and a start round based on a fee per round.

    Parameters
    ----------
    fee_round : UInt64
        Fee per round.
        In asset's milli base units per round.
    round_end : UInt64
        End round.
    round_start : UInt64
        Start round.

    Returns
    -------
    fee_operational : UInt64
        Operational fee between round_end and round_start.
        In asset's base unit.
    """
    return (fee_round * (round_end - round_start)) // UInt64(FROM_BASE_TO_MILLI_MULTIPLIER)

@subroutine
def try_send_note(
    account: Account,
    msg: Bytes,
) -> None:
    """
    Tries to send a notification message to an account.

    Parameters
    ----------
    account : Account
        Account to which to send the note to.
    msg : arc4.String
        Message to send in the note field.

    """

    if op.balance(account) >= Global.min_balance:
        itxn.Payment(
            receiver=account,
            amount=0,
            note=msg,
        ).submit()

    return

@subroutine
def calc_earnings(
    amount: UInt64,
    commission: UInt64,
    asset_id: UInt64,
) -> EarningsDistribution:
    """
    Calculates the earnings of platform and user based on the amount and charged commission.

    Parameters
    ----------
    amount : UInt64
        Amount of total earnings to divide.
    commission : UInt64
        Commission charged.
    asset_id : UInt64
        Asset ID of the earnings denomination (i.e. ASA ID or 0 for ALGO).

    Returns
    -------
    earnings_distribution : EarningsDistribution
        Amount of earnings earned by user which equal the amount minus platform commission,
        amount of earnings earned by the platform which equal the commission, and
        the asset in which the earnings are denominated.
    """
    tmp = op.mulw(amount, commission)
    plat_earn = op.divw(tmp[0], tmp[1], UInt64(COMMISSION_MAX))
    user_earn = amount - plat_earn

    return EarningsDistribution(
        user=arc4.UInt64(user_earn),
        platform=arc4.UInt64(plat_earn),
        asset_id=arc4.UInt64(asset_id),
    )

@subroutine
def maximum(
    a: UInt64,
    b: UInt64,
) -> UInt64:
    """
    Return the maximum of two UInt64.
    """
    if a < b:
        c = b
    else:
        c = a
    return c

