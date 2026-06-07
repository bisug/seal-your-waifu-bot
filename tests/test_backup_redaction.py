import unittest

from Grabber.modules.admin.db_backup import _redact_mongo_uri


class BackupRedactionTests(unittest.TestCase):
    def test_redacts_credentials_and_query_params(self):
        redacted = _redact_mongo_uri(
            "mongodb+srv://user:secret@example.mongodb.net/db?retryWrites=true"
        )

        self.assertEqual(redacted, "mongodb+srv://***:***@example.mongodb.net/db")
        self.assertNotIn("user", redacted)
        self.assertNotIn("secret", redacted)
        self.assertNotIn("retryWrites", redacted)

    def test_invalid_uri_returns_redacted_placeholder(self):
        self.assertEqual(_redact_mongo_uri("not-a-uri"), "<redacted>")

