/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   map.rs                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/05 17:04:32 by nguiard           #+#    #+#             */
/*   Updated: 2024/08/25 19:46:11 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

use std::{cmp::min, collections::VecDeque, fmt::Display, time::Instant};

use serde::Serialize;
use rand::{rngs::StdRng, RngCore, SeedableRng};
use GameCellContent::*;

use crate::communication::send_to;

use super::player::PlayerDirection;
const DEVIDE_U32_TO_U8: u32 = 16843009;

use crate::TURN_TO_REGENERATE;

/// Indexes in the "max" tab
const LINEMATE_INDEX: usize = 0;
const DERAUMERE_INDEX: usize = 1;
const SIBUR_INDEX: usize = 2;
const MENDIANE_INDEX: usize = 3;
const PHIRAS_INDEX: usize = 4;
const THYSTAME_INDEX: usize = 5;
const FOOD_INDEX: usize = 6;
const PLAYER_INDEX: usize = 7;

/// Colors
const THYSTAME_COLOR: &str = "\x1b[1;100;95m";
const PHIRAS_COLOR: &str = "\x1b[1;100;94m";
const MENDIANE_COLOR: &str = "\x1b[1;100;32m";
const SIBUR_COLOR: &str = "\x1b[1;100;31m";
const DERAUMERE_COLOR: &str = "\x1b[1;100;35m";
const LINEMATE_COLOR: &str = "\x1b[1;100;90m";
const FOOD_COLOR: &str = "\x1b[0;42;97m";
const EGG_COLOR: &str = "\x1b[0;43;97m";
const PLAYER_COLOR: &str = "\x1b[0;107;30m";
const RESET: &str = "\x1b[0m";

#[derive(Debug, Clone, Copy, Serialize)]
pub enum GameCellContent {
	Linemate(u16),
	Deraumere(u16),
	Sibur(u16),
	Mendiane(u16),
	Phiras(u16),
	Thystame(u16),
	Player(u16),
	Food(u16),
	Egg(u16)
}

impl PartialEq for GameCellContent {
	fn eq(&self, other: &Self) -> bool {
		match (self, other) {
			(Linemate(_), Linemate(_)) => true,
			(Deraumere(_), Deraumere(_)) => true,
			(Sibur(_), Sibur(_)) => true,
			(Mendiane(_), Mendiane(_)) => true,
			(Phiras(_), Phiras(_)) => true,
			(Thystame(_), Thystame(_)) => true,
			(Player(_), Player(_)) => true,
			(Food(_), Food(_)) => true,
			(Egg(_), Egg(_)) => true,
			(_, _) => false
		}
	}
}

impl GameCellContent {
	/// Returns the amount of the current 
	pub fn amount(&self) -> u16 {
		match self {
			Linemate(x)
			| Deraumere(x)
			| Sibur(x)
			| Mendiane(x)
			| Phiras(x)
			| Thystame(x)
			| Player(x)
			| Food(x)
			| Egg(x) => *x,
		}
	}

	pub fn remove(&mut self, amount: u16) {
		match self {
			Linemate(x)
			| Deraumere(x)
			| Sibur(x)
			| Mendiane(x)
			| Phiras(x)
			| Thystame(x)
			| Player(x)
			| Food(x)
			| Egg(x) => {
				if *x <= amount {
					*x = 0;
				} else {
					*x -= amount;
				}
			}
		}
	}

	pub fn add(&mut self, amount: u16) {
		match self {
			Linemate(x)
			| Deraumere(x)
			| Sibur(x)
			| Mendiane(x)
			| Phiras(x)
			| Thystame(x)
			| Player(x)
			| Food(x)
			| Egg(x) => {
				if *x as u32 + amount as u32 >= u16::MAX.into() {
					*x = u16::MAX;
				} else {
					*x += amount;
				}
			}
		}
	}

	pub fn eq_amount(&self, other: &Self) -> bool {
		self == other && self.amount() == other.amount()
	}
}

#[derive(Debug, Clone, Default, PartialEq, Copy, Serialize)]
pub struct GamePosition {
	pub x: u8,
	pub y: u8,
}

#[derive(Debug, Clone, Default, PartialEq, Copy, Serialize)]
pub struct GamePositionDiff {
	pub x: i16,
	pub y: i16,
}

#[derive(Debug, Clone, Default, Serialize)]
pub struct GameCell {
	pub position: GamePosition,
	pub content: Vec<GameCellContent>
}

impl Display for GameCell {
	fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
		let mvp = self.mvp();
		let color: &str = match mvp {
			Player(_) => PLAYER_COLOR,
			Linemate(_) => LINEMATE_COLOR,
			Deraumere(_) => DERAUMERE_COLOR,
			Sibur(_) => SIBUR_COLOR,
			Mendiane(_) => MENDIANE_COLOR,
			Phiras(_) => PHIRAS_COLOR,
			Thystame(_) => THYSTAME_COLOR,
			Food(_) => FOOD_COLOR,
			Egg(_) => EGG_COLOR,
		};
		let amout_str: &str = match mvp.amount() {
			0 => "\x1b[42;90m.",
			1 => "1",
			2 => "2",
			3 => "3",
			4 => "4",
			5 => "5",
			6 => "6",
			7 => "7",
			8 => "8",
			9 => "9",
			_ => "+",
		};
		write!(f, "{color}{amout_str}")
	}
}

impl GameCell {
	pub fn empty() -> Self {
		GameCell {
			position: GamePosition {
				x: 0,
				y: 0,
			},
			content: vec![
				Linemate(0),
				Deraumere(0),
				Sibur(0),
				Mendiane(0),
				Phiras(0),
				Thystame(0),
				Player(0),
				Food(0)
			],
		}
	}

	pub fn remove_content(&mut self, to_rm: GameCellContent) -> bool {
		for i in 0..self.content.len() {
			if self.content[i] == to_rm && self.content[i].amount() > 0 {
				self.content[i].remove(to_rm.amount());
				return true;
			}
		}
		false
	}

	pub fn add_content(&mut self, to_add: GameCellContent) -> bool {
		for i in 0..self.content.len() {
			if self.content[i] == to_add {
				self.content[i].add(to_add.amount());
				return true;
			}
		}
		false
	}

	pub fn get_content(&self, to_get: GameCellContent)
		-> Option<GameCellContent> {
		for i in 0..self.content.len() {
			if self.content[i] == to_get {
				return Some(self.content[i]);
			}
		}
		None
	}

	/// Removes the empty contents
	pub fn purify(&mut self) {
		let mut new_content: Vec<GameCellContent> = vec![];
		
		for x in &self.content {
			if x.amount() > 0 {
				new_content.push(*x);
			}
		}

		self.content = new_content;
	}
	
	pub fn mvp(&self) -> GameCellContent {
		let mut linemate_amout: u16 = 0;
		let mut deraumere_amout: u16 = 0;
		let mut sibur_amout: u16 = 0;
		let mut mendiane_amout: u16 = 0;
		let mut phiras_amout: u16 = 0;
		let mut thystame_amout: u16 = 0;
		let mut player_amout: u16 = 0;
		let mut food_amout: u16 = 0;
		let mut egg_amout: u16 = 0;
	
		for i in 0..self.content.len() {
			match self.content[i] {
				Linemate(x) => linemate_amout = x,
				Deraumere(x) => deraumere_amout = x,
				Sibur(x) => sibur_amout = x,
				Mendiane(x) => mendiane_amout = x,
				Phiras(x) => phiras_amout = x,
				Thystame(x) => thystame_amout = x,
				Player(x) => player_amout = x,
				Food(x) => food_amout = x,
				Egg(x) => egg_amout = x,
			}
		};

		if player_amout > 0 {
			return Player(player_amout);
		}
		if egg_amout > 0 {
			return Egg(egg_amout);
		}
		if thystame_amout > 0 {
			return Thystame(thystame_amout);
		}
		if phiras_amout > 0 {
			return Phiras(phiras_amout);
		}
		if mendiane_amout > 0 {
			return Mendiane(mendiane_amout);
		}
		if sibur_amout > 0 {
			return Sibur(sibur_amout);
		}
		if deraumere_amout > 0 {
			return Deraumere(deraumere_amout);
		}
		if linemate_amout > 0 {
			return Linemate(linemate_amout);
		}
		Food(food_amout)
	}

	pub fn diff_content(&self, new: &Self) -> Option<SendCell> {
		if new.content.len() != self.content.len() {
			return Some(SendCell::from(new));
		}
		for i in 0..new.content.len() {
			if !self.content[i].eq_amount(&new.content[i]) {
				return Some(SendCell::from(new));
			}
		}
		None
	}
}

impl PartialEq for GameCell {
	fn eq(&self, other: &Self) -> bool {
		if self.content == other.content
			&& self.position == other.position {
			return true;
		}
		false
	}
}

#[derive(Debug, Serialize, Clone)]
pub struct GameMap {
	pub max_position: GamePosition,
	pub cells: Vec<Vec<GameCell>>,
}

impl Display for GameMap {
	fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
		let mut end_str = format!("Dimentions: X:{} Y:{}\n", self.max_position.x, self.max_position.y);
	
		for y in 0..self.cells[0].len() {
			for x in 0..self.cells.len() {
				end_str = format!("{end_str}{}", self.cells[x][y]);
			}
			end_str += RESET;
			end_str += "\n";
		}
		write!(f, "{}", end_str)
	}
}

impl GameMap {
	pub fn new(x: u8, y: u8, teams: u8, clients: u8, seed: usize) -> (Self, VecDeque<GamePosition>) {
		let mut cells = vec![vec![GameCell::empty(); y.into()]; x.into()];
		let mut rng = StdRng::seed_from_u64(seed as u64);
		let before_map = Instant::now();

		for vec_x in 0..cells.len() {
			for vec_y in 0..cells[0].len() {
				cells[vec_x][vec_y].position = GamePosition {
					x: vec_x as u8,
					y: vec_y as u8,
				};
			}
		}

		let player_positions = Self::place_ressources(&mut cells,
			&mut rng,
			x, y,
			teams,
			clients);

		println!("Time to create the map: {:?}", Instant::now() - before_map);
		(GameMap {
			cells,
			max_position: GamePosition {
				x,
				y,
			}
		},
		player_positions)
	}

	fn place_ressources(
		cells: &mut [Vec<GameCell>],
		rng: &mut StdRng,
		x: u8,
		y: u8,
		nb_of_team: u8,
		clients: u8) -> VecDeque<GamePosition> {
		let mut interest_points = vec![
			GamePosition::default();
			(1 + rng.next_u32() % 2 + (x > 80) as u32 + (y > 55) as u32) as usize
		];
		let start = GamePosition {
			x: rand_u8(rng) % x,
			y: rand_u8(rng) % y,
		};
		let mut player_positions: VecDeque<GamePosition> = VecDeque::new();

		for point_number in 0..interest_points.len() {
			interest_points[point_number] = GamePosition {
				x: rand_u8(rng) % x,
				y: rand_u8(rng) % y,
			};
		}

		let mut max: Vec<GameCellContent> = vec![
			Linemate(9 * nb_of_team as u16),
			Deraumere(7 * nb_of_team as u16 + 5),
			Sibur(8 * nb_of_team as u16),
			Mendiane(3 * nb_of_team as u16 + 3),
			Phiras(6 * nb_of_team as u16 + 15),
			Thystame(nb_of_team as u16 + 3),
			Food(min(u16::MAX as u32, 25 *
				(x as u32 * y as u32) / 30 *
				((nb_of_team / 3) + 1) as u32 + 2000) as u16),
			Player((nb_of_team * clients) as u16),
		];

		fn everything_placed(max: &Vec<GameCellContent>) -> bool {
			for item in max {
				if item.amount() > 0 {
					return false;
				}
			};
			true
		}

		while !everything_placed(&max) {
			for vecx in 0..cells.len() {
				for vecy in 0..cells[0].len() {
					let current_cell = &mut cells
						[move_to_pos(x, vecx as u8, start.x as i16)]
						[move_to_pos(y, vecy as u8, start.y as i16)];
					Self::place_single_ressource(&interest_points,
						rng,
						current_cell,
						&mut max[THYSTAME_INDEX],
						&GamePosition { x, y },
					);
					Self::place_single_ressource(&interest_points,
						rng,
						current_cell,
						&mut max[PHIRAS_INDEX],
						&GamePosition { x, y },
					);
					Self::place_single_ressource(&interest_points,
						rng,
						current_cell,
						&mut max[MENDIANE_INDEX],
						&GamePosition { x, y },
					);
					Self::place_single_ressource(&interest_points,
						rng,
						current_cell,
						&mut max[SIBUR_INDEX],
						&GamePosition { x, y },
					);
					Self::place_single_ressource(&interest_points,
						rng,
						current_cell,
						&mut max[DERAUMERE_INDEX],
						&GamePosition { x, y },
					);
					Self::place_single_ressource(&interest_points,
						rng,
						current_cell,
						&mut max[LINEMATE_INDEX],
						&GamePosition { x, y },
					);
					Self::place_single_ressource(&interest_points,
						rng,
						current_cell,
						&mut max[FOOD_INDEX],
						&GamePosition { x, y },
					);
					if let Some(pos) = Self::place_player(&interest_points,
						&mut max[PLAYER_INDEX],
						&GamePosition { x, y },
						rng,
						current_cell) {
						player_positions.push_back(pos);
					}
				}
			}
		};
		player_positions
	}

	pub fn regenerate_ressources(&mut self,
		rng: &mut StdRng,
		x: u8,
		y: u8) {
		let mut interest_points = vec![
			GamePosition::default();
			(1 + rng.next_u32() % 2 + (x > 80) as u32 + (y > 55) as u32) as usize
		];
		let start = GamePosition {
			x: rand_u8(rng) % x,
			y: rand_u8(rng) % y,
		};

		for point_number in 0..interest_points.len() {
			interest_points[point_number] = GamePosition {
				x: rand_u8(rng) % x,
				y: rand_u8(rng) % y,
			};
		}

		let mut max: Vec<GameCellContent> = vec![
			Linemate(10),
			Deraumere(9),
			Sibur(8),
			Mendiane(7),
			Phiras(5),
			Thystame(3),
			Food(TURN_TO_REGENERATE as u16 * (8 + (rand_u8(rng) % 5)) as u16), // enough food for 8~13 players
		];

		fn everything_placed(max: &Vec<GameCellContent>) -> bool {
			for item in max {
				if item.amount() > 0 {
					return false;
				}
			};
			true
		}

		while !everything_placed(&max) {
			for vecx in 0..self.cells.len() {
				for vecy in 0..self.cells[0].len() {
					let current_cell = &mut self.cells
						[move_to_pos(x, vecx as u8, start.x as i16)]
						[move_to_pos(y, vecy as u8, start.y as i16)];
					Self::place_single_ressource(&interest_points,
						rng,
						current_cell,
						&mut max[THYSTAME_INDEX],
						&GamePosition { x, y },
					);
					Self::place_single_ressource(&interest_points,
						rng,
						current_cell,
						&mut max[PHIRAS_INDEX],
						&GamePosition { x, y },
					);
					Self::place_single_ressource(&interest_points,
						rng,
						current_cell,
						&mut max[MENDIANE_INDEX],
						&GamePosition { x, y },
					);
					Self::place_single_ressource(&interest_points,
						rng,
						current_cell,
						&mut max[SIBUR_INDEX],
						&GamePosition { x, y },
					);
					Self::place_single_ressource(&interest_points,
						rng,
						current_cell,
						&mut max[DERAUMERE_INDEX],
						&GamePosition { x, y },
					);
					Self::place_single_ressource(&interest_points,
						rng,
						current_cell,
						&mut max[LINEMATE_INDEX],
						&GamePosition { x, y },
					);
					Self::place_single_ressource(&interest_points,
						rng,
						current_cell,
						&mut max[FOOD_INDEX],
						&GamePosition { x, y },
					);
				}
			}
		};
	}

	fn place_single_ressource(
		ipts: &[GamePosition],
		rng: &mut StdRng,
		curr: &mut GameCell,
		to_place: &mut GameCellContent,
		max_pos: &GamePosition
	) {
		if to_place.amount() == 0 {
			return;
		}
		match to_place {
			Linemate(_) => Self::place_linemate(ipts, to_place, max_pos, rng, curr),
			Deraumere(_) => Self::place_deraumere(ipts, to_place, max_pos, rng, curr),
			Sibur(_) => Self::place_sibur(ipts, to_place, max_pos, rng, curr),
			Mendiane(_) => Self::place_mendiane(ipts, to_place, max_pos, rng, curr),
			Phiras(_) => Self::place_phiras(ipts, to_place, max_pos, rng, curr),
			Thystame(_) => Self::place_thystame(ipts, to_place, max_pos, rng, curr),
			Food(_) => Self::place_food(ipts, to_place, max_pos, rng, curr),
			_ => {}
		}
	}

	fn place_thystame(
			interest_points: &[GamePosition],
			to_place: &mut GameCellContent,
			max_position: &GamePosition,
			rng: &mut StdRng,
			current_cell: &mut GameCell
		) {
		let mut nb_to_place = ((rng.next_u32() % 32) == 1) as u16;
		if nb_to_place > to_place.amount() {
			nb_to_place = to_place.amount()
		}
		let start_interest_point_index = rng.next_u32();
		if current_cell.content.contains(&Thystame(0)) &&
			nb_to_place > 0 {
			for i in 0..interest_points.len() {
				if Self::is_in_range_of_interest_point(
					&current_cell.position,
					&interest_points[(start_interest_point_index as usize + i) % interest_points.len()],
					max_position,
					0,
					1) {
						to_place.remove(nb_to_place);
						current_cell.add_content(Thystame(nb_to_place));
						break;
				}
			}
		}
	}

	fn place_phiras(
		interest_points: &[GamePosition],
		to_place: &mut GameCellContent,
		max_position: &GamePosition,
		rng: &mut StdRng,
		current_cell: &mut GameCell
	) {
		let mut nb_to_place = ((rng.next_u32() % 24) == 1) as u16;
		if nb_to_place > to_place.amount() {
			nb_to_place = to_place.amount()
		}
		let start_interest_point_index = rng.next_u32();
		if current_cell.content.contains(&Phiras(0)) &&
			nb_to_place > 0 {
			for i in 0..interest_points.len() {
				if Self::is_in_range_of_interest_point(
					&current_cell.position,
					&interest_points[(start_interest_point_index as usize + i) % interest_points.len()],
					max_position,
					1,
					3) {
						to_place.remove(nb_to_place);
						current_cell.add_content(Phiras(nb_to_place));
						break;
				}
			}
		}
	}

	fn place_mendiane(
		interest_points: &[GamePosition],
		to_place: &mut GameCellContent,
		max_position: &GamePosition,
		rng: &mut StdRng,
		current_cell: &mut GameCell
	) {
		let mut nb_to_place = ((rng.next_u32() % 24) == 1) as u16;
		if nb_to_place > to_place.amount() {
			nb_to_place = to_place.amount()
		}
		let start_interest_point_index = rng.next_u32();
		if current_cell.content.contains(&Mendiane(0)) &&
			nb_to_place > 0 {
			for i in 0..interest_points.len() {
				if Self::is_in_range_of_interest_point(
					&current_cell.position,
					&interest_points[(start_interest_point_index as usize + i) % interest_points.len()],
					max_position,
					3,
					7) {
						to_place.remove(nb_to_place);
						current_cell.add_content(Mendiane(nb_to_place));
						break;
				}
			}
		}
	}

	fn place_sibur(
		interest_points: &[GamePosition],
		to_place: &mut GameCellContent,
		max_position: &GamePosition,
		rng: &mut StdRng,
		current_cell: &mut GameCell
	) {
		let mut nb_to_place = ((rng.next_u32() % 24) == 1) as u16;
		if nb_to_place > to_place.amount() {
			nb_to_place = to_place.amount()
		}
		let start_interest_point_index = rng.next_u32();
		if current_cell.content.contains(&Sibur(0)) &&
			nb_to_place > 0 {
			for i in 0..interest_points.len() {
				if Self::is_in_range_of_interest_point(
					&current_cell.position,
					&interest_points[(start_interest_point_index as usize + i) % interest_points.len()],
					max_position,
					7,
					10) {
						to_place.remove(nb_to_place);
						current_cell.add_content(Sibur(nb_to_place));
						break;
				}
			}
		}
	}

	fn place_deraumere(
		interest_points: &[GamePosition],
		to_place: &mut GameCellContent,
		max_position: &GamePosition,
		rng: &mut StdRng,
		current_cell: &mut GameCell
	) {
		let mut nb_to_place = ((rng.next_u32() % 24) == 1) as u16;
		if nb_to_place > to_place.amount() {
			nb_to_place = to_place.amount()
		}
		let start_interest_point_index = rng.next_u32();
		if current_cell.content.contains(&Deraumere(0)) &&
			nb_to_place > 0 {
			for i in 0..interest_points.len() {
				if Self::is_in_range_of_interest_point(
					&current_cell.position,
					&interest_points[(start_interest_point_index as usize + i) % interest_points.len()],
					max_position,
					8,
					12) {
						to_place.remove(nb_to_place);
						current_cell.add_content(Deraumere(nb_to_place));
						break;
				}
			}
		}
	}

	fn place_linemate(
		interest_points: &[GamePosition],
		to_place: &mut GameCellContent,
		max_position: &GamePosition,
		rng: &mut StdRng,
		current_cell: &mut GameCell
	) {
		let mut nb_to_place = ((rng.next_u32() % 24) == 1) as u16;
		if nb_to_place > to_place.amount() {
			nb_to_place = to_place.amount()
		}
		let start_interest_point_index = rng.next_u32();
		if current_cell.content.contains(&Linemate(0)) &&
			nb_to_place > 0 {
			for i in 0..interest_points.len() {
				if Self::is_in_range_of_interest_point(
					&current_cell.position,
					&interest_points[(start_interest_point_index as usize + i) % interest_points.len()],
					max_position,
					9,
					14) {
						to_place.remove(nb_to_place);
						current_cell.add_content(Linemate(nb_to_place));
						break;
				}
			}
		}
	}

	fn place_food(
		interest_points: &[GamePosition],
		to_place: &mut GameCellContent,
		max_position: &GamePosition,
		rng: &mut StdRng,
		current_cell: &mut GameCell
	) {
		let mut nb_to_place = ((rng.next_u32() % 15) == 1) as u16;
		if nb_to_place > to_place.amount() {
			nb_to_place = to_place.amount()
		}
		let start_interest_point_index = rng.next_u32();
		if current_cell.content.contains(&Food(0)) &&
			nb_to_place > 0 {
			for i in 0..interest_points.len() {
				if Self::is_in_range_of_interest_point(
					&current_cell.position,
					&interest_points[(start_interest_point_index as usize + i) % interest_points.len()],
					max_position,
					10,
					35) {
						to_place.remove(nb_to_place);
						current_cell.add_content(Food(nb_to_place));
						break;
				}
			}
		}
	}

	fn place_player(
		interest_points: &[GamePosition],
		to_place: &mut GameCellContent,
		max_position: &GamePosition,
		rng: &mut StdRng,
		current_cell: &mut GameCell
	) -> Option<GamePosition> {
		let mut nb_to_place = ((rng.next_u32() % 150) == 1) as u16;
		if nb_to_place > to_place.amount() {
			nb_to_place = to_place.amount()
		}
		let start_interest_point_index = rng.next_u32();
		if current_cell.content.contains(&Player(0)) &&
			nb_to_place > 0 {
			for i in 0..interest_points.len() {
				if Self::is_in_range_of_interest_point(
					&current_cell.position,
					&interest_points[(start_interest_point_index as usize + i) % interest_points.len()],
					max_position,
					15,
					25) {
						to_place.remove(nb_to_place);
						current_cell.add_content(Player(nb_to_place));
						return Some(current_cell.position);
				}
			}
		}
		None
	}

	fn is_in_range_of_interest_point(
		my_position: &GamePosition,
		interest_point: &GamePosition,
		max_position: &GamePosition,
		min: u8,
		max: u8)
		-> bool {
		let distance = Self::distance(interest_point, my_position, max_position);
		if distance >= min as u16 && distance <= max as u16 {
			return true;
		}
		false
	}

	fn distance(
		current: &GamePosition,
		other: &GamePosition,
		max_position: &GamePosition,
	) -> u16 {
		let dist_x = min(
			(current.x as i16 - other.x as i16).abs(),
			current.x as i16 + (max_position.x as i16 - other.x as i16),
		);
		let dist_y = min(
			(current.y as i16 - other.y as i16).abs(),
			current.y as i16 + (max_position.y as i16 - other.y as i16),
		);

		(dist_x + dist_y) as u16
	}

	pub fn voir_data(&self,
		pos: GamePosition,
		direction: PlayerDirection,
		level: u8) -> String {
		let mut interest: Vec<GameCell> = vec![];
	
		match direction {
			PlayerDirection::North => {
				for y in 0..=level as i16 {
					for x in -y..=y {
						interest.push(self.cells[move_to_pos(self.max_position.x, pos.x, x)]
									[move_to_pos(self.max_position.y, pos.y, -y)]
									.clone())
					}
				}
			}
			PlayerDirection::South => {
				for y in 0..=level as i16 {
					for x in -y..=y {
						interest.push(self.cells[move_to_pos(self.max_position.x, pos.x, x)]
									[move_to_pos(self.max_position.y, pos.y, y)]
									.clone())
					}
				}
			}
			PlayerDirection::West => {
				for x in 0..=level as i16 {
					for y in -x..=x {
						interest.push(self.cells[move_to_pos(self.max_position.x, pos.x, -x)]
									[move_to_pos(self.max_position.y, pos.y, y)]
									.clone())
					}
				}
			}
			PlayerDirection::East => {
				for x in 0..=level as i16 {
					for y in -x..=x {
						interest.push(self.cells[move_to_pos(self.max_position.x, pos.x, x)]
									[move_to_pos(self.max_position.y, pos.y, y)]
									.clone())
					}
				}
			}
		}
		
		if interest.len() > 0 {
			interest[0].remove_content(Player(1));
		}
		let variable = interest.into_iter().map(|cell| SendCell::from(cell)).collect::<Vec<SendCell>>();
		
		serde_json::to_string(&variable).unwrap() + "\n"
	}
	
	pub fn send_map(&self, fd: i32) {
		let mut new_cells = self.cells.clone();
		let mut cells_to_send: Vec<Vec<SendCell>> = vec![vec![
			SendCell {
				p: GamePosition {
					x: 0,
					y: 0
				},
				c: vec![],
			}; self.max_position.y as usize
		]; self.max_position.x as usize];

		for x in 0..new_cells.len() {
			for y in 0..new_cells[0].len() {
				new_cells[x][y].purify();
				cells_to_send[x][y] = SendCell::from(&new_cells[x][y]);
			}
		}

		let splitted = (serde_json::to_string(&cells_to_send).unwrap() + "\x04")
								.chars()
								.collect::<Vec<char>>()
								.chunks(4096)
								.map(|c| c.iter().collect::<String>())
								.collect::<Vec<String>>();

		for chunk in splitted {
			send_to(fd, chunk.as_str());
		}

		println!("GUI connected.");
	}

	pub fn get_cell(&self, x: u8, y: u8) -> Option<&GameCell> {
		if x > self.max_position.x || y > self.max_position.y {
			return None
		}
		Some(&self.cells[x as usize][y as usize])
	}

	pub fn get_cell_mut(&mut self, x: u8, y: u8) -> Option<&mut GameCell> {
		if x > self.max_position.x || y > self.max_position.y {
			return None
		}
		Some(&mut self.cells[x as usize][y as usize])
	}

	pub fn add_content_cell(&mut self, pos: GamePosition, content: GameCellContent)
		-> bool {
		let current_cell = &mut self.get_cell_mut(pos.x, pos.y).unwrap();
	
		current_cell.add_content(content)
	}

	pub fn remove_content_cell(&mut self, pos: GamePosition, content: GameCellContent)
		-> bool {
		let current_cell = &mut self.get_cell_mut(pos.x, pos.y).unwrap();
	
		current_cell.remove_content(content)
	}

	pub fn comes_from(&self, a: GamePosition, b: GamePosition, direction: PlayerDirection) -> u8 {
		let shortest = GamePositionDiff {
			x: b.x as i16 - a.x as i16,
			y: b.y as i16 - a.y as i16,
		};
		
		if a == b {
			return 0;
		}

		let mut angle = f64::atan2(f64::from(shortest.y), f64::from(shortest.x)).to_degrees();

		match direction {
			PlayerDirection::North => {},
			PlayerDirection::South => angle += 180_f64,
			PlayerDirection::East => angle += 270_f64,
			PlayerDirection::West => angle += 90_f64,
		}

		match (angle as i32 + 360) % 360 {
			0..=22 | 338..=360 => 7,
			23..=67 => 6,
			68..=112 => 5,
			113..=157 => 4,
			158..=202 => 3,
			203..=247 => 2,
			248..=292 => 1,
			293..=337 => 8,
			_ => unreachable!()
		}
	}
}

#[derive(Clone, Serialize)]
pub struct SendCell {
	p: GamePosition,
	c: Vec<GameCellContent>
}

impl From<GameCell> for SendCell {
	fn from(mut value: GameCell) -> Self {
		value.purify();
		SendCell {
			p: value.position,
			c: value.content,
		}
	}
}

impl From<&GameCell> for SendCell {
	fn from(value: &GameCell) -> Self {
		let mut purified = value.clone();
		purified.purify();
		SendCell {
			p: purified.position,
			c: purified.content,
		}
	}
}

fn rand_u8(rng: &mut StdRng) -> u8 {
	(rng.next_u32() / DEVIDE_U32_TO_U8) as u8
}

/// Gives the position after moving `movement` cells
/// 
/// pos_max: maximal position (args.x for x axis)<br/>
/// pos: current position<br/>
/// movement: The amount to move, negative to go the other way
pub fn move_to_pos(pos_max: u8, pos: u8, movement: i16) -> usize {
	(pos as i16 + movement).rem_euclid(pos_max as i16) as usize
}