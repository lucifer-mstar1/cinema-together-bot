from types import SimpleNamespace

from app.force_join import _split_required_chat, validate_force_join_configuration, force_join_keyboard, PrivateChatOnlyMiddleware
from app.texts import t


def test_v30_malformed_double_https_force_join_link_is_rejected():
    assert _split_required_chat('-1001|https://t.me/https://t.me/+bad|Group') is None


def test_v30_force_join_keyboard_contains_only_given_missing_chats():
    missing = [
        _split_required_chat('@second_required_channel'),
    ]
    kb = force_join_keyboard([m for m in missing if m], 'uz')
    texts = [button.text for row in kb.inline_keyboard for button in row]
    assert any('second_required_channel' in text for text in texts)
    assert not any('first_required_channel' in text for text in texts)
    assert texts[-1] == t('force_join_check', 'uz')


def test_v30_private_only_middleware_blocks_group_messages():
    middleware = PrivateChatOnlyMiddleware()
    event = SimpleNamespace(chat=SimpleNamespace(type='group'))
    called = False

    async def handler(_event, _data):
        nonlocal called
        called = True
        return 'handled'

    import asyncio
    result = asyncio.run(middleware(handler, event, {}))
    assert result is None
    assert called is False
