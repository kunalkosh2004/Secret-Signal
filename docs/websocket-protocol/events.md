# WebSocket Protocol

## Event Envelope

All WebSocket messages follow this format:

```json
{
  "event": "STRING",
  "request_id": "UUID (optional, for client-to-server requests)",
  "room_id": "UUID",
  "timestamp": "ISO-8601 timestamp",
  "payload": {}
}
```

## Client-to-Server Events

- `JOIN_ROOM` - Player joins a room
- `LEAVE_ROOM` - Player leaves a room
- `PLAYER_READY` - Player signals readiness to start game
- `SEND_MESSAGE` - Player sends a chat message
- `REPLY_TO_MESSAGE` - Player replies to a specific message
- `ADD_REACTION` - Player adds a reaction to a message
- `CAST_VOTE` - Player votes for a suspected Coordinator
- `SUBMIT_ACCUSATION` - Player submits an accusation (alternative to voting)

## Server-to-Client Events

- `ROOM_STATE` - Current state of the room (players, settings, etc.)
- `PLAYER_JOINED` - Notification when a player joins the room
- `PLAYER_LEFT` - Notification when a player leaves the room
- `PLAYER_READY_CHANGED` - Notification when a player's ready status changes
- `MESSAGE_SENT` - New chat message broadcast
- `MESSAGE_REPLIED` - Notification when a message receives a reply
- `REACTION_ADDED` - Notification when a reaction is added to a message
- `ROUND_STARTED` - Indicates the start of a new round
- `PHASE_CHANGED` - Indicates a phase transition within a round
- `TIMER_UPDATED` - Updates for round/phase timers
- `MISSION_ASSIGNED` - Private mission sent to Coordinator
- `MISSION_PROGRESS_UPDATED` - Update on mission completion progress
- `VOTE_UPDATED` - Current vote tallies
- `ACCUSATION_RESULT` - Result of an accusation vote
- `ROUND_ENDED` - Indicates the end of a round
- `GAME_ENDED` - Indicates the end of the game
- `ERROR` - Error message from the server