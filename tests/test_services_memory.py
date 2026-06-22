from app.services import WAITING, ACTIVE, cancel_waiting


def test_cancel_waiting_is_safe():
    WAITING.clear()
    cancel_waiting(123)
    assert WAITING == {}
