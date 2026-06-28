import streamlit as st
from pawpal_system import Owner, Pet, Task, Calendar

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.markdown("Welcome to **PawPal+** — your pet care planning assistant.")

st.divider()

# ── STEP 1: Owner & Pet inputs ───────────────────────────────────────────────
st.subheader("Owner & Pet Info")

owner_name        = st.text_input("Owner name", value="Jordan")
available_minutes = st.number_input(
    "Time available today (minutes)", min_value=5, max_value=600, value=60, step=5
)
pet_name = st.text_input("Pet name", value="Mochi")
species  = st.selectbox("Species", ["dog", "cat", "other"])

# ── STEP 2: Persist Owner & Pet in session_state ─────────────────────────────
if "owner" not in st.session_state or st.session_state.owner.name != owner_name:
    st.session_state.owner = Owner(owner_name, available_minutes=int(available_minutes))
    pet = Pet(pet_name, species)
    st.session_state.owner.add_pet(pet)
    st.session_state.pet = pet
    st.session_state.tasks = []   # reset tasks when owner changes

st.session_state.owner.available_minutes = int(available_minutes)

# ── STEP 3: Task inputs ──────────────────────────────────────────────────────
st.divider()
st.subheader("Tasks")
st.caption("Add tasks below — they'll be saved until you generate a schedule.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col4:
    preferred_time = st.selectbox(
        "Preferred time", ["", "morning", "afternoon", "evening", "night"]
    )
with col5:
    recurrence = st.selectbox("Repeats", ["none", "daily", "weekly"])

if st.button("Add task"):
    st.session_state.tasks.append({
        "title":            task_title,
        "duration_minutes": int(duration),
        "priority":         priority,
        "preferred_time":   preferred_time,
        "recurrence":       None if recurrence == "none" else recurrence,
        "status":           "pending",
        "due_in_days":      0,   # 0 == due today; future occurrences wait
    })
    st.success(f"Task '{task_title}' added!")

# ── Task list with Mark Done buttons ─────────────────────────────────────────
if st.session_state.tasks:
    st.write("Current tasks:")

    header = st.columns([3, 2, 2, 2, 2])
    for col, label in zip(header, ["Title", "Priority", "Time", "Repeats", "Status"]):
        col.markdown(f"**{label}**")

    for i, task in enumerate(st.session_state.tasks):
        col_a, col_b, col_c, col_d, col_e = st.columns([3, 2, 2, 2, 2])
        due_in = task.get("due_in_days", 0)
        title = task["title"] if due_in == 0 else f"{task['title']} (in {due_in}d)"
        col_a.write(title)
        col_b.write(task["priority"])
        col_c.write(task["preferred_time"] or "—")
        col_d.write(task.get("recurrence") or "once")

        if task.get("status") == "complete":
            col_e.success("✓ done")
        elif due_in > 0:
            col_e.info("upcoming")
        else:
            if col_e.button("Mark done", key=f"done_{i}"):
                st.session_state.tasks[i]["status"] = "complete"
                r = task.get("recurrence")
                if r in ("daily", "weekly"):
                    # Mirror Task.mark_complete(): the next occurrence is due
                    # tomorrow (daily) or in a week (weekly), not today.
                    next_task = dict(task)
                    next_task["status"] = "pending"
                    next_task["due_in_days"] = 1 if r == "daily" else 7
                    st.session_state.tasks.append(next_task)
                    st.info(
                        f"'{task['title']}' marked done — "
                        f"next {r} occurrence scheduled for later!"
                    )
                st.rerun()

    st.divider()
    if st.button("Clear all tasks"):
        st.session_state.tasks = []
        st.rerun()
else:
    st.info("No tasks yet. Add one above.")

# ── STEP 4: Generate Schedule ────────────────────────────────────────────────
st.divider()
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    due_today = [
        t for t in st.session_state.tasks
        if t.get("status") != "complete" and t.get("due_in_days", 0) == 0
    ]

    if not due_today:
        st.warning("Add at least one task due today before generating a schedule.")
    else:
        owner = st.session_state.owner
        pet   = st.session_state.pet

        # Clear old activities so re-runs don't duplicate
        pet.activities = []
        for task in due_today:
            pet.add_activity(Task(
                title=            task["title"],
                duration_minutes= task["duration_minutes"],
                priority=         task["priority"],
                preferred_time=   task.get("preferred_time", ""),
                recurrence=       task.get("recurrence"),
            ))

        calendar = Calendar()
        calendar.build_plan(owner, owner.all_tasks())
        st.session_state.calendar = calendar

        if calendar.slots:
            st.success(f"Planned {len(calendar.slots)} activity(ies) for {owner.name}!")
            st.table([
                {
                    "Start":    f"{start // 60}:{start % 60:02d}",
                    "End":      f"{end   // 60}:{end   % 60:02d}",
                    "Task":     task_obj.title,
                    "Pet":      task_obj.pet.name if task_obj.pet else "—",
                    "Priority": task_obj.priority,
                    "Repeats":  task_obj.recurrence or "once",
                    "Minutes":  task_obj.duration_minutes,
                }
                for start, end, task_obj in calendar.slots
            ])

            if calendar.conflicts:
                st.subheader("⚠️ Conflicts detected")
                for note in calendar.conflicts:
                    st.warning(note)
            else:
                st.success("✅ No scheduling conflicts detected!")
        else:
            st.warning("Nothing could be scheduled within the available time.")

        st.markdown("### Why this plan")
        st.text(calendar.explain())