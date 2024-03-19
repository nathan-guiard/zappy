/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   level_up.rs                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/19 17:20:38 by nguiard           #+#    #+#             */
/*   Updated: 2024/03/19 18:33:57 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

use super::map::GameCellContent;
use super::map::GameCellContent::*;
use super::player::Player;

pub fn has_enough_ressources(inventory: &[GameCellContent],
	level: u8,
	nb_of_same_lvl: u8) -> bool {
	match level {
		1 => enough_level1(inventory, nb_of_same_lvl),
		2 => enough_level2(inventory, nb_of_same_lvl),
		3 => enough_level3(inventory, nb_of_same_lvl),
		4 => enough_level4(inventory, nb_of_same_lvl),
		5 => enough_level5(inventory, nb_of_same_lvl),
		6 => enough_level6(inventory, nb_of_same_lvl),
		7 => enough_level7(inventory, nb_of_same_lvl),
		_ => false
	}
}

pub fn remove_ressources(player: &mut Player) {
	match player.level {
		1 => {
			player.remove_from_inventory(Linemate(1));
		}
		2 => {
			player.remove_from_inventory(Linemate(1));
			player.remove_from_inventory(Deraumere(1));
			player.remove_from_inventory(Sibur(1));
		}
		3 => {
			player.remove_from_inventory(Linemate(2));
			player.remove_from_inventory(Sibur(1));
			player.remove_from_inventory(Phiras(2));
		}
		4 => {
			player.remove_from_inventory(Linemate(1));
			player.remove_from_inventory(Deraumere(1));
			player.remove_from_inventory(Sibur(2));
			player.remove_from_inventory(Phiras(1));
		}
		5 => {
			player.remove_from_inventory(Linemate(1));
			player.remove_from_inventory(Deraumere(2));
			player.remove_from_inventory(Sibur(1));
			player.remove_from_inventory(Mendiane(3));
		}
		6 => {
			player.remove_from_inventory(Linemate(1));
			player.remove_from_inventory(Deraumere(2));
			player.remove_from_inventory(Sibur(3));
			player.remove_from_inventory(Phiras(1));
		}
		7 => {
			player.remove_from_inventory(Linemate(2));
			player.remove_from_inventory(Deraumere(2));
			player.remove_from_inventory(Sibur(2));
			player.remove_from_inventory(Mendiane(2));
			player.remove_from_inventory(Phiras(2));
			player.remove_from_inventory(Thystame(1));
		}
		_ => {},
	}
} 


fn enough_level1(inventory: &[GameCellContent], nb_of_same_lvl: u8) -> bool {
	let mut enough_linemate = false;

	if nb_of_same_lvl < 1 {
		return false;
	}
	for x in inventory {
		if x == &Linemate(0) {
			enough_linemate = x.amount() >= 1;
		}
	}
	enough_linemate
}

fn enough_level2(inventory: &[GameCellContent], nb_of_same_lvl: u8) -> bool {
	let mut enough_linemate = false;
	let mut enough_deraumere = false;

	if nb_of_same_lvl < 2 {
		return false;
	}
	for x in inventory {
		if x == &Linemate(0) {
			enough_linemate = x.amount() >= 1;
		}
		if x == &Deraumere(0) {
			enough_deraumere = x.amount() >= 1;
		}
	}
	enough_linemate && enough_deraumere
}

fn enough_level3(inventory: &[GameCellContent], nb_of_same_lvl: u8) -> bool {
	let mut enough_linemate = false;
	let mut enough_sibur = false;
	let mut enough_phiras = false;

	if nb_of_same_lvl < 2 {
		return false;
	}
	for x in inventory {
		if x == &Linemate(0) {
			enough_linemate = x.amount() >= 2;
		}
		if x == &Sibur(0) {
			enough_sibur = x.amount() >= 1;
		}
		if x == &Phiras(0) {
			enough_phiras = x.amount() >= 2;
		}
	}
	enough_linemate && enough_sibur && enough_phiras
}

fn enough_level4(inventory: &[GameCellContent], nb_of_same_lvl: u8) -> bool {
	let mut enough_linemate = false;
	let mut enough_sibur = false;
	let mut enough_phiras = false;
	let mut enough_deraumere = false;

	if nb_of_same_lvl < 4 {
		return false;
	}
	for x in inventory {
		if x == &Linemate(0) {
			enough_linemate = x.amount() >= 1;
		}
		if x == &Deraumere(0) {
			enough_deraumere = x.amount() >= 1;
		}
		if x == &Sibur(0) {
			enough_sibur = x.amount() >= 2;
		}
		if x == &Phiras(0) {
			enough_phiras = x.amount() >= 1;
		}
	}
	enough_linemate && enough_sibur && enough_phiras && enough_deraumere
}

fn enough_level5(inventory: &[GameCellContent], nb_of_same_lvl: u8) -> bool {
	let mut enough_linemate = false;
	let mut enough_sibur = false;
	let mut enough_mendiane = false;
	let mut enough_deraumere = false;

	if nb_of_same_lvl < 4 {
		return false;
	}
	for x in inventory {
		if x == &Linemate(0) {
			enough_linemate = x.amount() >= 1;
		}
		if x == &Deraumere(0) {
			enough_deraumere = x.amount() >= 2;
		}
		if x == &Sibur(0) {
			enough_sibur = x.amount() >= 1;
		}
		if x == &Mendiane(0) {
			enough_mendiane = x.amount() >= 3;
		}
	}
	enough_linemate && enough_sibur && enough_mendiane && enough_deraumere
}

fn enough_level6(inventory: &[GameCellContent], nb_of_same_lvl: u8) -> bool {
	let mut enough_linemate = false;
	let mut enough_sibur = false;
	let mut enough_phiras = false;
	let mut enough_deraumere = false;

	if nb_of_same_lvl < 6 {
		return false;
	}
	for x in inventory {
		if x == &Linemate(0) {
			enough_linemate = x.amount() >= 1;
		}
		if x == &Deraumere(0) {
			enough_deraumere = x.amount() >= 2;
		}
		if x == &Sibur(0) {
			enough_sibur = x.amount() >= 3;
		}
		if x == &Phiras(0) {
			enough_phiras = x.amount() >= 1;
		}
	}
	enough_linemate && enough_sibur && enough_phiras && enough_deraumere
}

fn enough_level7(inventory: &[GameCellContent], nb_of_same_lvl: u8) -> bool {
	let mut enough_linemate = false;
	let mut enough_sibur = false;
	let mut enough_phiras = false;
	let mut enough_deraumere = false;
	let mut enough_mendiane = false;
	let mut enough_thystame = false;

	if nb_of_same_lvl < 6 {
		return false;
	}
	for x in inventory {
		if x == &Linemate(0) {
			enough_linemate = x.amount() >= 2;
		}
		if x == &Deraumere(0) {
			enough_deraumere = x.amount() >= 2;
		}
		if x == &Sibur(0) {
			enough_sibur = x.amount() >= 2;
		}
		if x == &Mendiane(0) {
			enough_mendiane = x.amount() >= 2;
		}
		if x == &Phiras(0) {
			enough_phiras = x.amount() >= 2;
		}
		if x == &Thystame(0) {
			enough_thystame = x.amount() >= 1;
		}
	}
	enough_linemate && enough_sibur && enough_phiras &&
	enough_deraumere && enough_mendiane && enough_thystame
}