/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   mod.rs                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/05 17:25:42 by nguiard           #+#    #+#             */
/*   Updated: 2024/08/28 17:09:55 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

pub mod map;
pub mod player;
pub mod gui;
pub mod level_up;
pub mod teams;
pub mod egg;

use std::{collections::HashMap, io::{Error, ErrorKind::InvalidInput}};

use rand::{rngs::StdRng, SeedableRng};

use crate::communication::send_to;
use crate::PlayerState::WaitingIncantation;

use self::{
	egg::Egg, gui::GraphicClient, level_up::{has_enough_ressources, remove_ressources}, map::{move_to_pos, GameMap, GamePosition}, player::{get_player_from_fd, get_player_from_fd_mut, Player, PlayerActionKind, PlayerDirection, PlayerState}, teams::Team
};

const MAX_LEVEL_TO_WIN: u8 = 6;

#[derive(Debug)]
pub struct Game {
	pub players: Vec<Player>,
	pub map: GameMap,
	pub last_map: Option<GameMap>, // needed for updates to gui
	pub gui: Option<GraphicClient>,
	pub teams: HashMap<String, Team>,
	pub eggs: Vec<Egg>,
	current_egg_id: u128,
	pub castings: HashMap<String, (GamePosition, u8, Vec<i32>)>
}

impl Game {
	pub fn new(x: u8, y: u8, teams: Vec<String>, clients: u8, seed: usize) -> Result<Self, std::io::Error> {
		let (map, mut positions) = GameMap::new(x, y, teams.len() as u8, clients, seed);
		let mut teams_map: HashMap<String, Team>= HashMap::new();
		for t in teams {
			let mut new_team = Team::new(t.clone());
			for _ in 0..clients {
				if let Some(pos) = positions.pop_front() {
					new_team.add_position(pos);
				} else {
					return Err(Error::new(InvalidInput, "Could not give a position to the first player of a team"));
				}
			} 
			if teams_map.insert(t.clone(), new_team).is_some() {
				return Err(Error::new(InvalidInput, "Duplicate in team name"));
			}
		}
		Ok(Game {
			players: vec![],
			map: map.clone(),
			last_map: None,
			gui: None,
			teams: teams_map,
			eggs: vec!(),
			current_egg_id: 0,
			castings: HashMap::new(),
		})
	}
	
	pub fn try_remove_gui(&mut self, fd: i32) {
		match &self.gui {
			Some(gc) => if fd == gc.fd { self.gui = None },
			None => {},
		}
	}

	/// Logic of the game, what occurs every tick
	pub fn execute(&mut self) {
		let mut to_remove = None;
		let mut actions_to_do_after: Vec<(i32, PlayerActionKind)> = vec![];
		let mut dead_players: Vec<i32> = vec![];
		let mut updated_castings: Vec<(GamePosition, u8, String)> = vec![];

		for player in self.players.iter_mut() {
			if let Some(action) = player.execute_casting(&mut self.map,
				&mut self.teams,
				&mut self.eggs,
				&mut self.current_egg_id,
				&self.castings) {
				actions_to_do_after.push((player.fd, action))
			}
			match player.execute_queue(&self.map, &mut self.teams, &mut self.eggs, self.gui.is_some()) {
				Err(_) => to_remove = Some(player.fd),
				Ok(action) => match action {
					PlayerActionKind::Incantation => {
						let key = Self::casting_insert(
							&mut self.castings,
							(player.position, player.level),
							player.fd);
						updated_castings.push((player.position, player.level, key));
					},
					_ => {}
				}
			}
		}

		for (pos, level, key) in updated_castings {
			if Self::casting_update(&mut self.players, pos, level) {
				self.castings.remove(&key);
			}
		}

		for (fd, action) in &mut actions_to_do_after {
			match action {
				PlayerActionKind::Expulse => {
					Self::handle_kick(&mut self.players, &mut self.map, *fd);
				}
				PlayerActionKind::Broadcast(text) => {
					Self::handle_broadcast(&self.players, &self.map, *fd, text);
				}
				PlayerActionKind::Incantation => {
					Self::handle_incantation(&mut self.players, &mut self.map, *fd);
				}
				_ => {}
			}
		}
		
		if let Some(fd) = to_remove {
			self.players.retain(|p| p.fd != fd);
			self.gui = Some(GraphicClient::new(to_remove.unwrap()));
			self.map.send_map(self.gui.as_ref().unwrap().fd);
		}
		
		for player in &mut self.players {
			if player.loose_food(&mut self.map) {
				dead_players.push(player.fd);
			}
			player.increment_casting();
			if player.recieved_this_turn {
				send_to(player.fd, "\x04");
				player.recieved_this_turn = false;
			}
		}

		self.players.retain(|p| !dead_players.contains(&p.fd));

		self.eggs.retain_mut(|egg| {
			if let Some((position, team_name)) = egg.try_hatch() {
				if let Some(team) = self.teams.get_mut(&team_name) {
					team.add_position(position);
				}
				false
			} else {
				true
			}
		})
	}

	pub fn regenerate_ressources(&mut self, seed: usize) {
		self.map.regenerate_ressources(&mut StdRng::seed_from_u64(seed as u64),
			self.map.max_position.x,
			self.map.max_position.y);
	}

	fn handle_incantation(players: &mut Vec<Player>, map: &mut GameMap, fd: i32) {
		let player = get_player_from_fd(players, fd).unwrap();
		let pos = player.position.clone();
		let level = player.level;
		let cell = map.get_cell_mut(pos.x, pos.y).unwrap();
		let mut same_level = 0;
		let mut to_level_up: Vec<i32> = vec![];

		for p in players.clone() {
			if p.position == pos && p.level == level {
				same_level += 1;
				to_level_up.push(p.fd);
			}
		}

		if has_enough_ressources(&cell.content, level, same_level) {
			remove_ressources(cell, level);
			for fd in to_level_up {
				let p = get_player_from_fd_mut(players, fd).unwrap();
				p.level += 1;
				p.state = PlayerState::Idle;
				println!("Player leveled up!");
				send_to(p.fd, "ok\n");
				p.recieved_this_turn = true;
			}
		} else {
			for fd in to_level_up {
				let p = get_player_from_fd_mut(players, fd).unwrap();
				p.state = PlayerState::Idle;
				send_to(p.fd, "ko\n");
				p.recieved_this_turn = true;
			}
		}
	}

	fn handle_broadcast(players: &Vec<Player>,
		map: &GameMap,
		broadcasting: i32,
		text: &String) {

		let mut other = players.clone();
		other.retain(|p| p.fd != broadcasting);
		let mut position = GamePosition { x: 255, y: 255 };
	
		for p in players {
			if p.fd == broadcasting {
				position = p.position.clone();
				break;
			}
		}

		if position.x == 255 {
			return;
		}

		for p in &mut other {
			let comming_from: u8;
			if p.position == position {
				comming_from = 0;
			} else {
				comming_from = map.comes_from(p.position, position, p.direction.clone());
			}
			send_to(p.fd, format!("broadcast {comming_from}: {text}\n").as_str());
			p.recieved_this_turn = true;
		}
	}
	
	fn handle_kick(players: &mut Vec<Player>, map: &mut GameMap, kicking_fd: i32) {
		let mut other = players.clone();
		let kicking = players;
		other.retain(|p| p.fd != kicking_fd);
		kicking.retain(|p| p.fd == kicking_fd);
	
		for player in kicking.clone() {
			let cell = &map.cells[player.position.x as usize][player.position.y as usize];
		
			if let Some(player_content) = cell.get_content(map::GameCellContent::Player(0)) {
				if player_content.amount() > 1 {
					for i in 0..other.len() {
						if other[i].position == player.position {
							Self::move_kicked_player(map, &mut other[i], player.direction.clone());
							other[i].interrupt_casting();
						}
					}
				}
			}
		}

		for player in other {
			kicking.push(player);
		}
	}

	fn move_kicked_player(map: &mut GameMap,
		player: &mut Player,
		direction: PlayerDirection) {
		let mut pos = player.position;

		map.remove_content_cell(pos, map::GameCellContent::Player(1));
		match direction {
			PlayerDirection::North => pos.y = move_to_pos(map.max_position.y, pos.y, -1) as u8,
			PlayerDirection::South => pos.y = move_to_pos(map.max_position.y, pos.y, 1) as u8,
			PlayerDirection::East => pos.x = move_to_pos(map.max_position.x, pos.x, 1) as u8,
			PlayerDirection::West => pos.x = move_to_pos(map.max_position.x, pos.x, -1) as u8,
		}

		map.add_content_cell(pos, map::GameCellContent::Player(1));
		player.position = pos;
		send_to(player.fd, format!("deplacement {}\n", direction).as_str());
		player.recieved_this_turn = true;
	}
	
	pub fn win_check(&mut self) -> Option<String> {
		let mut not_lost_teams: Vec<&Team> = vec![];

		self.loose_check();
		for team in self.teams.values() {
			if team.max_level == MAX_LEVEL_TO_WIN {
				return Some(format!(
					"End of game: Win: Team {} won the game by elevating!\n",
					not_lost_teams[1].name));
			}
			if !team.lost {
				not_lost_teams.push(team);
			}
		}

		if not_lost_teams.len() == 0 {
			return Some("End of game: Draw: Every team lost.\n".to_string())
		} else if not_lost_teams.len() == 1 {
			return Some(format!(
				"End of game: Win: Team {} won the game by being the last one alive!\n",
				not_lost_teams[0].name));
		}
		None
	}
	
	fn loose_check(&mut self) {
		let mut players_alive: Vec<u8> = vec![];
		let mut i = 0;

		for team_name in self.teams.keys() {
			let mut count = 0;
			for player in &self.players {
				if &player.team == team_name {
					if count != u8::MAX {
						count += 1;
					}
				}
			}
			players_alive.push(count)
		}

		for (team_name, team) in &mut self.teams {
			if !team.lost && team.available_connections() + players_alive[i] as usize == 0 {
				println!("Team {} lost the game.", team_name);
				team.lost = true;
			}
			i += 1;
		}
	}
	
	fn casting_insert(
		castings: &mut HashMap<String, (GamePosition, u8, Vec<i32>)>,
		key: (GamePosition, u8),
		fd: i32) -> String {
		let key_string = format!("{} {} {}", key.0.x, key.0.y, key.1);
	
		match castings.get_mut(&key_string) {
			None => {
				castings.insert(key_string.clone(), (key.0, key.1, vec![fd]));
			},
			Some(casting) => {
				casting.2.push(fd);
			}
		}
		key_string
	}

	fn casting_update(players: &mut Vec<Player>, position: GamePosition, level: u8) -> bool {
		let mut nb_of_players = match level {
			1 => 1,
			2 | 3 => 2,
			4 | 5 => 4,
			6 | 7 => 6,
			_ => 1000000,
		};

		// enough players?
		for p in & *players {
			if p.position == position &&
				p.level == level &&
				nb_of_players > 0 {
				nb_of_players -= 1;
			}
		}

		if nb_of_players > 0 {
			return false
		}

		// Start the casting
		for p in players {
			if p.position == position &&
				p.level == level &&
				p.state == WaitingIncantation {
				p.start_incantation_casting();
			}
		}
		true
	}
}

impl Drop for Game {
	fn drop(&mut self) {
		for x in &self.players {
			send_to(x.fd, "Disconnected from the server: server closed\n");
			unsafe { libc::close(x.fd) };
		}
		if let Some(x) = &self.gui {
			send_to(x.fd, "Disconnected from the server: server closed\n");
			unsafe { libc::close(x.fd) };
		}
	}
}