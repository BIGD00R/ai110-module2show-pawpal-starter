# PawPal+ Project Reflection

> **Draft note:** I wrote these answers from what was actually built and tested in this project. Lines marked **Your turn** need your own experience. Reword everything in your own voice before submitting.

## 1. System Design

**Three core actions a user should be able to perform**

1. **Add an owner and pet.** Enter basic info (owner name, how much time they have per day, pet name, species, age) so the app knows who it is planning for.
2. **Add and edit care tasks.** Create tasks such as a walk, feeding, or medication for a pet, each with at least a duration and a priority, and optionally a start time and a repeat setting.
3. **Generate and view today's plan.** Ask the app for a daily schedule that fits the owner's available time, ordered by priority, and read a short explanation of why tasks were included, ordered, or left out.

**a. Initial design**

My initial UML (see `diagrams/uml_draft.mmd`) has four classes:

- **Task** (dataclass): one care activity. It holds a title, duration in minutes, priority, category, optional preferred time, and a completed flag. It can mark itself complete and say whether it is high priority.
- **Pet** (dataclass): holds the pet's name, species, age, and its list of tasks. It is responsible for adding and removing its own tasks and returning the ones still pending.
- **Owner**: holds the owner's name, daily available minutes, preferences, and a list of pets. It manages its pets and can gather every task across all of them.
- **Scheduler**: takes an owner and builds the daily plan. It selects and orders tasks to fit the available time and produces an explanation of its choices.

Relationships: an Owner has many Pets, a Pet has many Tasks, and the Scheduler works from an Owner. I kept the scheduling logic out of the data classes so Task, Pet and Owner stay simple containers and all the decision-making lives in one place.

**b. Design changes**

The design changed in two rounds. After reviewing the skeleton for missing relationships and bottlenecks, I made two changes:

- **Added `pet_name` to Task.** The scheduler gathers tasks from every pet into one flat list, which would lose track of which pet each task is for. A plan that says "Walk (30 min)" without saying which pet is not useful, so `Pet.add_task` now stamps the task with its pet's name.
- **Gave Scheduler `plan` and `skipped` attributes.** `explain_plan()` originally had nothing to explain, because `generate_daily_plan()` only returned a list and kept no record of what it dropped or why. Storing the chosen tasks and the skipped tasks with a reason lets the explanation come from the same data as the plan.

Later, adding sorting, recurrence and conflict detection grew the model (see `diagrams/uml_final.mmd`): `Task` gained `start_time`, `due_date` and `frequency`; `Pet` gained `complete_task()`; `Owner` gained `filter_tasks()`; and `Scheduler` gained `sort_by_time()` and `find_conflicts()`. The four-class structure itself stayed the same, and the new behavior went into the class that already owned that kind of work.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers four things: the owner's available minutes (a hard budget), each task's priority, whether the task is already completed, and its due date (tasks due in the future are left out of today's plan). Start times are used for sorting and for conflict warnings, but not for choosing tasks. The owner's `preferences` and a task's `category` and `preferred_time` are stored but not used yet.

I ranked priority first, then duration, because the cost of missing something is very different across tasks: skipping medication is worse than skipping grooming. Within the same priority, shorter tasks go first so more of them fit in the time available. The time budget is treated as a hard limit because an owner really cannot do more than they have time for.

**b. Tradeoffs**

My scheduler **warns about time conflicts but does not resolve them**. `Scheduler.find_conflicts()` checks real overlaps (a 08:00 walk lasting 30 minutes conflicts with a 08:15 feeding, not only with another 08:00 task) and returns warning messages, but `generate_daily_plan()` picks tasks by priority and available minutes without looking at start times. In my demo, "Medication" and "Evening walk" both start at 18:00 and both end up in the plan, with the conflict reported separately.

A related, smaller tradeoff is in the overlap check itself. I first wrote it as a sorted sweep that stops early, then replaced it with a plain pairwise comparison (`itertools.combinations`) because it is much easier to read. It does more comparisons as the task list grows, but an owner has a few dozen tasks at most, so the simpler version is the better choice.

This is reasonable here because the owner knows things the app doesn't: whether two pets can be walked together, or whether a 10-minute medication can happen while the dog eats. Automatically moving or dropping a task could silently break a medication schedule, so for now the app flags the problem and lets the owner decide.

---

## 3. AI Collaboration

**a. How you used AI**

I used the AI coding assistant at every stage: brainstorming the four classes and drafting the UML, generating the class skeleton, implementing the methods, proposing a list of small algorithms (sorting, filtering, recurrence, conflicts), drafting tests, and wiring the logic into the Streamlit UI. The features that helped most were the ones that let it act on the whole project: editing several files in one go, and running the code and the test suite right away instead of just describing what should happen. The most helpful prompts were specific and asked for review rather than just generation, for example asking it to look at the skeleton for missing relationships, and asking "what are the most important edge cases to test for a pet scheduler with sorting and recurring tasks?"

**b. Judgment and verification**

- **A suggestion I changed to keep the design clean.** A natural way to build recurring tasks is to have `Task.mark_complete()` add the next occurrence to its pet directly. I kept `Task` unaware of its pet: `mark_complete()` just returns the next occurrence, and `Pet.complete_task()` decides where it goes. That keeps `Task` a simple data object and puts the "add to the list" step in the class that owns the list. I also left out an AI-suggested stretch idea, automatically assigning start times in the plan, because it would have made the scheduler much more complicated than this scenario needs.
- **How I verified.** I did not trust the first implementation just because it ran. Before writing the final tests I probed for edge cases with a short script, which showed three real bugs: completing a recurring task twice created duplicate copies, finishing an overdue task late created a next occurrence still in the past, and a task with no due date was never compared for conflicts. I fixed each one and added a test that fails without the fix. I also checked the final UML against the code with a script that compares the class members.

> **Your turn:** add a moment from your own work where you disagreed with or rewrote something the AI suggested, if you have one. The examples above are accurate for this project, but the strongest answers are ones you lived through.

> **Your turn (separate chat sessions):** the assignment asks how separate chats for different phases helped. The work behind this draft was done in one continuous session, so write honestly about how you kept the phases apart (design, skeleton, algorithms, tests, UI), and whether separate chats would have helped.

---

## 4. Testing and Verification

**a. What you tested**

I wrote 44 pytest tests covering five areas: sorting (chronological order, numeric rather than text comparison, unscheduled tasks last, ties), filtering (by pet, by status, both, neither), recurring tasks (daily and weekly next dates, month and year rollover, no duplicates, overdue tasks), conflict detection (overlaps, identical start times, and the cases that must not be flagged, like back-to-back tasks), and the daily plan (priority order, exact fit, zero minutes, tasks left out). These matter because the scheduler's value is that its output can be trusted: a wrongly sorted list or a missed conflict would quietly give the owner bad information. The tests use a fixed "today" so they don't break when the calendar changes.

**b. Confidence**

I'm fairly confident in the scheduling logic: 4 out of 5. All 44 tests pass, and the edge-case probe found bugs that are now fixed and covered. I'm not at 5 because the Streamlit UI has no automated tests (I only exercised it with a stand-in script), and a few design limits remain: the plan ignores start times, and sorting ignores dates.

With more time I would test: tasks that run past midnight, two pending tasks with the same title on one pet, very long task lists, changing a task after it is created (editing is not supported yet), and the UI itself using Streamlit's testing tools.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with keeping the logic separate from the UI. Because `pawpal_system.py` knows nothing about Streamlit, I could test it thoroughly, demo it from the command line with `main.py`, and then connect the UI at the end without rewriting anything. The conflict warnings also came out well: they name both tasks, both pets and the times, and they say when a warning is safe to ignore.

**b. What you would improve**

I would let the scheduler use start times when building the plan, so it could avoid or resolve conflicts instead of only reporting them. I would also add editing and deleting of tasks in the UI, save data between sessions (right now everything resets when the page is reloaded), and finally use the `preferences`, `category` and `preferred_time` fields that are stored but ignored.

**c. Key takeaway**

Working with a powerful AI tool is mostly about being the lead architect: the AI can produce working code quickly, but it does not know which tradeoffs are right for this app. My job was to set the structure (what each class owns, what the scheduler should and should not do), decide where to keep things simple, and check the results instead of assuming they were right. The bugs I found in the first working version were a good reminder that code that runs is not the same as code that is correct.

> **Your turn:** replace or add to this takeaway with the one thing you personally learned.
