# pyright: reportMissingModuleSource=false


from algopy import (
    Application,
    ARC4Contract,
    Asset,
    BoxMap,
    BoxRef,
    Bytes,
    Global,
    GlobalState,
    TransactionType,
    Txn,
    UInt64,
    arc4,
    compile_contract,
    gtxn,
    itxn,
    op,
    subroutine,
    urange,
)

from smart_contracts.delegator_contract.contract import DelegatorContract
from smart_contracts.validator_ad.constants import (
    STATE_CREATED,
    STATE_NONE,
    STATE_NOT_LIVE,
    STATE_NOT_READY,
    STATE_READY,
    STATE_SET,
    STATE_TEMPLATE_LOAD,
    STATE_TEMPLATE_LOADED,
)

from ..helpers.common import (
    BreachLimitsReturn,
    ContractDeleteReturn,
    DelAppList,
    DelegationTermsBalance,
    DelegationTermsGeneral,
    EarningsDistribution,
    EarningsDistributionAndMessage,
    KeyRegTxnInfo,
    Message,
    PartnerCommissions,
    Sha256,
    ValidatorASA,
    ValidatorSelfDisclosure,
    ValidatorTermsGating,
    ValidatorTermsPricing,
    ValidatorTermsStakeLimits,
    ValidatorTermsTiming,
    ValidatorTermsWarnings,
    maximum,
)
from ..helpers.constants import (
    ALGO_ASA_ID,
    BOX_ASA_KEY_PREFIX,
    BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY,
    ERROR_AD_END_IS_IN_PAST,
    ERROR_AD_TERMS_MBR,
    ERROR_ALGO_AVAILABLE_BALANCE_NOT_ZERO,
    ERROR_AMOUNT,
    ERROR_ASA_BOX_NOT_DELETED,
    ERROR_ASA_NOT_STORED_AT_VALIDATOR_AD,
    ERROR_CALLED_BY_NOT_CREATOR,
    ERROR_CALLED_BY_NOT_VAL_MANAGER,
    ERROR_CALLED_BY_NOT_VAL_OWNER,
    ERROR_CALLED_FROM_STATE_CREATED_TEMPLATE_LOAD_OR_TEMPLATE_LOADED,
    ERROR_CANNOT_REMOVE_ASA_WITH_ACTIVE_DELEGATORS,
    ERROR_DELEGATION_ENDS_TOO_LATE,
    ERROR_DELEGATION_PERIOD_TOO_LONG,
    ERROR_DELEGATION_PERIOD_TOO_SHORT,
    ERROR_DELEGATOR_DOES_NOT_EXIST_AT_VALIDATOR_AD,
    ERROR_DELEGATOR_LIST_FULL,
    ERROR_DELETE_ACTIVE_DELEGATORS,
    ERROR_DELETE_ASA_REMAIN,
    ERROR_DELETE_TEMPLATE_BOX,
    ERROR_FAIL_TO_REMOVE_DELEGATOR_CONTRACT_FROM_LIST,
    ERROR_NO_MEMORY_FOR_MORE_DELEGATORS,
    ERROR_NOT_PAYMENT_OR_XFER,
    ERROR_NOT_STATE_CREATED,
    ERROR_NOT_STATE_READY,
    ERROR_NOT_STATE_READY_OR_NOT_READY,
    ERROR_NOT_STATE_TEMPLATE_LOAD,
    ERROR_RECEIVER,
    ERROR_REQUESTED_MAX_STAKE_TOO_HIGH,
    ERROR_TERM_DURATION_MIN_LARGER_THAN_MAX,
    ERROR_TERM_GRATIS_MAX,
    ERROR_TERMS_MIN_DURATION_SETUP_CONFIRM,
    ERROR_VALIDATOR_FULL,
    FROM_BASE_TO_MICRO_MULTIPLIER,
    FROM_MILLI_TO_NANO_MULTIPLIER,
    MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD,
    ONE_IN_PPM,
    STAKE_GRATIS_MAX,
)


# ------- Smart contract -------
class ValidatorAd(ARC4Contract, avm_version=11):
    """
    Ad of a validator owner to offer node running services to users.
    Users, i.e. delegators, can open requests for the service and conclude an individual delegator contract with the
    validator.
    The contract terms are defined by this ad contents at time of the creation of the delegator contract.
    The validator owner can change the ad to offer different terms for future delegator contracts.
    The validator ad smart contract also acts as an escrow account for the payment received by the validator from
    delegators for its service.

    Global state
    ------------
    noticeboard_app_id : UInt64
        App ID of noticeboard platform to which this contract belongs to.

    terms_time: ValidatorTermsTiming
        Validator's terms about timing.
    terms_price: ValidatorTermsPricing
        Validator's terms about pricing.
    terms_stake: ValidatorTermsStakeLimits
        Validator's terms about stake limits.
    terms_reqs: ValidatorTermsGating
        Validator's terms about gating requirements.
    terms_warn: ValidatorTermsWarnings
        Validator's terms about warnings.

    delegation_terms_general : DelegationTermsGeneral
        General delegation terms that validator defines and agrees to respect if a delegator concludes a delegator
        contract based on them.
    delegation_terms_balance : DelegationTermsBalance
        Requirements for delegator beneficiary balance that validator defines and agrees to respect if a delegator
        concludes a delegator contract based on them.

    val_owner : Account
        Validator owner account.
    val_manager : Account
        Validator manager account.

    val_info : ValidatorSelfDisclosure
        Self-disclosed information about the validator.

    state : Bytes
        State of the contract. Can be one of the following:
            CREATED - validator ad has been created.
            TEMPLATE_LOAD - validator ad is getting loaded the delegator contract template.
            TEMPLATE_LOADED - validator ad ended loading of the delegator contract template.
            SET - initial terms of validator ad have been set.
            READY - validator ad manager is ready to accept new delegators.
            NOT_READY - validator ad manager is not ready to accept new delegators.
            NOT_LIVE - validator ad owner does not want to accept new delegators.

    cnt_del : UInt64
        Counter of current delegators.
    cnt_del_max : UInt64
        Maximum number of delegators the validator is willing to manage simultaneously.
    del_app_list : DelAppList
        List of app ID of the currently active delegator contracts.

    tc_sha256 : Sha256
        Hash (i.e. SHA 256) of the Terms and Conditions agreed by the validator.

    total_algo_earned : UInt64
        Total amount of ALGO the validator ad has earned.
    total_algo_fees_generated : UInt64
        Total amount of ALGO the validator has generated as fees for the platform.

    cnt_asa : UInt64
        Counter of number of different ASAs supported by the contract.

    Box storage
    -----------
    asas : asa_[ASA_ID] = ValidatorASA
        Box map for storing ASA IDs that are or were supported by the validator ad at any point of time before deletion.
        Each entry is a ValidatorASA, with fields for total_earnings and total_fees_generated for that ASA.
        Keys correspond to "asa_" followed by byte representation of ASA ID.

    template : BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY = Bytes
        Box for storing the delegator contract template.

    Methods
    -------
    ad_create(
        val_owner: arc4.Address,
    ) -> arc4.UInt64:
        Creates a new validator ad and returns its app ID.

    ad_config(
        val_owner: arc4.Address,
        val_manager: arc4.Address,
        live : arc4.Bool,
        cnt_del_max : UInt64,
    ) -> None:
        Set the operational configuration of the validator ad.

    ad_delete(
        val_owner: arc4.Address,
    ) -> None:
        Validator owner deletes a validator ad.

    ad_ready(
        val_manager: arc4.Address,
        ready: arc4.Bool,
    ) -> None:
        Ad manager sets its readiness for operation.

    ad_self_disclose(
        val_owner: arc4.Address,
        val_info: ValidatorSelfDisclosure,
    ) -> None:
        Ad owner sets its self-disclosure information.

    ad_terms(
        val_owner: arc4.Address,
        tc_sha256: Sha256,
        terms_time: ValidatorTermsTiming,
        terms_price: ValidatorTermsPricing,
        terms_stake: ValidatorTermsStakeLimits,
        terms_reqs: ValidatorTermsGating,
        terms_warn: ValidatorTermsWarnings,
        txn: gtxn.PaymentTransaction,
    ) -> None:
        Sets all the terms of the validator.

    ad_income(
        val_owner: arc4.Address,
        asset_id: UInt64,
    ) -> arc4.UInt64:
        Validator owner withdraws all available balance from the validator ad for the given asset.

    ad_asa_close(
        val_owner: arc4.Address,
        asset_id: UInt64,
    ) -> None:
        Removes the asset's storage on the validator ad.

    template_load_init(
        val_owner: arc4.Address,
        template_size: UInt64,
        mbr_txn: gtxn.PaymentTransaction,
    ) -> None:
        Starts the process of uploading delegator contract template.

    template_load_data(
        val_owner: arc4.Address,
        offset: UInt64,
        data: Bytes,
    ) -> None:
        Uploads a data chunk to the delegator contract template.

    template_load_end(
        val_owner: arc4.Address,
    ) -> None:
        Ends uploading of the delegator contract template.

    contract_create(
        del_manager: arc4.Address,
        del_beneficiary: arc4.Address,
        rounds_duration: UInt64,
        stake_max: UInt64,
        partner_address: arc4.Address,
        partner_commissions: PartnerCommissions,
        mbr_txn: gtxn.PaymentTransaction,
        txn: gtxn.Transaction,
    ) -> arc4.UInt64:
        Creates a new delegator contract with the current delegation terms for the input
        delegator contract manager and delegator contract beneficiary with the specified duration.

    keys_confirm(
        del_manager: arc4.Address,
        del_app: Application,
    ) -> None:
        Delegator manager confirms that the keys have been confirmed by the delegator beneficiary.

    keys_not_confirmed(
        del_app: Application,
    ) -> Message:
        Reports that keys of a delegator contract have not been confirmed in time.

    keys_not_submitted(
        del_app: Application,
    ) -> Message:
        Reports that keys of a delegator contract have not been submitted in time.

    keys_submit(
        val_manager: arc4.Address,
        del_app: Application,
        key_reg_txn_info : KeyRegTxnInfo,
    ) -> Message:
        Validator manager submits the keys generated for the delegator beneficiary according to the contract terms.

    breach_limits(
        del_app: Application,
    ) -> BreachLimitsReturn:
        Reports that a limit breach event occurred on the delegator beneficiary.

    breach_pay(
        del_app: Application,
    ) -> Message:
        Reports that a payment for the fee cannot be made from the delegator beneficiary.

    breach_suspended(
        del_app: Application,
    ) -> EarningsDistributionAndMessage:
        Reports that the delegator beneficiary was suspended by consensus.

    contract_claim(
        del_app: Application,
    ) -> EarningsDistribution:
        Claims and distributes the operational fee of validator up to this round to the validator and noticeboard.

    contract_expired(
        del_app: Application,
    ) -> Message:
        Reports that a delegator contract has expired.

    contract_withdraw(
        del_manager: arc4.Address,
        del_app: Application,
    ) -> None:
        Reports that a delegator has gracefully withdrawn from the delegator contract prematurely.

    contract_delete(
        del_manager: arc4.Address,
        del_app: Application,
    ) -> ContractDeleteReturn:
        Delegator deletes an ended contract, withdraws any remaining balance, and returns the MBR from ValidatorAd.

    contract_report_expiry_soon(
        before_expiry: UInt64,
        report_period: UInt64,
    ) -> Message:
        Reports that the contract will expire soon.

    gas(
    ) -> None:
        To fit more resources in app reference arrays.

    Private methods
    ---------------
    _add_del_to_list(self, del_app_id: UInt64) -> bool:
        Assign created delegator contract to first free space in the list of delegator contracts.

    _remove_del_from_list(self, del_app_id: UInt64) -> bool:
        Remove the delegator contract from list of delegator contracts.

    _exists_del_in_list(self, del_app_id: UInt64) -> bool:
        Checks if a delegator contract exists in validator ad's list of delegator contracts.

    _mark_validator_earnings(self, earnings_distribution: EarningsDistribution) -> None:
        Mark increase in validator's earnings.

    """

    def __init__(self) -> None:
        """
        Define smart contract's global storage.
        """
        self.noticeboard_app_id = UInt64(0)

        self.tc_sha256 = Sha256.from_bytes(op.bzero(32))

        self.terms_time = GlobalState(
            ValidatorTermsTiming.from_bytes(op.bzero(40)),
            key="T",
        )
        self.terms_price = GlobalState(
            ValidatorTermsPricing.from_bytes(op.bzero(40)),
            key="P",
        )
        self.terms_stake = GlobalState(
            ValidatorTermsStakeLimits.from_bytes(op.bzero(16)),
            key="S",
        )
        self.terms_reqs = GlobalState(
            ValidatorTermsGating.from_bytes(op.bzero(32)),
            key="G",
        )
        self.terms_warn = GlobalState(
            ValidatorTermsWarnings.from_bytes(op.bzero(16)),
            key="W",
        )

        self.val_owner = Global.zero_address
        self.val_manager = Global.zero_address

        self.val_info = GlobalState(
            ValidatorSelfDisclosure.from_bytes(op.bzero(120)),
            key="V",
            description="Self-disclosed information about validator."
        )

        self.state = Bytes(STATE_NONE)

        self.cnt_del = UInt64(0)
        self.cnt_del_max = UInt64(0)

        self.del_app_list = DelAppList.from_bytes(op.bzero(8 * MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD))

        self.total_algo_earned = UInt64(0)
        self.total_algo_fees_generated = UInt64(0)

        self.cnt_asa = UInt64(0)

        self.asas = BoxMap(Asset, ValidatorASA, key_prefix=BOX_ASA_KEY_PREFIX)

        self.template = BoxRef(key=BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY)

    @arc4.abimethod(create="require")
    def ad_create(
        self,
        val_owner: arc4.Address,
    ) -> arc4.UInt64:
        """
        Creates a new ValidatorAd.
        Defines validator ad owner account.
        Defines Noticeboard app ID to which this contract belongs to.

        Parameters
        ----------
        val_owner : arc4.Address
            Owner address for the validator ad.

        Returns
        -------
        validator_app_id : Application
            App ID of the created validator ad application.
        """

        # Set global variables
        self.noticeboard_app_id = Global.caller_application_id

        self.val_owner = val_owner.native

        # Change state to CREATED
        self.state = Bytes(STATE_CREATED)

        return arc4.UInt64(Global.current_application_id.id)

    @arc4.abimethod()
    def ad_config(
        self,
        val_owner: arc4.Address,
        val_manager: arc4.Address,
        live : arc4.Bool,
        cnt_del_max : UInt64,
    ) -> None:
        """
        Sets all operation configuration parameters for the validator ad, i.e.
        the validator manager account, the status whether the ad is live to accept new delegators (`live=True`)
        or not (`live=False`), and the maximum number of delegators the validators can accept.

        Parameters
        ----------
        val_owner : arc4.Address
            Owner address of the validator ad.
        val_manager : arc4.Address
            Manager address for the validator ad.
        live : arc4.Bool
            Set to True if validator ad should be accepting new delegators, otherwise set to False.
        cnt_del_max : UInt64
            Maximum number of delegators the validator is willing to manage simultaneously.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR
        assert (
            self.state != Bytes(STATE_CREATED) and
            self.state != Bytes(STATE_TEMPLATE_LOAD) and
            self.state != Bytes(STATE_TEMPLATE_LOADED)
        ), ERROR_CALLED_FROM_STATE_CREATED_TEMPLATE_LOAD_OR_TEMPLATE_LOADED
        assert val_owner.native == self.val_owner, ERROR_CALLED_BY_NOT_VAL_OWNER

        self.val_manager = val_manager.native

        assert cnt_del_max <= UInt64(MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD), ERROR_NO_MEMORY_FOR_MORE_DELEGATORS  # noqa: E501
        self.cnt_del_max = cnt_del_max

        if live.native:
            self.state = Bytes(STATE_NOT_READY)
        else:
            self.state = Bytes(STATE_NOT_LIVE)

        return

    @arc4.abimethod(allow_actions=["DeleteApplication"])
    def ad_delete(
        self,
        val_owner: arc4.Address,
    ) -> None:
        """
        Validator owner deletes a validator ad.
        Possible only if there are no active delegators and all balances have been claimed.

        Parameters
        ----------
        val_owner : arc4.Address
            Owner address of the validator ad.

        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR
        assert val_owner.native == self.val_owner, ERROR_CALLED_BY_NOT_VAL_OWNER

        assert self.cnt_del == UInt64(0), ERROR_DELETE_ACTIVE_DELEGATORS
        assert self.cnt_asa == UInt64(0), ERROR_DELETE_ASA_REMAIN

        assert Global.current_application_address.balance-Global.current_application_address.min_balance == UInt64(0), \
            ERROR_ALGO_AVAILABLE_BALANCE_NOT_ZERO

        assert self.template.delete(), ERROR_DELETE_TEMPLATE_BOX # Should not be possible to raise the error if code ok

        # Close account to owner to return the MBR
        rcv = self.val_owner
        itxn.Payment(
            receiver=rcv,
            amount=0,
            close_remainder_to=rcv,
        ).submit()

        return

    @arc4.abimethod()
    def ad_ready(
        self,
        val_manager: arc4.Address,
        ready: arc4.Bool,
    ) -> None:
        """
        Ad manager sets its readiness for operation.

        Parameters
        ----------
        val_manager : arc4.Address
            Manager address for the validator ad.
        ready : arc4.Bool
            Set to True if validator manager is ready for accepting new delegators, otherwise set to False.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR
        assert (
            self.state == Bytes(STATE_READY) or
            self.state == Bytes(STATE_NOT_READY)
        ), ERROR_NOT_STATE_READY_OR_NOT_READY

        assert val_manager.native == self.val_manager, ERROR_CALLED_BY_NOT_VAL_MANAGER

        if ready.native:
            self.state = Bytes(STATE_READY)
        else:
            self.state = Bytes(STATE_NOT_READY)

        return

    @arc4.abimethod()
    def ad_self_disclose(
        self,
        val_owner: arc4.Address,
        val_info: ValidatorSelfDisclosure,
    ) -> None:
        """
        Ad owner sets its self-disclosure information.

        Parameters
        ----------
        val_owner : arc4.Address
            Owner address of the validator ad.
        val_info : ValidatorSelfDisclosure
            Self-disclosed information about the validator.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR
        assert val_owner.native == self.val_owner, ERROR_CALLED_BY_NOT_VAL_OWNER

        self.val_info.value = val_info.copy()

        return

    @arc4.abimethod()
    def ad_terms(
        self,
        val_owner: arc4.Address,
        tc_sha256: Sha256,
        terms_time: ValidatorTermsTiming,
        terms_price: ValidatorTermsPricing,
        terms_stake: ValidatorTermsStakeLimits,
        terms_reqs: ValidatorTermsGating,
        terms_warn: ValidatorTermsWarnings,
        txn: gtxn.PaymentTransaction,
    ) -> None:
        """
        Sets all the terms of the validator.
        With this action, the validator agrees with the (new) terms.

        Parameters
        ----------
        val_owner : arc4.Address
            Owner address of the validator ad.
        tc_sha256 : Sha256
            Hash (i.e. SHA 256) of the Terms and Conditions agreed by the validator.
        terms_time: ValidatorTermsTiming
            Validator's terms about timing.
        terms_price: ValidatorTermsPricing
            Validator's terms about pricing.
        terms_stake: ValidatorTermsStakeLimits
            Validator's terms about stake limits.
        terms_reqs: ValidatorTermsGating
            Validator's terms about gating requirements.
        terms_warn: ValidatorTermsWarnings
            Validator's terms about warnings.
        txn : gtxn.PaymentTransaction
            Transaction for the payment of MBR increase.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR
        assert val_owner.native == self.val_owner, ERROR_CALLED_BY_NOT_VAL_OWNER

        mbr_cur = Global.current_application_address.min_balance

        # Sanity checks on input terms
        assert terms_time.rounds_setup.native + terms_time.rounds_confirm.native < terms_time.rounds_duration_min, \
            ERROR_TERMS_MIN_DURATION_SETUP_CONFIRM
        assert terms_time.rounds_duration_min <= terms_time.rounds_duration_max, \
            ERROR_TERM_DURATION_MIN_LARGER_THAN_MAX
        assert terms_stake.stake_gratis <= UInt64(STAKE_GRATIS_MAX), ERROR_TERM_GRATIS_MAX
        assert terms_time.round_max_end > Global.round, ERROR_AD_END_IS_IN_PAST

        self.tc_sha256 = tc_sha256.copy()
        self.terms_time.value = terms_time.copy()
        self.terms_price.value = terms_price.copy()
        self.terms_stake.value = terms_stake.copy()
        self.terms_reqs.value = terms_reqs.copy()
        self.terms_warn.value = terms_warn.copy()

        asset_id = terms_price.fee_asset_id.native
        if asset_id != UInt64(ALGO_ASA_ID):
            asset = Asset(asset_id)
            if asset not in self.asas:
                # Opt in to the asset
                itxn.AssetTransfer(
                    xfer_asset=asset,
                    asset_receiver=Global.current_application_address,
                    asset_amount=0,
                ).submit()

                # Create the entry
                self.asas[asset] = ValidatorASA(
                    total_earning=arc4.UInt64(0),
                    total_fees_generated=arc4.UInt64(0),
                )

                self.cnt_asa += 1

        # Check if payment for increase of MBR was made
        assert txn.receiver == Global.current_application_address, ERROR_RECEIVER
        mbr_new = Global.current_application_address.min_balance
        mbr_pay_amount = mbr_new - mbr_cur
        assert txn.amount == mbr_pay_amount, ERROR_AD_TERMS_MBR


        if self.state == Bytes(STATE_TEMPLATE_LOADED):
            self.state = Bytes(STATE_SET)

        return

    @arc4.abimethod()
    def ad_income(
        self,
        val_owner: arc4.Address,
        asset_id: UInt64,
    ) -> arc4.UInt64:
        """
        Validator owner withdraws all available balance from the validator ad for the given asset.

        Parameters
        ----------
        val_owner : arc4.Address
            Owner address of the validator ad.
        asset_id : UInt64
            ID of the asset (i.e. ASA ID or 0 for ALGO) for which the owner would like to withdraw all earnings from
            the validator ad.

        Returns
        -------
        income : arc4.UInt64
            Withdrawn income from the validator ad for the input asset.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR
        assert val_owner.native == self.val_owner, ERROR_CALLED_BY_NOT_VAL_OWNER

        asset = Asset(asset_id)
        if asset.id != UInt64(ALGO_ASA_ID):
            bal = asset.balance(Global.current_application_address)
            itxn.AssetTransfer(
                xfer_asset=asset,
                asset_receiver=val_owner.native,
                asset_amount=bal,
            ).submit()
        else:
            bal = Global.current_application_address.balance - Global.current_application_address.min_balance
            itxn.Payment(
                receiver=val_owner.native,
                amount=bal,
            ).submit()

        return arc4.UInt64(bal)

    @arc4.abimethod()
    def ad_asa_close(
        self,
        val_owner: arc4.Address,
        asset_id: UInt64,
    ) -> None:
        """
        Removes the asset's storage on the validator ad.
        To be used before deleting the contract.

        Parameters
        ----------
        val_owner : arc4.Address
            Owner address of the validator ad.
        asset_id : UInt64
            ID of the asset (i.e. ASA ID or 0 for ALGO) for which the owner would like remove its storage.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR
        assert val_owner.native == self.val_owner, ERROR_CALLED_BY_NOT_VAL_OWNER

        assert self.cnt_del == UInt64(0), ERROR_CANNOT_REMOVE_ASA_WITH_ACTIVE_DELEGATORS

        asset = Asset(asset_id)
        # Check if ASA is even stored on the ValidatorAd. This inherently fails for ALGO, which is stored separately.
        assert asset in self.asas, ERROR_ASA_NOT_STORED_AT_VALIDATOR_AD

        assert op.Box.delete(Bytes(BOX_ASA_KEY_PREFIX) + op.itob(asset_id)), ERROR_ASA_BOX_NOT_DELETED
        self.cnt_asa -= 1

        itxn.AssetTransfer(
            xfer_asset=asset,
            asset_receiver=val_owner.native,
            asset_amount=0,
            asset_close_to=val_owner.native,
        ).submit()

        return

    @arc4.abimethod()
    def template_load_init(
        self,
        val_owner: arc4.Address,
        template_size: UInt64,
        mbr_txn: gtxn.PaymentTransaction,
    ) -> None:
        """
        Starts the process of uploading delegator contract template.

        Parameters
        ----------
        val_owner : arc4.Address
            Owner address of the validator ad.
        template_size : UInt64
            Size of the delegator contract template in bytes.
        mbr_txn : gtxn.PaymentTransaction
            Payment transaction for the payment of the increase of validator ad MBR due to creation of
            box for storing the delegator contract template.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR
        assert val_owner.native == self.val_owner, ERROR_CALLED_BY_NOT_VAL_OWNER

        mbr_cur = Global.current_application_address.min_balance

        assert self.state == Bytes(STATE_CREATED), ERROR_NOT_STATE_CREATED

        assert self.template.create(size=template_size)

        self.state = Bytes(STATE_TEMPLATE_LOAD)

        # Check if the input MBR payment transaction was sufficient for increase validator ad's MBR
        mbr_new = Global.current_application_address.min_balance
        amt = (mbr_new - mbr_cur)
        assert mbr_txn.receiver == Global.current_application_address, ERROR_RECEIVER
        assert mbr_txn.amount == amt, ERROR_AMOUNT

        return

    @arc4.abimethod()
    def template_load_data(
        self,
        val_owner: arc4.Address,
        offset: UInt64,
        data: Bytes,
    ) -> None:
        """
        Uploads a data chunk to the delegator contract template.

        Parameters
        ----------
        val_owner : arc4.Address
            Owner address of the validator ad.
        offset : UInt64
            Offset in the box at which to replace the data.
        data : Bytes
            Data to replace in the box at the defined position.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR
        assert val_owner.native == self.val_owner, ERROR_CALLED_BY_NOT_VAL_OWNER

        assert self.state == Bytes(STATE_TEMPLATE_LOAD), ERROR_NOT_STATE_TEMPLATE_LOAD

        self.template.replace(offset, data)

        return

    @arc4.abimethod()
    def template_load_end(
        self,
        val_owner: arc4.Address,
    ) -> None:
        """
        Ends uploading of the delegator contract template.

        Parameters
        ----------
        val_owner : arc4.Address
            Owner address of the validator ad.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR
        assert val_owner.native == self.val_owner, ERROR_CALLED_BY_NOT_VAL_OWNER

        assert self.state == Bytes(STATE_TEMPLATE_LOAD), ERROR_NOT_STATE_TEMPLATE_LOAD

        self.state = Bytes(STATE_TEMPLATE_LOADED)

        return

    # # ----- ----- ----- ----------------------------- ----- ----- -----
    # # ----- ----- ----- Delegator Contract Management ----- ----- -----
    # # ----- ----- ----- ----------------------------- ----- ----- -----

    @arc4.abimethod()
    def contract_create(
        self,
        del_manager: arc4.Address,
        del_beneficiary: arc4.Address,
        rounds_duration: UInt64,
        stake_max: UInt64,
        partner_address: arc4.Address,
        partner_commissions: PartnerCommissions,
        mbr_txn: gtxn.PaymentTransaction,
        txn: gtxn.Transaction,
    ) -> arc4.UInt64:
        """
        Creates a new delegator contract with the current delegation terms for the input
        delegator contract manager and delegator contract beneficiary with the specified duration.

        Parameters
        ----------
        del_manager : arc4.Address
            Manager address for the delegation contract.
        del_beneficiary : arc4.Address
            Beneficiary address for the delegation contract.
        rounds_duration : UInt64
            Contract duration in number of rounds.
        stake_max : UInt64
            The maximum amount of ALGO that the delegator beneficiary address intends to have at any point in time
            during the contract duration.
        partner_address : arc4.Address
            Address of the partner that collects the partner convenience fees.
            If there is no partner, set it to Global.zero_address.
        partner_commissions : PartnerCommissions
            Commissions charged on top of validator setup and operational fees, for partner's convenience offer.
            The values are represented in ppm.
        mbr_txn : gtxn.PaymentTransaction
            Payment transaction for the payment of the increase of validator ad MBR due to creation of a new contract.
        txn : gtxn.Transaction
            Transaction for the payment of the setup and operational fee.

        Returns
        -------
        delegator_app_id : arc4.UInt64
            App ID of the created delegator contract application.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR

        assert self.state == Bytes(STATE_READY), ERROR_NOT_STATE_READY

        mbr_cur = Global.current_application_address.min_balance

        # Create a new delegator contract
        compiled = compile_contract(DelegatorContract)
        if self.template.length > UInt64(4096):
            approval_program = (
                self.template.extract(UInt64(0), UInt64(4096)),
                self.template.extract(UInt64(4096), self.template.length - UInt64(4096)),
            )
        else:
            approval_program = (
                self.template.extract(UInt64(0), self.template.length),
                Bytes(),
            )

        del_app_id, txn_create = arc4.abi_call(
            DelegatorContract.contract_create,
            del_manager,
            del_beneficiary,
            self.noticeboard_app_id,
            approval_program=approval_program,
            clear_state_program=compiled.clear_state_program,
            global_num_uint=compiled.global_uints,
            global_num_bytes=compiled.global_bytes,
            local_num_uint=compiled.local_uints,
            local_num_bytes=compiled.local_bytes,
            extra_program_pages=compiled.extra_program_pages,
        )
        del_app = Application(del_app_id.native)

        # Fund the created delegator contract
        del_mbr_fund = Global.min_balance + Global.asset_opt_in_min_balance
        itxn.Payment(
            receiver=del_app.address,
            amount=del_mbr_fund,
        ).submit()

        # Setup the delegator contract
        assert rounds_duration >= self.terms_time.value.rounds_duration_min, ERROR_DELEGATION_PERIOD_TOO_SHORT
        assert rounds_duration <= self.terms_time.value.rounds_duration_max, ERROR_DELEGATION_PERIOD_TOO_LONG
        assert Global.round + rounds_duration <= self.terms_time.value.round_max_end, ERROR_DELEGATION_ENDS_TOO_LATE

        stake_max_scaled_price = stake_max // UInt64(FROM_BASE_TO_MICRO_MULTIPLIER)
        tmp = op.mulw(self.terms_price.value.fee_round_var.native, stake_max_scaled_price)
        fee_round_var = op.divw(tmp[0], tmp[1], UInt64(FROM_MILLI_TO_NANO_MULTIPLIER))
        fee_round = maximum(
            self.terms_price.value.fee_round_min.native,
            fee_round_var
        )
        fee_setup = self.terms_price.value.fee_setup.native

        if partner_address != arc4.Address(Global.zero_address):
            tmp = op.mulw(fee_round, partner_commissions.commission_operational.native)
            fee_round_partner = op.divw(tmp[0], tmp[1], UInt64(ONE_IN_PPM))

            tmp = op.mulw(fee_setup, partner_commissions.commission_setup.native)
            fee_setup_partner = op.divw(tmp[0], tmp[1], UInt64(ONE_IN_PPM))
        else:
            fee_round_partner = UInt64(0)
            fee_setup_partner = UInt64(0)

        delegation_terms_general = DelegationTermsGeneral(
            commission = self.terms_price.value.commission,
            fee_round = arc4.UInt64(fee_round),
            fee_setup = arc4.UInt64(fee_setup),
            fee_asset_id = self.terms_price.value.fee_asset_id,
            partner_address = partner_address,
            fee_round_partner = arc4.UInt64(fee_round_partner),
            fee_setup_partner = arc4.UInt64(fee_setup_partner),
            rounds_setup = self.terms_time.value.rounds_setup,
            rounds_confirm = self.terms_time.value.rounds_confirm,
        )

        stake_max_max = self.terms_stake.value.stake_max.native
        assert stake_max <= stake_max_max, ERROR_REQUESTED_MAX_STAKE_TOO_HIGH

        tmp = op.mulw(stake_max, self.terms_stake.value.stake_gratis.native)
        stake_gratis_abs = op.divw(tmp[0], tmp[1], UInt64(STAKE_GRATIS_MAX))
        stake_max_w_gratis = stake_max + stake_gratis_abs
        if stake_max_w_gratis < stake_max_max:
            stake_max_given = stake_max_w_gratis
        else:
            stake_max_given = stake_max_max

        delegation_terms_balance = DelegationTermsBalance(
            stake_max = arc4.UInt64(stake_max_given),
            cnt_breach_del_max = self.terms_warn.value.cnt_warning_max,
            rounds_breach = self.terms_warn.value.rounds_warning,
            gating_asa_list = self.terms_reqs.value.gating_asa_list.copy(),
        )

        app_txn = arc4.abi_call(
            DelegatorContract.contract_setup,
            self.tc_sha256.copy(),
            delegation_terms_general.copy(),
            delegation_terms_balance.copy(),
            rounds_duration,
            app_id=del_app.id,
        )

        # Check payment and forward it to the created delegator contract
        if txn.type == TransactionType.Payment:
            assert txn.receiver == Global.current_application_address, ERROR_RECEIVER
            txn_forward = itxn.InnerTransaction(
                type=TransactionType.Payment,
                receiver=del_app.address,
                amount=txn.amount,
            )
        elif txn.type == TransactionType.AssetTransfer:
            assert txn.asset_receiver == Global.current_application_address, ERROR_RECEIVER
            txn_forward = itxn.InnerTransaction(
                type=TransactionType.AssetTransfer,
                xfer_asset=txn.xfer_asset,
                asset_receiver=del_app.address,
                asset_amount=txn.asset_amount,
            )
        else:
            assert False, ERROR_NOT_PAYMENT_OR_XFER  # noqa: B011

        # Pay setup fee to the delegator contract
        app_txn = arc4.abi_call(  # noqa: F841
            DelegatorContract.contract_pay,
            txn_forward.copy(),
            app_id=del_app.id,
        )

        # Add created delegator contract to the list of active delegators of this validator ad
        assert self._add_del_to_list(del_app.id), ERROR_DELEGATOR_LIST_FULL
        # Check if validator ad has reached its limit on maximum accepted delegators
        assert self.cnt_del <= self.cnt_del_max, ERROR_VALIDATOR_FULL

        # Check if the input MBR payment transaction was sufficient for increase validator ad's MBR and
        # for funding the delegator contract's MBR
        mbr_new = Global.current_application_address.min_balance
        amt = del_mbr_fund + (mbr_new - mbr_cur)
        assert mbr_txn.receiver == Global.current_application_address, ERROR_RECEIVER
        assert mbr_txn.amount == amt, ERROR_AMOUNT

        return arc4.UInt64(del_app.id)

    @arc4.abimethod()
    def keys_confirm(
        self,
        del_manager: arc4.Address,
        del_app: Application,
    ) -> None:
        """
        Delegator manager confirms that the delegator beneficiary has confirmed the submitted keys
        and pays for the operational fee.

        Parameters
        ----------
        del_manager : arc4.Address
            Purported delegator manager account.
        del_app_id : UInt64
            App ID of the delegator contract.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR

        assert self._exists_del_in_list(del_app.id), ERROR_DELEGATOR_DOES_NOT_EXIST_AT_VALIDATOR_AD

        # Call keys_confirm of the delegator contract
        app_txn = arc4.abi_call(  # noqa: F841
            DelegatorContract.keys_confirm,
            del_manager,
            app_id=del_app.id,
        )

        return

    @arc4.abimethod()
    def keys_not_confirmed(
        self,
        del_app: Application,
    ) -> Message:
        """
        Reports that keys of a delegator contract have not been confirmed in time.

        Parameters
        ----------
        del_app : Application
            App ID of the delegator contract.

        Returns
        -------
        del_manager : arc4.Address
            Address of delegator manager.
        msg : NotificationMessage
            Notification message about the action.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR

        assert self._exists_del_in_list(del_app.id), ERROR_DELEGATOR_DOES_NOT_EXIST_AT_VALIDATOR_AD

        # Call keys_not_confirmed of the delegator contract
        res, app_txn = arc4.abi_call(
            DelegatorContract.keys_not_confirmed,
            app_id=del_app.id,
        )

        # Remove the delegator contract from the list
        assert self._remove_del_from_list(del_app.id), ERROR_FAIL_TO_REMOVE_DELEGATOR_CONTRACT_FROM_LIST

        return Message(
            del_manager=res.del_manager,
            msg=res.msg.copy(),
        )

    @arc4.abimethod()
    def keys_not_submitted(
        self,
        del_app: Application,
    ) -> Message:
        """
        Reports that keys of a delegator contract have not been submitted in time.

        Parameters
        ----------
        del_app : Application
            App ID of the delegator contract.

        Returns
        -------
        del_manager : arc4.Address
            Address of delegator manager.
        msg : NotificationMessage
            Notification message about the action.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR

        assert self._exists_del_in_list(del_app.id), ERROR_DELEGATOR_DOES_NOT_EXIST_AT_VALIDATOR_AD

        # Call keys_not_submitted of the delegator contract
        res, app_txn = arc4.abi_call(
            DelegatorContract.keys_not_submitted,
            app_id=del_app.id,
        )

        # Remove the delegator contract from the list
        assert self._remove_del_from_list(del_app.id), ERROR_FAIL_TO_REMOVE_DELEGATOR_CONTRACT_FROM_LIST

        return Message(
            del_manager=res.del_manager,
            msg=res.msg.copy(),
        )

    @arc4.abimethod()
    def keys_submit(
        self,
        val_manager: arc4.Address,
        del_app: Application,
        key_reg_txn_info : KeyRegTxnInfo,
    ) -> Message:
        """
        Validator manager submits the keys generated for the delegator beneficiary according to the contract terms.

        Parameters
        ----------
        val_manager : arc4.Address
            Purported validator manager account.
        del_app : Application
            App ID of the delegator contract.
        key_reg_txn_info : KeyRegTxnInfo
            Information about the generated participation keys.

        Returns
        -------
        del_manager : arc4.Address
            Address of delegator manager.
        msg : arc4.String
            Notification message about the action.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR

        assert self._exists_del_in_list(del_app.id), ERROR_DELEGATOR_DOES_NOT_EXIST_AT_VALIDATOR_AD

        assert self.val_manager == val_manager.native, ERROR_CALLED_BY_NOT_VAL_MANAGER

        # Call keys_submit of the delegator contract
        res, app_txn = arc4.abi_call(
            DelegatorContract.keys_submit,
            key_reg_txn_info,
            app_id=del_app.id,
        )
        earnings_distribution = res.earnings_distribution.copy()

        # Mark increase in validator's earnings
        self._mark_validator_earnings(earnings_distribution.copy())

        return Message(
            del_manager=res.del_manager,
            msg=res.msg.copy(),
        )

    @arc4.abimethod()
    def breach_limits(
        self,
        del_app: Application,
    ) -> BreachLimitsReturn:
        """
        Reports that a limit breach event occurred on the delegator beneficiary.

        Parameters
        ----------
        del_app : Application
            App ID of the delegator contract.

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

        assert self._exists_del_in_list(del_app.id), ERROR_DELEGATOR_DOES_NOT_EXIST_AT_VALIDATOR_AD

        # Call breach_limits of the delegator contract
        res, app_txn = arc4.abi_call(
            DelegatorContract.breach_limits,
            app_id=del_app.id,
        )

        # Mark increase in validator's earnings
        self._mark_validator_earnings(res.earnings_distribution.copy())

        if res.max_breach_reached.native:
            # Remove the delegator contract from the list
            assert self._remove_del_from_list(del_app.id), ERROR_FAIL_TO_REMOVE_DELEGATOR_CONTRACT_FROM_LIST

        return res.copy()

    @arc4.abimethod()
    def breach_pay(
        self,
        del_app: Application,
    ) -> Message:
        """
        Reports that a payment for the fee cannot be made from the delegator contract.
        This can happen if the DelegatorContract payment asset has been frozen or clawed back by the asset manager.

        Parameters
        ----------
        del_app : Application
            App ID of the delegator contract.

        Returns
        -------
        del_manager : arc4.Address
            Address of delegator manager.
        msg : NotificationMessage
            Notification message about the action.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR

        assert self._exists_del_in_list(del_app.id), ERROR_DELEGATOR_DOES_NOT_EXIST_AT_VALIDATOR_AD

        # Call breach_pay of the delegator contract
        res, app_txn = arc4.abi_call(
            DelegatorContract.breach_pay,
            app_id=del_app.id,
        )

        # Remove the delegator contract from the list
        assert self._remove_del_from_list(del_app.id), ERROR_FAIL_TO_REMOVE_DELEGATOR_CONTRACT_FROM_LIST

        return res.copy()

    @arc4.abimethod()
    def breach_suspended(
        self,
        del_app: Application,
    ) -> EarningsDistributionAndMessage:
        """
        Reports that the delegator beneficiary was suspended by consensus.

        Parameters
        ----------
        del_app : Application
            App ID of the delegator contract.

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

        assert self._exists_del_in_list(del_app.id), ERROR_DELEGATOR_DOES_NOT_EXIST_AT_VALIDATOR_AD

        # Call breach_suspended of the delegator contract
        res, app_txn = arc4.abi_call(
            DelegatorContract.breach_suspended,
            app_id=del_app.id,
        )

        # Mark increase in validator's earnings
        self._mark_validator_earnings(res.earnings_distribution.copy())

        # Remove the delegator contract from the list
        assert self._remove_del_from_list(del_app.id), ERROR_FAIL_TO_REMOVE_DELEGATOR_CONTRACT_FROM_LIST

        return res.copy()

    @arc4.abimethod()
    def contract_claim(
        self,
        del_app: Application,
    ) -> EarningsDistribution:
        """
        Claims the operational fee up to this round from a delegator contract and
        transfers it to the validator ad as well as the commission to the platform.

        Parameters
        ----------
        del_app : Application
            App ID of the delegator contract.

        Returns
        -------
        earnings_distribution : EarningsDistribution
            Amount of earnings of validator which equal any not yet claimed operational fee minus platform commission,
            amount of platform earnings from the commission, and
            the asset in which the earnings are denoted.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR

        assert self._exists_del_in_list(del_app.id), ERROR_DELEGATOR_DOES_NOT_EXIST_AT_VALIDATOR_AD

        # Call keys_not_submitted of the delegator contract
        earnings_distribution, app_txn = arc4.abi_call(
            DelegatorContract.contract_claim,
            app_id=del_app.id,
        )

        # Mark increase in validator's earnings
        self._mark_validator_earnings(earnings_distribution.copy())

        return earnings_distribution.copy()

    @arc4.abimethod()
    def contract_expired(
        self,
        del_app: Application,
    ) -> Message:
        """
        Reports that a delegator contract has expired.

        Parameters
        ----------
        del_app : Application
            App ID of the delegator contract.

        Returns
        -------
        del_manager : arc4.Address
            Address of delegator manager.
        msg : NotificationMessage
            Notification message about the action.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR

        assert self._exists_del_in_list(del_app.id), ERROR_DELEGATOR_DOES_NOT_EXIST_AT_VALIDATOR_AD

        # Call contract_expired of the delegator contract
        res, app_txn = arc4.abi_call(
            DelegatorContract.contract_expired,
            app_id=del_app.id,
        )

        # Mark increase in validator's earnings
        self._mark_validator_earnings(res.earnings_distribution.copy())

        # Remove the delegator contract from the list
        assert self._remove_del_from_list(del_app.id), ERROR_FAIL_TO_REMOVE_DELEGATOR_CONTRACT_FROM_LIST

        return Message(
            del_manager=res.del_manager,
            msg=res.msg.copy(),
        )

    @arc4.abimethod()
    def contract_withdraw(
        self,
        del_manager: arc4.Address,
        del_app: Application,
    ) -> None:
        """
        Reports that a delegator has gracefully withdrawn from the contract prematurely.
        The delegator beneficiary should issue a key deregistration transaction 320 round before this call.

        Parameters
        ----------
        del_manager : arc4.Address
            Purported delegator manager account.
        del_app : Application
            App ID of the delegator contract.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR

        assert self._exists_del_in_list(del_app.id), ERROR_DELEGATOR_DOES_NOT_EXIST_AT_VALIDATOR_AD

        # Call contract_withdraw of the delegator contract
        earnings_distribution, app_txn = arc4.abi_call(
            DelegatorContract.contract_withdraw,
            del_manager,
            app_id=del_app.id,
        )

        # Mark increase in validator's earnings
        self._mark_validator_earnings(earnings_distribution.copy())

        # Remove the delegator contract from the list
        assert self._remove_del_from_list(del_app.id), ERROR_FAIL_TO_REMOVE_DELEGATOR_CONTRACT_FROM_LIST

        return

    @arc4.abimethod()
    def contract_delete(
        self,
        del_manager: arc4.Address,
        del_app: Application,
    ) -> ContractDeleteReturn:
        """
        Delegator deletes an ended contract, withdraws any remaining balance, and returns the MBR from ValidatorAd.

        Parameters
        ----------
        del_manager : arc4.Address
            Purported delegator manager account.
        del_app : Application
            App ID of the delegator contract.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR

        mbr_cur = Global.current_application_address.min_balance

        # Call contract_delete of the delegator contract
        remaining_balance, app_txn = arc4.abi_call(
            DelegatorContract.contract_delete,
            del_manager,
            app_id=del_app.id,
        )

        mbr_new = Global.current_application_address.min_balance
        amt = mbr_cur - mbr_new

        # Send the freed MBR to delegator manager
        itxn.Payment(
            receiver=del_manager.native,
            amount=amt,
        ).submit()

        return remaining_balance

    @arc4.abimethod()
    def contract_report_expiry_soon(
        self,
        before_expiry: UInt64,
        report_period: UInt64,
        del_app: Application,
    ) -> Message:
        """
        Reports that the contract will expire soon.

        Parameters
        ----------
        before_expiry: UInt64
            How many rounds before contract end can the report be made.
        report_period: UInt64
            How frequently can the report be made.
        del_app : Application
            App ID of the delegator contract.

        Returns
        -------
        del_manager : arc4.Address
            Address of delegator manager.
        msg : NotificationMessage
            Notification message about the action.
        """

        assert Txn.sender == Global.creator_address, ERROR_CALLED_BY_NOT_CREATOR

        # Call contract_report_expiry_soon of the delegator contract
        res, app_txn = arc4.abi_call(
            DelegatorContract.contract_report_expiry_soon,
            before_expiry,
            report_period,
            app_id=del_app.id,
        )

        return res

    @arc4.abimethod()
    def gas(
        self,
    ) -> None:
        """
        To fit more resources in app reference arrays.
        """
        return

    # ----- ----- ----- ------------------ ----- ----- -----
    # ----- ----- ----- Read-only functions ----- ----- ----
    # ----- ----- ----- ------------------ ----- ----- -----
    @arc4.abimethod(readonly=True)
    def get_validator_asa(
        self,
        asset_id : UInt64,
    ) -> ValidatorASA:
        """
        Returns information about the ASA that is or was supported by the validator ad at any point of time before
        deletion.

        Returns
        -------
        asa_info : ValidatorASA
            Information about the payment asset that is or was accepted on the platform.
        """
        return self.asas[Asset(asset_id)]

    # ----- ----- ----- ------------------ ----- ----- -----
    # ----- ----- ----- Internal functions ----- ----- -----
    # ----- ----- ----- ------------------ ----- ----- -----
    @subroutine
    def _add_del_to_list(self, del_app_id: UInt64) -> bool:
        """Assign created delegator contract to first free space in the list of delegator contracts."""
        del_added = False
        for del_idx in urange(MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD):
            if self.del_app_list[del_idx] == arc4.UInt64(0):
                self.del_app_list[del_idx] = arc4.UInt64(del_app_id)
                del_added = True
                self.cnt_del += 1
                break

        return del_added

    @subroutine
    def _remove_del_from_list(self, del_app_id: UInt64) -> bool:
        """Remove the delegator contract from list of delegator contracts."""
        del_removed = False
        for del_idx in urange(MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD):
            if self.del_app_list[del_idx] == arc4.UInt64(del_app_id):
                self.del_app_list[del_idx] = arc4.UInt64(0)
                del_removed = True
                self.cnt_del -= 1
                break

        return del_removed

    @subroutine
    def _exists_del_in_list(self, del_app_id: UInt64) -> bool:
        """Checks if a delegator contract exists in validator ad's list of delegator contracts."""
        del_exists = False
        for del_idx in urange(MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD):
            if self.del_app_list[del_idx] == arc4.UInt64(del_app_id):
                del_exists = True
                break

        return del_exists

    @subroutine
    def _mark_validator_earnings(self, earnings_distribution: EarningsDistribution) -> None:
        """ Mark increase in validator's earnings. """
        asset_id = earnings_distribution.asset_id.native
        if asset_id != UInt64(ALGO_ASA_ID):
            asset = Asset(asset_id)
            self.asas[asset].total_earning = arc4.UInt64(
                self.asas[asset].total_earning.native + earnings_distribution.user.native
            )
            self.asas[asset].total_fees_generated = arc4.UInt64(
                self.asas[asset].total_fees_generated.native + earnings_distribution.platform.native
            )
        else:
            self.total_algo_earned += earnings_distribution.user.native
            self.total_algo_fees_generated += earnings_distribution.platform.native

        return
