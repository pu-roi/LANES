import pytest
from app.schemas.feed import VoteResponse
from app.models.interaction import InteractionType
from app.schemas.interaction import PostInteractionCreate


def test_vote_response_schema():
    res = VoteResponse(
        post_id=42,
        upvotes=10,
        downvotes=3,
        net_score=7,
        user_interaction="upvote"
    )
    assert res.post_id == 42
    assert res.upvotes == 10
    assert res.downvotes == 3
    assert res.net_score == 7
    assert res.user_interaction == "upvote"


def test_vote_response_schema_neutral():
    res = VoteResponse(
        post_id=42,
        upvotes=0,
        downvotes=0,
        net_score=0,
        user_interaction=None
    )
    assert res.net_score == 0
    assert res.user_interaction is None


def test_post_interaction_create():
    interaction = PostInteractionCreate(
        post_id=1,
        interaction_type=InteractionType.UPVOTE
    )
    assert interaction.post_id == 1
    assert interaction.interaction_type == InteractionType.UPVOTE
