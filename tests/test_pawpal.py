import pytest

from pawpal_system import Pet, Task, Priority, TaskCategory


def test_task_completion_marks_completed():
    task = Task(
        title="Test task",
        duration_minutes=10,
        priority=Priority.MEDIUM,
        category=TaskCategory.GENERAL,
    )

    assert task.completed is False

    task.mark_completed()

    assert task.completed is True


def test_pet_add_task_increases_task_count():
    pet = Pet(name="Buddy", species="dog")
    initial_count = len(pet.tasks)

    new_task = Task(
        title="Play fetch",
        duration_minutes=15,
        priority=Priority.LOW,
        category=TaskCategory.WALK,
    )

    pet.add_task(new_task)

    assert len(pet.tasks) == initial_count + 1
    assert pet.tasks[0] == new_task
