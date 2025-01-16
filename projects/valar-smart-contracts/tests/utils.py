import base64
import dataclasses
import os
import time
from typing import Optional

from algokit_utils import (
    LogicError,
    is_localnet,
)
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import AssetTransferParams, PayParams
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    TransactionSigner,
    TransactionWithSigner,
)
from algosdk.error import AlgodHTTPError
from pytest import ExceptionInfo

from smart_contracts.artifacts.delegator_contract.client import KeyRegTxnInfo
from smart_contracts.artifacts.noticeboard.client import PartnerCommissions
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    COMMISSION_MAX,
    FROM_BASE_TO_MICRO_MULTIPLIER,
    FROM_BASE_TO_MILLI_MULTIPLIER,
    FROM_MILLI_TO_NANO_MULTIPLIER,
    ONE_IN_PPM,
    STAKE_GRATIS_MAX,
)


# ------- Functions -------
def wait_for_rounds(
    algorand_client: AlgorandClient,
    num_rounds: int,
    acc: AddressAndSigner | None = None,
) -> None:
    """
    Waits for rounds to pass.
    If on localnet, this is done by sending individual zero payment transactions.
    If on other networks, wait for more rounds to pass.

    Parameters
    ----------
    algorand_client: AlgorandClient
        Algorand client for the network connection.
    acc : AddressAndSigner
        Account with signer that is sending transactions.
    num_rounds : int
        Number of rounds to progress.

    """

    if is_localnet(algorand_client.client.algod):
        if acc is None:
            raise Exception("For progressing rounds on localnet an account is needed.")
        for _ in range(num_rounds):
            # Send the transaction
            txn = TransactionWithSigner(
                algorand_client.transactions.payment(
                    PayParams(
                        sender=acc.address,
                        receiver=acc.address,
                        amount=0,
                        extra_fee=0,
                    )
                ),
                signer=acc.signer,
            )

            atc = AtomicTransactionComposer()
            atc.add_transaction(txn)

            res = atc.execute(algorand_client.client.algod, 0)  # noqa: F841
            # print(f"Transaction sent with txID: {res.tx_ids}")
    else:
        status = algorand_client.client.algod.status()
        current_round = status["last-round"]
        while current_round + num_rounds > algorand_client.client.algod.status()["last-round"]:
            time.sleep(3)

    return

def wait_for_suspension(
    algorand_client: AlgorandClient,
    address: str,
    acc: AddressAndSigner | None = None,
) -> None:
    """
    Waits for account to be suspended from consensus.
    If on localnet, an account must be sending individual zero payment transactions.
    If on other networks, wait for more rounds to pass.

    Parameters
    ----------
    algorand_client: AlgorandClient
        Algorand client for the network connection.
    acc : AddressAndSigner
        Account with signer that is sending transactions.
    address : str
        Account to be suspended.

    """

    if is_localnet(algorand_client.client.algod):
        if acc is None:
            raise Exception("For progressing rounds on localnet an account is needed.")
        while True:
            # # Send the transaction
            # txn = TransactionWithSigner(
            #     algorand_client.transactions.payment(
            #         PayParams(
            #             sender=acc.address,
            #             receiver=acc.address,
            #             amount=0,
            #             extra_fee=0,
            #         )
            #     ),
            #     signer=acc.signer,
            # )

            # atc = AtomicTransactionComposer()
            # atc.add_transaction(txn)

            # atc.execute(algorand_client.client.algod, 0)

            # Emulate suspension by closing out the account and opening it again
            bal = balance(algorand_client, address, ALGO_ASA_ID)
            algorand_client.send.payment(
                PayParams(
                    sender=address,
                    receiver=acc.address,
                    amount=0,
                    close_remainder_to=acc.address,
                )
            )
            algorand_client.send.payment(
                PayParams(
                    sender=acc.address,
                    receiver=address,
                    amount=bal,
                )
            )

            is_tracked = is_account_tracked(algorand_client, address)
            if not is_tracked:
                break
    else:
        while is_account_tracked(algorand_client, address):
            time.sleep(3)

    return

def is_expected_logic_error(
    error_code : str,
    e : ExceptionInfo[LogicError],
) -> bool:
    return "assert // " + error_code + "\t\t<-- Error" in str(e.value)

def is_opted_in(
    algorand_client : AlgorandClient,
    address : str,
    asset_id : int,
) -> bool | None:
    if asset_id != ALGO_ASA_ID:
        opted_in = True if balance(algorand_client, address, asset_id) is not None else None
    else:
        opted_in = None

    return opted_in

def is_online(
    algorand_client: AlgorandClient,
    address: str,
) -> bool:
    online = (
        algorand_client.client.algod.account_info(
            address=address,
        )["status"]
        == "Online"
    )

    return online

@dataclasses.dataclass(kw_only=True)
class KeyRegTxnInfoPlain:
    vote_first: int | None = None
    vote_last: int | None = None
    vote_key_dilution: int | None = None
    selection_pk: str | None = None
    vote_pk: str | None = None
    state_proof_pk: str | None = None
    sender: str | None = None

    def to_key_reg_txn_info(self,
        vote_first: Optional[int] = None,
        vote_last: Optional[int] = None,
        vote_key_dilution: Optional[int] = None,
        selection_pk: Optional[str] = None,
        vote_pk: Optional[str] = None,
        state_proof_pk: Optional[str] = None,
        sender: Optional[str] = None,
    ) -> KeyRegTxnInfo:
        return KeyRegTxnInfo(
            vote_first=vote_first if vote_first is not None else self.vote_first,
            vote_last=vote_last if vote_last is not None else self.vote_last,
            vote_key_dilution=vote_key_dilution if vote_key_dilution is not None else self.vote_key_dilution,
            vote_pk=base64.b64decode(vote_pk if vote_pk is not None else self.vote_pk),
            selection_pk=base64.b64decode(selection_pk if selection_pk is not None else self.selection_pk),
            state_proof_pk=base64.b64decode(state_proof_pk if state_proof_pk is not None else self.state_proof_pk),
            sender=sender if sender is not None else self.sender,
        )

def get_account_key_reg_info(
    algorand_client: AlgorandClient,
    address: str,
) -> KeyRegTxnInfoPlain | None:
    try:
        info = algorand_client.client.algod.account_info(address=address)["participation"]
        key_reg_info = KeyRegTxnInfoPlain(
            vote_first=info["vote-first-valid"],
            vote_last=info["vote-last-valid"],
            vote_key_dilution=info["vote-key-dilution"],
            vote_pk=info["vote-participation-key"],
            selection_pk=info["selection-participation-key"],
            state_proof_pk=info["state-proof-key"],
            sender=address,
        )
    except Exception as e:
        print(e)
        key_reg_info = None

    return key_reg_info

def is_account_tracked(
    algorand_client: AlgorandClient,
    address: str,
) -> bool:
    try:
        tracked = algorand_client.client.algod.account_info(address=address)["incentive-eligible"]
    except Exception as e:
        print(e)
        tracked = False

    return tracked

def balance(
    algorand_client : AlgorandClient,
    address : str,
    asset_id : int,
) -> int | None:
    try:
        if asset_id != ALGO_ASA_ID:
            bal = algorand_client.client.algod.account_asset_info(
                address = address,
                asset_id = asset_id,
            )["asset-holding"]["amount"]
        else:
            bal = algorand_client.client.algod.account_info(
                address = address,
            )["amount"]
    except Exception as e:
        print(e)
        bal = None

    return bal

def available_balance(
    algorand_client : AlgorandClient,
    address : str,
    asset_id : int,
) -> int:
    if asset_id == ALGO_ASA_ID:
        bal = balance(algorand_client, address, asset_id)
        mbr = get_mbr(algorand_client,address)
        bal -= mbr
    else:
        frozen = is_frozen(algorand_client, address, asset_id)
        if frozen:
            bal = 0
        else:
            bal = balance(algorand_client, address, asset_id)
            bal = 0 if bal is None else bal

    return bal

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

def get_mbr(
    algorand_client : AlgorandClient,
    address : str,
) -> int:
    try:
        mbr = algorand_client.client.algod.account_info(
            address = address,
        )["min-balance"]
    except Exception as e:
        print(e)
        mbr = None

    return mbr

def is_frozen(
    algorand_client : AlgorandClient,
    address : str,
    asset_id : int,
) -> bool | None:
    try:
        if asset_id != ALGO_ASA_ID:
            frozen = algorand_client.client.algod.account_asset_info(
                address = address,
                asset_id = asset_id,
            )["asset-holding"]["is-frozen"]
        else:
            frozen = False
    except Exception as e:
        print(e)
        frozen = None

    return frozen

def is_deleted(
    algorand_client : AlgorandClient,
    app_id : int,
) -> bool | None:
    try:
        app_info = algorand_client.client.algod.application_info(app_id)  # noqa: F841
        deleted = False
    except AlgodHTTPError as e:
        if "does not exist" in str(e):
            deleted = True
        else:
            deleted = None

    return deleted

def calc_earnings(
    amount: int,
    commission: int,
) -> tuple[int, int]:
    """
    Parameters
    ----------
    amount : int
        Amount to be distributed as earnings.
    commission : int
        Platform commission.

    Returns
    -------
    user : int
        Earning of user.
    pla : int
        Earning of platform.
    """

    multiplication = amount * commission
    pla = multiplication // COMMISSION_MAX
    user = amount - pla

    return (user, pla)

def calc_operational_fee(
    fee_round: int,
    round_end: int,
    round_start: int,
) -> int:

    return (fee_round * (round_end - round_start)) // FROM_BASE_TO_MILLI_MULTIPLIER

def calc_fee_round(
    max_stake: int, # in microALGO
    fee_round_min: int, # in milli base unit per round
    fee_round_var: int, # in nano base unit per round and per 1 ALGO
) -> int:

    stake_scaled = (max_stake // FROM_BASE_TO_MICRO_MULTIPLIER)
    var = (fee_round_var * stake_scaled) // FROM_MILLI_TO_NANO_MULTIPLIER
    return max(fee_round_min, var)

def calc_fees_partner(
    partner_commissions: PartnerCommissions, # in ppm
    fee_setup: int, # in milli base unit per round
    fee_round: int, # in nano base unit per round and per 1 ALGO
) -> tuple[int, int]:

    fee_setup_partner = (fee_setup * partner_commissions.commission_setup) // ONE_IN_PPM
    fee_round_partner = (fee_round * partner_commissions.commission_operational) // ONE_IN_PPM

    return (fee_setup_partner, fee_round_partner)

def calc_stake_max(
    stake_max: int,
    stake_max_max: int,
    stake_gratis: int,
) -> int:

    stake_gratis_abs = (stake_max * stake_gratis) // STAKE_GRATIS_MAX
    stake_max_w_gratis = stake_max + stake_gratis_abs
    if stake_max_w_gratis < stake_max_max:
        stake_max_given = stake_max_w_gratis
    else:
        stake_max_given = stake_max_max

    return stake_max_given

def create_pay_fee_txn(
    algorand_client : AlgorandClient,
    asset_id : int,
    amount : int,
    sender : str,
    signer : TransactionSigner,
    receiver : str,
    extra_fee : int = 0,
) -> TransactionWithSigner:
    if asset_id == ALGO_ASA_ID:
        txn = TransactionWithSigner(
            algorand_client.transactions.payment(
                PayParams(
                    sender=sender,
                    signer=signer,
                    receiver=receiver,
                    amount=amount,
                    extra_fee=extra_fee,
                )
            ),
            signer=signer,
        )
    else:
        txn = TransactionWithSigner(
            algorand_client.transactions.asset_transfer(
                AssetTransferParams(
                    sender=sender,
                    signer=signer,
                    receiver=receiver,
                    amount=amount,
                    extra_fee=extra_fee,
                    asset_id=asset_id,
                )
            ),
            signer=signer,
        )

    return txn

def calc_box_mbr(
    box_bytes_len: int,
    box_name: bytes | None = None,
) -> int:
    """
    Calculates MBR of a box.

    Parameters
    ----------
    box_bytes_len : int
        Length of bytes of the box.
    box_name: bytes | None = None
        Optional box name as bytes, to be added to len.

    Returns
    -------
    mbr : int
        MBR for the box
    """
    if box_name is not None:
        box_name_size = len(box_name)
    else:
        box_name_size = 0

    mbr = 2_500 + 400 * (box_name_size + box_bytes_len)

    return mbr

def create_and_fund_account(
    algorand_client: AlgorandClient,
    dispenser: AddressAndSigner,
    asset_ids: list[int] | None = None,
    optin_to_assets: list[bool] | None = None,
    fund_w_assets: list[bool] | None = None,
    algo_amount: int = 100_000_000,
    asa_amount: int = 100_000_000,
) -> AddressAndSigner:
    acc = algorand_client.account.random()

    if os.getenv("STORE_GENERATED_ACCOUNTS") == "true":
        # Store account into KMD
        kmd_client = algorand_client.client.kmd
        wallets: list[dict] = kmd_client.list_wallets()

        wallet = next((w for w in wallets if w["name"] == "unencrypted-default-wallet"), None)
        if wallet is not None:
            wallet_id = wallet["id"]
            wallet_handle = kmd_client.init_wallet_handle(wallet_id, "")

            sk = acc.signer.private_key
            kmd_client.import_key(wallet_handle, sk)

    algorand_client.send.payment(
        PayParams(
            sender=dispenser.address,
            receiver=acc.address,
            amount=algo_amount,
        )
    )

    if asset_ids is not None:
        for idx, asset_id in enumerate(asset_ids):
            if optin_to_assets is not None:
                optin_to_asset = optin_to_assets[idx]
            else:
                optin_to_asset = True

            if asset_id != ALGO_ASA_ID and optin_to_asset:
                # Opt-in to ASA
                algorand_client.send.asset_transfer(
                    AssetTransferParams(
                        sender=acc.address,
                        receiver=acc.address,
                        amount=0,
                        asset_id=asset_id,
                        signer=acc.signer,
                    )
                )

                if fund_w_assets is not None:
                    fund_w_asset = fund_w_assets[idx]
                else:
                    fund_w_asset = True

                if fund_w_asset:
                    # Get some ASA
                    algorand_client.send.asset_transfer(
                        AssetTransferParams(
                            sender=dispenser.address,
                            receiver=acc.address,
                            amount=asa_amount,
                            asset_id=asset_id,
                        )
                    )

    return acc
