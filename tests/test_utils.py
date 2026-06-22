from app.utils import has_contact_info, valid_anon_name


def test_valid_names():
    assert valid_anon_name("SilentMoon")
    assert valid_anon_name("abc_123")
    assert not valid_anon_name("ab")
    assert not valid_anon_name("bad name")


def test_contact_detection():
    assert has_contact_info("write me @username")
    assert has_contact_info("https://example.com")
    assert has_contact_info("+998 90 123 45 67")
    assert not has_contact_info("hello how are you")
