"""PawPal+ system implementation.

The four classes from the project UML (diagrams/uml.mmd):

    Owner ──owns──> Pet ──has──> Task
    Owner ──uses──> Calendar ──schedules──> Task

Owner, Pet, and Task are plain data holders. Calendar contains all of the
scheduling logic: it selects tasks by priority within the owner's
available-minutes budget, lays them out in time-of-day order, flags conflicts,
and records reasoning so the plan can be explained.
"""

from datetime import date, timedelta

# Lower number == higher priority. Unknown labels fall back to "medium".
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

# Lower number == earlier in the day. Tasks with no preferred time sort last.
TIME_ORDER = {"morning": 0, "afternoon": 1, "evening": 2, "night": 3}
UNTIMED_RANK = len(TIME_ORDER)  # untimed tasks fall after every known window

# Recurrence values a Task may carry. None means a one-off task.
VALID_RECURRENCES = ("daily", "weekly")


def _format_minutes(total):
    """Render a minutes-since-midnight value as H:MM (e.g. 75 -> '1:15')."""
    hours, minutes = divmod(int(total), 60)
    return f"{hours}:{minutes:02d}"


class Owner:
    """The person planning care. Owns pets and provides a time budget."""

    def __init__(self, name, available_minutes, preferred_times=None,
                 day_start_minutes=480):
        """Create an owner with a name, daily minute budget, and time preferences.

        ``day_start_minutes`` anchors the plan to a real clock time
        (default 480 == 8:00) so slots read as "8:30" rather than "0:30".
        """
        self.name = name
        self.available_minutes = int(available_minutes)
        self.preferred_times = list(preferred_times) if preferred_times else []
        self.day_start_minutes = int(day_start_minutes)
        self.pets = []  # populated via add_pet()

    def add_pet(self, pet):
        """Register a pet under this owner (ignores duplicates)."""
        if pet not in self.pets:
            self.pets.append(pet)

    def all_tasks(self, pet=None, status=None, due_on_or_before=None):
        """Flatten owned pets' tasks into a single list.

        Optionally filter to one ``pet``, a single ``status``
        (e.g. "pending" or "complete"), and/or tasks whose ``due_date`` is
        on or before ``due_on_or_before`` (a ``date``). The date filter keeps
        future recurring occurrences out of an earlier day's view.
        """
        tasks = []
        for owned in self.pets:
            if pet is not None and owned is not pet:
                continue
            tasks.extend(owned.activities)
        if status is not None:
            tasks = [task for task in tasks if task.status == status]
        if due_on_or_before is not None:
            tasks = [task for task in tasks if task.due_date <= due_on_or_before]
        return tasks

    def tasks_for_pet(self, pet):
        """Return only the tasks belonging to ``pet``."""
        return self.all_tasks(pet=pet)

    def __repr__(self):
        """Return a short debug representation of the owner."""
        return f"Owner({self.name!r}, {self.available_minutes} min, {len(self.pets)} pet(s))"


class Pet:
    """An animal owned by an Owner. Holds the tasks it needs done."""

    def __init__(self, name, species):
        """Create a pet with a name and species and an empty task list."""
        self.name = name
        self.species = species
        self.activities = []  # list[Task]

    def add_activity(self, activity):
        """Attach a Task to this pet and back-reference the pet on the task."""
        activity.pet = self
        self.activities.append(activity)

    def __repr__(self):
        """Return a short debug representation of the pet."""
        return f"Pet({self.name!r}, {self.species!r}, {len(self.activities)} task(s))"


class Task:
    """A single pet-care task to be scheduled."""

    VALID_PRIORITIES = ("high", "medium", "low")

    def __init__(self, title, duration_minutes, priority="medium",
                 preferred_time="", category="general", recurrence=None):
        """Create a task, validating duration and normalizing labels."""
        if int(duration_minutes) <= 0:
            raise ValueError("duration_minutes must be a positive number of minutes")

        priority = str(priority).lower()
        if priority not in self.VALID_PRIORITIES:
            priority = "medium"

        if recurrence is not None:
            recurrence = str(recurrence).lower()
            if recurrence not in VALID_RECURRENCES:
                recurrence = None

        self.title = title
        self.duration_minutes = int(duration_minutes)
        self.priority = priority
        self.preferred_time = preferred_time
        self.category = category
        self.recurrence = recurrence
        self.status = "pending"      # "pending" until marked done
        self.pet = None              # set by Pet.add_activity()
        self.due_date = date.today() # defaults to today; updated on recurrence

    def mark_complete(self, pet=None):
        """Mark this task done and auto-create the next occurrence if recurring.

        If the task recurs daily, the next instance is due tomorrow.
        If it recurs weekly, the next instance is due in seven days.
        Pass the owning ``pet`` to register the new task automatically.

        Returns the new Task if recurring, otherwise None.
        """
        self.status = "complete"

        if self.recurrence == "daily":
            next_due = date.today() + timedelta(days=1)
        elif self.recurrence == "weekly":
            next_due = date.today() + timedelta(weeks=1)
        else:
            return None  # one-off task, nothing more to do

        next_task = Task(
            title=            self.title,
            duration_minutes= self.duration_minutes,
            priority=         self.priority,
            preferred_time=   self.preferred_time,
            category=         self.category,
            recurrence=       self.recurrence,
        )
        next_task.due_date = next_due

        if pet is not None:
            pet.add_activity(next_task)

        return next_task

    def is_complete(self):
        """Return True once the task has been completed."""
        return self.status == "complete"

    def time_rank(self):
        """Return this task's time-of-day sort rank (untimed sorts last)."""
        return TIME_ORDER.get(self.preferred_time, UNTIMED_RANK)

    def __repr__(self):
        """Return a short debug representation of the task."""
        return (
            f"Task({self.title!r}, {self.duration_minutes}min, "
            f"{self.priority!r}, {self.status}, due={self.due_date})"
        )


class Calendar:
    """Builds and explains a daily plan from a set of tasks.

    After build_plan() runs:
      - ``slots`` holds (start_min, end_min, task) tuples for scheduled work,
        ordered chronologically and anchored to the owner's day start
      - ``conflicts`` holds one note per detected scheduling clash
      - ``reasoning`` holds one human-readable line per decision made
    """

    def __init__(self):
        """Create an empty calendar with no slots, conflicts, or reasoning yet."""
        self.slots = []      # list[tuple(start_min, end_min, Task)]
        self.conflicts = []  # list[str]
        self.reasoning = []  # list[str]

    def sort_by_priority(self, activities):
        """Return tasks ordered by priority, then shorter-first as a tiebreak.

        Used to decide which tasks win scarce budget when not everything fits.
        """
        return sorted(
            activities,
            key=lambda task: (PRIORITY_ORDER.get(task.priority, 1), task.duration_minutes),
        )

    def sort_by_time(self, activities):
        """Return tasks ordered by time of day, then priority, then duration.

        Tasks with no preferred_time are placed at the end of the day.
        Within the same time window, higher-priority tasks come first.
        """
        return sorted(
            activities,
            key=lambda task: (
                task.time_rank(),
                PRIORITY_ORDER.get(task.priority, 1),
                task.duration_minutes,
            ),
        )

    def fits_in_budget(self, activity, remaining):
        """Return True when the task fits in the remaining minutes."""
        return activity.duration_minutes <= remaining

    def _detect_conflicts(self, tasks, owner):
        """Record notes for tasks that compete for the same time window.

        Runs over every task planned for the day (not just the ones that
        survived the budget) so a clash is reported even when one of the
        clashing tasks gets cut for time.

        Flags two kinds of clashes:
        - Same category tasks in the same time window (e.g. two feedings
          both marked 'morning').
        - More than two tasks stacked into an owner-preferred window.

        Note: ``preferred_time`` is a coarse window, not a clock time, and
        the planner lays tasks out back-to-back, so true minute-level
        overlaps cannot occur — window contention is the meaningful signal.
        """
        notes = []
        by_window = {}
        for task in tasks:
            if not task.preferred_time:
                continue
            by_window.setdefault(task.preferred_time, []).append(task)

        for window, tasks in by_window.items():
            by_category = {}
            for task in tasks:
                by_category.setdefault(task.category, []).append(task)
            for category, group in by_category.items():
                if len(group) > 1:
                    titles = ", ".join(f"'{t.title}'" for t in group)
                    notes.append(
                        f"{len(group)} {category} tasks ({titles}) all set for "
                        f"{window} — they may collide."
                    )

            if window in owner.preferred_times and len(tasks) > 2:
                notes.append(
                    f"{len(tasks)} tasks are stacked into your preferred "
                    f"{window} window."
                )

        return notes

    def build_plan(self, owner, activities, for_date=None):
        """Plan tasks within the owner's budget, then lay them out by time.

        Only tasks that are pending and due on or before ``for_date``
        (default: today) are considered, so future recurring occurrences
        don't leak into an earlier day's plan. Selection is priority-first so
        the most important tasks win scarce minutes; the resulting day is then
        ordered chronologically. Over-budget days are flagged up front, and
        tasks that do not fit are recorded in ``reasoning`` rather than dropped
        silently. Same-window clashes are recorded in ``conflicts``.
        """
        self.slots = []
        self.conflicts = []
        self.reasoning = []

        if for_date is None:
            for_date = date.today()

        budget = owner.available_minutes
        remaining = budget

        # Only pending tasks compete for time; done tasks shouldn't be replanned.
        pending = [task for task in activities if not task.is_complete()]
        skipped_done = len(activities) - len(pending)

        # Tasks due later (e.g. tomorrow's recurring occurrence) wait their turn.
        active = [task for task in pending if task.due_date <= for_date]
        deferred = len(pending) - len(active)

        self.reasoning.append(
            f"Planning {len(active)} task(s) due by {for_date} for {owner.name} "
            f"within a {budget}-minute budget, highest priority first."
        )
        if skipped_done:
            self.reasoning.append(
                f"Ignored {skipped_done} already-completed task(s)."
            )
        if deferred:
            self.reasoning.append(
                f"Deferred {deferred} task(s) not due until after {for_date}."
            )

        if not active:
            self.reasoning.append("No tasks are due, so the plan is empty.")
            return

        # Up-front budget check so owners learn early the day is overcommitted.
        total_needed = sum(task.duration_minutes for task in active)
        if total_needed > budget:
            self.reasoning.append(
                f"Heads up: {len(active)} tasks need {total_needed} min but only "
                f"{budget} min are available — lower-priority tasks may be cut."
            )

        # Select which tasks fit, highest priority first.
        selected = []
        for task in self.sort_by_priority(active):
            if self.fits_in_budget(task, remaining):
                selected.append(task)
                remaining -= task.duration_minutes
            else:
                self.reasoning.append(
                    f"Skipped '{task.title}' ({task.duration_minutes} min): "
                    f"only {remaining} min left in the budget."
                )

        # Lay the selected tasks out in time-of-day order, anchored to the
        # owner's day start so slots read as real clock times.
        cursor = owner.day_start_minutes
        for task in self.sort_by_time(selected):
            start, end = cursor, cursor + task.duration_minutes
            self.slots.append((start, end, task))
            cursor = end

            who = f" for {task.pet.name}" if task.pet else ""
            line = (
                f"{_format_minutes(start)}-{_format_minutes(end)}: "
                f"{task.title}{who} ({task.priority} priority, "
                f"{task.duration_minutes} min)"
            )
            if task.preferred_time:
                line += f" — owner prefers {task.preferred_time}"
            if task.recurrence:
                line += f" | repeats {task.recurrence}"
            self.reasoning.append(line)

        # Flag same-window clashes across every task due today — including any
        # cut for budget, so a real conflict isn't hidden by trimming.
        self.conflicts = self._detect_conflicts(active, owner)
        for note in self.conflicts:
            self.reasoning.append(f"Conflict: {note}")

        self.reasoning.append(
            f"Scheduled {len(self.slots)} of {len(active)} task(s); "
            f"{remaining} of {budget} minutes left unused."
        )

    def explain(self):
        """Return the recorded reasoning as a single readable string."""
        if not self.reasoning:
            return "No plan has been built yet."
        return "\n".join(self.reasoning)