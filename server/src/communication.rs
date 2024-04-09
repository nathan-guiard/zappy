/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   communication.rs                                   :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/07 05:53:29 by nguiard           #+#    #+#             */
/*   Updated: 2024/04/09 11:44:05 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

use std::{collections::HashMap, io::Error};

use libc::{c_void, send, EWOULDBLOCK};

use crate::game::{gui::GraphicClient, player::{get_player_from_fd_mut, Player}};
use colored::Colorize;

pub fn process_data(data: &HashMap<i32, Vec<String>>,
	players: &mut [Player],
	gui: &mut Option<GraphicClient>) {
	let mut unwrapped_gui: &mut GraphicClient = &mut GraphicClient {
		fd: -1,
		enabled: true,
	};
	if gui.is_some() {
		unwrapped_gui = gui.as_mut().unwrap()
	}
	
	for (fd, lines) in data {
		if let Some(player) = get_player_from_fd_mut(players, *fd) {
			player.push_to_queue(lines.clone());
		}
		if !unwrapped_gui.enabled && &unwrapped_gui.fd == fd {
			unwrapped_gui.enable(lines.clone());
		}
	}
}

pub fn get_all_data(ready_to_read: &Vec<i32>)
	-> Result<HashMap<i32, Vec<String>>, Error> {
	let mut data: HashMap<i32, Vec<String>> = HashMap::new();

	for fd in ready_to_read {
		data.insert(*fd, get_data_from_fd(*fd)?);
	}

	Ok(data)
}

pub fn get_data_from_fd(fd: i32) -> Result<Vec<String>, Error> {
	let mut buf = [0_u8; 1024];
	let mut line = String::new();

	loop {
		match unsafe { libc::read(fd, buf.as_mut_ptr() as *mut c_void, 1024) } {
			0 => {
				break;
			}
			size => {
				if size == -1 {
					let last_error = Error::last_os_error();
					if let Some(e) = last_error.raw_os_error() {
						if e == EWOULDBLOCK {
							break;
						}
						eprintln!("{}", "Could not read data from client".red().bold());
						return Err(last_error);
					}
				}
				line += String::from_utf8_lossy(&buf[0..size as usize]).to_string().as_str()
			}
		}
	}
	let lines: Vec<String> = split_keep_newline(line);
	Ok(lines)
}

pub fn split_keep_newline(to_split: String) -> Vec<String> {
	let mut result: Vec<String> = Vec::new();
    let mut current_string = String::new();

    for c in to_split.chars() {
        if c == '\n' {
            current_string.push(c);
            result.push(current_string.clone());
            current_string.clear();
        } else {
            current_string.push(c);
        }
    }

    if !current_string.is_empty() {
        result.push(current_string);
    }
	
	result
}

pub fn send_to(fd: i32, data: &str) {
	unsafe { send(fd, data.as_bytes().as_ptr() as _, data.len(), 0) };
}