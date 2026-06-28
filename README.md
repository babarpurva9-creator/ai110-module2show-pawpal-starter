# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
SAMPLE OUTPUT
=============================================
Planning 5 task(s) for Purva within a 120-minute budget, highest priority first.
0:00-0:10: Feed Bruno (high priority, 10 min) — owner prefers morning
0:10-0:40: Morning walk (high priority, 30 min) — owner prefers morning
0:40-1:25: Vet appointment (high priority, 45 min) — owner prefers afternoon
1:25-1:35: Feed Whiskers (medium priority, 10 min) — owner prefers evening
1:35-1:55: Playtime (low priority, 20 min) — owner prefers evening
Scheduled 5 of 5 task(s); 5 of 120 minutes left unused.
=============================================
```
## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```
# What is covered in each test:
1. test_mark_complete_updates_status:
A newly created task starts as "pending". After calling mark_complete(), it should flip to "complete" and is_complete() should return True.

2. test_adding_task_increases_pet_task_count:
A pet starts with zero activities. Each call to add_activity() should grow the list by one — it's checking that tasks are actually being stored.

3. test_add_activity_sets_pet_back_reference:
When a task is added to a pet, the task itself should know which pet it belongs to (via a task.pet back-reference). This ensures the link goes both ways.

4. test_all_tasks_filters_by_pet_and_status:
Checks two filtering methods on an owner with multiple pets. tasks_for_pet(dog) should return only that dog's tasks. all_tasks(status="pending") should exclude anything already completed.

test_plan_skips_completed_tasks:
5. When building a calendar plan, completed tasks shouldn't be scheduled or consume any time budget — only pending tasks should appear in the slots.

6. test_plan_orders_slots_by_time_of_day:
Even if tasks are added in random order (evening before morning), the calendar should sort them chronologically. It also checks that the first slot's start time matches the owner's day_start_minutes.

7. test_plan_detects_same_window_category_conflict:
Two tasks in the same time window and same category (e.g., both "feeding" in the morning) should be flagged as a conflict in calendar.conflicts.

8.test_future_recurring_occurrence_not_planned_today:
Completing a daily task creates tomorrow's occurrence. Since that new task is due tomorrow, today's calendar plan should be empty — and the reasoning log should mention it was deferred.

9. test_conflict_detected_even_when_task_cut_for_budget:
If two tasks clash but only one fits in the time budget, the second gets cut — but the conflict should still be flagged anyway. Cutting a task doesn't silently hide the scheduling problem.

10.test_invalid_recurrence_falls_back_to_none:
Unrecognized recurrence strings (like "hourly") should normalize to None rather than causing errors. Known values like "daily" should pass through unchanged.

11.test_sort_by_time_returns_chronological_order:
Feeds sort_by_time() a deliberately scrambled list — night, untimed, morning, afternoon, evening — and expects them back in strict chronological order: morning → afternoon → evening → night, with untimed tasks always last.

12.test_marking_daily_task_complete_creates_next_day_occurrence:
The core recurrence contract: completing a daily task should produce a new, distinct task that is pending, due exactly one day from today, and has the same title/duration/recurrence as the original. It should also be auto-registered on the pet.

13.test_scheduler_flags_tasks_sharing_a_time_window:
Two tasks in the same time window should always produce a non-empty calendar.conflicts list, and the conflict note should name the window (e.g., "morning"). This is the basic conflict-detection smoke test.

Sample test output:

```
# Paste your pytest output here
================================================== test session starts ==================================================
platform win32 -- Python 3.13.5, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Purva\OneDrive\Desktop\Codepath\ai110-module2show-pawpal-starter
plugins: anyio-4.14.1
collected 13 items                                                                                                       

tests\test_pawpal.py .............                                                                                 [100%]

================================================== 13 passed in 0.59s ===================================================

Confidence Level: 5
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
