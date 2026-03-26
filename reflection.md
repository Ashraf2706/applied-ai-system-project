# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

A system where a Scheduler takes owner constraints, pet information, and a set of care Tasks, then produces an optimized plan by respecting time availability and task priorities.


- What classes did you include, and what responsibilities did you assign to each?

Owner: Stores owner name, available daily time budget and manage owner preferneces/ constraints.

Pet: Store pet info (name, species). Track pet-specific requirements

Task: Store task details: name, duration (minutes), priority level, category (walk/feed/med). Support updating task attributes

Scheduler: Accept owner, pet, and list of tasks as input. Implement scheduling algorithm (sort by priority, fit within time constraints). Generate a daily plan with task timing. Provide reasoning for placement decisions

DailyPlan: Store scheduled tasks with assigned times. Track which tasks fit and which were deferred. Provide explanation of scheduling decisions

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Added pet_name: Optional[str] to Task:
Why: explicit owner/pet task linkage, ready for multi-pet support.

Added tasks: List["Task"] to Pet, plus add_task/remove_task stubs:
Why: captures direct Pet-to-Task relationship.
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
