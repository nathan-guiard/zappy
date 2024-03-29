/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   main.rs                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/04 09:08:14 by nguiard           #+#    #+#             */
/*   Updated: 2024/03/22 11:09:44 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

mod connections;
mod watcher;
mod game;
mod communication;
mod update_gui;

use std::io::{Error, ErrorKind};
use std::process::ExitCode;
use std::sync::atomic::AtomicBool;
use std::time::{Duration, Instant};
use colored::Colorize;
use epoll::Events;
use game::Game;
use libc::{EPOLLIN, EPOLLRDHUP};
use rand::Rng;
use structopt::StructOpt;

use update_gui::update_gui;
use watcher::Watcher;
use connections::ServerConnection;
use communication::{get_all_data, process_data};

use crate::game::player::{get_player_from_fd, PlayerState};

static mut EXIT: AtomicBool = AtomicBool::new(false);

#[derive(StructOpt, Debug)]
struct Args {
	#[structopt(short, long, default_value = "4227")]
	port: u16,

	/// The map width
	#[structopt(short, default_value = "65")]
	x: u8,

	/// The map height
	#[structopt(short, default_value = "35")]
	y: u8,

	/// The team name(s)
	#[structopt(short = "n", long)]
	team_name: Vec<String>,

	/// The number of clients authorized at the beginning of the game per team
	#[structopt(short, long, default_value = "1")]
	clients: u8,

	/// The time unit divider, every step of the server will go at 1/t second
	#[structopt(short, long, default_value = "16")]
	time: u8,

	/// The seed that will be used to generate the map, 0 means randomly
	#[structopt(short, long, default_value = "0")]
	seed: usize,
}

fn main() -> Result<ExitCode, Error> {
	// Argument
	let mut args = Args::from_args();
	args_check(&mut args)?;
	let tick_speed = Duration::from_secs_f64(1_f64 / args.time as f64);

	// Connection
	let con_data = ServerConnection::init_socket(args.port)?;
	let mut watcher = Watcher::new()?;
	watcher.add(con_data.socket_fd, Events::EPOLLIN)?;

	// All the game
	let mut game: Game = Game::new(args.x, args.y,
									args.team_name,
									args.clients,
									args.seed)?;
	print!("{}", game.map);

	// Timing
	let mut before = Instant::now();
	let mut exec_time = Duration::default();
	let mut last_sleep = Duration::default();
	let mut turn_nb: usize = 0;

	// Ctrl-C
	if ctrlc::set_handler(|| {
		println!("Recieved CTRL-C, the server will shut down in the next turn.");
		unsafe { EXIT.store(true, std::sync::atomic::Ordering::Release) };
	}).is_err() {
		eprintln!("Could not set up Ctrl-C handler. Aborting");
		return Ok(ExitCode::from(1));
	}

	loop {
		let new_events = match watcher.update() {
			Ok(events) => events,
			Err(e) => {
				eprintln!("{}: {e}", "Error trying to update".red().bold());
				return Err(e);
			}
		};
		
		let mut ready_to_read: Vec<i32> = vec![];
		
		for event in new_events {
			if event.data == con_data.socket_fd as u64 &&
			event.events == EPOLLIN as u32 {
				if let Some(new_player) = con_data.get_new_connections(&mut watcher)? {
					game.players.push(new_player);
				}
			} else if event.events == EPOLLIN as u32 {
				ready_to_read.push(event.data as i32);
			} else if event.events & (EPOLLRDHUP as u32) != 0 {
				game.try_remove_gui(
					con_data.deconnection(event.data as i32, &mut watcher)?
				);
				if let Some(player) = get_player_from_fd(&mut game.players, event.data as i32) {
					if let Some(team_of_player) = game.teams.get_mut(&player.team) {
						if player.state != PlayerState::Dead {
							team_of_player.add_position(player.position);
						}
					}
				}
				game.players.retain(|p| p.fd != event.data as i32);
			}
		}
		
		let data = get_all_data(&ready_to_read)?;
		process_data(&data, &mut game.players, &mut game.gui);
		
		game.execute();
		update_gui(&game);
		game.last_map = Some(game.map.clone());

		if unsafe { EXIT.load(std::sync::atomic::Ordering::Relaxed) } {
			println!("Last turn finished.");
			break;
		}
		
		turn_nb += 1;
		time_check(&tick_speed, &mut exec_time, &mut before, &mut last_sleep, turn_nb);
		std::thread::sleep(last_sleep);
		before = Instant::now();

		if unsafe { EXIT.load(std::sync::atomic::Ordering::Relaxed) } {
			println!("Last turn finished.");
			break;
		}
	};
	Ok(ExitCode::from(0))
}

fn time_check(tick_speed: &Duration, exec_time: &mut Duration,
	before: &mut Instant, last_sleep: &mut Duration, turn_nb: usize) {
	*exec_time = Instant::now().checked_duration_since(*before).unwrap_or_default();
	*last_sleep = tick_speed.checked_sub(*exec_time).unwrap_or_default();
	println!("\x1b[3;2;90m---\x1b[0;2;32m turn {} |\texec: {:?}\x1b[0m", turn_nb, exec_time);
}

fn args_check(args: &mut Args) -> Result<(), Error> {
	if args.time > 128 {
		return Err(Error::new(ErrorKind::InvalidInput,
			"Time cannot be more than 128"));
	}
	if args.x > 150 || args.y > 120 {
		return Err(Error::new(ErrorKind::InvalidInput,
			"Map too big, max size is X:150, Y:120"));
	}
	if args.x < 30 || args.y < 25 {
		return Err(Error::new(ErrorKind::InvalidInput,
			"Map too big, max size is X:30, Y:25"));
	}
	if args.team_name.is_empty() {
		args.team_name.push("ekip".into());
	}
	if args.team_name.len() > 4 {
		return Err(Error::new(ErrorKind::InvalidInput,
			"Cannot have more than 4 teams"));
		}
	for team_name in &args.team_name {
		if team_name == "gui" {
			return Err(Error::new(ErrorKind::InvalidInput,
				"None of the teams can be named 'gui'"));
		}
	}
	if args.clients < 1 || args.clients > 6 as u8 {
		return Err(Error::new(ErrorKind::InvalidInput,
			"Clients per team at the beginning of the game must be between 1 and 6."));
	}
	if args.seed == 0 {
		args.seed = rand::thread_rng().gen();
	}
	println!("Server port: {}", args.port);
	println!("Map dimentions: X:{} Y:{}", args.x, args.y);
	println!("Seed: {}", args.seed);
	println!("Tick rate: {}s", 1_f64 / args.time as f64);
	println!("---");
	Ok(())
}