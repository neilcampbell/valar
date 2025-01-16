"""Test full journeys, to check if the daemon correctly services delcos from start to finish.

Notes
-----
- Tests fail when run in a bundle, but succees when run independently.
"""
import copy
import yaml
import time
import pytest
from pathlib import Path
from typing import Dict, List, Tuple

from test.test_journey.DelcoChecker import DelcoChecker
from test.test_journey.DelcoOrchestrator import DelcoOrchestrator
from test.test_journey.NodeOrchestrator import NodeOrchestrator
from test.utils import LocalnerRoundProgressor

from valar_daemon.constants import (
    DELCO_STATE_READY,
    DELCO_STATE_SUBMITTED,
    DELCO_STATE_LIVE,
    DELCO_STATE_ENDED_NOT_CONFIRMED,
    DELCO_STATE_ENDED_EXPIRED,
    DELCO_STATE_ENDED_NOT_SUBMITTED
)


### Helpers ############################################################################################################

def load_test_configs(
    journey_templates_path: Path=None,
    parameters_path: Path=None, 
) -> List[List]:
    """Load test configs / parameters and resolve data references.

    Parameters
    ----------
    journey_templates_file : Path, optional
        Path to the journay templates, by default None
    parameters_file : Path, optional
        Path to the test parameters / config, by default None

    Returns
    -------
    List[List]
        Multiple test configs for: Delco actions, delco states, and node actions.
    """

    # Load the journey templates
    if journey_templates_path is None:
        journey_templates_path = Path(Path(__file__).parent, "journey_templates.yaml")
    with journey_templates_path.open("r") as f:
        journey_templates =  yaml.safe_load(f)

    # Load the test configurations / parameters
    if parameters_path is None:
        parameters_path = Path(Path(__file__).parent, "parameters.yaml")
    with parameters_path.open("r") as f:
        parameters = yaml.safe_load(f)

    # Resolve references to centralized data
    resolved_config_list = []
    for config in parameters:
        # Populate delco actions from templates
        delco_actions = [
            journey_templates["delco_actions"][actions_template] for actions_template in config["delco_actions"]
        ]
        # Populate delco states from templates - convert state names to their corresponding masks
        delco_states = []
        for states_template in config["delco_states"]:
            resolved_state_list = list()
            for state in journey_templates["delco_states"][states_template]:
                state_mask = eval(state) # COnvert
                resolved_state_list.append(state_mask)
            delco_states.append(resolved_state_list)
        # Populate node actions from templates
        actions_template = config["node_actions"]
        node_actions = journey_templates["node_actions"][actions_template]
        # Populate other parameters
        resolved_config_list.append([
            copy.deepcopy(delco_actions), # To avoid popping items for later tests
            copy.deepcopy(delco_states),
            copy.deepcopy(node_actions),
            config["valad_state"],
            config["timeout_s"],
            config["round_period_s"],
            config["delben_equal_delman"],
            config["algo_fee_asset"],
            # config["gating_asset_id"],
            # config["fee_asset_id"]
        ])

    return resolved_config_list


### Component definitions ##############################################################################################



### Test definitions ###################################################################################################

@pytest.mark.parametrize(
    "delco_actions, delco_states, node_actions, "
    "valad_state, timeout_s, round_period_s, delben_equal_delman, algo_fee_asset",
    # "valad_state, timeout_s, round_period_s, delben_equal_delman, gating_asset_id, fee_asset_id",
    load_test_configs()
)
def test_journey(
    algorand_client,
    delco_actions: List[List], 
    delco_states: List, 
    node_actions: List[List],
    valad_app_wrapper_and_valman,
    tmp_path,
    noticeboard,
    action_inputs,
    timeout_s,
    round_period_s,
    delben_equal_delman, gating_asset_id, fee_asset_id # Remove later
):
    
    get_round = lambda: algorand_client.client.algod.status()['last-round']
    
    valad_app, valman = valad_app_wrapper_and_valman
    print(f'Created validator ad with ID {valad_app.app_id} and state {valad_app.state}.')

    # Initialize delegator (contract) orchestrators with checkers
    delco_orc_list = []
    for actions, states in zip(delco_actions, delco_states):
        delco_orc_list.append(
            DelcoOrchestrator(
                actions=actions, 
                checker=DelcoChecker(states=states), 
                algorand_client=algorand_client,
                valad_id=valad_app.app_id,
                noticeboard=noticeboard,
                action_inputs=action_inputs
            )
        )

    # Initialize servicer
    node_orc = NodeOrchestrator(
        actions=node_actions,
        valman=valman,
        valad_id=valad_app.app_id,
        daemon_loop_period_s=3,
        config_path=tmp_path
    )

    lrp = LocalnerRoundProgressor(
        algorand_client=algorand_client,
        round_period_s=round_period_s
    )
    lrp.run()

    start_round = get_round()

    start_time = time.time() 
    while True:
        last_relative_round = get_round() - start_round
        # Refresh node orchestrators
        node_orc.refresh(last_relative_round)
        # Refresh delegator (contract) orchestrators
        [delco_orc.refresh(last_relative_round) for delco_orc in delco_orc_list]
        # Check for test completion (all foreseen delegator contract states reached)
        check_completion = [delco_orc.checker.check_completion() for delco_orc in delco_orc_list]
        if -1 in check_completion:
            print(
                [delco_orc.checker.targeted_states for delco_orc in delco_orc_list]
            )
            print(
                [delco_orc.checker.visited_states for delco_orc in delco_orc_list]
            )
            result = False
            break
        elif all(check == 0 for check in check_completion):
            result = True
            print(f'Successfull on round {get_round()}, give daemon change to recognize and log final state (e.g. ended).')
            time.sleep(node_orc.daemon.loop_period_s+1)
            break
        if time.time() - start_time > timeout_s:
            print(f'Timeout on round {get_round()}')
            result = False
            break
        else: 
            time.sleep(0.1)

    node_orc.stop_daemon_thread()
    lrp.stop()
    assert result
