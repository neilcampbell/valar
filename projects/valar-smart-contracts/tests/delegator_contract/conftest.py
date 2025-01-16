
import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import AssetTransferParams, PayParams
from algokit_utils.config import config

from smart_contracts.artifacts.delegator_contract.client import DelegatorContractClient
from smart_contracts.helpers.constants import ALGO_ASA_ID
from tests.conftest import TestConsts
from tests.delegator_contract.utils import DelegatorContract


@pytest.fixture(scope="package", params=[ALGO_ASA_ID, "asa"])
def asset(request : pytest.FixtureRequest, asa : int) -> int:
    if request.param == "asa":
        return asa
    else:
        return request.param

@pytest.fixture(scope="function")
def creator(
    algorand_client: AlgorandClient,
    dispenser: AddressAndSigner,
    asset : int,
) -> AddressAndSigner:
    acc = algorand_client.account.random()
    algorand_client.send.payment(
        PayParams(
            sender=dispenser.address,
            receiver=acc.address,
            amount=TestConsts.acc_dispenser_amt,
        )
    )

    if asset != ALGO_ASA_ID:
        # Opt-in to ASA
        algorand_client.send.asset_transfer(
            AssetTransferParams(
                sender=acc.address,
                receiver=acc.address,
                amount=0,
                asset_id=asset,
                signer=acc.signer,
            )
        )

        # Get some ASA
        algorand_client.send.asset_transfer(
            AssetTransferParams(
                sender=dispenser.address,
                receiver=acc.address,
                amount=TestConsts.acc_dispenser_asa_amt,
                asset_id=asset,
            )
        )

    return acc

@pytest.fixture(scope="function")
def del_manager(
    algorand_client: AlgorandClient,
    dispenser: AddressAndSigner,
    asset : int,
) -> AddressAndSigner:
    acc = algorand_client.account.random()
    algorand_client.send.payment(
        PayParams(
            sender=dispenser.address,
            receiver=acc.address,
            amount=TestConsts.acc_dispenser_amt,
        )
    )

    if asset != ALGO_ASA_ID:
        # Opt-in to ASA
        algorand_client.send.asset_transfer(
            AssetTransferParams(
                sender=acc.address,
                receiver=acc.address,
                amount=0,
                asset_id=asset,
                signer=acc.signer,
            )
        )

        # Get some ASA
        algorand_client.send.asset_transfer(
            AssetTransferParams(
                sender=dispenser.address,
                receiver=acc.address,
                amount=TestConsts.acc_dispenser_asa_amt,
                asset_id=asset,
            )
        )

    return acc

@pytest.fixture(scope="function")
def del_beneficiary(
    algorand_client: AlgorandClient,
    dispenser: AddressAndSigner,
    asset : int,
) -> AddressAndSigner:
    acc = algorand_client.account.random()
    algorand_client.send.payment(
        PayParams(
            sender=dispenser.address,
            receiver=acc.address,
            amount=TestConsts.acc_dispenser_amt,
        )
    )

    if asset != ALGO_ASA_ID:
        # Opt-in to ASA
        algorand_client.send.asset_transfer(
            AssetTransferParams(
                sender=acc.address,
                receiver=acc.address,
                amount=0,
                asset_id=asset,
                signer=acc.signer,
            )
        )

        # Get some ASA
        algorand_client.send.asset_transfer(
            AssetTransferParams(
                sender=dispenser.address,
                receiver=acc.address,
                amount=TestConsts.acc_dispenser_asa_amt,
                asset_id=asset,
            )
        )

    return acc

@pytest.fixture(scope="module")
def partner(
    algorand_client: AlgorandClient,
    dispenser: AddressAndSigner,
    asset : int,
) -> AddressAndSigner:
    acc = algorand_client.account.random()
    algorand_client.send.payment(
        PayParams(
            sender=dispenser.address,
            receiver=acc.address,
            amount=TestConsts.acc_dispenser_amt,
        )
    )

    if asset != ALGO_ASA_ID:
        # Opt-in to ASA
        algorand_client.send.asset_transfer(
            AssetTransferParams(
                sender=acc.address,
                receiver=acc.address,
                amount=0,
                asset_id=asset,
                signer=acc.signer,
            )
        )

        # Get some ASA
        algorand_client.send.asset_transfer(
            AssetTransferParams(
                sender=dispenser.address,
                receiver=acc.address,
                amount=TestConsts.acc_dispenser_asa_amt,
                asset_id=asset,
            )
        )

    return acc

@pytest.fixture(scope="function")
def delegator_contract_client(
    algorand_client: AlgorandClient,
    creator: AddressAndSigner,
) -> DelegatorContractClient:
    """
    Create a new DelegatorContract client.

    Parameters
    ----------
    algorand_client : AlgorandClient

    creator : AddressAndSigner

    Returns
    -------
    delegator_contract_client : DelegatorContractClient
        Delegator contract app client.
    """

    config.configure(
        debug=True,
        # trace_all=True,
    )

    delegator_contract_client = DelegatorContractClient(
        algorand_client.client.algod,
        creator=creator.address,
        signer=creator.signer,
        indexer_client=algorand_client.client.indexer,
    )

    return delegator_contract_client

@pytest.fixture(scope="function")
def delegator_contract(
    delegator_contract_client: DelegatorContractClient,
    algorand_client : AlgorandClient,
    creator : AddressAndSigner,
    del_beneficiary : AddressAndSigner,
    del_manager : AddressAndSigner,
) -> DelegatorContract:

    return DelegatorContract(
        delegator_contract_client=delegator_contract_client,
        algorand_client=algorand_client,
        acc=creator,
        del_beneficiary=del_beneficiary,
        del_manager=del_manager,
    )

