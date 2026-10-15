"""Exercise the real library in the test process, including host preservation."""
import ctypes
import errno
import http.client
import http.server
import os
from pathlib import Path
import signal
import socket
import sys
import tempfile
import threading
import time
import unittest


class EmbeddedNginx(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library = ctypes.CDLL(sys.argv[1])
        cls.library.qfli_nginx_version.restype = ctypes.c_char_p
        cls.library.qfli_nginx_start.argtypes = [ctypes.c_char_p, ctypes.c_int]
        cls.library.qfli_nginx_start.restype = ctypes.c_int64
        cls.library.qfli_nginx_poll.argtypes = [ctypes.c_int64, ctypes.POINTER(ctypes.c_int)]
        cls.library.qfli_nginx_stop.argtypes = [ctypes.c_int64]
        cls.library.qfli_nginx_release.argtypes = [ctypes.c_int64]

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="qfli-embedded-test-")
        self.prefix = Path(self.directory.name)
        (self.prefix / "index.html").write_text("actual embedded upstream", encoding="utf-8")
        self.token = None
        self.peer = None
        self.write_config()

    def tearDown(self):
        if self.peer:
            self.peer.close()
        if self.token:
            self.library.qfli_nginx_stop(self.token)
            self.finish(0)
        self.directory.cleanup()

    def write_config(self, extra="", core="daemon off; master_process off;", port=None):
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            self.port = port or reservation.getsockname()[1]
        (self.prefix / "nginx.conf").write_text(f"""
{core}
pid nginx.pid;
error_log stderr warn;
events {{ worker_connections 64; }}
http {{
  access_log access.log;
  client_body_temp_path client_temp;
  proxy_temp_path proxy_temp;
  proxy_buffering off;
  server {{
    listen 127.0.0.1:{self.port};
    root "{self.prefix}";
    add_header X-Qfli-Engine nginx always;
    {extra}
  }}
}}
""", encoding="utf-8")

    def start(self, test=False):
        self.token = self.library.qfli_nginx_start(os.fsencode(self.prefix), int(test))
        self.assertGreater(self.token, 0)
        return self.token

    def finish(self, expected):
        code = ctypes.c_int()
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            result = self.library.qfli_nginx_poll(self.token, ctypes.byref(code))
            if result == 1:
                token = self.token
                self.assertEqual(self.library.qfli_nginx_release(token), 0)
                self.token = None
                self.assertEqual(code.value, expected)
                return token
            self.assertEqual(result, 0)
            time.sleep(0.01)
        self.fail("native worker did not complete its cleanup")

    def get(self, path="/"):
        deadline = time.monotonic() + 4
        while True:
            connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
            try:
                connection.request("GET", path)
                response = connection.getresponse()
                return response.status, dict(response.getheaders()), response.read()
            except ConnectionRefusedError:
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.01)
            finally:
                connection.close()

    def test_actual_version_static_and_404(self):
        self.assertEqual(self.library.qfli_nginx_version(), b"1.31.6")
        self.start()
        status, headers, body = self.get()
        self.assertEqual((status, body), (200, b"actual embedded upstream"))
        self.assertEqual(headers["Server"], "nginx/1.31.6")
        self.assertEqual(headers["X-Qfli-Engine"], "nginx")
        self.assertEqual(self.get("/missing.js")[0], 404)

    def test_configuration_check_then_server(self):
        self.start(test=True)
        self.finish(0)
        self.start()
        self.assertEqual(self.get()[0], 200)

    def test_access_log_after_configuration_check(self):
        # Regression: the embedded engine reuses process-global time state across
        # nginx invocations. A configuration check (-t) followed by the server
        # used to leave ngx_time() at 0, which made the HTTP log handler treat
        # every line as a disk-full duplicate and skip it, leaving access.log
        # empty. The real editor always validates before starting.
        self.start(test=True)
        self.finish(0)
        self.start()
        self.assertEqual(self.get("/")[0], 200)
        deadline = time.monotonic() + 2
        access = self.prefix / "access.log"
        while time.monotonic() < deadline:
            if access.exists() and access.stat().st_size > 0:
                break
            time.sleep(0.05)
        self.assertIn('"GET / HTTP/1.1" 200', access.read_text(), "access log line missing after -t")

    def test_bad_config_and_unsafe_core_recovery(self):
        for text in ["bad_directive;", "daemon on; master_process off;", "daemon off; master_process on;",
                     "daemon off; master_process off; timer_resolution 10ms;"]:
            self.write_config(core=text)
            self.start(test=True)
            self.finish(1)
        self.assertIn("embedded Nginx requires", (self.prefix / "error.log").read_text())
        self.write_config()
        self.start()
        self.assertEqual(self.get()[0], 200)

    def test_conflict_recovery_and_rebind(self):
        with socket.socket() as occupied:
            occupied.bind(("127.0.0.1", 0))
            occupied.listen()
            self.write_config(port=occupied.getsockname()[1])
            self.start()
            self.finish(1)
        self.assertIn("Address already in use", (self.prefix / "error.log").read_text())
        self.start()
        self.assertEqual(self.get()[0], 200)
        self.library.qfli_nginx_stop(self.token)
        self.finish(0)
        with socket.socket() as rebound:
            rebound.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            rebound.bind(("127.0.0.1", self.port))

    def test_busy_and_stale_tokens(self):
        old = self.start()
        self.assertEqual(self.get()[0], 200)
        self.assertEqual(self.library.qfli_nginx_start(os.fsencode(self.prefix), 0), -errno.EBUSY)
        self.assertEqual(self.library.qfli_nginx_release(old), -errno.EBUSY)
        self.library.qfli_nginx_stop(old)
        self.finish(0)
        self.start()
        self.assertEqual(self.library.qfli_nginx_stop(old), 0)
        self.assertEqual(self.library.qfli_nginx_release(old), 0)
        self.assertEqual(self.get()[0], 200)

    def test_stop_before_backend_ready(self):
        for _ in range(20):
            self.start()
            for _ in range(10):
                self.assertEqual(self.library.qfli_nginx_stop(self.token), 0)
            self.finish(0)

    def test_proxy_request_fidelity(self):
        class Echo(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers["Content-Length"]))
                self.send_response(201)
                self.send_header("X-Request-Path", self.path)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            def log_message(self, *args):
                pass
        upstream = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Echo)
        worker = threading.Thread(target=upstream.serve_forever)
        worker.start()
        try:
            self.write_config(extra=f"location /api/ {{ proxy_pass http://127.0.0.1:{upstream.server_port}/v1/; }}")
            self.start()
            self.get()
            client = http.client.HTTPConnection("127.0.0.1", self.port, timeout=4)
            body = b"large real proxy body\x00" * 4000
            client.request("POST", "/api/items?q=7", body)
            response = client.getresponse()
            self.assertEqual(response.status, 201)
            self.assertEqual(response.getheader("X-Request-Path"), "/v1/items?q=7")
            self.assertEqual(response.read(), body)
            client.close()
        finally:
            upstream.shutdown()
            upstream.server_close()
            worker.join()

    def test_stop_with_active_proxy_and_idle_http(self):
        with socket.socket() as upstream:
            upstream.bind(("127.0.0.1", 0))
            upstream.listen()
            upstream.settimeout(3)
            self.write_config(extra=f"location /slow {{ proxy_pass http://127.0.0.1:{upstream.getsockname()[1]}; }}")
            self.start()
            self.get()
            self.peer = socket.create_connection(("127.0.0.1", self.port))
            self.peer.sendall(b"GET /slow HTTP/1.1\r\nHost: localhost\r\n\r\n")
            remote, _ = upstream.accept()
            with remote:
                remote.settimeout(2)
                self.assertIn(b"GET /slow", remote.recv(4096))
                self.library.qfli_nginx_stop(self.token)
                self.finish(0)
                self.assertEqual(remote.recv(4096), b"")
        self.peer.close()
        self.peer = None
        self.start()
        self.get()
        self.peer = socket.create_connection(("127.0.0.1", self.port))
        self.peer.sendall(b"GET / HTTP/1.1\r\nHost:")
        self.library.qfli_nginx_stop(self.token)
        self.finish(0)

    def test_host_and_descriptor_preservation(self):
        libc = ctypes.CDLL(None)
        os.environ["QFLI_EMBEDDED_HOST_SENTINEL"] = "preserved"
        before_environment = ctypes.c_void_p.in_dll(libc, "environ").value
        before_signals = {s: signal.getsignal(s) for s in [signal.SIGPIPE, signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGALRM]}
        before_stdio = [os.fstat(fd) for fd in range(3)]
        before_cwd = os.getcwd()
        before_descriptors = len(os.listdir("/proc/self/fd"))
        for _ in range(40):
            self.start()
            self.get()
            self.library.qfli_nginx_stop(self.token)
            self.finish(0)
        self.assertEqual(len(os.listdir("/proc/self/fd")), before_descriptors)
        self.assertEqual(ctypes.c_void_p.in_dll(libc, "environ").value, before_environment)
        self.assertEqual({s: signal.getsignal(s) for s in before_signals}, before_signals)
        self.assertEqual([os.fstat(fd) for fd in range(3)], before_stdio)
        self.assertEqual(os.getcwd(), before_cwd)
        self.assertEqual(os.environ["QFLI_EMBEDDED_HOST_SENTINEL"], "preserved")


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]], verbosity=2)
