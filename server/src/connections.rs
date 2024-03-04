/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   connections.rs                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/04 14:12:44 by nguiard           #+#    #+#             */
/*   Updated: 2024/03/04 19:29:47 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

use std::{
	collections::HashMap,
	error::Error,
	fs::File,
	mem,
	os::fd::FromRawFd,
	thread,
	time::Duration
};

use libc::*;

#[derive(Clone, Copy)]
pub struct ServerConnection {
	soc_addr: sockaddr_in,
	socket_fd: i32,
}

pub fn init_socket(port: u16) -> ServerConnection {
	let mut result: ServerConnection;
	result = unsafe { std::mem::zeroed() };
	result.socket_fd = unsafe { socket(AF_INET, SOCK_STREAM, 0) };
	if result.socket_fd < 0 {
		// Return some kind of error
		todo!();
	}

	result.soc_addr.sin_addr.s_addr = INADDR_ANY.to_be();
	result.soc_addr.sin_port = port.to_be();
	result.soc_addr.sin_family = AF_INET as u16;

	if unsafe { fcntl(result.socket_fd, F_SETFL, O_NONBLOCK) }	< 0 {
		unsafe { libc::close(result.socket_fd) };
		// Return some kind of error;
		todo!();
	}

	if unsafe { bind(result.socket_fd,
		&result.soc_addr as *const _ as *const _,
		std::mem::size_of_val(&result.soc_addr) as u32) } != 0 {
		unsafe { libc::close(result.socket_fd) };
		// Return some kind of error
		todo!();
	}

	if unsafe { listen(result.socket_fd, 32) } != 0 {
		unsafe { libc::close(result.socket_fd) };
		// Return some kind of error
		todo!();
	}

	return result;
}

pub fn get_data(con_data: &ServerConnection, open_connections: &mut Vec<File>)
	-> HashMap<File, String> {
	let mut result: HashMap<File, String> = HashMap::new();

	// Check for new connections (maybe another function)
	loop {
		let new_connection = unsafe {
			accept(con_data.socket_fd,
				std::ptr::null_mut(),
				std::ptr::null_mut())
		};
		if new_connection == -1 {
			if let Some(errno) = get_errno() {
				dbg!(errno);
				if errno == EWOULDBLOCK || errno == EAGAIN {
					println!("No (more) incoming connections");
				} else {
					println!("Error: {errno}");
					// Return some kind of error
					todo!();
				}
			} else {
				// Handle connection
				println!("No errno location !?");
				todo!();
			}
		} else {
			println!("Connection!");
			unsafe { File::from_raw_fd(new_connection) };
			todo!();
		}
	}

	for _ in  0..open_connections.len() {

		// Get the data
		loop {
			break;
		}
	}

	return result;
}

fn get_errno() -> Option<i32> {
	let location = unsafe { __errno_location() };
	if location.is_null() {
		None
	} else {
		Some(unsafe { *location } )
	}
}

fn get_data_single_client() {
	
}