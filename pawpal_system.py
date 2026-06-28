"""PawPal+ system skeleton.

Class stubs generated from the project UML (diagrams/uml.mmd):
Owner, Pet, Activity, and Calendar. No scheduling logic yet — fill in the
method bodies as you implement the system.
"""


class Owner:
    """The person planning care. Owns pets and provides a time budget."""

    def __init__(self, name, available_minutes, preferred_times=None):
        self.name = name                                                # str
        self.available_minutes = available_minutes                      # int
        self.preferred_times = preferred_times if preferred_times is not None else []  # list[str]

    def add_pet(self, pet):
        """Register a pet under this owner."""
        # TODO: implement
        pass


class Pet:
    """An animal owned by an Owner. Holds the activities it needs."""

    def __init__(self, name, species):
        self.name = name            # str
        self.species = species      # str
        self.activities = []        # list[Activity]

    def add_activity(self, activity):
        """Attach an Activity to this pet."""
        # TODO: implement
        pass


class Activity:
    """A single pet-care activity to be scheduled."""

    def __init__(self, title, duration_minutes, priority="medium",
                 preferred_time="", category="general"):
        self.title = title                        # str
        self.duration_minutes = duration_minutes  # int
        self.priority = priority                  # str: "high" | "medium" | "low"
        self.preferred_time = preferred_time      # str
        self.category = category                  # str


class Calendar:
    """Builds and explains a daily plan from a set of activities."""

    def __init__(self):
        self.slots = []        # list[tuple]
        self.reasoning = []    # list[str]

    def build_plan(self, owner, activities):
        """Schedule activities into the owner's time budget by priority."""
        # TODO: implement
        pass

    def sort_by_priority(self, activities):
        """Return activities ordered by priority (highest first)."""
        # TODO: implement
        pass

    def fits_in_budget(self, activity, remaining):
        """Return True when the activity fits in the remaining minutes."""
        # TODO: implement
        pass

    def explain(self):
        """Return the recorded reasoning as a single readable string."""
        # TODO: implement
        pass
