/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   player.rs                                          :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/07 15:53:10 by nguiard           #+#    #+#             */
/*   Updated: 2024/10/07 14:36:58 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

use std::collections::HashMap;

use crate::communication::send_to;

use super::{
	egg::Egg, map::{
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
const BEACON_TIME: u16 = 42;
const FORK_TIME: u16 = 42;

const ENDED_INCANTATION: u16 = 342;
const FOOD_PER_COLLECT: u16 = 126;
const FOOD_ON_START: u16 = 1260;

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
	pub id: usize,
	pub recieved_this_turn: bool,
}

impl Player {
	pub fn new(fd: i32, id: usize) -> Self {
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
			id,
			recieved_this_turn: false,
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
	}

	pub fn execute_casting(&mut self,
		map: &mut GameMap,
		teams: &mut HashMap<String, Team>,
		eggs: &mut Vec<Egg>,
		egg_id: &mut u128,
		castings: &HashMap<String, (GamePosition, u8, Vec<i32>)>) -> Option<PlayerActionKind> {
		match self.state {
			Idle | Dead | LevelMax | WaitingIncantation => return None,
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
						Expulse => { send_to(self.fd, "ok\n"); self.recieved_this_turn = true}, // handled after this function ends
						Broadcast(_) => self.exec_broadcast(),
						Incantation => return Some(self.action.kind.clone()), // handled after this function ends
						Fork => {
							if let Some(team) = teams.get_mut(&self.team) {
								self.exec_fork(eggs, egg_id, team);
							} else {
								send_to(self.fd, "ko\n");
								self.recieved_this_turn = true;
							}
						}
						Connect => self.exec_connect(teams),
						Beacon => self.exec_beacon(castings),
					}
					self.state = Idle;
					let last_action = self.action.kind.clone();
					self.action.kind = NoAction;
					return Some(last_action);
				}
				return None;
			}
		}
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
		self.recieved_this_turn = true;
	}

	fn exec_gauche(&mut self) {
		match self.direction {
			North => self.direction = West,
			West => self.direction = South,
			South => self.direction = East,
			East => self.direction = North,
		}
		send_to(self.fd, "ok\n");
		self.recieved_this_turn = true;
	}

	fn exec_droite(&mut self) {
		match self.direction {
			North => self.direction = East,
			East => self.direction = South,
			South => self.direction = West,
			West => self.direction = North,
		}
		send_to(self.fd, "ok\n");
		self.recieved_this_turn = true;
	}
	
	fn exec_voir(&mut self, map: &GameMap) {
		send_to(self.fd, &map.voir_data(self.position, self.direction.clone(), self.level));
		self.recieved_this_turn = true;
	}
	
	fn exec_inventaire(&mut self) {
		send_to(self.fd, (serde_json::to_string(&self.inventory).unwrap() + "\n").as_str());
		self.recieved_this_turn = true;
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
						self.recieved_this_turn = true;
						return;
					}
				}
			}
			_ => {
				send_to(self.fd, "ko\n");
				self.recieved_this_turn = true;
				return;
			} // error was not taking something (?)
		};
		if ressource_taken == Food(1) {
			if map.remove_content_cell(self.position, ressource_taken) {
				send_to(self.fd, "ok: took food\n");
				self.recieved_this_turn = true;
				self.add_food(FOOD_PER_COLLECT);
			}
			else {
				send_to(self.fd, "ko: no food on cell\n");
				self.recieved_this_turn = true;
			}
			return;
		}
		if map.remove_content_cell(self.position, ressource_taken) {
			send_to(self.fd, format!("ok: took {ressource_name}\n").as_str());
			self.recieved_this_turn = true;
			self.add_to_inventory(ressource_taken);
		}
		else {
			send_to(self.fd, format!("ko: no {ressource_name} on cell\n").as_str());
			self.recieved_this_turn = true;
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
						send_to(self.fd,"ko: cannot drop food\n");
						self.recieved_this_turn = true;
						return;
					}
					other => {
						send_to(self.fd, format!("ko: {other} not reckognised\n").as_str());
						self.recieved_this_turn = true;
						return;
					}
				}
			}
			_ => {
				send_to(self.fd, "ko\n");
				self.recieved_this_turn = true;
				return;
			}
		};
		if self.remove_from_inventory(ressource_dropped) {
			map.add_content_cell(self.position, ressource_dropped);
			send_to(self.fd, format!("ok: dropped {ressource_name}\n").as_str());
			self.recieved_this_turn = true;
		}
		else {
			send_to(self.fd, format!("ko: no {ressource_name} on your inventory\n").as_str());
			self.recieved_this_turn = true;
		}
	}

	fn exec_connect(&mut self, teams: &HashMap<String, Team>) {
		match teams.get(&self.team) {
			Some(t) => send_to(self.fd, &(t.available_connections().min(t.slots_available() as usize).to_string() + "\n")),
			None => send_to(self.fd, "0\n"),
		}
		self.recieved_this_turn = true;
	}

	fn exec_fork(&mut self, eggs: &mut Vec<Egg>, current_egg_id: &mut u128, team: &mut Team) {
		if team.slots_available() > 0 {
			*current_egg_id += 1;
			eggs.push(Egg::new(self.position, self.team.clone(), *current_egg_id));
			send_to(self.fd, "ok\n");
		} else {
			send_to(self.fd, "ko\n");
		}
		self.recieved_this_turn = true;
	}

	fn exec_broadcast(&mut self) {
		send_to(self.fd, "ok\n");
		self.recieved_this_turn = true;
	}

	fn exec_beacon(&mut self, castings: &HashMap<String, (GamePosition, u8, Vec<i32>)>) {
		let mut positions = vec![];
		for (pos, level, _) in castings.values() {
			if *level == self.level {
				positions.push(pos);
			}
		}

		let json = serde_json::to_string(&positions);
		
		if json.is_err() {
			send_to(self.fd, "ko\n");
			self.recieved_this_turn = true;
		}
		
		send_to(self.fd, format!("{}\n", json.unwrap()).as_str());
		self.recieved_this_turn = true;
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
	/// Returns Err if the Player has to be turned into a GraphicClient
	/// 	or Ok(action) with the action that is being executed
	pub fn execute_queue(&mut self,
		map: &GameMap,
		teams: &mut HashMap<String, Team>,
		eggs: &mut Vec<Egg>,
		has_gui: bool) -> Result<PlayerActionKind, ()> {
		if self.command_queue.is_empty() ||
			self.state != Idle {
			return Ok(NoAction);
		}
		let action = self.command_queue.first().unwrap().to_ascii_lowercase();
		self.command_queue.remove(0);
		if self.team.is_empty() {
			if self.team_check(map, teams, &action, has_gui) {
				return Err(());
			} else {
				return Ok(NoAction);
			}
		} else {
			match PlayerAction::from(action) {
				Ok(player_action) => {
					self.action = player_action.clone();
					if self.start_casting(&player_action.kind) {
						if matches!(player_action.kind, Connect) {
							self.exec_connect(teams);
						}
					}
					Ok(player_action.kind)
				}
				Err(e) => {
					send_to(self.fd, e.as_str());
					self.recieved_this_turn = true;
					self.execute_queue(map, teams, eggs, has_gui)
				}
			}
		}
	}
	
	fn team_check(&mut self, map: &GameMap, teams: &mut HashMap<String, Team>, team: &str, has_gui: bool) -> bool {
		if self.team.is_empty() {
			if team.to_ascii_lowercase() == "gui\n" && !has_gui {
				return true;
			}
			if let Some(internal_team) = teams.get_mut(&team[0..&team.len() - 1].to_string()) {
				let connection_nbr = internal_team.available_connections();
				let slots = internal_team.slots_available();
				if connection_nbr > 0 && slots > 0 {
					self.enable_playability(internal_team.name.clone(),
						internal_team.get_next_position().unwrap_or(GamePosition {x: 0, y: 0}));
					internal_team.current_player_count += 1;
					send_to(self.fd, format!("{}\n{} {}\n",
							connection_nbr.min(slots as usize),
							map.max_position.x,
							map.max_position.y
						).as_str());
					eprintln!("New player in team {}", &team[0..&team.len() - 1].to_string())
				}
			} else {
				send_to(self.fd, format!(
						"The team {} does not exist or is full.\n",
						&team[0..&team.len() - 1].to_string()
					).as_str());
			}
		}
		false
	}

	pub fn die(&mut self,
		map: &mut GameMap) {

		self.state = Dead;
		map.cells[self.position.x as usize][self.position.y as usize].remove_content(Player(1));
		send_to(self.fd, "You died\n\x04");
		self.recieved_this_turn = true;
		println!("A player from team {} died", self.team);
		unsafe { libc::close(self.fd); }
	}
	
	pub fn loose_food(&mut self,
		map: &mut GameMap) -> bool {
		if self.team.is_empty() ||
			self.state == Dead ||
			self.state == LevelMax {
			return false;
		}
		for x in &mut self.inventory {
			if matches!(x, &mut Food(_)) {
				if x.amount() == 0 {
					self.die(map);
					return true;
				} else {
					*x = Food(x.amount() - 1);
				}
			}
		}
		false
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

	/// Starts the casting of an action
	/// 
	/// Return true if the action has no cast time
	pub fn start_casting(&mut self, action: &PlayerActionKind) -> bool {
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
				Incantation => { self.wait_incantation(); return true },
				Fork => self.state = Casting(0, FORK_TIME),
				Connect => return true,
				Beacon => self.state = Casting(0, BEACON_TIME),
				NoAction => {},
			}
		}
		false
	}

	pub fn interrupt_casting(&mut self) -> bool {
		if matches!(self.state, Casting(_, _)) {
			self.state = Idle;
			self.action.kind = NoAction;
			return true;
		}
		false
	}

	pub fn increment_casting(&mut self) -> bool {
		match self.state {
			Casting(current, max) => {
				if current == max {
					if matches!(self.action.kind, Incantation) {
						self.state = Casting(ENDED_INCANTATION, INCANTATION_TIME);
						true
					} else {
						self.state = Idle;
						true
					}
				} else {
					if matches!(self.action.kind, Incantation) &&
						current == ENDED_INCANTATION &&
						max == INCANTATION_TIME {
						false
					} else {
						self.state = Casting(current + 1, max);
						false
					}
				}
 			},
			_ => false
		}
	}

	// INCANTATION

	pub fn wait_incantation(&mut self) {
		self.state =  WaitingIncantation;
	}

	pub fn start_incantation_casting(&mut self) {
		self.state = Casting(0, INCANTATION_TIME);
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
				"beacon" => Ok(Self { kind: PlayerActionKind::Beacon }),
				"connect" => Ok(Self { kind: PlayerActionKind::Connect }),
				"broadcast" => Ok(Self { kind: PlayerActionKind::Broadcast(it.collect::<Vec<&str>>().join(" ")) }),
				"prend" => {
					if let Some(object) = it.next() {
						Ok(Self {
							kind: PlayerActionKind::Prend(object.into()),
						})
					} else {
						Err(String::from("prend takes an argument, you need to take something\n"))
					}
				}
				"pose" => {
					if let Some(object) = it.next() {
						Ok(Self {
							kind: PlayerActionKind::Pose(object.into()),
						})
					} else {
						Err(String::from("pose takes an argument, you need to put something down\n"))
					}
				}
				_ => Err(String::from("Unrecognised action\n"))
			};
		}
		Err(String::from("Empty line\n"))
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
	Beacon,
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

impl std::fmt::Display for PlayerDirection {
	fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
		match self {
			North => write!(f, "North"),
			South => write!(f, "South"),
			East => write!(f, "East"),
			West => write!(f, "West"),
		}
	}
}

#[derive(Debug, PartialEq, Serialize, Clone)]
pub enum PlayerState {
	Idle,
	Dead,
	/// (current time, remaining time)
	Casting(u16, u16),
	LevelMax,
	WaitingIncantation,
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
	id: usize,
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
			id: player.id,
		}
	}
}

pub fn get_player_from_fd(players: &[Player], fd: i32) -> Option<&Player> {
	players.iter().find(|p| p.fd == fd)
}

pub fn get_player_from_fd_mut(players: &mut [Player], fd: i32) -> Option<&mut Player> {
	players.iter_mut().find(|p| p.fd == fd)
}