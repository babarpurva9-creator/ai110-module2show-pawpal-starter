import streamlit as st

from pawpal import Owner, Pet, Activity, Calendar

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
available_minutes = st.number_input(
    "Time available today (minutes)", min_value=5, max_value=600, value=60, step=5
)
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

if st.button("Add task"):
    st.session_state.tasks.append(
        {"title": task_title, "duration_minutes": int(duration), "priority": priority}
    )

if st.session_state.tasks:
    st.write("Current tasks:")
    st.table(st.session_state.tasks)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button should call your scheduling logic once you implement it.")

if st.button("Generate schedule"):
    if not st.session_state.tasks:
        st.info("Add at least one task above before generating a schedule.")
    else:
        # Build the domain objects from the UI inputs.
        owner = Owner(owner_name, available_minutes=int(available_minutes))
        pet = Pet(pet_name, species)
        owner.add_pet(pet)
        for task in st.session_state.tasks:
            pet.add_activity(
                Activity(
                    title=task["title"],
                    duration_minutes=task["duration_minutes"],
                    priority=task["priority"],
                )
            )

        calendar = Calendar()
        calendar.build_plan(owner, owner.all_activities())

        if calendar.slots:
            st.success(f"Planned {len(calendar.slots)} activity(ies) for {owner.name}.")
            st.table(
                [
                    {
                        "Start": f"{start // 60}:{start % 60:02d}",
                        "End": f"{end // 60}:{end % 60:02d}",
                        "Activity": activity.title,
                        "Priority": activity.priority,
                        "Minutes": activity.duration_minutes,
                    }
                    for start, end, activity in calendar.slots
                ]
            )
        else:
            st.warning("Nothing could be scheduled within the available time.")

        st.markdown("### Why this plan")
        st.text(calendar.explain())
