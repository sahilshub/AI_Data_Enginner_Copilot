import threading


class Metrics:
    """
    In-memory, process-local metrics store.

    Deliberately not persisted or exported anywhere yet — this step is about
    having *some* visibility into request volume/latency/error rate while the
    app is running, not about building a metrics pipeline. Prometheus/Grafana
    (mentioned in AGENTS.md's preferred stack) are a later, separate concern:
    swapping this out for a real metrics client shouldn't require touching
    call sites, only this module.

    Thread-safe: FastAPI's sync endpoints run in a thread pool, so counters
    are guarded by a lock rather than assumed single-threaded.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._total_requests = 0
        self._failed_requests = 0
        self._total_duration_ms = 0.0
        self._metadata_refreshes = 0
        self._metadata_refresh_failures = 0

    def record_request(self, status_code: int, duration_ms: float) -> None:
        with self._lock:
            self._total_requests += 1
            self._total_duration_ms += duration_ms
            if status_code >= 400:
                self._failed_requests += 1

    def record_metadata_refresh(self, success: bool) -> None:
        with self._lock:
            self._metadata_refreshes += 1
            if not success:
                self._metadata_refresh_failures += 1

    def snapshot(self) -> dict:
        with self._lock:
            total = self._total_requests
            avg_duration_ms = (self._total_duration_ms / total) if total else 0.0
            return {
                "total_requests": total,
                "failed_requests": self._failed_requests,
                "average_request_duration_ms": round(avg_duration_ms, 2),
                "metadata_refreshes": self._metadata_refreshes,
                "metadata_refresh_failures": self._metadata_refresh_failures,
            }


# Single process-wide instance — every request/refresh call records into this one.
metrics = Metrics()
