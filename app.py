import streamlit as st

from ai_advisor import PetCareAdvisor
from pawpal_system import DailyPlan, Owner, Pet, Priority, Scheduler, Task, TaskCategory

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")
st.title("🐾 PawPal+ — AI-Powered Pet Care Planner")

# ── Session state ────────────────────────────────────────────────────────────
for key, default in [
    ("owner_vault", {}),
    ("last_plan", None),
    ("ai_results", {}),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar: owner settings ───────────────────────────────────────────────────
with st.sidebar:
    st.header("API Key")
    api_key_input = st.text_input(
        "Anthropic API key",
        type="password",
        placeholder="sk-ant-...",
        help="Required for AI Care Analysis. Get one at console.anthropic.com",
    )

    st.divider()
    st.header("Owner Settings")
    owner_name = st.text_input("Your name", value="Jordan")

    if owner_name not in st.session_state.owner_vault:
        st.session_state.owner_vault[owner_name] = Owner(name=owner_name)
    owner: Owner = st.session_state.owner_vault[owner_name]

    time_budget = st.slider("Daily time budget (minutes)", 30, 480, 120, step=15)
    owner.update_time_budget(time_budget)

    st.divider()
    st.markdown(f"**Pets registered:** {len(owner.pets)}")
    st.markdown(f"**Total tasks:** {len(owner.all_tasks())}")
    st.markdown(f"**Pending tasks:** {len(owner.pending_tasks())}")

scheduler = Scheduler(owner)

# ── Pet & task management ─────────────────────────────────────────────────────
col_pet, col_task = st.columns(2)

with col_pet:
    st.subheader("Add a Pet")
    pet_name_input = st.text_input("Pet name", value="Mochi")
    species_input = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
    if st.button("Add Pet"):
        if owner.get_pet(pet_name_input) is None:
            owner.add_pet(Pet(name=pet_name_input, species=species_input))
            st.success(f"Added {pet_name_input}!")
        else:
            st.warning(f"{pet_name_input} already exists.")

with col_task:
    st.subheader("Add a Task")
    pet_options = [p.name for p in owner.pets]
    task_pet = st.selectbox("Assign to pet", pet_options or ["No pets yet"], key="task_pet_select")
    task_title = st.text_input("Task title", value="Morning walk")

    tc1, tc2 = st.columns(2)
    with tc1:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        priority = st.selectbox("Priority", ["high", "medium", "low"])
    with tc2:
        category = st.selectbox("Category", ["walk", "feed", "meds", "general"])
        frequency = st.selectbox("Frequency", ["daily", "twice-a-day", "weekly", "once"])
    time_of_day = st.selectbox("Preferred time", ["any", "morning", "afternoon", "evening"])

    if st.button("Add Task"):
        target_pet = owner.get_pet(task_pet)
        if target_pet is None:
            st.error("Add a pet first.")
        else:
            task = Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=Priority[priority.upper()],
                category=TaskCategory[category.upper()],
                frequency=frequency,
                preferred_time_of_day=None if time_of_day == "any" else time_of_day,
            )
            target_pet.add_task(task)
            st.success(f"Added '{task_title}' to {target_pet.name}.")

# ── Current task tables ───────────────────────────────────────────────────────
st.divider()
st.subheader("Current Task Lists")

if not owner.pets:
    st.info("No pets yet. Add one above.")
else:
    for pet in owner.pets:
        with st.expander(
            f"🐾 {pet.name} ({pet.species}) — {len(pet.pending_tasks())} pending / {len(pet.completed_tasks())} done",
            expanded=True,
        ):
            if pet.tasks:
                st.table(
                    [
                        {
                            "#": i,
                            "Task": t.title,
                            "Min": t.duration_minutes,
                            "Priority": t.priority.value,
                            "Category": t.category.value,
                            "Frequency": t.frequency,
                            "Status": "Done" if t.completed else "Pending",
                        }
                        for i, t in enumerate(pet.tasks, 1)
                    ]
                )
            else:
                st.info("No tasks yet.")

# ── AI Care Analysis (agentic workflow) ───────────────────────────────────────
st.divider()
st.subheader("🤖 AI Care Analysis")
st.caption(
    "The AI advisor runs a four-step agentic loop: **observe** → **think** → **act** → **verify**. "
    "It identifies missing care tasks and reviews your generated schedule."
)

if not owner.pets:
    st.info("Add a pet to enable AI analysis.")
elif not api_key_input:
    st.warning("Enter your Anthropic API key in the sidebar to enable AI analysis.")
else:
    ai_pet_name = st.selectbox(
        "Analyze care plan for:", [p.name for p in owner.pets], key="ai_pet_select"
    )
    ai_pet = owner.get_pet(ai_pet_name)

    if st.button("🔍 Run AI Care Analysis", type="primary"):
        with st.spinner("Claude is analyzing your pet's care plan…"):
            advisor = PetCareAdvisor(api_key=api_key_input)
            current_plan: DailyPlan | None = st.session_state.last_plan
            analysis = advisor.run_care_analysis(ai_pet, owner, current_plan)
            st.session_state.ai_results[ai_pet_name] = analysis

    if ai_pet_name in st.session_state.ai_results:
        analysis = st.session_state.ai_results[ai_pet_name]

        # Workflow log
        with st.expander("Agentic workflow log", expanded=False):
            for entry in analysis.get("logs", []):
                st.text(entry)

        if analysis.get("error"):
            st.error(f"AI error: {analysis['error']}")
        else:
            suggestions = analysis.get("suggestions", [])
            if suggestions:
                st.markdown("**Missing care tasks Claude identified:**")
                for s in suggestions:
                    with st.container(border=True):
                        st.markdown(
                            f"**{s['title']}** — {s['duration_minutes']} min · "
                            f"{s['priority']} priority · {s['frequency']} · {s['category']}"
                        )
                        st.caption(f"Why: {s.get('reason', '—')}")

                if st.button(f"➕ Add all {len(suggestions)} suggestion(s) to {ai_pet_name}"):
                    added = 0
                    for s in suggestions:
                        try:
                            new_task = Task(
                                title=s["title"],
                                duration_minutes=int(s["duration_minutes"]),
                                priority=Priority[s["priority"].upper()],
                                category=TaskCategory[s["category"].upper()],
                                frequency=s.get("frequency", "daily"),
                                preferred_time_of_day=s.get("preferred_time_of_day"),
                            )
                            ai_pet.add_task(new_task)
                            added += 1
                        except (KeyError, ValueError):
                            pass
                    st.success(f"Added {added} task(s) to {ai_pet_name}.")
                    st.rerun()
            else:
                st.success("Care plan looks complete — no missing tasks detected.")

            if analysis.get("review"):
                st.markdown("**AI Schedule Review:**")
                st.info(analysis["review"])
            elif st.session_state.last_plan is None:
                st.caption("Generate a schedule below to get an AI plan review.")

# ── Schedule generation ────────────────────────────────────────────────────────
st.divider()
st.subheader("📅 Daily Schedule")

if st.button("Generate Schedule", type="primary"):
    if not owner.pets or not owner.all_tasks():
        st.error("Add at least one pet with tasks before generating a schedule.")
    else:
        plan = scheduler.generate_daily_plan()
        st.session_state.last_plan = plan
        # Clear stale AI reviews so users re-run analysis against new plan
        for key in list(st.session_state.ai_results):
            st.session_state.ai_results[key].pop("review", None)
        st.success(
            f"Schedule generated — {len(plan.scheduled_tasks)} task(s) scheduled, "
            f"{len(plan.unscheduled_tasks)} deferred."
        )

if st.session_state.last_plan:
    plan: DailyPlan = st.session_state.last_plan

    if plan.scheduled_tasks:
        st.markdown("**Scheduled tasks:**")
        st.table(
            [
                {
                    "Time": f"{item.start_time.strftime('%H:%M')} – {item.end_time.strftime('%H:%M')}",
                    "Pet": item.pet_name or "?",
                    "Task": item.task.title,
                    "Priority": item.task.priority.value,
                    "Min": item.task.duration_minutes,
                }
                for item in plan.scheduled_tasks
            ]
        )
    else:
        st.warning("No tasks fit within the daily budget. Try increasing it in the sidebar.")

    if plan.unscheduled_tasks:
        st.markdown("**Deferred (outside budget):**")
        for t in plan.unscheduled_tasks:
            st.markdown(f"- {t.title} ({t.priority.value}, {t.duration_minutes} min)")

    warnings = plan.conflict_warnings()
    if warnings:
        st.warning("Schedule conflicts detected:")
        for w in warnings:
            st.markdown(f"- {w}")

    with st.expander("Scheduler reasoning"):
        st.text(scheduler.provide_reasoning(plan))
