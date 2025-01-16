
import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import AssetCreateParams, AssetTransferParams, PayParams
from algokit_utils.config import config

from smart_contracts.artifacts.validator_ad.client import ValidatorAdClient
from smart_contracts.helpers.constants import ALGO_ASA_ID
from tests.conftest import TestConsts
from tests.validator_ad.utils import ValidatorAd


@pytest.fixture(scope="package", params=[ALGO_ASA_ID, "asa"])
def asset(request : pytest.FixtureRequest, asa : int) -> int:
    if request.param == "asa":
        return asa
    else:
        return request.param

@pytest.fixture(scope="package")
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

@pytest.fixture(scope="package")
def asa_2(algorand_client: AlgorandClient) -> int:
    _dispenser = algorand_client.account.dispenser()
    # Dispenser creates a 2nd ASA to be used during the tests
    res = algorand_client.send.asset_create(
        AssetCreateParams(
            sender=_dispenser.address,
            total = 11_402_000_000,
            decimals = 8,
            default_frozen = False,
            manager = _dispenser.address,
            reserve = _dispenser.address,
            freeze = _dispenser.address,
            clawback = _dispenser.address,
            unit_name = "T1",
            asset_name = "TEST_TOKEN_1",
        )
    )

    asa_id = res["confirmation"]["asset-index"]

    return asa_id

@pytest.fixture(scope="module")
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
def val_manager(
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
def val_owner(
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
def validator_ad_client(
    algorand_client: AlgorandClient,
    creator: AddressAndSigner,
) -> ValidatorAdClient:
    """
    Create a new ValidatorAd client.

    Parameters
    ----------
    algorand_client : AlgorandClient

    creator : AddressAndSigner

    Returns
    -------
    validator_ad_client : ValidatorAdClient
        Validator ad app client.
    """

    config.configure(
        debug=True,
        # trace_all=True,
    )

    validator_ad_client = ValidatorAdClient(
        algorand_client.client.algod,
        creator=creator.address,
        signer=creator.signer,
        indexer_client=algorand_client.client.indexer,
    )

    return validator_ad_client

@pytest.fixture(scope="function")
def validator_ad(
    validator_ad_client: ValidatorAdClient,
    algorand_client : AlgorandClient,
    creator : AddressAndSigner,
    del_beneficiary : AddressAndSigner,
    del_manager : AddressAndSigner,
) -> ValidatorAd:

    return ValidatorAd(
        validator_ad_client=validator_ad_client,
        algorand_client=algorand_client,
        acc=creator,
        del_beneficiary=del_beneficiary,
        del_manager=del_manager,
    )

@pytest.fixture(scope="function")
def validator_ad_client_2(
    algorand_client: AlgorandClient,
    creator: AddressAndSigner,
) -> ValidatorAdClient:
    """
    Create a new ValidatorAd client.

    Parameters
    ----------
    algorand_client : AlgorandClient

    creator : AddressAndSigner

    Returns
    -------
    validator_ad_client : ValidatorAdClient
        Validator ad app client.
    """

    config.configure(
        debug=True,
        # trace_all=True,
    )

    validator_ad_client = ValidatorAdClient(
        algorand_client.client.algod,
        creator=creator.address,
        signer=creator.signer,
        indexer_client=algorand_client.client.indexer,
    )

    return validator_ad_client

@pytest.fixture(scope="function")
def validator_ad_2(
    validator_ad_client_2: ValidatorAdClient,
    algorand_client : AlgorandClient,
    creator : AddressAndSigner,
    del_beneficiary : AddressAndSigner,
    del_manager : AddressAndSigner,
) -> ValidatorAd:

    return ValidatorAd(
        validator_ad_client=validator_ad_client_2,
        algorand_client=algorand_client,
        acc=creator,
        del_beneficiary=del_beneficiary,
        del_manager=del_manager,
    )


