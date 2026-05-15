import sqlite3
import os
import hashlib
from datetime import datetime

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_BASE_DIR, "data", "elroi.db")

CLASSES = ["PlayGroup", "PP1", "PP2", "Grade 1", "Grade 2", "Grade 3", "Grade 4"]
TERMS = ["Term I", "Term II", "Term III"]

# Class sort order for display
CLASS_ORDER = {c: i for i, c in enumerate(CLASSES)}

# Fee structure
TUITION_FEES = {
    "Term I": {
        "PlayGroup": {"Tuition": 4500, "Admission Fee": 500, "Development Fee": 300},
        "PP1":       {"Tuition": 4500, "Admission Fee": 500, "Development Fee": 300},
        "PP2":       {"Tuition": 4500, "Admission Fee": 500, "Development Fee": 300},
        "Grade 1":   {"Tuition": 5000, "Admission Fee": 500, "Development Fee": 300},
        "Grade 2":   {"Tuition": 5000, "Admission Fee": 500, "Development Fee": 300},
        "Grade 3":   {"Tuition": 5000, "Admission Fee": 500, "Development Fee": 300},
        "Grade 4":   {"Tuition": 5000, "Admission Fee": 500, "Development Fee": 300},
    },
    "Term II": {
        "PlayGroup": {"Tuition": 4500},
        "PP1":       {"Tuition": 4500},
        "PP2":       {"Tuition": 4500},
        "Grade 1":   {"Tuition": 5000},
        "Grade 2":   {"Tuition": 5000},
        "Grade 3":   {"Tuition": 5000},
        "Grade 4":   {"Tuition": 5000},
    },
    "Term III": {
        "PlayGroup": {"Tuition": 4500},
        "PP1":       {"Tuition": 4500},
        "PP2":       {"Tuition": 4500},
        "Grade 1":   {"Tuition": 5000},
        "Grade 2":   {"Tuition": 5000},
        "Grade 3":   {"Tuition": 5000},
        "Grade 4":   {"Tuition": 5000},
    },
}

# For new students joining mid-year (Term II/III) — they also pay Admission + Development Fee
NEW_STUDENT_EXTRAS = {"Admission Fee": 500, "Development Fee": 300}


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    c = conn.cursor()

    # Students table
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id   TEXT PRIMARY KEY,
            name         TEXT NOT NULL,
            class        TEXT NOT NULL,
            dob          TEXT,
            teacher      TEXT,
            year         INTEGER DEFAULT 2026,
            is_new_student INTEGER DEFAULT 0,
            join_term    TEXT DEFAULT 'Term I',
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Fee categories settings — dynamic; is_fixed=1 means cannot be deleted/renamed
    c.execute("""
        CREATE TABLE IF NOT EXISTS fee_settings (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT UNIQUE NOT NULL,
            amount   REAL NOT NULL,
            is_fixed INTEGER NOT NULL DEFAULT 0
        )
    """)

    # Student fees ledger — one row per student per fee-component per term
    c.execute("""
        CREATE TABLE IF NOT EXISTS student_fees (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  TEXT NOT NULL,
            term        TEXT NOT NULL,
            category    TEXT NOT NULL,
            total_owed  REAL NOT NULL DEFAULT 0,
            total_paid  REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            UNIQUE(student_id, term, category)
        )
    """)

    # Payment transactions log
    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  TEXT NOT NULL,
            term        TEXT NOT NULL,
            category    TEXT NOT NULL,
            amount      REAL NOT NULL,
            paid_date   TEXT,
            paid_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes       TEXT,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)
    # Add paid_date column if upgrading from old schema
    try:
        c.execute("ALTER TABLE payments ADD COLUMN paid_date TEXT")
    except Exception:
        pass

    # Promotion history
    c.execute("""
        CREATE TABLE IF NOT EXISTS promotion_history (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id   TEXT NOT NULL,
            from_class   TEXT NOT NULL,
            to_class     TEXT NOT NULL,
            promoted_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Requirements master list
    c.execute("""
        CREATE TABLE IF NOT EXISTS requirements (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            quantity    INTEGER NOT NULL DEFAULT 1,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Per-student requirement tracking — flat, no terms
    c.execute("""
        CREATE TABLE IF NOT EXISTS student_requirements (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id     TEXT NOT NULL,
            requirement_id INTEGER NOT NULL,
            qty_brought    INTEGER NOT NULL DEFAULT 0,
            updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, requirement_id)
        )
    """)

    # Admin credentials — single admin account
    c.execute("""
        CREATE TABLE IF NOT EXISTS admin_credentials (
            id            INTEGER PRIMARY KEY CHECK (id = 1),
            username      TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    # Seed default credentials (admin / elroi2026) if not set yet
    existing = c.execute("SELECT id FROM admin_credentials WHERE id=1").fetchone()
    if not existing:
        c.execute(
            "INSERT INTO admin_credentials (id, username, password_hash) VALUES (1, ?, ?)",
            ("admin", _hash("elroi2026"))
        )

    conn.commit()
    conn.close()


def _hash(password):
    """SHA-256 hash a password string."""
    return hashlib.sha256(password.encode()).hexdigest()


# ── Students ────────────────────────────────────────────────────────────────

def generate_student_id():
    """Generate next ID in format EFS/001/2026, EFS/002/2026, etc."""
    year = datetime.now().year
    conn = get_connection()
    # Find all IDs for this year matching the pattern
    rows = conn.execute(
        "SELECT student_id FROM students WHERE student_id LIKE ?",
        (f"EFS/%/{year}",)
    ).fetchall()
    conn.close()
    max_seq = 0
    for row in rows:
        try:
            parts = row["student_id"].split("/")
            seq = int(parts[1])
            if seq > max_seq:
                max_seq = seq
        except (IndexError, ValueError):
            pass
    return f"EFS/{str(max_seq + 1).zfill(3)}/{year}"


def add_student(student_id, name, cls, dob, teacher, is_new_student=False, join_term="Term I"):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO students (student_id,name,class,dob,teacher,year,is_new_student,join_term) VALUES (?,?,?,?,?,2026,?,?)",
            (student_id, name, cls, dob or None, teacher, 1 if is_new_student else 0, join_term)
        )
        conn.commit()
        _init_student_fees(conn, student_id, cls, is_new_student, join_term)
        return True, "Student added successfully."
    except sqlite3.IntegrityError:
        return False, "Student ID already exists."
    finally:
        conn.close()


def _init_student_fees(conn, student_id, cls, is_new_student, join_term):
    """Create fee rows for every applicable term/category for a student."""
    terms_to_init = TERMS if not is_new_student else TERMS[TERMS.index(join_term):]

    for term in terms_to_init:
        fee_structure = dict(TUITION_FEES[term][cls])  # copy

        # New students joining Term II/III also pay Admission + Development Fee
        if is_new_student and term == join_term and join_term != "Term I":
            fee_structure.update(NEW_STUDENT_EXTRAS)

        for category, amount in fee_structure.items():
            conn.execute(
                "INSERT OR IGNORE INTO student_fees (student_id,term,category,total_owed,total_paid) VALUES (?,?,?,?,0)",
                (student_id, term, category, amount)
            )

    conn.commit()


def get_all_students():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM students").fetchall()
    conn.close()
    students = [dict(r) for r in rows]
    students.sort(key=lambda s: (CLASS_ORDER.get(s["class"], 99), s["student_id"]))
    return students


def get_students_by_class(cls):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM students WHERE class=? ORDER BY name", (cls,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_student(student_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM students WHERE student_id=?", (student_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_student(student_id, name, cls, dob, teacher):
    conn = get_connection()
    conn.execute(
        "UPDATE students SET name=?, class=?, dob=?, teacher=? WHERE student_id=?",
        (name, cls, dob or None, teacher, student_id)
    )
    conn.commit()
    conn.close()


def delete_student(student_id):
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("DELETE FROM student_requirements WHERE student_id=?", (student_id,))
    conn.execute("DELETE FROM payments WHERE student_id=?", (student_id,))
    conn.execute("DELETE FROM student_fees WHERE student_id=?", (student_id,))
    conn.execute("DELETE FROM promotion_history WHERE student_id=?", (student_id,))
    conn.execute("DELETE FROM students WHERE student_id=?", (student_id,))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    conn.close()


def update_teacher(cls, teacher_name):
    conn = get_connection()
    conn.execute("UPDATE students SET teacher=? WHERE class=?", (teacher_name, cls))
    conn.commit()
    conn.close()


# ── Fee Settings ────────────────────────────────────────────────────────────

def add_fee_category(category, amount):
    """Add a new dynamic fee category (not fixed). Returns (ok, msg)."""
    category = category.strip()
    if not category:
        return False, "Category name cannot be empty."
    protected = {"Tuition", "Admission Fee", "Development Fee"}
    if category in protected:
        return False, f"'{category}' is a reserved tuition name."
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO fee_settings (category, amount, is_fixed) VALUES (?, ?, 0)",
            (category, amount)
        )
        conn.commit()
        return True, f"Category '{category}' added."
    except sqlite3.IntegrityError:
        return False, f"Category '{category}' already exists."
    finally:
        conn.close()


def set_fee_setting(category, amount):
    """Update the amount for an existing category."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO fee_settings (category, amount, is_fixed) VALUES (?, ?, 0)"
        " ON CONFLICT(category) DO UPDATE SET amount=?",
        (category, amount, amount)
    )
    conn.commit()
    conn.close()


def delete_fee_category(category):
    """Delete a dynamic fee category. Fixed categories cannot be deleted. Returns (ok, msg)."""
    conn = get_connection()
    row = conn.execute("SELECT is_fixed FROM fee_settings WHERE category=?", (category,)).fetchone()
    if not row:
        conn.close()
        return False, "Category not found."
    if row["is_fixed"]:
        conn.close()
        return False, f"'{category}' is a fixed category and cannot be deleted."
    # Remove from settings and from all student fee rows that have no payment yet
    conn.execute("DELETE FROM fee_settings WHERE category=?", (category,))
    conn.execute(
        "DELETE FROM student_fees WHERE category=? AND total_paid=0",
        (category,)
    )
    conn.commit()
    conn.close()
    return True, f"Category '{category}' deleted."


def get_fee_settings():
    conn = get_connection()
    rows = conn.execute("SELECT category, amount, is_fixed FROM fee_settings ORDER BY is_fixed DESC, category").fetchall()
    conn.close()
    return [{"category": r["category"], "amount": r["amount"], "is_fixed": r["is_fixed"]} for r in rows]


# ── Student Fees & Payments ─────────────────────────────────────────────────

def get_student_fees(student_id, term=None):
    conn = get_connection()
    if term:
        rows = conn.execute(
            "SELECT * FROM student_fees WHERE student_id=? AND term=? ORDER BY term,category",
            (student_id, term)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM student_fees WHERE student_id=? ORDER BY term,category",
            (student_id,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def record_payment(student_id, term, category, amount, notes="", paid_date=None):
    """Record a payment with automatic carryover: older term balances are cleared first.
    Returns (ok, summary_message)."""
    if amount <= 0:
        return False, "Amount must be greater than 0."
    if not paid_date:
        paid_date = datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()

    # Gather all unpaid balances across all terms, ordered oldest first
    all_fees = conn.execute(
        """SELECT term, category, total_owed, total_paid
           FROM student_fees WHERE student_id=?
           ORDER BY CASE term
               WHEN 'Term I'   THEN 1
               WHEN 'Term II'  THEN 2
               WHEN 'Term III' THEN 3 END,
           category""",
        (student_id,)
    ).fetchall()

    # Determine which terms come before the selected term
    term_order = {t: i for i, t in enumerate(TERMS)}
    selected_order = term_order.get(term, 0)

    # Build list: first all earlier-term rows with balance, then the selected term's chosen category
    carry_targets = []
    for f in all_fees:
        f_order = term_order.get(f["term"], 0)
        bal = f["total_owed"] - f["total_paid"]
        if f_order < selected_order and bal > 0:
            carry_targets.append(dict(f))

    # Now add the actual selected category for this term
    target_fee = conn.execute(
        "SELECT * FROM student_fees WHERE student_id=? AND term=? AND category=?",
        (student_id, term, category)
    ).fetchone()
    if not target_fee:
        conn.close()
        return False, "Fee record not found."

    target_bal = target_fee["total_owed"] - target_fee["total_paid"]
    carry_targets.append({"term": term, "category": category,
                          "total_owed": target_fee["total_owed"],
                          "total_paid": target_fee["total_paid"]})

    # Check total outstanding across carry targets is enough to absorb
    total_outstanding = sum(f["total_owed"] - f["total_paid"] for f in carry_targets)
    if amount > total_outstanding + 0.01:
        conn.close()
        return False, f"Amount exceeds total outstanding balance of Ksh {total_outstanding:,.0f}."

    remaining = amount
    summary_parts = []

    for f in carry_targets:
        if remaining <= 0:
            break
        bal = f["total_owed"] - f["total_paid"]
        if bal <= 0:
            continue
        apply = min(remaining, bal)
        conn.execute(
            "UPDATE student_fees SET total_paid=total_paid+? WHERE student_id=? AND term=? AND category=?",
            (apply, student_id, f["term"], f["category"])
        )
        conn.execute(
            "INSERT INTO payments (student_id,term,category,amount,paid_date,notes) VALUES (?,?,?,?,?,?)",
            (student_id, f["term"], f["category"], apply, paid_date, notes)
        )
        summary_parts.append(f"Ksh {apply:,.0f} → {f['term']} {f['category']}")
        remaining -= apply

    conn.commit()
    conn.close()

    summary = "Payment recorded. " + " | ".join(summary_parts)
    return True, summary


# ── Promotion ───────────────────────────────────────────────────────────────

def promote_all_students():
    """Promote every student up one class. Grade 4 students are removed (left school)."""
    conn = get_connection()
    students = conn.execute("SELECT * FROM students").fetchall()
    promoted = []
    left = []

    for s in students:
        current = s["class"]
        if current not in CLASSES:
            continue
        idx = CLASSES.index(current)
        if idx < len(CLASSES) - 1:
            next_cls = CLASSES[idx + 1]
            conn.execute(
                "UPDATE students SET class=?, join_term='Term I', is_new_student=0 WHERE student_id=?",
                (next_cls, s["student_id"])
            )
            conn.execute(
                "INSERT INTO promotion_history (student_id,from_class,to_class) VALUES (?,?,?)",
                (s["student_id"], current, next_cls)
            )
            _init_student_fees(conn, s["student_id"], next_cls, False, "Term I")
            promoted.append(s["student_id"])
        else:
            # Grade 4 → completed, remove from system
            conn.execute("DELETE FROM students WHERE student_id=?", (s["student_id"],))
            left.append(s["student_id"])

    conn.commit()
    conn.close()
    return promoted, left


def assign_extra_fee(student_id, category, terms):
    """Assign an extra fee category to a specific student for chosen terms.
    terms: list of term strings e.g. ['Term I', 'Term III']
    Returns (ok, msg)."""
    conn = get_connection()
    setting = conn.execute("SELECT amount FROM fee_settings WHERE category=?", (category,)).fetchone()
    if not setting:
        conn.close()
        return False, f"Category '{category}' not found in fee settings."
    amount = setting["amount"]
    added = []
    for term in terms:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO student_fees (student_id,term,category,total_owed,total_paid) VALUES (?,?,?,?,0)",
                (student_id, term, category, amount)
            )
            added.append(term)
        except Exception:
            pass
    conn.commit()
    conn.close()
    return True, f"'{category}' assigned for {', '.join(added)}."


def remove_extra_fee(student_id, category, term):
    """Remove an extra fee from a student for a specific term.
    Cannot remove if any payment has been made. Returns (ok, msg)."""
    conn = get_connection()
    row = conn.execute(
        "SELECT total_paid FROM student_fees WHERE student_id=? AND term=? AND category=?",
        (student_id, term, category)
    ).fetchone()
    if not row:
        conn.close()
        return False, "Fee record not found."
    if row["total_paid"] > 0:
        conn.close()
        return False, f"Cannot remove — payment of {row['total_paid']:,.0f} already recorded."
    conn.execute(
        "DELETE FROM student_fees WHERE student_id=? AND term=? AND category=?",
        (student_id, term, category)
    )
    conn.commit()
    conn.close()
    return True, f"'{category}' removed for {term}."


def get_student_extra_fees(student_id):
    """Return only the extra (non-tuition) fee rows for a student."""
    tuition_cats = {"Tuition", "Admission Fee", "Development Fee"}
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM student_fees WHERE student_id=? ORDER BY term, category",
        (student_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows if r["category"] not in tuition_cats]


def get_payment_history(student_id, term=None, category=None):
    conn = get_connection()
    query = "SELECT * FROM payments WHERE student_id=?"
    params = [student_id]
    if term:
        query += " AND term=?"
        params.append(term)
    if category:
        query += " AND category=?"
        params.append(category)
    query += " ORDER BY paid_date DESC, paid_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_student_balance_summary(student_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT SUM(total_owed) as owed, SUM(total_paid) as paid FROM student_fees WHERE student_id=?",
        (student_id,)
    ).fetchone()
    conn.close()
    owed = row["owed"] or 0
    paid = row["paid"] or 0
    return {"total_owed": owed, "total_paid": paid, "total_balance": owed - paid}


def add_exam_fee(student_id, term, exam_name, amount):
    exam_name = exam_name.strip()
    if not exam_name:
        return False, "Exam name cannot be empty."
    if amount <= 0:
        return False, "Amount must be greater than 0."
    category = f"Exam: {exam_name}"
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO student_fees (student_id,term,category,total_owed,total_paid) VALUES (?,?,?,?,0)",
            (student_id, term, category, amount)
        )
        conn.commit()
        return True, f"Exam '{exam_name}' added for {term}."
    except sqlite3.IntegrityError:
        return False, f"Exam '{exam_name}' already exists for {term}."
    finally:
        conn.close()


# ── Salaries ──────────────────────────────────────────────────────────────────

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def init_salary_tables(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL UNIQUE,
            salary     REAL NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS salary_payments (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            month      TEXT NOT NULL DEFAULT '',
            amount     REAL NOT NULL,
            paid_date  TEXT,
            notes      TEXT,
            paid_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (teacher_id) REFERENCES teachers(id)
        )
    """)
    conn.commit()
    cols = [r[1] for r in conn.execute("PRAGMA table_info(salary_payments)").fetchall()]
    if "term" in cols and "month" not in cols:
        conn.execute("ALTER TABLE salary_payments RENAME TO _sp_old")
        conn.execute("""
            CREATE TABLE salary_payments (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                month      TEXT NOT NULL DEFAULT '',
                amount     REAL NOT NULL,
                paid_date  TEXT,
                notes      TEXT,
                paid_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES teachers(id)
            )
        """)
        conn.execute("""
            INSERT INTO salary_payments (id,teacher_id,month,amount,paid_date,notes,paid_at)
            SELECT id,teacher_id,COALESCE(term,''),amount,paid_date,notes,paid_at FROM _sp_old
        """)
        conn.execute("DROP TABLE _sp_old")
        conn.commit()


def get_teachers():
    conn = get_connection()
    init_salary_tables(conn)
    rows = conn.execute("SELECT * FROM teachers ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_teacher(name, salary):
    name = name.strip()
    if not name:
        return False, "Teacher name cannot be empty."
    conn = get_connection()
    init_salary_tables(conn)
    try:
        conn.execute("INSERT INTO teachers (name, salary) VALUES (?, ?)", (name, salary))
        conn.commit()
        return True, f"Teacher '{name}' added."
    except sqlite3.IntegrityError:
        return False, f"Teacher '{name}' already exists."
    finally:
        conn.close()


def update_teacher_salary(teacher_id, name, salary):
    conn = get_connection()
    init_salary_tables(conn)
    conn.execute("UPDATE teachers SET name=?, salary=? WHERE id=?", (name, salary, teacher_id))
    conn.commit()
    conn.close()
    return True, "Updated."


def delete_teacher(teacher_id):
    conn = get_connection()
    init_salary_tables(conn)
    conn.execute("DELETE FROM salary_payments WHERE teacher_id=?", (teacher_id,))
    conn.execute("DELETE FROM teachers WHERE id=?", (teacher_id,))
    conn.commit()
    conn.close()


def record_salary_payment(teacher_id, month, amount, paid_date=None, notes=""):
    if amount <= 0:
        return False, "Amount must be greater than 0."
    conn = get_connection()
    init_salary_tables(conn)
    teacher = conn.execute("SELECT * FROM teachers WHERE id=?", (teacher_id,)).fetchone()
    if not teacher:
        conn.close()
        return False, "Teacher not found."
    paid = conn.execute(
        "SELECT SUM(amount) as total FROM salary_payments WHERE teacher_id=? AND month=?",
        (teacher_id, month)
    ).fetchone()["total"] or 0
    balance = teacher["salary"] - paid
    if amount > balance + 0.01:
        conn.close()
        return False, f"Exceeds remaining salary balance of Ksh {balance:,.0f} for {month}."
    if not paid_date:
        paid_date = datetime.now().strftime("%Y-%m-%d")
    conn.execute(
        "INSERT INTO salary_payments (teacher_id,month,amount,paid_date,notes) VALUES (?,?,?,?,?)",
        (teacher_id, month, amount, paid_date, notes)
    )
    conn.commit()
    conn.close()
    return True, "Salary payment recorded."


def get_salary_payments(teacher_id=None, month=None):
    conn = get_connection()
    init_salary_tables(conn)
    query = """SELECT sp.*, t.name as teacher_name, t.salary as full_salary
               FROM salary_payments sp JOIN teachers t ON sp.teacher_id=t.id WHERE 1=1"""
    params = []
    if teacher_id:
        query += " AND sp.teacher_id=?"
        params.append(teacher_id)
    if month:
        query += " AND sp.month=?"
        params.append(month)
    query += " ORDER BY sp.paid_date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_teacher_salary_summary(teacher_id, month):
    conn = get_connection()
    init_salary_tables(conn)
    teacher = conn.execute("SELECT * FROM teachers WHERE id=?", (teacher_id,)).fetchone()
    paid_row = conn.execute(
        "SELECT SUM(amount) as total FROM salary_payments WHERE teacher_id=? AND month=?",
        (teacher_id, month)
    ).fetchone()
    conn.close()
    if not teacher:
        return None
    paid = paid_row["total"] or 0
    return {"salary": teacher["salary"], "paid": paid, "balance": teacher["salary"] - paid}


# ── Miscellaneous Expenses ────────────────────────────────────────────────────

def init_misc_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS misc_expenses (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            term       TEXT NOT NULL,
            item       TEXT NOT NULL,
            amount     REAL NOT NULL,
            expense_date TEXT,
            notes      TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def add_misc_expense(term, item, amount, expense_date=None, notes=""):
    item = item.strip()
    if not item:
        return False, "Item name cannot be empty."
    if amount <= 0:
        return False, "Amount must be greater than 0."
    if not expense_date:
        expense_date = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    init_misc_table(conn)
    conn.execute(
        "INSERT INTO misc_expenses (term,item,amount,expense_date,notes) VALUES (?,?,?,?,?)",
        (term, item, amount, expense_date, notes)
    )
    conn.commit()
    conn.close()
    return True, f"Expense '{item}' recorded."


def get_misc_expenses(term=None):
    conn = get_connection()
    init_misc_table(conn)
    if term:
        rows = conn.execute(
            "SELECT * FROM misc_expenses WHERE term=? ORDER BY expense_date DESC",
            (term,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM misc_expenses ORDER BY term, expense_date DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_misc_expense(expense_id):
    conn = get_connection()
    init_misc_table(conn)
    conn.execute("DELETE FROM misc_expenses WHERE id=?", (expense_id,))
    conn.commit()
    conn.close()
    return True, "Expense deleted."


def get_misc_summary():
    """Return total per term."""
    conn = get_connection()
    init_misc_table(conn)
    rows = conn.execute(
        "SELECT term, SUM(amount) as total FROM misc_expenses GROUP BY term"
    ).fetchall()
    conn.close()
    return {r["term"]: r["total"] for r in rows}


# ── Requirements ─────────────────────────────────────────────────────────────

def add_requirement(name, quantity=1):
    name = name.strip()
    if not name:
        return False, "Name cannot be empty."
    if quantity < 1:
        return False, "Quantity must be at least 1."
    conn = get_connection()
    try:
        conn.execute("INSERT INTO requirements (name, quantity) VALUES (?,?)", (name, quantity))
        conn.commit()
        return True, f"'{name}' added."
    except sqlite3.IntegrityError:
        return False, f"'{name}' already exists."
    finally:
        conn.close()


def get_requirements():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM requirements ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_requirement(req_id, name, quantity):
    name = name.strip()
    if not name:
        return False, "Name cannot be empty."
    conn = get_connection()
    conn.execute("UPDATE requirements SET name=?, quantity=? WHERE id=?", (name, quantity, req_id))
    conn.commit()
    conn.close()
    return True, "Updated."


def delete_requirement(req_id):
    conn = get_connection()
    conn.execute("DELETE FROM student_requirements WHERE requirement_id=?", (req_id,))
    conn.execute("DELETE FROM requirements WHERE id=?", (req_id,))
    conn.commit()
    conn.close()
    return True, "Deleted."


def get_student_requirements(student_id):
    """Return all requirements with how many this student has brought."""
    conn = get_connection()
    reqs = conn.execute("SELECT * FROM requirements ORDER BY name").fetchall()
    result = []
    for r in reqs:
        sr = conn.execute(
            "SELECT qty_brought FROM student_requirements WHERE student_id=? AND requirement_id=?",
            (student_id, r["id"])
        ).fetchone()
        result.append({
            "id": r["id"],
            "name": r["name"],
            "required": r["quantity"],
            "brought": sr["qty_brought"] if sr else 0
        })
    conn.close()
    return result


def set_student_requirement(student_id, req_id, qty_brought):
    """Update or insert a student requirement — no terms, flat tracking."""
    conn = get_connection()
    conn.execute(
        "UPDATE student_requirements SET qty_brought=?, updated_at=CURRENT_TIMESTAMP "
        "WHERE student_id=? AND requirement_id=?",
        (qty_brought, student_id, req_id)
    )
    if conn.execute(
        "SELECT COUNT(*) FROM student_requirements WHERE student_id=? AND requirement_id=?",
        (student_id, req_id)
    ).fetchone()[0] == 0:
        conn.execute(
            "INSERT INTO student_requirements (student_id, requirement_id, qty_brought) VALUES (?,?,?)",
            (student_id, req_id, qty_brought)
        )
    conn.commit()
    conn.close()


def verify_login(username, password):
    """Return True if username+password match stored credentials."""
    conn = get_connection()
    row = conn.execute("SELECT username, password_hash FROM admin_credentials WHERE id=1").fetchone()
    conn.close()
    if not row:
        return False
    return row["username"] == username and row["password_hash"] == _hash(password)


def get_username():
    conn = get_connection()
    row = conn.execute("SELECT username FROM admin_credentials WHERE id=1").fetchone()
    conn.close()
    return row["username"] if row else "admin"


def change_credentials(new_username, new_password):
    """Update username and password. Returns (ok, msg)."""
    new_username = new_username.strip()
    if not new_username:
        return False, "Username cannot be empty."
    if len(new_password) < 6:
        return False, "Password must be at least 6 characters."
    conn = get_connection()
    conn.execute(
        "UPDATE admin_credentials SET username=?, password_hash=? WHERE id=1",
        (new_username, _hash(new_password))
    )
    conn.commit()
    conn.close()
    return True, "Credentials updated successfully."


