extends Node

signal map_ready(map: Array)
signal map_update(data: Dictionary)

var peer: StreamPeerTCP = StreamPeerTCP.new()

enum GameState {
	BIENVENUE,
	INIT_MAP,
	PLAY
}

var game_state: GameState = GameState.BIENVENUE



# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	print("quouquoubebe")
	if peer.connect_to_host("127.0.0.1", 4227) != OK:
		print("Pair host port, not valid")
	print("quouquoube")

#var adam_born: bool = false

var buf: String
#var map: Array

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	#if peer.get_status() == StreamPeerTCP.STATUS_CONNECTED: #and not adam_born:
		#print("CONNCTED")
		#pass
	peer.poll()
	var packet: String
	if peer.get_available_bytes() > 0:
		packet = peer.get_string(peer.get_available_bytes())
		#print("available")
		match game_state:
			GameState.BIENVENUE:
				if packet == "BIENVENUE\n":
					peer.put_data("gui\n".to_ascii_buffer())
					game_state = GameState.INIT_MAP
			GameState.INIT_MAP:
				buf += packet
				if buf and packet.to_ascii_buffer()[packet.to_ascii_buffer().size() - 1] == 4:
					var map_parsed: Array = JSON.parse_string(buf)
					buf = ""
					game_state = GameState.PLAY
					map_ready.emit(map_parsed)
					peer.put_data("ready\n".to_ascii_buffer())
			GameState.PLAY:
				buf += packet
				if buf and packet.to_ascii_buffer()[packet.to_ascii_buffer().size() - 1] == 4:
					var data_parsed: Dictionary = JSON.parse_string(buf)
					buf = ""
					#print("map_parsed: ", data_parsed)
					map_update.emit(data_parsed)
				
				



