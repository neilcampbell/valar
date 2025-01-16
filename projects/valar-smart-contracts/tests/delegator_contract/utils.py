import base64
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

from smart_contracts.artifacts.delegator_contract.client import DelegatorContractClient, KeyRegTxnInfo
from smart_contracts.delegator_contract.constants import (
    STATE_CREATED,
    STATE_ENDED_CANNOT_PAY,
    STATE_ENDED_EXPIRED,
    STATE_ENDED_LIMITS,
    STATE_ENDED_NOT_CONFIRMED,
    STATE_ENDED_NOT_SUBMITTED,
    STATE_ENDED_SUSPENDED,
    STATE_ENDED_WITHDREW,
    STATE_LIVE,
    STATE_READY,
    STATE_SET,
    STATE_SUBMITTED,
)
from smart_contracts.helpers.constants import ALGO_ASA_ID, INCENTIVES_ELIGIBLE_FEE, MBR_ACCOUNT, MBR_ASA
from tests.utils import (
    available_balance,
    balance,
    create_pay_fee_txn,
    is_opted_in,
    wait_for_rounds,
    wait_for_suspension,
)

from .client_helper import DelegatorContractGlobalState
from .config import ActionInputs

POSSIBLE_STATES = Literal[
    "START",
    "CREATED",
    "SET",
    "READY",
    "SUBMITTED",
    "ENDED_CANNOT_PAY",
    "ENDED_EXPIRED",
    "ENDED_LIMITS",
    "ENDED_NOT_CONFIRMED",
    "ENDED_NOT_SUBMITTED",
    "ENDED_SUSPENDED",
    "ENDED_WITHDREW",
    "LIVE",
]

EXTENDED_POSSIBLE_STATES_WITH_VIA = Literal[
    "ENDED_CANNOT_PAY_VIA_READY",
    "ENDED_CANNOT_PAY_VIA_SUBMITTED",
    "ENDED_CANNOT_PAY_VIA_LIVE",
]

POSSIBLE_ACTIONS = Literal[
    "contract_create",
    "contract_setup",
    "contract_pay",
    "keys_confirm",
    "keys_not_confirmed",
    "keys_not_submitted",
    "keys_submit",
    "breach_limits",
    "breach_pay",
    "breach_suspended",
    "contract_claim",
    "contract_expired",
    "contract_withdraw",
    "contract_delete",
    "contract_report_expiry_soon",
]

class DelegatorContract:
    def __init__(
        self,
        delegator_contract_client : DelegatorContractClient,
        algorand_client : AlgorandClient,
        acc : AddressAndSigner,
        del_beneficiary: AddressAndSigner,
        del_manager : AddressAndSigner,
    ):
        self.delegator_contract_client = delegator_contract_client
        self.algorand_client = algorand_client
        self.acc = acc
        self.del_beneficiary = del_beneficiary
        self.del_manager = del_manager

    def action(
        self,
        action_name : POSSIBLE_ACTIONS,
        action_inputs : ActionInputs,
    ) -> ABITransactionResponse:
        """
        Executes a particular action on the DelegatorContract instance (on its current state).
        """
        if action_name == "contract_create":
            sp = self.algorand_client.client.algod.suggested_params()

            del_beneficiary = action_inputs.del_beneficiary\
                if action_inputs.del_beneficiary is not None \
                else self.del_beneficiary.address

            del_manager = action_inputs.del_manager\
                if action_inputs.del_manager is not None \
                else self.del_manager.address

            res = self.delegator_contract_client.create_contract_create(
                del_manager = del_manager,
                del_beneficiary = del_beneficiary,
                noticeboard_app_id = action_inputs.noticeboard_app_id,
                transaction_parameters=TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params = sp,
                ),
            )

        elif action_name == "contract_setup":
            # Fund contract with MBR for account and (potential) ASA opt-in
            if action_inputs.delegation_terms_general.fee_asset_id == ALGO_ASA_ID:
                amount = MBR_ACCOUNT
            else:
                amount = MBR_ACCOUNT + MBR_ASA
            receiver = action_inputs.receiver if action_inputs.receiver is not None \
                else self.delegator_contract_client.app_address
            self.algorand_client.send.payment(
                PayParams(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    receiver = receiver,
                    amount = amount,
                )
            )

            tc_sha256 = action_inputs.tc_sha256

            # Increase fee for (potential) ASA opt-in inner txn
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 2 * sp.min_fee
            sp.flat_fee = True

            # Check if ASA ID needs to be added to foreign assets array
            asset = action_inputs.delegation_terms_general.fee_asset_id
            foreign_assets = [asset] if asset != ALGO_ASA_ID else None

            res = self.delegator_contract_client.contract_setup(
                tc_sha256 = tc_sha256,
                delegation_terms_general = action_inputs.delegation_terms_general,
                delegation_terms_balance = action_inputs.delegation_terms_balance,
                rounds_duration = action_inputs.rounds_duration,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params = sp,
                    foreign_assets = foreign_assets,
                ),
            )

        elif action_name == "contract_pay":
            gs = self.get_global_state()
            receiver = action_inputs.receiver if action_inputs.receiver is not None \
                else self.delegator_contract_client.app_address
            # Create fee payment transaction
            amount = action_inputs.amount \
                if action_inputs.amount is not None \
                else (
                    gs.delegation_terms_general.fee_setup + \
                    gs.delegation_terms_general.fee_setup_partner + \
                    gs.fee_operational + \
                    gs.fee_operational_partner
                )

            pay_fee_txn = create_pay_fee_txn(
                algorand_client = self.algorand_client,
                asset_id = action_inputs.delegation_terms_general.fee_asset_id,
                amount = amount,
                sender = self.acc.address,
                signer = self.acc.signer,
                receiver = receiver,
            )

            # Add assets to the foreign asset array
            foreign_assets = [asa_reg[0] for asa_reg in gs.delegation_terms_balance.gating_asa_list if asa_reg[0] != ALGO_ASA_ID]  # noqa: E501
            if action_inputs.delegation_terms_general.fee_asset_id != ALGO_ASA_ID:
                foreign_assets.append(action_inputs.delegation_terms_general.fee_asset_id)
            foreign_accounts = [gs.del_beneficiary]

            res = self.delegator_contract_client.contract_pay(
                txn = pay_fee_txn,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    foreign_assets = foreign_assets,
                    accounts=foreign_accounts,
                ),
            )

        elif action_name == "keys_confirm":
            gs = self.get_global_state()
            del_manager = action_inputs.del_manager if action_inputs.del_manager is not None else gs.del_manager

            del_beneficiary = action_inputs.key_reg_sender if \
                    action_inputs.key_reg_sender is not None else \
                    gs.del_beneficiary

            # Add a key reg transaction by delegator beneficiary
            if action_inputs.key_reg_before_confirm:
                del_beneficiary_signer = self.algorand_client.account.get_signer(del_beneficiary)

                key_reg_fee = action_inputs.key_reg_fee \
                    if action_inputs.key_reg_fee is not None \
                    else INCENTIVES_ELIGIBLE_FEE

                vote_first = action_inputs.key_reg_vote_first if \
                    action_inputs.key_reg_vote_first is not None else \
                    gs.round_start
                vote_last = action_inputs.key_reg_vote_last if \
                    action_inputs.key_reg_vote_last is not None else \
                    gs.round_end
                vote_key_dilution = action_inputs.key_reg_vote_key_dilution if \
                    action_inputs.key_reg_vote_key_dilution is not None else \
                    gs.vote_key_dilution

                vote_key=action_inputs.key_reg_vote if \
                    action_inputs.key_reg_vote is not None else \
                    base64.b64encode(gs.vote_key).decode("utf-8")
                selection_key=action_inputs.key_reg_selection if \
                    action_inputs.key_reg_selection is not None else \
                    base64.b64encode(gs.sel_key).decode("utf-8")
                state_proof_key=action_inputs.key_reg_state_proof if \
                    action_inputs.key_reg_state_proof is not None else \
                    base64.b64encode(gs.state_proof_key).decode("utf-8")

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


            if action_inputs.key_reg_atomically:
                res = self.delegator_contract_client.compose(
                    atc=atc
                ).keys_confirm(
                    del_manager = del_manager,
                    transaction_parameters = TransactionParameters(
                        sender = self.acc.address,
                        signer = self.acc.signer,
                        accounts = [del_beneficiary]
                    ),
                ).execute()
            else:
                res = self.delegator_contract_client.keys_confirm(
                    del_manager = del_manager,
                    transaction_parameters = TransactionParameters(
                        sender = self.acc.address,
                        signer = self.acc.signer,
                        accounts = [del_beneficiary]
                    ),
                )

        elif action_name == "keys_not_confirmed":
            gs = self.get_global_state()
            del_manager = action_inputs.del_manager if action_inputs.del_manager is not None else gs.del_manager

            if action_inputs.wait_until_keys_not_confirmed is True:
                # Wait until keys can be reported as not confirmed
                gs_start = self.get_global_state()
                status = self.algorand_client.client.algod.status()
                current_round = status["last-round"]
                num_rounds = \
                    gs_start.round_start + \
                    gs_start.delegation_terms_general.rounds_setup + \
                    gs_start.delegation_terms_general.rounds_confirm \
                    - current_round
                wait_for_rounds(
                    algorand_client=self.algorand_client,
                    num_rounds=num_rounds,
                    acc=self.acc,
                )

            # Increase fee for (potential) return of operational fee
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 2 * sp.min_fee
            sp.flat_fee = True
            # Add manager account to the foreign account array if it isn't the sender
            foreign_accounts = [del_manager]
            # Add asset to the foreign asset array
            if action_inputs.delegation_terms_general.fee_asset_id != ALGO_ASA_ID:
                foreign_assets = [action_inputs.delegation_terms_general.fee_asset_id]
            else:
                foreign_assets = None

            res = self.delegator_contract_client.keys_not_confirmed(
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params=sp,
                    accounts=foreign_accounts,
                    foreign_assets=foreign_assets,
                ),
            )

        elif action_name == "keys_not_submitted":
            gs = self.get_global_state()
            del_manager = action_inputs.del_manager if action_inputs.del_manager is not None else gs.del_manager

            if action_inputs.wait_until_keys_not_submitted is True:
                # Wait until keys can be reported as not submitted
                gs_start = self.get_global_state()
                status = self.algorand_client.client.algod.status()
                current_round = status["last-round"]
                num_rounds = \
                    gs_start.round_start + \
                    gs_start.delegation_terms_general.rounds_setup \
                    - current_round
                wait_for_rounds(
                    algorand_client=self.algorand_client,
                    num_rounds=num_rounds,
                    acc=self.acc,
                )

            # Increase fee for (potential) return of setup and operational fee
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 2 * sp.min_fee
            sp.flat_fee = True
            # Add manager account to the foreign account array if it isn't the sender
            foreign_accounts = [del_manager]
            # Add asset to the foreign asset array
            if action_inputs.delegation_terms_general.fee_asset_id != ALGO_ASA_ID:
                foreign_assets = [action_inputs.delegation_terms_general.fee_asset_id]
            else:
                foreign_assets = None

            res = self.delegator_contract_client.keys_not_submitted(
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params=sp,
                    accounts=foreign_accounts,
                    foreign_assets=foreign_assets,
                ),
            )

        elif action_name == "keys_submit":
            gs = self.get_global_state()
            vote_first = action_inputs.key_reg_vote_first if \
                action_inputs.key_reg_vote_first is not None else gs.round_start
            vote_last = action_inputs.key_reg_vote_last if \
                action_inputs.key_reg_vote_last is not None else gs.round_end
            vote_key_dilution = action_inputs.key_reg_vote_key_dilution if \
                action_inputs.key_reg_vote_key_dilution is not None else round(sqrt(gs.round_end-gs.round_start))
            key_sender = action_inputs.key_reg_sender if \
                action_inputs.key_reg_sender is not None else gs.del_beneficiary

            # Increase fee for (potential) distribution of earnings
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 4 * sp.min_fee
            sp.flat_fee = True
            # Add asset to the foreign asset array
            if action_inputs.delegation_terms_general.fee_asset_id != ALGO_ASA_ID:
                foreign_assets = [action_inputs.delegation_terms_general.fee_asset_id]
            else:
                foreign_assets = None
            foreign_accounts = [action_inputs.delegation_terms_general.partner_address]

            res = self.delegator_contract_client.keys_submit(
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
                    accounts=foreign_accounts,
                ),
            )

        elif action_name == "breach_limits":
            gs = self.get_global_state()

            if action_inputs.wait_until_limit_breach is True:
                # Wait until next limit breach
                gs_start = self.get_global_state()
                status = self.algorand_client.client.algod.status()
                current_round = status["last-round"]
                num_rounds = \
                    gs_start.round_breach_last + \
                    gs_start.delegation_terms_balance.rounds_breach \
                    - current_round
                wait_for_rounds(
                    algorand_client=self.algorand_client,
                    num_rounds=num_rounds,
                    acc=self.acc,
                )

            # Increase fee for (potential) distribution of earnings and note sending
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 5 * sp.min_fee
            sp.flat_fee = True
            # Add assets to the foreign asset array
            foreign_assets = [asa_reg[0] for asa_reg in gs.delegation_terms_balance.gating_asa_list if asa_reg[0] != ALGO_ASA_ID]  # noqa: E501
            if action_inputs.delegation_terms_general.fee_asset_id != ALGO_ASA_ID:
                foreign_assets.append(action_inputs.delegation_terms_general.fee_asset_id)
            # Add beneficiary account and manager account to the foreign account array
            foreign_accounts = [
                gs.del_beneficiary,
                gs.del_manager,
                gs.delegation_terms_general.partner_address,
            ]

            res = self.delegator_contract_client.breach_limits(
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params=sp,
                    foreign_assets=foreign_assets,
                    accounts=foreign_accounts,
                ),
            )

        elif action_name == "breach_pay":
            # Increase fee for (potential) distribution of earnings
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 4 * sp.min_fee
            sp.flat_fee = True
            # Add asset to the foreign asset array
            if action_inputs.delegation_terms_general.fee_asset_id != ALGO_ASA_ID:
                foreign_assets = [action_inputs.delegation_terms_general.fee_asset_id]
            else:
                foreign_assets = None
            foreign_accounts = [action_inputs.delegation_terms_general.partner_address]

            res = self.delegator_contract_client.breach_pay(
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params=sp,
                    foreign_assets=foreign_assets,
                    accounts=foreign_accounts,
                ),
            )

        elif action_name == "breach_suspended":
            gs = self.get_global_state()

            if action_inputs.wait_until_suspended:
                wait_for_suspension(self.algorand_client, gs.del_beneficiary, self.acc)

            # Increase fee for (potential) distribution of earnings
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 4 * sp.min_fee
            sp.flat_fee = True
            # Add asset to the foreign asset array
            if action_inputs.delegation_terms_general.fee_asset_id != ALGO_ASA_ID:
                foreign_assets = [action_inputs.delegation_terms_general.fee_asset_id]
            else:
                foreign_assets = None
            foreign_accounts = [action_inputs.delegation_terms_general.partner_address, gs.del_beneficiary]

            res = self.delegator_contract_client.breach_suspended(
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params=sp,
                    foreign_assets=foreign_assets,
                    accounts=foreign_accounts,
                ),
            )

        elif action_name == "contract_claim":
            # Increase fee for (potential) distribution of earnings
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 4 * sp.min_fee
            sp.flat_fee = True
            # Add asset to the foreign asset array
            if action_inputs.delegation_terms_general.fee_asset_id != ALGO_ASA_ID:
                foreign_assets = [action_inputs.delegation_terms_general.fee_asset_id]
            else:
                foreign_assets = None
            foreign_accounts = [action_inputs.delegation_terms_general.partner_address]

            res = self.delegator_contract_client.contract_claim(
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params=sp,
                    foreign_assets=foreign_assets,
                    accounts=foreign_accounts,
                ),
            )

        elif action_name == "contract_expired":
            if action_inputs.wait_until_expired is True:
                # Wait until contract expires
                gs_start = self.get_global_state()
                status = self.algorand_client.client.algod.status()
                current_round = status["last-round"]
                num_rounds = (gs_start.round_end-1) - current_round
                wait_for_rounds(
                    algorand_client=self.algorand_client,
                    num_rounds=num_rounds,
                    acc=self.acc,
                )

            # Increase fee for (potential) distribution of earnings
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 4 * sp.min_fee
            sp.flat_fee = True
            # Add asset to the foreign asset array
            if action_inputs.delegation_terms_general.fee_asset_id != ALGO_ASA_ID:
                foreign_assets = [action_inputs.delegation_terms_general.fee_asset_id]
            else:
                foreign_assets = None
            foreign_accounts = [action_inputs.delegation_terms_general.partner_address]

            res = self.delegator_contract_client.contract_expired(
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params=sp,
                    foreign_assets=foreign_assets,
                    accounts=foreign_accounts,
                ),
            )

        elif action_name == "contract_withdraw":
            gs = self.get_global_state()
            del_manager = action_inputs.del_manager if action_inputs.del_manager is not None else gs.del_manager

            # Increase fee for (potential) distribution of earnings
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 4 * sp.min_fee
            sp.flat_fee = True
            # Add asset to the foreign asset array
            if action_inputs.delegation_terms_general.fee_asset_id != ALGO_ASA_ID:
                foreign_assets = [action_inputs.delegation_terms_general.fee_asset_id]
            else:
                foreign_assets = None
            foreign_accounts = [action_inputs.delegation_terms_general.partner_address]

            res = self.delegator_contract_client.contract_withdraw(
                del_manager=del_manager,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params=sp,
                    foreign_assets=foreign_assets,
                    accounts=foreign_accounts,
                ),
            )

        elif action_name == "contract_delete":
            gs = self.get_global_state()
            del_manager = action_inputs.del_manager if action_inputs.del_manager is not None else gs.del_manager

            # Increase fee for distribution any remaining balances
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 3 * sp.min_fee
            sp.flat_fee = True
            # Add asset to the foreign asset array
            if action_inputs.delegation_terms_general.fee_asset_id != ALGO_ASA_ID:
                foreign_assets = [action_inputs.delegation_terms_general.fee_asset_id]
            else:
                foreign_assets = None

            # Add manager account to the foreign account array if it isn't the sender
            foreign_accounts = [del_manager]

            res = self.delegator_contract_client.delete_contract_delete(
                del_manager=del_manager,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                    suggested_params=sp,
                    foreign_assets=foreign_assets,
                    accounts = foreign_accounts,
                ),
            )

        elif action_name == "contract_report_expiry_soon":
            before_expiry=action_inputs.before_expiry
            report_period=action_inputs.report_period
            if action_inputs.wait_expiry_report is True:
                # Wait until it can be reported that contract will expire soon
                gs = self.get_global_state()
                status = self.algorand_client.client.algod.status()
                current_round = status["last-round"]
                num_rounds_1st = gs.round_end - current_round - before_expiry
                num_rounds_other = gs.round_expiry_soon_last + report_period - current_round
                num_rounds = num_rounds_other \
                    if gs.round_expiry_soon_last != 0 \
                    else num_rounds_1st
                wait_for_rounds(
                    algorand_client=self.algorand_client,
                    num_rounds=num_rounds,
                    acc=self.acc,
                )

            res = self.delegator_contract_client.contract_report_expiry_soon(
                before_expiry=before_expiry,
                report_period=report_period,
                transaction_parameters = TransactionParameters(
                    sender = self.acc.address,
                    signer = self.acc.signer,
                ),
            )

        else:
            raise ValueError(f"Invalid action name {action_name}")

        return res

    def get_global_state(self) -> DelegatorContractGlobalState:
        if self.delegator_contract_client.app_id == 0:
            return None
        else:
            return DelegatorContractGlobalState.from_global_state(self.delegator_contract_client.get_global_state())

    def get_state(self) -> POSSIBLE_STATES:
        gs = self.get_global_state()
        if gs is None:
            state = "START"

        else:
            state_enc = gs.state

            if state_enc == STATE_CREATED:
                state = "CREATED"
            elif state_enc == STATE_ENDED_CANNOT_PAY:
                state = "ENDED_CANNOT_PAY"
            elif state_enc == STATE_ENDED_EXPIRED:
                state = "ENDED_EXPIRED"
            elif state_enc == STATE_ENDED_LIMITS:
                state = "ENDED_LIMITS"
            elif state_enc == STATE_ENDED_NOT_CONFIRMED:
                state = "ENDED_NOT_CONFIRMED"
            elif state_enc == STATE_ENDED_NOT_SUBMITTED:
                state = "ENDED_NOT_SUBMITTED"
            elif state_enc == STATE_ENDED_SUSPENDED:
                state = "ENDED_SUSPENDED"
            elif state_enc == STATE_ENDED_WITHDREW:
                state = "ENDED_WITHDREW"
            elif state_enc == STATE_LIVE:
                state = "LIVE"
            elif state_enc == STATE_READY:
                state = "READY"
            elif state_enc == STATE_SET:
                state = "SET"
            elif state_enc == STATE_SUBMITTED:
                state = "SUBMITTED"
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
        Moves a DelegatorContract instance from its current state to the target_state,
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
            self.action(action_name, action_inputs)

    def get_path_to_state(
        self,
        target_state : POSSIBLE_STATES | EXTENDED_POSSIBLE_STATES_WITH_VIA,
        current_state : POSSIBLE_STATES | None = None,
    ) -> list[str]:
        """
        Returns a list of actions that transition from the start to the target state.
        """
        to_start = []
        to_created = [*to_start, "contract_create"]
        to_set = [*to_created, "contract_setup"]
        to_ready = [*to_set, "contract_pay"]
        to_submitted = [*to_ready, "keys_submit"]
        to_live = [*to_submitted, "keys_confirm"]

        state_transitions = {
            "START": to_start,
            "CREATED": to_created,
            "SET": to_set,
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
            "ENDED_CANNOT_PAY_VIA_SUBMITTED": [*to_submitted, "breach_pay"],
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
            address=self.delegator_contract_client.app_address,
            asset_id=asset_id,
        )

    def app_balance(
        self,
        asset_id : int,
    ) -> bool | None:
        return balance(
            algorand_client=self.algorand_client,
            address=self.delegator_contract_client.app_address,
            asset_id=asset_id,
        )

    def app_available_balance(
        self,
        asset_id : int,
    ) -> int:
        return available_balance(
            algorand_client=self.algorand_client,
            address=self.delegator_contract_client.app_address,
            asset_id=asset_id,
        )
