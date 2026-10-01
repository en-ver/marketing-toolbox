"""Process-safe native OAuth lifecycle coordination contracts.

Workers install network, ADC, and keyring barriers before importing application code.
They use a synthetic file-backed keyring only so separate spawned processes can
exercise the production lock without touching an OS credential store.
"""

from __future__ import annotations

import contextlib
import json
import multiprocessing
import os
import socket
import stat
from pathlib import Path
from queue import Empty
from typing import Any

import pytest


def _deny_network(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("OAuth locking tests must not use network services")


class _FileBackend:
    """Tiny synthetic keyring shared by workers only while production holds its lock."""

    def __init__(
        self,
        state_path: Path,
        *,
        fail_write: bool = False,
        read_entered: Any | None = None,
        release_read: Any | None = None,
    ) -> None:
        self.state_path = state_path
        self.fail_write = fail_write
        self.read_entered = read_entered
        self.release_read = release_read

    def _read(self) -> dict[str, str]:
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}

    def _write(self, records: dict[str, str]) -> None:
        self.state_path.write_text(json.dumps(records), encoding="utf-8")

    @staticmethod
    def _key(service: str, username: str) -> str:
        return f"{service}\0{username}"

    def get_password(self, service: str, username: str) -> str | None:
        if self.read_entered is not None:
            self.read_entered.set()
            assert self.release_read is not None
            assert self.release_read.wait(10)
        return self._read().get(self._key(service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        records = self._read()
        records[self._key(service, username)] = password
        self._write(records)
        if self.fail_write:
            raise RuntimeError("synthetic set failure")

    def delete_password(self, service: str, username: str) -> None:
        records = self._read()
        records.pop(self._key(service, username), None)
        self._write(records)


class _WinVaultBackpackBackend:
    """Faithfully model keyring 25.6.0 WinVault bare/compound targets."""

    def __init__(
        self,
        state_path: Path,
        snapshot_read: Any | None = None,
        release_snapshot: Any | None = None,
        active_writers: Any | None = None,
        concurrent_entry: Any | None = None,
    ) -> None:
        self.state_path = state_path
        self.snapshot_read = snapshot_read
        self.release_snapshot = release_snapshot
        self.active_writers = active_writers
        self.concurrent_entry = concurrent_entry

    def _read(self) -> dict[str, dict[str, str]]:
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}

    def _write(self, targets: dict[str, dict[str, str]]) -> None:
        self.state_path.write_text(json.dumps(targets), encoding="utf-8")

    @staticmethod
    def _compound_name(username: str, service: str) -> str:
        return f"{username}@{service}"

    def _read_credential(self, target: str) -> dict[str, str] | None:
        return self._read().get(target)

    def get_password(self, service: str, username: str) -> str | None:
        credential = self._read_credential(service)
        if credential is None or credential["username"] != username:
            credential = self._read_credential(self._compound_name(username, service))
        return None if credential is None else credential["password"]

    def set_password(self, service: str, username: str, password: str) -> None:
        # keyring.backends.Windows.WinVault.set_password reads the bare target,
        # moves that one credential to username@service, then writes the new
        # credential under the bare service target.
        existing = self._read_credential(service)
        if self.snapshot_read is not None:
            self.snapshot_read.set()
            assert self.release_snapshot is not None
            assert self.active_writers is not None
            with self.active_writers.get_lock():
                if self.active_writers.value:
                    assert self.concurrent_entry is not None
                    self.concurrent_entry.set()
                    raise AssertionError("concurrent WinVault backpack mutation")
                self.active_writers.value += 1
            try:
                assert self.release_snapshot.wait(10)
            finally:
                with self.active_writers.get_lock():
                    self.active_writers.value -= 1

        targets = self._read()
        if existing is not None:
            targets[self._compound_name(existing["username"], service)] = existing
        targets[service] = {"username": username, "password": str(password)}
        self._write(targets)

    def delete_password(self, service: str, username: str) -> None:
        targets = self._read()
        deleted = False
        for target in (service, self._compound_name(username, service)):
            existing = targets.get(target)
            if existing is not None and existing["username"] == username:
                deleted = True
                targets.pop(target)
        if not deleted:
            raise RuntimeError("synthetic missing password")
        self._write(targets)


def _install_worker_barriers() -> None:
    """Install every external-service barrier before application import."""
    socket.create_connection = _deny_network  # type: ignore[assignment]
    socket.getaddrinfo = _deny_network  # type: ignore[assignment]
    import google.auth
    import keyring

    google.auth.default = _deny_network  # type: ignore[assignment]
    keyring.get_keyring = _deny_network  # type: ignore[assignment]


def _oauth_for_worker(root: str, backend: Any) -> Any:
    _install_worker_barriers()
    from marketing_common import oauth

    root_path = Path(root)
    oauth._canonical_oauth_lock_path = lambda: root_path / "locks" / "service.lock"
    oauth.marker_path = lambda tool, access: (
        root_path / "markers" / tool / f"{access}.json"
    )
    oauth._approved_backend = lambda: backend
    oauth.urlopen = _deny_network
    return oauth


def _credentials(oauth: Any, scope: str, token: str) -> Any:
    return oauth.UserCredentials(
        token="access",
        refresh_token=token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id="client",
        client_secret="secret",
        scopes=[scope],
    )


def _storage_worker(
    action: str,
    root: str,
    tool: str,
    access: str,
    token: str,
    marker_published: Any,
    release_marker: Any,
    fail_write: bool,
    invoked: Any,
    results: Any,
    forget_lock_attempted: Any | None = None,
    forget_read_entered: Any | None = None,
    release_forget_read: Any | None = None,
) -> None:
    backend = _FileBackend(
        Path(root) / "keyring.json",
        fail_write=fail_write,
        read_entered=forget_read_entered,
        release_read=release_forget_read,
    )
    oauth = _oauth_for_worker(root, backend)
    if marker_published is not None:
        production_write_marker = oauth._write_marker

        def pause_after_marker(path: Path) -> None:
            production_write_marker(path)
            marker_published.set()
            assert release_marker is not None
            assert release_marker.wait(10)

        oauth._write_marker = pause_after_marker
    if forget_lock_attempted is not None:
        production_lock = oauth._native_oauth_lock

        @contextlib.contextmanager
        def observe_forget_lock_attempt() -> Any:
            forget_lock_attempted.set()
            with production_lock():
                yield

        oauth._native_oauth_lock = observe_forget_lock_attempt
    if invoked is not None:
        invoked.set()
    try:
        if action == "store":
            scope = oauth.scope_for_access(tool, access)
            oauth.store_native_credentials(
                tool, access, _credentials(oauth, scope, token)
            )
            results.put((action, "stored"))
        elif action == "forget":
            oauth.forget_native_credentials(tool, access)
            results.put((action, "forgotten"))
        elif action == "status":
            scope = oauth.scope_for_access(tool, access)
            results.put((action, oauth.native_record_status(tool, access, scope)))
        else:
            raise AssertionError(f"unsupported worker action: {action}")
    except oauth.OAuthAuthenticationError as exc:
        results.put((action, type(exc).__name__, str(exc)))


def _backpack_store_worker(
    root: str,
    tool: str,
    access: str,
    token: str,
    invoked: Any,
    snapshot_read: Any,
    release_snapshot: Any,
    active_writers: Any,
    concurrent_entry: Any,
    results: Any,
) -> None:
    backend = _WinVaultBackpackBackend(
        Path(root) / "winvault-backpack.json",
        snapshot_read,
        release_snapshot,
        active_writers,
        concurrent_entry,
    )
    oauth = _oauth_for_worker(root, backend)
    invoked.set()
    try:
        scope = oauth.scope_for_access(tool, access)
        oauth.store_native_credentials(tool, access, _credentials(oauth, scope, token))
        results.put(("store", "stored"))
    except oauth.OAuthAuthenticationError as exc:
        results.put(("store", type(exc).__name__, str(exc)))


def _lock_holder(root: str, entered: Any, release: Any) -> None:
    backend = _FileBackend(Path(root) / "keyring.json")
    oauth = _oauth_for_worker(root, backend)
    with oauth._native_oauth_lock():
        entered.set()
        assert release.wait(10)


def _lock_exit_holder(root: str, entered: Any) -> None:
    backend = _FileBackend(Path(root) / "keyring.json")
    oauth = _oauth_for_worker(root, backend)
    with oauth._native_oauth_lock():
        entered.set()
        os._exit(0)


def _drain(results: Any, expected: int) -> list[tuple[object, ...]]:
    received: list[tuple[object, ...]] = []
    for _ in range(expected):
        try:
            received.append(results.get(timeout=10))
        except Empty as exc:
            raise AssertionError("worker did not return a result") from exc
    return received


def _join(processes: list[multiprocessing.Process]) -> None:
    for process in processes:
        process.join(10)
    stalled = [process for process in processes if process.is_alive()]
    for process in stalled:
        process.terminate()
    for process in stalled:
        process.join(5)
    assert not stalled, "worker did not stop after its bounded synchronization"
    assert all(process.exitcode == 0 for process in processes)


def test_store_then_forget_process_race_leaves_no_orphan(tmp_path: Path) -> None:
    context = multiprocessing.get_context("spawn")
    marker_published = context.Event()
    release_marker = context.Event()
    forget_lock_attempted = context.Event()
    forget_read_entered = context.Event()
    release_forget_read = context.Event()
    results = context.Queue()
    root = str(tmp_path)
    store = context.Process(
        target=_storage_worker,
        args=(
            "store",
            root,
            "ga4datactl",
            "read",
            "one",
            marker_published,
            release_marker,
            False,
            None,
            results,
        ),
    )
    forget = context.Process(
        target=_storage_worker,
        args=(
            "forget",
            root,
            "ga4datactl",
            "read",
            "",
            None,
            None,
            False,
            None,
            results,
        ),
        kwargs={
            "forget_lock_attempted": forget_lock_attempted,
            "forget_read_entered": forget_read_entered,
            "release_forget_read": release_forget_read,
        },
    )
    processes = [store]
    store.start()
    try:
        assert marker_published.wait(10)
        assert (tmp_path / "markers" / "ga4datactl" / "read.json").exists()
        forget.start()
        processes.append(forget)
        # This is set by the real production lock context manager, rather than
        # immediately before calling forget. The backend event is set only by
        # the forget operation's production keyring read.
        assert forget_lock_attempted.wait(10)
        assert not forget_read_entered.wait(1)

        # Releasing now would create an orphan in an unlocked implementation:
        # its forget operation has already reached and paused in this read,
        # then deletes before the store writes the secret. The service lock
        # keeps that read unreachable until the paused store completes.
        release_marker.set()
        assert forget_read_entered.wait(10)
        release_forget_read.set()
    finally:
        release_marker.set()
        release_forget_read.set()
        _join(processes)

    assert sorted(_drain(results, 2)) == [("forget", "forgotten"), ("store", "stored")]
    assert not (tmp_path / "markers" / "ga4datactl" / "read.json").exists()
    assert json.loads((tmp_path / "keyring.json").read_text(encoding="utf-8")) == {}


def test_failed_store_compensation_cannot_erase_concurrent_replacement(
    tmp_path: Path,
) -> None:
    context = multiprocessing.get_context("spawn")
    started = context.Event()
    release = context.Event()
    results = context.Queue()
    root = str(tmp_path)
    failed = context.Process(
        target=_storage_worker,
        args=(
            "store",
            root,
            "ga4datactl",
            "read",
            "broken",
            started,
            release,
            True,
            None,
            results,
        ),
    )
    failed.start()
    assert started.wait(10)
    replacement = context.Process(
        target=_storage_worker,
        args=(
            "store",
            root,
            "ga4datactl",
            "read",
            "replacement",
            None,
            None,
            False,
            None,
            results,
        ),
    )
    replacement.start()
    release.set()
    _join([failed, replacement])

    outcomes = _drain(results, 2)
    assert ("store", "stored") in outcomes
    assert any(
        outcome[:2] == ("store", "OAuthAuthenticationError")
        and "partial credential was removed" in outcome[2]
        for outcome in outcomes
    )
    records = json.loads((tmp_path / "keyring.json").read_text(encoding="utf-8"))
    assert "replacement" in next(iter(records.values()))
    assert (tmp_path / "markers" / "ga4datactl" / "read.json").exists()


def test_cross_tier_stores_share_one_service_lock_without_losing_records(
    tmp_path: Path,
) -> None:
    context = multiprocessing.get_context("spawn")
    first_invoked = context.Event()
    second_invoked = context.Event()
    first_snapshot_read = context.Event()
    second_snapshot_read = context.Event()
    release_first_snapshot = context.Event()
    release_second_snapshot = context.Event()
    active_writers = context.Value("i", 0)
    concurrent_entry = context.Event()
    results = context.Queue()
    root = str(tmp_path)
    first = context.Process(
        target=_backpack_store_worker,
        args=(
            root,
            "ga4datactl",
            "read",
            "data",
            first_invoked,
            first_snapshot_read,
            release_first_snapshot,
            active_writers,
            concurrent_entry,
            results,
        ),
    )
    second = context.Process(
        target=_backpack_store_worker,
        args=(
            root,
            "gtmctl",
            "publish",
            "gtm",
            second_invoked,
            second_snapshot_read,
            release_second_snapshot,
            active_writers,
            concurrent_entry,
            results,
        ),
    )
    processes = [first]
    first.start()
    try:
        assert first_invoked.wait(10)
        assert first_snapshot_read.wait(10)
        second.start()
        processes.append(second)
        assert second_invoked.wait(10)
        # A per-record lock allows both writes to enter the backend's bare
        # target read/modify/write sequence. The guard then reports the
        # conflicting entry rather than relying on a timing-dependent loss.
        assert not second_snapshot_read.wait(1)
        assert not concurrent_entry.is_set()
        release_first_snapshot.set()
        assert second_snapshot_read.wait(10)
        release_second_snapshot.set()
    finally:
        release_first_snapshot.set()
        release_second_snapshot.set()
        _join(processes)

    assert sorted(_drain(results, 2)) == [("store", "stored"), ("store", "stored")]
    backend = _WinVaultBackpackBackend(tmp_path / "winvault-backpack.json")
    service = "marketing-toolbox.oauth"
    first_name = "ga4datactl:read"
    second_name = "gtmctl:publish"
    # The first record was moved from the bare target to its compound target;
    # the second is the bare target. Both must resolve through that algorithm.
    targets = json.loads(
        (tmp_path / "winvault-backpack.json").read_text(encoding="utf-8")
    )
    assert targets[service]["username"] == second_name
    assert targets[f"{first_name}@{service}"]["username"] == first_name
    first_record = backend.get_password(service, first_name)
    second_record = backend.get_password(service, second_name)
    assert first_record is not None
    assert second_record is not None
    assert json.loads(first_record)["refresh_token"] == "data"
    assert json.loads(second_record)["refresh_token"] == "gtm"
    assert not concurrent_entry.is_set()
    assert (tmp_path / "locks" / "service.lock").exists()


def test_reader_waits_for_store_and_observes_one_complete_snapshot(
    tmp_path: Path,
) -> None:
    context = multiprocessing.get_context("spawn")
    started = context.Event()
    release = context.Event()
    results = context.Queue()
    root = str(tmp_path)
    store = context.Process(
        target=_storage_worker,
        args=(
            "store",
            root,
            "ga4datactl",
            "read",
            "one",
            started,
            release,
            False,
            None,
            results,
        ),
    )
    store.start()
    assert started.wait(10)
    reader = context.Process(
        target=_storage_worker,
        args=(
            "status",
            root,
            "ga4datactl",
            "read",
            "",
            None,
            None,
            False,
            None,
            results,
        ),
    )
    reader.start()
    release.set()
    _join([store, reader])

    assert sorted(_drain(results, 2), key=str) == [
        ("status", True),
        ("store", "stored"),
    ]


def test_lock_contention_budget_excludes_filesystem_open(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from marketing_common import oauth

    class ControlledClock:
        now = 0.0

        def monotonic(self) -> float:
            return self.now

        def advance(self, seconds: float) -> None:
            self.now += seconds

    class DelayedThreadGuard:
        def __init__(self, clock: ControlledClock) -> None:
            self.clock = clock
            self.timeouts: list[float] = []

        def acquire(self, timeout: float) -> bool:
            self.timeouts.append(timeout)
            self.clock.advance(2.0)
            return True

        def release(self) -> None:
            pass

    clock = ControlledClock()
    guard = DelayedThreadGuard(clock)
    os_wait_budgets: list[float] = []
    closed: list[int] = []
    monkeypatch.setattr(oauth.time, "monotonic", clock.monotonic)
    monkeypatch.setattr(oauth, "_native_oauth_thread_lock", guard)
    monkeypatch.setattr(
        oauth, "_canonical_oauth_lock_path", lambda: tmp_path / "service.lock"
    )

    def delayed_open(_path: Path) -> int:
        clock.advance(100.0)
        return 123

    def contended_os_lock(descriptor: int, timeout_seconds: float) -> None:
        assert descriptor == 123
        os_wait_budgets.append(timeout_seconds)
        clock.advance(2.5)

    monkeypatch.setattr(oauth, "_open_native_oauth_lock_file", delayed_open)
    monkeypatch.setattr(oauth, "_acquire_os_lock", contended_os_lock)
    monkeypatch.setattr(oauth, "_release_os_lock", lambda _descriptor: None)
    monkeypatch.setattr(oauth.os, "close", closed.append)

    with oauth._native_oauth_lock():
        pass

    # This is injected time, not wall-clock timing: 2s thread wait leaves 3s
    # for OS contention even after 100s of unbudgeted filesystem work.
    assert guard.timeouts == [5.0]
    assert os_wait_budgets == [pytest.approx(3.0)]
    assert clock.now == pytest.approx(104.5)
    assert closed == [123]


def test_contention_is_bounded_and_process_exit_releases_persistent_lock(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    context = multiprocessing.get_context("spawn")
    entered = context.Event()
    release = context.Event()
    holder = context.Process(
        target=_lock_holder, args=(str(tmp_path), entered, release)
    )
    holder.start()
    assert entered.wait(10)

    from marketing_common import oauth

    lock_path = tmp_path / "locks" / "service.lock"
    monkeypatch.setattr(oauth, "_canonical_oauth_lock_path", lambda: lock_path)
    monkeypatch.setattr(oauth, "_NATIVE_OAUTH_LOCK_TIMEOUT_SECONDS", 0.05)
    with (
        pytest.raises(oauth.OAuthAuthenticationError, match="busy; retry"),
        oauth._native_oauth_lock(),
    ):
        pytest.fail("contended lock must not be acquired")
    release.set()
    _join([holder])

    assert lock_path.exists()
    with oauth._native_oauth_lock():
        pass
    assert lock_path.exists()


def test_process_exit_releases_the_persistent_os_lock(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    context = multiprocessing.get_context("spawn")
    entered = context.Event()
    holder = context.Process(target=_lock_exit_holder, args=(str(tmp_path), entered))
    holder.start()
    assert entered.wait(10)
    _join([holder])

    from marketing_common import oauth

    lock_path = tmp_path / "locks" / "service.lock"
    monkeypatch.setattr(oauth, "_canonical_oauth_lock_path", lambda: lock_path)
    with oauth._native_oauth_lock():
        pass
    assert lock_path.exists()


def test_exception_releases_the_thread_and_os_lock(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from marketing_common import oauth

    lock_path = tmp_path / "locks" / "service.lock"
    monkeypatch.setattr(oauth, "_canonical_oauth_lock_path", lambda: lock_path)
    with pytest.raises(RuntimeError, match="synthetic"), oauth._native_oauth_lock():
        raise RuntimeError("synthetic")
    with oauth._native_oauth_lock():
        pass


def test_unlock_failure_closes_descriptor_and_releases_thread_lock(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from marketing_common import oauth

    lock_path = tmp_path / "locks" / "service.lock"
    release_os_lock = oauth._release_os_lock
    close = oauth.os.close
    release_attempted: list[int] = []
    closed: list[int] = []
    monkeypatch.setattr(oauth, "_canonical_oauth_lock_path", lambda: lock_path)

    def fail_release(descriptor: int) -> None:
        release_attempted.append(descriptor)
        raise OSError("synthetic unlock failure")

    def record_close(descriptor: int) -> None:
        if release_attempted:
            closed.append(descriptor)
        close(descriptor)

    monkeypatch.setattr(oauth, "_release_os_lock", fail_release)
    monkeypatch.setattr(oauth.os, "close", record_close)
    with (
        pytest.raises(
            oauth.OAuthAuthenticationError, match="coordination is unavailable"
        ),
        oauth._native_oauth_lock(),
    ):
        pass
    assert closed == release_attempted

    monkeypatch.setattr(oauth, "_release_os_lock", release_os_lock)
    monkeypatch.setattr(oauth.os, "close", close)
    with oauth._native_oauth_lock():
        pass


def test_close_failure_is_sanitized_and_releases_thread_lock(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from marketing_common import oauth

    lock_path = tmp_path / "locks" / "service.lock"
    close = oauth.os.close
    closed: list[int] = []
    monkeypatch.setattr(oauth, "_canonical_oauth_lock_path", lambda: lock_path)

    def close_then_fail(descriptor: int) -> None:
        closed.append(descriptor)
        close(descriptor)
        raise OSError("synthetic close failure")

    monkeypatch.setattr(oauth.os, "close", close_then_fail)
    with (
        pytest.raises(
            oauth.OAuthAuthenticationError, match="coordination is unavailable"
        ),
        oauth._native_oauth_lock(),
    ):
        pass
    assert len(closed) == 1

    monkeypatch.setattr(oauth.os, "close", close)
    with oauth._native_oauth_lock():
        pass


def test_lock_file_is_noninheritable_regular_and_single_link(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from marketing_common import oauth

    lock_path = tmp_path / "locks" / "service.lock"
    monkeypatch.setattr(oauth, "_canonical_oauth_lock_path", lambda: lock_path)
    descriptor = oauth._open_native_oauth_lock_file(lock_path)
    try:
        details = os.fstat(descriptor)
        assert not os.get_inheritable(descriptor)
        assert stat.S_ISREG(details.st_mode)
        assert details.st_nlink == 1
    finally:
        os.close(descriptor)


@pytest.mark.skipif(os.name != "posix", reason="POSIX lock mode checks")
def test_lock_rejects_nonprivate_mode_reuse(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from marketing_common import oauth

    lock_path = tmp_path / "locks" / "service.lock"
    monkeypatch.setattr(oauth, "_canonical_oauth_lock_path", lambda: lock_path)
    with oauth._native_oauth_lock():
        pass
    assert stat.S_IMODE(lock_path.stat().st_mode) == 0o600

    lock_path.chmod(0o644)
    with (
        pytest.raises(
            oauth.OAuthAuthenticationError, match="coordination is unavailable"
        ),
        oauth._native_oauth_lock(),
    ):
        pass


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX O_NOFOLLOW")
def test_lock_rejects_a_symlink_final_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from marketing_common import oauth

    lock_path = tmp_path / "locks" / "service.lock"
    monkeypatch.setattr(oauth, "_canonical_oauth_lock_path", lambda: lock_path)
    with oauth._native_oauth_lock():
        pass
    lock_path.unlink()
    target = tmp_path / "target.lock"
    target.write_text("", encoding="utf-8")
    lock_path.symlink_to(target)
    with (
        pytest.raises(
            oauth.OAuthAuthenticationError, match="coordination is unavailable"
        ),
        oauth._native_oauth_lock(),
    ):
        pass


def test_lock_rejects_hardlinks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from marketing_common import oauth

    lock_path = tmp_path / "locks" / "service.lock"
    monkeypatch.setattr(oauth, "_canonical_oauth_lock_path", lambda: lock_path)
    with oauth._native_oauth_lock():
        pass
    hardlink = tmp_path / "other.lock"
    os.link(lock_path, hardlink)
    with (
        pytest.raises(
            oauth.OAuthAuthenticationError, match="coordination is unavailable"
        ),
        oauth._native_oauth_lock(),
    ):
        pass


@pytest.mark.skipif(os.name != "posix", reason="POSIX lock hierarchy checks")
def test_lock_rejects_nonprivate_app_hierarchy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from marketing_common import oauth

    lock_path = tmp_path / "locks" / "service.lock"
    monkeypatch.setattr(oauth, "_canonical_oauth_lock_path", lambda: lock_path)
    with oauth._native_oauth_lock():
        pass
    lock_path.parent.chmod(0o755)
    with (
        pytest.raises(
            oauth.OAuthAuthenticationError, match="coordination is unavailable"
        ),
        oauth._native_oauth_lock(),
    ):
        pass


def test_selected_marker_absence_skips_lock_and_keyring(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from marketing_common import oauth

    monkeypatch.setattr(
        oauth,
        "marker_path",
        lambda *_args: tmp_path / "markers" / "ga4datactl" / "read.json",
    )
    monkeypatch.setattr(
        oauth,
        "_canonical_oauth_lock_path",
        lambda: pytest.fail("absent marker must not open the canonical lock"),
    )
    monkeypatch.setattr(
        oauth,
        "_approved_backend",
        lambda: pytest.fail("absent marker must not access keyring"),
    )

    assert (
        oauth.load_native_credentials_if_present(
            "ga4datactl", "read", oauth.SCOPE_CATALOG["ga4datactl"]["read"]
        )
        is None
    )
    assert not oauth.native_record_status(
        "ga4datactl", "read", oauth.SCOPE_CATALOG["ga4datactl"]["read"]
    )
    oauth.forget_native_credentials("ga4datactl", "read")


def test_marker_roots_do_not_change_canonical_lock_identity(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from marketing_common import oauth

    canonical = tmp_path / "canonical" / "service.lock"
    paths = {
        "ga4datactl": tmp_path / "first-root" / "ga4datactl" / "read.json",
        "gtmctl": tmp_path / "second-root" / "gtmctl" / "read.json",
    }
    monkeypatch.setattr(oauth, "_canonical_oauth_lock_path", lambda: canonical)
    monkeypatch.setattr(oauth, "marker_path", lambda tool, access: paths[tool])
    backend = _FileBackend(tmp_path / "keyring.json")
    monkeypatch.setattr(oauth, "_approved_backend", lambda: backend)

    for tool, access, token in (
        ("ga4datactl", "read", "one"),
        ("gtmctl", "read", "two"),
    ):
        scope = oauth.scope_for_access(tool, access)
        oauth.store_native_credentials(tool, access, _credentials(oauth, scope, token))

    assert canonical.exists()
    assert all(path.exists() for path in paths.values())
