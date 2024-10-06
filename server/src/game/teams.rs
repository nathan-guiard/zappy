/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   teams.rs                                           :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/20 11:16:22 by nguiard           #+#    #+#             */
/*   Updated: 2024/10/02 15:14:36 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

use super::map::GamePosition;
use std::collections::VecDeque;

const MAX_PLAYER_PER_TEAM: u8 = 16;

#[derive(Debug)]
pub struct Team {
	pub name: String,
	pub max_level: u8,
	next_posititons: VecDeque<GamePosition>,
	pub lost: bool,
	pub current_player_count: u8,
}

impl Team {
	pub fn new(name: String) -> Self {
		Self {
			name,
			max_level: 0,
			next_posititons: VecDeque::new(),
			lost: false,
			current_player_count: 0,
		}
	}

	pub fn available_connections(&self) -> usize {
		self.next_posititons.len()
	}

	pub fn get_next_position(&mut self) -> Option<GamePosition> {
		self.next_posititons.pop_front()
	}

	pub fn add_position(&mut self, position: GamePosition) {
		self.next_posititons.push_back(position)
	}

	pub fn slot_available(&self) -> bool {
		if self.current_player_count >= MAX_PLAYER_PER_TEAM {
			false
		} else {
			true
		}
	}
}