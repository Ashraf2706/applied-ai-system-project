from datetime import datetime

from pawpal_system import Owner, Pet, Task, Scheduler, Priority, TaskCategory


def main():
    owner = Owner(name="Jordan")
    owner.update_time_budget(120)  # for scheduler budget reference

    # Create two pets
    mochi = Pet(name="Mochi", species="dog")
    whiskers = Pet(name="Whiskers", species="cat")
    owner.add_pet(mochi)
    owner.add_pet(whiskers)

    # Add tasks for pets
    t1 = Task(
        title="Morning walk",
        duration_minutes=30,
        priority=Priority.HIGH,
        category=TaskCategory.WALK,
        frequency="daily",
    )
    t2 = Task(
        title="Feed kibble",
        duration_minutes=10,
        priority=Priority.MEDIUM,
        category=TaskCategory.FEED,
        frequency="twice-a-day",
    )
    t3 = Task(
        title="Administer meds",
        duration_minutes=15,
        priority=Priority.HIGH,
        category=TaskCategory.MEDS,
        frequency="daily",
    )

    mochi.add_task(t1)
    whiskers.add_task(t2)
    mochi.add_task(t3)

    # Run scheduler
    scheduler = Scheduler(owner)
    plan = scheduler.generate_daily_plan(start_time=datetime.now().replace(hour=8, minute=0, second=0, microsecond=0))

    print("Today's Schedule")
    print("================")
    print(scheduler.provide_reasoning(plan))


if __name__ == "__main__":
    main()
