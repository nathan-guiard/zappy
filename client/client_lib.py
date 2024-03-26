import socket

resource = ["linemate", "deraumere", "sibur", "mendiane", "phiras", "thystame"]

levels = {1: {"linemate": 1},
        2: {"linemate": 1, "deraumere": 1, "sibur": 1},
        3: {"linemate": 2, "sibur": 1, "phiras": 2},
        4: {"linemate": 1, "deraumere": 1, "sibur": 2, "phiras": 1},
        5: {"linemate": 1, "deraumere": 2, "sibur": 1, "mendiane": 3},
        6: {"linemate": 1, "deraumere": 2, "sibur": 3, "phiras": 1},
        7: {"linemate": 2, "deraumere": 2, "sibur": 2, "mendiane": 2, "phiras": 2, "thystame": 1},
}

DEAD = "You died\n"

class Player:

	def __init__(self, client: socket, start_player) -> None:
		self.client = client
		start_player = start_player.split('\n')
		coord = tuple(start_player[1].split())
		print(coord)
		self.map=[]
		print(start_player)
		self.routine()
		print(self.envoie_message("voir"))

	def envoie_message(self, message):
		message += '\n'
		# print('Envoi de message :' , message.encode())
		n = self.client.send((message).encode())
		if n != len(message):
			print('Erreur envoi.')
		# print('Reception...')
		return self.client.recv(1024).decode()
	
	def routine(self):
		while True:
			retour_command = self.envoie_message("voir")
			print(retour_command)
			if retour_command == DEAD:
				print("Je suis dead")
				exit() 
 
 
 
 
 
 