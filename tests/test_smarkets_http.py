"""Contratto HTTP del client condiviso da pre-partita, live e outright."""
import io
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fetch_smarkets_outrights as client


class TestSmarketsHTTP(unittest.TestCase):
    def test_json_request_on_relative_and_paginated_urls(self):
        for path in ("/events/?limit=1", client.API + "/events/?offset=200"):
            with self.subTest(path=path), patch.object(client, "_attendi_il_turno"), \
                    patch("urllib.request.urlopen", return_value=io.BytesIO(b'{"events": []}')) as send:
                self.assertEqual(client._get(path), {"events": []})
                request = send.call_args.args[0]
                self.assertEqual(request.full_url, path if path.startswith("https:") else client.API + path)
                self.assertEqual(request.get_header("Accept"), "application/json")
                self.assertIn("Polymarket-Oracle", request.get_header("User-agent"))
                self.assertEqual(send.call_args.kwargs["timeout"], 30)

    def test_forbidden_still_fails_without_retry(self):
        error = urllib.error.HTTPError(client.API, 403, "Forbidden", {}, None)
        with patch.object(client, "_attendi_il_turno"), \
                patch("urllib.request.urlopen", side_effect=error) as send:
            with self.assertRaises(urllib.error.HTTPError):
                client._get("/events/")
            self.assertEqual(send.call_count, 1)
