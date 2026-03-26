from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict

class Priority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TaskCategory(Enum):
    WALK = "walk"
    FEED = "feed"
    MEDS = "meds"
    GENERAL = "general"

@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Priority
    category: TaskCategory = TaskCategory.GENERAL
    frequency: str = "once"  # daily, weekly, twice-a-day, etc.
    completed: bool = False
    notes: Optional[str] = None

    def mark_completed(self) -> None:
        """Mark the task as completed."""
        self.completed = True

    def mark_pending(self) -> None:
        """Set the task status back to pending."""
        self.completed = False

    def update_duration(self, minutes: int) -> None:
        """Update the task duration in minutes."""
        self.duration_minutes = minutes

    def update_priority(self, priority: Priority) -> None:
        """Update the task priority."""
        self.priority = priority

    def update_category(self, category: TaskCategory) -> None:
        """Update the task category."""
        self.category = category

    def to_dict(self) -> Dict[str, str]:
        """Convert task details to a dictionary."""
        return {
            "title": self.title,
            "duration_minutes": str(self.duration_minutes),
            "priority": self.priority.value,
            "category": self.category.value,
            "frequency": self.frequency,
            "completed": str(self.completed),
            "notes": self.notes or "",
        }

@dataclass
class Pet:
    name: str
    species: str
    requirements: List[str] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)

    def add_requirement(self, requirement: str) -> None:
        """Add a requirement to the pet if not already present."""
        if requirement not in self.requirements:
            self.requirements.append(requirement)

    def remove_requirement(self, requirement: str) -> None:
        """Remove a requirement from the pet."""
        if requirement in self.requirements:
            self.requirements.remove(requirement)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet if not already assigned."""
        if task not in self.tasks:
            self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet."""
        if task in self.tasks:
            self.tasks.remove(task)

    def all_tasks(self) -> List[Task]:
        """Return all tasks for the pet."""
        return list(self.tasks)

    def pending_tasks(self) -> List[Task]:
        """Return pending tasks for the pet."""
        return [task for task in self.tasks if not task.completed]

    def completed_tasks(self) -> List[Task]:
        """Return completed tasks for the pet."""
        return [task for task in self.tasks if task.completed]

@dataclass
class Owner:
    name: str
    pets: List[Pet] = field(default_factory=list)
    preferences: Dict[str, str] = field(default_factory=dict)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner."""
        if pet not in self.pets:
            self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from the owner."""
        if pet in self.pets:
            self.pets.remove(pet)

    def get_pet(self, name: str) -> Optional[Pet]:
        """Get a pet by name."""
        return next((pet for pet in self.pets if pet.name == name), None)

    def all_tasks(self) -> List[Task]:
        """Return all tasks across all pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def pending_tasks(self) -> List[Task]:
        """Return all pending tasks across pets."""
        return [task for task in self.all_tasks() if not task.completed]

    def completed_tasks(self) -> List[Task]:
        """Return all completed tasks across pets."""
        return [task for task in self.all_tasks() if task.completed]

    def set_preference(self, key: str, value: str) -> None:
        """Set an owner preference.

        """
        self.preferences[key] = value

    def update_time_budget(self, minutes: int) -> None:
        """Update owner's daily time budget preference."""
        self.preferences["daily_time_budget"] = str(minutes)

@dataclass
class ScheduledTask:
    task: Task
    start_time: datetime
    end_time: datetime
    reasoning: Optional[str] = None

@dataclass
class DailyPlan:
    scheduled_tasks: List[ScheduledTask] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)

    def total_duration(self) -> int:
        """Return total duration of scheduled tasks."""
        return sum(st.task.duration_minutes for st in self.scheduled_tasks)

    def add_scheduled_task(self, scheduled_task: ScheduledTask) -> None:
        """Append a scheduled task to the plan."""
        self.scheduled_tasks.append(scheduled_task)

    def summary(self) -> str:
        """Get a text summary of the daily plan."""
        lines = [f"Daily plan created at {self.generated_at.isoformat()}"]
        for st in self.scheduled_tasks:
            lines.append(
                f"{st.start_time.strftime('%H:%M')}-{st.end_time.strftime('%H:%M')}: {st.task.title} ({st.task.priority.value})"
            )
        return "\n".join(lines)

class Scheduler:
    def __init__(self, owner: Owner):
        """Initialize scheduler with an owner context."""
        self.owner = owner

    def retrieve_all_tasks(self) -> List[Task]:
        """Retrieve every task from the owner's pets."""
        return self.owner.all_tasks()

    def retrieve_pending_tasks(self) -> List[Task]:
        """Retrieve all pending tasks for the owner."""
        return self.owner.pending_tasks()

    def retrieve_by_priority(self, priority: Priority) -> List[Task]:
        """Retrieve tasks filtered by priority."""
        return [t for t in self.owner.all_tasks() if t.priority == priority]

    def sort_by_priority(self, tasks: Optional[List[Task]] = None) -> List[Task]:
        """Return tasks sorted from high to low priority."""
        tasks = tasks if tasks is not None else self.retrieve_pending_tasks()
        priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
        return sorted(tasks, key=lambda t: priority_order.get(t.priority, 3))

    def fit_within_constraints(self, max_minutes: Optional[int] = None) -> List[Task]:
        """Pick tasks that fit within a daily time budget."""
        max_minutes = int(self.owner.preferences.get("daily_time_budget", "0")) if max_minutes is None else max_minutes
        selected = []
        remaining = max_minutes

        for task in self.sort_by_priority():
            if task.duration_minutes <= remaining:
                selected.append(task)
                remaining -= task.duration_minutes

        return selected

    def generate_daily_plan(self, start_time: Optional[datetime] = None, max_minutes: Optional[int] = None) -> DailyPlan:
        """Build a DailyPlan from selected tasks and start time."""
        if start_time is None:
            start_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)

        selected_tasks = self.fit_within_constraints(max_minutes=max_minutes)
        plan = DailyPlan()
        current = start_time

        for task in selected_tasks:
            end = current + timedelta(minutes=task.duration_minutes)
            reason = f"Picked {task.title}; priority={task.priority.value}; duration={task.duration_minutes}"
            plan.add_scheduled_task(ScheduledTask(task=task, start_time=current, end_time=end, reasoning=reason))
            current = end

        return plan

    def complete_task(self, task: Task) -> None:
        """Mark a task as completed."""
        task.mark_completed()

    def provide_reasoning(self, plan: DailyPlan) -> str:
        """Provide a narrative reasoning for a given DailyPlan."""
        lines = ["Scheduler reasoning:"]
        lines.append(f"total planned minutes: {plan.total_duration()}")
        lines.append(plan.summary())
        return "\n".join(lines)


