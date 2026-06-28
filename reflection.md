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
