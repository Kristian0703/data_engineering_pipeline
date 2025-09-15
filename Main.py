import sqlite3
import sys
import logging
import pandas as pd
from dataframeinspector import DataFrameInspector
from helpers import write_changelog, get_next_version
from unit_tests import run_unit_tests

# --- Logging Setup ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

file_handler = logging.FileHandler("data_cleaning.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

error_handler = logging.FileHandler("error.log")
error_handler.setFormatter(formatter)
error_handler.setLevel(logging.ERROR)
logger.addHandler(error_handler)


def main():
    # 1. Connect to source database
    try:
        conn = sqlite3.connect(r"dev\cademycode.db")
        logger.info("Connected to source database.")
    except Exception as e:
        logger.error(f"Error connecting to source database: {e}")
        sys.exit(1)

    # 2. Extract data
    students_df = pd.read_sql_query("SELECT * FROM cademycode_students;", conn)
    courses_df = pd.read_sql_query("SELECT * FROM cademycode_courses;", conn)
    student_jobs_df = pd.read_sql_query("SELECT * FROM cademycode_student_jobs;", conn)

    # 3. Transform / Clean data
    students_df_obj = DataFrameInspector(students_df)
    students_df_obj.convert_column_type("dob", "date_only")
    students_df_obj.convert_column_type(
        ["job_id", "num_course_taken", "current_career_path_id"], "int"
    )
    students_df_obj.convert_column_type("time_spent_hrs", "float")
    students_df_obj.extract_json_column("contact_info")

    student_jobs_df_obj = DataFrameInspector(student_jobs_df)
    student_jobs_df_obj.convert_column_type("avg_salary", "float")
    student_jobs_df_obj.drop_duplicates(subset=["job_id"])

    students_df_clean = students_df_obj.df
    student_jobs_df_clean = student_jobs_df_obj.df

    courses_df_clean = courses_df.copy()

    # Add synthetic "No path selected" row with career_path_id = 0
    no_path_row = pd.DataFrame({
        "career_path_id": [0],
        "career_path_name": ["No path selected"],
        "hours_to_complete": [0.0]
    })

    # Append to courses dataframe if not already present
    if 0 not in courses_df_clean["career_path_id"].values:
        courses_df_clean = pd.concat([courses_df_clean, no_path_row], ignore_index=True)
        logger.info("Added synthetic 'No path selected' row to courses table.")

    
    merged_student_courses_df = pd.merge(
        students_df_clean,
        courses_df_clean,
        left_on="current_career_path_id",
        right_on="career_path_id",
        how="left",
        suffixes=("_students", "_courses"),
    ).drop(columns=["career_path_id"])

    final_df = pd.merge(
        merged_student_courses_df, student_jobs_df_clean, on="job_id", how="left"
    )

    # 4. Validate with unit tests
    tests_passed, new_rows = run_unit_tests(
        students_df_clean, courses_df_clean, student_jobs_df_clean, final_df
    )
    if not tests_passed:
        logger.error("ETL process stopped due to failed tests.")
        sys.exit(1)

    # 5. Load into clean database
    try:
        conn_clean = sqlite3.connect(r"dev\cademycode_clean.db")

        # --- Master Table ---
        final_df.to_sql(
            "cademycode_master_students_table",
            conn_clean,
            if_exists="replace",
            index=False,
        )
        logger.info("Master table written successfully.")

        # --- Individual Tables ---
        students_df_clean.to_sql("students", conn_clean, if_exists="replace", index=False)
        courses_df_clean.to_sql("courses", conn_clean, if_exists="replace", index=False)
        student_jobs_df_clean.to_sql("students_jobs", conn_clean, if_exists="replace", index=False)
        conn_clean.commit()

        logger.info("Individual tables (students, courses, students_jobs) written successfully.")

    except Exception as e:
        logger.error(f"Error writing to clean database: {e}")
        sys.exit(1)

    # 6. Update changelog
    version = get_next_version()
    write_changelog(version, new_rows)
    logger.info(f"Changelog updated → Version {version}, {new_rows} new rows added.")

    # 7. Export master table to CSV (with newline fix)
    try:
        with open(r"dev\cademycode_master_students_table.csv", "w", encoding="utf-8", newline="") as f:
            final_df.to_csv(f, index=False)
        logger.info("Master table exported to CSV successfully (no blank lines).")
    except Exception as e:
        logger.error(f"Error exporting master table to CSV: {e}")
        sys.exit(1)
        
    conn.close()
    conn_clean.close()

if __name__ == "__main__":
    main()
