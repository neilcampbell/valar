# pyright: reportMissingModuleSource=false
from algopy import (
    Application,
    ARC4Contract,
    Asset,
    Bytes,
    Global,
    GlobalState,
    TransactionType,
    Txn,
    UInt64,
    arc4,
    gtxn,
    itxn,
    op,
    subroutine,
    urange,
)

from ..helpers.common import (
    BreachLimitsReturn,
    ContractDeleteReturn,
    DelegationTermsBalance,
    DelegationTermsGeneral,
    EarningsDistribution,
    EarningsDistributionAndMessage,
    KeyRegTxnInfo,
    Message,
    NotificationMessage,
    SelPk,
    Sha256,
    StateProofPk,
    VotePk,
    calc_earnings,
    calc_fee_operational,
)
from ..helpers.constants import (
    ALGO_ASA_ID,
    ERROR_ACCOUNT_HAS_NOT_BEEN_SUSPENDED,
    ERROR_ACCOUNT_HAS_NOT_REGISTERED_FOR_SUSPENSION_TRACKING,
    ERROR_ALGO_IS_PERMISSIONLESS,
    ERROR_ALREADY_EXPIRED,
    ERROR_AMOUNT,
    ERROR_ASSET_ID,
    ERROR_BALANCE_FROZEN,
    ERROR_CALLED_BY_NOT_CREATOR,
    ERROR_ENOUGH_FUNDS_FOR_EARNED_OPERATIONAL_FEE,
    ERROR_ENOUGH_FUNDS_FOR_OPERATIONAL_FEE,
    ERROR_ENOUGH_FUNDS_FOR_SETUP_AND_OPERATIONAL_FEE,
    ERROR_INSUFFICIENT_ALGO,
    ERROR_INSUFFICIENT_BALANCE,
    ERROR_IS_STILL_ELIGIBLE,
    ERROR_KEY_BENEFICIARY_MISMATCH,
    ERROR_KEY_CONFIRM_TOO_LATE,
    ERROR_KEY_SUBMIT_TOO_LATE,
    ERROR_LIMIT_BREACH_TOO_EARLY,
    ERROR_NOT_ELIGIBLE,
    ERROR_NOT_ENDED_STATE,
    ERROR_NOT_MANAGER,
    ERROR_NOT_PAYMENT_OR_XFER,
    ERROR_NOT_STATE_CREATED,
    ERROR_NOT_STATE_LIVE,
    ERROR_NOT_STATE_LIVE_OR_SUBMITTED_OR_READY,
    ERROR_NOT_STATE_READY,
    ERROR_NOT_STATE_SET,
    ERROR_NOT_STATE_SUBMITTED,
    ERROR_NOT_YET_EXPIRED,
    ERROR_OPERATION_FEE_ALREADY_CLAIMED_AT_ROUND,
    ERROR_RECEIVER,
    ERROR_REPORT_NOT_CONFIRMED_TOO_EARLY,
    ERROR_REPORT_NOT_SUBMITTED_TOO_EARLY,
    ERROR_TOO_SOON_TO_REPORT_EXPIRY_SOON,
    ERROR_TOO_SOON_TO_REPORT_EXPIRY_SOON_AGAIN,
    ERROR_VOTE_FIRST_ROUND_MISMATCH,
    ERROR_VOTE_LAST_ROUND_MISMATCH,
    MSG_CORE_BREACH_LIMITS_END,
    MSG_CORE_BREACH_LIMITS_ERROR,
    MSG_CORE_BREACH_PAY,
    MSG_CORE_BREACH_SUSPENDED,
    MSG_CORE_CONTRACT_EXPIRED,
    MSG_CORE_KEYS_NOT_CONFIRMED,
    MSG_CORE_KEYS_NOT_SUBMITTED,
    MSG_CORE_KEYS_SUBMIT,
    MSG_CORE_WILL_EXPIRE,
)
from .constants import (
    STATE_CREATED,
    STATE_ENDED_CANNOT_PAY,
    STATE_ENDED_EXPIRED,
    STATE_ENDED_LIMITS,
    STATE_ENDED_MASK,
    STATE_ENDED_NOT_CONFIRMED,
    STATE_ENDED_NOT_SUBMITTED,
    STATE_ENDED_SUSPENDED,
    STATE_ENDED_WITHDREW,
    STATE_LIVE,
    STATE_NONE,
    STATE_READY,
    STATE_SET,
    STATE_SUBMITTED,
)


# ------- Smart contract -------
class DelegatorContract(ARC4Contract, avm_version=11):
    """
    Contract between a delegator manager and a validator (a.k.a. node runner), for the latter to participate in
    consensus on the behalf of the delegator beneficiary for specific amount of time and for a specific fee.
    The contract terms and conditions are defined in this contract.
    The contract also acts as an escrow account for the delegator's payment to the validator for the service.

    Global state
    ------------
    noticeboard_app_id : UInt64
        App ID of noticeboard platform to which this contract belongs to.
    validator_ad_app_id : UInt64
        App ID of validator ad to which this contract belongs to.


    delegation_terms_general : DelegationTermsGeneral
        General delegation terms agreed by delegator and validator to govern this contract.
    fee_operational : UInt64
        Calculated operational fee based on the agreed contract terms.
    fee_operational_partner : UInt64
        Calculated operational fee charged for convenience by the partner.
    delegation_terms_balance : DelegationTermsBalance
        Requirements for delegator beneficiary balance agreed by delegator and validator to govern this contract.

    del_manager : Account
        Delegator manager account.
    del_beneficiary : UInt64
        Delegator beneficiary account.

    round_start : UInt64
        Agreed start round of the contract, i.e. time of its creation.
    round_end : UInt64
        Agreed end round of the contract.
    round_ended : UInt64
        Actual round at which the contract ended.
        Can be smaller than round_end in case of early contract end.

    vote_key_dilution : UInt64
        Vote key dilution parameter of the agreed participation key.
    vote_pk = VotePk
        Vote public key of the agreed participation key.
    selection_pk : SelPk
        Selection public key of the agreed participation key.
    state_proof_pk = StateProofPk
        State proof public key of the agreed participation key.

    state : Bytes
        State of the contract. Can be one of the following:
            CREATED - contract has been created.
            LIVE - contract is live.
            READY - waiting for keys submission.
            SET - contract terms have been set.
            SUBMITTED - waiting for keys confirmation.
            ENDED_NOT_SUBMITTED - keys have not been submitted in time.
            ENDED_NOT_CONFIRMED - keys have not been confirmed in time.
            ENDED_LIMITS - maximum number of limit breach events has been reached.
            ENDED_WITHDREW - delegator withdrew from the contract prematurely.
            ENDED_EXPIRED - contract has expired.
            ENDED_SUSPENDED - delegator has been suspended by consensus.
            ENDED_CANNOT_PAY - delegator cannot pay the validator (as funds could have been frozen and/or clawed back).

    tc_sha256 : Sha256
        Hash (i.e. SHA 256) of the Terms and Conditions defining the delegation contract concluded between the delegator
        and validator.

    cnt_breach_del : UInt64
        Counter of limit breach events.
    round_breach_last : UInt64
        Number of round of last limit breach event.

    round_claim_last : UInt64
        Number of the round the operational fee was last claimed.

    round_expiry_soon_last : UInt64
        Number of the round it was last reported that the contract will expire soon.

    Methods
    -------
    contract_create(
        del_manager: arc4.Address,
        del_beneficiary: arc4.Address,
        noticeboard_app_id: UInt64,
    ) -> Application:
        Creates a new delegator contract and returns its app ID.

    contract_setup(
        delegation_terms_general: DelegationTermsGeneral,
        delegation_terms_balance: DelegationTermsBalance,
        rounds_duration: UInt64,
    ) -> None:
        Sets the delegation contract terms.

    contract_pay(
        txn: gtxn.Transaction,
    ) -> None:
        Pays the validator setup and operational fee.

    keys_confirm(
        del_manager: arc4.Address,
    ) -> None:
        Delegator confirms the participation keys.

    keys_not_confirmed() -> Message:
        Reports that keys have not been confirmed in time.

    keys_not_submitted() -> Message:
        Reports that keys have not been submitted in time.

    keys_submit(
        key_reg_txn_info : KeyRegTxnInfo,
    ) -> EarningsDistributionAndMessage:
        ValidatorAd submits the keys generated for the delegator beneficiary according to the contract terms.

    breach_limits(
    ) -> BreachLimitsReturn:
        Reports that a limit breach event occurred.

    breach_pay(
    ) -> Message:
        Reports that a payment for the fee cannot be made from DelegatorContract (due to freeze or claw back).

    breach_suspended(
    ) -> EarningsDistributionAndMessage:
        Reports that the delegator beneficiary was suspended by consensus.

    contract_claim(
    ) -> EarningsDistribution:
        Claims and distributes the operational fee of validator up to this round to the validator and noticeboard,
        as well as to the partner.

    contract_expired(
    ) -> EarningsDistributionAndMessage:
        Reports that a contract has expired.

    contract_withdraw(
        del_manager: arc4.Address,
    ) -> EarningsDistribution:
        Delegator gracefully withdraws from the contract prematurely.

    contract_delete(
        del_manager: arc4.Address,
        updating : arc4.Bool,
    ) -> ContractDeleteReturn:
        Delegator deletes an ended contract and withdraws any remaining balance.

    contract_report_expiry_soon(
        before_expiry: UInt64,
        report_period: UInt64,
    ) -> Message:
        Reports that the contract will expire soon.

    Private methods
    ---------------
    _distribute_earnings(
        amount: UInt64,
        amount_partner: UInt64,
    ) -> EarningsDistribution:
        Internal method for distributing the earnings between the validator ad and the noticeboard platform,
        as well as for distributing the earnings of the partner.

    _is_eligible(
    ) -> arc4.Bool:
        Check if del_beneficiary meets the agreed balance limits or not

    _try_return_fee(
        fee_asset: Asset,
        amt_return: UInt64,
    ) -> None:
        Tries to return the input fee amount of given asset to del_manager.
        The fee cannot be returned if the del_manager is closed out or frozen for the given asset.

    """

    def __init__(self) -> None:
        """
        Define smart contract's global storage.
        """

        self.noticeboard_app_id = UInt64(0)
        self.validator_ad_app_id = UInt64(0)

        self.delegation_terms_general = GlobalState(
            DelegationTermsGeneral.from_bytes(op.bzero(96)),
            key="G",
            description="General delegation terms."
        )
        self.fee_operational = UInt64(0)
        self.fee_operational_partner = UInt64(0)
        self.delegation_terms_balance = GlobalState(
            DelegationTermsBalance.from_bytes(op.bzero(56)),
            key="B",
            description="Balance related delegation terms."
        )

        self.del_manager = Global.zero_address
        self.del_beneficiary = Global.zero_address

        self.round_start = UInt64(0)
        self.round_end = UInt64(0)
        self.round_ended = UInt64(0)

        self.vote_key_dilution = UInt64(0)
        self.sel_key = SelPk.from_bytes(op.bzero(32))
        self.vote_key = VotePk.from_bytes(op.bzero(32))
        self.state_proof_key = StateProofPk.from_bytes(op.bzero(64))

        self.state = Bytes(STATE_NONE)

        self.tc_sha256 = Sha256.from_bytes(op.bzero(32))

        self.cnt_breach_del = UInt64(0)
        self.round_breach_last = UInt64(0)

        self.round_claim_last = UInt64(0)

        self.round_expiry_soon_last = UInt64(0)

    @arc4.abimethod(create="require")
    def contract_create(
        self,
        del_manager: arc4.Address,
        del_beneficiary: arc4.Address,
        noticeboard_app_id: UInt64,
    ) -> arc4.UInt64:
        """
        Creates a new DelegatorContract.
        Defines delegator contract manager and beneficiary accounts.
        Defines Noticeboard and ValidatorAd app ID to which this contract belongs to.

        Parameters
        ----------
        del_manager : arc4.Address
            Manager address for the delegation contract.
        del_beneficiary : arc4.Address
            Beneficiary address for the delegation contract.
        noticeboard_app_id : UInt64
            App ID of the Noticeboard smart contract to which to tie this contract.

        Returns
        -------
        delegator_app_id : Application
            App ID of the created delegation contract application.
        """

        # Set global variables
        self.noticeboard_app_id = noticeboard_app_id
        self.validator_ad_app_id = Global.caller_application_id

        self.del_manager = del_manager.native
        self.del_beneficiary = del_beneficiary.native

        # Change state to CREATED
        self.state = Bytes(STATE_CREATED)

        return arc4.UInt64(Global.current_application_id.id)

    @arc4.abimethod()
    def contract_setup(
        self,
        tc_sha256: Sha256,
        delegation_terms_general: DelegationTermsGeneral,
        delegation_terms_balance: DelegationTermsBalance,
        rounds_duration: UInt64,
    ) -> None:
        """
        Sets the general and balance delegation contract terms.
        Defines contract start and end rounds.
        Opts in the payment asset if it is not ALGO.

        Parameters
        ----------
        tc_sha256 : Sha256
            Hash (i.e. SHA 256) of the Terms and Conditions defining the delegation contract concluded between the
            delegator and validator.
        delegation_terms_general : DelegationTermsGeneral
            General delegation contract terms.
        delegation_terms_balance : DelegationTermsBalance
            Balance delegation contract terms.
        rounds_duration : UInt64
            Contract duration in number of rounds.

        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR
        assert self.state == Bytes(STATE_CREATED), ERROR_NOT_STATE_CREATED

        self.tc_sha256 = tc_sha256.copy()
        self.delegation_terms_general.value = delegation_terms_general.copy()
        self.delegation_terms_balance.value = delegation_terms_balance.copy()

        self.round_start = Global.round
        self.round_end = self.round_start + rounds_duration
        self.round_claim_last = self.round_start

        # Calculate operational fee
        self.fee_operational = calc_fee_operational(
            fee_round=self.delegation_terms_general.value.fee_round.native,
            round_end=self.round_end,
            round_start=self.round_start,
        )
        # Calculate the partner convenience operational fee
        self.fee_operational_partner = calc_fee_operational(
            fee_round=self.delegation_terms_general.value.fee_round_partner.native,
            round_end=self.round_end,
            round_start=self.round_start,
        )

        if delegation_terms_general.fee_asset_id != UInt64(ALGO_ASA_ID):
            # Opt in to the asset
            itxn.AssetTransfer(
                xfer_asset=delegation_terms_general.fee_asset_id.native,
                asset_receiver=Global.current_application_address,
                asset_amount=0,
            ).submit()

        # Change state to SET
        self.state = Bytes(STATE_SET)

        return

    @arc4.abimethod()
    def contract_pay(
        self,
        txn: gtxn.Transaction,
    ) -> None:
        """
        Pays the validator setup and operational fee.

        Parameters
        ----------
        txn : gtxn.Transaction
            Transaction for the payment of the setup and operational fees.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR
        assert self.state == Bytes(STATE_SET), ERROR_NOT_STATE_SET

        # Check payment
        base_fee = self.delegation_terms_general.value.fee_setup.native + self.fee_operational
        partner_fee = self.delegation_terms_general.value.fee_setup_partner.native + self.fee_operational_partner
        amt_expected = base_fee + partner_fee
        if txn.type == TransactionType.Payment:
            assert txn.receiver == Global.current_application_address, ERROR_RECEIVER

            assert UInt64(ALGO_ASA_ID) == self.delegation_terms_general.value.fee_asset_id, ERROR_ASSET_ID
            assert txn.amount == amt_expected, ERROR_AMOUNT
        elif txn.type == TransactionType.AssetTransfer:
            assert txn.asset_receiver == Global.current_application_address, ERROR_RECEIVER

            assert txn.xfer_asset.id == self.delegation_terms_general.value.fee_asset_id, ERROR_ASSET_ID
            assert txn.asset_amount == amt_expected, ERROR_AMOUNT
        else:
            assert False, ERROR_NOT_PAYMENT_OR_XFER  # noqa: B011

        # Check if del_beneficiary is eligible according to the agreed terms
        assert self._is_eligible().native, ERROR_NOT_ELIGIBLE

        # Change state to READY
        self.state = Bytes(STATE_READY)

        return

    @arc4.abimethod()
    def keys_confirm(
        self,
        del_manager: arc4.Address,
    ) -> None:
        """
        Delegator manager confirms that the delegator beneficiary has confirmed the submitted keys..

        Parameters
        ----------
        del_manager : arc4.Address
            Purported delegator manager account.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR
        assert self.state == Bytes(STATE_SUBMITTED), ERROR_NOT_STATE_SUBMITTED

        assert del_manager == self.del_manager, ERROR_NOT_MANAGER

        # Check if confirmation was done in time
        assert Global.round <= (
            self.round_start +
            self.delegation_terms_general.value.rounds_setup.native +
            self.delegation_terms_general.value.rounds_confirm.native
        ), ERROR_KEY_CONFIRM_TOO_LATE

        # Check that beneficiary account has `AcctIncentiveEligible` flag set to true because otherwise
        # the delegator's contract would report breach_suspension right away.
        acct_incentive_eligible_raw = op.AcctParamsGet.acct_incentive_eligible(self.del_beneficiary)
        acct_incentive_eligible = acct_incentive_eligible_raw[0]
        assert acct_incentive_eligible, ERROR_ACCOUNT_HAS_NOT_REGISTERED_FOR_SUSPENSION_TRACKING

        # Set the last breach round to current one
        self.round_breach_last = Global.round
        # Reset the number of breaches
        self.cnt_breach_del = UInt64(0)

        # Change state to LIVE
        self.state = Bytes(STATE_LIVE)

        return

    @arc4.abimethod()
    def keys_not_confirmed(
        self,
    ) -> Message:
        """
        Reports that keys have not been confirmed in time.

        Returns
        -------
        del_manager : arc4.Address
            Address of delegator manager.
        msg : NotificationMessage
            Notification message about the action.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR
        assert self.state == Bytes(STATE_SUBMITTED), ERROR_NOT_STATE_SUBMITTED

        # Check if time for confirmation has passed
        assert Global.round > (
            self.round_start +
            self.delegation_terms_general.value.rounds_setup.native +
            self.delegation_terms_general.value.rounds_confirm.native
        ), ERROR_REPORT_NOT_CONFIRMED_TOO_EARLY

        # If possible, return the operational fees to the delegator manager
        fee_asset = Asset(self.delegation_terms_general.value.fee_asset_id.native)
        amt_return = self.fee_operational + self.fee_operational_partner
        self._try_return_fee(
            fee_asset=fee_asset,
            amt_return=amt_return,
        )

        # Change state to ENDED_NOT_CONFIRMED
        self.state = Bytes(STATE_ENDED_NOT_CONFIRMED)

        # Mark end of contract
        self.round_ended = Global.round

        msg = NotificationMessage.from_bytes(MSG_CORE_KEYS_NOT_CONFIRMED)
        return Message(
            del_manager=arc4.Address(self.del_manager),
            msg=msg.copy(),
        )

    @arc4.abimethod()
    def keys_not_submitted(
        self,
    ) -> Message:
        """
        Reports that keys have not been submitted in time.

        Returns
        -------
        del_manager : arc4.Address
            Address of delegator manager.
        msg : NotificationMessage
            Notification message about the action.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR
        assert self.state == Bytes(STATE_READY), ERROR_NOT_STATE_READY

        # Check if time for submission has passed
        assert Global.round > (
            self.round_start +
            self.delegation_terms_general.value.rounds_setup.native
        ), ERROR_REPORT_NOT_SUBMITTED_TOO_EARLY

        # If possible, return the sum of the setup and operational fees to the delegator manager
        fee_asset = Asset(self.delegation_terms_general.value.fee_asset_id.native)
        base_fee = self.delegation_terms_general.value.fee_setup.native + self.fee_operational
        partner_fee = self.delegation_terms_general.value.fee_setup_partner.native + self.fee_operational_partner
        amt_return = base_fee + partner_fee
        self._try_return_fee(
            fee_asset=fee_asset,
            amt_return=amt_return,
        )

        # Change state to ENDED_NOT_SUBMITTED
        self.state = Bytes(STATE_ENDED_NOT_SUBMITTED)

        # Mark end of contract
        self.round_ended = Global.round

        msg = NotificationMessage.from_bytes(MSG_CORE_KEYS_NOT_SUBMITTED)
        return Message(
            del_manager=arc4.Address(self.del_manager),
            msg=msg.copy(),
        )

    @arc4.abimethod()
    def keys_submit(
        self,
        key_reg_txn_info : KeyRegTxnInfo,
    ) -> EarningsDistributionAndMessage:
        """
        ValidatorAd submits the keys generated for the delegator beneficiary according to the contract terms.

        Parameters
        ----------
        key_reg_txn_info : KeyRegTxnInfo
            Information about the generated participation keys.

        Returns
        -------
        earnings_distribution : EarningsDistribution
            Amount of earnings of the validator which equal the setup fee minus platform commission,
            amount of platform earnings from the commission, and
            the asset in which the earnings are denoted.
        del_manager : arc4.Address
            Address of delegator manager.
        msg : NotificationMessage
            Notification message about the action.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR
        assert self.state == Bytes(STATE_READY), ERROR_NOT_STATE_READY

        # Sanity check on submitted key information
        assert self.del_beneficiary == key_reg_txn_info.sender, ERROR_KEY_BENEFICIARY_MISMATCH
        assert self.round_start == key_reg_txn_info.vote_first, ERROR_VOTE_FIRST_ROUND_MISMATCH
        assert self.round_end == key_reg_txn_info.vote_last, ERROR_VOTE_LAST_ROUND_MISMATCH

        # Store submitted key information
        self.vote_key_dilution = key_reg_txn_info.vote_key_dilution.native
        self.vote_key = key_reg_txn_info.vote_pk.copy()
        self.sel_key = key_reg_txn_info.selection_pk.copy()
        self.state_proof_key = key_reg_txn_info.state_proof_pk.copy()

        # Check if submission was done in time
        assert Global.round <= (
            self.round_start +
            self.delegation_terms_general.value.rounds_setup.native
        ), ERROR_KEY_SUBMIT_TOO_LATE

        # Distribute earnings from the setup fee
        earnings_distribution = self._distribute_earnings(
            self.delegation_terms_general.value.fee_setup.native,
            self.delegation_terms_general.value.fee_setup_partner.native,
        )

        # Change state to LIVE
        self.state = Bytes(STATE_SUBMITTED)

        msg = NotificationMessage.from_bytes(MSG_CORE_KEYS_SUBMIT)
        return EarningsDistributionAndMessage(
            earnings_distribution = earnings_distribution.copy(),
            del_manager=arc4.Address(self.del_manager),
            msg=msg.copy(),
        )

    @arc4.abimethod()
    def breach_limits(
        self,
    ) -> BreachLimitsReturn:
        """
        Reports that a limit breach event occurred.

        Returns
        -------
        max_breach_reached : arc4.Bool
            Boolean denoting if maximum number of breaches has already been reached (True) or not (False).
        earnings_distribution : EarningsDistribution
            Amount of earnings of the validator which equal any unclaimed operational fee minus platform commission,
            amount of platform earnings from the commission, and
            the asset in which the earnings are denoted.
        del_manager : arc4.Address
            Address of delegator manager.
        msg : NotificationMessage
            Notification message about the action.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR
        assert self.state == Bytes(STATE_LIVE), ERROR_NOT_STATE_LIVE

        assert self.round_end > Global.round, ERROR_ALREADY_EXPIRED

        assert self.round_breach_last + self.delegation_terms_balance.value.rounds_breach.native < Global.round, \
            ERROR_LIMIT_BREACH_TOO_EARLY

        assert not self._is_eligible().native, ERROR_IS_STILL_ELIGIBLE

        # Update limit breach event counter
        self.cnt_breach_del += 1
        self.round_breach_last = Global.round

        # Claim earnings up to this round
        earnings_distribution = self.contract_claim()

        max_breach_reached = False
        msg = NotificationMessage.from_bytes(MSG_CORE_BREACH_LIMITS_ERROR)
        if self.cnt_breach_del >= self.delegation_terms_balance.value.cnt_breach_del_max:
            # Change state to ENDED_LIMITS
            self.state = Bytes(STATE_ENDED_LIMITS)
            # Mark end of contract
            self.round_ended = Global.round
            # Mark that maximum number of breaches has been reached
            max_breach_reached = True
            msg = NotificationMessage.from_bytes(MSG_CORE_BREACH_LIMITS_END)

        return BreachLimitsReturn(
            max_breach_reached = arc4.Bool(max_breach_reached),
            earnings_distribution=earnings_distribution.copy(),
            del_manager=arc4.Address(self.del_manager),
            msg=msg.copy(),
        )

    @arc4.abimethod()
    def breach_pay(
        self,
    ) -> Message:
        """
        Reports that a payment for the fee cannot be made from DelegatorContract.
        This can happen if the DelegatorContract payment asset has been frozen or clawed back by the asset manager.

        Returns
        -------
        del_manager : arc4.Address
            Address of delegator manager.
        msg : NotificationMessage
            Notification message about the action.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR
        assert self.state == Bytes(STATE_LIVE) or self.state == Bytes(STATE_SUBMITTED) or self.state == Bytes(STATE_READY), ERROR_NOT_STATE_LIVE_OR_SUBMITTED_OR_READY  # noqa: E501

        assert self.delegation_terms_general.value.fee_asset_id != UInt64(ALGO_ASA_ID), ERROR_ALGO_IS_PERMISSIONLESS

        fee_round = self.delegation_terms_general.value.fee_round.native
        fee_round_partner = self.delegation_terms_general.value.fee_round_partner.native
        fee_setup = self.delegation_terms_general.value.fee_setup.native
        fee_setup_partner = self.delegation_terms_general.value.fee_setup_partner.native

        asset = Asset(self.delegation_terms_general.value.fee_asset_id.native)
        if asset.frozen(Global.current_application_address):
            pass
        else:
            if self.state == Bytes(STATE_READY):
                base_fee = fee_setup + self.fee_operational
                partner_fee = fee_setup_partner + self.fee_operational_partner
                amt = base_fee + partner_fee
                assert asset.balance(Global.current_application_address) < amt, ERROR_ENOUGH_FUNDS_FOR_SETUP_AND_OPERATIONAL_FEE  # noqa: E501
            elif self.state == Bytes(STATE_SUBMITTED):
                base_fee = self.fee_operational
                partner_fee = self.fee_operational_partner
                amt = base_fee + partner_fee
                assert asset.balance(Global.current_application_address) < amt, ERROR_ENOUGH_FUNDS_FOR_OPERATIONAL_FEE
            elif self.state == Bytes(STATE_LIVE):
                if Global.round < self.round_end:
                    tmp_r = Global.round
                else:
                    tmp_r = self.round_end

                base_fee = calc_fee_operational(
                    fee_round=fee_round,
                    round_end=tmp_r,
                    round_start=self.round_claim_last,
                )
                partner_fee = calc_fee_operational(
                    fee_round=fee_round_partner,
                    round_end=tmp_r,
                    round_start=self.round_claim_last,
                )
                amt = base_fee + partner_fee
                assert asset.balance(Global.current_application_address) < amt, ERROR_ENOUGH_FUNDS_FOR_EARNED_OPERATIONAL_FEE  # noqa: E501

        # Change state to ENDED_CANNOT_PAY
        self.state = Bytes(STATE_ENDED_CANNOT_PAY)
        # Mark end of contract
        self.round_ended = Global.round

        msg = NotificationMessage.from_bytes(MSG_CORE_BREACH_PAY)
        return Message(
            del_manager=arc4.Address(self.del_manager),
            msg=msg.copy(),
        )

    @arc4.abimethod()
    def breach_suspended(
        self,
    ) -> EarningsDistributionAndMessage:
        """
        Reports that the delegator beneficiary was suspended by consensus.

        Returns
        -------
        earnings_distribution : EarningsDistribution
            Amount of earnings of the validator which equal any unclaimed operational fee minus platform commission,
            amount of platform earnings from the commission, and
            the asset in which the earnings are denoted.
        del_manager : arc4.Address
            Address of delegator manager.
        msg : NotificationMessage
            Notification message about the action.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR
        assert self.state == Bytes(STATE_LIVE), ERROR_NOT_STATE_LIVE

        assert self.round_end > Global.round, ERROR_ALREADY_EXPIRED

        # Confirm that account was suspended based on `AcctIncentiveEligible` parameter
        acct_incentive_eligible_raw = op.AcctParamsGet.acct_incentive_eligible(self.del_beneficiary)
        acct_incentive_eligible = acct_incentive_eligible_raw[0]
        assert not acct_incentive_eligible, ERROR_ACCOUNT_HAS_NOT_BEEN_SUSPENDED

        # Claim earnings up to this round
        earnings_distribution = self.contract_claim()
        # Change state to ENDED_SUSPENDED
        self.state = Bytes(STATE_ENDED_SUSPENDED)
        # Mark end of contract
        self.round_ended = Global.round

        msg = NotificationMessage.from_bytes(MSG_CORE_BREACH_SUSPENDED)
        return EarningsDistributionAndMessage(
            earnings_distribution=earnings_distribution.copy(),
            del_manager=arc4.Address(self.del_manager),
            msg=msg.copy(),
        )

    @arc4.abimethod()
    def contract_claim(
        self,
    ) -> EarningsDistribution:
        """
        Claims operational fee of validator up to this round.
        Commission from the fee gets claimed by the noticeboard.
        Partner convenience fee gets claimed by the partner.

        Returns
        -------
        earnings_distribution : EarningsDistribution
            Amount of earnings of the validator which equal any unclaimed operational fee minus platform commission,
            amount of platform earnings from the commission, and
            the asset in which the earnings are denoted.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR
        assert self.state == Bytes(STATE_LIVE), ERROR_NOT_STATE_LIVE

        assert self.round_claim_last < Global.round, ERROR_OPERATION_FEE_ALREADY_CLAIMED_AT_ROUND

        if Global.round > self.round_end:
            round_claim_to = self.round_end
        else:
            round_claim_to = Global.round

        fee_operational_earned = calc_fee_operational(
            self.delegation_terms_general.value.fee_round.native,
            round_claim_to,
            self.round_claim_last,
        )
        fee_operational_earned_partner = calc_fee_operational(
            self.delegation_terms_general.value.fee_round_partner.native,
            round_claim_to,
            self.round_claim_last,
        )
        earnings_distribution = self._distribute_earnings(
            fee_operational_earned,
            fee_operational_earned_partner,
        )

        self.round_claim_last = round_claim_to

        return earnings_distribution.copy()

    @subroutine
    def _distribute_earnings(
        self,
        amount: UInt64,
        amount_partner: UInt64,
    ) -> EarningsDistribution:
        """
        Internal method for distributing the earnings between the validator ad and the noticeboard platform,
        as well as for distributing the earnings of the partner.

        Parameters
        ----------
        amount : UInt64
            Amount of earnings to be distributed.
        amount_partner : UInt64
            Amount of earnings of the partner to be distributed.

        Returns
        -------
        earnings_distribution : EarningsDistribution
            Amount of earnings sent to the validator ad which equal the amount minus platform commission,
            amount of earnings sent to the noticeboard platform which equal the commission, and
            the asset in which the earnings are paid.
        """

        asset = Asset(self.delegation_terms_general.value.fee_asset_id.native)
        val_app = Application(self.validator_ad_app_id)
        pla_app = Application(self.noticeboard_app_id)

        partner = self.delegation_terms_general.value.partner_address.native

        # Calculate earnings
        earnings_distribution = calc_earnings(
            amount=amount,
            commission=self.delegation_terms_general.value.commission.native,
            asset_id=asset.id,
        )

        if asset.id != UInt64(ALGO_ASA_ID):
            assert asset.balance(Global.current_application_address) >= amount + amount_partner, \
                ERROR_INSUFFICIENT_BALANCE

            assert not asset.frozen(Global.current_application_address), \
                ERROR_BALANCE_FROZEN

            # Send validator earnings to ValidatorAd if it can accept them
            if val_app.address.is_opted_in(asset):
                if not asset.frozen(val_app.address):
                    itxn.AssetTransfer(
                        xfer_asset=asset,
                        asset_receiver=val_app.address,
                        asset_amount=earnings_distribution.user.native,
                    ).submit()

            # Send platform earnings to Noticeboard if it can accept them
            if pla_app.address.is_opted_in(asset):
                if not asset.frozen(pla_app.address):
                    itxn.AssetTransfer(
                        xfer_asset=asset,
                        asset_receiver=pla_app.address,
                        asset_amount=earnings_distribution.platform.native,
                    ).submit()

            # Send partner earnings to partner_address if it is non-zero
            if partner != Global.zero_address:
                # Send the earnings if the partner_address can accept them
                if partner.is_opted_in(asset):
                    if not asset.frozen(partner):
                        itxn.AssetTransfer(
                            xfer_asset=asset,
                            asset_receiver=partner,
                            asset_amount=amount_partner,
                        ).submit()
        else:
            assert (
                Global.current_application_address.balance -
                Global.current_application_address.min_balance
            ) >= amount + amount_partner, \
                ERROR_INSUFFICIENT_ALGO
                # If everything is coded correct, this error should be impossible to happen.

            # Send validator earnings to ValidatorAd
            itxn.Payment(
                receiver=val_app.address,
                amount=earnings_distribution.user.native,
            ).submit()

            # Send platform earnings to Noticeboard
            itxn.Payment(
                receiver=pla_app.address,
                amount=earnings_distribution.platform.native,
            ).submit()

            # Send partner earnings to partner_address if it is non-zero
            if partner != Global.zero_address:
                # Try sending partner earnings to partner_address
                if op.balance(partner) >= Global.min_balance:
                    itxn.Payment(
                        receiver=partner,
                        amount=amount_partner,
                    ).submit()

        return earnings_distribution.copy()

    @arc4.abimethod()
    def contract_expired(
        self,
    ) -> EarningsDistributionAndMessage:
        """
        Reports that a contract has expired.

        Returns
        -------
        earnings_distribution : EarningsDistribution
            Amount of earnings of the validator which equal any unclaimed operational fee minus platform commission,
            amount of platform earnings from the commission, and
            the asset in which the earnings are denoted.
        del_manager : arc4.Address
            Address of delegator manager.
        msg : NotificationMessage
            Notification message about the action.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR
        assert self.state == Bytes(STATE_LIVE), ERROR_NOT_STATE_LIVE

        assert self.round_end <= Global.round, ERROR_NOT_YET_EXPIRED

        # Claim earnings up to this round
        earnings_distribution = self.contract_claim()
        # Change state to ENDED_EXPIRED
        self.state = Bytes(STATE_ENDED_EXPIRED)
        # Mark end of contract
        self.round_ended = Global.round

        msg = NotificationMessage.from_bytes(MSG_CORE_CONTRACT_EXPIRED)
        return EarningsDistributionAndMessage(
            earnings_distribution=earnings_distribution.copy(),
            del_manager=arc4.Address(self.del_manager),
            msg=msg.copy(),
        )

    @arc4.abimethod()
    def contract_withdraw(
        self,
        del_manager: arc4.Address,
    ) -> EarningsDistribution:
        """
        Delegator gracefully withdraws from the contract prematurely.
        The delegator beneficiary should issue a key deregistration transaction 320 round before this call.

        Parameters
        ----------
        del_manager : arc4.Address
            Manager address for the delegation contract.

        Returns
        -------
        earnings_distribution : EarningsDistribution
            Amount of earnings of the validator which equal any unclaimed operational fee minus platform commission,
            amount of platform earnings from the commission, and
            the asset in which the earnings are denoted.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR
        assert self.state == Bytes(STATE_LIVE), ERROR_NOT_STATE_LIVE

        assert del_manager == self.del_manager, ERROR_NOT_MANAGER

        assert self.round_end > Global.round, ERROR_ALREADY_EXPIRED

        # Claim earnings up to this round
        earnings_distribution = self.contract_claim()
        # Change state to ENDED_WITHDREW
        self.state = Bytes(STATE_ENDED_WITHDREW)
        # Mark end of contract
        self.round_ended = Global.round

        return earnings_distribution.copy()

    @arc4.abimethod(allow_actions=["DeleteApplication"])
    def contract_delete(
        self,
        del_manager: arc4.Address,
    ) -> ContractDeleteReturn:
        """
        Delegator deletes an ended contract and withdraws any remaining balance.
        There can be non-zero balance to withdraw if someone sent the contract some balance,
        or if it was not possible to claim the fee by validator and/or noticeboard if they had
        the asset frozen.

        Parameters
        ----------
        del_manager : arc4.Address
            Manager address for the delegation contract.

        Returns
        -------
        remaining_balance : UInt64
            Balance of the fee asset that remained in the contract.
        asset_id : UInt64
            Asset ID of the remaining balance.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR
        assert (self.state & Bytes(STATE_ENDED_MASK)) == Bytes(STATE_ENDED_MASK), ERROR_NOT_ENDED_STATE

        assert del_manager == self.del_manager, ERROR_NOT_MANAGER

        asset_id = self.delegation_terms_general.value.fee_asset_id.native
        if asset_id == UInt64(ALGO_ASA_ID):
            bal = Global.current_application_address.balance - Global.current_application_address.min_balance

            itxn.Payment(
                receiver=self.del_manager,
                amount=bal,
            ).submit()
        else:
            asset = Asset(asset_id)
            bal = asset.balance(Global.current_application_address)

            itxn.AssetTransfer(
                xfer_asset=asset,
                asset_receiver=self.del_manager,
                asset_amount=bal,
                asset_close_to=self.del_manager,
            ).submit()

        # Close out the account to delegator manager
        itxn.Payment(
            receiver=self.del_manager,
            amount=0,
            close_remainder_to=self.del_manager,
        ).submit()

        return ContractDeleteReturn(
            remaining_balance=arc4.UInt64(bal),
            asset_id=arc4.UInt64(asset_id),
        )

    @arc4.abimethod()
    def contract_report_expiry_soon(
        self,
        before_expiry: UInt64,
        report_period: UInt64,
    ) -> Message:
        """
        Reports that the contract will expire soon.
        Notification message can be triggered only a pre-defined time in advance and
        with limited frequency to prevent spamming.

        Parameters
        ----------
        before_expiry: UInt64
            How many rounds before contract end can the report be made.
        report_period: UInt64
            How frequently can the report be made.

        Returns
        -------
        del_manager : arc4.Address
            Address of delegator manager.
        msg : NotificationMessage
            Notification message about the action.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR
        assert self.state == Bytes(STATE_LIVE), ERROR_NOT_STATE_LIVE

        assert Global.round + before_expiry >= self.round_end, ERROR_TOO_SOON_TO_REPORT_EXPIRY_SOON
        assert self.round_end > Global.round, ERROR_ALREADY_EXPIRED

        assert Global.round >= self.round_expiry_soon_last + report_period, ERROR_TOO_SOON_TO_REPORT_EXPIRY_SOON_AGAIN
        self.round_expiry_soon_last = Global.round

        msg = NotificationMessage.from_bytes(MSG_CORE_WILL_EXPIRE)
        return Message(
            del_manager=arc4.Address(self.del_manager),
            msg=msg.copy(),
        )

    # ----- ----- ----- ------------------ ----- ----- -----
    # ----- ----- ----- Internal functions ----- ----- -----
    # ----- ----- ----- ------------------ ----- ----- -----
    @subroutine
    def _is_eligible(
        self,
    ) -> arc4.Bool:
        """
        Check if del_beneficiary meets the agreed balance limits or not

        Returns
        -------
        is_eligible : arc4.Bool
            True if del_beneficiary meets all the balance limits, or False if it does not.
        """

        is_eligible = True

        # Check ALGO limit
        algo_bal = self.del_beneficiary.balance
        is_eligible = is_eligible and (algo_bal <= self.delegation_terms_balance.value.stake_max)

        # Check ASA limits
        asa_id_list = self.delegation_terms_balance.value.gating_asa_list.copy()
        for idx in urange(asa_id_list.length):
            asset_id = asa_id_list[idx].id.native
            if asset_id != ALGO_ASA_ID:
                asset = Asset(asset_id)
                if self.del_beneficiary.is_opted_in(asset):
                    asa_bal = asset.balance(self.del_beneficiary)
                else:
                    asa_bal = UInt64(0)
                is_eligible = is_eligible and (asa_bal >= asa_id_list[idx].min.native)

        return arc4.Bool(is_eligible)

    @subroutine
    def _try_return_fee(
        self,
        fee_asset: Asset,
        amt_return: UInt64,
    ) -> None:
        """
        Tries to return the input fee amount of given asset to del_manager.
        The fee cannot be returned if the del_manager is closed out or frozen for the given asset.

        Parameters
        ----------
        fee_asset: Asset
            Asset to return.
        amt_return: UInt64
            Amount to return.
        """

        if fee_asset.id != UInt64(ALGO_ASA_ID):
            if self.del_manager.is_opted_in(fee_asset):
                if not fee_asset.frozen(self.del_manager):
                    asset_balance = fee_asset.balance(self.del_manager)
                    if asset_balance >= amt_return:
                        itxn.AssetTransfer(
                            xfer_asset=fee_asset,
                            asset_receiver=self.del_manager,
                            asset_amount=amt_return,
                        ).submit()
        else:
            if op.balance(self.del_manager) >= Global.min_balance:
                itxn.Payment(
                    receiver=self.del_manager,
                    amount=amt_return,
                ).submit()

        return
