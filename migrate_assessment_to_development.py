"""
One-time migration script.
Run this ONCE to rename "Assessment Fee" to "Development Fee" in your database.

Usage:
    python migrate_assessment_to_development.py
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "elroi.db")

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Count rows to be updated
    count_fees = c.execute(
        "SELECT COUNT(*) FROM student_fees WHERE category='Assessment Fee'"
    ).fetchone()[0]
    count_payments = c.execute(
        "SELECT COUNT(*) FROM payments WHERE category='Assessment Fee'"
    ).fetchone()[0]

    print(f"Found {count_fees} student_fees rows with 'Assessment Fee'")
    print(f"Found {count_payments} payment rows with 'Assessment Fee'")

    if count_fees == 0 and count_payments == 0:
        print("Nothing to migrate — already up to date.")
        conn.close()
        return

    # Rename in student_fees
    c.execute(
        "UPDATE student_fees SET category='Development Fee' WHERE category='Assessment Fee'"
    )
    # Rename in payments history
    c.execute(
        "UPDATE payments SET category='Development Fee' WHERE category='Assessment Fee'"
    )

    conn.commit()
    conn.close()

    print("Migration complete!")
    print(f"  - {count_fees} student_fees rows renamed")
    print(f"  - {count_payments} payment rows renamed")
    print("\nYou can delete this script now.")

if __name__ == "__main__":
    migrate()
