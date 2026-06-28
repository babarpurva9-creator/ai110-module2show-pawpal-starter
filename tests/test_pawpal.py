"""Simple behavior tests for PawPal+ (pawpal_system.py)."""

import os
import sys

# Make the project root importable when running pytest from anywhere.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import Calendar, Owner, Pet, Task


def test_mark_complete_updates_status():
    """mark_complete() should flip the task's status from pending to complete."""
    task = Task("Morning walk", 20, "high")

    assert task.status == "pending"   # tasks start out not done
    assert task.is_complete() is False

    task.mark_complete()

    assert task.status == "complete"  # status updated after marking done
    assert task.is_complete() is True


def test_adding_task_increases_pet_task_count():
    """add_activity() should increase the number of tasks on the pet."""
    pet = Pet("Mochi", "dog")
    assert len(pet.activities) == 0   # no tasks to start

    pet.add_activity(Task("Feed", 10, "high"))
    assert len(pet.activities) == 1   # one task after first add

    pet.add_activity(Task("Walk", 20, "medium"))
    assert len(pet.activities) == 2   # count grows with each task


def test_add_activity_sets_pet_back_reference():
    """add_activity() should record which pet a task belongs to."""
    pet = Pet("Mochi", "dog")
    task = Task("Feed", 10, "high")
    pet.add_activity(task)
    assert task.pet is pet


def test_all_tasks_filters_by_pet_and_status():
    """all_tasks() should filter by pet and by status."""
    owner = Owner("Sam", available_minutes=120)
    dog = Pet("Bruno", "dog")
    cat = Pet("Whiskers", "cat")
    owner.add_pet(dog)
    owner.add_pet(cat)

    dog_feed = Task("Feed Bruno", 10, "high")
    cat_feed = Task("Feed Whiskers", 10, "medium")
    dog.add_activity(dog_feed)
    cat.add_activity(cat_feed)
    dog_feed.mark_complete()

    assert owner.tasks_for_pet(dog) == [dog_feed]
    assert owner.all_tasks(status="pending") == [cat_feed]


def test_plan_skips_completed_tasks():
    """Completed tasks should not consume budget or appear in slots."""
    owner = Owner("Sam", available_minutes=120)
    pet = Pet("Bruno", "dog")
    owner.add_pet(pet)
    done = Task("Done walk", 30, "high")
    todo = Task("Feed", 10, "high")
    pet.add_activity(done)
    pet.add_activity(todo)
    done.mark_complete()

    calendar = Calendar()
    calendar.build_plan(owner, owner.all_tasks())

    scheduled = [task for _, _, task in calendar.slots]
    assert scheduled == [todo]


def test_plan_orders_slots_by_time_of_day():
    """Slots should come out in time-of-day order, not insertion order."""
    owner = Owner("Sam", available_minutes=120, day_start_minutes=480)
    pet = Pet("Bruno", "dog")
    owner.add_pet(pet)
    pet.add_activity(Task("Evening play", 20, "high", preferred_time="evening"))
    pet.add_activity(Task("Morning walk", 30, "high", preferred_time="morning"))

    calendar = Calendar()
    calendar.build_plan(owner, owner.all_tasks())

    titles = [task.title for _, _, task in calendar.slots]
    assert titles == ["Morning walk", "Evening play"]
    # First slot is anchored to the owner's 8:00 day start.
    assert calendar.slots[0][0] == 480


def test_plan_detects_same_window_category_conflict():
    """Two same-category tasks in one window should be flagged as a conflict."""
    owner = Owner("Sam", available_minutes=120)
    pet = Pet("Bruno", "dog")
    owner.add_pet(pet)
    pet.add_activity(Task("Feed kibble", 10, "high", preferred_time="morning", category="feeding"))
    pet.add_activity(Task("Feed treats", 10, "high", preferred_time="morning", category="feeding"))

    calendar = Calendar()
    calendar.build_plan(owner, owner.all_tasks())

    assert any("feeding" in note for note in calendar.conflicts)


def test_future_recurring_occurrence_not_planned_today():
    """A next occurrence due tomorrow must stay out of today's plan."""
    owner = Owner("Sam", available_minutes=120)
    pet = Pet("Bruno", "dog")
    owner.add_pet(pet)
    feed = Task("Feed", 10, "high", recurrence="daily")
    pet.add_activity(feed)

    next_feed = feed.mark_complete(pet=pet)  # creates tomorrow's occurrence
    assert next_feed in pet.activities

    calendar = Calendar()
    calendar.build_plan(owner, owner.all_tasks())  # for_date defaults to today

    # Original is complete, next one is due tomorrow -> nothing scheduled today.
    assert calendar.slots == []
    assert any("Deferred" in line for line in calendar.reasoning)


def test_conflict_detected_even_when_task_cut_for_budget():
    """A same-window clash should surface even if one clashing task is cut."""
    owner = Owner("Sam", available_minutes=45)  # only the first vet task fits
    pet = Pet("Whiskers", "cat")
    owner.add_pet(pet)
    pet.add_activity(Task("Vet", 45, "high", preferred_time="afternoon", category="medical"))
    pet.add_activity(Task("Grooming", 30, "medium", preferred_time="afternoon", category="medical"))

    calendar = Calendar()
    calendar.build_plan(owner, owner.all_tasks())

    assert len(calendar.slots) == 1                       # Grooming cut for budget
    assert any("medical" in note for note in calendar.conflicts)  # clash still flagged


def test_invalid_recurrence_falls_back_to_none():
    """An unrecognized recurrence label should normalize to None."""
    assert Task("Walk", 20, recurrence="hourly").recurrence is None
    assert Task("Walk", 20, recurrence="daily").recurrence == "daily"
