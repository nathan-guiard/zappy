# Communication with the server

## What sends what

### Graphical user interface

On connection, the server sends the whole map as it is. <br />
It sends an array of an array of cells, so `[[SendCell]]`

On every tick, the server sends the updated cells and every player
(because every player HAS TO be update due to food loss). <br />
It sends an `UpdateMap`.

### AI Client

On connection, the server sends "BIENVENUE\n" then expects a team name. When a viable team name is given, the server sends the size of the map like this: "{X} {Y}\n". From this moment the client can send commands to the server.

Data types sent in response of the commands:
- avance: ok/ko
- gauche: ok/ko
- droite: ok/ko
- prend: ok/ko
- pose: ok/ko
- expulse: ok/ko
- broadcast: ok
- incantation: ok/ko
- connect: number
- fork: ok/ko
- voir: `[SendCell]`
- inventaire: `[GameCellContent]`

## Data types

### UpdateMap

```json
{
	"cells": [SendCell],
	"players": [SendPlayer], 
}
```

---
### SendCell:

```json
{
	"p": GamePosition,
	"c": [GameCellContent], 
}
```

---
### GamePosition

```json
{
	"x": number,
	"y": number, 
}
```

---
### GameCellContent

```json
{
	"Linemate": number, // OR
	"Deraumere": number, // OR
	"Sibur": number, // OR
	"Mendiane": number, // OR
	"Phiras": number, // OR
	"Thystame": number, // OR
	"Player": number, // OR
	"Food": number,
}
```

---
### SendPlayer

```json
{
	"position": GamePosition,
	"direction": string, // see below
	"team": string,
	"action": string or object, // see below
	"inventory": [GameCellContent],
	"state": string or object, // see below
	"level": number,
	"food": PlayerFood,
}
```

direction can only be one of:
- `North`
- `South`
- `East`
- `West`

action can only be one of:
- `"Avance"`
- `"Gauche"`
- `"Droite"`
- `"Voir"`
- `"Inventaire"`
- `"Expulse"`
- `"Incantation"`
- `"Fork"`
- `"Connect"`
- `"NoAction"`
- `"Prend": string`
  - The string is what is being taken
- `"Pose": string`
  - The string is what is being dropped
- `"Broadcast": string`
  - The string is what will be braodcasted

state can only be one of:
- `"Idle"`
- `"Levelmax"`
- `"Dead"`
- `"Casting": [number, number]`
  - The first number is the current progress
  - The second number is the amount of steps needed

---
### PlayerFood
```json
{
	"HasSome": number, // OR
	"TurnsWithout": number
}
```