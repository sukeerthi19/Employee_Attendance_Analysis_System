# Employee Attendance Analysis System

**Difficulty:** Beginner  
**Language:** Python  
**Database:** SQLite (included, no database server required)  
**Analysis:** Pandas, NumPy, Matplotlib

## Features
- Add and list employee records.
- Record daily attendance using `Present`, `Absent`, `Leave`, or `Holiday`.
- Prevent duplicate attendance for the same employee and date with a database `UNIQUE` constraint.
- Generate monthly employee attendance summaries and attendance percentages.
- Generate department-wise summaries.
- Create an absenteeism bar chart.
- Import attendance from CSV and export all records to CSV.
- Includes sample employees and sample attendance records.

## Attendance calculation rules
- `Present`, `Absent`, and `Leave` are counted as working-day entries.
- `Holiday` is excluded from the attendance percentage denominator.
- Attendance percentage = `Present days / (Present + Absent + Leave days) × 100`.
- The sample data uses weekdays for example working days and marks weekends as `Holiday`. Adapt the sample generation if your institution/company has a different calendar.

## Requirements
- Python 3.9 or newer
- Packages listed in `requirements.txt`

## Run on Windows
1. Extract the ZIP file.
2. Install Python from the official Python website if it is not already installed. During installation, tick **Add Python to PATH**.
3. Open the project folder.
4. Click the folder address bar, type `cmd`, and press Enter.
5. Run:
   ```bash
   python -m pip install -r requirements.txt
   python main.py
   ```
6. Choose an option from the menu. The database `attendance.db` is created automatically on first run.

## Reports
Generated reports are saved in the `reports` folder:
- `monthly_attendance_YYYY-MM.csv`
- `department_summary_YYYY-MM.csv`
- `absenteeism_YYYY-MM.png`
- `all_attendance_records.csv`

## CSV import format
`data/sample_attendance.csv` has the required columns:
```csv
employee_code,attendance_date,status
EMP001,2026-10-01,Present
EMP002,2026-10-01,Leave
```
The employee code must already exist. Valid statuses are `Present`, `Absent`, `Leave`, and `Holiday`. Duplicate or invalid rows are skipped.

## MySQL schema (optional)
The runnable version uses SQLite to make setup easy for beginners. If you need MySQL for a course requirement, `schema.sql` contains equivalent MySQL tables. The application would need its connection layer changed to use MySQL credentials.

## Project structure
```text
Employee_Attendance_Analysis_System/
├── main.py
├── requirements.txt
├── README.md
├── schema.sql
├── data/
│   └── sample_attendance.csv
└── reports/
```
