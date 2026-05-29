# Elroi Favoured School — Management System
**Created by Favour Maina**

---

## First-Time Setup

Open a terminal / command prompt in this folder and run:

```
pip install -r requirements.txt
```

That installs all three libraries needed:
- `customtkinter` — the desktop UI
- `reportlab` — PDF generation
- `Pillow` — image support

---

## Running the App

```
python main.py
```

Or double-click `main.py` in VS Code and press **Run**.

---

## File Structure

```
elroi_school/
├── main.py           ← Launch this
├── database.py       ← All data logic (SQLite)
├── reports_gen.py    ← PDF generation
├── requirements.txt
├── data/
│   └── elroi.db      ← Auto-created on first run (your database)
└── reports/          ← All generated PDFs saved here
```

---

## How to Use

### 1. Fee Settings (do this first)
Go to **⚙ Fee Settings** tab:
- **Add** any extra fee category you need — e.g. Lunch, Uniform, Tour, Exam
- Enter the category name and amount per term, then click **+ Add**
- Each category row has its own **Save** button to update the amount
- Click **✕ Delete** to remove a category (only possible if no payments have been made against it)
- Tuition fees are fixed in the system and shown for reference on the right

### 2. Add Students
Go to **👤 Students** tab:
- Fill in Student ID, Name, Class, DOB (optional), Teacher
- For new students joining Term II or III, tick "New student" and pick their joining term
- Click **Add Student**

### 3. Record Payments
Go to **💰 Payments** tab:
- Search for a student by name or ID
- Pick the Term and Fee Category
- Type the amount paid (e.g. `2,500` or `2500`) and click **Record Payment**
- The balance auto-updates immediately

### 4. Generate PDFs
- **📊 Reports** tab → Student Register (per class or whole school)
- **📊 Reports** tab → Payment Report (per class or whole school)
- **💰 Payments** tab → Payment Report for a single student

### 5. Year-End Promotion
Go to **📊 Reports** → **Promote All** after Term III ends.
- Every student moves up one class automatically
- **Grade 2 → Grade 3** (promoted, not removed)
- **Grade 3** students graduate and are removed
- Old payment records are kept in history
- 
The system can also be used on browser by typing the network socket
---

## Notes
- All data is stored in `data/elroi.db` — **back this file up regularly**
- Reports are saved in the `reports/` folder with a timestamp in the filename
- Amounts are displayed as whole numbers with commas (e.g. 1,000)
- The system works fully offline — no internet needed
