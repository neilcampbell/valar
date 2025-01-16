import time
import threading
import dataclasses
from typing import List

from algokit_utils.beta.algorand_client import AlgorandClient

from valar_daemon.DelegatorContractClient import DelegatorContractClient
from valar_daemon.utils import DELCO_STATE_SUBMITTED


@dataclasses.dataclass(kw_only=True)
class DelegatorAction:
    round: int = 0
    handler: object = None
    args: tuple = dataclasses.field(default_factory=tuple)
    kwargs: dict = dataclasses.field(default_factory=dict)

    def invoke(self):
        if self.handler:
            return self.handler(*self.args, **self.kwargs)
            # return self.handler(**self.kwargs)


class DelegatorOrchestrator(object):
    """
    Issue given delegator-side action.
    Key confirmation (async) and delco creation (spawns client) are separate actions.
    """

    def __init__(
        self,
        algorand_client: AlgorandClient,
        action_list: List[DelegatorAction],
        delco_creation_action: DelegatorAction=None,
        delco_client: DelegatorContractClient=None,
        auto_confirm_keys: bool=False,
        delco_confirm_keys_action: DelegatorAction=None
    ):
        self.algorand_client = algorand_client
        self.delco_creation_action = delco_creation_action
        self.delco_client = delco_client
        self.auto_confirm_keys = auto_confirm_keys
        self.delco_confirm_keys_action = delco_confirm_keys_action
        self.action_list = action_list
        self.run_flag = True
        self.keys_exist = False
        self.delco_id = None

    def _run(self):
        while self.run_flag:
            # Nothing left to do
            if not self.are_more_actions_pending() and self.delco_client is not None:
                if not self.auto_confirm_keys or (self.auto_confirm_keys and self.keys_exist):
                    self.run_flag = False
            # Delco has to be created
            if self.delco_client is None:
                # Create delco on specific round
                if self._get_round() >= self.delco_creation_action.round:
                    # Create delco - needs 3 block rounds
                    delco_id = self.delco_creation_action.invoke()
                    self.delco_client = DelegatorContractClient(
                        self.algorand_client.client.algod,
                        app_id=delco_id
                    )
                    self.delco_id = delco_id
                    # Update app_id for all action
                    for action in self.action_list:
                        if 'app_id' in action.kwargs.keys():
                            action.kwargs['app_id'] = delco_id
            else:
                # Grab state and confirm keys if applicable
                state = self.delco_client.get_global_state().state.as_bytes
                if state == DELCO_STATE_SUBMITTED and self.auto_confirm_keys:
                    self.delco_confirm_keys_action.kwargs['app_id'] = self.delco_id
                    self.delco_confirm_keys_action.invoke() # Takes 1 round
                    self.keys_exist = True
                # Execute actions
                action = self.pool_for_next_action()
                if action is not None:
                    action.invoke()         
                time.sleep(0.1)

    def _get_round(self):
        return self.algorand_client.client.algod.status()["last-round"]

    def pool_for_next_action(
        self
    ):
        current_round = self._get_round()
        for idx, action in enumerate(self.action_list):
            if action.round <= current_round:
                return self.action_list.pop(idx)
        return None
        
    def are_more_actions_pending(
        self
    ):
        if len(self.action_list) > 0:
            return True
        else:
            return False

    def stop(self):
        self.run_flag = False
        self.thread.join()

    def run(self):
        self.thread = threading.Thread(
            target=self._run
        )
        self.thread.start()
