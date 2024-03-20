import socket

HOST = 'localhost'
PORT = 8888

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))
print('Connextion vers ' + HOST + ':' + str(PORT) + ' reussie.')

def envoie_message(message):
	print('Envoi de message : ' + message)
	n = client.send(message.encode())
	if (n != len(message)):
		print('Erreur envoi.')
	else:
		print('Envoi ok.')
	print('Reception...')
	return client.recv(1024)

messages = ("", "team", "team2")
for msg in messages:
	print(envoie_message(msg))
