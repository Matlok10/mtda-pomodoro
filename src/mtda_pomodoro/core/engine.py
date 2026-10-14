# modulo encargado de manejar los timers del pomodoro

import time
import os
import asyncio
from core.state import PomodoroPhase, TimeStatus, EngineState, PomodoroBConfig
from typing import Callable, List, Optional
import core.config

TickCallback = Callable[[int, PomodoroPhase], None]
PhaseChangeCallback = Callable[[PomodoroPhase, PomodoroPhase], None]
SessionCompleteCallback = Callable[[PomodoroPhase, int], None]


# principal base config
class PomodoroEngine:
    def __init__(self, config: Optional[PomodoroBConfig] = None):

        # inyect config
        self.config = config or PomodoroBConfig()

        self.current_phase = PomodoroPhase.WORK
        self.status = TimeStatus.IDLE
        self.current_repetition = 1

        # init count of remaining seconds
        self.remaining_seconds = self._get_duracion_for[self.current_phase]

        # manage of concurrent and time stamp
        self._time_timestap: float = 0.0
        self._loop_task: Optional[asyncio.tasks] = None

        # list of suscriptions (pluguins)
        self._tick_listeners: list[TickCallback] = []
        self._phase_listeners: list[PhaseChangeCallback] = []
        self._complete_listeners: list[SessionCompleteCallback] = []

    # public interfase
    # observers
    def subscribe_tick(self, listeners: TickCallback):
        # registry listeners
        self._tick_listeners.append(listeners)

    def subscribe_phase_change(self, listeners: PhaseChangeCallback):
        self._phase_listeners.append(listeners)

    def subscribe_complete_rep(self, listeners: SessionCompleteCallback):
        self._complete_listeners.append(listeners)

    # calculate time
    def start_count(self) -> None:
        # start count or resume
        if self.status == TimeStatus.RUNNING:
            return

        self._target_timestap = time.monotonic() + self.remaining_seconds
        self.status = TimeStatus.RUNNING
        self._loop_task = asyncio.create_task(self._run_loop())

    def reset_count(self) -> None:
        # restart count
        if self._loop_task:
            self._loop_task.cancel()

        self.status = TimeStatus.IDLE
        self.remaining_seconds = self._get_duracion_for(self.current_phase)
        self._notify_tick()

    def update_count(self, new_config: PomodoroBConfig) -> None:
        # when count is stop, can change count time
        self.config = new_config

        if self.status == TimeStatus.IDLE:
            self.remaining_seconds = self._get_duracion_for(self.current_phase)
            self._notify_tick()

    # private logic
    # link phase with minunes
    def _get_duracion_for(self, phase: PomodoroPhase) -> int:
        mapping = {
            PomodoroPhase.WORK: self.config.work_minutes,
            PomodoroPhase.SHORT_BREAK: self.config.short_break,
            PomodoroPhase.LONG_BREAK: self.config.long_break,
        }
        return mapping[phase]

    # notications for suscriptions
    # time
    def _notify_tick(self) -> None:
        for listeners in self._tick_listeners:
            listeners(self.remaining_seconds, self.current_phase)

    # phase change
    def _notify_phase_change(
        self, old_phase: PomodoroPhase, new_phase: PomodoroPhase
    ) -> None:
        for listeners in self._phase_listeners:
            listeners(old_phase, new_phase)

    # complete rep
    def _notify_complete_rep(self, phase: PomodoroPhase) -> None:
        for listeners in self._complete_listeners:
            listeners(phase, self.current_repetition)

    # execute cronologic change
    def _manager_time_completiton(self) -> None:
        complete_phase = self.current_phase
        self._notify_complete_rep(complete_phase)
        self._advance_phase()

    # change phase
    def _advance_phase(self) -> None:
        old_phase = self.current_phase
        # logic of phases
        if old_phase == PomodoroPhase.WORK:
            if self.current_repetition % self.config.repetitions_work == 0:
                self.current_phase = PomodoroPhase.LONG_BREAK
            else:
                self.current_phase = PomodoroPhase.SHORT_BREAK
        else:
            if old_phase == PomodoroPhase.LONG_BREAK:
                self.current_repetition = 1
            else:
                self.current_repetition += 1

            self.current_phase = PomodoroPhase.WORK
        # logic time of new_phase
        self.remaining_seconds = self._get_duracion_for(self.current_phase)
        self.status = TimeStatus

        # notications
        self._notify_phase_change(old_phase, self.current_phase)
        self._notify_tick()
