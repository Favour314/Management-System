import customtkinter as ctk
from tkinter import messagebox, ttk
import tkinter as tk
from datetime import datetime
import database as db
import reports_gen as rg
import os, subprocess, sys

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

NAVY  = "#1a2e4a"
GOLD  = "#c9a84c"
WHITE = "#ffffff"
LIGHT = "#f5f0e8"
GREY  = "#666666"
RED   = "#c0392b"
GREEN = "#1e7e34"
MID   = "#d0c9b8"


def open_pdf(path):
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])
    except Exception as e:
        messagebox.showinfo("PDF Saved", f"Report saved to:\n{path}")


def fmt(n):
    try:
        return f"{int(round(float(n))):,}"
    except:
        return str(n)


def label(parent, text, size=11, bold=False, color=NAVY, **kwargs):
    font = ("Helvetica", size, "bold" if bold else "normal")
    kwargs.pop("text_color", None)
    kwargs.pop("fg_color", None)
    return ctk.CTkLabel(parent, text=text, font=font, text_color=color, **kwargs)


def labeled_header(parent, text, size=11, bold=True):
    return ctk.CTkLabel(parent, text=text,
                        font=("Helvetica", size, "bold" if bold else "normal"),
                        text_color=WHITE, fg_color=NAVY, corner_radius=6)


def entry(parent, placeholder="", width=200, **kwargs):
    return ctk.CTkEntry(parent, placeholder_text=placeholder,
                        width=width, corner_radius=6,
                        border_color=MID, fg_color=WHITE, **kwargs)


def btn(parent, text, command, color=NAVY, text_color=WHITE, width=130, **kwargs):
    return ctk.CTkButton(parent, text=text, command=command,
                         fg_color=color, hover_color=GOLD,
                         text_color=text_color, corner_radius=8,
                         font=("Helvetica", 10, "bold"), width=width, **kwargs)


class StudentsTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=LIGHT)
        self._build()
        self.refresh_table()

    def _build(self):
        left = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=12,
                            border_width=1, border_color=MID, width=300)
        left.pack(side="left", fill="y", padx=(10,5), pady=10)
        left.pack_propagate(False)

        label(left, "Add / Edit Student", size=13, bold=True).pack(pady=(12,4))
        ctk.CTkFrame(left, height=2, fg_color=GOLD).pack(fill="x", padx=10, pady=(0,10))

        form = ctk.CTkFrame(left, fg_color="transparent")
        form.pack(fill="x", padx=14)

        # Auto-generated Student ID (read-only)
        label(form, "Student ID (auto-generated)", size=10, color=GREY).pack(anchor="w", pady=(6,1))
        id_row = ctk.CTkFrame(form, fg_color="transparent")
        id_row.pack(fill="x")
        self.e_id = ctk.CTkEntry(id_row, width=190, corner_radius=6,
                                  border_color=GOLD, fg_color=LIGHT,
                                  text_color=NAVY, font=("Helvetica", 10, "bold"),
                                  state="readonly")
        self.e_id.pack(side="left", padx=(0,6))
        btn(id_row, "↻ New ID", self._refresh_id, color=GOLD, text_color=NAVY, width=60).pack(side="left")
        self._refresh_id()

        self.e_name    = entry(form, "e.g. Jane Doe", width=260)
        self.e_dob     = entry(form, "YYYY-MM-DD (optional)", width=260)
        self.e_teacher = entry(form, "Class teacher", width=260)

        for lbl_text, widget in [("Full Name *", self.e_name),
                                  ("Date of Birth", self.e_dob), ("Teacher Name", self.e_teacher)]:
            label(form, lbl_text, size=10, color=GREY).pack(anchor="w", pady=(6,1))
            widget.pack(fill="x")

        label(form, "Class *", size=10, color=GREY).pack(anchor="w", pady=(6,1))
        self.v_class = ctk.StringVar(value=db.CLASSES[0])
        self.dd_class = ctk.CTkOptionMenu(form, variable=self.v_class,
                                          values=db.CLASSES, width=260,
                                          fg_color=WHITE, button_color=NAVY,
                                          text_color=NAVY, corner_radius=6)
        self.dd_class.pack(fill="x")

        self.v_new = ctk.BooleanVar(value=False)
        new_row = ctk.CTkFrame(form, fg_color="transparent")
        new_row.pack(fill="x", pady=(8,0))
        ctk.CTkCheckBox(new_row, text="New student (joining mid-year)",
                        variable=self.v_new, command=self._toggle_new,
                        text_color=NAVY, fg_color=NAVY,
                        font=("Helvetica", 10)).pack(side="left")

        self.join_frame = ctk.CTkFrame(form, fg_color="transparent")
        label(self.join_frame, "Joining Term *", size=10, color=GREY).pack(anchor="w", pady=(4,1))
        self.v_join_term = ctk.StringVar(value="Term II")
        self.dd_join = ctk.CTkOptionMenu(self.join_frame, variable=self.v_join_term,
                                         values=["Term II", "Term III"], width=260,
                                         fg_color=WHITE, button_color=NAVY,
                                         text_color=NAVY, corner_radius=6)
        self.dd_join.pack(fill="x")

        btn_frame = ctk.CTkFrame(left, fg_color="transparent")
        btn_frame.pack(pady=14, padx=14, fill="x")
        btn(btn_frame, "Add Student", self.add_student, width=260).pack(fill="x", pady=(0,6))
        btn(btn_frame, "Update Student", self.update_student, color="#1e7e34", width=260).pack(fill="x", pady=(0,6))
        btn(btn_frame, "Delete Student", self.delete_student, color=RED, width=260).pack(fill="x")

        self.status_lbl = label(left, "", size=9, color=GREEN)
        self.status_lbl.pack(pady=(4,0))

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True, padx=(5,10), pady=10)

        top_bar = ctk.CTkFrame(right, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0,6))
        label(top_bar, "Student Register", size=13, bold=True).pack(side="left")

        self.e_search = entry(top_bar, "Search name or ID...", width=200)
        self.e_search.pack(side="right")
        self.e_search.bind("<KeyRelease>", lambda e: self.refresh_table())

        self.v_filter = ctk.StringVar(value="All Classes")
        ctk.CTkOptionMenu(top_bar, variable=self.v_filter,
                          values=["All Classes"] + db.CLASSES,
                          command=lambda _: self.refresh_table(),
                          fg_color=WHITE, button_color=NAVY,
                          text_color=NAVY, corner_radius=6, width=150).pack(side="right", padx=(0,8))

        tree_frame = ctk.CTkFrame(right, fg_color=WHITE, corner_radius=10,
                                  border_width=1, border_color=MID)
        tree_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Elroi.Treeview", background=WHITE, fieldbackground=WHITE,
                        rowheight=26, font=("Helvetica", 10))
        style.configure("Elroi.Treeview.Heading", background=NAVY, foreground=WHITE,
                        font=("Helvetica", 10, "bold"), relief="flat")
        style.map("Elroi.Treeview", background=[("selected", GOLD)], foreground=[("selected", NAVY)])

        cols = ("id", "name", "class", "dob", "teacher")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", style="Elroi.Treeview")
        for c, h, w in [("id","Student ID",90),("name","Full Name",200),("class","Class",90),
                         ("dob","Date of Birth",100),("teacher","Teacher",150)]:
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="center" if c != "name" else "w")

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        sb.pack(side="right", fill="y", pady=4)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.count_lbl = label(right, "", size=9, color=GREY)
        self.count_lbl.pack(anchor="e", pady=(4,0))

        t_frame = ctk.CTkFrame(right, fg_color=WHITE, corner_radius=10,
                               border_width=1, border_color=MID)
        t_frame.pack(fill="x", pady=(8,0))
        labeled_header(t_frame, "  Update Class Teacher", size=11).pack(fill="x")

        row2 = ctk.CTkFrame(t_frame, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=8)
        self.v_tclass = ctk.StringVar(value=db.CLASSES[0])
        ctk.CTkOptionMenu(row2, variable=self.v_tclass, values=db.CLASSES,
                          fg_color=WHITE, button_color=NAVY, text_color=NAVY,
                          corner_radius=6, width=130).pack(side="left", padx=(0,8))
        self.e_tname = entry(row2, "New teacher name", width=200)
        self.e_tname.pack(side="left", padx=(0,8))
        btn(row2, "Update", self.update_teacher, width=100).pack(side="left")

    def _toggle_new(self):
        if self.v_new.get():
            self.join_frame.pack(fill="x")
        else:
            self.join_frame.pack_forget()

    def _refresh_id(self):
        """Generate and display the next available student ID."""
        new_id = db.generate_student_id()
        self.e_id.configure(state="normal")
        self.e_id.delete(0, "end")
        self.e_id.insert(0, new_id)
        self.e_id.configure(state="readonly")

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        search = self.e_search.get().lower().strip()
        cls_filter = self.v_filter.get()
        all_students = db.get_all_students()
        shown = 0
        for s in all_students:
            if cls_filter != "All Classes" and s["class"] != cls_filter:
                continue
            if search and search not in s["name"].lower() and search not in s["student_id"].lower():
                continue
            tag = "odd" if shown % 2 else "even"
            self.tree.insert("", "end", iid=s["student_id"], values=(
                s["student_id"], s["name"], s["class"],
                s["dob"] or "—", s["teacher"] or "—"), tags=(tag,))
            shown += 1
        self.tree.tag_configure("even", background=WHITE)
        self.tree.tag_configure("odd", background=LIGHT)
        self.count_lbl.configure(text=f"Showing {shown} of {len(all_students)} students")

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        s = db.get_student(sel[0])
        if not s:
            return
        # Show selected student's ID in the field (readonly)
        self.e_id.configure(state="normal")
        self.e_id.delete(0, "end")
        self.e_id.insert(0, s["student_id"])
        self.e_id.configure(state="readonly")
        for e, val in [(self.e_name, s["name"]),
                       (self.e_dob, s["dob"] or ""), (self.e_teacher, s["teacher"] or "")]:
            e.delete(0, "end")
            e.insert(0, val)
        self.v_class.set(s["class"])

    def _get_form(self):
        return (self.e_id.get().strip(), self.e_name.get().strip(),
                self.v_class.get(), self.e_dob.get().strip(), self.e_teacher.get().strip())

    def add_student(self):
        sid, name, cls, dob, teacher = self._get_form()
        if not sid or not name:
            messagebox.showwarning("Missing", "Student name is required.")
            return
        is_new = self.v_new.get()
        join_term = self.v_join_term.get() if is_new else "Term I"
        ok, msg = db.add_student(sid, name, cls, dob, teacher, is_new, join_term)
        self.status_lbl.configure(text=msg, text_color=GREEN if ok else RED)
        if ok:
            # Clear form and generate next ID ready for next student
            self.e_name.delete(0, "end")
            self.e_dob.delete(0, "end")
            self.e_teacher.delete(0, "end")
            self._refresh_id()
            self.refresh_table()

    def update_student(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a student to update.")
            return
        sid, name, cls, dob, teacher = self._get_form()
        db.update_student(sel[0], name, cls, dob, teacher)
        self.status_lbl.configure(text="Student updated.", text_color=GREEN)
        self.refresh_table()

    def delete_student(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a student to delete.")
            return
        if messagebox.askyesno("Confirm", f"Delete student {sel[0]}? This cannot be undone."):
            db.delete_student(sel[0])
            self.status_lbl.configure(text="Student deleted.", text_color=RED)
            self.refresh_table()

    def update_teacher(self):
        cls = self.v_tclass.get()
        name = self.e_tname.get().strip()
        if not name:
            messagebox.showwarning("Missing", "Enter a teacher name.")
            return
        db.update_teacher(cls, name)
        self.e_tname.delete(0, "end")
        self.status_lbl.configure(text=f"Teacher updated for {cls}.", text_color=GREEN)
        self.refresh_table()


class PaymentsTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=LIGHT)
        self._selected_student = None
        self._build()

    def _build(self):
        # ── Top: student search bar ──────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=10,
                           border_width=1, border_color=MID)
        top.pack(fill="x", padx=10, pady=(10,5))
        labeled_header(top, "  Find Student", size=12).pack(fill="x")

        search_row = ctk.CTkFrame(top, fg_color="transparent")
        search_row.pack(fill="x", padx=10, pady=8)
        label(search_row, "Search:", size=10).pack(side="left", padx=(0,6))
        self.e_search = entry(search_row, "Name or Student ID...", width=240)
        self.e_search.pack(side="left", padx=(0,8))
        self.e_search.bind("<KeyRelease>", self._search_students)

        self.v_student = ctk.StringVar()
        self.dd_student = ctk.CTkOptionMenu(search_row, variable=self.v_student,
                                            values=["—"], command=self._load_student,
                                            fg_color=WHITE, button_color=NAVY,
                                            text_color=NAVY, corner_radius=6, width=300)
        self.dd_student.pack(side="left")
        self.info_lbl = label(top, "", size=10, color=GREY)
        self.info_lbl.pack(pady=(0,6))

        # ── Main body: left=fee summary, right=record payment ────────────────
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=10, pady=5)

        # LEFT — fee summary + grand total
        left = ctk.CTkFrame(main, fg_color=WHITE, corner_radius=10,
                            border_width=1, border_color=MID)
        left.pack(side="left", fill="both", expand=True, padx=(0,5))

        labeled_header(left, "  Fee Summary", size=12).pack(fill="x")

        self.fee_scroll = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self.fee_scroll.pack(fill="both", expand=True, padx=6, pady=(4,0))

        # Grand total bar pinned at bottom of left panel
        self.grand_frame = ctk.CTkFrame(left, fg_color=NAVY, corner_radius=0, height=36)
        self.grand_frame.pack(fill="x", pady=(4,0))
        self.grand_frame.pack_propagate(False)
        self.grand_lbl = ctk.CTkLabel(self.grand_frame, text="",
                                      font=("Helvetica", 11, "bold"), text_color=GOLD)
        self.grand_lbl.pack(side="left", padx=12, pady=6)
        self.grand_bal_lbl = ctk.CTkLabel(self.grand_frame, text="",
                                          font=("Helvetica", 11, "bold"), text_color=WHITE)
        self.grand_bal_lbl.pack(side="right", padx=12, pady=6)

        # RIGHT — record payment + exam fee
        right = ctk.CTkFrame(main, fg_color=WHITE, corner_radius=10,
                             border_width=1, border_color=MID, width=300)
        right.pack(side="left", fill="y", padx=(5,0))
        right.pack_propagate(False)

        right_scroll = ctk.CTkScrollableFrame(right, fg_color="transparent")
        right_scroll.pack(fill="both", expand=True)

        # — Record Payment section —
        labeled_header(right_scroll, "  Record Payment", size=12).pack(fill="x")
        form = ctk.CTkFrame(right_scroll, fg_color="transparent")
        form.pack(fill="x", padx=10, pady=8)

        label(form, "Term", size=10, color=GREY).pack(anchor="w", pady=(0,2))
        self.v_term = ctk.StringVar(value=db.TERMS[0])
        self.dd_term = ctk.CTkOptionMenu(form, variable=self.v_term, values=db.TERMS,
                                         command=self._update_categories,
                                         fg_color=WHITE, button_color=NAVY,
                                         text_color=NAVY, corner_radius=6, width=260)
        self.dd_term.pack(fill="x", pady=(0,6))

        label(form, "Fee Category", size=10, color=GREY).pack(anchor="w", pady=(0,2))
        self.v_cat = ctk.StringVar()
        self.dd_cat = ctk.CTkOptionMenu(form, variable=self.v_cat, values=["—"],
                                        command=self._on_cat_change,
                                        fg_color=WHITE, button_color=NAVY,
                                        text_color=NAVY, corner_radius=6, width=260)
        self.dd_cat.pack(fill="x", pady=(0,2))

        # Mini balance indicator for selected category
        self.cat_bal_lbl = label(form, "", size=9, color=GREY)
        self.cat_bal_lbl.pack(anchor="w", pady=(0,6))

        label(form, "Amount Paid (Ksh)", size=10, color=GREY).pack(anchor="w", pady=(0,2))
        self.e_amount = entry(form, "e.g. 2,500", width=260)
        self.e_amount.pack(fill="x", pady=(0,6))

        label(form, "Date of Payment", size=10, color=GREY).pack(anchor="w", pady=(0,2))
        date_row = ctk.CTkFrame(form, fg_color="transparent")
        date_row.pack(fill="x", pady=(0,6))
        self.e_date = entry(date_row, "YYYY-MM-DD", width=180)
        self.e_date.pack(side="left", padx=(0,6))
        self.e_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        btn(date_row, "Today", self._set_today, color=MID, text_color=NAVY, width=60).pack(side="left")

        label(form, "Notes (optional)", size=10, color=GREY).pack(anchor="w", pady=(0,2))
        self.e_notes = entry(form, "e.g. Cash payment", width=260)
        self.e_notes.pack(fill="x", pady=(0,10))

        btn(form, "✔  Record Payment", self._record_payment, color=GREEN, width=260).pack(fill="x")
        self.pay_status = label(right_scroll, "", size=9, color=GREEN)
        self.pay_status.pack(pady=(4,0), padx=10)

        # — Exam Fees section —
        ctk.CTkFrame(right_scroll, height=2, fg_color=GOLD).pack(fill="x", padx=10, pady=(12,0))
        labeled_header(right_scroll, "  Add Exam Fee", size=12).pack(fill="x", pady=(4,0))
        label(right_scroll,
              "Add a named exam fee for this student\nfor a specific term.",
              size=9, color=GREY).pack(anchor="w", padx=10, pady=(4,0))

        exam_form = ctk.CTkFrame(right_scroll, fg_color="transparent")
        exam_form.pack(fill="x", padx=10, pady=6)

        label(exam_form, "Exam Name", size=10, color=GREY).pack(anchor="w", pady=(0,2))
        self.e_exam_name = entry(exam_form, "e.g. Mid-term Exam", width=260)
        self.e_exam_name.pack(fill="x", pady=(0,6))

        label(exam_form, "Term", size=10, color=GREY).pack(anchor="w", pady=(0,2))
        self.v_exam_term = ctk.StringVar(value=db.TERMS[0])
        ctk.CTkOptionMenu(exam_form, variable=self.v_exam_term, values=db.TERMS,
                          fg_color=WHITE, button_color=NAVY,
                          text_color=NAVY, corner_radius=6, width=260).pack(fill="x", pady=(0,6))

        label(exam_form, "Amount (Ksh)", size=10, color=GREY).pack(anchor="w", pady=(0,2))
        self.e_exam_amt = entry(exam_form, "e.g. 500", width=260)
        self.e_exam_amt.pack(fill="x", pady=(0,10))

        btn(exam_form, "+ Add Exam Fee", self._add_exam_fee, color=NAVY, width=260).pack(fill="x")
        self.exam_status = label(right_scroll, "", size=9, color=GREEN)
        self.exam_status.pack(pady=(4,0), padx=10)

        # PDF button
        ctk.CTkFrame(right_scroll, height=2, fg_color=MID).pack(fill="x", padx=10, pady=(12,6))
        btn(right_scroll, "📄 Payment Report (PDF)", self._gen_payment_pdf,
            color=GOLD, text_color=NAVY, width=260).pack(padx=10, pady=(0,12))

    # ── helpers ──────────────────────────────────────────────────────────────

    def _set_today(self):
        self.e_date.delete(0, "end")
        self.e_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

    def _search_students(self, event=None):
        q = self.e_search.get().lower().strip()
        all_s = db.get_all_students()
        matches = [s for s in all_s
                   if q in s["name"].lower() or q in s["student_id"].lower()] if q else all_s
        options = [f"{s['student_id']} — {s['name']}" for s in matches[:20]]
        self.dd_student.configure(values=options or ["No match"])
        if options:
            self.v_student.set(options[0])
            self._load_student(options[0])

    def _load_student(self, val):
        if "—" not in val:
            return
        sid = val.split("—")[0].strip()
        self._selected_student = db.get_student(sid)
        if not self._selected_student:
            return
        s = self._selected_student
        self.info_lbl.configure(
            text=f"Class: {s['class']}   |   Teacher: {s['teacher'] or '—'}   |   ID: {s['student_id']}")
        self._update_categories()
        self._refresh_fee_summary()

    def _update_categories(self, *args):
        if not self._selected_student:
            return
        fees = db.get_student_fees(self._selected_student["student_id"], self.v_term.get())
        cats = [f["category"] for f in fees if f["total_owed"] - f["total_paid"] > 0]
        # Also include fully paid ones so user can see history
        all_cats = [f["category"] for f in fees]
        display = cats if cats else all_cats
        self.dd_cat.configure(values=display if display else ["—"])
        if display:
            self.v_cat.set(display[0])
            self._on_cat_change(display[0])

    def _on_cat_change(self, cat):
        if not self._selected_student or not cat or cat == "—":
            self.cat_bal_lbl.configure(text="")
            return
        fees = db.get_student_fees(self._selected_student["student_id"], self.v_term.get())
        for f in fees:
            if f["category"] == cat:
                bal = f["total_owed"] - f["total_paid"]
                color = GREEN if bal <= 0 else RED
                self.cat_bal_lbl.configure(
                    text=f"Owed: Ksh {fmt(f['total_owed'])}   Paid: Ksh {fmt(f['total_paid'])}   Balance: Ksh {fmt(bal)}",
                    text_color=color)
                return

    def _refresh_fee_summary(self):
        for w in self.fee_scroll.winfo_children():
            w.destroy()
        if not self._selected_student:
            self.grand_lbl.configure(text="")
            self.grand_bal_lbl.configure(text="")
            return

        fees = db.get_student_fees(self._selected_student["student_id"])
        by_term = {}
        for f in fees:
            by_term.setdefault(f["term"], []).append(f)

        for term in db.TERMS:
            rows = by_term.get(term)
            if not rows:
                continue

            tf = ctk.CTkFrame(self.fee_scroll, fg_color=LIGHT, corner_radius=8,
                              border_width=1, border_color=MID)
            tf.pack(fill="x", pady=(0,8))
            labeled_header(tf, f"  {term}", size=10).pack(fill="x")

            # Column headers
            hdr = ctk.CTkFrame(tf, fg_color=MID)
            hdr.pack(fill="x", padx=4, pady=(4,0))
            for txt, w in [("Category", 140), ("Owed", 65), ("Paid", 65), ("Balance", 65), ("Payments", 70)]:
                label(hdr, txt, size=9, bold=True, color=NAVY, width=w, anchor="center").pack(side="left")

            for r in rows:
                bal = r["total_owed"] - r["total_paid"]
                bg = WHITE if rows.index(r) % 2 == 0 else LIGHT

                row_f = ctk.CTkFrame(tf, fg_color=bg)
                row_f.pack(fill="x", padx=4)

                # Truncate long category names
                cat_display = r["category"] if len(r["category"]) <= 18 else r["category"][:16] + "…"
                label(row_f, cat_display, size=9, width=140, anchor="w").pack(side="left", padx=(2,0))
                label(row_f, fmt(r["total_owed"]), size=9, width=65, anchor="center").pack(side="left")
                label(row_f, fmt(r["total_paid"]), size=9, width=65, anchor="center").pack(side="left")
                label(row_f, fmt(bal), size=9, width=65,
                      color=GREEN if bal <= 0 else RED, anchor="center").pack(side="left")

                # Expandable payment history per row
                hist = db.get_payment_history(
                    self._selected_student["student_id"], term=term, category=r["category"])
                hist_btn_text = f"▼ {len(hist)}" if hist else "—"
                hist_btn = ctk.CTkButton(row_f, text=hist_btn_text, width=60,
                                         fg_color="transparent", hover_color=MID,
                                         text_color=NAVY, font=("Helvetica", 9),
                                         corner_radius=4)
                hist_btn.pack(side="left", padx=4, pady=1)

                # History detail frame (hidden by default)
                detail_frame = ctk.CTkFrame(tf, fg_color="#eef2f7", corner_radius=0)

                def _make_toggle(btn=hist_btn, df=detail_frame,
                                 h=hist, sid=self._selected_student["student_id"],
                                 t=term, c=r["category"]):
                    shown = [False]
                    def toggle():
                        if not h:
                            return
                        if shown[0]:
                            df.pack_forget()
                            btn.configure(text=f"▼ {len(h)}")
                            shown[0] = False
                        else:
                            # Build history rows
                            for child in df.winfo_children():
                                child.destroy()
                            for p in h:
                                pr = ctk.CTkFrame(df, fg_color="transparent")
                                pr.pack(fill="x", padx=20, pady=1)
                                d = p["paid_date"] or p["paid_at"][:10]
                                label(pr, d, size=8, color=GREY, width=90, anchor="w").pack(side="left")
                                label(pr, f"Ksh {fmt(p['amount'])}", size=8,
                                      color=GREEN, width=90, anchor="center").pack(side="left")
                                note = p["notes"] or ""
                                if note:
                                    label(pr, note, size=8, color=GREY, width=120, anchor="w").pack(side="left")
                            df.pack(fill="x", padx=4, after=row_f)
                            btn.configure(text=f"▲ {len(h)}")
                            shown[0] = True
                    return toggle

                hist_btn.configure(command=_make_toggle())

            # Term total row
            t_owed = sum(r["total_owed"] for r in rows)
            t_paid = sum(r["total_paid"] for r in rows)
            t_bal  = t_owed - t_paid
            tot_f = ctk.CTkFrame(tf, fg_color=NAVY)
            tot_f.pack(fill="x", padx=4, pady=(2,4))
            label(tot_f, f"  {term} TOTAL", size=9, bold=True, color=GOLD, width=140).pack(side="left")
            label(tot_f, fmt(t_owed), size=9, bold=True, color=WHITE, width=65, anchor="center").pack(side="left")
            label(tot_f, fmt(t_paid), size=9, bold=True, color=WHITE, width=65, anchor="center").pack(side="left")
            label(tot_f, fmt(t_bal), size=9, bold=True,
                  color=GREEN if t_bal <= 0 else RED, width=65, anchor="center").pack(side="left")

        # Grand total across all terms
        summary = db.get_student_balance_summary(self._selected_student["student_id"])
        g_bal = summary["total_balance"]
        self.grand_lbl.configure(
            text=f"GRAND TOTAL  |  Owed: Ksh {fmt(summary['total_owed'])}   Paid: Ksh {fmt(summary['total_paid'])}")
        self.grand_bal_lbl.configure(
            text=f"Balance: Ksh {fmt(g_bal)}",
            text_color=GREEN if g_bal <= 0 else RED)

    def _record_payment(self):
        if not self._selected_student:
            messagebox.showwarning("No Student", "Please select a student first.")
            return
        raw = self.e_amount.get().strip().replace(",", "")
        try:
            amount = float(raw)
        except ValueError:
            messagebox.showwarning("Invalid Amount", "Enter a valid number e.g. 1,000 or 1000.")
            return
        paid_date = self.e_date.get().strip()
        if not paid_date:
            paid_date = datetime.now().strftime("%Y-%m-%d")
        cat = self.v_cat.get()
        if not cat or cat == "—":
            messagebox.showwarning("No Category", "Select a fee category.")
            return
        ok, msg = db.record_payment(
            self._selected_student["student_id"],
            self.v_term.get(), cat, amount,
            notes=self.e_notes.get().strip(),
            paid_date=paid_date
        )
        self.pay_status.configure(text=msg, text_color=GREEN if ok else RED)
        if ok:
            self.e_amount.delete(0, "end")
            self.e_notes.delete(0, "end")
            self._update_categories()
            self._refresh_fee_summary()

    def _add_exam_fee(self):
        if not self._selected_student:
            messagebox.showwarning("No Student", "Please select a student first.")
            return
        name = self.e_exam_name.get().strip()
        raw  = self.e_exam_amt.get().strip().replace(",", "")
        try:
            amount = float(raw)
        except ValueError:
            self.exam_status.configure(text="Enter a valid amount.", text_color=RED)
            return
        ok, msg = db.add_exam_fee(
            self._selected_student["student_id"],
            self.v_exam_term.get(), name, amount
        )
        self.exam_status.configure(text=msg, text_color=GREEN if ok else RED)
        if ok:
            self.e_exam_name.delete(0, "end")
            self.e_exam_amt.delete(0, "end")
            self._update_categories()
            self._refresh_fee_summary()

    def _gen_payment_pdf(self):
        if not self._selected_student:
            messagebox.showwarning("No Student", "Select a student first.")
            return
        path = rg.generate_payment_report(student_id=self._selected_student["student_id"])
        open_pdf(path)

        open_pdf(path)


class FeeSettingsTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=LIGHT)
        self._selected_student = None
        self._build()
        self._load_settings()

    def _build(self):
        # ── LEFT: manage fee categories ──────────────────────────────────────
        left = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=12,
                            border_width=1, border_color=MID, width=360)
        left.pack(side="left", fill="y", padx=(10,5), pady=10)
        left.pack_propagate(False)

        labeled_header(left, "  Extra Fee Categories", size=13).pack(fill="x")
        label(left, "Create categories like Lunch, Uniform, Tour.\nThey won't be charged until you assign them to a student.",
              size=10, color=GREY).pack(pady=(8,2), padx=10)
        ctk.CTkFrame(left, height=2, fg_color=GOLD).pack(fill="x", padx=10, pady=(0,8))

        # Add new category
        add_frame = ctk.CTkFrame(left, fg_color=LIGHT, corner_radius=8)
        add_frame.pack(fill="x", padx=10, pady=(0,8))
        label(add_frame, "New Category", size=10, color=NAVY).pack(anchor="w", padx=8, pady=(6,2))
        row_add = ctk.CTkFrame(add_frame, fg_color="transparent")
        row_add.pack(fill="x", padx=8, pady=(0,8))
        self.e_new_cat = entry(row_add, "e.g. Lunch", width=130)
        self.e_new_cat.pack(side="left", padx=(0,6))
        self.e_new_amt = entry(row_add, "Amount", width=80)
        self.e_new_amt.pack(side="left", padx=(0,6))
        btn(row_add, "+ Add", self._add_category, color=GREEN, width=60).pack(side="left")

        label(left, "Existing Categories:", size=10, bold=True, color=NAVY).pack(anchor="w", padx=12, pady=(4,2))
        self.cat_scroll = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self.cat_scroll.pack(fill="both", expand=True, padx=6, pady=(0,4))

        hdr = ctk.CTkFrame(self.cat_scroll, fg_color=MID, corner_radius=6)
        hdr.pack(fill="x", pady=(0,3))
        for txt, w in [("Category", 120), ("Amount", 80), ("", 110)]:
            label(hdr, txt, size=9, bold=True, color=NAVY, width=w, anchor="center").pack(side="left", padx=2, pady=3)

        self.cat_rows_frame = ctk.CTkFrame(self.cat_scroll, fg_color="transparent")
        self.cat_rows_frame.pack(fill="both", expand=True)

        self.cat_status = label(left, "", size=9, color=GREEN)
        self.cat_status.pack(pady=(2,6))

        # ── RIGHT: assign fee to student ─────────────────────────────────────
        right = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=12,
                             border_width=1, border_color=MID)
        right.pack(side="left", fill="both", expand=True, padx=(5,10), pady=10)

        labeled_header(right, "  Assign Fee to a Student", size=13).pack(fill="x")
        label(right, "Pick a student, choose a category and which term(s) it applies to, then assign.",
              size=10, color=GREY).pack(pady=(8,2), padx=10)
        ctk.CTkFrame(right, height=2, fg_color=GOLD).pack(fill="x", padx=10, pady=(0,10))

        # Student search
        search_row = ctk.CTkFrame(right, fg_color="transparent")
        search_row.pack(fill="x", padx=12, pady=(0,6))
        label(search_row, "Student:", size=10).pack(side="left", padx=(0,6))
        self.e_assign_search = entry(search_row, "Search name or ID...", width=180)
        self.e_assign_search.pack(side="left", padx=(0,6))
        self.e_assign_search.bind("<KeyRelease>", self._search_students)
        self.v_assign_student = ctk.StringVar(value="— select student —")
        self.dd_assign_student = ctk.CTkOptionMenu(
            search_row, variable=self.v_assign_student,
            values=["— select student —"], command=self._on_student_select,
            fg_color=WHITE, button_color=NAVY, text_color=NAVY, corner_radius=6, width=220)
        self.dd_assign_student.pack(side="left")

        self.assign_info = label(right, "", size=9, color=GREY)
        self.assign_info.pack(anchor="w", padx=14)

        # Category + term selection
        pick_frame = ctk.CTkFrame(right, fg_color=LIGHT, corner_radius=8)
        pick_frame.pack(fill="x", padx=12, pady=(6,0))

        col1 = ctk.CTkFrame(pick_frame, fg_color="transparent")
        col1.pack(side="left", fill="y", padx=(10,10), pady=10)
        label(col1, "Fee Category", size=10, bold=True, color=NAVY).pack(anchor="w", pady=(0,4))
        self.v_assign_cat = ctk.StringVar(value="")
        self.dd_assign_cat = ctk.CTkOptionMenu(
            col1, variable=self.v_assign_cat, values=["— add a category first —"],
            fg_color=WHITE, button_color=NAVY, text_color=NAVY, corner_radius=6, width=160)
        self.dd_assign_cat.pack()
        self.assign_cat_amt = label(col1, "", size=9, color=GREY)
        self.assign_cat_amt.pack(anchor="w", pady=(3,0))
        self.v_assign_cat.trace_add("write", self._update_cat_amount)

        ctk.CTkFrame(pick_frame, width=2, fg_color=MID).pack(side="left", fill="y", pady=8)

        col2 = ctk.CTkFrame(pick_frame, fg_color="transparent")
        col2.pack(side="left", fill="y", padx=(10,10), pady=10)
        label(col2, "Apply to Term(s)", size=10, bold=True, color=NAVY).pack(anchor="w", pady=(0,4))
        self.term_vars = {}
        for t in db.TERMS:
            var = ctk.BooleanVar(value=False)
            self.term_vars[t] = var
            ctk.CTkCheckBox(col2, text=t, variable=var,
                            text_color=NAVY, fg_color=NAVY,
                            font=("Helvetica", 10)).pack(anchor="w", pady=2)

        btn_col = ctk.CTkFrame(pick_frame, fg_color="transparent")
        btn_col.pack(side="left", fill="y", padx=(6,10), pady=10)
        btn(btn_col, "✔ Assign", self._assign_fee, color=GREEN, width=100).pack(pady=(20,6))

        self.assign_status = label(right, "", size=10, color=GREEN)
        self.assign_status.pack(pady=(6,4))

        # Current extra fees for this student
        labeled_header(right, "  This Student's Extra Fees", size=11).pack(fill="x", pady=(4,0))
        self.assigned_scroll = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self.assigned_scroll.pack(fill="both", expand=True, padx=8, pady=(4,8))

        self._refresh_assign_cat_dropdown()

    def _load_settings(self):
        """Rebuild category list on the left panel."""
        for w in self.cat_rows_frame.winfo_children():
            w.destroy()
        settings = db.get_fee_settings()
        if not settings:
            label(self.cat_rows_frame, "No categories yet. Add one above.",
                  size=10, color=GREY).pack(pady=10)
            self._refresh_assign_cat_dropdown()
            return
        for i, cat_info in enumerate(settings):
            bg = WHITE if i % 2 == 0 else LIGHT
            row = ctk.CTkFrame(self.cat_rows_frame, fg_color=bg, corner_radius=6)
            row.pack(fill="x", pady=1)
            label(row, cat_info["category"], size=10, width=118, anchor="w").pack(side="left", padx=(6,2), pady=5)
            amt_e = entry(row, "", width=72)
            amt_e.insert(0, fmt(cat_info["amount"]))
            amt_e.pack(side="left", padx=(0,4), pady=5)

            def _make_save(cat=cat_info["category"], e=amt_e):
                def _save():
                    raw = e.get().strip().replace(",", "")
                    try:
                        db.set_fee_setting(cat, float(raw))
                        self.cat_status.configure(text=f"'{cat}' updated.", text_color=GREEN)
                        self._refresh_assign_cat_dropdown()
                    except ValueError:
                        self.cat_status.configure(text="Invalid amount.", text_color=RED)
                return _save

            def _make_delete(cat=cat_info["category"]):
                def _delete():
                    ok, msg = db.delete_fee_category(cat)
                    self.cat_status.configure(text=msg, text_color=GREEN if ok else RED)
                    if ok:
                        self._load_settings()
                        self._refresh_assigned_fees()
                return _delete

            btn(row, "Save", _make_save(), color=NAVY, width=46).pack(side="left", padx=(0,3), pady=5)
            del_btn = btn(row, "✕", _make_delete(),
                         color=RED if not cat_info["is_fixed"] else MID,
                         text_color=WHITE, width=30)
            del_btn.pack(side="left", padx=(0,4), pady=5)
            if cat_info["is_fixed"]:
                del_btn.configure(state="disabled")

        self._refresh_assign_cat_dropdown()

    def _add_category(self):
        cat = self.e_new_cat.get().strip()
        raw = self.e_new_amt.get().strip().replace(",", "")
        if not cat:
            self.cat_status.configure(text="Enter a category name.", text_color=RED)
            return
        try:
            amount = float(raw)
        except ValueError:
            self.cat_status.configure(text="Enter a valid amount.", text_color=RED)
            return
        ok, msg = db.add_fee_category(cat, amount)
        self.cat_status.configure(text=msg, text_color=GREEN if ok else RED)
        if ok:
            self.e_new_cat.delete(0, "end")
            self.e_new_amt.delete(0, "end")
            self._load_settings()

    def _refresh_assign_cat_dropdown(self):
        settings = db.get_fee_settings()
        cats = [s["category"] for s in settings] if settings else []
        self.dd_assign_cat.configure(values=cats if cats else ["— add a category first —"])
        if cats:
            self.v_assign_cat.set(cats[0])
            self._update_cat_amount()
        else:
            self.v_assign_cat.set("")

    def _update_cat_amount(self, *args):
        cat = self.v_assign_cat.get()
        settings = db.get_fee_settings()
        for s in settings:
            if s["category"] == cat:
                self.assign_cat_amt.configure(text=f"Ksh {fmt(s['amount'])} per term")
                return
        self.assign_cat_amt.configure(text="")

    def _search_students(self, event=None):
        q = self.e_assign_search.get().lower().strip()
        all_s = db.get_all_students()
        matches = [s for s in all_s
                   if q in s["name"].lower() or q in s["student_id"].lower()] if q else all_s
        options = [f"{s['student_id']} — {s['name']}" for s in matches[:20]]
        self.dd_assign_student.configure(values=options if options else ["No match"])
        if options:
            self.v_assign_student.set(options[0])
            self._on_student_select(options[0])

    def _on_student_select(self, val):
        if "—" not in val or val == "— select student —":
            return
        sid = val.split("—")[0].strip()
        self._selected_student = db.get_student(sid)
        if self._selected_student:
            s = self._selected_student
            self.assign_info.configure(
                text=f"Class: {s['class']}   Teacher: {s['teacher'] or '—'}")
        self._refresh_assigned_fees()

    def _assign_fee(self):
        if not self._selected_student:
            self.assign_status.configure(text="Select a student first.", text_color=RED)
            return
        cat = self.v_assign_cat.get()
        if not cat or cat == "— add a category first —":
            self.assign_status.configure(text="Select a fee category.", text_color=RED)
            return
        chosen_terms = [t for t, var in self.term_vars.items() if var.get()]
        if not chosen_terms:
            self.assign_status.configure(text="Tick at least one term.", text_color=RED)
            return
        ok, msg = db.assign_extra_fee(self._selected_student["student_id"], cat, chosen_terms)
        self.assign_status.configure(text=msg, text_color=GREEN if ok else RED)
        if ok:
            for var in self.term_vars.values():
                var.set(False)
            self._refresh_assigned_fees()

    def _refresh_assigned_fees(self):
        for w in self.assigned_scroll.winfo_children():
            w.destroy()
        if not self._selected_student:
            label(self.assigned_scroll, "No student selected.", size=10, color=GREY).pack(pady=8)
            return
        extras = db.get_student_extra_fees(self._selected_student["student_id"])
        if not extras:
            label(self.assigned_scroll, "No extra fees assigned to this student yet.",
                  size=10, color=GREY).pack(pady=8)
            return

        # Group by category
        by_cat = {}
        for f in extras:
            by_cat.setdefault(f["category"], []).append(f)

        for cat, rows in by_cat.items():
            cf = ctk.CTkFrame(self.assigned_scroll, fg_color=LIGHT, corner_radius=8,
                              border_width=1, border_color=MID)
            cf.pack(fill="x", pady=(0,6))
            hdr_row = ctk.CTkFrame(cf, fg_color=NAVY, corner_radius=6)
            hdr_row.pack(fill="x")
            label(hdr_row, f"  {cat}", size=10, bold=True, color=WHITE).pack(side="left", pady=4)

            for r in rows:
                bal = r["total_owed"] - r["total_paid"]
                term_row = ctk.CTkFrame(cf, fg_color="transparent")
                term_row.pack(fill="x", padx=6, pady=2)
                label(term_row, r["term"], size=9, width=80, anchor="w").pack(side="left")
                label(term_row, f"Owed: {fmt(r['total_owed'])}", size=9, width=100, color=GREY).pack(side="left")
                label(term_row, f"Paid: {fmt(r['total_paid'])}", size=9, width=100, color=GREY).pack(side="left")
                label(term_row, f"Bal: {fmt(bal)}", size=9, width=80,
                      color=GREEN if bal <= 0 else RED).pack(side="left")

                def _make_remove(sid=self._selected_student["student_id"],
                                 c=r["category"], t=r["term"]):
                    def _remove():
                        ok, msg = db.remove_extra_fee(sid, c, t)
                        self.assign_status.configure(text=msg, text_color=GREEN if ok else RED)
                        if ok:
                            self._refresh_assigned_fees()
                    return _remove

                remove_btn = btn(term_row, "✕ Remove", _make_remove(),
                                 color=RED, text_color=WHITE, width=80)
                remove_btn.pack(side="left", padx=(6,0))
                if r["total_paid"] > 0:
                    remove_btn.configure(state="disabled")


class ReportsTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=LIGHT)
        self._build()

    def _build(self):
        label(self, "Generate Reports", size=14, bold=True).pack(pady=(12, 2))
        label(self, "All PDFs are saved to the reports/ folder and opened automatically.",
              size=10, color=GREY).pack(pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 4))

        # ── 1. Student Register ───────────────────────────────────────────────
        reg_card = ctk.CTkFrame(scroll, fg_color=WHITE, corner_radius=12,
                                border_width=1, border_color=MID)
        reg_card.pack(fill="x", pady=(0, 10))
        labeled_header(reg_card, "  1 · Student Register", size=12).pack(fill="x")
        r1 = ctk.CTkFrame(reg_card, fg_color="transparent")
        r1.pack(fill="x", padx=16, pady=10)
        label(r1, "Class:", size=10).pack(side="left", padx=(0, 8))
        self.v_reg_class = ctk.StringVar(value="All Classes")
        ctk.CTkOptionMenu(r1, variable=self.v_reg_class,
                          values=["All Classes"] + db.CLASSES,
                          fg_color=WHITE, button_color=NAVY, text_color=NAVY,
                          corner_radius=6, width=160).pack(side="left", padx=(0, 16))
        btn(r1, "Generate PDF", self._gen_register, width=160).pack(side="left")

        # ── 2. Single Student Payment Report ─────────────────────────────────
        single_card = ctk.CTkFrame(scroll, fg_color=WHITE, corner_radius=12,
                                   border_width=1, border_color=MID)
        single_card.pack(fill="x", pady=(0, 10))
        labeled_header(single_card, "  2 · Single Student Payment Report", size=12).pack(fill="x")
        sc_inner = ctk.CTkFrame(single_card, fg_color="transparent")
        sc_inner.pack(fill="x", padx=16, pady=10)
        label(sc_inner, "Search:", size=10).pack(side="left", padx=(0, 6))
        self.e_single_search = entry(sc_inner, "Name or Student ID...", width=180)
        self.e_single_search.pack(side="left", padx=(0, 8))
        self.e_single_search.bind("<KeyRelease>", self._search_single_student)
        self.v_single_student = ctk.StringVar(value="— select student —")
        self.dd_single_student = ctk.CTkOptionMenu(
            sc_inner, variable=self.v_single_student,
            values=["— select student —"],
            fg_color=WHITE, button_color=NAVY, text_color=NAVY,
            corner_radius=6, width=240)
        self.dd_single_student.pack(side="left", padx=(0, 16))
        btn(sc_inner, "Generate PDF", self._gen_single_payment,
            color=GOLD, text_color=NAVY, width=160).pack(side="left")

        # ── 3. Payment Report per Term ────────────────────────────────────────
        pay_card = ctk.CTkFrame(scroll, fg_color=WHITE, corner_radius=12,
                                border_width=1, border_color=MID)
        pay_card.pack(fill="x", pady=(0, 10))
        labeled_header(pay_card, "  3 · Payment Report per Term (Class / All)", size=12).pack(fill="x")
        pay_inner = ctk.CTkFrame(pay_card, fg_color="transparent")
        pay_inner.pack(fill="x", padx=16, pady=10)

        cls_col = ctk.CTkFrame(pay_inner, fg_color="transparent")
        cls_col.pack(side="left", padx=(0, 24))
        label(cls_col, "Class:", size=10).pack(anchor="w", pady=(0, 4))
        self.v_pay_class = ctk.StringVar(value="All Classes")
        ctk.CTkOptionMenu(cls_col, variable=self.v_pay_class,
                          values=["All Classes"] + db.CLASSES,
                          fg_color=WHITE, button_color=NAVY, text_color=NAVY,
                          corner_radius=6, width=150).pack()

        term_col = ctk.CTkFrame(pay_inner, fg_color="transparent")
        term_col.pack(side="left", padx=(0, 24))
        label(term_col, "Term(s):", size=10).pack(anchor="w", pady=(0, 4))
        self.pay_term_vars = {}
        term_chk_row = ctk.CTkFrame(term_col, fg_color="transparent")
        term_chk_row.pack()
        for t in db.TERMS:
            var = ctk.BooleanVar(value=True)
            self.pay_term_vars[t] = var
            ctk.CTkCheckBox(term_chk_row, text=t, variable=var,
                            text_color=NAVY, fg_color=NAVY,
                            font=("Helvetica", 10), width=90).pack(side="left", padx=(0, 6))

        btn_col = ctk.CTkFrame(pay_inner, fg_color="transparent")
        btn_col.pack(side="left")
        btn(btn_col, "Generate PDF", self._gen_payment, color=GREEN, width=160).pack(pady=(18, 0))

        # ── 4. Pending Balances Report ────────────────────────────────────────
        bal_card = ctk.CTkFrame(scroll, fg_color=WHITE, corner_radius=12,
                                border_width=1, border_color=MID)
        bal_card.pack(fill="x", pady=(0, 10))
        labeled_header(bal_card, "  4 · Pending Balances Report", size=12).pack(fill="x")
        bal_inner = ctk.CTkFrame(bal_card, fg_color="transparent")
        bal_inner.pack(fill="x", padx=16, pady=10)
        label(bal_inner,
              "Shows every student with an outstanding balance, summed across all terms.",
              size=9, color=GREY).pack(anchor="w", pady=(0, 8))

        bal_cls_col = ctk.CTkFrame(bal_inner, fg_color="transparent")
        bal_cls_col.pack(side="left", padx=(0, 24))
        label(bal_cls_col, "Class:", size=10).pack(anchor="w", pady=(0, 4))
        self.v_bal_class = ctk.StringVar(value="All Classes")
        ctk.CTkOptionMenu(bal_cls_col, variable=self.v_bal_class,
                          values=["All Classes"] + db.CLASSES,
                          fg_color=WHITE, button_color=NAVY, text_color=NAVY,
                          corner_radius=6, width=150).pack()

        bal_btn_col = ctk.CTkFrame(bal_inner, fg_color="transparent")
        bal_btn_col.pack(side="left")
        btn(bal_btn_col, "Generate PDF", self._gen_balances, color=RED, width=160).pack(pady=(18, 0))

        # ── 5. Year-End Promotion ─────────────────────────────────────────────
        prom_card = ctk.CTkFrame(scroll, fg_color=WHITE, corner_radius=12,
                                 border_width=1, border_color=MID)
        prom_card.pack(fill="x", pady=(0, 10))
        labeled_header(prom_card, "  5 · Year-End Promotion", size=12).pack(fill="x")
        r3 = ctk.CTkFrame(prom_card, fg_color="transparent")
        r3.pack(fill="x", padx=16, pady=12)
        label(r3,
              "Promote ALL students to next class after Term III ends.\n"
              "Grade 3 → Grade 4.  Grade 4 students complete school and are removed.",
              size=10, color=GREY, justify="left").pack(side="left", padx=(0, 16))
        btn(r3, "Promote All", self._promote, color=RED, width=160).pack(side="left")

        self.status = label(self, "", size=10, color=GREEN)
        self.status.pack(pady=(4, 8))

    # ── handlers ─────────────────────────────────────────────────────────────

    def _gen_register(self):
        try:
            cls = self.v_reg_class.get()
            path = rg.generate_student_register(None if cls == "All Classes" else cls)
            self.status.configure(text=f"Saved: {os.path.basename(path)}", text_color=GREEN)
            open_pdf(path)
        except Exception as e:
            messagebox.showerror("Error", f"Could not generate report:\n{e}")

    def _search_single_student(self, event=None):
        q = self.e_single_search.get().lower().strip()
        all_s = db.get_all_students()
        matches = ([s for s in all_s
                    if q in s["name"].lower() or q in s["student_id"].lower()]
                   if q else all_s)
        options = [f"{s['student_id']} — {s['name']}" for s in matches[:20]]
        self.dd_single_student.configure(values=options if options else ["No match"])
        if options:
            self.v_single_student.set(options[0])

    def _gen_single_payment(self):
        val = self.v_single_student.get()
        if val in ("— select student —", "No match", "") or " — " not in val:
            messagebox.showwarning("No Student", "Search and select a student first.")
            return
        sid = val.rsplit(" — ", 1)[0].strip()
        try:
            path = rg.generate_payment_report(student_id=sid)
            self.status.configure(text=f"Saved: {os.path.basename(path)}", text_color=GREEN)
            open_pdf(path)
        except Exception as e:
            messagebox.showerror("Error", f"Could not generate report:\n{e}")

    def _gen_payment(self):
        selected_terms = [t for t, var in self.pay_term_vars.items() if var.get()]
        if not selected_terms:
            messagebox.showwarning("No Term", "Please select at least one term.")
            return
        cls = self.v_pay_class.get()
        try:
            path = rg.generate_payment_report(
                class_filter=None if cls == "All Classes" else cls,
                terms_filter=selected_terms
            )
            self.status.configure(text=f"Saved: {os.path.basename(path)}", text_color=GREEN)
            open_pdf(path)
        except Exception as e:
            messagebox.showerror("Error", f"Could not generate report:\n{e}")

    def _gen_balances(self):
        cls = self.v_bal_class.get()
        try:
            path = rg.generate_balances_report(
                class_filter=None if cls == "All Classes" else cls
            )
            self.status.configure(text=f"Saved: {os.path.basename(path)}", text_color=GREEN)
            open_pdf(path)
        except Exception as e:
            messagebox.showerror("Error", f"Could not generate report:\n{e}")

    def _promote(self):
        if not messagebox.askyesno("Confirm Promotion",
                "This will move ALL students to the next class.\n"
                "Grade 3 → Grade 4 (promoted).\n"
                "Grade 4 students complete the school and are removed.\n\nAre you sure?"):
            return
        promoted, left = db.promote_all_students()
        msg = (f"Promoted {len(promoted)} students. "
               f"{len(left)} completed Grade 4 and removed.")
        self.status.configure(text=msg, text_color=GREEN)
        messagebox.showinfo("Promotion Complete", msg)
class RequirementsTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=LIGHT)
        self._selected_sid = None
        self._build()
        self._load_req_list()

    def _build(self):
        left = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=12,
                            border_width=1, border_color=MID, width=340)
        left.pack(side="left", fill="y", padx=(10,5), pady=10)
        left.pack_propagate(False)

        labeled_header(left, "  Requirements List", size=13).pack(fill="x")
        label(left, "Define items every student must bring.\nSet quantity if more than one needed.",
              size=10, color=GREY).pack(pady=(8,4), padx=10)
        ctk.CTkFrame(left, height=2, fg_color=GOLD).pack(fill="x", padx=10, pady=(0,8))

        add_f = ctk.CTkFrame(left, fg_color=LIGHT, corner_radius=8)
        add_f.pack(fill="x", padx=10, pady=(0,8))
        label(add_f, "Item Name", size=9, color=GREY).pack(anchor="w", padx=8, pady=(6,1))
        self.e_req_name = entry(add_f, "e.g. Exercise Book", width=290)
        self.e_req_name.pack(fill="x", padx=8)
        qty_row = ctk.CTkFrame(add_f, fg_color="transparent")
        qty_row.pack(fill="x", padx=8, pady=(4,8))
        label(qty_row, "Quantity needed:", size=9, color=GREY).pack(side="left", padx=(0,6))
        self.e_req_qty = entry(qty_row, "1", width=50)
        self.e_req_qty.insert(0, "1")
        self.e_req_qty.pack(side="left", padx=(0,8))
        btn(qty_row, "+ Add", self._add_req, color=GREEN, width=70).pack(side="left")

        self.req_list_scroll = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self.req_list_scroll.pack(fill="both", expand=True, padx=6, pady=(0,4))
        self.req_status = label(left, "", size=9, color=GREEN)
        self.req_status.pack(pady=(2,6))

        right = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=12,
                             border_width=1, border_color=MID)
        right.pack(side="left", fill="both", expand=True, padx=(5,10), pady=10)

        labeled_header(right, "  Student Requirements", size=13).pack(fill="x")
        label(right, "Select a student to update what they have brought.",
              size=10, color=GREY).pack(pady=(8,4), padx=10)
        ctk.CTkFrame(right, height=2, fg_color=GOLD).pack(fill="x", padx=10, pady=(0,8))

        search_row = ctk.CTkFrame(right, fg_color="transparent")
        search_row.pack(fill="x", padx=10, pady=(0,6))
        label(search_row, "Student:", size=10).pack(side="left", padx=(0,6))
        self.e_std_search = entry(search_row, "Name or ID...", width=180)
        self.e_std_search.pack(side="left", padx=(0,6))
        self.e_std_search.bind("<KeyRelease>", self._search_students)
        self.v_student = ctk.StringVar(value="— select —")
        self.dd_student = ctk.CTkOptionMenu(right, variable=self.v_student,
                                            values=["— select —"],
                                            command=self._load_student_reqs,
                                            fg_color=WHITE, button_color=NAVY,
                                            text_color=NAVY, corner_radius=6, width=300)
        self.dd_student.pack(fill="x", padx=10, pady=(0,8))

        self.std_req_scroll = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self.std_req_scroll.pack(fill="both", expand=True, padx=8, pady=(0,4))
        self.std_status = label(right, "", size=9, color=GREEN)
        self.std_status.pack(pady=(2,6))

    def _load_req_list(self):
        for w in self.req_list_scroll.winfo_children():
            w.destroy()
        reqs = db.get_requirements()
        if not reqs:
            label(self.req_list_scroll, "No requirements yet. Add one above.",
                  size=10, color=GREY).pack(pady=10)
            return
        hdr = ctk.CTkFrame(self.req_list_scroll, fg_color=MID, corner_radius=6)
        hdr.pack(fill="x", pady=(0,3))
        for txt, w in [("Item", 148), ("Qty", 38), ("", 100)]:
            label(hdr, txt, size=9, bold=True, color=NAVY, width=w, anchor="center").pack(side="left", padx=2, pady=3)
        for i, r in enumerate(reqs):
            bg = WHITE if i % 2 == 0 else LIGHT
            row = ctk.CTkFrame(self.req_list_scroll, fg_color=bg, corner_radius=6)
            row.pack(fill="x", pady=1)
            e_n = entry(row, "", width=136)
            e_n.insert(0, r["name"])
            e_n.pack(side="left", padx=(4,2), pady=4)
            e_q = entry(row, "", width=34)
            e_q.insert(0, str(r["quantity"]))
            e_q.pack(side="left", padx=(0,4), pady=4)

            def _mk_save(rid=r["id"], en=e_n, eq=e_q):
                def _s():
                    try:
                        qty = int(eq.get().strip())
                    except ValueError:
                        self.req_status.configure(text="Invalid quantity.", text_color=RED)
                        return
                    ok, msg = db.update_requirement(rid, en.get().strip(), qty)
                    self.req_status.configure(text=msg, text_color=GREEN if ok else RED)
                    self._load_req_list()
                return _s

            def _mk_del(rid=r["id"]):
                def _d():
                    ok, msg = db.delete_requirement(rid)
                    self.req_status.configure(text=msg, text_color=GREEN if ok else RED)
                    self._load_req_list()
                    if self._selected_sid:
                        self._render_student_reqs(self._selected_sid)
                return _d

            btn(row, "Save", _mk_save(), color=NAVY, width=44).pack(side="left", padx=(0,2), pady=4)
            btn(row, "✕", _mk_del(), color=RED, width=28).pack(side="left", padx=(0,4), pady=4)

    def _add_req(self):
        name = self.e_req_name.get().strip()
        try:
            qty = int(self.e_req_qty.get().strip())
        except ValueError:
            self.req_status.configure(text="Enter a valid quantity.", text_color=RED)
            return
        ok, msg = db.add_requirement(name, qty)
        self.req_status.configure(text=msg, text_color=GREEN if ok else RED)
        if ok:
            self.e_req_name.delete(0, "end")
            self.e_req_qty.delete(0, "end")
            self.e_req_qty.insert(0, "1")
            self._load_req_list()

    def _search_students(self, event=None):
        q = self.e_std_search.get().lower().strip()
        all_s = db.get_all_students()
        matches = [s for s in all_s
                   if q in s["name"].lower() or q in s["student_id"].lower()] if q else all_s
        options = [f"{s['student_id']} — {s['name']}" for s in matches[:20]]
        self.dd_student.configure(values=options if options else ["No match"])
        if options:
            self.v_student.set(options[0])
            self._load_student_reqs(options[0])

    def _load_student_reqs(self, val):
        if not val or val == "— select —" or " — " not in val:
            return
        self._selected_sid = val.rsplit(" — ", 1)[0].strip()
        self._render_student_reqs(self._selected_sid)

    def _render_student_reqs(self, sid):
        for w in self.std_req_scroll.winfo_children():
            w.destroy()
        reqs = db.get_student_requirements(sid)
        if not reqs:
            label(self.std_req_scroll, "No requirements defined yet. Add some on the left.",
                  size=10, color=GREY).pack(pady=10)
            return
        hdr = ctk.CTkFrame(self.std_req_scroll, fg_color=NAVY, corner_radius=6)
        hdr.pack(fill="x", pady=(0,4))
        for txt, w in [("Requirement", 190), ("Need", 55), ("Brought", 65), ("Status", 95), ("", 70)]:
            label(hdr, txt, size=9, bold=True, color=WHITE, width=w, anchor="center").pack(side="left", padx=2, pady=4)
        for i, r in enumerate(reqs):
            bg = WHITE if i % 2 == 0 else LIGHT
            row = ctk.CTkFrame(self.std_req_scroll, fg_color=bg, corner_radius=6)
            row.pack(fill="x", pady=1)
            label(row, r["name"], size=10, width=190, anchor="w").pack(side="left", padx=(6,2), pady=5)
            label(row, str(r["required"]), size=10, width=55, anchor="center").pack(side="left")
            e_b = entry(row, "0", width=55)
            e_b.delete(0, "end")
            e_b.insert(0, str(r["brought"]))
            e_b.pack(side="left", padx=(4,4), pady=5)
            done    = r["brought"] >= r["required"]
            partial = 0 < r["brought"] < r["required"]
            stxt = "✔ Complete" if done else ("Partial" if partial else "✗ Missing")
            scol = GREEN if done else (GOLD if partial else RED)
            sl = label(row, stxt, size=9, color=scol, width=95, anchor="center")
            sl.pack(side="left")

            def _mk_upd(rid=r["id"], e=e_b, s=sl, req=r["required"], student_id=sid):
                def _upd():
                    try:
                        qty = int(e.get().strip())
                    except ValueError:
                        self.std_status.configure(text="Enter a valid number.", text_color=RED)
                        return
                    try:
                        db.set_student_requirement(student_id, rid, qty)
                    except Exception as ex:
                        self.std_status.configure(text=f"Error: {ex}", text_color=RED)
                        return
                    done2 = qty >= req
                    part2 = 0 < qty < req
                    try:
                        s.configure(
                            text="✔ Complete" if done2 else ("Partial" if part2 else "✗ Missing"),
                            text_color=GREEN if done2 else (GOLD if part2 else RED)
                        )
                    except Exception:
                        pass
                    self.std_status.configure(text="Updated.", text_color=GREEN)
                return _upd

            btn(row, "Update", _mk_upd(), color=NAVY, width=62).pack(side="left", padx=(4,6), pady=5)


class MiscTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=LIGHT)
        self._build()
        self._load_expenses()

    def _build(self):
        # TOP — add expense
        top = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=12,
                           border_width=1, border_color=MID)
        top.pack(fill="x", padx=10, pady=(10,5))
        labeled_header(top, "  Add Miscellaneous Expense", size=13).pack(fill="x")

        form = ctk.CTkFrame(top, fg_color="transparent")
        form.pack(fill="x", padx=14, pady=10)

        label(form, "Term", size=10, color=GREY).pack(side="left", padx=(0,4))
        self.v_term = ctk.StringVar(value=db.TERMS[0])
        ctk.CTkOptionMenu(form, variable=self.v_term, values=db.TERMS,
                          command=lambda _: self._load_expenses(),
                          fg_color=WHITE, button_color=NAVY, text_color=NAVY,
                          corner_radius=6, width=110).pack(side="left", padx=(0,12))

        label(form, "Item", size=10, color=GREY).pack(side="left", padx=(0,4))
        self.e_item = entry(form, "e.g. Cooking Oil", width=160)
        self.e_item.pack(side="left", padx=(0,12))

        label(form, "Amount (Ksh)", size=10, color=GREY).pack(side="left", padx=(0,4))
        self.e_amt = entry(form, "e.g. 500", width=100)
        self.e_amt.pack(side="left", padx=(0,12))

        label(form, "Date", size=10, color=GREY).pack(side="left", padx=(0,4))
        self.e_date = entry(form, "YYYY-MM-DD", width=120)
        self.e_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.e_date.pack(side="left", padx=(0,12))

        label(form, "Notes", size=10, color=GREY).pack(side="left", padx=(0,4))
        self.e_notes = entry(form, "optional", width=120)
        self.e_notes.pack(side="left", padx=(0,12))

        btn(form, "+ Add", self._add_expense, color=GREEN, width=80).pack(side="left")
        self.add_status = label(top, "", size=9, color=GREEN)
        self.add_status.pack(pady=(0,6))

        # BOTTOM — expenses by term
        self.exp_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.exp_scroll.pack(fill="both", expand=True, padx=10, pady=(0,10))

    def _load_expenses(self):
        for w in self.exp_scroll.winfo_children():
            w.destroy()
        term = self.v_term.get()
        expenses = db.get_misc_expenses(term=term)
        total = sum(e["amount"] for e in expenses)

        # Term header + total
        hf = ctk.CTkFrame(self.exp_scroll, fg_color=NAVY, corner_radius=8)
        hf.pack(fill="x", pady=(0,6))
        label(hf, f"  {term}", size=11, bold=True, color=GOLD).pack(side="left", padx=8, pady=6)
        label(hf, f"Total: Ksh {fmt(total)}", size=10, bold=True, color=WHITE).pack(side="right", padx=12, pady=6)

        if not expenses:
            label(self.exp_scroll, "No expenses recorded for this term.", size=10, color=GREY).pack(pady=10)
            return

        # Column headers
        hdr = ctk.CTkFrame(self.exp_scroll, fg_color=MID, corner_radius=6)
        hdr.pack(fill="x", pady=(0,3))
        for txt, w in [("Date", 90), ("Item", 200), ("Amount", 100), ("Notes", 180), ("", 60)]:
            label(hdr, txt, size=9, bold=True, color=NAVY, width=w, anchor="center").pack(side="left", padx=2, pady=3)

        for i, e in enumerate(expenses):
            bg = WHITE if i % 2 == 0 else LIGHT
            row = ctk.CTkFrame(self.exp_scroll, fg_color=bg, corner_radius=6)
            row.pack(fill="x", pady=1)
            label(row, e["expense_date"] or "—", size=9, width=90, anchor="center").pack(side="left")
            label(row, e["item"], size=9, width=200, anchor="w").pack(side="left", padx=4)
            label(row, f"Ksh {fmt(e['amount'])}", size=9, width=100, color=RED, anchor="center").pack(side="left")
            label(row, e["notes"] or "", size=9, width=180, anchor="w").pack(side="left", padx=4)

            def _make_del(eid=e["id"]):
                def _d():
                    db.delete_misc_expense(eid)
                    self._load_expenses()
                return _d

            btn(row, "✕", _make_del(), color=RED, width=30).pack(side="left", padx=4, pady=3)

    def _add_expense(self):
        item = self.e_item.get().strip()
        raw = self.e_amt.get().strip().replace(",", "")
        try:
            amount = float(raw)
        except ValueError:
            self.add_status.configure(text="Invalid amount.", text_color=RED)
            return
        ok, msg = db.add_misc_expense(
            self.v_term.get(), item, amount,
            self.e_date.get().strip(), self.e_notes.get().strip()
        )
        self.add_status.configure(text=msg, text_color=GREEN if ok else RED)
        if ok:
            self.e_item.delete(0, "end")
            self.e_amt.delete(0, "end")
            self.e_notes.delete(0, "end")
            self._load_expenses()


class LoginWindow(ctk.CTkToplevel):
    """Modal login screen — blocks the main window until correct credentials entered."""
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.title("Login — Elroi Favoured School")
        self.geometry("420x520")
        self.resizable(False, False)
        self.configure(fg_color=NAVY)
        self.grab_set()
        self.lift()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="ELROI FAVOURED SCHOOL",
                     font=("Helvetica", 16, "bold"), text_color=GOLD).pack(pady=(36, 2))
        ctk.CTkLabel(self, text="Management System",
                     font=("Helvetica", 11), text_color=MID).pack()
        ctk.CTkFrame(self, height=2, fg_color=GOLD).pack(fill="x", padx=40, pady=(20, 0))

        card = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=14)
        card.pack(padx=40, pady=20, fill="both", expand=True)

        ctk.CTkLabel(card, text="🔒  Sign In",
                     font=("Helvetica", 14, "bold"), text_color=NAVY).pack(pady=(24, 4))
        ctk.CTkLabel(card, text="Enter your credentials to continue.",
                     font=("Helvetica", 10), text_color=GREY).pack(pady=(0, 18))

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(padx=28, fill="x")

        ctk.CTkLabel(form, text="Username", font=("Helvetica", 10),
                     text_color=GREY).pack(anchor="w", pady=(0, 2))
        self.e_user = ctk.CTkEntry(form, corner_radius=8, border_color=MID,
                                   fg_color=LIGHT, font=("Helvetica", 11))
        self.e_user.pack(fill="x")
        self.e_user.insert(0, "admin")

        ctk.CTkLabel(form, text="Password", font=("Helvetica", 10),
                     text_color=GREY).pack(anchor="w", pady=(14, 2))
        self.e_pass = ctk.CTkEntry(form, corner_radius=8, border_color=MID,
                                   fg_color=LIGHT, font=("Helvetica", 11), show="●")
        self.e_pass.pack(fill="x")
        self.e_pass.bind("<Return>", lambda e: self._login())

        self.err_lbl = ctk.CTkLabel(form, text="", font=("Helvetica", 10), text_color=RED)
        self.err_lbl.pack(pady=(8, 0))

        ctk.CTkButton(card, text="Sign In", command=self._login,
                      fg_color=NAVY, hover_color=GOLD, text_color=WHITE,
                      corner_radius=10, font=("Helvetica", 12, "bold"),
                      height=40).pack(padx=28, pady=(10, 8), fill="x")

        ctk.CTkLabel(self, text="Default credentials:  admin  /  elroi2026",
                     font=("Helvetica", 9), text_color=GREY).pack(pady=(0, 12))

    def _login(self):
        user = self.e_user.get().strip()
        pwd  = self.e_pass.get()
        if db.verify_login(user, pwd):
            self.grab_release()
            self.destroy()
            self.on_success()
        else:
            self.err_lbl.configure(text="Incorrect username or password.")
            self.e_pass.delete(0, "end")
            self.e_pass.focus_set()

    def _on_close(self):
        self.master.destroy()


class ChangePasswordDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Change Credentials")
        self.geometry("380x420")
        self.resizable(False, False)
        self.configure(fg_color=LIGHT)
        self.grab_set()
        self.lift()
        self.focus_force()
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Change Username & Password",
                     font=("Helvetica", 13, "bold"), text_color=NAVY).pack(pady=(20, 4))
        ctk.CTkFrame(self, height=2, fg_color=GOLD).pack(fill="x", padx=20, pady=(0, 16))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(padx=30, fill="x")

        ctk.CTkLabel(form, text=f"Current username:  {db.get_username()}",
                     font=("Helvetica", 10), text_color=GREY).pack(anchor="w", pady=(0, 12))

        ctk.CTkLabel(form, text="New Username", font=("Helvetica", 10),
                     text_color=GREY).pack(anchor="w", pady=(0, 2))
        self.e_user = ctk.CTkEntry(form, corner_radius=8, border_color=MID,
                                   fg_color=WHITE, font=("Helvetica", 11))
        self.e_user.pack(fill="x")
        self.e_user.insert(0, db.get_username())

        ctk.CTkLabel(form, text="New Password", font=("Helvetica", 10),
                     text_color=GREY).pack(anchor="w", pady=(12, 2))
        self.e_pass = ctk.CTkEntry(form, corner_radius=8, border_color=MID,
                                   fg_color=WHITE, font=("Helvetica", 11), show="●")
        self.e_pass.pack(fill="x")

        ctk.CTkLabel(form, text="Confirm Password", font=("Helvetica", 10),
                     text_color=GREY).pack(anchor="w", pady=(12, 2))
        self.e_confirm = ctk.CTkEntry(form, corner_radius=8, border_color=MID,
                                      fg_color=WHITE, font=("Helvetica", 11), show="●")
        self.e_confirm.pack(fill="x")

        self.status = ctk.CTkLabel(form, text="", font=("Helvetica", 10), text_color=RED)
        self.status.pack(pady=(10, 0))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=16)
        ctk.CTkButton(btn_row, text="Save Changes", command=self._save,
                      fg_color=NAVY, hover_color=GOLD, text_color=WHITE,
                      corner_radius=8, font=("Helvetica", 11, "bold"), width=140).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_row, text="Cancel", command=self.destroy,
                      fg_color=MID, hover_color=GREY, text_color=NAVY,
                      corner_radius=8, font=("Helvetica", 11, "bold"), width=100).pack(side="left")

    def _save(self):
        new_user = self.e_user.get().strip()
        new_pass = self.e_pass.get()
        confirm  = self.e_confirm.get()
        if new_pass != confirm:
            self.status.configure(text="Passwords do not match.", text_color=RED)
            return
        ok, msg = db.change_credentials(new_user, new_pass)
        self.status.configure(text=msg, text_color=GREEN if ok else RED)
        if ok:
            self.after(1200, self.destroy)


class ElroiApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Elroi Favoured School — Management System")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(fg_color=LIGHT)
        self.withdraw()          # hidden until login succeeds

        db.init_db()
        LoginWindow(self._on_login_success)

    def _on_login_success(self):
        self._build_main()
        self.deiconify()
        self.lift()
        self.focus_force()

    def _build_main(self):
        # Clear any previous widgets (e.g. after logout)
        for w in self.winfo_children():
            w.destroy()

        header = ctk.CTkFrame(self, fg_color=NAVY, height=56, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="ELROI FAVOURED SCHOOL",
                     font=("Helvetica", 18, "bold"), text_color=GOLD).pack(side="left", padx=20, pady=8)
        ctk.CTkLabel(header, text="Management System  |  2026",
                     font=("Helvetica", 10), text_color=MID).pack(side="left", pady=8)

        right_hdr = ctk.CTkFrame(header, fg_color="transparent")
        right_hdr.pack(side="right", padx=16)
        ctk.CTkLabel(right_hdr, text=f"👤  {db.get_username()}",
                     font=("Helvetica", 10), text_color=MID).pack(side="left", padx=(0, 12))
        ctk.CTkButton(right_hdr, text="⚙ Change Password",
                      command=self._change_password,
                      fg_color="transparent", hover_color="#2a3f5e",
                      text_color=MID, border_width=1, border_color=MID,
                      corner_radius=6, font=("Helvetica", 9), width=130, height=28).pack(side="left", padx=(0, 8))
        ctk.CTkButton(right_hdr, text="🔒 Logout",
                      command=self._logout,
                      fg_color="transparent", hover_color="#2a3f5e",
                      text_color=GOLD, border_width=1, border_color=GOLD,
                      corner_radius=6, font=("Helvetica", 9, "bold"), width=80, height=28).pack(side="left")

        self.tab = ctk.CTkTabview(self, fg_color=LIGHT,
                                  segmented_button_fg_color=NAVY,
                                  segmented_button_selected_color=GOLD,
                                  segmented_button_selected_hover_color=GOLD,
                                  segmented_button_unselected_color=NAVY,
                                  segmented_button_unselected_hover_color="#2a3f5e",
                                  text_color=WHITE, corner_radius=0)
        self.tab.pack(fill="both", expand=True)

        for t in ["Students", "Payments", "Fee Settings", "Requirements", "Miscellaneous", "Reports"]:
            self.tab.add(t)

        StudentsTab(self.tab.tab("Students")).pack(fill="both", expand=True)
        PaymentsTab(self.tab.tab("Payments")).pack(fill="both", expand=True)
        FeeSettingsTab(self.tab.tab("Fee Settings")).pack(fill="both", expand=True)
        RequirementsTab(self.tab.tab("Requirements")).pack(fill="both", expand=True)
        MiscTab(self.tab.tab("Miscellaneous")).pack(fill="both", expand=True)
        ReportsTab(self.tab.tab("Reports")).pack(fill="both", expand=True)

    def _change_password(self):
        ChangePasswordDialog(self)

    def _logout(self):
        if messagebox.askyesno("Logout", "Log out and return to the login screen?"):
            self.withdraw()
            LoginWindow(self._on_login_success)


if __name__ == "__main__":
    app = ElroiApp()
    app.mainloop()
