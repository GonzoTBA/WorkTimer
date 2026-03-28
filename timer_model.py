from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
import time


class TimerState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"


@dataclass
class TimerSnapshot:
    state: TimerState
    remaining_seconds: int
    initial_seconds: int


class TimerModel:
    def __init__(self, initial_seconds: int = 15 * 60) -> None:
        self._initial_seconds = max(1, int(initial_seconds))
        self._state = TimerState.IDLE
        self._target_end_monotonic: float | None = None
        self._paused_remaining_seconds = self._initial_seconds

    @property
    def state(self) -> TimerState:
        return self._state

    @property
    def initial_seconds(self) -> int:
        return self._initial_seconds

    def set_initial_duration(self, seconds: int) -> None:
        self._initial_seconds = max(1, int(seconds))
        if self._state in {TimerState.IDLE, TimerState.FINISHED}:
            self._paused_remaining_seconds = self._initial_seconds
            self._state = TimerState.IDLE

    def start(self, seconds: int | None = None) -> None:
        if seconds is not None:
            self._initial_seconds = max(1, int(seconds))

        self._paused_remaining_seconds = self._initial_seconds
        self._target_end_monotonic = time.monotonic() + self._paused_remaining_seconds
        self._state = TimerState.RUNNING

    def pause(self) -> None:
        if self._state != TimerState.RUNNING:
            return

        self._paused_remaining_seconds = self.remaining_seconds()
        self._target_end_monotonic = None
        self._state = TimerState.PAUSED

    def resume(self) -> None:
        if self._state != TimerState.PAUSED:
            return

        self._target_end_monotonic = time.monotonic() + self._paused_remaining_seconds
        self._state = TimerState.RUNNING

    def reset(self) -> None:
        self._target_end_monotonic = None
        self._paused_remaining_seconds = self._initial_seconds
        self._state = TimerState.IDLE

    def tick(self) -> bool:
        if self._state != TimerState.RUNNING or self._target_end_monotonic is None:
            return False

        if self.remaining_seconds() > 0:
            return False

        self._target_end_monotonic = None
        self._paused_remaining_seconds = 0
        self._state = TimerState.FINISHED
        return True

    def remaining_seconds(self) -> int:
        if self._state == TimerState.RUNNING and self._target_end_monotonic is not None:
            seconds_left = self._target_end_monotonic - time.monotonic()
            return max(0, math.ceil(seconds_left))

        if self._state == TimerState.FINISHED:
            return 0

        return max(0, int(self._paused_remaining_seconds))

    def snapshot(self) -> TimerSnapshot:
        return TimerSnapshot(
            state=self._state,
            remaining_seconds=self.remaining_seconds(),
            initial_seconds=self._initial_seconds,
        )
