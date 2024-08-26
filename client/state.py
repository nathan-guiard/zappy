class State:
    def enter_state(self):
        pass

    def exit_state(self):
        pass

    def update(self):
        return None

class Idle(State):
    def enter_state(self):
        print("Je suis rentre en etat IDLE")
    
    def exit_state(self):
        print("Je suis sorti de l'etat IDLE")

    def update(self) -> State:
        if ca fait 10 secondes:
            return Recherche()
        return None

class Recherche(State):
    def enter_state(self):
        print("Je suis en etat RECHERCHE")
    
    def exit_state(self):
        print("Je suis sorti de l'etat RECHERCHE")

    def update(self) -> State:
        if il a pas trouve parteneaire:
            prendre_food
            return None
        else:
            return Incantation()
        

class Incantation(State):
    def enter_state(self):
        print("Je suis en etat INCANTATION")
    
    def exit_state(self):
        pass

    def update(self) -> State:
        pass