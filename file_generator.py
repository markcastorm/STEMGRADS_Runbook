# file_generator.py
# Generate output files for STEMGRADS data (XLS, META, ZIP)

import os
import logging
import shutil
import zipfile
import pandas as pd
from datetime import datetime
import config

logger = logging.getLogger(__name__)


class STEMGRADSFileGenerator:
    """Generates output files (DATA XLS, META XLS, ZIP) from master data"""

    def __init__(self):
        self.logger = logger

    def create_data_file(self, master_df, output_dir):
        """
        Create DATA XLS file from master DataFrame.

        Format: STEMGRADS_DATA_YYYYMMDD.xls
        Structure:
        - Row 1: Time series codes
        - Row 2: Time series descriptions
        - Row 3+: Year and values

        Args:
            master_df: Master DataFrame with all data
            output_dir: Directory to save file

        Returns:
            str: Path to created file
        """

        self.logger.info("Creating DATA file...")

        try:
            # Generate filename with current date
            date_stamp = datetime.now().strftime('%Y%m%d')
            filename = f'STEMGRADS_DATA_{date_stamp}.xls'
            filepath = os.path.join(output_dir, filename)

            # Master already has proper structure:
            # Row 0: codes, Row 1: descriptions, Row 2+: data

            # Save to XLS format
            master_df.to_excel(filepath, index=False, header=False, engine='openpyxl')

            self.logger.info(f"Created DATA file: {filename}")
            return filepath

        except Exception as e:
            self.logger.error(f"Error creating DATA file: {e}")
            return None

    def create_meta_file(self, output_dir):
        """
        Create METADATA XLS file.

        Format: STEMGRADS_META_YYYYMMDD.xls
        Contains static metadata about the time series.

        Args:
            output_dir: Directory to save file

        Returns:
            str: Path to created file
        """

        self.logger.info("Creating META file...")

        try:
            # Generate filename with current date
            date_stamp = datetime.now().strftime('%Y%m%d')
            filename = f'STEMGRADS_META_{date_stamp}.xls'
            filepath = os.path.join(output_dir, filename)

            # Calculate next release date (next September or end of month)
            now = datetime.now()
            if now.month < 9:
                next_release = datetime(now.year, 9, 30, 12, 0, 0)
            else:
                next_release = datetime(now.year + 1, 9, 30, 12, 0, 0)

            next_release_str = next_release.strftime('%Y-%m-%dT%H:%M:%S')

            # Create metadata rows
            meta_data = []

            # Header row
            meta_data.append([
                'TS_CODE',
                'TS_DESCRIPTION',
                'PROVIDER',
                'DATASET',
                'FREQUENCY',
                'COUNTRY',
                'UNIT',
                'SOURCE_URL',
                'NEXT_RELEASE_DATE'
            ])

            # Data rows for each time series
            for code in config.COLUMN_ORDER:
                country = config.CODE_TO_COUNTRY_MAP.get(code, '')
                description = config.CODE_TO_DESCRIPTION_MAP.get(code, '')

                meta_data.append([
                    code,
                    description,
                    config.PROVIDER_NAME,
                    config.DATASET_NAME,
                    config.FREQUENCY,
                    country,
                    'Percent',
                    config.BASE_URL,
                    next_release_str
                ])

            # Create DataFrame and save
            meta_df = pd.DataFrame(meta_data)
            meta_df.to_excel(filepath, index=False, header=False, engine='openpyxl')

            self.logger.info(f"Created META file: {filename}")
            return filepath

        except Exception as e:
            self.logger.error(f"Error creating META file: {e}")
            return None

    def create_zip_file(self, data_file, meta_file, output_dir):
        """
        Create ZIP file containing DATA and META files.

        Format: STEMGRADS_YYYYMMDD.zip

        Args:
            data_file: Path to DATA file
            meta_file: Path to META file
            output_dir: Directory to save ZIP

        Returns:
            str: Path to created ZIP file
        """

        self.logger.info("Creating ZIP file...")

        try:
            # Generate filename with current date
            date_stamp = datetime.now().strftime('%Y%m%d')
            zip_filename = f'STEMGRADS_{date_stamp}.zip'
            zip_filepath = os.path.join(output_dir, zip_filename)

            # Create ZIP
            with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add DATA file
                if data_file and os.path.exists(data_file):
                    zipf.write(data_file, os.path.basename(data_file))
                    self.logger.info(f"Added to ZIP: {os.path.basename(data_file)}")

                # Add META file
                if meta_file and os.path.exists(meta_file):
                    zipf.write(meta_file, os.path.basename(meta_file))
                    self.logger.info(f"Added to ZIP: {os.path.basename(meta_file)}")

            self.logger.info(f"Created ZIP file: {zip_filename}")
            return zip_filepath

        except Exception as e:
            self.logger.error(f"Error creating ZIP file: {e}")
            return None

    def copy_to_latest(self, files, latest_dir):
        """
        Copy files to 'latest' directory.

        Args:
            files: Dict of file paths
            latest_dir: Path to latest directory
        """

        self.logger.info("Copying files to 'latest' directory...")

        try:
            # Create latest directory
            os.makedirs(latest_dir, exist_ok=True)

            # Remove all existing files in latest directory
            for existing_file in os.listdir(latest_dir):
                file_path = os.path.join(latest_dir, existing_file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    self.logger.debug(f"Removed old file: {existing_file}")

            # Copy new files
            for file_type, filepath in files.items():
                if filepath and os.path.exists(filepath):
                    dest = os.path.join(latest_dir, os.path.basename(filepath))
                    shutil.copy2(filepath, dest)
                    self.logger.info(f"Copied {file_type}: {os.path.basename(filepath)}")

        except Exception as e:
            self.logger.error(f"Error copying to latest: {e}")

    def generate_files(self, master_df):
        """
        Main method: Generate all output files.

        Args:
            master_df: Master DataFrame with all data

        Returns:
            dict with paths to all generated files
        """

        self.logger.info("=" * 70)
        self.logger.info("GENERATING OUTPUT FILES")
        self.logger.info("=" * 70)

        # Create output directory
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)

        output_files = {}

        # Create DATA file
        data_file = self.create_data_file(master_df, config.OUTPUT_DIR)
        output_files['data_file'] = data_file

        # Create META file
        meta_file = self.create_meta_file(config.OUTPUT_DIR)
        output_files['meta_file'] = meta_file

        # Create ZIP file
        zip_file = self.create_zip_file(data_file, meta_file, config.OUTPUT_DIR)
        output_files['zip_file'] = zip_file

        # Copy to latest directory
        self.copy_to_latest(output_files, config.LATEST_OUTPUT_DIR)

        self.logger.info("=" * 70)

        return output_files


def main():
    """Test the file generator"""
    from logger_setup import setup_logging

    setup_logging()

    # Load master data for testing
    if os.path.exists(config.MASTER_DATA_FILE):
        master_df = pd.read_csv(config.MASTER_DATA_FILE, header=None)

        generator = STEMGRADSFileGenerator()
        output_files = generator.generate_files(master_df)

        if output_files:
            print("\n[SUCCESS] Files generated")
            for file_type, filepath in output_files.items():
                if filepath:
                    print(f"  {file_type}: {filepath}")
        else:
            print("\n[FAILED] Could not generate files")
    else:
        print(f"Master file not found: {config.MASTER_DATA_FILE}")


if __name__ == '__main__':
    main()
