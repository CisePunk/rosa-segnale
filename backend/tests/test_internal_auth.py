import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class InternalAuthTest(unittest.TestCase):
    def test_internal_routes_remain_open_when_auth_env_is_absent(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            response = TestClient(app).get("/dashboard")

        self.assertNotEqual(response.status_code, 401)

    def test_internal_routes_require_basic_auth_when_configured(self) -> None:
        env = {
            "INTERNAL_AUTH_USERNAME": "reviewer",
            "INTERNAL_AUTH_PASSWORD": "secret",
        }

        with patch.dict(os.environ, env, clear=False):
            client = TestClient(app)
            missing = client.get("/dashboard")
            wrong = client.get("/dashboard", auth=("reviewer", "wrong"))
            right = client.get("/dashboard", auth=("reviewer", "secret"))

        self.assertEqual(missing.status_code, 401)
        self.assertEqual(wrong.status_code, 401)
        self.assertNotEqual(right.status_code, 401)


if __name__ == "__main__":
    unittest.main()
