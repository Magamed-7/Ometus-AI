import asyncio
from collections import defaultdict

_subscribers: dict[str, set[asyncio.Queue]] = defaultdict(set)


def subscribe(email: str) -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue()
    _subscribers[email].add(queue)
    return queue


def unsubscribe(email: str, queue: asyncio.Queue):
    listeners = _subscribers.get(email)

    if listeners is None:
        return

    listeners.discard(queue)

    if not listeners:
        _subscribers.pop(email, None)


async def publish(email: str, event: dict):
    for queue in list(_subscribers.get(email, ())):
        await queue.put(event)


def listeners_count(email: str) -> int:
    return len(_subscribers.get(email, ()))
