@tool
extends Button
class_name PlayerInfoBtn


@onready var texture_rect: TextureRect = %TextureRect
@onready var label_info: Label = $HBoxContainer/LabeInfo

var player_id: int

@export var logo: Texture2D:
	set(val):
		# print(val)
		logo = val
		if texture_rect:
			texture_rect.texture = logo
		
@export var info: String:
	set(val):
		# print("info: ", val)
		info = val
		if label_info:
			label_info.text = info

@export var logo_color: Color:
	set(val):
		logo_color = val
		if texture_rect:
			# print("shader parama: ", (texture_rect.material as ShaderMaterial).get_shader_parameter("outline_color"))
			(texture_rect.material as ShaderMaterial).set_shader_parameter("outline_color", logo_color)

func _ready() -> void:
		#texture_rect.material = preload("res://player_shader.tres")
		#(texture_rect.material as ShaderMaterial).set_shader_parameter("shader_parameter/outline_color", Vector4(255,1,1, 1))
	texture_rect.material = preload("res://player_shader.tres").duplicate()
