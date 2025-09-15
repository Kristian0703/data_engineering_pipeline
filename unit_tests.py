import sqlite3
import pandas as pd
import logging
import warnings

logger = logging.getLogger(__name__)

def run_unit_tests(students_df, courses_df, jobs_df, final_df):
    """
    Runs validation checks on the cleaned data before committing to the clean database.
    Returns (passed: bool, new_rows: int).
    """
    try:
        # --- 1. Schema Check ---
        expected_cols = [
            "uuid", "job_id", "current_career_path_id", "dob", "name", "sex",
            "email", "mailing_address", "num_course_taken", "time_spent_hrs",
            "career_path_name", "hours_to_complete", "job_category", "avg_salary"
        ]
        missing_cols = [col for col in expected_cols if col not in final_df.columns]
        if missing_cols:
            raise AssertionError(f"Schema mismatch: missing columns {missing_cols}")

        # --- 2. Foreign Key Integrity ---
        missing_career_paths = final_df[
            final_df["current_career_path_id"].notnull() &
            ~final_df["current_career_path_id"].isin(courses_df["career_path_id"])
        ]
        if not missing_career_paths.empty:
            raise AssertionError(f"Found {len(missing_career_paths)} rows with missing career_path_id.")

        # --- 3. Primary Key Duplicates ---
        if final_df["uuid"].duplicated().any():
            raise AssertionError("Duplicate UUIDs found in final dataset.")

        # --- 4. New Data Check ---
        try:
            conn_clean = sqlite3.connect(r"dev\\cademycode_clean.db")
            existing_df = pd.read_sql_query(
                "SELECT * FROM cademycode_master_students_table;", conn_clean
            )
            new_rows = len(final_df) - len(existing_df)
            if new_rows <= 0:
                # Warn but do not fail → still refresh the clean database
                warnings.warn("No new data found — clean database will still be refreshed.")
                new_rows = 0
        except sqlite3.DatabaseError:
            # First run → treat all rows as new
            new_rows = len(final_df)

        return True, new_rows

    except AssertionError as e:
        logger.error(f"Unit Test Failed: {e}")
        return False, 0
