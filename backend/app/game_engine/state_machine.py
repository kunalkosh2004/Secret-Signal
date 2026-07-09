from enum import Enum


class GamePhase(str, Enum):
    WAITING = "waiting"
    ROLE_ASSIGNMENT = "role_assignment"
    ROUND_START = "round_start"
    INTERACTION = "interaction"
    EVALUATION = "evaluation"
    DISCUSSION = "discussion"
    VOTING = "voting"
    RESULT = "result"
    GAME_OVER = "game_over"

VALID_TRANSITIONS = {
    GamePhase.WAITING: {
        GamePhase.ROLE_ASSIGNMENT,
    },

    GamePhase.ROLE_ASSIGNMENT: {
        GamePhase.ROUND_START,
    },

    GamePhase.ROUND_START: {
        GamePhase.INTERACTION,
    },

    GamePhase.INTERACTION: {
        GamePhase.EVALUATION,
    },

    GamePhase.EVALUATION: {
        GamePhase.DISCUSSION,
    },

    GamePhase.DISCUSSION: {
        GamePhase.VOTING,
    },

    GamePhase.VOTING: {
        GamePhase.RESULT,
    },

    GamePhase.RESULT: {
        GamePhase.ROUND_START,
        GamePhase.GAME_OVER,
    },

    GamePhase.GAME_OVER: set(),
}

def can_transition(
    current_phase: GamePhase,
    next_phase: GamePhase,
) -> bool:
    return next_phase in VALID_TRANSITIONS.get(
        current_phase,
        set(),
    )

def validate_transition(
    current_phase: GamePhase,
    next_phase: GamePhase,
) -> None:
    if not can_transition(current_phase, next_phase):
        raise ValueError(
            f"Invalid phase transition: "
            f"{current_phase.value} -> {next_phase.value}"
        )