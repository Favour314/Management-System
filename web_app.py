"""
Elroi Favoured School — Web App (Mobile-friendly)
Run with:  python web_app.py
Then open on your phone: http://<your-pc-ip>:5000
Find your PC IP: run  ipconfig  in Command Prompt, look for IPv4 Address
"""

from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, flash
import database as db
import os

app = Flask(__name__)
app.secret_key = "elroi_school_2026_secret"

# ── Helpers ───────────────────────────────────────────────────────────────────

def fmt(n):
    try:
        return f"{int(round(float(n))):,}"
    except:
        return str(n)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ── Base template ─────────────────────────────────────────────────────────────

BASE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#1a2e4a">
<title>Elroi School</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
:root{--navy:#1a2e4a;--gold:#c9a84c;--white:#ffffff;--light:#f5f0e8;--grey:#666;--red:#c0392b;--green:#1e7e34;--mid:#d0c9b8}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--light);color:var(--navy);min-height:100vh;padding-bottom:80px}
.topbar{background:var(--navy);color:var(--gold);padding:14px 16px;font-size:16px;font-weight:700;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;box-shadow:0 2px 8px rgba(0,0,0,.3)}
.topbar .sub{font-size:11px;color:var(--mid);font-weight:400}
.topbar a{color:var(--gold);text-decoration:none;font-size:12px}
.nav{position:fixed;bottom:0;left:0;right:0;background:var(--navy);display:flex;z-index:100;box-shadow:0 -2px 8px rgba(0,0,0,.3)}
.nav a{flex:1;text-align:center;padding:8px 2px 10px;color:var(--mid);text-decoration:none;font-size:9px;font-weight:600;border-top:3px solid transparent;transition:all .2s}
.nav a.active,.nav a:hover{color:var(--gold);border-top-color:var(--gold)}
.nav a span{display:block;font-size:18px;margin-bottom:2px}
.card{background:var(--white);border-radius:12px;margin:12px;padding:16px;box-shadow:0 1px 4px rgba(0,0,0,.08)}
.card h2{font-size:14px;color:var(--navy);margin-bottom:12px;font-weight:700;display:flex;align-items:center;gap:6px}
.card h2::after{content:'';flex:1;height:2px;background:var(--gold);border-radius:2px}
input,select,textarea{width:100%;padding:10px 12px;border:1.5px solid var(--mid);border-radius:8px;font-size:14px;background:var(--white);color:var(--navy);outline:none;appearance:none;-webkit-appearance:none}
input:focus,select:focus{border-color:var(--navy)}
label{display:block;font-size:12px;color:var(--grey);margin-bottom:4px;margin-top:10px}
.btn{display:inline-block;padding:11px 18px;border-radius:8px;font-size:14px;font-weight:700;border:none;cursor:pointer;text-decoration:none;text-align:center}
.btn-navy{background:var(--navy);color:var(--white)}
.btn-gold{background:var(--gold);color:var(--navy)}
.btn-green{background:var(--green);color:var(--white)}
.btn-red{background:var(--red);color:var(--white)}
.btn-block{width:100%;display:block;margin-top:14px}
.btn-sm{padding:6px 12px;font-size:12px;border-radius:6px}
.row{display:flex;gap:8px;align-items:center}
.badge{display:inline-block;padding:3px 8px;border-radius:20px;font-size:11px;font-weight:700}
.badge-green{background:#d4edda;color:var(--green)}
.badge-red{background:#f8d7da;color:var(--red)}
.badge-orange{background:#fff3cd;color:#856404}
.badge-grey{background:#e9ecef;color:var(--grey)}
.table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:var(--navy);color:var(--white);padding:8px 10px;text-align:left;font-size:12px;font-weight:600}
td{padding:8px 10px;border-bottom:1px solid var(--light)}
tr:nth-child(even) td{background:var(--light)}
.alert{padding:10px 14px;border-radius:8px;margin:8px 12px;font-size:13px;font-weight:600}
.alert-green{background:#d4edda;color:var(--green)}
.alert-red{background:#f8d7da;color:var(--red)}
.section-title{font-size:12px;font-weight:700;color:var(--grey);text-transform:uppercase;letter-spacing:.5px;margin:16px 12px 4px}
.student-row{display:flex;align-items:center;padding:12px 14px;background:var(--white);border-bottom:1px solid var(--light);gap:12px}
.student-row:first-child{border-radius:12px 12px 0 0}
.student-row:last-child{border-radius:0 0 12px 12px;border-bottom:none}
.avatar{width:38px;height:38px;border-radius:50%;background:var(--navy);color:var(--gold);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:15px;flex-shrink:0}
.student-info{flex:1;min-width:0}
.student-name{font-weight:700;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.student-sub{font-size:11px;color:var(--grey)}
.stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:0 12px}
.stat-box{background:var(--white);border-radius:10px;padding:14px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.06)}
.stat-num{font-size:22px;font-weight:800;color:var(--navy)}
.stat-label{font-size:11px;color:var(--grey);margin-top:3px}
.back{display:flex;align-items:center;gap:6px;padding:10px 12px;font-size:13px;color:var(--navy);font-weight:600;text-decoration:none}
.back::before{content:'←';font-size:16px}
.fee-row{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--light)}
.fee-row:last-child{border-bottom:none}
.progress-bar{height:6px;background:var(--light);border-radius:3px;overflow:hidden;margin-top:4px}
.progress-fill{height:100%;background:var(--green);border-radius:3px;transition:width .3s}
.chip{display:inline-block;padding:4px 10px;border-radius:20px;font-size:11px;font-weight:600;background:var(--light);color:var(--navy);margin:2px}
.chip.active{background:var(--navy);color:var(--white)}
.payment-item{padding:10px 12px;background:var(--white);border-radius:8px;margin-bottom:6px;border-left:4px solid var(--gold)}
.empty{text-align:center;padding:40px 20px;color:var(--grey);font-size:14px}
</style>
</head>
<body>
<div class="topbar">
  <div>
    <div>ELROI FAVOURED SCHOOL</div>
    <div class="sub">Management System</div>
  </div>
  <a href="/logout">Logout</a>
</div>
{% with messages = get_flashed_messages(with_categories=true) %}
  {% for cat, msg in messages %}
    <div class="alert alert-{{ 'green' if cat == 'success' else 'red' }}">{{ msg }}</div>
  {% endfor %}
{% endwith %}
{{ content | safe }}
<nav class="nav">
  <a href="/" class="{{ 'active' if active=='home' else '' }}"><span>🏠</span>Home</a>
  <a href="/students" class="{{ 'active' if active=='students' else '' }}"><span>👤</span>Students</a>
  <a href="/payments" class="{{ 'active' if active=='payments' else '' }}"><span>💰</span>Payments</a>
  <a href="/fees" class="{{ 'active' if active=='fees' else '' }}"><span>⚙️</span>Fees</a>
  <a href="/more" class="{{ 'active' if active=='more' else '' }}"><span>☰</span>More</a>
</nav>
</body></html>"""

def render(content, active="home", **kwargs):
    from flask import render_template_string
    return render_template_string(BASE, content=content, active=active, **kwargs)

# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET","POST"])
def login():
    error = ""
    if request.method == "POST":
        u = request.form.get("username","").strip()
        p = request.form.get("password","")
        if db.verify_login(u, p):
            session["logged_in"] = True
            session["username"] = u
            return redirect(url_for("home"))
        error = "Incorrect username or password."
    return render_template_string("""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="theme-color" content="#1a2e4a">
<title>Login — Elroi School</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,sans-serif;background:#1a2e4a;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.card{background:#fff;border-radius:16px;padding:28px 24px;width:100%;max-width:360px}
h1{color:#1a2e4a;font-size:20px;margin-bottom:4px}
.sub{color:#666;font-size:13px;margin-bottom:24px}
label{display:block;font-size:12px;color:#666;margin-bottom:4px;margin-top:14px}
input{width:100%;padding:11px 14px;border:1.5px solid #d0c9b8;border-radius:8px;font-size:15px;outline:none}
input:focus{border-color:#1a2e4a}
.btn{width:100%;padding:13px;background:#1a2e4a;color:#fff;border:none;border-radius:8px;font-size:15px;font-weight:700;cursor:pointer;margin-top:20px}
.btn:hover{background:#c9a84c;color:#1a2e4a}
.error{background:#f8d7da;color:#c0392b;padding:10px;border-radius:8px;font-size:13px;margin-top:12px;font-weight:600}
.school{color:#c9a84c;font-size:22px;font-weight:800;letter-spacing:.5px;margin-bottom:6px}
.hint{font-size:11px;color:#999;margin-top:14px;text-align:center}
</style></head>
<body>
<div class="card">
  <div class="school">ELROI</div>
  <h1>Sign In</h1>
  <div class="sub">Favoured School Management</div>
  <form method="POST">
    <label>Username</label>
    <input name="username" value="admin" autocomplete="username">
    <label>Password</label>
    <input name="password" type="password" autocomplete="current-password">
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    <button class="btn" type="submit">Sign In</button>
  </form>
  <div class="hint">Default: admin / elroi2026</div>
</div>
</body></html>""", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ── Home ──────────────────────────────────────────────────────────────────────

@app.route("/")
@login_required
def home():
    students = db.get_all_students()
    total = len(students)
    by_class = {}
    for s in students:
        by_class[s["class"]] = by_class.get(s["class"], 0) + 1

    # Quick balance stats
    conn = db.get_connection()
    owing = conn.execute(
        "SELECT COUNT(DISTINCT student_id) as c FROM student_fees WHERE total_owed > total_paid"
    ).fetchone()["c"]
    conn.close()

    stats = f"""
<div style="background:var(--navy);color:var(--gold);padding:16px;margin-bottom:4px">
  <div style="font-size:13px;opacity:.8">Welcome back, {session.get('username','')}</div>
</div>
<div class="stat-grid" style="margin-top:12px">
  <div class="stat-box"><div class="stat-num">{total}</div><div class="stat-label">Students</div></div>
  <div class="stat-box"><div class="stat-num">{len(by_class)}</div><div class="stat-label">Classes</div></div>
  <div class="stat-box"><div class="stat-num">{owing}</div><div class="stat-label">With Balance</div></div>
  <div class="stat-box"><div class="stat-num">{sum(by_class.get(c,0) for c in ['Grade 3','Grade 4'])}</div><div class="stat-label">Upper Grades</div></div>
</div>
<div class="section-title">Classes</div>
<div class="card" style="padding:0;overflow:hidden">"""

    for cls in db.CLASSES:
        count = by_class.get(cls, 0)
        stats += f"""<a href="/students?class={cls}" style="text-decoration:none">
  <div class="student-row">
    <div class="avatar">{cls[0]}</div>
    <div class="student-info">
      <div class="student-name">{cls}</div>
      <div class="student-sub">{count} student{'s' if count!=1 else ''}</div>
    </div>
    <div style="color:var(--gold);font-size:18px">›</div>
  </div></a>"""
    stats += "</div>"

    # Quick links
    stats += """
<div class="section-title">Quick Actions</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:0 12px 12px">
  <a href="/students/add" class="btn btn-navy btn-block" style="margin-top:0;text-align:center">+ Add Student</a>
  <a href="/payments" class="btn btn-gold btn-block" style="margin-top:0;text-align:center">💰 Payments</a>
  <a href="/reports" class="btn btn-navy btn-block" style="margin-top:0;background:#744210;text-align:center">📄 Reports</a>
  <a href="/misc" class="btn btn-navy btn-block" style="margin-top:0;background:#276749;text-align:center">📋 Expenses</a>
</div>"""
    return render(stats, "home")

# ── Students ──────────────────────────────────────────────────────────────────

@app.route("/students")
@login_required
def students():
    cls_filter = request.args.get("class","")
    search = request.args.get("q","").lower()
    all_s = db.get_all_students()
    if cls_filter:
        all_s = [s for s in all_s if s["class"] == cls_filter]
    if search:
        all_s = [s for s in all_s if search in s["name"].lower() or search in s["student_id"].lower()]

    title = cls_filter if cls_filter else "All Students"
    html = f"""
<a href="/" class="back">Home</a>
<div style="padding:0 12px 8px;display:flex;gap:8px">
  <input style="flex:1" type="text" placeholder="Search name or ID..." value="{search}"
    oninput="window.location='/students?{'class='+cls_filter+'&' if cls_filter else ''}q='+this.value">
  <a href="/students/add" class="btn btn-navy btn-sm" style="white-space:nowrap">+ Add</a>
</div>
<div class="section-title">{title} · {len(all_s)} students</div>
<div class="card" style="padding:0;overflow:hidden">"""

    if not all_s:
        html += '<div class="empty">No students found</div>'
    for s in all_s:
        initials = "".join(w[0] for w in s["name"].split()[:2]).upper()
        html += f"""<a href="/student/{s['student_id']}" style="text-decoration:none">
  <div class="student-row">
    <div class="avatar">{initials}</div>
    <div class="student-info">
      <div class="student-name">{s['name']}</div>
      <div class="student-sub">{s['student_id']} · {s['class']}</div>
    </div>
    <div style="color:var(--gold);font-size:18px">›</div>
  </div></a>"""
    html += "</div>"
    return render(html, "students")

@app.route("/student/<path:sid>")
@login_required
def student_detail(sid):
    s = db.get_student(sid)
    if not s:
        flash("Student not found", "error")
        return redirect(url_for("students"))

    summary = db.get_student_balance_summary(sid)
    fees = db.get_student_fees(sid)
    by_term = {}
    for f in fees:
        by_term.setdefault(f["term"], []).append(f)

    html = f"""
<a href="/students" class="back">Students</a>
<div class="card">
  <div style="display:flex;align-items:center;gap:14px;margin-bottom:12px">
    <div class="avatar" style="width:50px;height:50px;font-size:20px">{"".join(w[0] for w in s['name'].split()[:2]).upper()}</div>
    <div>
      <div style="font-size:18px;font-weight:800">{s['name']}</div>
      <div style="font-size:12px;color:var(--grey)">{s['student_id']} · {s['class']}</div>
    </div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:13px">
    <div><span style="color:var(--grey)">Teacher:</span> {s['teacher'] or '—'}</div>
    <div><span style="color:var(--grey)">DOB:</span> {s['dob'] or '—'}</div>
  </div>
</div>

<div class="stat-grid">
  <div class="stat-box">
    <div class="stat-num" style="font-size:16px">Ksh {fmt(summary['total_owed'])}</div>
    <div class="stat-label">Total Owed</div>
  </div>
  <div class="stat-box">
    <div class="stat-num" style="font-size:16px;color:{'var(--red)' if summary['total_balance']>0 else 'var(--green)'}">Ksh {fmt(summary['total_balance'])}</div>
    <div class="stat-label">Balance</div>
  </div>
</div>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 12px">
  <a href="/pay/{sid}" class="btn btn-green btn-block" style="margin-top:0;text-align:center">💰 Record Payment</a>
  <a href="/student/{sid}/edit" class="btn btn-navy btn-block" style="margin-top:0;text-align:center">✏️ Edit</a>
</div>

<div class="section-title">Fee Summary</div>"""

    for term in db.TERMS:
        rows = by_term.get(term, [])
        if not rows:
            continue
        t_owed = sum(r["total_owed"] for r in rows)
        t_paid = sum(r["total_paid"] for r in rows)
        t_bal  = t_owed - t_paid
        pct    = int((t_paid/t_owed*100) if t_owed else 100)
        html += f"""
<div class="card">
  <h2>{term}</h2>
  <div class="progress-bar"><div class="progress-fill" style="width:{pct}%"></div></div>
  <div style="font-size:11px;color:var(--grey);margin-top:4px;margin-bottom:10px">{pct}% paid · Balance: Ksh {fmt(t_bal)}</div>"""
        for r in rows:
            bal = r["total_owed"] - r["total_paid"]
            status = "badge-green" if bal<=0 else ("badge-orange" if r["total_paid"]>0 else "badge-red")
            status_txt = "Paid" if bal<=0 else ("Partial" if r["total_paid"]>0 else "Unpaid")
            html += f"""<div class="fee-row">
    <div>
      <div style="font-size:13px;font-weight:600">{r['category']}</div>
      <div style="font-size:11px;color:var(--grey)">Paid: Ksh {fmt(r['total_paid'])} / Owed: Ksh {fmt(r['total_owed'])}</div>
    </div>
    <span class="badge {status}">{status_txt}</span>
  </div>"""
        html += "</div>"

    # Payment history
    history = db.get_payment_history(sid)[:10]
    if history:
        html += '<div class="section-title">Recent Payments</div><div style="padding:0 12px">'
        for h in history:
            d = h["paid_date"] or (h["paid_at"][:10] if h["paid_at"] else "—")
            html += f"""<div class="payment-item">
  <div style="font-weight:700;font-size:14px">Ksh {fmt(h['amount'])} — {h['category']}</div>
  <div style="font-size:12px;color:var(--grey)">{h['term']} · {d}{' · '+h['notes'] if h['notes'] else ''}</div>
</div>"""
        html += "</div>"

    html += f"""
<div style="padding:12px">
  <form method="POST" action="/student/{sid}/delete"
    onsubmit="return confirm('Delete {s['name']}? This cannot be undone.')">
    <button class="btn btn-red btn-block" type="submit">🗑 Delete Student</button>
  </form>
</div>"""
    return render(html, "students")

@app.route("/students/add", methods=["GET","POST"])
@login_required
def add_student():
    next_id = db.generate_student_id()
    if request.method == "POST":
        sid     = request.form.get("student_id","").strip()
        name    = request.form.get("name","").strip()
        cls     = request.form.get("class","")
        dob     = request.form.get("dob","").strip()
        teacher = request.form.get("teacher","").strip()
        is_new  = bool(request.form.get("is_new"))
        join    = request.form.get("join_term","Term I")
        if not sid or not name:
            flash("Student ID and Name are required.", "error")
        else:
            ok, msg = db.add_student(sid, name, cls, dob, teacher, is_new, join)
            if ok:
                flash(msg, "success")
                return redirect(url_for("students"))
            else:
                flash(msg, "error")

    cls_options = "".join(f'<option value="{c}">{c}</option>' for c in db.CLASSES)
    html = f"""
<a href="/students" class="back">Students</a>
<div class="card">
  <h2>Add Student</h2>
  <form method="POST">
    <label>Student ID</label>
    <input name="student_id" value="{next_id}" readonly style="background:var(--light);color:var(--navy);font-weight:700">
    <label>Full Name *</label>
    <input name="name" placeholder="e.g. Jane Doe" required>
    <label>Class *</label>
    <select name="class">{cls_options}</select>
    <label>Date of Birth</label>
    <input name="dob" type="date">
    <label>Teacher</label>
    <input name="teacher" placeholder="Class teacher name">
    <label style="display:flex;align-items:center;gap:8px;margin-top:12px">
      <input type="checkbox" name="is_new" style="width:auto" id="isnew" onchange="document.getElementById('joinrow').style.display=this.checked?'block':'none'">
      New student joining mid-year
    </label>
    <div id="joinrow" style="display:none">
      <label>Joining Term</label>
      <select name="join_term">
        <option>Term II</option><option>Term III</option>
      </select>
    </div>
    <button class="btn btn-green btn-block" type="submit">Add Student</button>
  </form>
</div>"""
    return render(html, "students")

@app.route("/student/<path:sid>/edit", methods=["GET","POST"])
@login_required
def edit_student(sid):
    s = db.get_student(sid)
    if not s:
        return redirect(url_for("students"))
    if request.method == "POST":
        name    = request.form.get("name","").strip()
        cls     = request.form.get("class","")
        dob     = request.form.get("dob","").strip()
        teacher = request.form.get("teacher","").strip()
        db.update_student(sid, name, cls, dob, teacher)
        flash("Student updated.", "success")
        return redirect(url_for("student_detail", sid=sid))

    cls_options = "".join(f'<option value="{c}" {"selected" if c==s["class"] else ""}>{c}</option>' for c in db.CLASSES)
    html = f"""
<a href="/student/{sid}" class="back">{s['name']}</a>
<div class="card">
  <h2>Edit Student</h2>
  <form method="POST">
    <label>Student ID</label>
    <input value="{s['student_id']}" disabled style="background:var(--light)">
    <label>Full Name</label>
    <input name="name" value="{s['name']}" required>
    <label>Class</label>
    <select name="class">{cls_options}</select>
    <label>Date of Birth</label>
    <input name="dob" type="date" value="{s['dob'] or ''}">
    <label>Teacher</label>
    <input name="teacher" value="{s['teacher'] or ''}">
    <button class="btn btn-green btn-block" type="submit">Save Changes</button>
  </form>
</div>"""
    return render(html, "students")

@app.route("/student/<path:sid>/delete", methods=["POST"])
@login_required
def delete_student(sid):
    db.delete_student(sid)
    flash("Student deleted.", "success")
    return redirect(url_for("students"))

# ── Payments ──────────────────────────────────────────────────────────────────

@app.route("/payments")
@login_required
def payments():
    search = request.args.get("q","").lower()
    all_s  = db.get_all_students()
    if search:
        all_s = [s for s in all_s if search in s["name"].lower() or search in s["student_id"].lower()]

    html = """
<div style="padding:10px 12px 4px;display:flex;gap:8px">
  <input style="flex:1" type="text" placeholder="Search student..." value="{q}"
    oninput="window.location='/payments?q='+this.value">
</div>
<div class="section-title">Select a Student</div>
<div class="card" style="padding:0;overflow:hidden">""".format(q=search)

    if not all_s:
        html += '<div class="empty">No students found</div>'
    for s in all_s:
        summary = db.get_student_balance_summary(s["student_id"])
        bal = summary["total_balance"]
        initials = "".join(w[0] for w in s["name"].split()[:2]).upper()
        badge_cls = "badge-red" if bal > 0 else "badge-green"
        html += f"""<a href="/pay/{s['student_id']}" style="text-decoration:none">
  <div class="student-row">
    <div class="avatar">{initials}</div>
    <div class="student-info">
      <div class="student-name">{s['name']}</div>
      <div class="student-sub">{s['student_id']} · {s['class']}</div>
    </div>
    <span class="badge {badge_cls}" style="white-space:nowrap">Ksh {fmt(bal)}</span>
  </div></a>"""
    html += "</div>"
    return render(html, "payments")

@app.route("/pay/<path:sid>", methods=["GET","POST"])
@login_required
def pay_student(sid):
    s = db.get_student(sid)
    if not s:
        return redirect(url_for("payments"))

    if request.method == "POST":
        term     = request.form.get("term","")
        category = request.form.get("category","")
        amount   = request.form.get("amount","").replace(",","")
        date     = request.form.get("paid_date","")
        notes    = request.form.get("notes","")
        exam_name= request.form.get("exam_name","").strip()
        exam_amt = request.form.get("exam_amount","").replace(",","")
        exam_term= request.form.get("exam_term","")

        if exam_name and exam_amt:
            try:
                ok, msg = db.add_exam_fee(sid, exam_term, exam_name, float(exam_amt))
                flash(msg, "success" if ok else "error")
            except:
                flash("Invalid exam amount.", "error")
        elif amount:
            try:
                ok, msg = db.record_payment(sid, term, category, float(amount), notes, date or None)
                flash(msg, "success" if ok else "error")
            except:
                flash("Invalid amount.", "error")
        return redirect(url_for("pay_student", sid=sid))

    fees  = db.get_student_fees(sid)
    by_term = {}
    for f in fees:
        by_term.setdefault(f["term"], []).append(f)
    summary = db.get_student_balance_summary(sid)

    term_opts  = "".join(f'<option value="{t}">{t}</option>' for t in db.TERMS)
    today = __import__("datetime").date.today().isoformat()

    html = f"""
<a href="/student/{sid}" class="back">{s['name']}</a>
<div class="card">
  <h2>Record Payment</h2>
  <form method="POST">
    <label>Term</label>
    <select name="term" id="termsel" onchange="updateCats()">{term_opts}</select>
    <label>Fee Category</label>
    <select name="category" id="catsel"></select>
    <label>Amount (Ksh)</label>
    <input name="amount" type="number" step="0.01" placeholder="e.g. 2500">
    <label>Date of Payment</label>
    <input name="paid_date" type="date" value="{today}">
    <label>Notes (optional)</label>
    <input name="notes" placeholder="e.g. Cash">
    <button class="btn btn-green btn-block" type="submit">✔ Record Payment</button>
  </form>
</div>

<div class="card">
  <h2>Add Exam Fee</h2>
  <form method="POST">
    <label>Exam Name</label>
    <input name="exam_name" placeholder="e.g. Mid-term Exam">
    <label>Term</label>
    <select name="exam_term">{term_opts}</select>
    <label>Amount (Ksh)</label>
    <input name="exam_amount" type="number" step="0.01" placeholder="e.g. 500">
    <button class="btn btn-navy btn-block" type="submit">+ Add Exam Fee</button>
  </form>
</div>

<div class="section-title">Balance Summary · Ksh {fmt(summary['total_balance'])} remaining</div>"""

    for term in db.TERMS:
        rows = by_term.get(term, [])
        if not rows:
            continue
        t_bal = sum(r["total_owed"]-r["total_paid"] for r in rows)
        html += f'<div class="card"><h2>{term} · Ksh {fmt(t_bal)}</h2>'
        for r in rows:
            bal = r["total_owed"] - r["total_paid"]
            pct = int((r["total_paid"]/r["total_owed"]*100) if r["total_owed"] else 100)
            html += f"""<div class="fee-row">
  <div style="flex:1">
    <div style="font-size:13px;font-weight:600">{r['category']}</div>
    <div class="progress-bar"><div class="progress-fill" style="width:{pct}%"></div></div>
    <div style="font-size:11px;color:var(--grey)">Paid {fmt(r['total_paid'])} / {fmt(r['total_owed'])}</div>
  </div>
  <div style="font-size:13px;font-weight:700;color:{'var(--red)' if bal>0 else 'var(--green)'};margin-left:10px">Ksh {fmt(bal)}</div>
</div>"""
        html += "</div>"

    # Build fees JSON for JS
    import json
    fees_json = json.dumps({t: [f["category"] for f in rows] for t, rows in by_term.items()})
    html += f"""
<script>
const feesData = {fees_json};
function updateCats(){{
  const term = document.getElementById('termsel').value;
  const cats = feesData[term] || [];
  const sel = document.getElementById('catsel');
  sel.innerHTML = cats.map(c=>`<option value="${{c}}">${{c}}</option>`).join('');
}}
updateCats();
</script>"""
    return render(html, "payments")

# ── Fee Settings ──────────────────────────────────────────────────────────────

@app.route("/fees", methods=["GET","POST"])
@login_required
def fee_settings():
    if request.method == "POST":
        action = request.form.get("action","")
        if action == "add":
            cat = request.form.get("category","").strip()
            try:
                amt = float(request.form.get("amount","0").replace(",",""))
                ok, msg = db.add_fee_category(cat, amt)
                flash(msg, "success" if ok else "error")
            except:
                flash("Invalid amount.", "error")
        elif action == "save":
            cat = request.form.get("category","")
            try:
                amt = float(request.form.get("amount","0").replace(",",""))
                db.set_fee_setting(cat, amt)
                flash(f"'{cat}' updated.", "success")
            except:
                flash("Invalid amount.", "error")
        elif action == "delete":
            cat = request.form.get("category","")
            ok, msg = db.delete_fee_category(cat)
            flash(msg, "success" if ok else "error")
        elif action == "assign":
            sid   = request.form.get("student_id","")
            cat   = request.form.get("category","")
            terms = request.form.getlist("terms")
            if sid and cat and terms:
                ok, msg = db.assign_extra_fee(sid, cat, terms)
                flash(msg, "success" if ok else "error")
            else:
                flash("Select student, category and at least one term.", "error")
        return redirect(url_for("fee_settings"))

    settings = db.get_fee_settings()
    students = db.get_all_students()

    html = '<div class="card"><h2>Extra Fee Categories</h2>'
    html += """<form method="POST">
  <input type="hidden" name="action" value="add">
  <div class="row">
    <input name="category" placeholder="e.g. Lunch" style="flex:1">
    <input name="amount" placeholder="Amount" style="width:100px">
    <button class="btn btn-green btn-sm" type="submit">+ Add</button>
  </div>
</form>"""

    if settings:
        html += '<div style="margin-top:14px">'
        for s in settings:
            html += f"""<form method="POST" style="margin-bottom:8px">
  <input type="hidden" name="action" value="save">
  <input type="hidden" name="category" value="{s['category']}">
  <div class="row">
    <span style="flex:1;font-weight:600;font-size:13px">{s['category']}</span>
    <input name="amount" value="{fmt(s['amount'])}" style="width:90px">
    <button class="btn btn-navy btn-sm" type="submit">Save</button>"""
            if not s["is_fixed"]:
                html += f"""</form>
  <form method="POST" style="display:inline">
    <input type="hidden" name="action" value="delete">
    <input type="hidden" name="category" value="{s['category']}">
    <button class="btn btn-red btn-sm" type="submit" onclick="return confirm('Delete {s['category']}?')">✕</button>
  </form>"""
            else:
                html += "</form>"
        html += "</div>"
    html += "</div>"

    # Assign to student
    cat_opts = "".join(f'<option value="{s["category"]}">{s["category"]}</option>' for s in settings) if settings else ""
    std_opts = "".join(f'<option value="{s["student_id"]}">{s["name"]} ({s["student_id"]})</option>' for s in students)
    term_chks = "".join(f'<label style="display:inline-flex;align-items:center;gap:4px;margin-right:12px"><input type="checkbox" name="terms" value="{t}" style="width:auto"> {t}</label>' for t in db.TERMS)

    html += f"""
<div class="card">
  <h2>Assign Fee to Student</h2>
  <form method="POST">
    <input type="hidden" name="action" value="assign">
    <label>Student</label>
    <select name="student_id"><option value="">— select —</option>{std_opts}</select>
    <label>Category</label>
    <select name="category"><option value="">— select —</option>{cat_opts}</select>
    <label>Term(s)</label>
    <div style="margin-top:6px">{term_chks}</div>
    <button class="btn btn-navy btn-block" type="submit">Assign</button>
  </form>
</div>

<div class="card">
  <h2>Tuition (Fixed)</h2>
  <div style="font-size:12px;color:var(--grey)">"""
    for cls in db.CLASSES:
        t1 = db.TUITION_FEES["Term I"][cls]
        html += f'<div style="padding:4px 0;border-bottom:1px solid var(--light)"><b>{cls}</b>: Ksh {fmt(sum(t1.values()))} (Term I) · Ksh {fmt(list(db.TUITION_FEES["Term II"][cls].values())[0])} (Term II/III)</div>'
    html += "</div></div>"
    return render(html, "fees")

# ── Requirements ──────────────────────────────────────────────────────────────

@app.route("/requirements", methods=["GET","POST"])
@login_required
def requirements():
    if request.method == "POST":
        action = request.form.get("action","")
        if action == "add":
            name = request.form.get("name","").strip()
            try:
                qty = int(request.form.get("quantity","1"))
                ok, msg = db.add_requirement(name, qty)
                flash(msg, "success" if ok else "error")
            except:
                flash("Invalid quantity.", "error")
        elif action == "delete":
            ok, msg = db.delete_requirement(int(request.form.get("req_id",0)))
            flash(msg, "success" if ok else "error")
        elif action == "update_student":
            sid   = request.form.get("student_id","")
            rid   = int(request.form.get("req_id",0))
            qty   = int(request.form.get("qty_brought",0))
            db.set_student_requirement(sid, rid, qty)
            flash("Updated.", "success")
        return redirect(url_for("requirements") + (f"?sid={request.form.get('student_id','')}" if request.form.get("student_id") else ""))

    reqs     = db.get_requirements()
    students = db.get_all_students()
    sid      = request.args.get("sid","")
    sel_student = db.get_student(sid) if sid else None
    std_opts = "".join(f'<option value="{s["student_id"]}" {"selected" if s["student_id"]==sid else ""}>{s["name"]} ({s["student_id"]})</option>' for s in students)

    html = """
<div class="card">
  <h2>Requirements List</h2>
  <form method="POST">
    <input type="hidden" name="action" value="add">
    <div class="row">
      <input name="name" placeholder="e.g. Exercise Book" style="flex:1">
      <input name="quantity" type="number" value="1" style="width:60px" min="1">
      <button class="btn btn-green btn-sm" type="submit">+ Add</button>
    </div>
  </form>"""

    if reqs:
        html += '<div style="margin-top:12px"><div class="table-wrap"><table><tr><th>Item</th><th>Qty</th><th></th></tr>'
        for r in reqs:
            html += f"""<tr>
  <td>{r['name']}</td>
  <td>{r['quantity']}</td>
  <td>
    <form method="POST" style="display:inline">
      <input type="hidden" name="action" value="delete">
      <input type="hidden" name="req_id" value="{r['id']}">
      <button class="btn btn-red btn-sm" type="submit">✕</button>
    </form>
  </td>
</tr>"""
        html += "</table></div></div>"
    html += "</div>"

    # Student tracking
    html += f"""
<div class="card">
  <h2>Student Tracking</h2>
  <form method="GET">
    <label>Select Student</label>
    <div class="row">
      <select name="sid" style="flex:1" onchange="this.form.submit()">
        <option value="">— select student —</option>{std_opts}
      </select>
    </div>
  </form>"""

    if sel_student and reqs:
        html += f'<div style="margin-top:12px;font-weight:700">{sel_student["name"]}</div><div class="table-wrap"><table><tr><th>Item</th><th>Need</th><th>Brought</th><th>Status</th></tr>'
        std_reqs = db.get_student_requirements(sel_student["student_id"])
        for r in std_reqs:
            done = r["brought"] >= r["required"]
            part = 0 < r["brought"] < r["required"]
            badge = "badge-green" if done else ("badge-orange" if part else "badge-red")
            status = "✔" if done else ("~" if part else "✗")
            html += f"""<tr>
  <td>{r['name']}</td>
  <td>{r['required']}</td>
  <td>
    <form method="POST" style="display:flex;gap:4px">
      <input type="hidden" name="action" value="update_student">
      <input type="hidden" name="student_id" value="{sel_student['student_id']}">
      <input type="hidden" name="req_id" value="{r['id']}">
      <input name="qty_brought" type="number" value="{r['brought']}" min="0" style="width:60px;padding:4px 6px;font-size:13px">
      <button class="btn btn-navy btn-sm" type="submit">✔</button>
    </form>
  </td>
  <td><span class="badge {badge}">{status}</span></td>
</tr>"""
        html += "</table></div>"
    html += "</div>"
    return render(html, "more")

# ── Miscellaneous ─────────────────────────────────────────────────────────────

@app.route("/misc", methods=["GET","POST"])
@login_required
def misc():
    if request.method == "POST":
        action = request.form.get("action","")
        if action == "add":
            term  = request.form.get("term","")
            item  = request.form.get("item","").strip()
            date  = request.form.get("expense_date","")
            notes = request.form.get("notes","")
            try:
                amt = float(request.form.get("amount","0").replace(",",""))
                ok, msg = db.add_misc_expense(term, item, amt, date or None, notes)
                flash(msg, "success" if ok else "error")
            except:
                flash("Invalid amount.", "error")
        elif action == "delete":
            db.delete_misc_expense(int(request.form.get("expense_id",0)))
            flash("Deleted.", "success")
        return redirect(url_for("misc"))

    term_filter = request.args.get("term", db.TERMS[0])
    expenses    = db.get_misc_expenses(term_filter)
    total       = sum(e["amount"] for e in expenses)
    today       = __import__("datetime").date.today().isoformat()
    term_opts   = "".join(f'<option value="{t}" {"selected" if t==term_filter else ""}>{t}</option>' for t in db.TERMS)

    html = f"""
<div class="card">
  <h2>Add Expense</h2>
  <form method="POST">
    <input type="hidden" name="action" value="add">
    <label>Term</label>
    <select name="term">{term_opts}</select>
    <label>Item</label>
    <input name="item" placeholder="e.g. Cooking Oil">
    <label>Amount (Ksh)</label>
    <input name="amount" type="number" step="0.01" placeholder="e.g. 500">
    <label>Date</label>
    <input name="expense_date" type="date" value="{today}">
    <label>Notes</label>
    <input name="notes" placeholder="optional">
    <button class="btn btn-green btn-block" type="submit">+ Add Expense</button>
  </form>
</div>

<form method="GET" style="padding:0 12px 4px;display:flex;align-items:center;gap:8px">
  <label style="margin:0;white-space:nowrap;font-size:13px">Filter:</label>
  <select name="term" onchange="this.form.submit()" style="flex:1">{term_opts}</select>
</form>

<div style="padding:0 12px;margin-bottom:6px">
  <div style="background:var(--navy);color:var(--gold);border-radius:8px;padding:10px 14px;font-weight:700">
    {term_filter} Total: Ksh {fmt(total)}
  </div>
</div>"""

    if expenses:
        html += '<div class="card" style="padding:0;overflow:hidden"><div class="table-wrap"><table><tr><th>Date</th><th>Item</th><th>Amount</th><th></th></tr>'
        for e in expenses:
            html += f"""<tr>
  <td style="white-space:nowrap">{e['expense_date'] or '—'}</td>
  <td>{e['item']}{('<br><small style="color:var(--grey)">'+e['notes']+'</small>') if e['notes'] else ''}</td>
  <td style="white-space:nowrap">Ksh {fmt(e['amount'])}</td>
  <td>
    <form method="POST">
      <input type="hidden" name="action" value="delete">
      <input type="hidden" name="expense_id" value="{e['id']}">
      <button class="btn btn-red btn-sm" type="submit">✕</button>
    </form>
  </td>
</tr>"""
        html += "</table></div></div>"
    else:
        html += '<div class="empty">No expenses for this term</div>'
    return render(html, "more")

# ── More ──────────────────────────────────────────────────────────────────────

@app.route("/more")
@login_required
def more():
    html = """
<div class="section-title">Reports</div>
<div class="card" style="padding:0;overflow:hidden">
  <a href="/reports" style="text-decoration:none"><div class="student-row"><div class="avatar" style="background:#744210">📄</div><div class="student-info"><div class="student-name">Generate Reports</div><div class="student-sub">PDF reports for students & payments</div></div><div style="color:var(--gold);font-size:18px">›</div></div></a>
</div>
<div class="section-title">Management</div>
<div class="card" style="padding:0;overflow:hidden">
  <a href="/requirements" style="text-decoration:none"><div class="student-row"><div class="avatar" style="background:#2c5282">✓</div><div class="student-info"><div class="student-name">Requirements</div><div class="student-sub">Track what students bring</div></div><div style="color:var(--gold);font-size:18px">›</div></div></a>
  <a href="/misc" style="text-decoration:none"><div class="student-row"><div class="avatar" style="background:#276749">📋</div><div class="student-info"><div class="student-name">Miscellaneous</div><div class="student-sub">School expenses per term</div></div><div style="color:var(--gold);font-size:18px">›</div></div></a>
  <a href="/promote" style="text-decoration:none"><div class="student-row"><div class="avatar" style="background:#742a2a">⬆</div><div class="student-info"><div class="student-name">Promote Students</div><div class="student-sub">Year-end class promotion</div></div><div style="color:var(--gold);font-size:18px">›</div></div></a>
  <a href="/change-password" style="text-decoration:none"><div class="student-row"><div class="avatar">🔑</div><div class="student-info"><div class="student-name">Change Password</div><div class="student-sub">Update login credentials</div></div><div style="color:var(--gold);font-size:18px">›</div></div></a>
</div>"""
    return render(html, "more")

@app.route("/promote", methods=["GET","POST"])
@login_required
def promote():
    if request.method == "POST":
        promoted, left = db.promote_all_students()
        msg = f"Promoted {len(promoted)} students. {len(left)} completed Grade 4 and removed."
        flash(msg, "success")
        return redirect(url_for("home"))

    students = db.get_all_students()
    html = """
<a href="/more" class="back">More</a>
<div class="card">
  <h2>Year-End Promotion</h2>
  <div style="font-size:13px;color:var(--grey);margin-bottom:16px;line-height:1.6">
    This will move ALL students up one class.<br>
    Grade 3 → Grade 4. Grade 4 students will be removed from the system.
  </div>
  <div style="background:var(--light);border-radius:8px;padding:12px;margin-bottom:16px">"""
    by_class = {}
    for s in students:
        by_class[s["class"]] = by_class.get(s["class"], 0) + 1
    for cls in db.CLASSES:
        c = by_class.get(cls, 0)
        if c:
            html += f'<div style="padding:4px 0;font-size:13px"><b>{cls}</b>: {c} students</div>'
    html += f"""</div>
  <form method="POST" onsubmit="return confirm('Promote all students? This cannot be undone.')">
    <button class="btn btn-red btn-block" type="submit">⬆ Promote All Students</button>
  </form>
</div>"""
    return render(html, "more")

@app.route("/change-password", methods=["GET","POST"])
@login_required
def change_password():
    if request.method == "POST":
        new_user = request.form.get("username","").strip()
        new_pass = request.form.get("password","")
        confirm  = request.form.get("confirm","")
        if new_pass != confirm:
            flash("Passwords do not match.", "error")
        else:
            ok, msg = db.change_credentials(new_user, new_pass)
            flash(msg, "success" if ok else "error")
            if ok:
                session.clear()
                return redirect(url_for("login"))
    html = f"""
<a href="/more" class="back">More</a>
<div class="card">
  <h2>Change Credentials</h2>
  <form method="POST">
    <label>New Username</label>
    <input name="username" value="{db.get_username()}">
    <label>New Password</label>
    <input name="password" type="password">
    <label>Confirm Password</label>
    <input name="confirm" type="password">
    <button class="btn btn-navy btn-block" type="submit">Save Changes</button>
  </form>
</div>"""
    return render(html, "more")

@app.route("/reports", methods=["GET","POST"])
@login_required
def reports():
    import reports_gen as rg
    import os

    if request.method == "POST":
        action = request.form.get("action","")
        try:
            if action == "register":
                cls = request.form.get("class","")
                path = rg.generate_student_register(None if cls == "All Classes" else cls)
                flash(f"Saved: {os.path.basename(path)}", "success")
            elif action == "payment_class":
                cls   = request.form.get("class","")
                terms = request.form.getlist("terms")
                if not terms:
                    terms = db.TERMS
                path = rg.generate_payment_report(
                    class_filter=None if cls == "All Classes" else cls,
                    terms_filter=terms
                )
                flash(f"Saved: {os.path.basename(path)}", "success")
            elif action == "payment_student":
                sid   = request.form.get("student_id","")
                terms = request.form.getlist("terms")
                inc_r = bool(request.form.get("include_requirements"))
                if not terms:
                    terms = db.TERMS
                if not sid:
                    flash("Select a student.", "error")
                else:
                    path = rg.generate_payment_report(
                        student_id=sid,
                        terms_filter=terms,
                        include_requirements=inc_r
                    )
                    flash(f"Saved: {os.path.basename(path)}", "success")
            elif action == "promote":
                promoted, left = db.promote_all_students()
                flash(f"Promoted {len(promoted)} students. {len(left)} removed.", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
        return redirect(url_for("reports"))

    students = db.get_all_students()
    cls_opts = "".join(f'<option value="{c}">{c}</option>' for c in ["All Classes"] + db.CLASSES)
    std_opts = "".join(f'<option value="{s["student_id"]}">{s["name"]} ({s["student_id"]})</option>' for s in students)
    term_chks= "".join(f'<label style="display:inline-flex;align-items:center;gap:4px;margin:4px 10px 4px 0"><input type="checkbox" name="terms" value="{t}" checked style="width:auto"> {t}</label>' for t in db.TERMS)

    html = """
<div class="section-title">Student Register PDF</div>
<div class="card">
  <h2>Student Register</h2>
  <form method="POST">
    <input type="hidden" name="action" value="register">
    <label>Class</label>
    <select name="class">""" + cls_opts + """</select>
    <button class="btn btn-navy btn-block" type="submit">📄 Generate Register PDF</button>
  </form>
</div>

<div class="section-title">Payment Report — Single Student</div>
<div class="card">
  <h2>Single Student Report</h2>
  <form method="POST">
    <input type="hidden" name="action" value="payment_student">
    <label>Student</label>
    <select name="student_id"><option value="">— select —</option>""" + std_opts + """</select>
    <label>Include Terms</label>
    <div style="margin-top:6px">""" + term_chks + """</div>
    <label style="display:flex;align-items:center;gap:8px;margin-top:10px">
      <input type="checkbox" name="include_requirements" style="width:auto" checked>
      Include Requirements section
    </label>
    <button class="btn btn-gold btn-block" style="color:var(--navy)" type="submit">📄 Generate Student PDF</button>
  </form>
</div>

<div class="section-title">Payment Report — Class / All</div>
<div class="card">
  <h2>Class Payment Report</h2>
  <form method="POST">
    <input type="hidden" name="action" value="payment_class">
    <label>Class</label>
    <select name="class">""" + cls_opts + """</select>
    <label>Include Terms</label>
    <div style="margin-top:6px">""" + term_chks + """</div>
    <button class="btn btn-green btn-block" type="submit">📄 Generate Class PDF</button>
  </form>
</div>

<div class="section-title">Reports Location</div>
<div class="card">
  <div style="font-size:13px;color:var(--grey);line-height:1.7">
    All PDFs are saved to the <b>reports/</b> folder inside your school system folder on your PC.<br>
    <span style="font-size:12px">C:\\Users\\user\\Desktop\\Elroi Favoured School Management System\\reports\\</span>
  </div>
</div>"""
    return render(html, "more")


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    db.init_db()
    import socket
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except:
        local_ip = "your-pc-ip"
    print("\n" + "="*55)
    print("  ELROI FAVOURED SCHOOL — Web App")
    print("="*55)
    print(f"\n  Open on your PC:     http://localhost:5000")
    print(f"  Open on your phone:  http://{local_ip}:5000")
    print(f"\n  (Make sure phone is on same WiFi as this PC)")
    print("\n  Press Ctrl+C to stop\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
