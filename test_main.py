import sqlite3
import pandas as pd
import pytest
from dataframeinspector import DataFrameInspector
from unit_tests import run_unit_tests


@pytest.fixture
def prepare_data():
    """Fixture to extract and clean data for testing."""
    conn = sqlite3.connect(r"dev\\cademycode.db")
    students_df = pd.read_sql_query("SELECT * FROM cademycode_students;", conn)
    courses_df = pd.read_sql_query("SELECT * FROM cademycode_courses;", conn)
    student_jobs_df = pd.read_sql_query("SELECT * FROM cademycode_student_jobs;", conn)

    # Clean students data
    students_df_obj = DataFrameInspector(students_df)
    students_df_obj.convert_column_type("dob", "date_only")
    students_df_obj.convert_column_type(
        ["job_id", "num_course_taken", "current_career_path_id"], "int"
    )
    students_df_obj.convert_column_type("time_spent_hrs", "float")
    students_df_obj.extract_json_column("contact_info")

    # Clean jobs data
    student_jobs_df_obj = DataFrameInspector(student_jobs_df)
    student_jobs_df_obj.convert_column_type("avg_salary", "float")
    student_jobs_df_obj.drop_duplicates(subset=["job_id"])

    students_df_clean = students_df_obj.df
    courses_df_clean = courses_df.copy()
    student_jobs_df_clean = student_jobs_df_obj.df

    # Add synthetic "No path selected" row
    no_path_row = pd.DataFrame({
        "career_path_id": [0],
        "career_path_name": ["No path selected"],
        "hours_to_complete": [0.0]
    })
    if 0 not in courses_df_clean["career_path_id"].values:
        courses_df_clean = pd.concat([courses_df_clean, no_path_row], ignore_index=True)

    merged_student_courses_df = pd.merge(
        students_df_clean,
        courses_df_clean,
        left_on="current_career_path_id",
        right_on="career_path_id",
        how="left",
    ).drop(columns=["career_path_id"])

    final_df = pd.merge(
        merged_student_courses_df, student_jobs_df_clean, on="job_id", how="left"
    )

    return students_df_clean, courses_df_clean, student_jobs_df_clean, final_df


def test_unit_tests_pass(prepare_data):
    """Ensure all data validation tests pass."""
    students_df_clean, courses_df_clean, student_jobs_df_clean, final_df = prepare_data
    tests_passed, new_rows = run_unit_tests(
        students_df_clean, courses_df_clean, student_jobs_df_clean, final_df
    )
    assert tests_passed, "Unit tests failed — see error.log"
