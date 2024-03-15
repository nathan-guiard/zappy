/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   gui.rs                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: nguiard <nguiard@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/03/12 18:12:59 by nguiard           #+#    #+#             */
/*   Updated: 2024/03/15 12:58:40 by nguiard          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#[derive(Debug)]
pub struct GraphicClient {
	pub fd: i32,
}

impl GraphicClient {
	pub fn new(fd: i32) -> Self {
		GraphicClient {
			fd,
		}
	}
}