from pydantic import BaseModel


class CastVoteRequest(BaseModel):
    target_user_id: int


class VoteTally(BaseModel):
    target_user_id: int
    count: int


class VoteResults(BaseModel):
    round_number: int
    total_votes: int
    tallies: list[VoteTally]
