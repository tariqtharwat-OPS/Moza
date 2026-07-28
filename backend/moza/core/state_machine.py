from moza.core.models import TaskStatus


_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.IDLE: {TaskStatus.PLANNING},
    TaskStatus.PLANNING: {TaskStatus.EXECUTING, TaskStatus.COMPLETED, TaskStatus.FAILED},
    TaskStatus.EXECUTING: {TaskStatus.WAITING_APPROVAL, TaskStatus.WAITING_TOOL, TaskStatus.WAITING_USER, TaskStatus.REFLECTING, TaskStatus.COMPLETED, TaskStatus.FAILED},
    TaskStatus.WAITING_APPROVAL: {TaskStatus.EXECUTING, TaskStatus.CANCELLED},
    TaskStatus.WAITING_TOOL: {TaskStatus.EXECUTING, TaskStatus.FAILED},
    TaskStatus.WAITING_USER: {TaskStatus.EXECUTING, TaskStatus.CANCELLED},
    TaskStatus.REFLECTING: {TaskStatus.EXECUTING, TaskStatus.RECOVERING, TaskStatus.COMPLETED},
    TaskStatus.RECOVERING: {TaskStatus.PLANNING, TaskStatus.FAILED},
    TaskStatus.PENDING: {TaskStatus.RUNNING, TaskStatus.FAILED},
    TaskStatus.RUNNING: {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.COMPLETED: set(),
    TaskStatus.FAILED: set(),
    TaskStatus.CANCELLED: set(),
}


def is_valid_transition(current: TaskStatus, next_state: TaskStatus) -> bool:
    allowed = _TRANSITIONS.get(current)
    if allowed is None:
        return False
    return next_state in allowed


def transition(current: TaskStatus, next_state: TaskStatus) -> TaskStatus:
    if not is_valid_transition(current, next_state):
        raise ValueError(
            f"Invalid state transition: {current.value} -> {next_state.value}"
        )
    return next_state
