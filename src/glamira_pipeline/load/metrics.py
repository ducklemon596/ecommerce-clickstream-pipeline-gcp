"""Per-component timing and CPU accounting for a load run.

Components are measured where they happen, so a run reports how long the
loader spent reading/decompressing, splitting, waiting for insert slots,
inserting and checkpointing, without a separate benchmark harness.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import logging
import resource
import threading
import time

LOGGER = logging.getLogger(__name__)
WINDOW_DOCS = 1_000_000


def _cpu(who: int) -> tuple[float, float]:
    usage = resource.getrusage(who)
    return usage.ru_utime, usage.ru_stime


@dataclass
class LoadMetrics:
    """Wall-clock seconds per component plus CPU of this process and of the decompressor.

    - ``source_wait_s``: producer blocked reading decompressed bytes.
    - ``split_s``: producer cutting documents into batches (excluding reads).
    - ``slot_wait_s``: producer blocked because all insert slots were busy
      (high means MongoDB is the bottleneck).
    - ``insert_wall_s`` / ``insert_cpu_s``: summed over worker threads; CPU is
      client-side only (building and sending messages), not ``mongod``.
    """

    hash_s: float = 0.0
    source_wait_s: float = 0.0
    split_s: float = 0.0
    slot_wait_s: float = 0.0
    insert_wall_s: float = 0.0
    insert_cpu_s: float = 0.0
    checkpoint_s: float = 0.0
    finalize_s: float = 0.0
    total_wall_s: float = 0.0
    process_cpu_user_s: float = 0.0
    process_cpu_sys_s: float = 0.0
    decompressor_cpu_s: float = 0.0
    peak_rss_mb: int = 0
    docs_per_s: float = 0.0
    windows: list[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._lock = threading.Lock()
        self._started = time.perf_counter()
        self._cpu0 = _cpu(resource.RUSAGE_SELF)
        self._children0 = sum(_cpu(resource.RUSAGE_CHILDREN))
        self._window_start = self._started
        self._next_window = WINDOW_DOCS

    def record_insert(self, wall: float, cpu: float) -> None:
        """Add one batch's insert time; safe to call from worker threads."""
        with self._lock:
            self.insert_wall_s += wall
            self.insert_cpu_s += cpu

    def record_progress(self, docs_done: int) -> None:
        """Log throughput each time another million documents is processed."""
        while docs_done >= self._next_window:
            now = time.perf_counter()
            rate = round(WINDOW_DOCS / (now - self._window_start))
            self.windows.append({"upto": self._next_window, "docs_per_s": rate})
            LOGGER.info("%s documents processed (%s docs/s in the last million)",
                        f"{self._next_window:,}", f"{rate:,}")
            self._window_start, self._next_window = now, self._next_window + WINDOW_DOCS

    def close(self, docs: int) -> dict:
        """Freeze totals and return a JSON/BSON-friendly dict of rounded values."""
        self.total_wall_s = time.perf_counter() - self._started
        user, system = _cpu(resource.RUSAGE_SELF)
        self.process_cpu_user_s = user - self._cpu0[0]
        self.process_cpu_sys_s = system - self._cpu0[1]
        self.decompressor_cpu_s = sum(_cpu(resource.RUSAGE_CHILDREN)) - self._children0
        self.peak_rss_mb = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
        self.docs_per_s = docs / self.total_wall_s if self.total_wall_s else 0.0
        return {key: round(value, 2) if isinstance(value, float) else value
                for key, value in asdict(self).items()}
