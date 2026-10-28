import sqlite3
from pathlib import Path
from datetime import date, datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
REPORT_DIR = ROOT / "reports"
DB_PATH = ROOT / "attendance.db"
DATA_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)

SCHEMA = """
CREATE TABLE IF NOT EXISTS employees (
    employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_code TEXT NOT NULL UNIQUE,
    employee_name TEXT NOT NULL,
    department TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    attendance_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('Present','Absent','Leave','Holiday')),
    FOREIGN KEY(employee_id) REFERENCES employees(employee_id),
    UNIQUE(employee_id, attendance_date)
);
"""

VALID_STATUSES = {"Present", "Absent", "Leave", "Holiday"}

def connect():
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA)
    return con

def seed_sample_data():
    """Load sample employees and attendance records only when the database is empty."""
    with connect() as con:
        count = con.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        if count:
            return
        employees = [
            ("EMP001", "Aarav Sharma", "IT"),
            ("EMP002", "Diya Reddy", "HR"),
            ("EMP003", "Kabir Kumar", "Finance"),
            ("EMP004", "Meera Nair", "IT"),
            ("EMP005", "Arjun Rao", "Sales"),
        ]
        con.executemany(
            "INSERT INTO employees(employee_code, employee_name, department) VALUES (?,?,?)",
            employees,
        )
        from calendar import monthrange
        year, month = date.today().year, date.today().month
        rows = []
        for emp_id in range(1, 6):
            for day in range(1, monthrange(year, month)[1] + 1):
                d = date(year, month, day)
                if d.weekday() >= 5:
                    status = "Holiday"
                else:
                    # Deterministic sample patterns for demonstration.
                    if (day + emp_id * 3) % 17 == 0:
                        status = "Leave"
                    elif (day + emp_id * 2) % 11 == 0:
                        status = "Absent"
                    else:
                        status = "Present"
                rows.append((emp_id, d.isoformat(), status))
        con.executemany(
            "INSERT OR IGNORE INTO attendance(employee_id, attendance_date, status) VALUES (?,?,?)",
            rows,
        )

def list_employees():
    with connect() as con:
        df = pd.read_sql_query(
            "SELECT employee_id, employee_code, employee_name, department FROM employees ORDER BY employee_id", con
        )
    print("\nEMPLOYEES")
    print(df.to_string(index=False) if not df.empty else "No employees found.")

def add_employee():
    code = input("Employee code: ").strip().upper()
    name = input("Employee name: ").strip()
    department = input("Department: ").strip()
    if not all((code, name, department)):
        print("All fields are required.")
        return
    try:
        with connect() as con:
            con.execute(
                "INSERT INTO employees(employee_code, employee_name, department) VALUES (?,?,?)",
                (code, name, department),
            )
        print("Employee added successfully.")
    except sqlite3.IntegrityError:
        print("That employee code already exists.")

def record_attendance():
    code = input("Employee code: ").strip().upper()
    raw_date = input("Date (YYYY-MM-DD): ").strip()
    status = input("Status (Present/Absent/Leave/Holiday): ").strip().title()
    try:
        datetime.strptime(raw_date, "%Y-%m-%d")
    except ValueError:
        print("Invalid date. Use YYYY-MM-DD.")
        return
    if status not in VALID_STATUSES:
        print("Invalid status. Choose Present, Absent, Leave, or Holiday.")
        return
    try:
        with connect() as con:
            row = con.execute("SELECT employee_id FROM employees WHERE employee_code=?", (code,)).fetchone()
            if not row:
                print("Employee code not found.")
                return
            con.execute(
                "INSERT INTO attendance(employee_id, attendance_date, status) VALUES (?,?,?)",
                (row[0], raw_date, status),
            )
        print("Attendance recorded successfully.")
    except sqlite3.IntegrityError:
        print("Duplicate blocked: attendance already exists for this employee on that date.")

def import_csv():
    path = DATA_DIR / "sample_attendance.csv"
    if not path.exists():
        print(f"CSV not found: {path}")
        return
    try:
        df = pd.read_csv(path)
        required = {"employee_code", "attendance_date", "status"}
        if not required.issubset(df.columns):
            print("CSV must contain employee_code, attendance_date, status columns.")
            return
        imported, skipped = 0, 0
        with connect() as con:
            codes = dict(con.execute("SELECT employee_code, employee_id FROM employees").fetchall())
            for _, row in df.iterrows():
                code = str(row["employee_code"]).strip().upper()
                status = str(row["status"]).strip().title()
                try:
                    datetime.strptime(str(row["attendance_date"]), "%Y-%m-%d")
                except ValueError:
                    skipped += 1
                    continue
                if code not in codes or status not in VALID_STATUSES:
                    skipped += 1
                    continue
                try:
                    con.execute(
                        "INSERT INTO attendance(employee_id, attendance_date, status) VALUES (?,?,?)",
                        (codes[code], str(row["attendance_date"]), status),
                    )
                    imported += 1
                except sqlite3.IntegrityError:
                    skipped += 1
        print(f"Import complete: {imported} added, {skipped} skipped (duplicates or invalid rows).")
    except Exception as exc:
        print(f"Could not import CSV: {exc}")

def load_attendance(start=None, end=None):
    query = """
        SELECT e.employee_id, e.employee_code, e.employee_name, e.department,
               a.attendance_date, a.status
        FROM attendance a JOIN employees e ON e.employee_id = a.employee_id
    """
    params = []
    clauses = []
    if start:
        clauses.append("a.attendance_date >= ?")
        params.append(start)
    if end:
        clauses.append("a.attendance_date <= ?")
        params.append(end)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY a.attendance_date, e.employee_code"
    with connect() as con:
        return pd.read_sql_query(query, con, params=params)

def period_input():
    month = input("Month (YYYY-MM, blank for current month): ").strip()
    if not month:
        month = date.today().strftime("%Y-%m")
    try:
        datetime.strptime(month, "%Y-%m")
    except ValueError:
        print("Invalid month. Use YYYY-MM.")
        return None
    return month

def monthly_report():
    month = period_input()
    if not month:
        return
    df = load_attendance(month + "-01", month + "-31")
    if df.empty:
        print("No attendance records found for that month.")
        return
    # Working days are weekdays with a recorded non-Holiday status; Leave and Absent
    # count as working days, while Holiday is excluded from the denominator.
    work = df[df["status"] != "Holiday"].copy()
    summary = work.groupby(
        ["employee_code", "employee_name", "department"], as_index=False
    ).agg(
        working_days=("status", "size"),
        present_days=("status", lambda s: int((s == "Present").sum())),
        absent_days=("status", lambda s: int((s == "Absent").sum())),
        leave_days=("status", lambda s: int((s == "Leave").sum())),
    )
    summary["attendance_percentage"] = np.where(
        summary["working_days"] > 0,
        summary["present_days"] / summary["working_days"] * 100,
        0.0,
    ).round(2)
    out = REPORT_DIR / f"monthly_attendance_{month}.csv"
    summary.to_csv(out, index=False)
    print(f"\nMONTHLY ATTENDANCE REPORT — {month}")
    print(summary.to_string(index=False))
    print(f"\nSaved: {out}")

def department_summary():
    month = period_input()
    if not month:
        return
    df = load_attendance(month + "-01", month + "-31")
    if df.empty:
        print("No attendance records found for that month.")
        return
    work = df[df["status"] != "Holiday"].copy()
    grouped = work.groupby("department").agg(
        working_day_entries=("status", "size"),
        present=("status", lambda s: int((s == "Present").sum())),
        absent=("status", lambda s: int((s == "Absent").sum())),
        leave=("status", lambda s: int((s == "Leave").sum())),
    ).reset_index()
    grouped["attendance_percentage"] = np.where(
        grouped["working_day_entries"] > 0,
        grouped["present"] / grouped["working_day_entries"] * 100,
        0.0,
    ).round(2)
    out = REPORT_DIR / f"department_summary_{month}.csv"
    grouped.to_csv(out, index=False)
    print("\nDEPARTMENT SUMMARY")
    print(grouped.to_string(index=False))
    print(f"\nSaved: {out}")

def absenteeism_chart():
    month = period_input()
    if not month:
        return
    df = load_attendance(month + "-01", month + "-31")
    if df.empty:
        print("No attendance records found for that month.")
        return
    absent = df[df["status"] == "Absent"].groupby("employee_name").size().sort_values(ascending=False)
    if absent.empty:
        print("No absences recorded for this month.")
        return
    ax = absent.plot(kind="bar", title=f"Absenteeism by Employee — {month}", xlabel="Employee", ylabel="Absent days")
    ax.figure.tight_layout()
    out = REPORT_DIR / f"absenteeism_{month}.png"
    ax.figure.savefig(out, dpi=150)
    plt.close(ax.figure)
    print(f"Absenteeism chart saved: {out}")

def export_all_records():
    df = load_attendance()
    out = REPORT_DIR / "all_attendance_records.csv"
    df.to_csv(out, index=False)
    print(f"Exported {len(df)} records to {out}")

def menu():
    seed_sample_data()
    while True:
        print("""
========================================
 EMPLOYEE ATTENDANCE ANALYSIS SYSTEM
========================================
1. View employees
2. Add employee
3. Record daily attendance
4. Generate monthly employee report
5. Generate department summary
6. Generate absenteeism chart
7. Import attendance from sample CSV
8. Export all attendance records
0. Exit
""")
        choice = input("Choose an option: ").strip()
        if choice == "1":
            list_employees()
        elif choice == "2":
            add_employee()
        elif choice == "3":
            record_attendance()
        elif choice == "4":
            monthly_report()
        elif choice == "5":
            department_summary()
        elif choice == "6":
            absenteeism_chart()
        elif choice == "7":
            import_csv()
        elif choice == "8":
            export_all_records()
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please choose 0–8.")

if __name__ == "__main__":
    menu()
