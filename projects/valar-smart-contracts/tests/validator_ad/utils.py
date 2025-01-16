import base64
import copy
import math
import os
from math import sqrt
from typing import Literal

from algokit_utils import ABITransactionResponse, TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import OnlineKeyRegParams, PayParams
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.constants import ZERO_ADDRESS

import tests.validator_ad.delegator_contract_interface as dc
from smart_contracts.artifacts.validator_ad.client import (
    KeyRegTxnInfo,
    ValidatorAdClient,
)
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    BOX_ASA_KEY_PREFIX,
    BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY,
    BOX_SIZE_PER_REF,
    INCENTIVES_ELIGIBLE_FEE,
    MBR_ACCOUNT,
    MBR_AD_TERMS,
    MBR_VALIDATOR_AD_DELEGATOR_CONTRACT_INCREASE,
)
from smart_contracts.validator_ad.constants import (
    STATE_CREATED,
    STATE_NOT_LIVE,
    STATE_NOT_READY,
    STATE_READY,
    STATE_SET,
    STATE_TEMPLATE_LOAD,
    STATE_TEMPLATE_LOADED,
)
from tests.utils import (
    available_balance,
    balance,
    calc_fee_round,
    calc_fees_partner,
    calc_operational_fee,
    create_pay_fee_txn,
    get_box,
    is_opted_in,
    wait_for_rounds,
    wait_for_suspension,
)

from .client_helper import ValidatorAdGlobalState, ValidatorASA, decode_asa_box
from .config import ActionInputs

POSSIBLE_STATES = Literal[
    "START",
    "CREATED",
    "TEMPLATE_LOAD",
    "TEMPLATE_LOADED",
    "SET",
    "READY",
    "NOT_READY",
    "NOT_LIVE",
]

EXTENDED_POSSIBLE_STATES_WITH_VIA = Literal[
    "",
]

POSSIBLE_ACTIONS = Literal[
    "ad_create",
    "ad_config",
    "ad_delete",
    "ad_ready",
    "ad_self_disclose",
    "ad_terms",
    "ad_income",
    "ad_asa_close",

    "template_load_init",
    "template_load_data",
    "template_load_end",

    "breach_limits",
    "breach_pay",
    "breach_suspended",

    "contract_claim",
    "contract_expired",
    "contract_withdraw",
    "contract_delete",
    "contract_report_expiry_soon",

    "keys_confirm",
    "keys_not_confirmed",
    "keys_not_submitted",
    "keys_submit",

    "contract_create",

    "get_validator_asa",
]

REL_PATH_TO_DELEGATOR_CONTRACT_BIN = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), \
        "../../smart_contracts/artifacts/delegator_contract/"
    )
)


class ValidatorAd:
    def __init__(
        self,
        validator_ad_client : ValidatorAdClient,
        algorand_client : AlgorandClient,
        acc : AddressAndSigner,
        del_beneficiary : AddressAndSigner,
        del_manager : AddressAndSigner,
    ):
        self.validator_ad_client = validator_ad_client
        self.algorand_client = algorand_client
        self.acc = acc
        self.del_beneficiary = del_beneficiary
        self.del_manager = del_manager

        directory = REL_PATH_TO_DELEGATOR_CONTRACT_BIN
        approval_bin_file = next(
            (os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".approval.bin")),
            ""
        )
        with open(approval_bin_file, "rb") as f:
            self.template_delegator_contract = f.read()

    def action(
        self,
        action_name : POSSIBLE_ACTIONS,
        action_inputs : ActionInputs,
    ) -> ABITransactionResponse:
        """
        Executes a particular action on the ValidatorAd instance (on its current state).
        """
        if action_name == "ad_create":
            sp = self.algorand_client.client.algod.suggested_params()

            res = self.validator_ad_client.create_ad_create(
                val_owner = action_inputs.val_owner,
                transaction_parameters=TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params = sp,
                ),
            )

        elif action_name == "ad_config":
            gs = self.get_global_state()
            val_owner = action_inputs.val_owner if action_inputs.val_owner is not None else gs.val_owner
            val_manager = action_inputs.val_manager
            live = action_inputs.live
            cnt_del_max = action_inputs.cnt_del_max

            res = self.validator_ad_client.ad_config(
                val_owner=val_owner,
                val_manager=val_manager,
                live=live,
                cnt_del_max=cnt_del_max,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                ),
            )

        elif action_name == "ad_delete":
            gs = self.get_global_state()
            val_owner = action_inputs.val_owner if action_inputs.val_owner is not None else gs.val_owner

            foreign_accounts = [val_owner]
            boxes = [(0, BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY) for _ in range(7)]

            # Prepare txn parameters
            sp = self.algorand_client.client.algod.suggested_params()
            sp.flat_fee = True
            sp.fee = 3*sp.min_fee

            res = self.validator_ad_client.delete_ad_delete(
                val_owner=val_owner,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params=sp,
                    accounts=foreign_accounts,
                    boxes=boxes,
                ),
            )

        elif action_name == "ad_ready":
            gs = self.get_global_state()
            val_manager = action_inputs.val_manager if action_inputs.val_manager is not None else gs.val_manager
            ready = action_inputs.ready

            res = self.validator_ad_client.ad_ready(
                val_manager=val_manager,
                ready=ready,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                ),
            )

        elif action_name == "ad_self_disclose":
            gs = self.get_global_state()
            val_owner = action_inputs.val_owner if action_inputs.val_owner is not None else gs.val_owner
            val_info = action_inputs.val_info

            res = self.validator_ad_client.ad_self_disclose(
                val_owner=val_owner,
                val_info=val_info,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                ),
            )

        elif action_name == "ad_terms":
            # Prepare txn parameters
            sp = self.algorand_client.client.algod.suggested_params()
            sp.flat_fee = True

            # Check if ASA ID needs to be added to validator ad
            asset = action_inputs.terms_price.fee_asset_id
            if asset != ALGO_ASA_ID:
                if self.app_asa_box(asset) is None:
                    # Set amount for MBR increase for box creation
                    amount = action_inputs.ad_terms_mbr if action_inputs.ad_terms_mbr is not None else MBR_AD_TERMS
                    # Increase fee for ASA opt-in inner txn
                    sp.fee = (2+1) * sp.min_fee
                    # Add asset to foreign assets array
                    foreign_assets = [asset]
                else:
                    amount = action_inputs.ad_terms_mbr if action_inputs.ad_terms_mbr is not None else 0
                    sp.fee = 2 * sp.min_fee
                    foreign_assets = []
                # Add the box for the new asset (to this smart contract)
                boxes = [(0, BOX_ASA_KEY_PREFIX + asset.to_bytes(8, byteorder="big"))]
            else:
                amount = action_inputs.ad_terms_mbr if action_inputs.ad_terms_mbr is not None else 0
                sp.fee = 2 * sp.min_fee
                foreign_assets = []
                boxes = []


            # Create payment transaction for (potential) ASA opt-in
            receiver = action_inputs.receiver if action_inputs.receiver is not None \
                else self.validator_ad_client.app_address
            mbr_txn = create_pay_fee_txn(
                algorand_client = self.algorand_client,
                asset_id = ALGO_ASA_ID,
                amount = amount,
                sender = self.acc.address,
                signer = self.acc.signer,
                receiver = receiver,
            )

            gs = self.get_global_state()
            val_owner = action_inputs.val_owner if action_inputs.val_owner is not None else gs.val_owner

            res = self.validator_ad_client.ad_terms(
                val_owner = val_owner,
                tc_sha256 = action_inputs.tc_sha256,
                terms_time = action_inputs.terms_time,
                terms_price = action_inputs.terms_price,
                terms_stake = action_inputs.terms_stake,
                terms_reqs = action_inputs.terms_reqs,
                terms_warn = action_inputs.terms_warn,
                txn = mbr_txn,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params = sp,
                    foreign_assets = foreign_assets,
                    boxes=boxes,
                ),
            )

        elif action_name == "ad_income":
            # Prepare txn parameters
            sp = self.algorand_client.client.algod.suggested_params()
            sp.flat_fee = True
            sp.fee = 2 * sp.min_fee

            gs = self.get_global_state()
            val_owner = action_inputs.val_owner if action_inputs.val_owner is not None else gs.val_owner
            asset_id = action_inputs.income_asset_id if \
                action_inputs.income_asset_id is not None else \
                gs.terms_price.fee_asset_id
            foreign_accounts = [val_owner]
            foreign_assets = [asset_id] if asset_id != ALGO_ASA_ID else []

            res = self.validator_ad_client.ad_income(
                val_owner=val_owner,
                asset_id=asset_id,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params=sp,
                    accounts=foreign_accounts,
                    foreign_assets=foreign_assets,
                ),
            )

        elif action_name == "ad_asa_close":
            gs = self.get_global_state()
            val_owner = action_inputs.val_owner if action_inputs.val_owner is not None else gs.val_owner
            asset = action_inputs.terms_price.fee_asset_id
            foreign_assets = [asset] if asset is not ALGO_ASA_ID else []
            boxes = [(0, BOX_ASA_KEY_PREFIX + asset.to_bytes(8, byteorder="big"))]
            foreign_accounts = [val_owner]

            # Prepare txn parameters
            sp = self.algorand_client.client.algod.suggested_params()
            sp.flat_fee = True
            sp.fee = 2 * sp.min_fee

            res = self.validator_ad_client.ad_asa_close(
                val_owner=val_owner,
                asset_id=asset,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params = sp,
                    foreign_assets = foreign_assets,
                    accounts=foreign_accounts,
                    boxes=boxes,
                ),
            )

        elif action_name == "template_load_init":
            # Fund contract with MBR for account
            amount = MBR_ACCOUNT
            self.algorand_client.send.payment(
                PayParams(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    receiver = self.validator_ad_client.app_address,
                    amount = amount,
                )
            )

            gs = self.get_global_state()
            val_owner = action_inputs.val_owner if action_inputs.val_owner is not None else gs.val_owner
            template_size = action_inputs.template_size \
                if action_inputs.template_size is not None \
                else len(self.template_delegator_contract)

            amount = action_inputs.template_box_mbr_amount if \
                action_inputs.template_box_mbr_amount is not None else \
                2_500 + 400 * (len(BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY) + template_size)
            receiver = action_inputs.template_box_mbr_receiver if \
                action_inputs.template_box_mbr_receiver is not None else \
                self.validator_ad_client.app_address
            mbr_txn = create_pay_fee_txn(
                algorand_client = self.algorand_client,
                asset_id = ALGO_ASA_ID,
                amount = amount,
                sender = self.acc.address,
                signer = self.acc.signer,
                receiver = receiver,
            )

            box_ref_num = math.ceil(template_size / BOX_SIZE_PER_REF)
            boxes = [(0, BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY) for _ in range(box_ref_num)]

            # Prepare txn parameters
            sp = self.algorand_client.client.algod.suggested_params()
            sp.flat_fee = True
            sp.fee = 2 * sp.min_fee

            res = self.validator_ad_client.template_load_init(
                val_owner=val_owner,
                template_size=template_size,
                mbr_txn=mbr_txn,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params = sp,
                    boxes=boxes,
                ),
            )

        elif action_name == "template_load_data":
            gs = self.get_global_state()
            val_owner = action_inputs.val_owner if action_inputs.val_owner is not None else gs.val_owner
            template_data_chunk = action_inputs.template_test_data_chunk \
                if action_inputs.template_test_data_chunk is not None \
                else self.template_delegator_contract
            template_data_offset = action_inputs.template_test_offset \
                if action_inputs.template_test_offset is not None \
                else 0

            data_chunk_num = math.ceil( len(template_data_chunk) / BOX_SIZE_PER_REF)
            # TO DO : Figure out why so many box references are needed
            #         even though the data is supplied only in 1024 chunks
            boxes = [(0, BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY) for _ in range(5)]

            for i in range(data_chunk_num):
                offset = i*BOX_SIZE_PER_REF + template_data_offset
                if i == data_chunk_num:
                    idx_end = len(template_data_chunk) % BOX_SIZE_PER_REF
                else:
                    idx_end = (i+1)*BOX_SIZE_PER_REF
                data = template_data_chunk[i*BOX_SIZE_PER_REF:idx_end]

                res = self.validator_ad_client.template_load_data(
                    val_owner=val_owner,
                    offset=offset,
                    data=data,
                    transaction_parameters = TransactionParameters(
                        sender = self.acc.address,
                        signer = self.acc.signer,
                        boxes=boxes,
                    ),
                )

        elif action_name == "template_load_end":
            gs = self.get_global_state()
            val_owner = action_inputs.val_owner if action_inputs.val_owner is not None else gs.val_owner

            res = self.validator_ad_client.template_load_end(
                val_owner=val_owner,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                ),
            )

        elif action_name == "contract_create":
            gs = self.get_global_state()
            val_owner = action_inputs.val_owner if action_inputs.val_owner is not None else gs.val_owner
            asset_id = gs.terms_price.fee_asset_id

            del_beneficiary = action_inputs.del_beneficiary\
                if action_inputs.del_beneficiary is not None \
                else self.del_beneficiary.address

            del_manager = action_inputs.del_manager\
                if action_inputs.del_manager is not None \
                else self.del_manager.address

            # Prepare txn parameters
            sp = self.algorand_client.client.algod.suggested_params()
            sp.flat_fee = True
            if asset_id == ALGO_ASA_ID:
                # 1 call to ValidatorAd app call,
                # 3 calls to DelegatorContract,
                # 2 inner transfers from ValidatorAd to DelegatorContract
                sp.fee = 6 * sp.min_fee
            else:
                # 1 call to ValidatorAd app call,
                # 3 calls to DelegatorContract,
                # 2 inner transfers from ValidatorAd to DelegatorContract
                # 1 inner asa opt-in on DelegatorContract
                sp.fee = 7 * sp.min_fee

            # Create payment transaction for (potential) ASA opt-in
            receiver = action_inputs.del_contract_creation_mbr_receiver if \
                action_inputs.del_contract_creation_mbr_receiver is not None else \
                self.validator_ad_client.app_address
            amount = action_inputs.del_contract_creation_mbr_amount if \
                action_inputs.del_contract_creation_mbr_amount is not None else \
                MBR_VALIDATOR_AD_DELEGATOR_CONTRACT_INCREASE
            mbr_txn = create_pay_fee_txn(
                algorand_client = self.algorand_client,
                asset_id = ALGO_ASA_ID,
                amount = amount,
                sender = self.acc.address,
                signer = self.acc.signer,
                receiver = receiver,
            )

            stake_max = action_inputs.del_stake_max if \
                action_inputs.del_stake_max is not None else \
                balance(
                    algorand_client=self.algorand_client,
                    address=self.del_beneficiary.address,
                    asset_id=ALGO_ASA_ID,
                )
            fee_round = calc_fee_round(stake_max, gs.terms_price.fee_round_min, gs.terms_price.fee_round_var)
            fee_setup = gs.terms_price.fee_setup
            rounds_duration = action_inputs.rounds_duration

            partner_address = action_inputs.partner_address
            partner_commissions = action_inputs.partner_commissions

            amount_expected = fee_setup + calc_operational_fee(fee_round, rounds_duration, 0)
            if partner_address != ZERO_ADDRESS:
                fee_setup_partner, fee_round_partner = calc_fees_partner(partner_commissions, fee_setup, fee_round)

                amount_expected += fee_setup_partner + calc_operational_fee(fee_round_partner, rounds_duration, 0)

            receiver = action_inputs.del_contract_creation_fee_receiver if \
                action_inputs.del_contract_creation_fee_receiver is not None else \
                self.validator_ad_client.app_address
            amount = action_inputs.del_contract_creation_fee_amount if \
                action_inputs.del_contract_creation_fee_amount is not None else \
                amount_expected
            txn = create_pay_fee_txn(
                algorand_client = self.algorand_client,
                asset_id = asset_id,
                amount = amount,
                sender = self.acc.address,
                signer = self.acc.signer,
                receiver = receiver,
            )

            boxes = [(0, BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY) for _ in range(8)]

            # Add assets to the foreign asset array
            foreign_assets = [asa_reg[0] for asa_reg in gs.terms_reqs.gating_asa_list if asa_reg[0] != ALGO_ASA_ID]
            if asset_id != ALGO_ASA_ID:
                foreign_assets.append(asset_id)
            foreign_accounts = [del_beneficiary]

            res = self.validator_ad_client.compose(
            ).gas(
                transaction_parameters=TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params = sp,
                    accounts=foreign_accounts,
                    foreign_assets=foreign_assets,
                ),
            ).contract_create(
                del_manager = del_manager,
                del_beneficiary = del_beneficiary,
                rounds_duration = rounds_duration,
                stake_max = stake_max,
                partner_address = partner_address,
                partner_commissions = partner_commissions,
                mbr_txn = mbr_txn,
                txn = txn,
                transaction_parameters=TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params = sp,
                    boxes=boxes,
                ),
            ).execute()

        elif action_name == "get_validator_asa":

            asset_id = action_inputs.terms_price.fee_asset_id

            # Add the box for the asset
            boxes = [(0, BOX_ASA_KEY_PREFIX + asset_id.to_bytes(8, byteorder="big"))]

            res = self.validator_ad_client.get_validator_asa(
                asset_id=asset_id,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    boxes=boxes,
                ),
            )

        return res


    def delegator_action(
        self,
        app_id : int,
        action_name : POSSIBLE_ACTIONS,
        action_inputs : ActionInputs,
    ) -> ABITransactionResponse:
        """
        Executes a particular action on the ValidatorAd instance (on its current state)
        for a particular DelegatorContract.
        """
        if action_name == "keys_confirm":
            gs_del = self.get_delegator_global_state(app_id)

            del_beneficiary = action_inputs.key_reg_sender if \
                    action_inputs.key_reg_sender is not None else \
                    gs_del.del_beneficiary

            del_manager = action_inputs.del_manager if \
                action_inputs.del_manager is not None else \
                gs_del.del_manager

            # Add a key reg transaction by delegator beneficiary
            if action_inputs.key_reg_before_confirm:
                del_beneficiary_signer = self.algorand_client.account.get_signer(del_beneficiary)

                key_reg_fee = action_inputs.key_reg_fee \
                    if action_inputs.key_reg_fee is not None \
                    else INCENTIVES_ELIGIBLE_FEE

                vote_first = action_inputs.key_reg_vote_first if \
                    action_inputs.key_reg_vote_first is not None else \
                    gs_del.round_start
                vote_last = action_inputs.key_reg_vote_last if \
                    action_inputs.key_reg_vote_last is not None else \
                    gs_del.round_end
                vote_key_dilution = action_inputs.key_reg_vote_key_dilution if \
                    action_inputs.key_reg_vote_key_dilution is not None else \
                    gs_del.vote_key_dilution

                vote_key=action_inputs.key_reg_vote if \
                    action_inputs.key_reg_vote is not None else \
                    base64.b64encode(gs_del.vote_key).decode("utf-8")
                selection_key=action_inputs.key_reg_selection if \
                    action_inputs.key_reg_selection is not None else \
                    base64.b64encode(gs_del.sel_key).decode("utf-8")
                state_proof_key=action_inputs.key_reg_state_proof if \
                    action_inputs.key_reg_state_proof is not None else \
                    base64.b64encode(gs_del.state_proof_key).decode("utf-8")

                if action_inputs.key_reg_atomically:
                    atc = AtomicTransactionComposer()
                    key_reg_txn = self.algorand_client.transactions.online_key_reg(
                        OnlineKeyRegParams(
                            vote_key=vote_key,
                            selection_key=selection_key,
                            vote_first=vote_first,
                            vote_last=vote_last,
                            vote_key_dilution=vote_key_dilution,
                            state_proof_key= state_proof_key,
                            sender = del_beneficiary,
                            static_fee = key_reg_fee,
                        )
                    )
                    key_reg_txn_w_signer = TransactionWithSigner(
                        txn = key_reg_txn,
                        signer = del_beneficiary_signer,
                    )
                    atc.add_transaction(key_reg_txn_w_signer)
                else:
                    self.algorand_client.send.online_key_reg(
                        OnlineKeyRegParams(
                            vote_key=vote_key,
                            selection_key=selection_key,
                            vote_first=vote_first,
                            vote_last=vote_last,
                            vote_key_dilution=vote_key_dilution,
                            state_proof_key= state_proof_key,
                            sender = del_beneficiary,
                            static_fee = key_reg_fee,
                            signer=del_beneficiary_signer,
                        )
                    )
            else:
                atc = None

            # Increase fee
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 3 * sp.min_fee
            sp.flat_fee = True

            if action_inputs.key_reg_atomically:
                res = self.validator_ad_client.compose(
                    atc=atc
                ).keys_confirm(
                    del_manager = del_manager,
                    del_app=app_id,
                    transaction_parameters = TransactionParameters(
                        sender = self.acc.address,
                        signer = self.acc.signer,
                        suggested_params=sp,
                        accounts = [del_beneficiary],
                    ),
                ).execute()
            else:
                res = self.validator_ad_client.keys_confirm(
                    del_manager = del_manager,
                    del_app=app_id,
                    transaction_parameters = TransactionParameters(
                        sender = self.acc.address,
                        signer = self.acc.signer,
                        suggested_params=sp,
                        accounts = [del_beneficiary],
                    ),
                )

        elif action_name == "keys_not_confirmed":
            if action_inputs.wait_until_keys_not_confirmed is True:
                # Wait until keys can be reported as not confirmed
                gs_del = self.get_delegator_global_state(app_id)
                status = self.algorand_client.client.algod.status()
                current_round = status["last-round"]
                num_rounds = \
                    gs_del.round_start + \
                    gs_del.delegation_terms_general.rounds_setup + \
                    gs_del.delegation_terms_general.rounds_confirm \
                    - current_round
                wait_for_rounds(
                    algorand_client=self.algorand_client,
                    num_rounds=num_rounds,
                    acc=self.acc,
                )

            # Increase fee for (potential) return of operational fee
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 3 * sp.min_fee
            sp.flat_fee = True
            # Add manager account to the foreign account array if it isn't the sender
            del_manager = action_inputs.del_manager if action_inputs.del_manager is not None else gs_del.del_manager
            foreign_accounts = [del_manager]
            # Add asset to the foreign asset array
            asset = action_inputs.terms_price.fee_asset_id if \
                action_inputs.terms_price.fee_asset_id is not None else \
                gs_del.delegation_terms_general.fee_asset_id
            if asset != ALGO_ASA_ID:
                foreign_assets = [asset]
            else:
                foreign_assets = None

            res = self.validator_ad_client.keys_not_confirmed(
                del_app=app_id,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params=sp,
                    accounts=foreign_accounts,
                    foreign_assets=foreign_assets,
                ),
            )

        elif action_name == "keys_not_submitted":
            gs_del = self.get_delegator_global_state(app_id)
            if action_inputs.wait_until_keys_not_submitted is True:
                # Wait until keys can be reported as not submitted
                status = self.algorand_client.client.algod.status()
                current_round = status["last-round"]
                num_rounds = \
                    gs_del.round_start + \
                    gs_del.delegation_terms_general.rounds_setup \
                    - current_round
                wait_for_rounds(
                    algorand_client=self.algorand_client,
                    num_rounds=num_rounds,
                    acc=self.acc,
                )

            # Increase fee for (potential) return of setup and operational fee
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 3 * sp.min_fee
            sp.flat_fee = True
            # Add manager account to the foreign account array if it isn't the sender
            del_manager = action_inputs.del_manager if action_inputs.del_manager is not None else gs_del.del_manager
            foreign_accounts = [del_manager]
            # Add asset to the foreign asset array
            asset = action_inputs.terms_price.fee_asset_id if \
                action_inputs.terms_price.fee_asset_id is not None else \
                gs_del.delegation_terms_general.fee_asset_id
            if asset != ALGO_ASA_ID:
                foreign_assets = [asset]
            else:
                foreign_assets = None

            res = self.validator_ad_client.keys_not_submitted(
                del_app=app_id,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params=sp,
                    accounts=foreign_accounts,
                    foreign_assets=foreign_assets,
                ),
            )

        elif action_name == "keys_submit":
            gs_del = self.get_delegator_global_state(app_id)
            vote_first = action_inputs.key_reg_vote_first if \
                action_inputs.key_reg_vote_first is not None else \
                gs_del.round_start
            vote_last = action_inputs.key_reg_vote_last if \
                action_inputs.key_reg_vote_last is not None else \
                gs_del.round_end
            vote_key_dilution = action_inputs.key_reg_vote_key_dilution if \
                action_inputs.key_reg_vote_key_dilution is not None else \
                round(sqrt(gs_del.round_end-gs_del.round_start))
            key_sender = action_inputs.key_reg_sender if \
                action_inputs.key_reg_sender is not None else \
                gs_del.del_beneficiary

            gs_val = self.get_global_state()
            val_manager = action_inputs.val_manager if action_inputs.val_manager is not None else gs_val.val_manager

            # Increase fee for (potential) distribution of earnings
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 4 * sp.min_fee
            sp.flat_fee = True
            # Add asset to the foreign asset array and box array
            asset = action_inputs.terms_price.fee_asset_id
            if asset != ALGO_ASA_ID:
                foreign_assets = [asset]
                boxes = boxes = [(0, BOX_ASA_KEY_PREFIX + asset.to_bytes(8, byteorder="big"))]
            else:
                foreign_assets = None
                boxes = None

            res = self.validator_ad_client.keys_submit(
                val_manager=val_manager,
                del_app=app_id,
                key_reg_txn_info = KeyRegTxnInfo(
                    vote_first=vote_first,
                    vote_last=vote_last,
                    vote_key_dilution=vote_key_dilution,
                    vote_pk=base64.b64decode(action_inputs.key_reg_vote),
                    selection_pk=base64.b64decode(action_inputs.key_reg_selection),
                    state_proof_pk=base64.b64decode(action_inputs.key_reg_state_proof),
                    sender=key_sender,
                ),
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params=sp,
                    foreign_assets=foreign_assets,
                    boxes=boxes,
                ),
            )

        elif action_name == "breach_limits":
            gs_del = self.get_delegator_global_state(app_id)
            if action_inputs.wait_until_limit_breach is True:
                # Wait until next limit breach
                status = self.algorand_client.client.algod.status()
                current_round = status["last-round"]
                num_rounds = \
                    gs_del.round_breach_last + \
                    gs_del.delegation_terms_balance.rounds_breach \
                    - current_round
                wait_for_rounds(
                    algorand_client=self.algorand_client,
                    num_rounds=num_rounds,
                    acc=self.acc,
                )

            # Increase fee for (potential) distribution of earnings and note sending
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 6 * sp.min_fee
            sp.flat_fee = True
            # Add assets to the foreign asset array
            foreign_assets = [asa_reg[0] for asa_reg in gs_del.delegation_terms_balance.gating_asa_list if asa_reg[0] != ALGO_ASA_ID]  # noqa: E501
            if gs_del.delegation_terms_general.fee_asset_id != ALGO_ASA_ID:
                foreign_assets.append(gs_del.delegation_terms_general.fee_asset_id)

            asset = action_inputs.terms_price.fee_asset_id
            if asset == ALGO_ASA_ID:
                boxes = []
            else:
                boxes = [(0, BOX_ASA_KEY_PREFIX + asset.to_bytes(8, byteorder="big"))]

            # Add beneficiary account and manager account to the foreign account array
            foreign_accounts = [gs_del.del_beneficiary, gs_del.del_manager]

            res = self.validator_ad_client.breach_limits(
                del_app=app_id,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params=sp,
                    foreign_assets=foreign_assets,
                    accounts=foreign_accounts,
                    boxes=boxes,
                ),
            )

        elif action_name == "breach_pay":
            # Increase fee for (potential) distribution of earnings
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 4 * sp.min_fee
            sp.flat_fee = True
            # Add asset to the foreign asset array and box array
            asset = action_inputs.terms_price.fee_asset_id
            if asset != ALGO_ASA_ID:
                foreign_assets = [asset]
                boxes = boxes = [(0, BOX_ASA_KEY_PREFIX + asset.to_bytes(8, byteorder="big"))]
            else:
                foreign_assets = None
                boxes = None

            res = self.validator_ad_client.breach_pay(
                del_app=app_id,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params=sp,
                    foreign_assets=foreign_assets,
                    boxes=boxes,
                ),
            )

        elif action_name == "breach_suspended":
            gs_del = self.get_delegator_global_state(app_id)

            if action_inputs.wait_until_suspended:
                wait_for_suspension(self.algorand_client, gs_del.del_beneficiary, self.acc)

           # Increase fee for (potential) distribution of earnings
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 4 * sp.min_fee
            sp.flat_fee = True
            # Add asset to the foreign asset array and box array
            asset = action_inputs.terms_price.fee_asset_id
            if asset != ALGO_ASA_ID:
                foreign_assets = [asset]
                boxes = boxes = [(0, BOX_ASA_KEY_PREFIX + asset.to_bytes(8, byteorder="big"))]
            else:
                foreign_assets = None
                boxes = None
            foreign_accounts = [gs_del.delegation_terms_general.partner_address, gs_del.del_beneficiary]

            res = self.validator_ad_client.breach_suspended(
                del_app=app_id,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params=sp,
                    foreign_assets=foreign_assets,
                    accounts=foreign_accounts,
                    boxes=boxes,
                ),
            )

        elif action_name == "contract_claim":
            # Increase fee for (potential) distribution of earnings
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 4 * sp.min_fee
            sp.flat_fee = True
            # Add asset to the foreign asset array and box array
            asset = action_inputs.terms_price.fee_asset_id
            if asset != ALGO_ASA_ID:
                foreign_assets = [asset]
                boxes = boxes = [(0, BOX_ASA_KEY_PREFIX + asset.to_bytes(8, byteorder="big"))]
            else:
                foreign_assets = None
                boxes = None

            res = self.validator_ad_client.contract_claim(
                del_app=app_id,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params=sp,
                    foreign_assets=foreign_assets,
                    boxes=boxes,
                ),
            )

        elif action_name == "contract_expired":
            if action_inputs.wait_until_expired is True:
                # Wait until contract expires
                gs_del = self.get_delegator_global_state(app_id)
                status = self.algorand_client.client.algod.status()
                current_round = status["last-round"]
                num_rounds = (gs_del.round_end-1) - current_round
                wait_for_rounds(
                    algorand_client=self.algorand_client,
                    num_rounds=num_rounds,
                    acc=self.acc,
                )

            # Increase fee for (potential) distribution of earnings
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 4 * sp.min_fee
            sp.flat_fee = True
            # Add asset to the foreign asset array and box array
            asset = action_inputs.terms_price.fee_asset_id
            if asset != ALGO_ASA_ID:
                foreign_assets = [asset]
                boxes = boxes = [(0, BOX_ASA_KEY_PREFIX + asset.to_bytes(8, byteorder="big"))]
            else:
                foreign_assets = None
                boxes = None

            res = self.validator_ad_client.contract_expired(
                del_app=app_id,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params=sp,
                    foreign_assets=foreign_assets,
                    boxes=boxes,
                ),
            )

        elif action_name == "contract_withdraw":
            gs_del = self.get_delegator_global_state(app_id)

            del_manager = action_inputs.del_manager\
                if action_inputs.del_manager is not None \
                else self.del_manager.address

            # Increase fee for (potential) distribution of earnings
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 4 * sp.min_fee
            sp.flat_fee = True
            # Add asset to the foreign asset array and box array
            asset = action_inputs.terms_price.fee_asset_id
            if asset != ALGO_ASA_ID:
                foreign_assets = [asset]
                boxes = boxes = [(0, BOX_ASA_KEY_PREFIX + asset.to_bytes(8, byteorder="big"))]
            else:
                foreign_assets = None
                boxes = None

            res = self.validator_ad_client.contract_withdraw(
                del_manager=del_manager,
                del_app=app_id,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params=sp,
                    foreign_assets=foreign_assets,
                    boxes=boxes,
                ),
            )

        elif action_name == "contract_delete":

            # Increase fee for distribution of any remaining balances and return of MBR
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 5 * sp.min_fee
            sp.flat_fee = True
            # Add asset to the foreign asset array
            if action_inputs.terms_price.fee_asset_id != ALGO_ASA_ID:
                foreign_assets = [action_inputs.terms_price.fee_asset_id]
            else:
                foreign_assets = None

            del_manager = action_inputs.del_manager\
                if action_inputs.del_manager is not None \
                else self.del_manager.address

            # Add manager account to the foreign account array if it isn't the sender
            foreign_accounts = [del_manager]

            res = self.validator_ad_client.contract_delete(
                del_manager=del_manager,
                del_app=app_id,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params=sp,
                    foreign_assets=foreign_assets,
                    accounts = foreign_accounts,
                ),
            )

        elif action_name == "contract_report_expiry_soon":
            gs_del = self.get_delegator_global_state(app_id)

            before_expiry=action_inputs.before_expiry
            report_period=action_inputs.report_period
            if action_inputs.wait_expiry_report is True:
                # Wait until it can be reported that contract will expire soon
                status = self.algorand_client.client.algod.status()
                current_round = status["last-round"]
                num_rounds_1st = gs_del.round_end - current_round - before_expiry
                num_rounds_other = gs_del.round_expiry_soon_last + report_period - current_round
                num_rounds = num_rounds_other \
                    if gs_del.round_expiry_soon_last != 0 \
                    else num_rounds_1st
                wait_for_rounds(
                    algorand_client=self.algorand_client,
                    num_rounds=num_rounds,
                    acc=self.acc,
                )

            # Increase fee for forwarding the call to delegator contract
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 2 * sp.min_fee
            sp.flat_fee = True

            res = self.validator_ad_client.contract_report_expiry_soon(
                before_expiry=before_expiry,
                report_period=report_period,
                del_app=app_id,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params=sp,
                ),
            )

        else:
            raise ValueError(f"Invalid action name {action_name}")

        return res

    def get_global_state(self) -> ValidatorAdGlobalState:
        if self.validator_ad_client.app_id == 0:
            return None
        else:
            return ValidatorAdGlobalState.from_global_state(self.validator_ad_client.get_global_state())

    def get_state(self) -> POSSIBLE_STATES:
        gs = self.get_global_state()
        if gs is None:
            state = "START"

        else:
            state_enc = gs.state

            if state_enc == STATE_CREATED:
                state = "CREATED"
            elif state_enc == STATE_TEMPLATE_LOAD:
                state = "TEMPLATE_LOAD"
            elif state_enc == STATE_TEMPLATE_LOADED:
                state = "TEMPLATE_LOADED"
            elif state_enc == STATE_SET:
                state = "SET"
            elif state_enc == STATE_READY:
                state = "READY"
            elif state_enc == STATE_NOT_READY:
                state = "NOT_READY"
            elif state_enc == STATE_NOT_LIVE:
                state = "NOT_LIVE"
            else:
                raise ValueError(f"Unknown state: {state_enc}")

        return state

    def initialize_state(
        self,
        target_state : POSSIBLE_STATES | EXTENDED_POSSIBLE_STATES_WITH_VIA,
        action_inputs : ActionInputs,
        current_state : POSSIBLE_STATES | None = None,
    ):
        """
        Moves a ValidatorAd instance from its current state to the target_state,
        while applying action_inputs to the actions that lead to that state.
        """

        if current_state is None:
            _current_state = self.get_state()
        else:
            _current_state = current_state

        if target_state == "START":
            return

        # Transition to the target state step by step
        path_to_state = self.get_path_to_state(
            target_state=target_state,
            current_state=_current_state,
        )

        for action_name in path_to_state:
            if action_name == "ad_config_live":
                action_inputs_passed = copy.deepcopy(action_inputs)
                action_inputs_passed.live = True
                action_name_passed = "ad_config"
            elif action_name == "ad_config_not_live":
                action_inputs_passed = copy.deepcopy(action_inputs)
                action_inputs_passed.live = False
                action_name_passed = "ad_config"
            elif action_name == "ad_ready_ready":
                action_inputs_passed = copy.deepcopy(action_inputs)
                action_inputs_passed.ready = True
                action_name_passed = "ad_ready"
            else:
                action_inputs_passed = action_inputs
                action_name_passed = action_name
            self.action(action_name_passed, action_inputs_passed)

    def get_path_to_state(
        self,
        target_state : POSSIBLE_STATES | EXTENDED_POSSIBLE_STATES_WITH_VIA,
        current_state : POSSIBLE_STATES | None = None,
    ) -> list[str]:
        """
        Returns a list of actions that transition from the start to the target state.
        """
        to_start = []
        to_created = [*to_start, "ad_create"]
        to_template_load = [*to_created, "template_load_init"]
        to_template_loaded = [*to_template_load, "template_load_data", "template_load_end"]
        to_set = [*to_template_loaded, "ad_terms"]
        to_not_ready = [*to_set, "ad_config_live"]
        to_not_live = [*to_set, "ad_config_not_live"]
        to_ready = [*to_not_ready, "ad_ready_ready"]

        state_transitions = {
            "START": to_start,
            "CREATED": to_created,
            "TEMPLATE_LOAD": to_template_load,
            "TEMPLATE_LOADED": to_template_loaded,
            "SET": to_set,
            "READY": to_ready,
            "NOT_READY": to_not_ready,
            "NOT_LIVE": to_not_live,
        }

        if target_state not in state_transitions:
            raise ValueError(f"Unknown target state: {target_state}")

        if current_state is not None:
            path = [item for item in state_transitions[target_state] if item not in state_transitions[current_state]]
        else:
            path = state_transitions[target_state]

        return path

    def get_delegator_global_state(self, app_id: int) -> dc.DelegatorContractGlobalState | None:
        if app_id == 0:
            res = None
        else:
            try:
                delegator_contract = dc.DelegatorContract(
                    delegator_contract_client=dc.DelegatorContractClient(
                        algod_client=self.algorand_client.client.algod,
                        app_id=app_id,
                    ),
                    algorand_client=self.algorand_client,
                    acc = self.acc, # Can be any account
                    del_beneficiary = self.acc, # Can be any account
                    del_manager = self.acc, # Can be any account
                )
                res = delegator_contract.get_global_state()
            except Exception:
                res = None
        return res

    def get_delegator_state(self, app_id: int) -> dc.POSSIBLE_STATES:
        gs = self.get_delegator_global_state(app_id)
        if gs is None:
            state = "START"

        else:
            state_enc = gs.state

            if state_enc == dc.STATE_ENDED_CANNOT_PAY:
                state = "ENDED_CANNOT_PAY"
            elif state_enc == dc.STATE_ENDED_EXPIRED:
                state = "ENDED_EXPIRED"
            elif state_enc == dc.STATE_ENDED_LIMITS:
                state = "ENDED_LIMITS"
            elif state_enc == dc.STATE_ENDED_NOT_CONFIRMED:
                state = "ENDED_NOT_CONFIRMED"
            elif state_enc == dc.STATE_ENDED_NOT_SUBMITTED:
                state = "ENDED_NOT_SUBMITTED"
            elif state_enc == dc.STATE_ENDED_SUSPENDED:
                state = "ENDED_SUSPENDED"
            elif state_enc == dc.STATE_ENDED_WITHDREW:
                state = "ENDED_WITHDREW"
            elif state_enc == dc.STATE_LIVE:
                state = "LIVE"
            elif state_enc == dc.STATE_READY:
                state = "READY"
            elif state_enc == dc.STATE_SUBMITTED:
                state = "SUBMITTED"
            else:
                raise ValueError(f"Unknown state: {state_enc}")

        return state

    def initialize_delegator_state(
        self,
        action_inputs : ActionInputs,
        app_id : int = 0,
        target_state : dc.POSSIBLE_STATES | dc.EXTENDED_POSSIBLE_STATES_WITH_VIA = "READY",
        current_state : dc.POSSIBLE_STATES | None = None,
    ) -> int:
        """
        Moves a DelegatorContract that is part of ValidatorAd from its current state to the target_state,
        while applying action_inputs to the actions that lead to that state.
        """

        if app_id != 0:
            if current_state is None:
                _current_state = self.get_delegator_state()
            else:
                _current_state = current_state
        else:
            _current_state = "START"

        if target_state == "START":
            return

        # Transition to the target state step by step
        path_to_state = self.get_delegator_path_to_state(
            target_state=target_state,
            current_state=_current_state,
        )

        application_id = app_id
        for action_name in path_to_state:
            if action_name == "contract_create":
                res = self.action(action_name, action_inputs)
                application_id = res.abi_results[-1].return_value
            else:
                self.delegator_action(
                    app_id=application_id,
                    action_name=action_name,
                    action_inputs=action_inputs,
                )

        return application_id

    def get_delegator_path_to_state(
        self,
        target_state : dc.POSSIBLE_STATES | dc.EXTENDED_POSSIBLE_STATES_WITH_VIA,
        current_state : dc.POSSIBLE_STATES | None = None,
    ) -> list[str]:
        """
        Returns a list of actions that transition DelegatorContract from the start to the target state.
        """
        to_start = []
        to_ready = [*to_start, "contract_create"]
        to_submitted = [*to_ready, "keys_submit"]
        to_live = [*to_submitted, "keys_confirm"]

        state_transitions = {
            "START": to_start,
            "READY": to_ready,
            "SUBMITTED": to_submitted,
            "LIVE": to_live,
            "ENDED_NOT_SUBMITTED": [*to_ready, "keys_not_submitted"],
            "ENDED_NOT_CONFIRMED": [*to_submitted, "keys_not_confirmed"],
            "ENDED_LIMITS": [*to_live, "breach_limits"],
            "ENDED_WITHDREW": [*to_live, "contract_withdraw"],
            "ENDED_EXPIRED": [*to_live, "contract_expired"],
            "ENDED_SUSPENDED": [*to_live, "breach_suspended"],
            "ENDED_CANNOT_PAY_VIA_READY": [*to_ready, "breach_pay"],
            "ENDED_CANNOT_PAY_VIA_LIVE": [*to_live, "breach_pay"],
        }

        if target_state not in state_transitions:
            raise ValueError(f"Unknown target state: {target_state}")

        if current_state is not None:
            path = [item for item in state_transitions[target_state] if item not in state_transitions[current_state]]
        else:
            path = state_transitions[target_state]

        return path

    def app_is_opted_in(
        self,
        asset_id : int,
    ) -> bool | None:
        return is_opted_in(
            algorand_client=self.algorand_client,
            address=self.validator_ad_client.app_address,
            asset_id=asset_id,
        )

    def app_balance(
        self,
        asset_id : int,
    ) -> bool | None:
        return balance(
            algorand_client=self.algorand_client,
            address=self.validator_ad_client.app_address,
            asset_id=asset_id,
        )

    def app_available_balance(
        self,
        asset_id : int,
    ) -> int:
        return available_balance(
            algorand_client=self.algorand_client,
            address=self.validator_ad_client.app_address,
            asset_id=asset_id,
        )

    def app_box(
        self,
        box_name : bytes,
    ) -> tuple[bytes, bool]:
        return get_box(
            algorand_client=self.algorand_client,
            box_name=box_name,
            app_id=self.validator_ad_client.app_id,
        )

    def app_asa_box(
        self,
        asa_id : int,
    ) -> ValidatorASA | None:
        if asa_id == ALGO_ASA_ID:
            raise ValueError("ALGO is not a box on ValidatorAd.")

        box_name = BOX_ASA_KEY_PREFIX + asa_id.to_bytes(8, byteorder="big")

        box_contents_raw, box_exists = self.app_box(box_name)

        if box_exists:
            box_contents = decode_asa_box(box_contents_raw)
        else:
            box_contents = None

        return box_contents
