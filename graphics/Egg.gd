extends Node2D

var tween_jump: Tween

func jump_anim() -> void:
	tween_jump = get_tree().create_tween()
	var old_scale: Vector2 = scale
	tween_jump.tween_property(self, "scale", scale * 1.5, 1).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_QUART).set_delay(1)
	tween_jump.tween_property(self, "position", position + Vector2(0, -200), 0.5).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_QUART)
	tween_jump.tween_property(self, "position", position + Vector2(0, 0), 0.5).set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_QUART)
	tween_jump.tween_property(self, "scale", old_scale, 0.2).set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_QUAD)

func rotate_anim() -> void:
	tween_jump = get_tree().create_tween()
	tween_jump.tween_property(self, "rotation_degrees", 360 * 4, 1).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_LINEAR)
	#tween_jump.tween_property(self, "rotation_degrees", 0, 1).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_LINEAR)

func _ready() -> void:
	jump_anim()
	#rotate_anim()
