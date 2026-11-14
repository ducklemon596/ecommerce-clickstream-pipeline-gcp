"""Run documents in ``load_runs``: provenance, single-writer lock and the resume checkpoint.

The checkpoint is a *batch watermark*: every batch below it is known to be in
the target. Batch boundaries are deterministic for a given source and batch
limits, so a later run with the same identity can skip straight to it.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import heapq
import uuid

from pymongo.database import Database
from pymongo.errors import DuplicateKeyError
from pymongo.write_concern import WriteConcern

RUNS_COLLECTION = "load_runs"
RUN_TYPE = "summary_load"
HEARTBEAT_TIMEOUT = timedelta(seconds=120)
RESUMABLE = ("running", "stopped", "failed", "abandoned")


class RunLocked(RuntimeError):
    """Another load into the same target has a live heartbeat."""


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Watermark:
    """Track the highest batch index below which every batch has completed.

    Workers finish out of order; a min-heap holds completed batches until the
    gap below them closes, so the watermark never skips an unfinished batch.
    """

    def __init__(self, next_index: int = 0, offset: int = 0) -> None:
        self.next_index = next_index
        self.offset = offset
        self._done: list[tuple[int, int]] = []

    def complete(self, index: int, end_offset: int) -> None:
        heapq.heappush(self._done, (index, end_offset))
        while self._done and self._done[0][0] == self.next_index:
            _, self.offset = heapq.heappop(self._done)
            self.next_index += 1


class RunStore:
    """Read and write ``load_runs`` documents with journaled writes."""

    def __init__(self, db: Database) -> None:
        self.runs = db[RUNS_COLLECTION].with_options(write_concern=WriteConcern(w=1, j=True))

    def check_lock(self, target: str) -> None:
        """Raise RunLocked if a run on ``target`` is alive; mark stale ``running`` runs as abandoned."""
        for run in self.runs.find({"type": RUN_TYPE, "target.namespace": target, "status": "running"}):
            heartbeat = run["heartbeat_at"].replace(tzinfo=timezone.utc)
            if utcnow() - heartbeat < HEARTBEAT_TIMEOUT:
                raise RunLocked(f"run {run['_id']} is still loading {target}")
            self.runs.update_one({"_id": run["_id"], "status": "running"}, {"$set": {"status": "abandoned"}})

    def latest(self, identity: dict) -> dict | None:
        """Return the most recent run with exactly this identity, if any."""
        return self.runs.find_one({"type": RUN_TYPE, "identity": identity}, sort=[("started_at", -1)])

    def start(self, identity: dict, *, source: dict, target: dict, params: dict,
              resumed_from: str | None, progress: dict, git_sha: str | None) -> str:
        """Insert a ``running`` run document and return its id.

        A partial unique index allows only one ``running`` load per target, so two
        loaders that both pass ``check_lock`` cannot both start: the second gets RunLocked.
        """
        self.runs.create_index([("target.namespace", 1)], name="one_running_load_per_target", unique=True,
                               partialFilterExpression={"type": RUN_TYPE, "status": "running"})
        run_id = utcnow().strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:8]
        now = utcnow()
        try:
            self.runs.insert_one({"_id": run_id, "type": RUN_TYPE, "status": "running", "identity": identity,
                                  "source": source, "target": target, "params": params,
                                  "resumed_from": resumed_from, "git_sha": git_sha, "started_at": now,
                                  "heartbeat_at": now, "finished_at": None, "progress": progress,
                                  "metrics": None, "error": None})
        except DuplicateKeyError as exc:
            raise RunLocked(f"another run started loading {target['namespace']}") from exc
        return run_id

    def checkpoint(self, run_id: str, progress: dict) -> None:
        """Persist progress and refresh the heartbeat (journaled, so it survives a mongod crash)."""
        self.runs.update_one({"_id": run_id}, {"$set": {"progress": progress, "heartbeat_at": utcnow()}})

    def finish(self, run_id: str, status: str, progress: dict, metrics: dict, error: str | None = None) -> None:
        self.runs.update_one({"_id": run_id}, {"$set": {
            "status": status, "progress": progress, "metrics": metrics, "error": error,
            "finished_at": utcnow(), "heartbeat_at": utcnow()}})
