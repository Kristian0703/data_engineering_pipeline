# 🛠️ Data Engineering Pipeline

This project implements a **data engineering pipeline** that extracts data from a SQLite database, transforms and validates it, writes cleaned data to a new database, and exports a master table to CSV. It includes **automated testing**, a **changelog versioning system**, and a **safe deployment script** that moves updated database files from development (`dev/`) to production (`prod/`) with rollback support.

---

## 📂 Project Structure

```
.
├── dev/                        # Development database files and CSV exports
├── prod/                       # Production database files
├── prod_backup/                # Backup of last known good production files
├── .last_deployed_version      # Stores the last deployed changelog version
├── changelog.txt               # Version history of database updates
├── data_cleaning.log           # Log file with ETL run details (INFO + ERROR)
├── error.log                   # Historical log of ETL errors
├── deployment_history.log      # Deployment attempts & results (auto-generated)
├── deploy.sh                   # Deployment script (runs ETL + deploys to prod)
├── Main.py                     # Main ETL pipeline script
├── dataframeinspector.py       # Helper class for column type conversion, cleaning
├── helpers.py                  # Utility functions (e.g., changelog writer)
├── unit_tests.py               # Validation and quality checks
├── test_main.py                # Integration tests for Main.py
├── pytest.ini                  # Pytest configuration
├── pytest_output.log           # Stores last test run results
└── DataPipeline.ipynb          # Jupyter notebook for ad-hoc analysis
```

---

## ⚙️ How It Works

### 1️⃣ ETL Pipeline (`Main.py`)
The ETL process is designed to be **reliable** and **automated**:

- **Extract:** Connects to `dev/cademycode.db` and loads:
  - `cademycode_students`
  - `cademycode_courses`
  - `cademycode_student_jobs`
- **Transform & Clean:**
  - Converts column types (dates, integers, floats)
  - Extracts nested JSON from `contact_info`
  - Removes duplicates from job data
  - Adds synthetic `No path selected` row if missing
  - Merges tables to create a master student-course-job table
- **Validate:** Runs unit tests (`run_unit_tests()`) to check:
  - Data integrity
  - Null values
  - Row counts
  - Correctness of transformations  
  ✅ If tests fail, the pipeline stops and logs an error.
- **Load:**
  - Writes clean data to `dev/cademycode_clean.db`
  - Replaces individual tables (`students`, `courses`, `students_jobs`)
  - Commits changes to SQLite database
- **Changelog:**
  - Increments version using `get_next_version()`
  - Writes an entry to `changelog.txt`
- **Export:**
  - Exports master table to CSV (`dev/cademycode_master_students_table.csv`)
  - Uses newline fix to avoid blank lines in CSV
- **Logging:** 
  - INFO and ERROR messages are written to `data_cleaning.log`
  - ERROR messages also go to `error.log`

Run manually:
```bash
python Main.py
```

---

### 2️⃣ Testing

This project uses **pytest** for unit and integration tests.  
Run tests manually with:

```bash
pytest
```

Test results are stored in `pytest_output.log` when run via deployment script.

---

### 3️⃣ Version Tracking (`changelog.txt`)

Each successful run updates `changelog.txt`:

```
[2025-09-16 08:11:44.431514] Version: v1.3 | New rows: 0 | Schema Changes: None
```

This ensures every deployment is tied to a specific version of the data.

---

### 4️⃣ Deployment Script (`deploy.sh`)

The deployment script automates the process of moving cleaned data from development to production safely.

**Features:**
- ✅ Runs tests first (fails early if they fail)
- ✅ Executes ETL pipeline
- ✅ Checks today's logs for any `ERROR` messages
- ✅ Compares `changelog.txt` with last deployed version
- ✅ Copies only `.db` files modified since last deployment
- ✅ Creates a production backup before overwriting files
- ✅ Rolls back to backup if any file copy fails
- ✅ Logs results to `deployment_history.log`

Run deployment:
```bash
./deploy.sh
```

Example output:
```
=== 🚀 Starting Deployment Process ===
🧪 Running tests...
✅ Tests passed.
🔄 Running ETL pipeline...
✅ ETL script executed.
🔎 Checking logs for today's errors (2025-09-16)...
✅ No errors detected today.
📦 New version detected: v1.3 (previous: v1.2)
🗄️ Creating backup of current production files...
➡️  Deploying cademycode_clean.db...
✅ Deployment complete (version v1.3).
=== 🎉 Deployment Finished Successfully ===
```

---

### 5️⃣ Rollback

If deployment fails:
- The script restores files from `prod_backup/`
- A rollback event is logged in `deployment_history.log`

Example rollback log:
```
[2025-09-17 09:00:03] ❌ Deployment FAILED — Errors detected in today's logs.
[2025-09-17 09:00:03] 🔄 Rollback complete — Production restored to version v1.3.
```

---

## 🧪 Logs

- **data_cleaning.log** — Detailed ETL run logs (INFO + ERROR)
- **error.log** — All error events (cumulative)
- **deployment_history.log** — Audit trail of deployment attempts, successes, failures, rollbacks

---

## 🔧 Setup Instructions

### Prerequisites
- Python 3.x  
- `pytest`  
- Git Bash or WSL (for running `deploy.sh` on Windows)

Install pytest manually:
```bash
pip install pytest pandas
```

---

## 📊 Example Workflow

1. **Run ETL**  
   ```bash
   python Main.py
   ```
   → Cleans data, writes to `dev/cademycode_clean.db`, updates changelog.

2. **Deploy to Production**  
   ```bash
   ./deploy.sh
   ```
   → Runs tests → runs ETL → checks logs → deploys if no errors.

3. **Review Deployment History**  
   ```bash
   cat deployment_history.log
   ```

---

## 🚀 Future Improvements

- 📈 Track deployment duration in `deployment_history.log`
- 📢 Add Slack/Email notifications on failures
- 🤖 Automate with cron or GitHub Actions for scheduled runs
- 🗂️ Add data quality dashboards to monitor trends over time
