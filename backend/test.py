import asyncio

from app.core.redis import (
    store_google_link_state,
    consume_google_link_state,
)


async def test():
    state = "link-test-state"

    await store_google_link_state(
        state=state,
        user_id=2,
    )

    first = await consume_google_link_state(state)
    print("First:", first)

    second = await consume_google_link_state(state)
    print("Second:", second)


asyncio.run(test())