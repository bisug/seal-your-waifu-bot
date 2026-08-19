import unittest

from backend.webapp import auth


class FakeRedis:
    def __init__(self, values):
        self.values = values
        self.keys = []

    async def get(self, key):
        self.keys.append(key)
        return self.values.get(key)


class FakeSessionsCollection:
    def __init__(self, document=None):
        self.document = document
        self.query = None

    async def find_one(self, query):
        self.query = query
        return self.document


class AuthSessionTokenTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.original_redis = auth.r
        self.original_sessions = auth.sessions_collection

    def tearDown(self):
        auth.r = self.original_redis
        auth.sessions_collection = self.original_sessions

    def test_token_key_uses_digest(self):
        token = "session-token-123"
        token_key = auth._token_key(token)

        self.assertTrue(token_key.startswith("auth_token:"))
        self.assertNotIn(token, token_key)
        self.assertEqual(token_key, auth._token_key(token))
        self.assertNotEqual(token_key, auth._legacy_token_key(token))

    async def test_redis_lookup_checks_hashed_key_before_legacy_key(self):
        token = "session-token-123"
        hashed_key = auth._token_key(token)
        legacy_key = auth._legacy_token_key(token)
        fake_redis = FakeRedis({legacy_key: "42"})
        auth.r = fake_redis
        auth.sessions_collection = FakeSessionsCollection()

        user_id = await auth.get_user_id_from_token(token)

        self.assertEqual(user_id, "42")
        self.assertEqual(fake_redis.keys, [hashed_key, legacy_key])

    async def test_mongo_lookup_uses_hashed_and_legacy_keys(self):
        token = "session-token-123"
        auth.r = None
        fake_sessions = FakeSessionsCollection({"user_id": "99"})
        auth.sessions_collection = fake_sessions

        user_id = await auth.get_user_id_from_token(token)

        self.assertEqual(user_id, "99")
        self.assertEqual(
            fake_sessions.query["_id"]["$in"],
            [auth._token_key(token), auth._legacy_token_key(token)],
        )

