extends Camera2D

# Called when the node enters the scene tree for the first time.

var desired_zoom: Vector2 = Vector2(1, 1)

func _process(delta: float) -> void:
	zoom = lerp(zoom, desired_zoom, 0.1)
	if zoom.x < 0.1:
		zoom = Vector2(0.1, 0.1)
	if zoom.y < 0.1:
		zoom = Vector2(0.1, 0.1)

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var mouse_event: InputEventMouseButton = event
		if mouse_event.button_index == MOUSE_BUTTON_WHEEL_UP:
			print("Zoom in")
			desired_zoom = zoom * 1.2
		elif mouse_event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			print("Zoom out")
			desired_zoom = zoom * 0.8
		elif mouse_event.button_index == MOUSE_BUTTON_LEFT:
			global_position = get_global_mouse_position()
