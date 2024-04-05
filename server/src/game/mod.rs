/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   mod.rs                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/05 17:25:42 by nguiard           #+#    #+#             */
/*   Updated: 2024/04/05 17:01:13 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

pub mod map;
pub mod player;
pub mod gui;
pub mod level_up;
pub mod teams;
pub mod egg;

use std::{collections::HashMap, io::{Error, ErrorKind::InvalidInput}};

use crate::communication::send_to;

use self::{
	egg::Egg,
	gui::GraphicClient,
	map::{move_to_pos, GameMap},
	player::{Player, PlayerActionKind, PlayerDirection},
	teams::Team
};


#[derive(Debug)]
pub struct Game {
	pub players: Vec<Player>,
	pub map: GameMap,
	pub last_map: Option<GameMap>, // needed for updates to gui
	pub gui: Option<GraphicClient>,
	pub teams: HashMap<String, Team>,
	pub eggs: Vec<Egg>
}

impl Game {
	pub fn new(x: u8, y: u8, teams: Vec<String>, clients: u8, seed: usize) -> Result<Self, std::io::Error> {
		let (map,mut positions) = GameMap::new(x, y, teams.len() as u8, clients, seed);
		let mut teams_map: HashMap<String, Team>= HashMap::new();
		for t in teams {
			let mut new_team = Team::new(t.clone());
			for _ in 0..clients {
				dbg!(&positions);
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
		let mut to_do_after: Vec<(i32, PlayerActionKind)> = vec![];
		
		for player in self.players.iter_mut() {
			if let Some(action) = player.execute_casting(&mut self.map, &mut self.teams, &mut self.eggs) {
				to_do_after.push((player.fd, action))
			}
			if player.execute_queue(&self.map, &mut self.teams, &mut self.eggs, self.gui.is_some()) {
				to_remove = Some(player.fd);
			}
		}

		for (fd, action) in &mut to_do_after {
			match action {
				PlayerActionKind::Expulse => {
					Self::handle_kick(&mut self.players, &mut self.map, *fd);
					dbg!(&self.players);
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
			player.loose_food(&mut self.map, &mut self.teams);
			player.increment_casting();
		}
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

	fn handle_kick(players: &mut Vec<Player>, map: &mut GameMap, kicking_fd: i32) {
		let mut other = players.clone();
		let mut kicking = players.clone();
		other.retain(|p| p.fd != kicking_fd);
		kicking.retain(|p| p.fd == kicking_fd);
	
		for player in kicking {
			let cell = &map.cells[player.position.x as usize][player.position.y as usize];
		
			if let Some(player_content) = cell.get_content(map::GameCellContent::Player(0)) {
				if player_content.amount() > 1 {
					for mut other_player in &mut other {
						if other_player.position == player.position {
							Self::move_kicked_player(map, &mut other_player, player.direction.clone());
							dbg!(&other_player);
						}
					}
				}
			}
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
		dbg!(&player);
		send_to(player.fd, format!("deplacement {}\n", direction).as_str());
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