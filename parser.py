# parser.py
# Parser for STEMGRADS - Parse CSV and update master data

import os
import logging
import pandas as pd
import numpy as np
import config

logger = logging.getLogger(__name__)


class STEMGRADSParser:
    """Parses UNESCO CSV data and updates master CSV"""

    def __init__(self):
        self.logger = logger

    def parse_csv(self, csv_path):
        """
        Parse the downloaded UNESCO CSV file.

        Expected CSV format (from UNESCO "Text file CSV" export):
        - Columns: NATMON_Indicator, LOCATION, Country, TIME, Time, Value, Flag Codes, Flags

        Args:
            csv_path: Path to CSV file

        Returns:
            DataFrame with Country, Year, Value columns
        """

        self.logger.info(f"Parsing data file: {csv_path}")

        try:
            # Read file — handle both .xlsx and .csv
            ext = os.path.splitext(csv_path)[1].lower()
            if ext in ('.xlsx', '.xls'):
                # Try each sheet; use the first one that has data
                xl = pd.ExcelFile(csv_path)
                self.logger.info(f"Excel sheets: {xl.sheet_names}")
                df = None
                for sheet in xl.sheet_names:
                    candidate = xl.parse(sheet)
                    if not candidate.empty:
                        df = candidate
                        self.logger.info(f"Using sheet: '{sheet}'")
                        break
                if df is None:
                    self.logger.error("All Excel sheets are empty")
                    return None
            else:
                df = pd.read_csv(csv_path, encoding='utf-8')

            self.logger.info(f"Columns: {list(df.columns)}")
            self.logger.info(f"Rows: {len(df)}")

            # Identify the relevant columns
            # UNESCO CSV typically has: Country, TIME/Time, Value
            country_col = None
            time_col = None
            value_col = None

            # Find country column
            # Priority: geoUnit (ISO code, new Excel format) > Country > Location
            for col in df.columns:
                col_lower = col.lower()
                if col_lower == 'geounit':
                    country_col = col
                    break
                elif 'country' in col_lower and 'code' not in col_lower:
                    country_col = col
                    break
                elif col_lower == 'location':
                    country_col = col

            # Find time column
            for col in df.columns:
                col_lower = col.lower()
                if col_lower == 'time' or col_lower == 'year':
                    time_col = col
                    break
                elif 'time' in col_lower:
                    time_col = col

            # Find value column
            for col in df.columns:
                col_lower = col.lower()
                if col_lower == 'value':
                    value_col = col
                    break
                elif 'obs_value' in col_lower:
                    value_col = col

            if not country_col:
                self.logger.error("Could not find Country column")
                return None

            if not time_col:
                self.logger.error("Could not find Time column")
                return None

            if not value_col:
                self.logger.error("Could not find Value column")
                return None

            self.logger.info(f"Using columns - Country: {country_col}, Time: {time_col}, Value: {value_col}")

            # Extract relevant columns
            parsed_df = df[[country_col, time_col, value_col]].copy()
            parsed_df.columns = ['Country', 'Year', 'Value']

            # Convert Year to integer
            parsed_df['Year'] = pd.to_numeric(parsed_df['Year'], errors='coerce')
            parsed_df = parsed_df.dropna(subset=['Year'])
            parsed_df['Year'] = parsed_df['Year'].astype(int)

            # Handle Value column - keep zeros, convert non-numeric to NaN
            # Important: Zero is a valid value, do not discard it
            def convert_value(val):
                if pd.isna(val):
                    return np.nan
                if isinstance(val, (int, float)):
                    return val
                val_str = str(val).strip()
                if val_str == '' or val_str == '...' or val_str == '..' or val_str == '-':
                    return np.nan
                try:
                    return float(val_str)
                except ValueError:
                    return np.nan

            parsed_df['Value'] = parsed_df['Value'].apply(convert_value)

            # Log statistics
            total_records = len(parsed_df)
            valid_values = parsed_df['Value'].notna().sum()
            zero_values = (parsed_df['Value'] == 0).sum()

            self.logger.info(f"Parsed {total_records} records")
            self.logger.info(f"Valid values: {valid_values} (including {zero_values} zeros)")
            self.logger.info(f"Unique countries: {parsed_df['Country'].nunique()}")
            self.logger.info(f"Year range: {parsed_df['Year'].min()} - {parsed_df['Year'].max()}")

            return parsed_df

        except Exception as e:
            self.logger.error(f"Error parsing CSV: {e}")
            return None

    def load_master_data(self):
        """Load master CSV file"""

        if not os.path.exists(config.MASTER_DATA_FILE):
            self.logger.warning(f"Master file not found: {config.MASTER_DATA_FILE}")
            self.logger.info("Will create new master file")
            return None

        try:
            # Read master CSV - it has a special structure:
            # Row 0: Column codes (e.g., STEMGRADS.MHL.A)
            # Row 1: Column descriptions
            # Row 2+: Years and data

            df = pd.read_csv(config.MASTER_DATA_FILE, header=None)

            self.logger.info(f"Loaded master data: {df.shape}")
            return df

        except Exception as e:
            self.logger.error(f"Error loading master data: {e}")
            return None

    def create_empty_master(self):
        """Create an empty master DataFrame with proper structure"""

        # Create DataFrame with just header rows
        # Year rows will be added dynamically by update_master based on actual data

        # Create data rows
        data = []

        # Row 0: Codes
        code_row = [''] + config.COLUMN_ORDER
        data.append(code_row)

        # Row 1: Descriptions
        desc_row = ['']
        for code in config.COLUMN_ORDER:
            desc_row.append(config.CODE_TO_DESCRIPTION_MAP.get(code, ''))
        data.append(desc_row)

        # No year rows - they will be added from actual scraped data

        df = pd.DataFrame(data)

        self.logger.info(f"Created empty master: {df.shape}")

        return df

    def transform_to_wide_format(self, parsed_df):
        """
        Transform parsed data from long format to wide format.

        Input: DataFrame with Country, Year, Value
        Output: DataFrame with years as rows, country codes as columns
        """

        self.logger.info("Transforming to wide format...")

        try:
            parsed_df = parsed_df.copy()

            # Build a reverse map: ISO code (e.g. 'AZE') -> master code ('STEMGRADS.AZE.A')
            # Works whether Country column contains ISO codes (new Excel format) or full names (old CSV format)
            iso_to_master = {code.split('.')[1]: code for code in config.COLUMN_ORDER}

            def resolve_code(country_val):
                # If it's already an ISO code (3 uppercase letters), map directly
                if str(country_val).strip().upper() == str(country_val).strip() and len(str(country_val).strip()) == 3:
                    return iso_to_master.get(str(country_val).strip().upper())
                # Otherwise treat as country name and use the name map
                return config.COUNTRY_TO_CODE_MAP.get(country_val)

            parsed_df['Code'] = parsed_df['Country'].apply(resolve_code)

            # Log unmapped countries
            unmapped = parsed_df[parsed_df['Code'].isna()]['Country'].unique()
            if len(unmapped) > 0:
                self.logger.warning(f"Unmapped countries ({len(unmapped)}): {list(unmapped)[:10]}...")

            # Remove rows without valid code mapping
            parsed_df = parsed_df.dropna(subset=['Code'])

            # Pivot to wide format
            wide_df = parsed_df.pivot_table(
                index='Year',
                columns='Code',
                values='Value',
                aggfunc='first'  # In case of duplicates, take first
            )

            # Sort by year
            wide_df = wide_df.sort_index()

            self.logger.info(f"Wide format shape: {wide_df.shape}")
            self.logger.info(f"Year range: {wide_df.index.min()} - {wide_df.index.max()}")

            return wide_df

        except Exception as e:
            self.logger.error(f"Error transforming to wide format: {e}")
            return None

    def update_master(self, parsed_df):
        """
        Rebuild master CSV entirely from source data.

        The source is the single source of truth.  On every run the master
        data rows are wiped and rebuilt so that:
          - Removed data points in the source are removed from the master.
          - Updated values are reflected immediately.
          - Decimal precision is preserved exactly as-is from the source.
          - Only years that exist in the source are present (no empty rows).
          - Zeros are kept as valid data.

        Args:
            parsed_df: DataFrame with Country, Year, Value columns

        Returns:
            Rebuilt master DataFrame
        """

        self.logger.info("=" * 70)
        self.logger.info("REBUILDING MASTER DATA FROM SOURCE (full override)")
        self.logger.info("=" * 70)

        # Transform new data to wide format
        new_wide = self.transform_to_wide_format(parsed_df)

        if new_wide is None or new_wide.empty:
            self.logger.error("No valid data to rebuild")
            return None

        # --- Build header rows ---
        # Row 0: codes
        code_row = [''] + list(config.COLUMN_ORDER)
        # Row 1: descriptions
        desc_row = ['']
        for code in config.COLUMN_ORDER:
            desc_row.append(config.CODE_TO_DESCRIPTION_MAP.get(code, ''))

        num_cols = len(code_row)

        # --- Build data rows from source only ---
        data_rows = []
        total_values = 0

        for year in sorted(new_wide.index):
            year_int = int(year)
            row = [str(year_int)]  # first column is the year
            for code in config.COLUMN_ORDER:
                if code in new_wide.columns:
                    val = new_wide.loc[year, code]
                    if pd.notna(val):
                        # Store the raw float so decimal precision is preserved
                        row.append(val)
                        total_values += 1
                    else:
                        row.append('')
                else:
                    row.append('')
            data_rows.append(row)

        # Assemble full master
        all_rows = [code_row, desc_row] + data_rows
        master_df = pd.DataFrame(all_rows)

        self.logger.info("=" * 70)
        self.logger.info("REBUILD SUMMARY")
        self.logger.info("=" * 70)
        self.logger.info(f"Years in master: {len(data_rows)} ({sorted(new_wide.index)[0]} - {sorted(new_wide.index)[-1]})")
        self.logger.info(f"Countries tracked: {len(config.COLUMN_ORDER)}")
        self.logger.info(f"Total data values: {total_values}")
        self.logger.info(f"Total rows in master: {len(master_df)}")
        self.logger.info("=" * 70)

        # Save rebuilt master
        self.save_master_data(master_df)

        return master_df

    def save_master_data(self, df):
        """Save updated master CSV file"""

        try:
            os.makedirs(os.path.dirname(config.MASTER_DATA_FILE), exist_ok=True)

            # Fix year column: data rows (row 2+) must be stored as plain integers.
            # Column 0 is float64 because rows 0-1 have NaN (codes/descriptions).
            # Cast column to object dtype first, then write integer strings so pandas
            # writes '1970' not '1970.0'.
            df = df.copy()
            df[0] = df[0].astype(object)
            for idx in range(2, len(df)):
                val = df.iloc[idx, 0]
                try:
                    df.iloc[idx, 0] = str(int(float(val)))
                except (ValueError, TypeError):
                    pass

            # Save without header (structure is embedded in data)
            df.to_csv(config.MASTER_DATA_FILE, index=False, header=False)

            self.logger.info(f"Saved master data: {config.MASTER_DATA_FILE}")

        except Exception as e:
            self.logger.error(f"Error saving master data: {e}")


def main():
    """Test the parser with sample data"""
    from logger_setup import setup_logging

    setup_logging()

    # Test with existing downloaded file if available
    test_files = [
        os.path.join(config.DOWNLOADS_DIR, f)
        for f in os.listdir(config.DOWNLOADS_DIR)
        if f.endswith('.csv')
    ] if os.path.exists(config.DOWNLOADS_DIR) else []

    if test_files:
        parser = STEMGRADSParser()
        csv_file = test_files[0]

        parsed_data = parser.parse_csv(csv_file)

        if parsed_data is not None:
            print(f"\n[SUCCESS] Parsed {len(parsed_data)} records")
            print(f"Sample data:\n{parsed_data.head()}")

            # Test update
            updated_master = parser.update_master(parsed_data)

            if updated_master is not None:
                print(f"\n[SUCCESS] Updated master: {updated_master.shape}")
        else:
            print("\n[FAILED] Could not parse CSV")
    else:
        print("No CSV files found for testing")


if __name__ == '__main__':
    main()
