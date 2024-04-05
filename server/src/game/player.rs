/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   player.rs                                          :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/07 15:53:10 by nguiard           #+#    #+#             */
/*   Updated: 2024/03/20 17:03:53 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

use std::collections::HashMap;

use crate::communication::send_to;

use super::{
	level_up::{has_enough_ressources, remove_ressources}, map::{
		move_to_pos,
		GameCellContent::{self, *},
		GameMap,
		GamePosition
	}, teams::Team
};
use serde::Serialize;
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

const FOOD_PER_COLLECT: u16 = 50;
const FOOD_ON_START: u16 = 250;

#[derive(Debug, Clone)]
pub struct Player {
	pub fd: i32,
	pub command_queue: Vec<String>,
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

	pub fn enable_playability(&mut self, team: String, position: GamePosition) {
		self.team = team;
		self.position = position;
		self.state = Idle;
		self.add_to_inventory(Food(FOOD_ON_START));
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

	pub fn execute_casting(&mut self,
		map: &mut GameMap,
		teams: &mut HashMap<String, Team>) -> bool {
		match self.state {
			Idle | Dead | LevelMax => {},
			Casting(into, max) => {
				println!("Is casting {:?}, {}/{}", self.action.kind, into, max);
				if into >= max {
					match self.action.kind {
						NoAction => {},
						Avance => self.exec_avance(map),
						Gauche => self.exec_gauche(),
						Droite => self.exec_droite(),
						Voir => self.exec_voir(map),
						Inventaire => self.exec_inventaire(),
						Prend(_) => self.exec_prend(map),
						Pose(_) => self.exec_pose(map),
						Expulse => send_to(self.fd, "Action not coded yet\n"), // self.exec_expulse(),
						Broadcast(_) => send_to(self.fd, "Action not coded yet\n"), // self.exec_broadcast(),
						Incantation => self.exec_incantation(teams),
						Fork => send_to(self.fd, "Action not coded yet\n"), // self.exec_fork(),
						Connect => send_to(self.fd, "Action not coded yet\n"), // self.exec_connect(),
					}
					self.state = Idle;
					self.action.kind = NoAction;
				}
			}
		}
		true
	}

	fn exec_avance(&mut self, map: &mut GameMap) {
		let mut new_pos: GamePosition = GamePosition {
			x: self.position.x,
			y: self.position.y,
		};
		
		match self.direction {
			North => new_pos.y = move_to_pos(map.max_position.y, new_pos.y, -1) as u8,
			South => new_pos.y = move_to_pos(map.max_position.y, new_pos.y, 1) as u8,
			East => new_pos.x = move_to_pos(map.max_position.x, new_pos.x, 1) as u8,
			West => new_pos.x = move_to_pos(map.max_position.x, new_pos.x, -1) as u8,
		}

		map.remove_content_cell(self.position, GameCellContent::Player(1));
		map.add_content_cell(new_pos, GameCellContent::Player(1));
		self.position = new_pos;
		send_to(self.fd, "ok\n");
	}

	fn exec_gauche(&mut self) {
		match self.direction {
			North => self.direction = West,
			West => self.direction = South,
			South => self.direction = East,
			East => self.direction = North,
		}
		send_to(self.fd, "ok\n");
	}

	fn exec_droite(&mut self) {
		match self.direction {
			North => self.direction = East,
			East => self.direction = South,
			South => self.direction = West,
			West => self.direction = North,
		}
		send_to(self.fd, "ok\n");
	}
	
	fn exec_voir(&self, map: &GameMap) {
		send_to(self.fd, &map.voir_data(self.position, self.direction.clone(), self.level))
	}
	
	fn exec_inventaire(&self) {
		send_to(self.fd, serde_json::to_string(&self.inventory).unwrap().as_str());
	}

	fn exec_prend(&mut self, map: &mut GameMap) {
		let ressource_name: String;
		let ressource_taken = match &self.action.kind {
			Prend(name) => {
				ressource_name = name.to_ascii_lowercase();
					match name.to_ascii_lowercase().as_str() {
					"linemate" => Linemate(1),
					"deraumere" => Deraumere(1),
					"sibur" => Sibur(1),
					"mendiane" => Mendiane(1),
					"phiras" => Phiras(1),
					"thystame" => Thystame(1),
					"food" => Food(1),
					other => {
						send_to(self.fd, format!("ko: {other} not reckognised\n").as_str());
						return;
					}
				}
			}
			_ => {
				send_to(self.fd, "ko\n");
				return;
			} // error was not taking something (?)
		};
		if ressource_taken == Food(1) {
			if map.remove_content_cell(self.position, ressource_taken) {
				send_to(self.fd, "ok: took food\n");
				self.add_food(FOOD_PER_COLLECT);
			}
			else {
				send_to(self.fd, "ko: no food on cell\n");
			}
			return;
		}
		if map.remove_content_cell(self.position, ressource_taken) {
			send_to(self.fd, format!("ok: took {ressource_name}\n").as_str());
			self.add_to_inventory(ressource_taken);
		}
		else {
			send_to(self.fd, format!("ko: no {ressource_name} on cell\n").as_str());
		}
	}

	fn exec_pose(&mut self, map: &mut GameMap) {
		let ressource_name: String;
		let ressource_dropped = match &self.action.kind {
			Pose(name) => {
				ressource_name = name.to_ascii_lowercase();
					match name.to_ascii_lowercase().as_str() {
					"linemate" => Linemate(1),
					"deraumere" => Deraumere(1),
					"sibur" => Sibur(1),
					"mendiane" => Mendiane(1),
					"phiras" => Phiras(1),
					"thystame" => Thystame(1),
					"food" => {
						send_to(self.fd, format!("ko: cannot drop food\n").as_str());
						return;
					}
					other => {
						send_to(self.fd, format!("ko: {other} not reckognised\n").as_str());
						return;
					}
				}
			}
			_ => {
				send_to(self.fd, "ko\n");
				return;
			} // error was not taking something (?)
		};
		if self.remove_from_inventory(ressource_dropped) {
			map.add_content_cell(self.position, ressource_dropped);
			send_to(self.fd, format!("ok: dropped {ressource_name}\n").as_str());
		}
		else {
			send_to(self.fd, format!("ko: no {ressource_name} on your inventory\n").as_str());
		}
	}

	fn exec_incantation(&mut self, teams: &mut HashMap<String, Team>) {
		if has_enough_ressources(&self.inventory, self.level, 8) { // to change last param
			remove_ressources(self);
			self.level += 1;
			send_to(self.fd, "ok\n");
			if self.level == 8 {
				self.state = LevelMax;
				send_to(self.fd, "Congratulations! You are level 8: the maximum level!\n");
				if let Some(my_team) = teams.get_mut(&self.team) {
					my_team.max_level += 1;
				}
			}
		} else {
			send_to(self.fd, "ko: not enough ressources\n");
		}
	}

	pub fn add_to_inventory(&mut self, to_add: GameCellContent) {
		for i in 0..self.inventory.len() {
			if self.inventory[i] == to_add {
				self.inventory[i].add(to_add.amount());
				return;
			}
		}
		self.inventory.push(to_add);
	}

	pub fn remove_from_inventory(&mut self, to_remove: GameCellContent) -> bool {
		for i in 0..self.inventory.len() {
			if self.inventory[i] == to_remove && self.inventory[i].amount() > 0 {
				self.inventory[i].remove(to_remove.amount());
				return true;
			}
		}
		false
	}

	/// Executes the queue of a player
	/// 
	/// Has to be executed after a call to `execute_casting()`
	/// 
	/// Returns true if the Player has to be turned into a GraphicClient
	pub fn execute_queue(&mut self, map: &GameMap, teams: &mut HashMap<String, Team>,
		has_gui: bool) -> bool {
		if self.command_queue.is_empty() ||
			self.state != Idle {
			return false;
		}
		let action = self.command_queue.first().unwrap().to_ascii_lowercase();
		self.command_queue.remove(0);
		if self.team.is_empty() {
			if self.team_check(map, teams, &action, has_gui) {
				return true;
			}
		} else {
			match PlayerAction::from(action) {
				Ok(player_action) => {
					self.action = player_action.clone();
					self.start_casting(&player_action.kind);
				}
				Err(e) => {
					send_to(self.fd, e.as_str());
					self.execute_queue(map, teams, has_gui); // sus
				}
			}	
		}
		false
	}
	
	fn team_check(&mut self, map: &GameMap, teams: &mut HashMap<String, Team>, team: &str, has_gui: bool) -> bool {
		if self.team.is_empty() {
			if team.to_ascii_lowercase() == "gui\n" && !has_gui {
				return true;
			}
			if let Some(internal_team) = teams.get_mut(&team[0..&team.len() - 1].to_string()) {
				let connection_nbr = internal_team.available_connections();
				if connection_nbr > 0 {
					self.enable_playability(internal_team.name.clone(),
						internal_team.get_next_position().unwrap_or(GamePosition {x: 0, y: 0}));
				}
				send_to(self.fd, format!("{}\n{} {}\n",
						connection_nbr,
						map.max_position.x,
						map.max_position.y
					).as_str());
			} else {
				send_to(self.fd, format!(
						"The team {} does not exist\n",
						&team[0..&team.len() - 1].to_string()
					).as_str());
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
		for x in &mut self.inventory {
			if matches!(x, &mut Food(_)) {
				if x.amount() == 0 {
					self.state =  Dead;
					send_to(self.fd, "You died\n");
				} else {
					*x = Food(x.amount() - 1);
				}
			}
		}
	}

	pub fn add_food(&mut self, food_amount: u16) {
		if self.team.is_empty() ||
			self.state == Dead ||
			self.state == LevelMax {
			return;
		}
		for x in &mut self.inventory {
			if matches!(x, &mut Food(_)) {
				if (x.amount() as u32 + food_amount as u32) > u16::MAX as u32 {
					*x = Food(u16::MAX);
				} else {
					*x = Food(x.amount() + food_amount);
				}
			}
		}
	}

	pub fn start_casting(&mut self, action: &PlayerActionKind) {
		if self.state == Idle {
			match action {
				Avance => self.state = Casting(0, AVANCE_TIME),
				Gauche => self.state = Casting(0, GAUCHE_TIME),
				Droite => self.state = Casting(0, DROITE_TIME),
				Voir => self.state = Casting(0, VOIR_TIME),
				Inventaire => self.state = Casting(0, INVENTAIRE_TIME),
				Prend(_) => self.state = Casting(0, PREND_TIME),
				Pose(_) => self.state = Casting(0, POSE_TIME),
				Expulse => self.state = Casting(0, EXPULSE_TIME),
				Broadcast(_) => self.state = Casting(0, BROADCAST_TIME),
				Incantation => self.state = Casting(0, INCANTATION_TIME),
				Fork => self.state = Casting(0, FORK_TIME),
				Connect => self.state = Casting(0, CONNECT_TIME),
				_ => {},
			}
		}
	}

	pub fn increment_casting(&mut self) -> bool {
		match self.state {
			Casting(current, max) => {
				if current == max {
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
		let mut it = line.split_ascii_whitespace();
		if let Some(first_word) = it.next() {
			return match first_word.to_ascii_lowercase().as_str() {
				"avance" => Ok(Self { kind: PlayerActionKind::Avance }),
				"gauche" => Ok(Self { kind: PlayerActionKind::Gauche }),
				"droite" => Ok(Self { kind: PlayerActionKind::Droite }),
				"voir" => Ok(Self { kind: PlayerActionKind::Voir }),
				"inventaire" => Ok(Self { kind: PlayerActionKind::Inventaire }),
				"expulse" => Ok(Self { kind: PlayerActionKind::Expulse }),
				"fork" => Ok(Self { kind: PlayerActionKind::Fork }),
				"incantation" => Ok(Self { kind: PlayerActionKind::Incantation }),
				"connect" => Ok(Self { kind: PlayerActionKind::Connect }),
				"broadcast" => Ok(Self { kind: PlayerActionKind::Broadcast(it.collect()) }),
				"prend" => {
					if let Some(object) = it.next() {
						Ok(Self {
							kind: PlayerActionKind::Prend(object.into()),
						})
					} else {
						Err(String::from("prend takes an argument, you need to take something"))
					}
				}
				"pose" => {
					if let Some(object) = it.next() {
						Ok(Self {
							kind: PlayerActionKind::Pose(object.into()),
						})
					} else {
						Err(String::from("pose takes an argument, you need to put something down"))
					}
				}
				_ => Err(String::from("Unrecognised action"))
			};
		}
		Err(String::from("Empty line"))
	}
}

#[derive(Serialize, Debug, Clone)]
pub enum PlayerActionKind {
	Avance,
	Gauche,
	Droite,
	Voir,
	Inventaire,
	Prend(String),
	Pose(String),
	Expulse,
	Broadcast(String),
	Incantation,
	Fork,
	Connect,
	NoAction,
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
}

impl From<Player> for SendPlayer {
	fn from(player: Player) -> Self {
		let mut inventory: Vec<GameCellContent> = vec![];
		
		for content in player.inventory.clone() {
			if content.amount() > 0 {
				inventory.push(content);
			}
		}

		Self {
			position: player.position,
			direction: player.direction.clone(),
			team: player.team.clone(),
			action: player.action.kind.clone(),
			inventory,
			state: player.state.clone(),
			level: player.level,
		}
	}
}

pub fn get_player_from_fd(players: &mut [Player], fd: i32) -> Option<&mut Player> {
	players.iter_mut().find(|p| p.fd == fd)
}