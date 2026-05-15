"""
Drop this file into your school system folder (same place as main.py and database.py).
Run it ONCE with:   python fix_assessment_fee.py
Then delete it.
"""

import sqlite3
import os

# Find the database — same folder as this script
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(THIS_DIR, "data", "elroi.db")

print(f"Looking for database at:\n  {DB_PATH}\n")

if not os.path.exists(DB_PATH):
    print("ERROR: Database not found at that path.")
    print("Make sure this script is in the same folder as main.py.")
    input("\nPress Enter to close...")
    exit(1)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Count rows to rename
fees_count = c.execute(
    "SELECT COUNT(*) FROM student_fees WHERE category='Assessment Fee'"
).fetchone()[0]
pay_count = c.execute(
    "SELECT COUNT(*) FROM payments WHERE category='Assessment Fee'"
).fetchone()[0]

print(f"Found {fees_count} fee rows with 'Assessment Fee'")
print(f"Found {pay_count} payment rows with 'Assessment Fee'")

if fees_count == 0 and pay_count == 0:
    print("\nNothing to fix — already showing 'Development Fee' everywhere.")
else:
    c.execute("UPDATE student_fees SET category='Development Fee' WHERE category='Assessment Fee'")
    c.execute("UPDATE payments    SET category='Development Fee' WHERE category='Assessment Fee'")
    conn.commit()
    print(f"\nDone! Renamed {fees_count} fee rows and {pay_count} payment rows.")

conn.close()
print("\nYou can delete this script now.")
input("Press Enter to close...")
