#!/usr/bin/env python3
"""Actual Linux AF_UNIX regression; never launches or claims to test ArkWeb."""

from contextlib import contextmanager
import ctypes
import errno
import fcntl
import os
from pathlib import Path
import signal
import socket
import sys
import threading
import time


MAX_TRANSFER = 64 * 1024
MAX_CONNECTIONS = 8
ADDRESS = b"\0webview_devtools_remote_" + str(os.getpid()).encode("ascii")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def descriptors():
    """Inspect this fixture's fds only; never discover a transport endpoint."""
    result = set()
    for name in os.listdir("/proc/self/fd"):
        try:
            fd = int(name)
            os.fstat(fd)
            result.add(fd)
        except (ValueError, OSError):
            pass  # The temporary fd used by listdir has already closed.
    return result


@contextmanager
def listener(backlog=16):
    # This is the only bound address in the fixture, always this process's PID.
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(ADDRESS)
        server.listen(backlog)
        server.settimeout(2)
        yield server


def accept(server):
    peer, _ = server.accept()
    peer.settimeout(2)
    return peer


class Transport:
    def __init__(self, path):
        library = ctypes.CDLL(str(Path(path).resolve()))
        byte_pointer = ctypes.POINTER(ctypes.c_uint8)
        self.open_call = library.qfli_web_cdp_open_self
        self.open_call.argtypes = []
        self.open_call.restype = ctypes.c_int64
        self.read_call = library.qfli_web_cdp_read
        self.read_call.argtypes = [ctypes.c_int64, byte_pointer, ctypes.c_size_t]
        self.read_call.restype = ctypes.c_int
        self.write_call = library.qfli_web_cdp_write
        self.write_call.argtypes = [ctypes.c_int64, byte_pointer, ctypes.c_size_t]
        self.write_call.restype = ctypes.c_int
        self.close_call = library.qfli_web_cdp_close
        self.close_call.argtypes = [ctypes.c_int64]
        self.close_call.restype = ctypes.c_int
        self.handles = set()

    def open(self):
        handle = self.open_call()
        if handle > 0:
            self.handles.add(handle)
        return handle

    def read(self, handle, capacity=MAX_TRANSFER):
        buffer = (ctypes.c_uint8 * capacity)()
        status = self.read_call(handle, buffer, capacity)
        return status, bytes(buffer[:max(0, status)])

    def write(self, handle, payload):
        buffer = (ctypes.c_uint8 * len(payload)).from_buffer_copy(payload)
        return self.write_call(handle, buffer, len(payload))

    def close(self, handle):
        status = self.close_call(handle)
        # Positive handles retire even when the close syscall reports an error.
        self.handles.discard(handle)
        return status

    def cleanup(self):
        for handle in list(self.handles):
            self.close(handle)


def no_engine(transport):
    baseline = descriptors()
    for _ in range(100):
        status = transport.open()
        require(status in (-errno.ECONNREFUSED, -errno.ENOENT),
                f"no engine must fail without a handle: {status}")
    require(descriptors() == baseline, "failed opens leaked a descriptor")


def bounds_binary_eof(transport):
    baseline = descriptors()
    with listener() as server:
        handle = transport.open()
        require(handle > 0, f"open: {handle}")
        with accept(server) as peer:
            require(transport.read(handle)[0] == -errno.EAGAIN, "empty read must not block")
            guard = (ctypes.c_uint8 * (MAX_TRANSFER + 2))(*([0xA5] * (MAX_TRANSFER + 2)))
            pointer = ctypes.cast(ctypes.byref(guard, 1), ctypes.POINTER(ctypes.c_uint8))
            peer.sendall(b"\x00a\xff")
            require(transport.read_call(handle, None, 1) == -errno.EINVAL, "null read")
            require(transport.read_call(handle, pointer, 0) == -errno.EINVAL, "zero read")
            require(transport.read_call(handle, pointer, MAX_TRANSFER + 1) == -errno.EINVAL,
                    "over-limit read")
            require(bytes(guard) == bytes([0xA5]) * len(guard), "invalid read changed buffer")
            require(transport.read_call(handle, pointer, MAX_TRANSFER) == 3, "short binary read")
            require(bytes(guard[1:4]) == b"\x00a\xff", "binary data changed")
            require(guard[0] == 0xA5 and guard[-1] == 0xA5, "read crossed caller bounds")
            require(transport.write_call(handle, None, 1) == -errno.EINVAL, "null write")
            require(transport.write_call(handle, pointer, 0) == -errno.EINVAL, "zero write")
            require(transport.write_call(handle, pointer, MAX_TRANSFER + 1) == -errno.EINVAL,
                    "over-limit write")
            require(transport.write(handle, b"\x00out\xff") == 5, "binary write count")
            require(peer.recv(64) == b"\x00out\xff", "binary write content")
            peer.shutdown(socket.SHUT_WR)
            require(transport.read(handle)[0] == 0, "peer half-close must produce EOF")
            require(transport.read(handle)[0] == 0, "EOF must remain sticky")
            require(transport.write(handle, b"still-open") == 10, "EOF must not close write half")
            require(peer.recv(64) == b"still-open", "half-close write content")
        require(transport.close(handle) == 0, "close")
        require(transport.close(handle) == 0, "repeated close")
        require(transport.read(handle)[0] == -errno.EBADF, "stale read")
        require(transport.write(handle, b"x") == -errno.EBADF, "stale write")
        require(transport.close(0) == -errno.EINVAL, "nonpositive close")
    require(descriptors() == baseline, "bounds/EOF descriptor leak")


def short_write_backpressure(transport):
    baseline = descriptors()
    with listener() as server:
        before = descriptors()
        handle = transport.open()
        require(handle > 0, f"open: {handle}")
        created = descriptors() - before
        require(len(created) == 1, "one raw client descriptor expected")
        fd = created.pop()
        require(fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_NONBLOCK, "client must be nonblocking")
        require(fcntl.fcntl(fd, fcntl.F_GETFD) & fcntl.FD_CLOEXEC, "client must be close-on-exec")
        # Only duplicate our freshly created client fd to force kernel pressure.
        # No production API or test-only hook exposes/configures a descriptor.
        with socket.fromfd(fd, socket.AF_UNIX, socket.SOCK_STREAM) as inspection:
            inspection.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)
        with accept(server) as peer:
            payload = bytes(range(256)) * 256
            accepted = []
            for _ in range(32):
                count = transport.write(handle, payload)
                if count == -errno.EAGAIN:
                    break
                require(0 < count <= MAX_TRANSFER, f"write result: {count}")
                accepted.append(payload[:count])
            else:
                raise AssertionError("bounded writes never reached EAGAIN")
            require(any(len(part) < MAX_TRANSFER for part in accepted), "real short write expected")
            expected = b"".join(accepted)
            received = bytearray()
            while len(received) < len(expected):
                chunk = peer.recv(min(MAX_TRANSFER, len(expected) - len(received)))
                require(chunk, "peer EOF during drain")
                received.extend(chunk)
            require(bytes(received) == expected, "accepted byte counts/content differ")
            require(transport.write(handle, b"recovered") == 9, "write after drain")
            require(peer.recv(64) == b"recovered", "recovered write content")
        require(transport.close(handle) == 0, "backpressure close")
    require(descriptors() == baseline, "backpressure descriptor leak")


def handle_limit_generation(transport):
    baseline = descriptors()
    with listener() as server:
        handles = []
        peers = []
        try:
            for _ in range(MAX_CONNECTIONS):
                handle = transport.open()
                require(handle > 0, f"open within limit: {handle}")
                handles.append(handle)
                peers.append(accept(server))
            full = descriptors()
            require(transport.open() == -errno.EMFILE, "handle limit")
            require(descriptors() == full, "limit failure leaked a descriptor")
            old = handles.pop(0)
            peers.pop(0).close()
            require(transport.close(old) == 0, "release slot")
            newer = transport.open()
            require(newer > max(handles + [old]), "opaque generations must never repeat")
            handles.append(newer)
            peers.append(accept(server))
            require(transport.close(old) == 0, "old close after slot reuse")
            require(transport.read(old)[0] == -errno.EBADF, "old read after reuse")
            require(transport.write(newer, b"new") == 3, "old close damaged newer connection")
            require(peers[-1].recv(8) == b"new", "new generation payload")
        finally:
            for handle in handles:
                transport.close(handle)
            for peer in peers:
                peer.close()
    require(descriptors() == baseline, "handle-generation descriptor leak")


def full_backlog_retry(transport):
    baseline = descriptors()
    with listener(backlog=0) as server:
        first = transport.open()
        require(first > 0, f"first backlog connection: {first}")
        full = descriptors()
        for _ in range(20):
            require(transport.open() == -errno.EAGAIN, "full AF_UNIX backlog needs a fresh retry")
        require(descriptors() == full, "backlog retries leaked descriptors or handles")
        with accept(server):
            require(transport.close(first) == 0, "backlog first close")
        retry = transport.open()
        require(retry > first, "new open after backlog drained")
        with accept(server):
            require(transport.close(retry) == 0, "backlog retry close")
    require(descriptors() == baseline, "backlog descriptor leak")


def broken_peer_sigpipe(transport):
    baseline = descriptors()
    previous = signal.getsignal(signal.SIGPIPE)
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    try:
        with listener() as server:
            before = descriptors()
            handle = transport.open()
            require(handle > 0, f"open: {handle}")
            peer = accept(server)
            peer.close()
            require(transport.read(handle)[0] == 0, "closed peer EOF")
            status = transport.write(handle, b"must-not-signal")
            require(status in (-errno.EPIPE, -errno.ECONNRESET), f"closed peer write: {status}")
            require(transport.read(handle)[0] == status, "terminal read must retain failure")
            require(transport.write(handle, b"again") == status, "terminal write must retain failure")
            require(descriptors() == before, "terminal failure must close the raw descriptor")
            require(signal.getsignal(signal.SIGPIPE) == signal.SIG_DFL, "library changed SIGPIPE handler")
            require(transport.close(handle) == 0, "failed connection close")
            require(transport.close(handle) == 0, "failed connection repeated close")
    finally:
        signal.signal(signal.SIGPIPE, previous)
    require(descriptors() == baseline, "broken-peer descriptor leak")


def concurrent_close(transport):
    baseline = descriptors()
    with listener() as server:
        handle = transport.open()
        require(handle > 0, f"open: {handle}")
        with accept(server):
            start = threading.Barrier(5)
            stop = threading.Event()
            failures = []

            def reader():
                try:
                    start.wait(timeout=2)
                    while True:
                        status, _ = transport.read(handle, 1)
                        require(status in (-errno.EAGAIN, -errno.EBADF), f"concurrent read: {status}")
                        require(transport.close_call(handle) == 0, "concurrent idempotent close")
                        if stop.is_set():
                            break
                except BaseException as error:
                    failures.append(error)

            workers = [threading.Thread(target=reader, daemon=True) for _ in range(4)]
            for worker in workers:
                worker.start()
            try:
                start.wait(timeout=2)
                require(transport.close(handle) == 0, "main close")
                newer = transport.open()
                require(newer > handle, "concurrent reuse generation")
                with accept(server) as peer:
                    require(transport.write(newer, b"safe") == 4, "stale close affected new fd")
                    require(peer.recv(8) == b"safe", "concurrent new payload")
                    require(transport.close(newer) == 0, "concurrent new close")
            finally:
                stop.set()
                for worker in workers:
                    worker.join(timeout=2)
                    require(not worker.is_alive(), "concurrent operation did not finish")
            require(not failures, f"worker failures: {failures}")
    require(descriptors() == baseline, "concurrent-close descriptor leak")


def main():
    if not sys.platform.startswith("linux"):
        raise SystemExit("This actual abstract-AF_UNIX fixture requires Linux")
    if len(sys.argv) != 2:
        raise SystemExit("usage: test_web_cdp_transport.py <compiled-C-ABI-library>")
    transport = Transport(sys.argv[1])
    baseline = descriptors()
    started = time.monotonic()
    cases = [no_engine, bounds_binary_eof, short_write_backpressure,
             handle_limit_generation, full_backlog_retry, broken_peer_sigpipe,
             concurrent_close]
    try:
        for case in cases:
            case(transport)
            require(not transport.handles, f"{case.__name__}: unreleased handle")
            print(f"PASS {case.__name__}", flush=True)
        require(descriptors() == baseline, "suite leaked descriptors")
    finally:
        transport.cleanup()
    elapsed = time.monotonic() - started
    print(f"PASS {len(cases)} real Linux self-socket cases in {elapsed:.3f}s; ArkWeb/NAPI not tested")


if __name__ == "__main__":
    main()
