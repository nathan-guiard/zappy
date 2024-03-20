import socket
import time
from client_lib import Player

HOST = 'localhost'
PORT = int(input("Port: "))

ret = [
	{"p":{"x":0,"y":0},"c":[]},
	{"p":{"x":64,"y":34},"c":[{"Food":5}]},
	{"p":{"x":0,"y":34},"c":[{"Food":3}]},
	{"p":{"x":1,"y":34},"c":[{"Food":1}]}]

def server_connexion():
	client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	while True:
		try:
			client.connect((HOST, PORT))
		except ConnectionRefusedError:
			print("Connexion error")
			continue
		break
	print('Connexion vers ' + HOST + ':' + str(PORT) + ' reussie.')
	client.send("".encode())
	client.recv(1024)
	return client


def team_connexion(client: socket):
	while True:
		team_name = input("Team name: ")
		n = client.send((team_name + '\n').encode())
		if n != len(team_name + '\n'):
			print('Erreur envoi.')
		# print('Reception...')
		start_player =  client.recv(1024)
		if start_player.decode() == "This team does not exist\n":
			print(f"Team name '{team_name}' is unknow\n")
			continue
		return start_player

if __name__ == "__main__":
	client = server_connexion()
	start_player = team_connexion(client)
	player = Player(client, start_player.decode())
