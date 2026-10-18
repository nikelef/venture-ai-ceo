import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from ai_ceo.server import PreviewHandler


class PreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), PreviewHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def test_evaluator_assets_and_health_are_served_with_security_headers(self):
        for route in ("/", "/catalog.js", "/app.js", "/style.css", "/review-notice.html", "/robots.txt", "/healthz",
                      "/demand.js", "/experiment-config.js", "/shopify-csv-checklist.html", "/sitemap.xml", "/venturecatalogpreflight20261019.txt"):
            with self.subTest(route=route), urllib.request.urlopen(self.base + route, timeout=3) as response:
                self.assertEqual(response.status, 200)
                self.assertIn("connect-src 'none'", response.headers["Content-Security-Policy"])
                self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
                body = response.read()
                self.assertTrue(body)
                if route == "/healthz":
                    self.assertFalse(json.loads(body)["sales_enabled"])

    def test_private_repository_paths_and_traversal_are_unavailable(self):
        for route in ("/.env", "/.git/config", "/data/decision.json", "/../MASTER_PROMPT.md", "/%2e%2e/README.md", "/research/"):
            with self.subTest(route=route), self.assertRaises(urllib.error.HTTPError) as raised:
                urllib.request.urlopen(self.base + route, timeout=3)
            self.assertEqual(raised.exception.code, 404)
            raised.exception.close()

    def test_checkout_webhook_and_upload_routes_are_disabled(self):
        for route in ("/checkout", "/webhooks/stripe", "/upload"):
            request = urllib.request.Request(self.base + route, method="POST", data=b"synthetic")
            with self.assertRaises(urllib.error.HTTPError) as raised:
                urllib.request.urlopen(request, timeout=3)
            self.assertEqual(raised.exception.code, 503)
            raised.exception.close()


if __name__ == "__main__":
    unittest.main()
