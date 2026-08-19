import unittest

from backend.webapp.ws import _extract_token_from_subprotocol


class WebSocketAuthTests(unittest.TestCase):
    def test_extracts_token_from_named_subprotocol_pair(self):
        self.assertEqual(
            _extract_token_from_subprotocol("seal-auth, 2d1f3c9a-9260-4028-9d83-c02ecf2ba87a"),
            "2d1f3c9a-9260-4028-9d83-c02ecf2ba87a",
        )

    def test_extracts_token_from_prefixed_subprotocol(self):
        self.assertEqual(
            _extract_token_from_subprotocol("chat, seal-token.abc123"),
            "abc123",
        )

    def test_returns_none_without_token(self):
        self.assertIsNone(_extract_token_from_subprotocol("chat, updates"))

