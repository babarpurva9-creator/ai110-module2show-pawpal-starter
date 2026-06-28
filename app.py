"""PawPal+ Streamlit UI — Phase 4 polish.

Surfaces all Calendar scheduler behaviours (sorting, conflict warnings,
budget reasoning, recurrence) through professional Streamlit components.
"""

import streamlit as st
from pawpal_system import Owner, Pet, Task, Calendar

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🐾 PawPal+")
st.markdown("Your smart pet-care planning assistant.")
st.divider()

# ── SECTION 1: Owner & Pet ────────────────────────────────────────────────────
st.subheader("👤 Owner & Pet Info")

col_owner, col_mins = st.columns(2)
with col_owner:
    owner_name = st.text_input("Owner name", value="Jordan")
with col_mins:
    available_minutes = st.number_input(
        "Time available today (minutes)", min_value=5, max_value=600, value=60, step=5
    )

col_pet, col_species, col_start = st.columns(3)
with col_pet:
    pet_name = st.text_input("Pet name", value="Mochi")
with col_species:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col_start:
    day_start_hour = st.number_input(
        "Day starts at (hour)", min_value=4, max_value=12, value=8
    )

# ── Session-state: Owner & Pet ────────────────────────────────────────────────
owner_changed = (
    "owner" not in st.session_state
    or st.session_state.owner.name != owner_name
    or st.session_state.pet.name  != pet_name
)

if owner_changed:
    st.session_state.owner = Owner(
        owner_name,
        available_minutes=int(available_minutes),
        day_start_minutes=int(day_start_hour) * 60,
    )
    pet = Pet(pet_name, species)
    st.session_state.owner.add_pet(pet)
    st.session_state.pet   = pet
    st.session_state.tasks = []

# Keep budget & start time live even without owner change.
st.session_state.owner.available_minutes  = int(available_minutes)
st.session_state.owner.day_start_minutes  = int(day_start_hour) * 60

# ── SECTION 2: Add Tasks ──────────────────────────────────────────────────────
st.divider()
st.subheader("📋 Tasks")
st.caption("Tasks are saved here until you build the schedule.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

with st.form("add_task_form", clear_on_submit=True):
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        task_title = st.text_input("Task title", value="Morning walk")
    with fc2:
        duration = st.number_input(
            "Duration (min)", min_value=1, max_value=240, value=20
        )
    with fc3:
        category = st.text_input("Category", value="general",
                                 help="e.g. feeding, exercise, medical")

    fc4, fc5, fc6 = st.columns(3)
    with fc4:
        priority = st.selectbox("Priority", ["high", "medium", "low"])
    with fc5:
        preferred_time = st.selectbox(
            "Preferred time", ["", "morning", "afternoon", "evening", "night"]
        )
    with fc6:
        recurrence = st.selectbox("Repeats", ["none", "daily", "weekly"])

    submitted = st.form_submit_button("➕ Add task")
    if submitted:
        st.session_state.tasks.append({
            "title":            task_title,
            "duration_minutes": int(duration),
            "priority":         priority,
            "preferred_time":   preferred_time,
            "category":         category,
            "recurrence":       None if recurrence == "none" else recurrence,
            "status":           "pending",
            "due_in_days":      0,
        })
        st.success(f"✅ '{task_title}' added!")

# ── Task list ─────────────────────────────────────────────────────────────────
if st.session_state.tasks:
    st.markdown("#### Current tasks")

    hc = st.columns([3, 2, 2, 2, 2, 2])
    for col, lbl in zip(hc, ["Title", "Priority", "Time", "Category", "Repeats", "Status"]):
        col.markdown(f"**{lbl}**")

    for i, task in enumerate(st.session_state.tasks):
        due_in = task.get("due_in_days", 0)
        display_title = task["title"] if due_in == 0 else f"{task['title']} (in {due_in}d)"

        ca, cb, cc, cd, ce, cf = st.columns([3, 2, 2, 2, 2, 2])
        ca.write(display_title)
        cb.write(task["priority"])
        cc.write(task["preferred_time"] or "—")
        cd.write(task.get("category", "general"))
        ce.write(task.get("recurrence") or "once")

        if task.get("status") == "complete":
            cf.success("✓ done")
        elif due_in > 0:
            cf.info("upcoming")
        else:
            if cf.button("Mark done", key=f"done_{i}"):
                st.session_state.tasks[i]["status"] = "complete"
                r = task.get("recurrence")
                if r in ("daily", "weekly"):
                    next_task = dict(task)
                    next_task["status"]      = "pending"
                    next_task["due_in_days"] = 1 if r == "daily" else 7
                    st.session_state.tasks.append(next_task)
                    st.info(
                        f"'{task['title']}' marked done — "
                        f"next {r} occurrence queued!"
                    )
                st.rerun()

    st.divider()
    if st.button("🗑️ Clear all tasks"):
        st.session_state.tasks = []
        st.rerun()
else:
    st.info("No tasks yet — add one above.")

# ── SECTION 3: Build Schedule ─────────────────────────────────────────────────
st.divider()
st.subheader("📅 Build Today's Schedule")

if st.button("⚙️ Generate schedule", type="primary"):
    due_today = [
        t for t in st.session_state.tasks
        if t.get("status") != "complete" and t.get("due_in_days", 0) == 0
    ]

    if not due_today:
        st.warning("⚠️ Add at least one pending task due today before generating.")
    else:
        owner = st.session_state.owner
        pet   = st.session_state.pet

        # Rebuild pet activities fresh so re-runs don't duplicate.
        pet.activities = []
        for t in due_today:
            pet.add_activity(Task(
                title=            t["title"],
                duration_minutes= t["duration_minutes"],
                priority=         t["priority"],
                preferred_time=   t.get("preferred_time", ""),
                category=         t.get("category", "general"),
                recurrence=       t.get("recurrence"),
            ))

        calendar = Calendar()
        calendar.build_plan(owner, owner.all_tasks())
        st.session_state.calendar = calendar

        # ── Conflict warnings — shown FIRST so the owner sees them immediately ──
        if calendar.conflicts:
            st.error("⚠️ Scheduling conflicts detected — review before confirming your plan:")
            for note in calendar.conflicts:
                # Pull out the window keyword for a targeted header.
                window = next(
                    (w for w in ("morning", "afternoon", "evening", "night")
                     if w in note), None
                )
                header = f"🕐 {window.capitalize()} window clash" if window else "🔀 Scheduling clash"
                with st.expander(header, expanded=True):
                    st.warning(note)
                    st.caption(
                        "💡 Tip: spread these tasks across different time windows "
                        "or increase your available minutes."
                    )
        else:
            st.success("✅ No scheduling conflicts detected!")

        # ── Schedule table ────────────────────────────────────────────────────
        if calendar.slots:
            total_scheduled = sum(end - start for start, end, _ in calendar.slots)
            remaining = owner.available_minutes - total_scheduled

            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Tasks scheduled",  len(calendar.slots))
            mc2.metric("Minutes used",     total_scheduled)
            mc3.metric("Minutes remaining", remaining)

            st.markdown("#### 🗓️ Your plan — sorted by time of day")
            st.table([
                {
                    "Start":    f"{start // 60}:{start % 60:02d}",
                    "End":      f"{end   // 60}:{end   % 60:02d}",
                    "Task":     task_obj.title,
                    "Pet":      task_obj.pet.name if task_obj.pet else "—",
                    "Priority": task_obj.priority.capitalize(),
                    "Category": task_obj.category,
                    "Repeats":  task_obj.recurrence or "once",
                    "Duration": f"{task_obj.duration_minutes} min",
                }
                for start, end, task_obj in calendar.slots
            ])

            # ── Tasks skipped for budget ──────────────────────────────────────
            skipped_lines = [
                line for line in calendar.reasoning if line.startswith("Skipped")
            ]
            if skipped_lines:
                with st.expander("⏭️ Tasks cut due to time budget", expanded=False):
                    for line in skipped_lines:
                        st.warning(line)
                    st.caption(
                        "💡 Tip: increase 'Time available today' or reduce task "
                        "durations to fit more into your day."
                    )
        else:
            st.warning("Nothing could be scheduled within your available time.")

        # ── Scheduler reasoning log ───────────────────────────────────────────
        with st.expander("🧠 Why this plan (scheduler reasoning)", expanded=False):
            for line in calendar.reasoning:
                if line.startswith("Conflict"):
                    st.error(line)
                elif line.startswith("Skipped"):
                    st.warning(line)
                elif line.startswith("Heads up"):
                    st.warning(line)
                elif line.startswith("Deferred") or line.startswith("Ignored"):
                    st.info(line)
                else:
                    st.write(line)