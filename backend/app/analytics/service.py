from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession

from app.events import repository as event_repository
from app.game_engine import repository as game_repository
from app.voting import repository as vote_repository
from app.missions import repository as mission_repository


@dataclass
class PlayerBehaviorProfile:
    user_id: int
    role: str
    message_count: int = 0
    questions_asked: int = 0
    topic_initiations: int = 0
    avg_message_length: float = 0.0
    suspicion_score: float = 0.0
    voting_accuracy: float = 0.0
    round_breakdown: list[dict] = field(default_factory=list)


@dataclass
class GameAnalysis:
    game_id: int
    total_rounds: int
    completed_missions: int
    winner: str
    players: list[PlayerBehaviorProfile]
    summary: str
    voting_patterns: dict
    coordination_score: float = 0.0


QUESTION_MARKERS = [
    "?",
    "who",
    "what",
    "where",
    "when",
    "why",
    "how",
    "do you",
    "did you",
    "are you",
    "is it",
    "could it",
    "maybe",
    "sus",
    "suspicious",
    "suspect",
    "trust",
    "prove",
    "claim",
]

TOPIC_SHIFTERS = [
    "but",
    "however",
    "actually",
    "wait",
    "no",
    "well",
    "okay so",
    "let me",
    "i think",
    "what if",
    "hang on",
    "hold on",
    "sorry",
    "btw",
    "by the way",
    "anyway",
]


def _count_questions(text: str) -> int:
    text_lower = text.lower()
    count = text_lower.count("?")
    for marker in QUESTION_MARKERS:
        if marker in text_lower:
            count += 1
    return count


def _count_topic_shifts(text: str) -> int:
    text_lower = text.lower()
    count = 0
    for shifter in TOPIC_SHIFTERS:
        if shifter in text_lower:
            count += 1
    return count


def _calculate_voting_accuracy(
    votes_rounds: list[dict],
    coordinator_user_id: int,
) -> float:
    if not votes_rounds:
        return 0.0

    correct = 0
    total = 0

    for vote_data in votes_rounds:
        votes = vote_data.get("votes", [])
        if not votes:
            continue

        vote_counts: dict[int, int] = {}
        for vote in votes:
            target = vote.get("target_user_id")
            if target:
                vote_counts[target] = vote_counts.get(target, 0) + 1

        if not vote_counts:
            continue

        total += 1
        top_target = max(vote_counts, key=vote_counts.get)
        if top_target == coordinator_user_id:
            correct += 1

    return correct / total if total > 0 else 0.0


def _calculate_player_suspicion(
    profile: PlayerBehaviorProfile,
    all_profiles: list["PlayerBehaviorProfile"],
    game: dict,
) -> float:
    score = 0.0

    if profile.message_count > 0:
        question_ratio = profile.questions_asked / profile.message_count
        if question_ratio > 0.3:
            score += 20.0
        elif question_ratio > 0.15:
            score += 10.0

    avg_msg_len = profile.avg_message_length
    all_lengths = [p.avg_message_length for p in all_profiles]
    if all_lengths:
        overall_avg = sum(all_lengths) / len(all_lengths)
        if avg_msg_len > overall_avg * 1.5:
            score += 15.0
        elif avg_msg_len < overall_avg * 0.5:
            score += 10.0

    if profile.topic_initiations > 3:
        score += 15.0
    elif profile.topic_initiations > 1:
        score += 5.0

    if profile.role == "coordinator":
        score += 25.0
    elif profile.role == "detective":
        score -= 15.0
    else:
        score += 5.0

    if profile.voting_accuracy > 0.6:
        score -= 10.0
    elif profile.voting_accuracy < 0.3:
        score += 10.0

    return max(0.0, min(100.0, score))


async def analyze_game(
    db: AsyncSession,
    game_id: int,
) -> GameAnalysis:
    game = await game_repository.get_by_id(db, game_id)

    if game is None:
        raise ValueError(f"Game {game_id} not found")

    game_players = await game_repository.get_game_players(
        db, game_id=game_id
    )

    all_events = await event_repository.get_game_events(
        db, game_id=game_id
    )

    messages_by_player: dict[int, list[dict]] = {}
    for event in all_events:
        if event.event_type == "message":
            uid = event.user_id
            if uid not in messages_by_player:
                messages_by_player[uid] = []
            messages_by_player[uid].append(
                {
                    "round": event.round_number,
                    "payload": event.payload,
                }
            )

    profiles: list[PlayerBehaviorProfile] = []

    for gp in game_players:
        uid = gp.user_id
        messages = messages_by_player.get(uid, [])

        msg_count = len(messages)
        questions = 0
        topic_shifts = 0
        total_len = 0.0

        for msg in messages:
            payload = msg.get("payload", {})
            text = payload.get("content", "")
            questions += _count_questions(text)
            topic_shifts += _count_topic_shifts(text)
            total_len += len(text)

        avg_len = total_len / msg_count if msg_count > 0 else 0.0

        votes_all_rounds = []
        for r in range(1, game.round_number + 1):
            round_votes = await vote_repository.get_votes_for_round(
                db, game_id=game_id, round_number=r
            )
            votes_all_rounds.append(
                {
                    "round": r,
                    "votes": [
                        {
                            "voter_user_id": v.voter_user_id,
                            "target_user_id": v.target_user_id,
                        }
                        for v in round_votes
                    ],
                }
            )

        coord = next(
            (gp for gp in game_players if gp.role == "coordinator"),
            None,
        )
        coord_uid = coord.user_id if coord else -1

        voting_accuracy = _calculate_voting_accuracy(
            votes_all_rounds, coord_uid
        )

        round_breakdown = []
        for r in range(1, game.round_number + 1):
            round_msgs = [
                m for m in messages if m.get("round") == r
            ]
            round_breakdown.append(
                {
                    "round": r,
                    "message_count": len(round_msgs),
                    "questions": sum(
                        _count_questions(
                            m.get("payload", {}).get("content", "")
                        )
                        for m in round_msgs
                    ),
                }
            )

        profile = PlayerBehaviorProfile(
            user_id=uid,
            role=gp.role,
            message_count=msg_count,
            questions_asked=questions,
            topic_initiations=topic_shifts,
            avg_message_length=avg_len,
            voting_accuracy=voting_accuracy,
            round_breakdown=round_breakdown,
        )

        profiles.append(profile)

    completed_missions = await mission_repository.count_completed_missions(
        db, game_id=game_id
    )

    for profile in profiles:
        profile.suspicion_score = _calculate_player_suspicion(
            profile, profiles, {"game": game}
        )

    winner = "coordinator"
    if completed_missions >= 5:
        winner = "investigation_team"
    elif game.phase == "game_over":
        last_votes = []
        for r in range(1, game.round_number + 1):
            round_votes = await vote_repository.get_votes_for_round(
                db, game_id=game_id, round_number=r
            )
            if round_votes:
                last_votes = round_votes

        if last_votes:
            vote_counts: dict[int, int] = {}
            for v in last_votes:
                vote_counts[v.target_user_id] = (
                    vote_counts.get(v.target_user_id, 0) + 1
                )
            if vote_counts:
                top_target = max(vote_counts, key=vote_counts.get)
                coord = next(
                    (
                        gp
                        for gp in game_players
                        if gp.role == "coordinator"
                    ),
                    None,
                )
                if coord and top_target == coord.user_id:
                    winner = "investigation_team"

    voting_patterns = {}
    for r in range(1, game.round_number + 1):
        round_votes = await vote_repository.get_votes_for_round(
            db, game_id=game_id, round_number=r
        )
        if round_votes:
            vote_counts_r: dict[int, int] = {}
            for v in round_votes:
                vote_counts_r[v.target_user_id] = (
                    vote_counts_r.get(v.target_user_id, 0) + 1
                )
            voting_patterns[str(r)] = vote_counts_r

    coord_profile = next(
        (p for p in profiles if p.role == "coordinator"), None
    )
    citizen_profiles = [
        p for p in profiles if p.role != "coordinator"
    ]

    coordination_score = 0.0
    if citizen_profiles and coord_profile:
        avg_citizen_msgs = sum(
            p.message_count for p in citizen_profiles
        ) / len(citizen_profiles)
        if coord_profile.message_count > 0:
            ratio = avg_citizen_msgs / coord_profile.message_count
            coordination_score = min(100.0, ratio * 50.0)

    summary_lines = []
    summary_lines.append(
        f"Game {game_id} had {game.round_number} rounds with "
        f"{completed_missions} completed missions."
    )

    coord = next(
        (p for p in profiles if p.role == "coordinator"), None
    )
    if coord:
        summary_lines.append(
            f"The coordinator (Player {coord.user_id}) sent "
            f"{coord.message_count} messages with an average "
            f"length of {coord.avg_message_length:.0f} characters."
        )

    suspicious = sorted(
        profiles, key=lambda p: p.suspicion_score, reverse=True
    )
    if suspicious:
        top = suspicious[0]
        summary_lines.append(
            f"Player {top.user_id} ({top.role}) had the "
            f"highest suspicion score of {top.suspicion_score:.1f}."
        )

    summary = " ".join(summary_lines)

    return GameAnalysis(
        game_id=game_id,
        total_rounds=game.round_number,
        completed_missions=completed_missions,
        winner=winner,
        players=profiles,
        summary=summary,
        voting_patterns=voting_patterns,
        coordination_score=coordination_score,
    )
