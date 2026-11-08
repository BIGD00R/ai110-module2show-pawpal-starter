# PawPal+

PawPal+ is a Streamlit app that helps a busy pet owner stay consistent with pet care. You enter your pets and their care tasks (walks, feeding, medication, grooming), and PawPal+ sorts them by time, warns you about overlaps, repeats daily and weekly tasks, and builds a plan for the day that fits the time you have.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority)
- Produce a daily plan and explain why it chose that plan

## ✨ Features

- **Owners, pets and tasks.** One owner with any number of pets. Each task has a duration, priority (low, medium, high), an optional start time, and a repeat setting (once, daily, weekly).
- **Sorting by time.** Task lists are shown in clock order, with unscheduled tasks last (`Scheduler.sort_by_time()`).
- **Filtering.** View tasks for one pet, only pending or completed tasks, or both together (`Owner.filter_tasks()`).
- **Conflict warnings.** Overlapping tasks are flagged in plain language, for the same pet or for different pets, without blocking anything (`Scheduler.find_conflicts()`).
- **Daily and weekly recurrence.** Completing a repeating task automatically creates the next one (`Task.mark_complete()`, `Pet.complete_task()`).
- **Priority-based daily plan.** Picks the most important tasks that fit the owner's available minutes, lists what was left out and why, and explains its choices (`Scheduler.generate_daily_plan()`, `Scheduler.explain_plan()`).
- **Input checks.** Invalid times and repeat settings are rejected, and duplicate pet names or duplicate pending task titles for one pet are refused in the UI.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run

```bash
streamlit run app.py   # the web app
python main.py         # a command-line demo of the scheduling logic
python -m pytest       # the test suite
```

### Project layout

| Path | Purpose |
|------|---------|
| `pawpal_system.py` | Logic layer: `Task`, `Pet`, `Owner`, `Scheduler` |
| `app.py` | Streamlit UI that calls the logic layer |
| `main.py` | CLI demo that prints sorting, filtering, recurrence and conflicts |
| `tests/test_pawpal.py` | pytest suite |
| `diagrams/uml_final.mmd` | Final class diagram (Mermaid source); `uml_final.png` is a rendered copy |
| `diagrams/uml_draft.mmd` | The original draft diagram, for comparison |
| `reflection.md` | Project reflection |

![PawPal+ class diagram](diagrams/uml_final.png)

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()` | Orders by `start_time` ("HH:MM"), compared as minutes since midnight. Tasks with no start time go last; ties are broken by priority (high first). Returns a new list. |
| Filtering | `Owner.filter_tasks(pet_name, completed)` | Filter by pet name (case-insensitive), completion status, or both. Leave a filter as `None` to skip it. |
| Daily plan | `Scheduler.generate_daily_plan(on_date)` | Skips completed tasks and tasks due after `on_date` (default today), then picks tasks by priority (high first), then shortest first, until the owner's available minutes run out. Skipped tasks are recorded with a reason. |
| Conflict handling | `Scheduler.find_conflicts()` | Flags any two pending, timed tasks on the same date whose time ranges overlap (same pet or different pets). A task with no due date counts as due today. Tasks that only touch (one ends as the next starts) are fine. Returns warning strings and never raises, and it does not move or remove tasks. |
| Recurring tasks | `Task.mark_complete()`, `Pet.complete_task()` | Tasks have `frequency` ("once", "daily", "weekly") and an optional `due_date`. Completing a daily or weekly task creates a copy due +1 or +7 days after the later of its due date and today (via `timedelta`), so a late task never recurs in the past. `Pet.complete_task()` attaches the copy to the same pet, and completing an already-completed task does nothing. |

Supporting helpers: `parse_time()` and `format_time()` convert between "HH:MM" and minutes; `Task.start_minutes()` and `Task.end_minutes()` expose a task's time range. Invalid times or frequencies raise `ValueError` when a task is created.

**Known limitations:** the plan is chosen by priority and available time, and it does not use start times, so a plan can contain two tasks that conflict. Use `find_conflicts()` to see them. `sort_by_time()` also ignores due dates, so it is meant for one day's tasks at a time. The owner's `preferences`, and each task's `category` and `preferred_time`, are stored but not used by the scheduler yet.

## 🧪 Testing PawPal+

```bash
python -m pytest

# With coverage (requires pytest-cov):
python -m pytest --cov
```

Output of a successful run:

```
============================= test session starts ==============================
platform linux -- Python 3.13.18, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/claude/pawpal
plugins: platformdirs-4.13.5, anyio-4.15.1
collected 44 items

tests/test_pawpal.py ............................................        [100%]

============================== 44 passed in 0.05s ==============================
```

**What the tests cover** (`tests/test_pawpal.py`):

- **Sorting:** chronological order, numeric (not text) comparison, unscheduled tasks last, priority tie-breaks, empty list, and the input list left unchanged.
- **Filtering:** by pet (case-insensitive), by status, by both, and with no filters or no matches.
- **Recurring tasks:** a daily task creates a task for the next day, weekly adds seven days, month and year rollover, details are carried over, one-time tasks don't recur, completing twice creates no duplicate, and an overdue task rolls forward from today instead of landing in the past.
- **Conflict detection:** overlapping tasks, identical start times, same-pet vs. different-pet labels, one long task overlapping several, and no false alarms for back-to-back, unscheduled, completed, or other-day tasks. A task with no due date counts as today.
- **Daily plan:** priority order, skipping what doesn't fit, exact fit, zero available minutes, ties, completed tasks, and future-dated tasks left out.
- **Validation:** bad times ("25:00", "8") and bad frequencies raise `ValueError`.

Date-dependent tests pass a fixed `today` so they don't break as the calendar moves. The Streamlit UI itself has no automated tests.

**Confidence level: ⭐⭐⭐⭐ (4 of 5).** The scheduling logic (sorting, filtering, recurrence, conflicts, planning) is well covered, including the edge cases above, and all 44 tests pass. I stopped short of 5 stars because the UI is untested, the plan chooses tasks without looking at start times (so it can include conflicting tasks), and the sort ignores due dates.

## 📸 Demo Walkthrough

### What the app lets you do

The page runs top to bottom in these sections:

1. **Owner:** set your name and how many minutes you have today.
2. **Pets:** add a pet (name, species, age). A table lists your pets and how many tasks each has. Duplicate names are refused.
3. **Add a task:** choose a pet, then set a title, duration, priority, an optional start time, and whether it repeats (once, daily, weekly). A pet can't have two pending tasks with the same title.
4. **Your tasks:** a table sorted by start time (unscheduled tasks last). Two dropdowns filter by pet and by status (all, pending, completed).
5. **Time conflicts:** a yellow warning box lists every overlap in plain language, naming both tasks, both pets and the clock times, with a hint on how to fix it (or that it's safe to ignore if the tasks can happen together). A green "No time conflicts" message shows when everything fits.
6. **Mark a task complete:** pick a pending task and mark it done. If it repeats, a message tells you when the next one is due, and the new task appears in the table.
7. **Today's schedule:** "Generate schedule" shows the chosen tasks in time order with a summary of the minutes used, any conflicts in the plan, a warning listing tasks that were left out and why, and a "Why this plan?" explanation.

### Example workflow

1. Set "Time available today" to 90 minutes.
2. Add a pet named Mochi (dog) and another named Luna (cat).
3. Add "Morning walk" for Mochi (30 min, high, 08:00, daily) and "Feeding" for Luna (10 min, high, 08:15).
4. The conflict box appears right away: the walk (08:00-08:30) overlaps the feeding (08:15-08:25). Change one start time to clear it.
5. Add "Brush fur" for Luna (20 min, low, no start time). It appears last in the task table.
6. Use the pet filter to show only Luna's tasks.
7. Mark "Morning walk" complete. Because it repeats daily, a new "Morning walk" due tomorrow is created.
8. Click "Generate schedule" to see today's plan and the explanation.

### Scheduler behaviors shown

- **Sorting:** the task table and the plan are always shown in clock order.
- **Filtering:** by pet and by status, combined.
- **Conflict warnings:** shown under the task table and again under the plan.
- **Recurrence:** completing a daily or weekly task adds the next occurrence, which stays out of today's plan until it is due.
- **Planning:** high-priority tasks are chosen first, and tasks that don't fit are reported with a reason.

### Sample CLI output

Output of `python main.py` (run on 2026-11-08). The tasks are added out of order on purpose, and Medication and Evening walk are both set to 18:00.

```
== All tasks, sorted by time ==
  08:00  Morning walk     Mochi   30 min  pending
  08:15  Feeding          Luna    10 min  pending
  09:00  Grooming         Mochi   45 min  pending
  18:00  Medication       Luna    10 min  pending
  18:00  Evening walk     Mochi   30 min  pending
  --:--  Brush fur        Luna    20 min  pending

== Mochi's tasks ==
  18:00  Evening walk     Mochi   30 min  pending
  08:00  Morning walk     Mochi   30 min  pending
  09:00  Grooming         Mochi   45 min  pending

== Luna's pending tasks ==
  08:15  Feeding          Luna    10 min  pending
  --:--  Brush fur        Luna    20 min  pending
  18:00  Medication       Luna    10 min  pending

== Conflict check ==
  Conflict (different pets): 'Morning walk' for Mochi (08:00-08:30) overlaps 'Feeding' for Luna (08:15-08:25)
  Conflict (different pets): 'Medication' for Luna (18:00-18:10) overlaps 'Evening walk' for Mochi (18:00-18:30)

== Completing 'Morning walk' (daily, so it should come back tomorrow) ==
  Next occurrence: Morning walk due 2026-11-09

== Completed tasks ==
  08:00  Morning walk     Mochi   30 min  done

== Today's plan ==
Planned 4 task(s) using 70 of 90 available minutes.
Tasks are ordered by priority (high first), then shortest first, so the most important care happens before time runs out.
- Included: Feeding for Luna at 08:15 (high priority).
- Included: Medication for Luna at 18:00 (high priority).
- Included: Evening walk for Mochi at 18:00 (medium priority).
- Included: Brush fur for Luna (low priority).
- Skipped: Grooming for Mochi (needs 45 min but only 20 min left).
```

Optional: add screenshots of the running app here for human reviewers.
