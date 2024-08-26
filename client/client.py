from state import State, Idle, Recherche, Incantation
from player import Player


state: State = None


def change_state(new_state: State):
    state.exit_state()
    state = new_state
    state.enter_state()

def main():
    state = change_state(Idle())
    while(1):
        new_state: State = state.update()
        if new_state:
            change_state(new_state)