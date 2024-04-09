/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   level_up.rs                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/19 17:20:38 by nguiard           #+#    #+#             */
/*   Updated: 2024/04/09 11:39:43 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

use super::map::{GameCell, GameCellContent};
use super::map::GameCellContent::*;

pub fn has_enough_ressources(ressources: &[GameCellContent],
	level: u8,
	nb_of_same_lvl: u8) -> bool {
	match level {
		1 => enough_level1(ressources, nb_of_same_lvl),
		2 => enough_level2(ressources, nb_of_same_lvl),
		3 => enough_level3(ressources, nb_of_same_lvl),
		4 => enough_level4(ressources, nb_of_same_lvl),
		5 => enough_level5(ressources, nb_of_same_lvl),
		6 => enough_level6(ressources, nb_of_same_lvl),
		7 => enough_level7(ressources, nb_of_same_lvl),
		_ => false
	}
}

pub fn remove_ressources(cell: &mut GameCell, level: u8) {
	match level {
		1 => {
			cell.remove_content(Linemate(1));
		}
		2 => {
			cell.remove_content(Linemate(1));
			cell.remove_content(Deraumere(1));
			cell.remove_content(Sibur(1));
		}
		3 => {
			cell.remove_content(Linemate(2));
			cell.remove_content(Sibur(1));
			cell.remove_content(Phiras(2));
		}
		4 => {
			cell.remove_content(Linemate(1));
			cell.remove_content(Deraumere(1));
			cell.remove_content(Sibur(2));
			cell.remove_content(Phiras(1));
		}
		5 => {
			cell.remove_content(Linemate(1));
			cell.remove_content(Deraumere(2));
			cell.remove_content(Sibur(1));
			cell.remove_content(Mendiane(3));
		}
		6 => {
			cell.remove_content(Linemate(1));
			cell.remove_content(Deraumere(2));
			cell.remove_content(Sibur(3));
			cell.remove_content(Phiras(1));
		}
		7 => {
			cell.remove_content(Linemate(2));
			cell.remove_content(Deraumere(2));
			cell.remove_content(Sibur(2));
			cell.remove_content(Mendiane(2));
			cell.remove_content(Phiras(2));
			cell.remove_content(Thystame(1));
		}
		_ => {},
	}
} 

fn enough_level1(ressources: &[GameCellContent], nb_of_same_lvl: u8) -> bool {
	let mut enough_linemate = false;

	if nb_of_same_lvl < 1 {
		return false;
	}
	for x in ressources {
		if x == &Linemate(0) {
			enough_linemate = x.amount() >= 1;
		}
	}
	enough_linemate
}

fn enough_level2(ressources: &[GameCellContent], nb_of_same_lvl: u8) -> bool {
	let mut enough_linemate = false;
	let mut enough_deraumere = false;

	if nb_of_same_lvl < 2 {
		return false;
	}
	for x in ressources {
		if x == &Linemate(0) {
			enough_linemate = x.amount() >= 1;
		}
		if x == &Deraumere(0) {
			enough_deraumere = x.amount() >= 1;
		}
	}
	enough_linemate && enough_deraumere
}

fn enough_level3(ressources: &[GameCellContent], nb_of_same_lvl: u8) -> bool {
	let mut enough_linemate = false;
	let mut enough_sibur = false;
	let mut enough_phiras = false;

	if nb_of_same_lvl < 2 {
		return false;
	}
	for x in ressources {
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

fn enough_level4(ressources: &[GameCellContent], nb_of_same_lvl: u8) -> bool {
	let mut enough_linemate = false;
	let mut enough_sibur = false;
	let mut enough_phiras = false;
	let mut enough_deraumere = false;

	if nb_of_same_lvl < 4 {
		return false;
	}
	for x in ressources {
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

fn enough_level5(ressources: &[GameCellContent], nb_of_same_lvl: u8) -> bool {
	let mut enough_linemate = false;
	let mut enough_sibur = false;
	let mut enough_mendiane = false;
	let mut enough_deraumere = false;

	if nb_of_same_lvl < 4 {
		return false;
	}
	for x in ressources {
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

fn enough_level6(ressources: &[GameCellContent], nb_of_same_lvl: u8) -> bool {
	let mut enough_linemate = false;
	let mut enough_sibur = false;
	let mut enough_phiras = false;
	let mut enough_deraumere = false;

	if nb_of_same_lvl < 6 {
		return false;
	}
	for x in ressources {
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

fn enough_level7(ressources: &[GameCellContent], nb_of_same_lvl: u8) -> bool {
	let mut enough_linemate = false;
	let mut enough_sibur = false;
	let mut enough_phiras = false;
	let mut enough_deraumere = false;
	let mut enough_mendiane = false;
	let mut enough_thystame = false;

	if nb_of_same_lvl < 6 {
		return false;
	}
	for x in ressources {
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