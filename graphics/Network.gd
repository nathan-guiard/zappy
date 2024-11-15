extends Node

signal map_ready(map: Array)
signal map_update(data: Dictionary)

var peer: StreamPeerTCP = StreamPeerTCP.new()

enum GameState {
	BIENVENUE,
	INIT_MAP,
	PLAY,
	END_GAME,
}

var game_state: GameState = GameState.BIENVENUE

var err_count: int = 0

# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	print("quouquoubebe")
	var args: PackedStringArray = OS.get_cmdline_args()
	var port: int = 4224
	print("ARGSSSSSSSSSSSS ",args)
	if args.size() > 0 and args[0].is_valid_int():
		port = int(args[0])
	if peer.connect_to_host("localhost", port) != OK:
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
	if game_state == GameState.PLAY and peer.get_status() == peer.STATUS_NONE:
		#print("status: ", peer.get_status())
		print("GAME ENDED")
		game_state = GameState.END_GAME
		var end_label: Label = %EndLabel
		end_label.visible = true
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
					var audio_music: AudioStreamPlayer = %AudioMusic
					audio_music.play()

			GameState.PLAY:
				buf += packet
				var buf_ascii: PackedByteArray = buf.to_ascii_buffer()
				var buf_04_count: int = buf_ascii.count(4)
				if buf_04_count > 0:
					var splited_buf: String = buf_ascii.slice(0, buf_ascii.find(4)).get_string_from_ascii()
					if JSON.parse_string(splited_buf) == null:
						err_count += 1
						push_error("err_count: ", err_count)
						#print()
						#print("JSON error: ", buf)
						#print()
						buf = ""
						return
					var data_parsed: Dictionary = JSON.parse_string(splited_buf)
					buf = ""
					#print("map_parsed: ", data_parsed)
					map_update.emit(data_parsed)
				
				



