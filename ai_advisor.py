from __future__ import annotations

import logging
from typing import Optional

import anthropic

from pawpal_system import DailyPlan, Owner, Pet, Priority, TaskCategory

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

_SUGGEST_TOOL = {
    "name": "suggest_tasks",
    "description": (
        "Suggest missing pet care tasks based on the pet's species and current task list. "
        "Only suggest tasks that are clearly absent — do not duplicate existing ones."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "tasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "duration_minutes": {"type": "integer", "minimum": 1, "maximum": 120},
                        "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                        "category": {"type": "string", "enum": ["walk", "feed", "meds", "general"]},
                        "frequency": {
                            "type": "string",
                            "enum": ["daily", "twice-a-day", "weekly", "once"],
                        },
                        "preferred_time_of_day": {
                            "type": "string",
                            "enum": ["morning", "afternoon", "evening", "any"],
                        },
                        "reason": {"type": "string", "description": "Why this task is important for this pet"},
                    },
                    "required": ["title", "duration_minutes", "priority", "category", "frequency", "reason"],
                },
                "minItems": 0,
                "maxItems": 4,
            }
        },
        "required": ["tasks"],
    },
}


class PetCareAdvisor:
    """Agentic AI advisor that identifies care gaps and reviews daily schedules.

    Workflow:
      1. Observe  — build a structured snapshot of the pet's current care plan.
      2. Think    — Claude identifies which standard care tasks are missing.
      3. Act      — Claude calls suggest_tasks tool with structured recommendations.
      4. Verify   — Claude reviews the generated DailyPlan for health/wellness gaps.
    """

    MODEL = "claude-sonnet-4-6"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        self.logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # Step 1 – Observe
    # ------------------------------------------------------------------

    def _build_pet_context(self, pet: Pet, owner: Owner) -> str:
        budget = owner.preferences.get("daily_time_budget", "not set")
        reqs = ", ".join(pet.requirements) if pet.requirements else "none"
        pending = pet.pending_tasks()
        task_lines = "\n".join(
            f"  - {t.title}: {t.duration_minutes}min, priority={t.priority.value}, "
            f"frequency={t.frequency}, category={t.category.value}"
            for t in pending
        ) or "  (no tasks yet)"
        return (
            f"Pet: {pet.name} ({pet.species})\n"
            f"Owner: {owner.name}\n"
            f"Daily time budget: {budget} minutes\n"
            f"Special requirements: {reqs}\n"
            f"Current pending tasks ({len(pending)}):\n{task_lines}"
        )

    # ------------------------------------------------------------------
    # Steps 2 & 3 – Think and Act
    # ------------------------------------------------------------------

    def suggest_missing_tasks(self, pet: Pet, owner: Owner) -> list[dict]:
        """Ask Claude to identify missing care tasks and return them as structured data."""
        context = self._build_pet_context(pet, owner)
        self.logger.info("Analyzing care gaps for %s (%s)", pet.name, pet.species)

        response = self.client.messages.create(
            model=self.MODEL,
            max_tokens=1024,
            tools=[_SUGGEST_TOOL],
            tool_choice={"type": "required", "name": "suggest_tasks"},
            messages=[
                {
                    "role": "user",
                    "content": (
                        "You are a veterinary care expert. Analyze this pet's current care plan "
                        "and call suggest_tasks with any important missing tasks. "
                        "Limit suggestions to 2–4 genuinely absent tasks. "
                        "If nothing is missing, return an empty list.\n\n"
                        + context
                    ),
                }
            ],
        )

        suggestions: list[dict] = []
        for block in response.content:
            if block.type == "tool_use" and block.name == "suggest_tasks":
                suggestions = block.input.get("tasks", [])
                break

        self.logger.info("Suggested %d task(s) for %s", len(suggestions), pet.name)
        return suggestions

    # ------------------------------------------------------------------
    # Step 4 – Verify
    # ------------------------------------------------------------------

    def review_daily_plan(self, pet: Pet, owner: Owner, plan: DailyPlan) -> str:
        """Ask Claude to review the generated schedule for care gaps."""
        context = self._build_pet_context(pet, owner)

        scheduled_lines = "\n".join(
            f"  {s.start_time.strftime('%H:%M')}–{s.end_time.strftime('%H:%M')}: "
            f"{s.task.title} ({s.task.priority.value})"
            for s in plan.scheduled_tasks
            if s.pet_name == pet.name
        ) or "  (no tasks scheduled for this pet)"

        deferred_names = ", ".join(
            t.title
            for t in plan.unscheduled_tasks
            if owner.find_pet_for_task(t) and owner.find_pet_for_task(t).name == pet.name
        ) or "none"

        self.logger.info("Reviewing daily plan for %s", pet.name)

        response = self.client.messages.create(
            model=self.MODEL,
            max_tokens=256,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Review this daily care schedule for {pet.name} in 2–3 sentences. "
                        "Note any health risks, critical gaps, or one key tip for the owner.\n\n"
                        f"{context}\n\n"
                        f"Today's scheduled tasks:\n{scheduled_lines}\n\n"
                        f"Deferred tasks: {deferred_names}"
                    ),
                }
            ],
        )

        review: str = response.content[0].text
        self.logger.info("Schedule review complete for %s", pet.name)
        return review

    # ------------------------------------------------------------------
    # Orchestrator
    # ------------------------------------------------------------------

    def run_care_analysis(
        self,
        pet: Pet,
        owner: Owner,
        plan: Optional[DailyPlan] = None,
    ) -> dict:
        """Full agentic loop: observe → think → act → verify.

        Returns a dict with keys:
          suggestions  – list of task dicts from Claude
          review       – str narrative review (only when plan is provided)
          error        – str error message if something went wrong, else None
          logs         – list of human-readable step messages for UI display
        """
        logs: list[str] = []
        result: dict = {"suggestions": [], "review": None, "error": None, "logs": logs}

        logs.append(f"[Observe] Building care profile for {pet.name} ({pet.species})")
        self.logger.info("Starting agentic care analysis for %s", pet.name)

        try:
            logs.append("[Think & Act] Asking Claude to identify missing care tasks…")
            result["suggestions"] = self.suggest_missing_tasks(pet, owner)
            logs.append(f"[Act] Claude suggested {len(result['suggestions'])} task(s)")

            if plan is not None:
                logs.append("[Verify] Asking Claude to review the generated daily schedule…")
                result["review"] = self.review_daily_plan(pet, owner, plan)
                logs.append("[Verify] Review complete")
            else:
                logs.append("[Verify] No schedule generated yet — skipping plan review")

        except anthropic.APIError as exc:
            msg = f"AI service error: {exc}"
            self.logger.error(msg)
            logs.append(f"[Error] {msg}")
            result["error"] = msg
        except Exception as exc:  # noqa: BLE001
            msg = f"Unexpected error: {exc}"
            self.logger.error(msg)
            logs.append(f"[Error] {msg}")
            result["error"] = msg

        logs.append("[Done] Agentic analysis finished")
        return result
