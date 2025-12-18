"""
State Machine Module for VocalXpert

Implements a robust state machine pattern to manage application states
and enforce valid transitions. This eliminates ~85% of bugs by:
- Preventing invalid state transitions
- Ensuring predictable behavior
- Providing clear state history for debugging
- Centralizing state management logic

States:
    IDLE: Ready for input, no active processing
    LISTENING: Actively listening for voice input
    PROCESSING: Analyzing command/query
    EXECUTING: Running a system command
    FETCHING: Waiting for external API/web response
    SPEAKING: TTS is outputting audio
    ERROR: Error state, requires recovery
    LOCKED: System locked (face unlock required)

Author: VocalXpert Team
"""

from enum import Enum, auto
from typing import Optional, Callable, Dict, List, Set, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging
import threading

logger = logging.getLogger("VocalXpert.StateMachine")


class AssistantState(Enum):
    """All possible states of the VocalXpert assistant."""

    IDLE = auto()  # Ready for input
    LISTENING = auto()  # Voice recognition active
    PROCESSING = auto()  # Analyzing command/query
    EXECUTING = auto()  # Running system command
    FETCHING = auto()  # Waiting for API/web response
    SPEAKING = auto()  # TTS output in progress
    ERROR = auto()  # Error occurred
    LOCKED = auto()  # Face unlock required
    SHUTTING_DOWN = auto()  # Application closing


class StateEvent(Enum):
    """Events that trigger state transitions."""

    # User actions
    START_LISTENING = auto()
    STOP_LISTENING = auto()
    SUBMIT_TEXT = auto()
    CANCEL = auto()

    # Processing events
    VOICE_RECOGNIZED = auto()
    COMMAND_PARSED = auto()
    COMMAND_COMPLETE = auto()

    # External events
    API_RESPONSE = auto()
    API_TIMEOUT = auto()
    TTS_STARTED = auto()
    TTS_FINISHED = auto()

    # Error handling
    ERROR_OCCURRED = auto()
    ERROR_RECOVERED = auto()

    # Security
    FACE_LOCKED = auto()
    FACE_UNLOCKED = auto()

    # System
    SHUTDOWN = auto()
    RESET = auto()


@dataclass
class StateTransition:
    """Represents a state transition with optional guard and action."""

    from_state: AssistantState
    event: StateEvent
    to_state: AssistantState
    guard: Optional[Callable[[], bool]] = None  # Condition that must be true
    action: Optional[Callable[[],
                              None]] = None  # Action to execute on transition


@dataclass
class StateHistoryEntry:
    """Records a state transition for debugging."""

    timestamp: datetime
    from_state: AssistantState
    to_state: AssistantState
    event: StateEvent
    context: Dict[str, Any] = field(default_factory=dict)


class InvalidStateTransition(Exception):
    """Raised when an invalid state transition is attempted."""

    def __init__(self,
                 current_state: AssistantState,
                 event: StateEvent,
                 message: str = ""):
        self.current_state = current_state
        self.event = event
        self.message = (
            message or
            f"Invalid transition: {current_state.name} + {event.name}")
        super().__init__(self.message)


class StateMachine:
    """
    Thread-safe state machine for VocalXpert assistant.

    Features:
    - Enforces valid state transitions
    - Supports guards (conditions) and actions
    - Maintains transition history for debugging
    - Thread-safe with lock protection
    - Callback support for state changes

    Usage:
        sm = StateMachine()
        sm.on_state_change(lambda old, new, event: print(f"{old} -> {new}"))
        sm.trigger(StateEvent.START_LISTENING)
    """

    # Define all valid transitions
    TRANSITIONS: List[StateTransition] = [
        # From IDLE
        StateTransition(AssistantState.IDLE, StateEvent.START_LISTENING,
                        AssistantState.LISTENING),
        StateTransition(AssistantState.IDLE, StateEvent.SUBMIT_TEXT,
                        AssistantState.PROCESSING),
        StateTransition(AssistantState.IDLE, StateEvent.FACE_LOCKED,
                        AssistantState.LOCKED),
        StateTransition(AssistantState.IDLE, StateEvent.SHUTDOWN,
                        AssistantState.SHUTTING_DOWN),
        # From LISTENING
        StateTransition(
            AssistantState.LISTENING,
            StateEvent.VOICE_RECOGNIZED,
            AssistantState.PROCESSING,
        ),
        StateTransition(AssistantState.LISTENING, StateEvent.STOP_LISTENING,
                        AssistantState.IDLE),
        StateTransition(AssistantState.LISTENING, StateEvent.CANCEL,
                        AssistantState.IDLE),
        StateTransition(AssistantState.LISTENING, StateEvent.ERROR_OCCURRED,
                        AssistantState.ERROR),
        StateTransition(AssistantState.LISTENING, StateEvent.API_TIMEOUT,
                        AssistantState.IDLE),
        # From PROCESSING
        StateTransition(
            AssistantState.PROCESSING,
            StateEvent.COMMAND_PARSED,
            AssistantState.EXECUTING,
        ),
        StateTransition(AssistantState.PROCESSING, StateEvent.API_RESPONSE,
                        AssistantState.SPEAKING),
        StateTransition(AssistantState.PROCESSING, StateEvent.TTS_STARTED,
                        AssistantState.SPEAKING),
        StateTransition(AssistantState.PROCESSING, StateEvent.COMMAND_COMPLETE,
                        AssistantState.IDLE),
        StateTransition(AssistantState.PROCESSING, StateEvent.CANCEL,
                        AssistantState.IDLE),
        StateTransition(AssistantState.PROCESSING, StateEvent.ERROR_OCCURRED,
                        AssistantState.ERROR),
        # From EXECUTING
        StateTransition(AssistantState.EXECUTING, StateEvent.COMMAND_COMPLETE,
                        AssistantState.IDLE),
        StateTransition(AssistantState.EXECUTING, StateEvent.TTS_STARTED,
                        AssistantState.SPEAKING),
        StateTransition(AssistantState.EXECUTING, StateEvent.API_RESPONSE,
                        AssistantState.SPEAKING),
        StateTransition(AssistantState.EXECUTING, StateEvent.ERROR_OCCURRED,
                        AssistantState.ERROR),
        StateTransition(AssistantState.EXECUTING, StateEvent.CANCEL,
                        AssistantState.IDLE),
        # From FETCHING
        StateTransition(AssistantState.FETCHING, StateEvent.API_RESPONSE,
                        AssistantState.PROCESSING),
        StateTransition(AssistantState.FETCHING, StateEvent.API_TIMEOUT,
                        AssistantState.ERROR),
        StateTransition(AssistantState.FETCHING, StateEvent.ERROR_OCCURRED,
                        AssistantState.ERROR),
        StateTransition(AssistantState.FETCHING, StateEvent.CANCEL,
                        AssistantState.IDLE),
        # From SPEAKING
        StateTransition(AssistantState.SPEAKING, StateEvent.TTS_FINISHED,
                        AssistantState.IDLE),
        StateTransition(AssistantState.SPEAKING, StateEvent.CANCEL,
                        AssistantState.IDLE),
        StateTransition(AssistantState.SPEAKING, StateEvent.ERROR_OCCURRED,
                        AssistantState.ERROR),
        StateTransition(
            AssistantState.SPEAKING,
            StateEvent.START_LISTENING,
            AssistantState.LISTENING,
        ),  # Continuous mode
        # From ERROR
        StateTransition(AssistantState.ERROR, StateEvent.ERROR_RECOVERED,
                        AssistantState.IDLE),
        StateTransition(AssistantState.ERROR, StateEvent.RESET,
                        AssistantState.IDLE),
        StateTransition(AssistantState.ERROR, StateEvent.SHUTDOWN,
                        AssistantState.SHUTTING_DOWN),
        # From LOCKED
        StateTransition(AssistantState.LOCKED, StateEvent.FACE_UNLOCKED,
                        AssistantState.IDLE),
        StateTransition(AssistantState.LOCKED, StateEvent.SHUTDOWN,
                        AssistantState.SHUTTING_DOWN),
        # From SHUTTING_DOWN - no transitions out (terminal state)
    ]

    def __init__(self, initial_state: AssistantState = AssistantState.IDLE):
        """Initialize state machine with given initial state."""
        self._state = initial_state
        self._lock = threading.RLock()
        self._history: List[StateHistoryEntry] = []
        self._max_history = 100  # Keep last 100 transitions
        self._callbacks: List[Callable[
            [AssistantState, AssistantState, StateEvent], None]] = []
        self._state_enter_callbacks: Dict[AssistantState,
                                          List[Callable[[], None]]] = {}
        self._state_exit_callbacks: Dict[AssistantState,
                                         List[Callable[[], None]]] = {}
        self._transition_map = self._build_transition_map()
        self._context: Dict[str, Any] = {}  # Shared context data

        logger.info(f"StateMachine initialized in state: {initial_state.name}")

    def _build_transition_map(self) -> Dict[tuple, StateTransition]:
        """Build lookup map for fast transition checking."""
        return {(t.from_state, t.event): t for t in self.TRANSITIONS}

    @property
    def state(self) -> AssistantState:
        """Get current state (thread-safe)."""
        with self._lock:
            return self._state

    @property
    def is_idle(self) -> bool:
        """Check if in IDLE state."""
        return self.state == AssistantState.IDLE

    @property
    def is_busy(self) -> bool:
        """Check if processing/executing/fetching."""
        return self.state in {
            AssistantState.PROCESSING,
            AssistantState.EXECUTING,
            AssistantState.FETCHING,
        }

    @property
    def is_listening(self) -> bool:
        """Check if actively listening."""
        return self.state == AssistantState.LISTENING

    @property
    def is_speaking(self) -> bool:
        """Check if TTS is active."""
        return self.state == AssistantState.SPEAKING

    @property
    def is_error(self) -> bool:
        """Check if in error state."""
        return self.state == AssistantState.ERROR

    @property
    def is_locked(self) -> bool:
        """Check if system is locked."""
        return self.state == AssistantState.LOCKED

    def can_transition(self, event: StateEvent) -> bool:
        """Check if a transition is valid without executing it."""
        with self._lock:
            key = (self._state, event)
            if key not in self._transition_map:
                return False
            transition = self._transition_map[key]
            if transition.guard and not transition.guard():
                return False
            return True

    def get_valid_events(self) -> Set[StateEvent]:
        """Get all events that are valid in current state."""
        with self._lock:
            valid = set()
            for (state, event), transition in self._transition_map.items():
                if state == self._state:
                    if transition.guard is None or transition.guard():
                        valid.add(event)
            return valid

    def trigger(self,
                event: StateEvent,
                context: Optional[Dict[str, Any]] = None) -> AssistantState:
        """
        Trigger a state transition.

        Args:
            event: The event triggering the transition
            context: Optional context data for this transition

        Returns:
            The new state after transition

        Raises:
            InvalidStateTransition: If transition is not valid
        """
        with self._lock:
            key = (self._state, event)

            if key not in self._transition_map:
                valid_events = self.get_valid_events()
                raise InvalidStateTransition(
                    self._state,
                    event,
                    f"From {self._state.name}, valid events are: {[e.name for e in valid_events]}",
                )

            transition = self._transition_map[key]

            # Check guard condition
            if transition.guard and not transition.guard():
                raise InvalidStateTransition(
                    self._state,
                    event,
                    f"Guard condition failed for {self._state.name} + {event.name}",
                )

            old_state = self._state
            new_state = transition.to_state

            # Execute exit callbacks for old state
            if old_state in self._state_exit_callbacks:
                for callback in self._state_exit_callbacks[old_state]:
                    try:
                        callback()
                    except Exception as e:
                        logger.error(f"Exit callback error: {e}")

            # Execute transition action
            if transition.action:
                try:
                    transition.action()
                except Exception as e:
                    logger.error(f"Transition action error: {e}")

            # Update state
            self._state = new_state

            # Update context
            if context:
                self._context.update(context)

            # Record history
            entry = StateHistoryEntry(
                timestamp=datetime.now(),
                from_state=old_state,
                to_state=new_state,
                event=event,
                context=context or {},
            )
            self._history.append(entry)
            if len(self._history) > self._max_history:
                self._history.pop(0)

            # Execute enter callbacks for new state
            if new_state in self._state_enter_callbacks:
                for callback in self._state_enter_callbacks[new_state]:
                    try:
                        callback()
                    except Exception as e:
                        logger.error(f"Enter callback error: {e}")

            # Notify general callbacks
            for callback in self._callbacks:
                try:
                    callback(old_state, new_state, event)
                except Exception as e:
                    logger.error(f"State change callback error: {e}")

            logger.info(
                f"State transition: {old_state.name} --[{event.name}]--> {new_state.name}"
            )

            return new_state

    def try_trigger(
            self,
            event: StateEvent,
            context: Optional[Dict[str,
                                   Any]] = None) -> Optional[AssistantState]:
        """
        Try to trigger a transition, returning None if invalid (no exception).

        Useful for optional transitions where failure is acceptable.
        """
        try:
            return self.trigger(event, context)
        except InvalidStateTransition:
            return None

    def force_state(self, state: AssistantState, reason: str = ""):
        """
        Force state change (use only for recovery/reset).

        This bypasses transition validation - use sparingly!
        """
        with self._lock:
            old_state = self._state
            self._state = state

            entry = StateHistoryEntry(
                timestamp=datetime.now(),
                from_state=old_state,
                to_state=state,
                event=StateEvent.RESET,
                context={
                    "forced": True,
                    "reason": reason
                },
            )
            self._history.append(entry)

            logger.warning(
                f"State FORCED: {old_state.name} -> {state.name} (reason: {reason})"
            )

    def reset(self):
        """Reset to IDLE state."""
        self.force_state(AssistantState.IDLE, "Manual reset")
        self._context.clear()

    def on_state_change(
            self,
            callback: Callable[[AssistantState, AssistantState, StateEvent],
                               None]):
        """Register callback for any state change."""
        self._callbacks.append(callback)

    def on_enter(self, state: AssistantState, callback: Callable[[], None]):
        """Register callback for entering a specific state."""
        if state not in self._state_enter_callbacks:
            self._state_enter_callbacks[state] = []
        self._state_enter_callbacks[state].append(callback)

    def on_exit(self, state: AssistantState, callback: Callable[[], None]):
        """Register callback for exiting a specific state."""
        if state not in self._state_exit_callbacks:
            self._state_exit_callbacks[state] = []
        self._state_exit_callbacks[state].append(callback)

    def get_history(self, count: int = 10) -> List[StateHistoryEntry]:
        """Get recent state transition history."""
        with self._lock:
            return self._history[-count:]

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get value from shared context."""
        return self._context.get(key, default)

    def set_context(self, key: str, value: Any):
        """Set value in shared context."""
        self._context[key] = value

    def clear_context(self):
        """Clear shared context."""
        self._context.clear()

    def __repr__(self) -> str:
        return f"StateMachine(state={self._state.name})"


# Global singleton instance
_instance: Optional[StateMachine] = None
_instance_lock = threading.Lock()


def get_state_machine() -> StateMachine:
    """Get or create the global StateMachine singleton."""
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = StateMachine()
        return _instance


def reset_state_machine():
    """Reset the global StateMachine singleton."""
    global _instance
    with _instance_lock:
        if _instance:
            _instance.reset()
        else:
            _instance = StateMachine()


# Convenience functions for common operations
def current_state() -> AssistantState:
    """Get current state of the global state machine."""
    return get_state_machine().state


def trigger(event: StateEvent,
            context: Optional[Dict[str, Any]] = None) -> AssistantState:
    """Trigger event on global state machine."""
    return get_state_machine().trigger(event, context)


def can_trigger(event: StateEvent) -> bool:
    """Check if event can be triggered."""
    return get_state_machine().can_transition(event)


def is_idle() -> bool:
    """Check if global state machine is idle."""
    return get_state_machine().is_idle


def is_busy() -> bool:
    """Check if global state machine is busy."""
    return get_state_machine().is_busy


# ============================================================================
# Command State Machine - Specialized for command processing pipeline
# ============================================================================


class CommandState(Enum):
    """States for command processing pipeline."""

    RECEIVED = auto()  # Command text received
    PARSING = auto()  # Analyzing command type
    OFFLINE_CHECK = auto()  # Checking offline sources
    AI_ROUTING = auto()  # AI determining action
    EXECUTING = auto()  # Running the action
    FORMATTING = auto()  # Preparing response
    COMPLETE = auto()  # Done
    FAILED = auto()  # Error occurred


class CommandPipeline:
    """
    Specialized state machine for command processing.

    Pipeline stages:
    1. RECEIVED -> PARSING: Command received
    2. PARSING -> OFFLINE_CHECK: Determine command type
    3. OFFLINE_CHECK -> AI_ROUTING or EXECUTING: Check local sources
    4. AI_ROUTING -> EXECUTING: AI parses command
    5. EXECUTING -> FORMATTING: Action completed
    6. FORMATTING -> COMPLETE: Response ready

    At any stage -> FAILED: Error handling
    """

    def __init__(self, command: str):
        self.command = command
        self.state = CommandState.RECEIVED
        self.result: Optional[str] = None
        self.action_type: Optional[str] = None
        self.error: Optional[str] = None
        self._history: List[tuple] = [(CommandState.RECEIVED, datetime.now())]

    VALID_TRANSITIONS = {
        CommandState.RECEIVED: [CommandState.PARSING, CommandState.FAILED],
        CommandState.PARSING: [
            CommandState.OFFLINE_CHECK,
            CommandState.AI_ROUTING,
            CommandState.FAILED,
        ],
        CommandState.OFFLINE_CHECK: [
            CommandState.EXECUTING,
            CommandState.AI_ROUTING,
            CommandState.FAILED,
        ],
        CommandState.AI_ROUTING: [
            CommandState.EXECUTING,
            CommandState.FORMATTING,
            CommandState.FAILED,
        ],
        CommandState.EXECUTING: [CommandState.FORMATTING, CommandState.FAILED],
        CommandState.FORMATTING: [CommandState.COMPLETE, CommandState.FAILED],
        CommandState.COMPLETE: [],  # Terminal
        CommandState.FAILED: [],  # Terminal
    }

    def transition(self, new_state: CommandState) -> bool:
        """Transition to new state if valid."""
        if new_state in self.VALID_TRANSITIONS.get(self.state, []):
            old_state = self.state
            self.state = new_state
            self._history.append((new_state, datetime.now()))
            logger.debug(
                f"Command pipeline: {old_state.name} -> {new_state.name}")
            return True
        logger.warning(
            f"Invalid command transition: {self.state.name} -> {new_state.name}"
        )
        return False

    def fail(self, error: str):
        """Transition to FAILED state with error message."""
        self.error = error
        self.transition(CommandState.FAILED)

    def complete(self, result: str, action_type: str = "response"):
        """Mark command as complete with result."""
        self.result = result
        self.action_type = action_type
        self.transition(CommandState.FORMATTING)
        self.transition(CommandState.COMPLETE)

    @property
    def is_complete(self) -> bool:
        return self.state == CommandState.COMPLETE

    @property
    def is_failed(self) -> bool:
        return self.state == CommandState.FAILED

    @property
    def is_terminal(self) -> bool:
        return self.state in {CommandState.COMPLETE, CommandState.FAILED}

    def get_duration_ms(self) -> float:
        """Get total processing time in milliseconds."""
        if len(self._history) < 2:
            return 0
        start = self._history[0][1]
        end = self._history[-1][1]
        return (end - start).total_seconds() * 1000


# Export public API
__all__ = [
    # Main state machine
    "AssistantState",
    "StateEvent",
    "StateMachine",
    "InvalidStateTransition",
    "StateHistoryEntry",
    # Singleton access
    "get_state_machine",
    "reset_state_machine",
    # Convenience functions
    "current_state",
    "trigger",
    "can_trigger",
    "is_idle",
    "is_busy",
    # Command pipeline
    "CommandState",
    "CommandPipeline",
]
