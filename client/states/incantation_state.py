from states.state import Idle

class IncantationState:
    def __init__(self, player):
        self.player = player

    def enter_state(self):
        pass

    def update(self):
        pass

    def exit_state(self):
        pass

class Idle(IncantationState):
    def enter_state(self):
        print("Player is idle, waiting to start an incantation.")

    def update(self):
        # Logic to transition to ProposeIncantation state
        if self.player.ready_for_incantation():
            return ProposeIncantation(self.player)

    def exit_state(self):
        print("Exiting Idle state.")

class ProposeIncantation(IncantationState):
    def enter_state(self):
        print("Proposing an incantation to other players.")
        self.player.propose_incantation()

    def update(self):
        # Transition to AwaitResponse after proposing
        return AwaitResponse(self.player)

    def exit_state(self):
        print("Exiting ProposeIncantation state.")

class AwaitResponse(IncantationState):
    def enter_state(self):
        print("Waiting for other players to respond.")

    def update(self):
        # Logic to check responses and transition to next state
        if self.player.responses_received():
            if self.player.all_responses_positive():
                return PrepareResources(self.player)
            else:
                return IncantationFailure(self.player)

    def exit_state(self):
        print("Exiting AwaitResponse state.")

class PrepareResources(IncantationState):
    def enter_state(self):
        print("Preparing resources for incantation.")

    def update(self):
        # Logic to prepare resources
        if self.player.resources_ready():
            return ReadyToIncant(self.player)

    def exit_state(self):
        print("Exiting PrepareResources state.")

class ReadyToIncant(IncantationState):
    def enter_state(self):
        print("All players are ready to start incantation.")

    def update(self):
        # Transition to Incanting state
        return Incanting(self.player)

    def exit_state(self):
        print("Exiting ReadyToIncant state.")


class Incanting(IncantationState):
    def enter_state(self):
        print("Starting the incantation process.")
        self.player.start_incantation()

    def update(self):
        # Logic to check if incantation is successful
        if self.player.incantation_successful():
            return IncantationSuccess(self.player)
        else:
            return IncantationFailure(self.player)

    def exit_state(self):
        print("Exiting Incanting state.")

class IncantationSuccess(IncantationState):
    def enter_state(self):
        print("Incantation succeeded! Level up.")
        self.player.level_up()

    def update(self):
        # Transition back to Idle after success
        return Idle(self.player)

    def exit_state(self):
        print("Exiting IncantationSuccess state.")

class IncantationFailure(IncantationState):
    def enter_state(self):
        print("Incantation failed.")

    def update(self):
        # Transition back to Idle after failure
        return Idle(self.player)

    def exit_state(self):
        print("Exiting IncantationFailure state.")
