/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   connections.rs                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/04 14:12:44 by nguiard           #+#    #+#             */
/*   Updated: 2024/03/05 15:07:12 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

use std::{fs::File, io::{BufRead, BufReader, Error, ErrorKind, Read}, os::fd::FromRawFd, str::from_utf8};

use epoll::Events;
use libc::*;

use crate::watcher::Watcher;

#[derive(Clone, Copy)]
pub struct ServerConnection {
	soc_addr: sockaddr_in,
	pub socket_fd: i32,
}

impl ServerConnection {
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
	
	pub fn get_new_connections(&self, watcher: &mut Watcher)
		-> Result<(), Error> {
		loop {
			let new_connection = unsafe {
				accept(self.socket_fd,
					std::ptr::null_mut(),
					std::ptr::null_mut())
			};
			if new_connection == -1 {
				let last_error = Error::last_os_error();
				if let Some(errno) = last_error.raw_os_error() {
					if errno == EWOULDBLOCK || errno == EAGAIN {
						return Ok(());
					}
				}
				return Err(last_error);
			}
			println!("Connection!");
			unsafe { fcntl(new_connection, F_SETFL, O_NONBLOCK) };
			watcher.add(new_connection, Events::EPOLLIN)?;
			return Ok(());
		}
	}

	pub fn deconnection(&self, fd: i32, watcher: &mut Watcher)
		-> Result<(), Error> {
		watcher.delete(fd)?;
		epoll::close(fd)?;
		Ok(())
	}
}

pub fn get_data(fd: i32) -> Result<Vec<String>, Error> {
	let mut buf = [0 as u8; 1024];
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
						return Err(last_error);
					}
				}
				line += String::from_utf8_lossy(&buf[0..size as usize]).to_string().as_str()
			}
		}
	}
	let lines: Vec<String> = line.split('\n').map(|l| l.to_string()).collect();
	Ok(lines)
}