"""Server-owned live polling, controlled by the local review console."""
import threading
from datetime import datetime, timedelta, timezone

from .operations import poll_once
from .store import connect


def utc_now():
    return datetime.now(timezone.utc)


class LiveScheduler:
    def __init__(self, db_path, employees_path, interval=900):
        self.db_path = db_path
        self.employees_path = employees_path
        self.interval = interval
        self._state_lock = threading.Lock()
        self._poll_lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._manual_thread = None
        self._checking = False
        self._next_check_at = None
        self._last_result = None
        self._last_error = None
        self._started_at = None

    def status(self):
        with self._state_lock:
            running = self._thread is not None and self._thread.is_alive()
            return {
                'running': running and not self._stop.is_set(),
                'stopping': running and self._stop.is_set(),
                'checking': self._checking,
                'interval_seconds': self.interval,
                'next_check_at': self._next_check_at,
                'last_result': self._last_result,
                'last_error': self._last_error,
                'started_at': self._started_at,
            }

    def start(self):
        with self._state_lock:
            if self._thread is not None and self._thread.is_alive():
                if self._stop.is_set():
                    raise ValueError('Previous source check is stopping; try again shortly')
                return self.status_unlocked()
            if self._checking: raise ValueError('A manual website check is still running; start the schedule after it finishes')
            self._stop = threading.Event()
            self._next_check_at = utc_now().isoformat()
            self._last_error = None
            self._thread = threading.Thread(target=self._run, name='atlas-live-scheduler', daemon=True)
            self._thread.start()
            return self.status_unlocked()

    def status_unlocked(self):
        running = self._thread is not None and self._thread.is_alive()
        return {
            'running': running and not self._stop.is_set(),
            'stopping': running and self._stop.is_set(),
            'checking': self._checking,
            'interval_seconds': self.interval,
            'next_check_at': self._next_check_at,
            'last_result': self._last_result,
            'last_error': self._last_error,
            'started_at': self._started_at,
        }

    def stop(self):
        with self._state_lock:
            self._stop.set()
            self._next_check_at = None
            return self.status_unlocked()

    def close(self):
        self.stop()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=2)
        if self._manual_thread is not None:
            self._manual_thread.join(timeout=2)

    def request_check(self):
        """Return immediately; network work uses its own SQLite connection."""
        with self._state_lock:
            if self._checking:
                raise ValueError('A website check is already in progress')
            self._checking=True
            self._last_error=None
            self._last_result=None
            self._started_at=utc_now().isoformat()
            self._manual_thread=threading.Thread(target=self._manual_check,name='atlas-manual-check',daemon=True)
            self._manual_thread.start()
            return self.status_unlocked()

    def _manual_check(self):
        db=None
        try:
            db=connect(self.db_path)
            result=self.check_now(db)
            with self._state_lock:
                self._last_result=result
        except Exception as exc:
            with self._state_lock:
                self._last_error=str(exc)
        finally:
            if db is not None: db.close()
            with self._state_lock:
                self._checking=False

    def check_now(self, db):
        if not self._poll_lock.acquire(blocking=False):
            raise ValueError('A website check is already in progress')
        try:
            return poll_once(db, self.employees_path)
        finally:
            self._poll_lock.release()

    def _run(self):
        while not self._stop.is_set():
            with self._state_lock:
                busy=self._checking
                if not busy:
                    self._checking = True
                    self._last_result=None
                    self._last_error=None
                    self._started_at=utc_now().isoformat()
                self._next_check_at = None
            if busy:
                if self._stop.wait(1): break
                continue
            db = None
            try:
                db = connect(self.db_path)
                result = self.check_now(db)
                with self._state_lock:
                    self._last_result = result
                    self._last_error = None
            except Exception as exc:
                with self._state_lock:
                    self._last_error = str(exc)
            finally:
                if db is not None:
                    db.close()
            with self._state_lock:
                self._checking = False
                self._next_check_at = (utc_now() + timedelta(seconds=self.interval)).isoformat() if not self._stop.is_set() else None
            if self._stop.wait(self.interval):
                break
        with self._state_lock:
            self._checking = False
            self._next_check_at = None
