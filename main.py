from pawpal_system import Owner, Pet, Task, Calendar

# ── Setup ────────────────────────────────────────────────────────────────────
owner = Owner(name="Purva", available_minutes=120, preferred_times=["morning", "evening"])

dog = Pet(name="Bruno", species="Dog")
cat = Pet(name="Whiskers", species="Cat")
owner.add_pet(dog)
owner.add_pet(cat)

# Add tasks OUT OF ORDER on purpose (evening before morning)
dog.add_activity(Task(title="Feed Bruno",      duration_minutes=10, priority="high",
                      preferred_time="morning",   category="feeding", recurrence="daily"))
dog.add_activity(Task(title="Evening walk",    duration_minutes=30, priority="medium",
                      preferred_time="evening",   category="exercise", recurrence="weekly"))
dog.add_activity(Task(title="Morning walk",    duration_minutes=20, priority="high",
                      preferred_time="morning",   category="exercise"))

cat.add_activity(Task(title="Feed Whiskers",   duration_minutes=10, priority="medium",
                      preferred_time="evening",   category="feeding", recurrence="daily"))
cat.add_activity(Task(title="Vet appointment", duration_minutes=45, priority="high",
                      preferred_time="afternoon", category="medical"))
# Two tasks in afternoon to trigger conflict detection
cat.add_activity(Task(title="Grooming",        duration_minutes=30, priority="medium",
                      preferred_time="afternoon", category="medical"))
cat.add_activity(Task(title="Playtime",        duration_minutes=20, priority="low",
                      preferred_time="",          category="exercise"))

# Mark one task complete to test filtering
dog.activities[2].mark_complete()  # Morning walk is done (one-off, no recurrence)

calendar = Calendar()
all_tasks = owner.all_tasks()

# ── Test 1: Sort by time ─────────────────────────────────────────────────────
print("=" * 45)
print("  TASKS SORTED BY TIME OF DAY")
print("=" * 45)
for task in calendar.sort_by_time(all_tasks):
    time = task.preferred_time if task.preferred_time else "no time set"
    print(f"  {time:>10}  |  {task.title} ({task.priority})")

# ── Test 2: Filter — pending tasks only ──────────────────────────────────────
print("\n" + "=" * 45)
print("  PENDING TASKS ONLY")
print("=" * 45)
for task in owner.all_tasks(status="pending"):
    print(f"  ✗  {task.title}")

# ── Test 3: Filter — completed tasks only ────────────────────────────────────
print("\n" + "=" * 45)
print("  COMPLETED TASKS ONLY")
print("=" * 45)
for task in owner.all_tasks(status="complete"):
    print(f"  ✓  {task.title}")

# ── Test 4: Filter by pet ────────────────────────────────────────────────────
print("\n" + "=" * 45)
print("  BRUNO'S TASKS ONLY")
print("=" * 45)
for task in owner.tasks_for_pet(dog):
    print(f"  🐾  {task.title} ({task.duration_minutes} min) — {task.status}")

# ── Test 5: Recurring task ───────────────────────────────────────────────────
print("\n" + "=" * 45)
print("  RECURRING TASK TEST")
print("=" * 45)
feed = dog.activities[0]  # Feed Bruno — daily recurrence
print(f"Before: {feed.title} | status: {feed.status} | due: {feed.due_date}")
next_feed = feed.mark_complete(pet=dog)
print(f"After:  {feed.title} | status: {feed.status}")
if next_feed:
    print(f"Next:   {next_feed.title} | due: {next_feed.due_date} | recurrence: {next_feed.recurrence}")

# ── Test 6: Full schedule + conflict detection ────────────────────────────────
print("\n" + "=" * 45)
print(f"  TODAY'S SCHEDULE FOR {owner.name.upper()}")
print("=" * 45)
all_tasks = owner.all_tasks()  # refresh after mark_complete added a new task
calendar.build_plan(owner, all_tasks)
print(calendar.explain())

if calendar.conflicts:
    print("\n  ⚠️  CONFLICTS DETECTED:")
    for note in calendar.conflicts:
        print(f"  →  {note}")
else:
    print("\n  ✅ No conflicts detected.")

print("=" * 45)