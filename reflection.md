# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

My initial UML modeled PawPal+ with four classes, each with a single clear responsibility:

- **Owner** — represents the person planning care. Holds their `name`, the `available_minutes` they have in the day (the time budget), and `preferred_times`. Knows how to `add_pet()`.
- **Pet** — represents an animal being cared for. Holds its `name`, `species`, and the `activities` it needs, and can `add_activity()`.
- **Task** — a single care task (e.g. a walk or meds). Holds `title`, `duration_minutes`, `priority`, `preferred_time`, and `category`. It is plain data with no behavior of its own.
- **Calendar** — the scheduling engine. It takes an owner and a list of activities and produces a daily plan. It owns the `slots` (the scheduled items) and the `reasoning` behind them, and exposes `build_plan()`, `sort_by_priority()`, `fits_in_budget()`, and `explain()`.

The key idea was to separate *data* (Owner, Pet, Task) from the *logic that arranges that data* (Calendar), so the scheduling rules live in exactly one place.

**b. Design changes**

Yes, the design evolved during implementation:

- **Naming and responsibility split.** My very first brainstorm used the name *Scheduler* for the engine. I renamed it to **Calendar** to better fit the pet-care domain, while keeping **Task** as the name for a single care item. I also kept Task as a pure data class rather than giving it scheduling methods — that responsibility belongs to the Calendar.
- **Priority as a string instead of an enum.** I initially considered a `HIGH/MEDIUM/LOW` enum. I switched `priority` to a simple string because the Streamlit UI already collects priority as a `"low"/"medium"/"high"` string, so a string avoids a conversion layer. The ordering logic lives in the Calendar via a small priority lookup instead.
- **Overflow handling.** I decided that activities which don't fit the time budget should be *flagged* in the Calendar's `reasoning` rather than silently dropped, so the owner can see *why* something was left out. This pushed me to make `reasoning` a first-class attribute of Calendar feeding the `explain()` output.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The `Calendar` considers several constraints when building a plan:

- **Time budget** — the owner's `available_minutes`. Tasks are only scheduled while they fit the remaining budget (`fits_in_budget`).
- **Priority** — `high / medium / low`, used to decide which tasks win scarce time (`sort_by_priority`).
- **Time-of-day preference** — each task's `preferred_time` window (`morning / afternoon / evening / night`), used to lay the day out chronologically (`sort_by_time`).
- **Owner preferences** — the owner's `preferred_times`, which feed the "too many tasks stacked in a preferred window" conflict check.
- **Due date** — only tasks due on or before the planned day are considered, so future recurring occurrences don't leak into today.
- **Completion status** — already-completed tasks are filtered out so they don't consume budget.

I decided **priority within the time budget** mattered most, because the core scenario is a *busy* owner with not enough time for everything. The most important rule is "make sure the high-priority things (meds, feeding) get done first." Time-of-day ordering is a secondary, presentational concern: it makes the plan readable but never bumps an important task out in favor of a less important one.

**b. Tradeoffs**

One clear tradeoff is **greedy priority-first selection instead of optimizing the total number (or value) of tasks that fit.** The scheduler walks tasks in priority order and takes each one that fits the remaining budget. This means a single high-priority 45-minute task can crowd out two medium 20-minute tasks that, together, would have used the time more "fully."

That tradeoff is reasonable here because pet care is not about maximizing throughput — it's about not missing the things that matter. An owner would rather complete one essential vet task than two optional enrichment activities. The greedy approach is also simple, predictable, and easy to *explain* (every skip is recorded in `reasoning`), which matters more for trust than squeezing the schedule to be mathematically optimal.

A second tradeoff is using **coarse time windows rather than real clock times** for conflict detection. Because tasks are laid out back-to-back, true minute-level overlaps can't happen — so the scheduler reports *window contention* (two `medical` tasks both wanting the afternoon) instead. This is less precise but matches how the owner actually thinks about their day.

---

## 3. AI Collaboration

**a. How you used AI**

I used AI in three main ways:

- **Design brainstorming** — talking through the class breakdown and the *Scheduler → Calendar* rename, and sanity-checking whether `Task` should hold scheduling logic (it shouldn't — it stayed a pure data class).
- **Test design** — asking which scheduling behaviors were most important to test, then generating a `pytest` suite covering sorting, recurrence, and conflict detection. AI helped me see that some behaviors were only tested *indirectly* (e.g. recurrence was checked through `build_plan` but never directly asserted that the next occurrence was due *tomorrow*), so I added dedicated tests for those exact contracts.
- **Documentation** — writing the algorithm list and demo walkthrough in the README, grounded in the actual method names.

The most helpful prompts were **specific and code-grounded** — pointing the AI at the actual files and asking "what are the most important cases to test for *this* sorting/recurrence logic" produced far better answers than vague "write some tests." Asking it to explain a tradeoff also surfaced design assumptions I hadn't made explicit.

**b. Judgment and verification**

One moment I didn't accept a suggestion as-is: when discussing conflict detection, the simplest idea was "two tasks at the same time = a conflict." I rejected that because my tasks use **coarse time windows**, not clock times, and feeding + walking both in the morning isn't a real clash. I kept my design that only flags a conflict when tasks share a **window *and* category** (or overstuff a preferred window). The AI even flagged this nuance back to me — that "duplicate times alone isn't always a conflict by design" — which confirmed the decision.

I verified AI suggestions by **running them, not trusting them**: the generated tests were run with `pytest` (all 13 pass), and I checked each test's assertions against the real behavior in `pawpal_system.py` rather than assuming the AI had read the logic correctly.

---

## 4. Testing and Verification

**a. What you tested**

The suite (`tests/test_pawpal.py`, 13 tests) covers the behaviors most likely to break the plan:

- **Sorting correctness** — `sort_by_time` returns a scrambled list in strict chronological order (`morning → afternoon → evening → night`), with untimed tasks always last.
- **Recurrence logic** — completing a daily task creates a new, distinct, pending task due exactly one day later, with the same title/duration/recurrence, auto-registered on the pet; and that future occurrence is *not* scheduled today.
- **Conflict detection** — tasks sharing a window/category are flagged, even when one of them is cut for budget.
- **Budget & filtering** — completed tasks don't consume time, and `all_tasks` filters correctly by pet and status.
- **Input normalization** — invalid recurrence strings fall back to `None`.

These were important because they are the **core promises of the app**: that the most important tasks get scheduled, that recurring tasks roll forward correctly, and that the owner is warned about clashes. They're also the places where an off-by-one or a wrong sort key would silently produce a *plausible-looking but wrong* plan.

**b. Confidence**

I'm highly confident (5/5) in the implemented behaviors — all 13 tests pass, and they assert concrete contracts (exact ordering, exact due dates) rather than just "it ran without error."

If I had more time, I'd test these edge cases next:

- **Weekly recurrence date math** — currently only daily's "+1 day" is asserted directly; weekly's "+7 days" deserves the same.
- **Multi-day planning** — calling `build_plan(for_date=tomorrow)` to confirm a deferred occurrence becomes active on the right day.
- **Boundary budgets** — zero/very small `available_minutes`, and a task whose duration exactly equals the remaining budget.
- **Tie-breaking** — equal priority *and* equal duration in the same window (is the order stable/predictable?).
- **Empty and single-task plans**, and tasks with unusual `preferred_time` strings.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with the **separation of data from logic** and the **explainable reasoning**. Keeping `Owner`, `Pet`, and `Task` as plain data holders and putting *all* scheduling rules in `Calendar` meant every behavior had exactly one home — which made it easy to test and easy to document. The `reasoning`/`explain()` design also turned out to be the best decision: instead of a schedule that just appears, the app can say *why* a task was scheduled, skipped, deferred, or flagged. That makes the output trustworthy rather than magic.

**b. What you would improve**

In another iteration I'd:

- **Make `priority` and `preferred_time` real types** (an enum or validated constant set) instead of bare strings, so an invalid window can't silently sort as "untimed."
- **Generalize recurrence** beyond daily/weekly (e.g. "every N days," specific weekdays) and support genuine **multi-day planning** rather than a single day at a time.
- **Move toward real clock-time scheduling** so conflict detection could catch true overlaps, not just window contention — though I'd only do this if the UI collected start times.
- **Decouple the UI's task model from the core `Task`** — `app.py` currently maintains a parallel dict-based representation that mirrors `Task.mark_complete` by hand, which is duplicated logic that could drift.

**c. Key takeaway**

The biggest lesson was that **design clarity and AI usefulness reinforce each other**. Because the responsibilities were cleanly separated, I could point AI at one file and ask precise questions ("what are the most important cases to test for *this* sort logic"), and get precise, verifiable answers. AI was most valuable not when I asked it to "build the thing," but when I used it to **pressure-test decisions I'd already reasoned about** — and the discipline of running and checking everything it produced, rather than trusting it, is what kept the project correct.
