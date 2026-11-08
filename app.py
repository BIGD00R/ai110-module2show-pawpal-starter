from datetime import date, time

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

PRIORITY_TO_INT = {"low": 1, "medium": 2, "high": 3}
INT_TO_PRIORITY = {v: k for k, v in PRIORITY_TO_INT.items()}
FREQUENCIES = ["once", "daily", "weekly"]


def task_rows(tasks: list[Task]) -> list[dict]:
    """Turn tasks into table rows for st.table."""
    return [
        {
            "time": t.start_time or "—",
            "pet": t.pet_name,
            "task": t.title,
            "minutes": t.duration_minutes,
            "priority": INT_TO_PRIORITY.get(t.priority, t.priority),
            "repeats": t.frequency,
            "due": str(t.due_date) if t.due_date else "—",
            "status": "done" if t.completed else "pending",
        }
        for t in tasks
    ]


def show_conflicts(warnings: list[str]) -> None:
    """Show scheduler conflict warnings in one clear, non-blocking box."""
    if not warnings:
        st.success("No time conflicts.")
        return
    items = "\n".join(f"- {w}" for w in warnings)
    st.warning(
        f"**{len(warnings)} time conflict(s) to look at**\n\n{items}\n\n"
        "To fix one, change a start time or shorten a task. If the tasks can happen "
        "together (for example, walking both dogs at once), you can safely ignore it."
    )


def complete_task_cb(pet: Pet, title: str) -> None:
    """Button callback. It runs before the page reruns, so the tables show the update."""
    next_task = pet.complete_task(title)
    messages = [("success", f"Marked '{title}' complete for {pet.name}.")]
    if next_task is not None:
        messages.append(
            ("info", f"🔁 This task repeats {next_task.frequency}. The next one is due {next_task.due_date}.")
        )
    st.session_state.flash = messages


st.title("🐾 PawPal+")
st.caption(f"Plan your pets' care for today ({date.today():%A, %B %d}).")

# Streamlit reruns this script on every click, so keep the Owner in
# st.session_state and only create it if it isn't already in the "vault".
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")
owner = st.session_state.owner
scheduler = Scheduler(owner)

# ---------------------------------------------------------------- owner
st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)
owner.available_minutes = int(
    st.number_input(
        "Time available today (minutes)",
        min_value=1,
        max_value=1440,
        value=owner.available_minutes,
    )
)

# ---------------------------------------------------------------- pets
st.subheader("Pets")
col_a, col_b, col_c = st.columns(3)
with col_a:
    pet_name = st.text_input("Pet name", value="Mochi")
with col_b:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col_c:
    age = st.number_input("Age", min_value=0, max_value=40, value=3)

if st.button("Add pet"):
    name = pet_name.strip()
    if not name:
        st.error("Please enter a pet name.")
    elif any(p.name.lower() == name.lower() for p in owner.pets):
        st.warning(f"You already have a pet named {name}.")
    else:
        owner.add_pet(Pet(name=name, species=species, age=int(age)))
        st.success(f"Added {name}.")

if owner.pets:
    st.table(
        [{"name": p.name, "species": p.species, "age": p.age, "tasks": len(p.tasks)} for p in owner.pets]
    )
else:
    st.info("No pets yet. Add one above.")

# ---------------------------------------------------------------- add a task
st.subheader("Add a task")

if owner.pets:
    target_name = st.selectbox("Task for", [p.name for p in owner.pets])

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    col4, col5 = st.columns(2)
    with col4:
        has_time = st.checkbox("Set a start time", value=True)
        start = st.time_input("Start time", value=time(8, 0), step=300, disabled=not has_time)
    with col5:
        frequency = st.selectbox("Repeats", FREQUENCIES)

    if st.button("Add task"):
        title = task_title.strip()
        target = next(p for p in owner.pets if p.name == target_name)
        if not title:
            st.error("Please enter a task title.")
        elif any(t.title.lower() == title.lower() for t in target.get_pending_tasks()):
            st.warning(f"{target.name} already has a pending task called '{title}'.")
        else:
            target.add_task(
                Task(
                    title=title,
                    duration_minutes=int(duration),
                    priority=PRIORITY_TO_INT[priority],
                    start_time=f"{start:%H:%M}" if has_time else None,
                    frequency=frequency,
                )
            )
            st.success(f"Added '{title}' to {target.name}.")
else:
    st.info("Add a pet first, then you can give it tasks.")

# ---------------------------------------------------------------- task list
st.subheader("Your tasks")

if owner.get_all_tasks():
    f1, f2 = st.columns(2)
    with f1:
        pet_filter = st.selectbox("Show pet", ["All pets"] + [p.name for p in owner.pets])
    with f2:
        status_filter = st.selectbox("Show status", ["All", "Pending", "Completed"])

    visible = owner.filter_tasks(
        pet_name=None if pet_filter == "All pets" else pet_filter,
        completed={"All": None, "Pending": False, "Completed": True}[status_filter],
    )
    if visible:
        st.caption("Sorted by start time. Tasks without a start time are listed last.")
        st.table(task_rows(scheduler.sort_by_time(visible)))
    else:
        st.info("No tasks match those filters.")

    st.markdown("**Time conflicts**")
    show_conflicts(scheduler.find_conflicts())

    # ---------------------------------------------------------- mark complete
    st.markdown("**Mark a task complete**")
    pending = scheduler.sort_by_time(owner.filter_tasks(completed=False))
    if pending:
        options = {
            f"{t.pet_name}: {t.title}" + (f" at {t.start_time}" if t.start_time else ""): t
            for t in pending
        }
        label = st.selectbox("Task", list(options), key="complete_choice")
        chosen = options[label]
        chosen_pet = next(p for p in owner.pets if p.name == chosen.pet_name)
        st.button(
            "Mark complete",
            on_click=complete_task_cb,
            args=(chosen_pet, chosen.title),
        )
    else:
        st.info("Nothing left to complete.")

    for kind, message in st.session_state.pop("flash", []):
        getattr(st, kind)(message)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ---------------------------------------------------------------- schedule
st.subheader("Today's schedule")
st.caption(
    f"You have {owner.available_minutes} minutes. The scheduler picks tasks by priority "
    "(high first, then shortest first), then shows the chosen tasks in time order."
)

if st.button("Generate schedule"):
    plan = scheduler.generate_daily_plan()
    if plan:
        used = sum(t.duration_minutes for t in plan)
        st.success(f"Planned {len(plan)} task(s), using {used} of {owner.available_minutes} minutes.")
        st.table(task_rows(scheduler.sort_by_time(plan)))
        show_conflicts(scheduler.find_conflicts(plan))
    elif scheduler.skipped:
        st.warning("Nothing fits in the time available.")
    else:
        st.info("No tasks are due today. Add a task or check the filters above.")

    if scheduler.skipped:
        lines = "\n".join(f"- {t.title} for {t.pet_name}: {reason}" for t, reason in scheduler.skipped)
        st.warning(f"**Left out of today's plan**\n\n{lines}")

    with st.expander("Why this plan?"):
        st.text(scheduler.explain_plan())
