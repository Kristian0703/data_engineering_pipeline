import pandas as pd
import ast

class DataFrameInspector:
    """A class for examining pandas DataFrames with useful methods."""

    def __init__(
        self, df: pd.DataFrame
    ):  # pd.DataFrame is a type hint that tells Python (and anyone reading your code) that df is expected to be a pandas.DataFrame object.
        """Initialize with a pandas DataFrame."""
        self.df = df

    def examine(self) -> pd.DataFrame:  # return type hint
        """Return summary statistics for the DataFrame."""
        info_df = pd.DataFrame(
            {
                "Columns": self.df.columns,
                "Data Types": self.df.dtypes.values,
                "Null Values": self.df.isnull().sum().values,
                "Unique Values": self.df.nunique().values,
            }
        )
        info_df.reset_index(drop=True, inplace=True)
        return info_df

    def shape(self) -> tuple:
        """Return the shape (rows, columns) of the DataFrame."""
        return self.df.shape

    def head(self, n=5) -> pd.DataFrame:
        """Return the first n rows of the DataFrame."""
        return self.df.head(n)

    def describe(self) -> pd.DataFrame:
        """Return descriptive statistics for numeric columns."""
        return self.df.describe()

    def convert_column_type(self, column, new_type: str) -> None:
        """
        Convert one or more columns to a specified data type, with safe handling for numeric conversions.

        Parameters:
        column (str | list): Name of the column (or list of column names) to convert.
        new_type (str): Target type (e.g., 'int', 'float', 'str', 'category', 'datetime64[ns]', 'date_only').

        Raises:
        KeyError: If any column does not exist.
        ValueError: If conversion fails.
        """
        # Ensure column is a list for easier iteration
        columns = [column] if isinstance(column, str) else column
        if not isinstance(columns, list):
            raise TypeError("Column must be a string or list of strings.")

        # Check that all columns exist
        missing_cols = [col for col in columns if col not in self.df.columns]
        if missing_cols:
            raise KeyError(f"Columns not found in DataFrame: {missing_cols}")

        for col in columns:
            try:
                if new_type == "date_only":
                    self.df[col] = pd.to_datetime(
                        self.df[col], errors="coerce"
                    ).dt.normalize()
                    print(
                        f"✅ Column '{col}' converted to datetime64[ns] with no time."
                    )

                elif new_type == "int":
                    # First convert to numeric (handles '7.0', '3.5', etc.)
                    numeric_series = pd.to_numeric(self.df[col], errors="coerce")
                    # Drop/fill NaN as needed before converting to int
                    if numeric_series.isnull().any():
                        print(
                            f"⚠️ Column '{col}' contains NaN after numeric conversion. Filling with 0."
                        )
                        numeric_series = numeric_series.fillna(0)
                    self.df[col] = numeric_series.astype(int)
                    print(f"✅ Column '{col}' safely converted to int.")

                else:
                    self.df[col] = self.df[col].astype(new_type)
                    print(f"✅ Column '{col}' converted to {new_type}.")

            except Exception as e:
                raise ValueError(f"Could not convert column '{col}' to {new_type}: {e}")

    def extract_json_column(self, column: str) -> None:
        """
        Expand a column containing JSON/dictionary-like data into separate columns
        and drop the original column.

        Parameters:
        column (str): Name of the column containing JSON strings or dictionaries.

        Raises:
        KeyError: If column does not exist.
        ValueError: If data cannot be parsed into dictionaries.
        """
        if column not in self.df.columns:
            raise KeyError(f"Column '{column}' not found in DataFrame.")

        try:
            # Step 1: Convert string to dictionary if needed
            if isinstance(self.df[column].iloc[0], str):
                self.df[column] = self.df[column].apply(ast.literal_eval)

            # Step 2: Extract keys into new columns
            keys = list(self.df[column].iloc[0].keys())
            for key in keys:
                self.df[key] = self.df[column].apply(lambda x: x.get(key))

            # Step 3: Drop original column
            self.df.drop(columns=[column], inplace=True)
            print(
                f"✅ Extracted keys {keys} from '{column}' and dropped the original column."
            )

        except Exception as e:
            raise ValueError(f"Could not extract keys from column '{column}': {e}")
        
    def drop_duplicates(self, subset=None, keep="first", inplace=True) -> pd.DataFrame:
        """
        Drop duplicate rows from the DataFrame.

        Parameters:
        subset (list or str, optional): Column label(s) to consider when identifying duplicates.
                                        If None, considers all columns.
        keep ({'first', 'last', False}, default='first'):
            - 'first': Drop duplicates except for the first occurrence.
            - 'last': Drop duplicates except for the last occurrence.
            - False: Drop all duplicates.
        inplace (bool): Whether to modify the DataFrame in place (default True).
                        If False, returns a new DataFrame with duplicates removed.

        Returns:
        pd.DataFrame: DataFrame with duplicates removed (only returned if inplace=False).
        """
        before_rows = len(self.df)
        result = self.df.drop_duplicates(subset=subset, keep=keep)

        after_rows = len(result)
        removed = before_rows - after_rows
        print(f"✅ Dropped {removed} duplicate row(s). {after_rows} row(s) remain.")

        if inplace:
            self.df = result
        else:
            return result

