class Checker(object):

    def __init__(
        self, 
        client,
        targeted_states,
    ):
        """Initialize checker.

        Parameters
        ----------
        client : object
            Validator ad or delegator contract client.
        targeted_states : list
            States that should be observed in the given seequence.
        """
        self.prev_state = None
        self.targeted_states = targeted_states
        self.visited_states = []
        self.client = client
        # Log initial state
        self.update_state_log_if_state_changed()

    def update_state_log_if_state_changed(self):
        """Checks previous state agains current state and adds it to the log if there was a change.
        """
        state = self.client.get_global_state().state.as_bytes
        if state != self.prev_state:
            self.visited_states.append(state)
            self.prev_state = state

    def have_target_states_been_visited(self):
        """Checks whether the target states have been visited.

        Returns
        -------
        bool
        """
        if len(self.targeted_states) != len(self.visited_states):
            return False
        for targeted_state, visited_state in zip(self.targeted_states, self.visited_states):
            if not targeted_state == visited_state:
                return False
        return True
