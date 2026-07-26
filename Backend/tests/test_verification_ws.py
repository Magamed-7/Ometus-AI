from app.services import email as email_service, notifications

EMAIL = "patient@ometus.test"


async def test_delivery_reports_progress_over_websocket(monkeypatch):
    monkeypatch.setattr(email_service, "send_verification_code", lambda email, code: None)
    queue = notifications.subscribe(EMAIL)

    try:
        assert await email_service.deliver_verification_code(EMAIL, "123456")
        assert queue.get_nowait() == {"status": "sending"}
        assert queue.get_nowait() == {"status": "sent"}
    finally:
        notifications.unsubscribe(EMAIL, queue)


async def test_delivery_reports_failure_over_websocket(monkeypatch):
    def explode(email, code):
        raise OSError("SMTP недоступен")

    monkeypatch.setattr(email_service, "send_verification_code", explode)
    queue = notifications.subscribe(EMAIL)

    try:
        assert await email_service.deliver_verification_code(EMAIL, "123456") is False
        assert queue.get_nowait() == {"status": "sending"}
        assert queue.get_nowait() == {"status": "failed"}
    finally:
        notifications.unsubscribe(EMAIL, queue)


async def test_events_go_only_to_subscribers_of_that_email(monkeypatch):
    monkeypatch.setattr(email_service, "send_verification_code", lambda email, code: None)
    mine = notifications.subscribe(EMAIL)
    stranger = notifications.subscribe("someone.else@ometus.test")

    try:
        await email_service.deliver_verification_code(EMAIL, "123456")

        assert mine.qsize() == 2
        assert stranger.empty()
    finally:
        notifications.unsubscribe(EMAIL, mine)
        notifications.unsubscribe("someone.else@ometus.test", stranger)


async def test_unsubscribe_leaves_no_listeners():
    queue = notifications.subscribe(EMAIL)
    assert notifications.listeners_count(EMAIL) == 1

    notifications.unsubscribe(EMAIL, queue)
    assert notifications.listeners_count(EMAIL) == 0
