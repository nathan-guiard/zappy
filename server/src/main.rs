/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   main.rs                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/04 09:08:14 by nguiard           #+#    #+#             */
/*   Updated: 2024/03/07 10:11:53 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

mod connections;
mod watcher;
mod game;
mod communication;

use std::io::{Error, ErrorKind};
use std::time::{Duration, Instant};
use epoll::Events;
use libc::{EPOLLIN, EPOLLRDHUP};
use rand::Rng;
use structopt::StructOpt;

use watcher::Watcher;
use connections::ServerConnection;
use game::map::GameMap;
use communication::{get_all_data, process_data};

#[derive(StructOpt, Debug)]
struct Args {
	#[structopt(short, long, default_value = "4227")]
	port: u16,

	/// The map width
	#[structopt(short, default_value = "65")]
	x: u8,

	/// The map height
	#[structopt(short, default_value = "25")]
	y: u8,

	/// The team name(s)
	#[structopt(short = "n", long)]
	team_name: Vec<String>,

	/// The number of clients authorized at the beginning of the game
	#[structopt(short, long, default_value = "100")]
	clients: u8,

	/// The time unit divider, every step of the server will go at 1/t second
	#[structopt(short, long, default_value = "16")]
	time: u8,

	/// The seed that will be used to generate the map, 0 means randomly
	#[structopt(short, long, default_value = "0")]
	seed: usize,
}

fn main() -> Result<(), Error> {
	let mut args = Args::from_args();
	args_check(&mut args)?;
	let tick_speed = Duration::from_secs_f64(1 as f64 / args.time as f64);
	let mut map = GameMap::new(args.x, args.y, args.seed);
	println!("{}", map);
	// return Ok(());
	let con_data = ServerConnection::init_socket(args.port)?;
	let mut watcher = Watcher::new()?;

	watcher.add(con_data.socket_fd, Events::EPOLLIN)?;

	
	let mut before = Instant::now();
	let mut exec_time = Duration::default();
	let mut last_sleep = Duration::default();
	loop {
		let new_events = match watcher.update() {
			Ok(events) => events,
			Err(e) => {
				eprintln!("Error trying to update: {e}");
				return Err(e);
			}
		};
		
		if new_events.is_empty() {
			time_check(&tick_speed, &mut exec_time, &mut before, &mut last_sleep);
			std::thread::sleep(last_sleep);
			before = Instant::now();
			continue;
		}
		
		let mut ready_to_read: Vec<i32> = vec![];
		
		for event in new_events {
			if event.data == con_data.socket_fd as u64 &&
			event.events == EPOLLIN as u32 {
				con_data.get_new_connections(&mut watcher)?;
			} else if event.events == EPOLLIN as u32 {
				ready_to_read.push(event.data as i32);
			} else if event.events & (EPOLLRDHUP as u32) != 0 {
				con_data.deconnection(event.data as i32, &mut watcher)?;
			}
		}
		
		let data = get_all_data(&ready_to_read)?;
		process_data(&data, &map);
		
		dbg!(data);
		time_check(&tick_speed, &mut exec_time, &mut before, &mut last_sleep);
		std::thread::sleep(last_sleep);
		before = Instant::now();
	}
}

fn time_check(tick_speed: &Duration, exec_time: &mut Duration,
	before: &mut Instant, last_sleep: &mut Duration) {
	*exec_time = Instant::now().checked_duration_since(*before).unwrap_or_default();
	*last_sleep = tick_speed.checked_sub(*exec_time).unwrap_or_default();
	println!("\x1b[3;2;90m---\x1b[0m\nexec: {:?}", exec_time);
}

fn args_check(args: &mut Args) -> Result<(), Error> {
	if args.x > 150 || args.y > 120 {
		return Err(Error::new(ErrorKind::InvalidInput,
			"Map too big, max size is X:150, Y:120"));
	}
	if args.x < 30 || args.y < 25 {
		return Err(Error::new(ErrorKind::InvalidInput,
			"Map too big, max size is X:30, Y:25"));
	}
	if args.team_name.is_empty() {
		args.team_name.push("Blue team".into());
	}
	if args.seed == 0 {
		args.seed = rand::thread_rng().gen();
	}
	Ok(())
}