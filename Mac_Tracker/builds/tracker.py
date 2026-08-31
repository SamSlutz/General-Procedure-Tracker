import pandas as pd
from datetime import datetime, timedelta
import os
import sys
import json

# === CONFIG ===
def get_app_dir():
    if getattr(sys, "frozen", False):
        # Go from:
        # YourApp.app/Contents/MacOS/YourApp
        # → YourApp.app
        return os.path.abspath(
            os.path.join(os.path.dirname(sys.executable), "..", "..", "..")
        )
    else:
        return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_app_dir()
CSV_PATH = os.path.join(BASE_DIR, "people.csv")
CONFIG_PATH = os.path.join(BASE_DIR, "tracker_config.json")
DATE_FMT = "%Y-%m-%d"

# Default settings: generic labels + the original 1-per-4-then-1-per-3 schedule
DEFAULT_CONFIG = {
    "process_1_label": "Foo",
    "process_2_label": "Bar",
    "starting_ratio": 1,     # Process 2 occurrences per Process 1 during the starting phase
    "change_point": 4,       # how many Process 1 occurrences the starting ratio applies to
    "following_ratio": 3,    # Process 2 occurrences per Process 1 after the change point
}


def load_config():
    """Load saved settings from tracker_config.json, falling back to defaults."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
            cfg = DEFAULT_CONFIG.copy()
            cfg.update(data)
            return cfg
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


# Module-level config shared across the app (CLI + GUI both read this)
_config = load_config()


def get_config():
    return _config


def update_config(**kwargs):
    """Update one or more settings, persist to disk, and return the new config."""
    _config.update(kwargs)
    save_config(_config)
    return _config


# === COLORS ===
class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    GRAY = "\033[90m"


def process_1_due_at(process_1_number, starting_ratio, change_point, following_ratio):
    """
    Cumulative Process 2 count at which the Nth Process 1 (1-indexed) becomes due.

    - starting_ratio: Process 2 occurrences between Process 1s during the starting phase
    - change_point: how many Process 1 occurrences the starting ratio applies to
    - following_ratio: Process 2 occurrences between Process 1s after the change point
    """
    starting_ratio = max(1, int(starting_ratio))
    following_ratio = max(1, int(following_ratio))
    change_point = max(1, int(change_point))

    if process_1_number <= change_point:
        return (process_1_number - 1) * starting_ratio
    return (change_point - 1) * starting_ratio + (process_1_number - change_point) * following_ratio


# === PERSON CLASS ===
class Person:
    def __init__(self, **kwargs):
        # CSV headers may include spaces
        self.name = kwargs.get("Name", "")
        self.registry = int(kwargs.get("Registry", 0))
        self.registry_date = kwargs.get("Registry Date", "")
        self.process_1 = int(kwargs.get("Process 1", 0))
        self.process_1_date = kwargs.get("Process 1 Date", "")
        self.process_2 = int(kwargs.get("Process 2", 0))
        self.process_2_date = kwargs.get("Process 2 Date", "")
        self.flag = kwargs.get("Flag", "N")
        self.registration_flag = kwargs.get("Registration Flag", "N")

        self.update_flags()  # auto-check flags on creation

    # --- Safe date parsing ---
    @staticmethod
    def _parse_date(date_str):
        try:
            return datetime.strptime(date_str.strip(), "%Y-%m-%d")
        except Exception:
            return None

    # --- Update both flags ---
    def update_flags(self):
        self._update_registration_flag()
        self._update_flag()

    def _update_registration_flag(self):
        reg_date = self._parse_date(self.registry_date)
        if reg_date is None:
            self.registration_flag = "Y"
            return
        six_months_ago = datetime.now() - timedelta(days=183)
        self.registration_flag = "Y" if reg_date < six_months_ago else "N"

    def _update_flag(self):
        cfg = get_config()
        next_process_1_number = self.process_1 + 1
        threshold = process_1_due_at(
            next_process_1_number,
            cfg["starting_ratio"],
            cfg["change_point"],
            cfg["following_ratio"],
        )
        self.flag = "Y" if self.process_2 >= threshold else "N"

    # --- Add Process 1 / Process 2 / Registry methods ---
    def add_process_1(self, date_str):
        # Ensure process_1_date is a string
        if not isinstance(self.process_1_date, str):
            self.process_1_date = ""
        # Append new Process 1 date
        self.process_1_date = (self.process_1_date + f", {date_str}") if self.process_1_date else date_str
        self.process_1 += 1
        self._update_flag()

    def add_process_2(self, date_str):
        if not isinstance(self.process_2_date, str):
            self.process_2_date = ""
        self.process_2 += 1
        self.process_2_date = (self.process_2_date + f", {date_str}") if self.process_2_date.strip() else date_str
        self.update_flags()

    def add_registry(self, date_str):
        if not isinstance(self.registry_date, str):
            self.registry_date = ""
        self.registry += 1
        self.registry_date = date_str
        self.update_flags()

    # --- Convert to dict for pandas ---
    def to_dict(self):
        return {
            "Name": self.name,
            "Registry": self.registry,
            "Registry Date": self.registry_date,
            "Process 1": self.process_1,
            "Process 1 Date": self.process_1_date,
            "Process 2": self.process_2,
            "Process 2 Date": self.process_2_date,
            "Flag": self.flag,
            "Registration Flag": self.registration_flag
        }


def recompute_all_flags(df):
    """Recompute flags for every row using the current config.
    Call this after changing the ratio settings so existing people update too."""
    for idx, row in df.iterrows():
        p = Person(**row.to_dict())
        df.loc[idx, "Flag"] = p.flag
        df.loc[idx, "Registration Flag"] = p.registration_flag
    return df


# === FILE HANDLING ===
def load_data():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(
            f"people.csv not found.\n\n"
            f"Place people.csv next to the application:\n{BASE_DIR}"
        )
    if os.path.exists(CSV_PATH):
        return pd.read_csv(CSV_PATH)
    else:
        cols = ["Name", "Registry", "Registry Date", "Process 1", "Process 1 Date",
                "Process 2", "Process 2 Date", "Flag", "Registration Flag"]
        return pd.DataFrame(columns=cols)


def save_data(df):
    df.to_csv(CSV_PATH, index=False)


def find_person(df, name):
    person_row = df[df["Name"].str.lower() == name.lower()]
    return person_row.iloc[0] if not person_row.empty else None


# === UTILITIES ===
def input_date(prompt):
    """Prompt for a date, defaulting to today's date if empty."""
    today_str = datetime.today().strftime(DATE_FMT)
    date_str = input(f"{prompt} (default {today_str}): ").strip()
    return date_str if date_str else today_str


# === DISPLAY ===
def print_person_info(person):
    print("\n" + "─" * 60)
    print(f"Person: {person['Name']}")
    print("─" * 60)
    print(f"Registry:            {person['Registry']}    Date: {person['Registry Date']}")

    print("\nProcess 1 History:")
    print("---------------")
    if isinstance(person["Process 1 Date"], str) and person["Process 1 Date"].strip():
        for i, d in enumerate(person["Process 1 Date"].split(","), 1):
            print(f"  Process 1 {i}: {d.strip()}")
    else:
        print("  None")

    print("\nProcess 2 History:")
    print("-----------------")
    if isinstance(person["Process 2 Date"], str) and person["Process 2 Date"].strip():
        for i, d in enumerate(person["Process 2 Date"].split(","), 1):
            print(f"  Process 2 {i}: {d.strip()}")
    else:
        print("  None")

    # --- Colored Flags Section ---
    print("\nFlags:")
    flag = (Color.GREEN + "N" + Color.RESET) if person["Flag"] == "N" else (Color.RED + "Y" + Color.RESET)
    reg_flag = (Color.GREEN + "N" + Color.RESET) if person["Registration Flag"] == "N" else (Color.RED + "Y" + Color.RESET)
    print(f"  Flag:                {flag}")
    print(f"  Registration Flag:  {reg_flag}")
    print(f"{Color.CYAN}{'─' * 60}{Color.RESET}\n")

# === PERSON CREATION ===
def add_new_person(df, name):
    print(f"\nCreating new person record for {name}:")

    today = datetime.now().strftime("%Y-%m-%d")
    registry_date = input(f"Enter Registry Date (or 'none')(default {today}): ").strip().lower() or today

    # Initialize Process 1 / Process 2 to 0

    process_1 = 0
    process_1_date = ""
    process_2 = 0
    process_2_date = ""

    # Flags start as "N"
    flag = "N"
    registration_flag = "N"

    # Build dictionary with CSV headers as keys
    new_person_data = {
        "Name": name,
        "Registry": 0 if registry_date == 'none' else 1,
        "Registry Date": registry_date,
        "Process 1": process_1,
        "Process 1 Date": process_1_date,
        "Process 2": process_2,
        "Process 2 Date": process_2_date,
        "Flag": flag,
        "Registration Flag": registration_flag
    }

    # Create Person using kwargs
    new_person = Person(**new_person_data)

    # Append to DataFrame
    df = pd.concat([df, pd.DataFrame([new_person.to_dict()])], ignore_index=True)

    # Save CSV
    df.to_csv(CSV_PATH, index=False)
    print(f"💾 New person '{name}' added and saved to CSV.")

    return df


# === UPDATE LOOP ===
def update_person(df, person_row, csv_path):
    """Update person data (Process 1 / Process 2 / Registry) with auto-save and removal option."""

    p = Person(**person_row.to_dict())

    # Display person info before showing menu
    print_person_info(p.to_dict())

    while True:
        print("\nSelect an action:")
        print("1. Add Process 1")
        print("2. Add Process 2")
        print("3. Add Registry")
        print("4. Remove Entry")
        print("5. Return to Main Menu")
        choice = input("> ").strip()

        if choice == "5":
            break

        today = datetime.now().strftime("%Y-%m-%d")

        if choice == "1":
            date_input = input(f"Enter Process 1 Date (default {today}): ").strip() or today
            p.add_process_1(date_input)
            print(f"✅ Process 1 {p.process_1} added on {date_input}")

        elif choice == "2":
            date_input = input(f"Enter Process 2 Date (default {today}): ").strip() or today
            p.add_process_2(date_input)
            print(f"✅ Process 2 {p.process_2} added on {date_input}")

        elif choice == "3":
            date_input = input(f"Enter Registry Date (default {today}): ").strip() or today
            p.add_registry(date_input)
            print(f"✅ Registry {p.registry} added on {date_input}")

        elif choice == "4":
            print("\nWhich type do you want to remove?")
            print("1. Process 1")
            print("2. Process 2")
            print("3. Registry")
            remove_choice = input("> ").strip()

            if remove_choice == "1" and p.process_1 > 0:
                # Show Process 1 history
                process_1_dates = [d.strip() for d in p.process_1_date.split(",")]
                for i, d in enumerate(process_1_dates, 1):
                    print(f"{i}. {d}")
                rm_index = int(input("Enter Process 1 number to remove: ").strip())
                if 1 <= rm_index <= len(process_1_dates):
                    removed = process_1_dates.pop(rm_index - 1)
                    p.process_1_date = ", ".join(process_1_dates)
                    p.process_1 -= 1
                    p.update_flags()
                    print(f"✅ Removed Process 1 {rm_index}: {removed}")
                else:
                    print("❌ Invalid Process 1 number.")

            elif remove_choice == "2" and p.process_2 > 0:
                # Show Process 2 history
                process_2_dates = [d.strip() for d in p.process_2_date.split(",")]
                for i, d in enumerate(process_2_dates, 1):
                    print(f"{i}. {d}")
                rm_index = int(input("Enter Process 2 number to remove: ").strip())
                if 1 <= rm_index <= len(process_2_dates):
                    removed = process_2_dates.pop(rm_index - 1)
                    p.process_2_date = ", ".join(process_2_dates)
                    p.process_2 -= 1
                    p.update_flags()
                    print(f"✅ Removed Process 2 {rm_index}: {removed}")
                else:
                    print("❌ Invalid Process 2 number.")

            elif remove_choice == "3" and p.registry > 0:
                print(f"Current Registry: {p.registry_date}")
                confirm = input("Remove registry? (Y/N): ").strip().upper()
                if confirm == "Y":
                    p.registry -= 1
                    p.registry_date = ""
                    p.update_flags()
                    print("✅ Registry removed.")
                else:
                    print("❌ Registry not removed.")

            else:
                print("❌ Nothing to remove or invalid option.")

        else:
            print("❌ Invalid menu option. Try again.")
            continue

        # --- Update DataFrame ---
        df.loc[df["Name"] == p.name, :] = pd.DataFrame([p.to_dict()]).values

        # --- Auto-save ---
        df.to_csv(csv_path, index=False)
        print(f"💾 Changes saved to {csv_path}")

        # --- Display updated person info ---
        print_person_info(p.to_dict())

    return df

# === MAIN ===
def main():
    df = load_data()
    print(f"\n{Color.BOLD}{Color.BLUE}=== General Procedure Tracker ==={Color.RESET}\n")

    while True:
        name = input(f"{Color.CYAN}Enter person name (or press Enter to exit): {Color.RESET}").strip()
        if not name:
            print(f"{Color.GRAY}Exiting program.{Color.RESET}")
            break

        person_row = find_person(df, name)
        if person_row is not None:
            df = update_person(df, person_row, CSV_PATH)
        else:
            ans = input(f"{Color.YELLOW}'{name}' not found. Create new person? (Y/N): {Color.RESET}").strip().upper()
            if ans == "Y":
                df = add_new_person(df, name)
            else:
                continue


if __name__ == "__main__":
    main()
