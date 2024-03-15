/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   player.rs                                          :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/07 15:53:10 by nguiard           #+#    #+#             */
/*   Updated: 2024/03/15 13:45:11 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

use crate::communication::send_to;

use super::{map::{GameCellContent, GameMap, GamePosition}, TURNS_TO_DIE};
use serde::Serialize;
use PlayerFood::*;
use PlayerState::*;
use PlayerDirection::*;
use PlayerActionKind::*;

const AVANCE_TIME: u16 = 7;
const DROITE_TIME: u16 = 7;
const GAUCHE_TIME: u16 = 7;
const VOIR_TIME: u16 = 7;
const INVENTAIRE_TIME: u16 = 1;
const PREND_TIME: u16 = 7;
const POSE_TIME: u16 = 7;
const EXPULSE_TIME: u16 = 7;
const BROADCAST_TIME: u16 = 7;
const INCANTATION_TIME: u16 = 300;
const FORK_TIME: u16 = 42;
const CONNECT_TIME: u16 = 0;

#[derive(Debug, Clone)]
pub struct Player {
	pub fd: i32,
	pub command_queue: Vec<String>,
	pub food: PlayerFood,
	pub level: u8,
	pub inventory: Vec<GameCellContent>,
	pub state: PlayerState,
	pub position: GamePosition,
	pub direction: PlayerDirection,
	pub team: String,
	pub action: PlayerAction,
}

impl Player {
	pub fn new(fd: i32) -> Self {
		Player {
			fd,
			command_queue: vec![],
			food: HasSome(250),
			level: 1,
			inventory: vec![],
			state: Idle,
			position: GamePosition {
				x: 0,
				y: 0,
			},
			direction: North,
			team: String::new(),
			action: PlayerAction::new(),
		}
	}
	
	pub fn push_to_queue(&mut self, mut new: Vec<String>) {
		if new.is_empty() {
			return;
		}
		if self.command_queue.is_empty() {
			self.command_queue = new;
			return;
		}
		if let Some(last) = self.command_queue.last_mut() {
			if !last.ends_with('\n') {
				last.push_str(new.first_mut().unwrap().clone().as_str());
				new.remove(0);
			}
			self.command_queue.append(&mut new);
		}
		dbg!(&self.command_queue);
	}

	/// Executes the queue of a player
	/// 
	/// Returns true if the Player has to be turned into a GraphicClient
	pub fn execute_queue(&mut self, map: &GameMap, teams: &[String],
		has_gui: bool) -> bool {
		if self.command_queue.is_empty() {
			return false;
		}
		let action = self.command_queue.first().unwrap().to_ascii_lowercase();
		self.command_queue.remove(0);
		if self.team_check(map, teams, action, has_gui) {
			return true;
		}
		false
	}
	
	fn team_check(&mut self, map: &GameMap, teams: &[String], team: String, has_gui: bool) -> bool {
		if self.team.is_empty() {
			if team.to_ascii_lowercase() == "gui\n" &&
				!has_gui {
				return true;
			}
			if teams.contains(&team[0..&team.len() - 1].to_string()) {
				self.team = team;
				send_to(self.fd, format!("1\n{} {}\n", map.max_position.x, map.max_position.y).as_str());
			} else {
				send_to(self.fd, "This team does not exist\n");
			}
		}
		false
	}
	
	pub fn loose_food(&mut self) {
		if self.team.is_empty() ||
			self.state == Dead ||
			self.state == LevelMax {
			return;
		}
		match self.food {
			HasSome(x) => {
				if x == 0 {
					self.food = TurnsWithout(0);
				} else {
					self.food = HasSome(x - 1);
				}
			},
			TurnsWithout(x) => {
				if x >= TURNS_TO_DIE {
					self.state = Dead;
				} else {
					self.food = TurnsWithout(x + 1);
				}
			}
		}
	}

	pub fn start_casting(&mut self, action: &str) {
		if self.state == Idle {
			match action.to_uppercase().as_str() {
				"AVANCE" => self.state = Casting(0, AVANCE_TIME),
				"GAUCHE" => self.state = Casting(0, GAUCHE_TIME),
				"DROITE" => self.state = Casting(0, DROITE_TIME),
				"VOIR" => self.state = Casting(0, VOIR_TIME),
				"INVENTAIRE" => self.state = Casting(0, INVENTAIRE_TIME),
				"PREND" => self.state = Casting(0, PREND_TIME),
				"POSE" => self.state = Casting(0, POSE_TIME),
				"EXPULSE" => self.state = Casting(0, EXPULSE_TIME),
				"BROADCAST" => self.state = Casting(0, BROADCAST_TIME),
				"INCANTATION" => self.state = Casting(0, INCANTATION_TIME),
				"FORK" => self.state = Casting(0, FORK_TIME),
				"CONNECT" => self.state = Casting(0, CONNECT_TIME),
				_ => {},
			}
		}
	}

	pub fn increment_casting(&mut self) -> bool {
		match self.state {
			Casting(current, max) => {
				if current + 1 == max {
					self.state = Idle;
					true
				} else {
					self.state = Casting(current + 1, max);
					false
				}
 			},
			_ => false
		}
	}
}

#[derive(Debug, Clone)]
pub struct PlayerAction {
	kind: PlayerActionKind,
}

impl PlayerAction {
	pub fn new() -> Self {
		PlayerAction {
			kind: PlayerActionKind::NoAction,
		}
	}

	pub fn from(line: String) -> Result<Self, String> {
		let first_word: String = line.split_ascii_whitespace().collect(); //pas sur
		
		match first_word.to_ascii_lowercase().as_str() {
			"avance" => Ok(Self { kind: PlayerActionKind::Avance }),
			"gauche" => Ok(Self { kind: PlayerActionKind::Gauche }),
			"droite" => Ok(Self { kind: PlayerActionKind::Droite }),
			"broadcast" => Ok(Self { kind: PlayerActionKind::Broadcast }),
			"voir" => Ok(Self { kind: PlayerActionKind::Voir }),
			"prend" => Ok(Self { kind: PlayerActionKind::Prend }),
			"pose" => Ok(Self { kind: PlayerActionKind::Pose }),
			"expulse" => Ok(Self { kind: PlayerActionKind::Expulse }),
			"fork" => Ok(Self { kind: PlayerActionKind::Fork }),
			"incantation" => Ok(Self { kind: PlayerActionKind::Incantation }),
			"connect" => Ok(Self { kind: PlayerActionKind::Connect }),
			_ => Err(String::from("Unrecognised action"))
		}
	}
	
	pub fn get_time(&self) -> u16 {
		match self.kind {
			Connect | NoAction => 0,
			Inventaire => 1,
			Avance | Gauche | Droite | Broadcast |
				Voir | Prend | Pose | Expulse => 7,
			Fork => 42,
			Incantation => 300,
		}
	}

	pub fn time_of(action: &Self) -> u16 {
		action.get_time()
	}
}

#[derive(Serialize, Debug, Clone)]
pub enum PlayerActionKind {
	Avance,
	Gauche,
	Droite,
	Voir,
	Inventaire,
	Prend,
	Pose,
	Expulse,
	Broadcast,
	Incantation,
	Fork,
	Connect,
	NoAction,
}

#[derive(Debug, Serialize, Clone)]
pub enum PlayerFood {
	HasSome(u16),
	TurnsWithout(u16),
}

#[derive(Debug, Serialize, Clone)]
pub enum PlayerDirection {
	North,
	South,
	East,
	West,
}

#[derive(Debug, PartialEq, Serialize, Clone)]
pub enum PlayerState {
	Idle,
	Dead,
	/// (current time, remaining time)
	Casting(u16, u16),
	LevelMax,
}

#[derive(Serialize)]
pub struct SendPlayer {
	position: GamePosition,
	direction: PlayerDirection,
	team: String,
	action: PlayerActionKind,
	inventory: Vec<GameCellContent>,
	state: PlayerState,
	level: u8,
	food: PlayerFood,
}

impl From<Player> for SendPlayer {
	fn from(player: Player) -> Self {
		let mut inventory: Vec<GameCellContent> = vec![];
		
		for content in player.inventory {
			if content.amount() > 0 {
				inventory.push(content);
			}
		}

		Self {
			position: player.position,
			direction: player.direction,
			team: player.team,
			action: player.action.kind,
			inventory,
			state: player.state,
			level: player.level,
			food: player.food,
		}
	}
}

pub fn get_player_from_fd(players: &mut Vec<Player>, fd: i32) -> Option<&mut Player> {
	players.iter_mut().find(|p| p.fd == fd)
}