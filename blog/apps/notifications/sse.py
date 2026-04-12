# Python imports
import asyncio
import json

# Django imports
from django.http import StreamingHttpResponse

# Redis imports
import redis.asyncio as aioredis

# Project imports
from settings.base import REDIS_URL

SSE_CHANNEL = 'posts:published'

async def event_generator():
    client = aioredis.from_url(REDIS_URL)
    pubsub = client.pubsub()
    await pubsub.subscribe(SSE_CHANNEL)

    try:
        yield ": keep-alive\n\n"

        async for raw in pubsub.listen():
            if raw["type"] != "message":
                continue
            payload = json.dumps(json.loads(raw["data"]))
            yield f"data: {payload}\n\n"

    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.unsubscribe(SSE_CHANNEL)
        await client.aclose()


async def post_stream(request):           
    response = StreamingHttpResponse(
        event_generator(),                
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response                       