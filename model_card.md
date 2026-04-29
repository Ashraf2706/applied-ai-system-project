
## Reflection and Ethics

### Limitations and biases

The AI advisor's suggestions are only as good as Claude's training data. Coverage is strong for common pets (dogs, cats) but may be generic or incomplete for exotic animals (birds, reptiles, rabbits). There is no memory between sessions — Claude cannot notice patterns over time ("this dog's walk has been getting shorter each week"). All suggestions are general wellness guidance and **are not a substitute for veterinary advice**; a production deployment would require a prominent disclaimer and possibly category filtering to exclude medication-related suggestions entirely.

The scheduling algorithm has its own limits: it uses a single global daily budget rather than per-pet budgets, does not account for the physical proximity of tasks, and detects but does not resolve conflicts.

### Could the system be misused?

The primary risk is **over-reliance on AI health suggestions** for an animal with a serious condition. A user might follow Claude's general recommendation without understanding their pet's specific medical context. Prevention strategies: (1) display a disclaimer that AI suggestions are for general wellness planning only; (2) filter out `category: meds` from AI-generated suggestions since medication decisions require a veterinarian; (3) add a confidence indicator reminding users that suggestions are probabilistic, not prescriptive.

A secondary risk is **API key exposure** if the app is deployed publicly without authentication, since each AI analysis call costs tokens.

### What surprised me during testing

Claude reliably used the `suggest_tasks` tool (because `tool_choice` was set to `required`) and produced well-typed JSON output in every test run — the schema enforcement worked exactly as intended. What was surprising was *quality variance by context richness*: for a dog with no tasks, suggestions were specific and useful. For a dog with six tasks already, Claude occasionally suggested tasks that were already present under a slightly different name (e.g., suggesting "Daily Walk" when "Morning walk" already existed). This reveals a real limitation: the AI compares task names as free text, not by semantic meaning. A production fix would normalize task titles or pass a structured task-type enum alongside each existing task.

### AI collaboration during this project

**Helpful suggestion:** When designing the `suggest_tasks` tool schema, Claude suggested adding `preferred_time_of_day` as an enum-constrained field in `input_schema`. This was immediately useful — it meant the AI's output already matched the `Task` dataclass field exactly, making the "Add all suggestions" feature trivial to implement without any string parsing or mapping logic.

**Flawed suggestion:** Claude initially generated a schedule review prompt that asked for a "detailed 5-point health assessment with action items." The resulting output was far too long for a UI panel and duplicated information already visible in the schedule table. The prompt had to be revised to explicitly cap the response at 2–3 sentences — without a length constraint, Claude defaults to maximally thorough output rather than what is actually useful in a compact interface.

---

## Project Structure

```
applied-ai-system-project/
├── app.py              # Streamlit web UI with AI integration
├── pawpal_system.py    # Core domain model and scheduler (original)
├── ai_advisor.py       # Agentic AI layer (PetCareAdvisor)
├── main.py             # CLI demo (no AI, no browser required)
├── requirements.txt    # Python dependencies
├── tests/
│   └── test_pawpal.py  # 12 unit tests for core scheduling logic
├── reflection.md       # Original project reflection (Modules 1–3)
├── model_card.md      # for relections
└── assests/
    └── uml_final.png       #  Original UML class diagram
```
