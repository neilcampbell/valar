import time
import string
import random
import pytest

from algosdk.error import AlgodHTTPError

from test.utils import (
    wait_for_rounds, 
    create_and_fund_account,
    does_partkey_exist,
    get_partkey_id,
    generate_partkey,
    try_to_delete_partkey,
    delete_existing_partkeys,
    calc_sleep_time_for_partkey_generation
)

from valar_daemon.PartkeyManager import (
    PartkeyManager, 
    PartkeyBuffer,
    PARTKEY_GENERATION_REQUEST_OK_ADDED,
    PARTKEY_GENERATION_REQUEST_FAIL_IN_PENDING,
    PARTKEY_GENERATION_REQUEST_FAIL_IN_GENERATED,
    PARTKEY_GENERATION_REQUEST_FAIL_PENDING_FULL,
    PARTKEY_GENERATION_REQUEST_FAIL_GENERATED_FULL,
    PARTKEY_GENERATION_REQUEST_FAIL_ALGOD_ERROR,
    PARTKEY_GENERATION_REQUEST_FAIL_IN_THE_PAST
)



### Setup ######################################################################

def generate_random_address(length=58):
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=length))

@pytest.fixture(scope="function")
def partkey_buffer():
    return PartkeyBuffer()

@pytest.fixture(scope="function")
def partkey_manager(algorand_client, logger_mockup):
    return PartkeyManager(
        # logging.Logger('test'),
        logger_mockup,
        algorand_client
    )

@pytest.fixture(scope="function")
def dummy_partkey(algorand_client):
    last_round = algorand_client.client.algod.status()['last-round']
    class DummyPartkey:
        address = algorand_client.account.random().address
        vote_first_valid = last_round
        vote_last_valid = last_round + 1_000
        selection_participation_key = 'BDKHhKErQR8lIfF7b5LDA3vMhGgJRfLdG3NjNIxOmaU='
        state_proof_key = 'X3mlzeJFIlYvO1WcitBPYv8sGJi4IHY6NE8uTL/FPdIteBy2+YSsL8bR/riBIr7BAP5lXSickPuADfSfl8bI2g=='
        vote_participation_key = 'RbWzclQA68VlgE7mpdOPDvu4oh1mlLgQ2frZUlkz0pc='
        vote_key_dilution = 32
        scheduled_deletion = None
    return DummyPartkey


### Tests ######################################################################

class TestPartkeyBuffer:

    @staticmethod
    @pytest.mark.parametrize(
        "max_num_of_keys, num_of_keys, expected_is_full_result", 
        [
            (50, 10, False),
            (50, 49, False),
            (50, 50, True),
            (50, 51, True),
        ]
    )
    def test_is_full(
        partkey_buffer: PartkeyBuffer,
        max_num_of_keys: int,
        num_of_keys: int,
        expected_is_full_result: bool
    ):
        partkey_buffer.max_num_of_keys = max_num_of_keys
        partkey_buffer.partkeys = [i for i in range(num_of_keys)]
        assert partkey_buffer.is_full() == expected_is_full_result

    @staticmethod
    @pytest.mark.parametrize(
        "test_buffer_full", 
        [
            (False),
            (True),
        ]
    )
    def test_add_partkey_to_buffer(
        dummy_partkey: dict,
        partkey_buffer: object,
        test_buffer_full: bool
    ):
        if test_buffer_full:
            partkey_buffer.max_num_of_keys = 50
            partkey_buffer.partkeys = [i for i in range(partkey_buffer.max_num_of_keys)]
            with pytest.raises(RuntimeError):
                partkey_buffer.add_partkey_to_buffer(
                    dummy_partkey.address,
                    dummy_partkey.vote_first_valid,
                    dummy_partkey.vote_last_valid
                )
        else:
            partkey_buffer.add_partkey_to_buffer(
                dummy_partkey.address,
                dummy_partkey.vote_first_valid,
                dummy_partkey.vote_last_valid
            )
            for entry in partkey_buffer.return_partkeys():
                if entry['address'] == dummy_partkey.address:
                    assert True
                    return
            assert False

    @staticmethod
    def test_get_next(
        dummy_partkey,
        partkey_buffer
    ):
        partkey_buffer.add_partkey_to_buffer(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        res = partkey_buffer.get_next()
        assert all([
            res['address'] == dummy_partkey.address,
            res['vote-first-valid'] == dummy_partkey.vote_first_valid,
            res['vote-last-valid'] == dummy_partkey.vote_last_valid
        ])

    @staticmethod
    def test_get_next_empty(
        partkey_buffer
    ):
        assert partkey_buffer.get_next() == None

    @staticmethod
    def test_is_empty_true(
        partkey_buffer
    ):
        assert partkey_buffer.is_empty()

    @staticmethod
    def test_is_empty_false(
        dummy_partkey,
        partkey_buffer
    ):
        for i in range(3):
            partkey_buffer.add_partkey_to_buffer(
                dummy_partkey.address,
                dummy_partkey.vote_first_valid,
                dummy_partkey.vote_last_valid
            )
        assert not partkey_buffer.is_empty()

    @staticmethod
    def test_pop_partkey_from_buffer(
        dummy_partkey,
        partkey_buffer
    ):
        for i in range(3):
            partkey_buffer.add_partkey_to_buffer(
                dummy_partkey.address,
                dummy_partkey.vote_first_valid,
                dummy_partkey.vote_last_valid
            )
        assert len(partkey_buffer.partkeys) == 3
        partkey_buffer.pop_partkey_from_buffer()
        assert len(partkey_buffer.partkeys) == 2

    @staticmethod
    def test_is_partkey_in_buffer(
        dummy_partkey,
        partkey_buffer
    ):
        res = partkey_buffer.is_partkey_in_buffer(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert res == False
        partkey_buffer.add_partkey_to_buffer(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        res = partkey_buffer.is_partkey_in_buffer(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert res == True

    @staticmethod
    def test_return_partkeys(
        dummy_partkey,
        partkey_buffer
    ):
        partkey_buffer.add_partkey_to_buffer(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert partkey_buffer.return_partkeys() == partkey_buffer.partkeys



class TestPartkeyManager:

    @staticmethod
    @pytest.mark.parametrize(
        "return_target", 
        [
            (PARTKEY_GENERATION_REQUEST_OK_ADDED),
            (PARTKEY_GENERATION_REQUEST_FAIL_IN_PENDING),
            (PARTKEY_GENERATION_REQUEST_FAIL_IN_GENERATED),
            (PARTKEY_GENERATION_REQUEST_FAIL_PENDING_FULL),
            (PARTKEY_GENERATION_REQUEST_FAIL_GENERATED_FULL),
            (PARTKEY_GENERATION_REQUEST_FAIL_ALGOD_ERROR),
            (PARTKEY_GENERATION_REQUEST_FAIL_IN_THE_PAST)
        ]
    )
    def test_add_partkey_generation_request(
        algorand_client,
        partkey_manager,
        dummy_partkey,
        return_target
    ):
        
        if return_target == PARTKEY_GENERATION_REQUEST_FAIL_ALGOD_ERROR:
            partkey_manager.algorand_client.client.algod.algod_address = "https://some.cloud"
        elif return_target == PARTKEY_GENERATION_REQUEST_FAIL_IN_THE_PAST:
            last_round = algorand_client.client.algod.status()['last-round']
            delta = dummy_partkey.vote_last_valid - last_round
            dummy_partkey.vote_first_valid -= delta
            dummy_partkey.vote_last_valid -= delta
        elif return_target == PARTKEY_GENERATION_REQUEST_FAIL_IN_PENDING:
            partkey_manager.buffer_pending.add_partkey_to_buffer(
                address=dummy_partkey.address,
                vote_first_valid=dummy_partkey.vote_first_valid,
                vote_last_valid=dummy_partkey.vote_last_valid,
                vote_key_dilution=dummy_partkey.vote_key_dilution,
                scheduled_deletion=dummy_partkey.scheduled_deletion
            )
        elif return_target == PARTKEY_GENERATION_REQUEST_FAIL_IN_GENERATED:
            partkey_manager.buffer_generated.add_partkey_to_buffer(
                address=dummy_partkey.address,
                vote_first_valid=dummy_partkey.vote_first_valid,
                vote_last_valid=dummy_partkey.vote_last_valid,
                vote_key_dilution=dummy_partkey.vote_key_dilution,
                scheduled_deletion=dummy_partkey.scheduled_deletion
            )
        elif return_target == PARTKEY_GENERATION_REQUEST_FAIL_PENDING_FULL:
            partkey_manager.buffer_pending.max_num_of_keys = 50
            partkey_manager.buffer_pending.partkeys = [i for i in range(50)]
        elif return_target == PARTKEY_GENERATION_REQUEST_FAIL_GENERATED_FULL:
            partkey_manager.buffer_generated.max_num_of_keys = 50
            partkey_manager.buffer_generated.partkeys = [i for i in range(50)]
        res = partkey_manager.add_partkey_generation_request(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert res == return_target
        # for entry in partkey_manager.buffer_pending.return_partkeys():
        #     if entry['address'] == dummy_partkey.address:
        #         assert True
        #         return
        # assert False

    # @staticmethod
    # def test_add_partkey_generation_request_fail_in_pending(
    #     partkey_manager,
    #     dummy_partkey
    # ):
    #     partkey_manager.buffer_pending.add_partkey_to_buffer(
    #         dummy_partkey.address,
    #         dummy_partkey.vote_first_valid,
    #         dummy_partkey.vote_last_valid
    #     )
    #     with pytest.raises(RuntimeError):
    #         partkey_manager.add_partkey_generation_request(
    #             dummy_partkey.address,
    #             dummy_partkey.vote_first_valid,
    #             dummy_partkey.vote_last_valid
    #         )

    # @staticmethod
    # def test_add_partkey_generation_request_fail_in_generated(
    #     partkey_manager,
    #     dummy_partkey
    # ):
    #     partkey_manager.buffer_generated.add_partkey_to_buffer(
    #         dummy_partkey.address,
    #         dummy_partkey.vote_first_valid,
    #         dummy_partkey.vote_last_valid
    #     )
    #     with pytest.raises(RuntimeError):
    #         partkey_manager.add_partkey_generation_request(
    #             dummy_partkey.address,
    #             dummy_partkey.vote_first_valid,
    #             dummy_partkey.vote_last_valid
    #         )

    @staticmethod
    def test_generate_partkey(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        # Cleanup
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        # Check that keys don't already exist
        if does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        ):
            raise RuntimeError('Found existing keys associated with the addres.')
        res = partkey_manager.generate_partkey(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid,
            dummy_partkey.vote_key_dilution
        )
        assert res == 0
        # Wait for processing
        time.sleep(
            calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
        )
        assert does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        # Cleanup
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )

    @staticmethod
    def test_generate_partkey_busy(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        # Cleanup
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        res_first = partkey_manager.generate_partkey(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid + 100_000
        )
        assert res_first == 0
        res_second = partkey_manager.generate_partkey(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert res_second == 1
        # Wait for processing
        # sleep_time = calc_sleep_time_for_partkey_generation(
        #     dummy_partkey.vote_last_valid + 100_000 - dummy_partkey.vote_first_valid
        # )
        # time.sleep(sleep_time)
        time.sleep(10)
        assert does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid + 100_000
        )
        # Cleanup
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid + 100_000
        )

    @staticmethod
    def test_generate_partkey_error(
        partkey_manager,
        dummy_partkey
    ):
        with pytest.raises(AlgodHTTPError):
            partkey_manager.generate_partkey(
                dummy_partkey.address,
                dummy_partkey.vote_first_valid,
                -1
            )

    @staticmethod
    def test_get_existing_partkey_parameters(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        # Cleanup
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        res_first = partkey_manager.generate_partkey(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        # assert res_first == 0
        time.sleep(
            calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
        )
        res = partkey_manager.get_existing_partkey_parameters(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert all([
            res['address'] == dummy_partkey.address,
            res['vote-first-valid'] == dummy_partkey.vote_first_valid,
            res['vote-last-valid'] == dummy_partkey.vote_last_valid
        ])
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )

    @staticmethod
    def test_get_existing_partkey_parameters_error(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        # Cleanup
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        res = partkey_manager.get_existing_partkey_parameters(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert res is None
        # with pytest.raises(RuntimeError):
        #     partkey_manager.get_existing_partkey_parameters(
        #         dummy_partkey.address,
        #         dummy_partkey.vote_first_valid,
        #         dummy_partkey.vote_last_valid
        #     )


    # @staticmethod
    # def test_generate_next_partkey(
    #     algorand_client,
    #     partkey_manager,
    #     dummy_partkey
    # ):
    #     # Cleanup
    #     try_to_delete_partkey(
    #         algorand_client,
    #         dummy_partkey.address,
    #         dummy_partkey.vote_first_valid,
    #         dummy_partkey.vote_last_valid
    #     )
    #     partkey_manager.add_partkey_generation_request(
    #         dummy_partkey.address,
    #         dummy_partkey.vote_first_valid,
    #         dummy_partkey.vote_last_valid
    #     )
    #     partkey_manager.generate_next_partkey()
    #     time.sleep(
    #         calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
    #     )
    #     assert does_partkey_exist(
    #         algorand_client, 
    #         dummy_partkey.address,
    #         dummy_partkey.vote_first_valid,
    #         dummy_partkey.vote_last_valid
    #     )
    #     # Cleanup
    #     try_to_delete_partkey(
    #         algorand_client,
    #         dummy_partkey.address,
    #         dummy_partkey.vote_first_valid,
    #         dummy_partkey.vote_last_valid
    #     )


    @staticmethod
    def test_move_next_partkey_to_generated_buffer(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        # Cleanup
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        partkey_manager.buffer_pending.add_partkey_to_buffer(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert len(partkey_manager.buffer_pending.partkeys) == 1
        assert len(partkey_manager.buffer_generated.partkeys) == 0
        res = partkey_manager.generate_partkey(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid,
        )
        assert res == 0
        # Wait for processing
        time.sleep(
            calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
        )
        assert does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        partkey_manager.move_next_partkey_to_generated_buffer()
        assert len(partkey_manager.buffer_pending.partkeys) == 0
        assert len(partkey_manager.buffer_generated.partkeys) == 1
        # Cleanup
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )


    @staticmethod
    def test_remove_old_entries_in_buffer_generated(
        algorand_client,
        partkey_manager,
        dummy_account,
        dummy_partkey
    ):
        delta_rounds = 3
        assert partkey_manager.buffer_generated.is_empty()
        partkey_manager.buffer_generated.add_partkey_to_buffer(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_first_valid + delta_rounds
        )
        generate_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_first_valid + delta_rounds
        )
        time.sleep(1)
        partkey_manager.remove_old_entries_in_buffer_generated()
        assert not partkey_manager.buffer_generated.is_empty()
        wait_for_rounds(
            algorand_client, 
            delta_rounds + 1
        )
        assert not partkey_manager.buffer_generated.is_empty()
        partkey_manager.remove_old_entries_in_buffer_generated()
        assert partkey_manager.buffer_generated.is_empty()


    @staticmethod
    def test_fetch_and_add_existing_partkeys_to_buffer_generated(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        delete_existing_partkeys(algorand_client)
        account_list = [create_and_fund_account(algorand_client) for i in range(5)]
        for i, account in enumerate(account_list):
            generate_partkey(
                algorand_client,
                account.address,
                dummy_partkey.vote_first_valid,
                dummy_partkey.vote_last_valid
            )
            time.sleep(
                calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
            )
            if i < 2:
                partkey_manager.buffer_generated.add_partkey_to_buffer(
                    address=account.address,
                    vote_first_valid=dummy_partkey.vote_first_valid,
                    vote_last_valid=dummy_partkey.vote_last_valid
                )
        assert len(partkey_manager.buffer_generated.return_partkeys()) == 2
        partkey_manager.fetch_and_add_existing_partkeys_to_buffer_generated()
        res = algorand_client.client.algod.algod_request(
            'GET', 
            '/participation'
        )
        assert len(partkey_manager.buffer_generated.return_partkeys()) == 5
        delete_existing_partkeys(algorand_client)


    @staticmethod
    def test_fetch_and_add_existing_partkeys_to_buffer_generated_nothing_new(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        delete_existing_partkeys(algorand_client)
        account_list = [create_and_fund_account(algorand_client) for i in range(5)]
        for i, account in enumerate(account_list):
            generate_partkey(
                algorand_client,
                account.address,
                dummy_partkey.vote_first_valid,
                dummy_partkey.vote_last_valid
            )
            time.sleep(
                calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
            )
            partkey_manager.buffer_generated.add_partkey_to_buffer(
                address=account.address,
                vote_first_valid=dummy_partkey.vote_first_valid,
                vote_last_valid=dummy_partkey.vote_last_valid
            )
        assert len(partkey_manager.buffer_generated.return_partkeys()) == 5
        partkey_manager.fetch_and_add_existing_partkeys_to_buffer_generated()
        res = algorand_client.client.algod.algod_request(
            'GET', 
            '/participation'
        )
        assert len(partkey_manager.buffer_generated.return_partkeys()) == 5
        delete_existing_partkeys(algorand_client)


    @staticmethod
    def test_fetch_and_add_existing_partkeys_to_buffer_generated_no_partkeys(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        delete_existing_partkeys(algorand_client)
        assert len(partkey_manager.buffer_generated.return_partkeys()) == 0
        partkey_manager.fetch_and_add_existing_partkeys_to_buffer_generated()
        res = algorand_client.client.algod.algod_request(
            'GET', 
            '/participation'
        )
        assert len(partkey_manager.buffer_generated.return_partkeys()) == 0
        delete_existing_partkeys(algorand_client)


    @staticmethod
    def test_is_partkey_generated(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        # Cleanup
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        res = partkey_manager.is_partkey_generated(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert res == False
        res_first = partkey_manager.generate_partkey(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert res_first == 0
        time.sleep(
            calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
        )
        res = partkey_manager.is_partkey_generated(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert res == True
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )


    @staticmethod
    def test_get_partkey_id(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        generate_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        time.sleep(
            calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
        )
        exists = does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert exists == True
        generated_partkey_id = get_partkey_id(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        fetched_partkey_id = partkey_manager.get_partkey_id(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert generated_partkey_id == fetched_partkey_id


    @staticmethod
    def test_delete_partkey_using_id(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        generate_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        time.sleep(
            calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
        )
        exists = does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert exists == True
        generated_partkey_id = get_partkey_id(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        partkey_manager.delete_partkey_using_id(
            generated_partkey_id
        )
        exists = does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert exists == False


    @staticmethod
    def test_delete_partkey(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        partkey_manager.buffer_generated.add_partkey_to_buffer(
            address = dummy_partkey.address,
            vote_first_valid = dummy_partkey.vote_first_valid,
            vote_last_valid = dummy_partkey.vote_last_valid
        )
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        generate_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        time.sleep(
            calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
        )
        exists = does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert exists == True
        partkey_manager.delete_partkey(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        exists = does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert exists == False


    @staticmethod
    def test_delete_partkey_raise_not_in_buf(
        partkey_manager,
        dummy_partkey
    ):
        with pytest.raises(RuntimeError):
            partkey_manager.delete_partkey(
                dummy_partkey.address,
                dummy_partkey.vote_first_valid,
                dummy_partkey.vote_last_valid
            )        


    @staticmethod
    def test_delete_partkey_raise_not_generated(
        partkey_manager,
        dummy_partkey
    ):
        partkey_manager.buffer_generated.add_partkey_to_buffer(
            address = dummy_partkey.address,
            vote_first_valid = dummy_partkey.vote_first_valid,
            vote_last_valid = dummy_partkey.vote_last_valid
        )
        with pytest.raises(RuntimeError):
            partkey_manager.delete_partkey(
                dummy_partkey.address,
                dummy_partkey.vote_first_valid,
                dummy_partkey.vote_last_valid
            )     

        
    @staticmethod
    def test_refresh_generate(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        partkey_manager.buffer_pending.add_partkey_to_buffer(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        partkey_manager.refresh()
        time.sleep(
            calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
        )
        exists = does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert exists
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )

        
    @staticmethod
    def test_refresh_change_buffers(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        partkey_manager.buffer_pending.add_partkey_to_buffer(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        generate_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        time.sleep(
            calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
        )
        exists = does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert exists == True
        partkey_manager.busy_generating_partkey = True
        assert not partkey_manager.buffer_pending.is_empty()
        assert partkey_manager.buffer_generated.is_empty()
        partkey_manager.refresh()
        assert partkey_manager.buffer_pending.is_empty()
        assert not partkey_manager.buffer_generated.is_empty()
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )

        
    @staticmethod
    def test_refresh_remove_old(
        algorand_client,
        partkey_manager,
        dummy_account,
        dummy_partkey
    ):
        delta_rounds = 3
        assert partkey_manager.buffer_generated.is_empty()
        partkey_manager.buffer_generated.add_partkey_to_buffer(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_first_valid + delta_rounds
        )
        generate_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_first_valid + delta_rounds
        )
        time.sleep(1)
        partkey_manager.refresh()
        assert not partkey_manager.buffer_generated.is_empty()
        wait_for_rounds(
            algorand_client, 
            delta_rounds + 1
        )
        assert not partkey_manager.buffer_generated.is_empty()
        partkey_manager.refresh()
        assert partkey_manager.buffer_generated.is_empty()


    @staticmethod
    def test_delete_scheduled_partkey(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        delta_rounds = 3
        partkey_manager.buffer_generated.add_partkey_to_buffer(
            address = dummy_partkey.address,
            vote_first_valid = dummy_partkey.vote_first_valid,
            vote_last_valid = dummy_partkey.vote_last_valid,
            scheduled_deletion = dummy_partkey.vote_first_valid + delta_rounds
        )
        generate_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        time.sleep(
            calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
        )
        wait_for_rounds(
            algorand_client, 
            delta_rounds + 1
        )
        exists = does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert exists == True
        partkey_manager.delete_scheduled_partkeys()
        exists = does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert exists == False


    @staticmethod
    def test_refresh_delete_scheduled_partkey(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        delta_rounds = 3
        partkey_manager.buffer_generated.add_partkey_to_buffer(
            address = dummy_partkey.address,
            vote_first_valid = dummy_partkey.vote_first_valid,
            vote_last_valid = dummy_partkey.vote_last_valid,
            scheduled_deletion = dummy_partkey.vote_first_valid + delta_rounds
        )
        generate_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        time.sleep(
            calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
        )
        partkey_manager.refresh()
        exists = does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert exists == True
        wait_for_rounds(
            algorand_client, 
            delta_rounds + 1
        )
        partkey_manager.refresh()
        exists = does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert exists == False
