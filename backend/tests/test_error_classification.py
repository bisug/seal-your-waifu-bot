"""Guard against kurigram error reclassifications breaking our catch order.

Kurigram 2.2.25 (#357) moved ChatWriteForbidden from Forbidden/403 to
BadRequest/400. Our wrappers rely on catching permission denials *before*
the generic BadRequest handler (which logs at ERROR). If a future release
reclassifies another error, these asserts fail instead of silently turning
permission denials into ERROR-level log spam.
"""
from pyrogram import errors

from backend.core.constants import PERMISSION_DENIED_ERRORS


def test_permission_denied_tuple_covers_write_denials():
    # The classes that mean "we are not allowed to post here".
    for name in ("ChatWriteForbidden", "ChatAdminRequired", "ChannelPrivate"):
        cls = getattr(errors, name)
        assert issubclass(cls, PERMISSION_DENIED_ERRORS), (
            f"{name} is no longer covered by PERMISSION_DENIED_ERRORS; "
            "it would fall through to the ERROR-level BadRequest handler"
        )


def test_permission_denied_tuple_covers_legacy_classes():
    for name in ("Forbidden", "Unauthorized"):
        cls = getattr(errors, name)
        assert issubclass(cls, PERMISSION_DENIED_ERRORS)


def test_permission_denied_tuple_is_not_broad():
    # Must never swallow genuine bad requests or flood waits.
    for name in ("BadRequest", "FloodWait", "SlowmodeWait", "MessageNotModified"):
        cls = getattr(errors, name)
        assert not issubclass(cls, PERMISSION_DENIED_ERRORS)


def test_message_ids_empty_is_bad_request():
    # deletion.py catches this typed error before the string-matching fallback.
    assert issubclass(errors.MessageIdsEmpty, errors.BadRequest)
