# State of pomodoro timer
from enum import Enum
from dataclasses import dataclass


class PomodoroPhase(Enum):
    WORK = "work"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"
    STOP_WORK = "stop_work"


class TimeStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"


@dataclass
class EngineState:
    phase: PomodoroPhase
    status: TimeStatus
    remaining_seconds: int
    current_cycle: int


@dataclass
class PomodoroBConfig:
    # config base of pomodoro
    work_minutes: int = 25 * 60
    short_break: int = 5 * 60
    long_break: int = 15 * 60
    repetitions_work: int = 4
