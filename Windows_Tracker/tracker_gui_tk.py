import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime
import pandas as pd

from builds.tracker import load_data, save_data, find_person, Person, CSV_PATH
from builds import tracker


class TrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("General Procedure Tracker")

        self.df = load_data()
        self.current_person = None

        self.cfg = tracker.get_config()
        self.process_1_label = self.cfg["process_1_label"]
        self.process_2_label = self.cfg["process_2_label"]

        self._build_ui()

    def _build_ui(self):
        tk.Label(self.root, text="General Procedure Tracker", font=("Helvetica", 16)).pack(pady=8)

        top = tk.Frame(self.root)
        top.pack()

        tk.Label(top, text="Person Name:").pack(side=tk.LEFT)
        self.name_entry = tk.Entry(top, width=25)
        self.name_entry.pack(side=tk.LEFT, padx=5)

        # Bind Enter key to load person
        self.name_entry.bind("<Return>", lambda e: self.load_person())

        self.summary = tk.Label(self.root, text="", font=("Courier", 11), justify="left")
        self.summary.pack(pady=8)

        lists = tk.Frame(self.root)
        lists.pack(padx=10)

        # Process 1 Frame
        process_1_frame = tk.Frame(lists)
        process_1_frame.pack(side=tk.LEFT, padx=10)
        self.process_1_history_label = tk.Label(process_1_frame, text=f"{self.process_1_label} History")
        self.process_1_history_label.pack()
        self.process_1_list = tk.Listbox(process_1_frame, width=30, height=10)
        self.process_1_list.pack()
        self.remove_process_1_btn = tk.Button(process_1_frame, text=f"Remove Selected {self.process_1_label}", command=self.remove_selected_process_1)
        self.remove_process_1_btn.pack(pady=2)
        self.edit_process_1_btn = tk.Button(process_1_frame, text=f"Edit Selected {self.process_1_label} Date", command=self.edit_selected_process_1)
        self.edit_process_1_btn.pack(pady=2)

        # Process 2 Frame
        process_2_frame = tk.Frame(lists)
        process_2_frame.pack(side=tk.LEFT, padx=10)
        self.process_2_history_label = tk.Label(process_2_frame, text=f"{self.process_2_label} History")
        self.process_2_history_label.pack()
        self.process_2_list = tk.Listbox(process_2_frame, width=30, height=10)
        self.process_2_list.pack()
        self.remove_process_2_btn = tk.Button(process_2_frame, text=f"Remove Selected {self.process_2_label}", command=self.remove_selected_process_2)
        self.remove_process_2_btn.pack(pady=2)
        self.edit_process_2_btn = tk.Button(process_2_frame, text=f"Edit Selected {self.process_2_label} Date", command=self.edit_selected_process_2)
        self.edit_process_2_btn.pack(pady=2)

        self.flags_frame = tk.Frame(self.root)
        self.flags_frame.pack(pady=8)

        btns = tk.Frame(self.root)
        btns.pack(pady=5)
        self.add_process_1_btn = tk.Button(btns, text=f"Add {self.process_1_label}", width=15, command=self.add_process_1)
        self.add_process_1_btn.pack(side=tk.LEFT, padx=5)
        self.add_process_2_btn = tk.Button(btns, text=f"Add {self.process_2_label}", width=15, command=self.add_process_2)
        self.add_process_2_btn.pack(side=tk.LEFT, padx=5)
        tk.Button(btns, text="Add Registry", width=15, command=self.add_registry).pack(side=tk.LEFT, padx=5)
        tk.Button(btns, text="Clear", width=15, command=self.clear_display).pack(side=tk.LEFT, padx=5)

        self._build_settings_panel()

    def _build_settings_panel(self):
        settings = tk.LabelFrame(self.root, text="Settings", padx=8, pady=8)
        settings.pack(pady=10, padx=10, fill="x")

        row1 = tk.Frame(settings)
        row1.pack(fill="x", pady=2)
        tk.Label(row1, text="Process 1 Label:", width=16, anchor="w").pack(side=tk.LEFT)
        self.process_1_label_entry = tk.Entry(row1, width=14)
        self.process_1_label_entry.insert(0, self.process_1_label)
        self.process_1_label_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(row1, text="Process 2 Label:", width=16, anchor="w").pack(side=tk.LEFT)
        self.process_2_label_entry = tk.Entry(row1, width=14)
        self.process_2_label_entry.insert(0, self.process_2_label)
        self.process_2_label_entry.pack(side=tk.LEFT, padx=5)

        row2 = tk.Frame(settings)
        row2.pack(fill="x", pady=2)
        tk.Label(row2, text="Starting Ratio:", width=16, anchor="w").pack(side=tk.LEFT)
        self.start_ratio_entry = tk.Entry(row2, width=6)
        self.start_ratio_entry.insert(0, str(self.cfg["starting_ratio"]))
        self.start_ratio_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(row2, text="Change Point:", width=16, anchor="w").pack(side=tk.LEFT)
        self.change_point_entry = tk.Entry(row2, width=6)
        self.change_point_entry.insert(0, str(self.cfg["change_point"]))
        self.change_point_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(row2, text="Following Ratio:", width=16, anchor="w").pack(side=tk.LEFT)
        self.follow_ratio_entry = tk.Entry(row2, width=6)
        self.follow_ratio_entry.insert(0, str(self.cfg["following_ratio"]))
        self.follow_ratio_entry.pack(side=tk.LEFT, padx=5)

        tk.Button(settings, text="Apply Settings", command=self.apply_settings).pack(pady=6)

    def apply_settings(self):
        process_1_label = self.process_1_label_entry.get().strip()
        process_2_label = self.process_2_label_entry.get().strip()

        if not process_1_label or not process_2_label:
            messagebox.showerror("Invalid Labels", "Both procedure labels must be non-empty.")
            return

        try:
            starting_ratio = int(self.start_ratio_entry.get().strip())
            change_point = int(self.change_point_entry.get().strip())
            following_ratio = int(self.follow_ratio_entry.get().strip())
            if starting_ratio < 1 or change_point < 1 or following_ratio < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid Ratio Settings",
                "Starting Ratio, Change Point, and Following Ratio must all be whole numbers of 1 or more."
            )
            return

        tracker.update_config(
            process_1_label=process_1_label,
            process_2_label=process_2_label,
            starting_ratio=starting_ratio,
            change_point=change_point,
            following_ratio=following_ratio,
        )

        self.cfg = tracker.get_config()
        self.process_1_label = process_1_label
        self.process_2_label = process_2_label

        self._relabel_widgets()

        # Ratio rules changed, so every person's flag needs recomputing
        self.df = tracker.recompute_all_flags(self.df)
        save_data(self.df)

        if self.current_person:
            row = find_person(self.df, self.current_person.name)
            if row is not None:
                self.current_person = Person(**row.to_dict())
            self.refresh_display()

        messagebox.showinfo("Settings Applied", "Labels and schedule updated for everyone.")

    def _relabel_widgets(self):
        self.process_1_history_label.config(text=f"{self.process_1_label} History")
        self.process_2_history_label.config(text=f"{self.process_2_label} History")
        self.remove_process_1_btn.config(text=f"Remove Selected {self.process_1_label}")
        self.edit_process_1_btn.config(text=f"Edit Selected {self.process_1_label} Date")
        self.remove_process_2_btn.config(text=f"Remove Selected {self.process_2_label}")
        self.edit_process_2_btn.config(text=f"Edit Selected {self.process_2_label} Date")
        self.add_process_1_btn.config(text=f"Add {self.process_1_label}")
        self.add_process_2_btn.config(text=f"Add {self.process_2_label}")

    def _parse_date(self, raw):
        if not raw:
            return None

        s = raw.strip()

        # Remove common separators
        s = s.replace("/", "").replace("-", "")

        if len(s) != 8 or not s.isdigit():
            messagebox.showerror(
                "Invalid Date",
                "Date must be in YYYY-MM-DD format (e.g. 2025-06-01)."
            )
            return None

        try:
            dt = datetime.strptime(s, "%Y%m%d")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            messagebox.showerror(
                "Invalid Date",
                "The date entered is not a valid calendar date."
            )
            return None

    def _prompt_date(self, title, prompt):
        """Ask for a date, pre-filled with today's date so pressing Enter accepts it."""
        today = datetime.now().strftime("%Y-%m-%d")
        raw = simpledialog.askstring(title, prompt, initialvalue=today)
        return self._parse_date(raw)

    def clear_display(self):
        self.current_person = None

        self.name_entry.delete(0, tk.END)

        self.summary.config(text="")

        self.process_1_list.delete(0, tk.END)
        self.process_2_list.delete(0, tk.END)

        for widget in self.flags_frame.winfo_children():
            widget.destroy()

    def load_person(self):
        self.root.update()  # commit Entry value
        name = self.name_entry.get().strip()
        if not name:
            return

        row = find_person(self.df, name)

        if row is not None:
            self.current_person = Person(**row.to_dict())
        else:
            self.current_person = Person(
                Name=name,
                **{
                    "Registry": 0,
                    "Registry Date": "",
                    "Process 1": 0,
                    "Process 1 Date": "",
                    "Process 2": 0,
                    "Process 2 Date": "",
                    "Flag": "N",
                    "Registration Flag": "N"
                }
            )
            self.df = pd.concat([self.df, pd.DataFrame([self.current_person.to_dict()])], ignore_index=True)
            save_data(self.df)

        self.refresh_display()

    def refresh_display(self):
        p = self.current_person

        self.summary.config(
            text=f"Person: {p.name}\nRegistry: {p.registry}    Date: {p.registry_date}"
        )

        self.process_1_list.delete(0, tk.END)
        if isinstance(p.process_1_date, str) and p.process_1_date.strip():
            for i, d in enumerate(p.process_1_date.split(","), 1):
                self.process_1_list.insert(tk.END, f"{self.process_1_label} {i}: {d.strip()}")

        self.process_2_list.delete(0, tk.END)
        if isinstance(p.process_2_date, str) and p.process_2_date.strip():
            for i, d in enumerate(p.process_2_date.split(","), 1):
                self.process_2_list.insert(tk.END, f"{self.process_2_label} {i}: {d.strip()}")

        # Refresh flags with colors
        for widget in self.flags_frame.winfo_children():
            widget.destroy()

        flag_color = "green" if p.flag == "N" else "red"
        reg_color = "green" if p.registration_flag == "N" else "red"

        tk.Label(self.flags_frame, text=f"Flag: {p.flag}", fg=flag_color, font=("Courier", 11, "bold")).pack(anchor="w")
        tk.Label(self.flags_frame, text=f"Registration Flag: {p.registration_flag}", fg=reg_color, font=("Courier", 11, "bold")).pack(anchor="w")

    def _save_person(self):
        self.df.loc[self.df["Name"] == self.current_person.name, :] = pd.DataFrame([self.current_person.to_dict()]).values
        save_data(self.df)

    def add_process_1(self):
        if not self.current_person:
            return
        date = self._prompt_date(f"Add {self.process_1_label}", f"Enter {self.process_1_label} date (YYYY-MM-DD):")
        if not date:
            return
        self.current_person.add_process_1(date)
        self._save_person()
        self.refresh_display()

    def add_process_2(self):
        if not self.current_person:
            return
        date = self._prompt_date(f"Add {self.process_2_label}", f"Enter {self.process_2_label} date (YYYY-MM-DD):")
        if not date:
            return
        self.current_person.add_process_2(date)
        self._save_person()
        self.refresh_display()

    def add_registry(self):
        if not self.current_person:
            return

        date = self._prompt_date("Add Registry", "Enter registry date (YYYY-MM-DD):")
        if not date:
            return

        self.current_person.add_registry(date)
        self._save_person()
        self.refresh_display()

    # --- Removal ---
    def remove_selected_process_1(self):
        sel = self.process_1_list.curselection()
        if not sel:
            return
        index = sel[0]
        dates = [d.strip() for d in self.current_person.process_1_date.split(",") if d.strip()]
        if index >= len(dates):
            return
        removed = dates.pop(index)
        self.current_person.process_1_date = ", ".join(dates) if dates else ""
        self.current_person.process_1 = len(dates)
        self.current_person.update_flags()
        self._save_person()
        self.process_1_list.selection_clear(0, tk.END)
        self.refresh_display()
        self.root.after(50, lambda: messagebox.showinfo(f"Removed {self.process_1_label}", f"Removed {self.process_1_label} {index+1}: {removed}"))

    def remove_selected_process_2(self):
        sel = self.process_2_list.curselection()
        if not sel:
            return
        index = sel[0]
        dates = [d.strip() for d in self.current_person.process_2_date.split(",") if d.strip()]
        if index >= len(dates):
            return
        removed = dates.pop(index)
        self.current_person.process_2_date = ", ".join(dates) if dates else ""
        self.current_person.process_2 = len(dates)
        self.current_person.update_flags()
        self._save_person()
        self.process_2_list.selection_clear(0, tk.END)
        self.refresh_display()
        # schedule the messagebox after the GUI finishes refreshing
        self.root.after(50, lambda: messagebox.showinfo(f"Removed {self.process_2_label}", f"Removed {self.process_2_label} {index+1}: {removed}"))

    # --- Editing ---
    def edit_selected_process_1(self):
        sel = self.process_1_list.curselection()
        if not sel:
            return

        index = sel[0]
        dates = [d.strip() for d in self.current_person.process_1_date.split(",")]
        current_date = dates[index]

        raw = simpledialog.askstring(
            f"Edit {self.process_1_label} Date",
            "Enter new date (YYYY-MM-DD):",
            initialvalue=current_date
        )

        new_date = self._parse_date(raw)
        if not new_date:
            return

        dates[index] = new_date
        self.current_person.process_1_date = ", ".join(dates)
        self.current_person.update_flags()
        self._save_person()
        self.refresh_display()

    def edit_selected_process_2(self):
        sel = self.process_2_list.curselection()
        if not sel:
            return

        index = sel[0]
        dates = [d.strip() for d in self.current_person.process_2_date.split(",")]
        current_date = dates[index]

        raw = simpledialog.askstring(
            f"Edit {self.process_2_label} Date",
            "Enter new date (YYYY-MM-DD):",
            initialvalue=current_date
        )

        new_date = self._parse_date(raw)
        if not new_date:
            return

        dates[index] = new_date
        self.current_person.process_2_date = ", ".join(dates)
        self.current_person.update_flags()
        self._save_person()
        self.refresh_display()


if __name__ == "__main__":
    root = tk.Tk()
    TrackerGUI(root)
    root.mainloop()
