import time
import uuid
from configs.logging_setup import log


class EventTracer:
    __slots__ = ("user_id", "trace_id", "start_time")

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.trace_id = uuid.uuid4().hex[:8]
        self.start_time = time.perf_counter()

    def _log(self, name: str, data: dict | None = None):
        elapsed = time.perf_counter() - self.start_time

        log.info(
            "[TRACE:%s][uid:%s][+%.4fs] %s %s",
            self.trace_id,
            self.user_id,
            elapsed,
            name,
            data or {},
        )

    def event(self, name: str, data: dict | None = None):
        self._log(name, data)

    def entry(self, text: str):
        self._log("ENTRY", {"text": text})

    def handler(self, name: str):
        self._log("HANDLER", {"name": name})

    def step(self, name: str):
        self._log("STEP", {"name": name})

    def state(self, state: str):
        self._log("STATE", {"state": state})

    def result(self, result: str):
        self._log("RESULT", {"result": result})

    def error(self, err: str):
        self._log("ERROR", {"error": err})