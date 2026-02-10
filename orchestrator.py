#!/usr/bin/env python3
# orchestrator.py
# Main orchestrator for STEMGRADS - UNESCO STEM Graduates Data Collection

import os
import sys
from datetime import datetime
import config
from logger_setup import setup_logging
from scraper import STEMGRADSScraper
from parser import STEMGRADSParser
from file_generator import STEMGRADSFileGenerator
import logging

logger = logging.getLogger(__name__)


def print_banner():
    """Print a welcome banner"""
    print("\n" + "=" * 70)
    print(" STEMGRADS - UNESCO STEM Field Graduates Data Collection")
    print(" Distribution of tertiary graduates by field of study")
    print("=" * 70 + "\n")


def print_configuration():
    """Print current configuration"""
    print("Configuration:")
    print("-" * 70)
    print(f"  Source URL: {config.BASE_URL}")
    print(f"  Dataset: {config.DATASET_NAME}")
    print(f"  Countries: {len(config.COUNTRY_TO_CODE_MAP)} mapped")
    print(f"  Year Range: Dynamic (read from website slider)")
    print(f"  Output: {config.OUTPUT_DIR}")
    print(f"  Master Data: {config.MASTER_DATA_FILE}")
    print(f"  Timestamp: {config.RUN_TIMESTAMP}")
    print("-" * 70 + "\n")


def main():
    """Main execution flow"""

    try:
        # Setup logging
        setup_logging()

        print_banner()
        print_configuration()

        # Step 1: Download data from UNESCO
        print("STEP 1: Downloading Data from UNESCO")
        print("=" * 70 + "\n")

        scraper = STEMGRADSScraper()
        csv_file = scraper.download_data()

        if not csv_file:
            logger.error("Failed to download data from UNESCO")
            print("\n[ERROR] Failed to download data. Exiting.")
            sys.exit(1)

        print(f"[SUCCESS] Downloaded: {os.path.basename(csv_file)}\n")
        logger.info(f"Successfully downloaded: {csv_file}")

        # Step 2: Parse downloaded data
        print("\nSTEP 2: Parsing Downloaded Data")
        print("=" * 70 + "\n")

        parser = STEMGRADSParser()
        parsed_data = parser.parse_csv(csv_file)

        if parsed_data is None or len(parsed_data) == 0:
            logger.error("Failed to parse downloaded data")
            print("\n[ERROR] Failed to parse data. Exiting.")
            sys.exit(1)

        print(f"[SUCCESS] Parsed {len(parsed_data)} records")
        print(f"  Countries: {parsed_data['Country'].nunique()}")
        print(f"  Year range: {parsed_data['Year'].min()} - {parsed_data['Year'].max()}")
        print(f"  Valid values: {parsed_data['Value'].notna().sum()}")
        print()

        logger.info(f"Successfully parsed {len(parsed_data)} records")

        # Step 3: Update master data
        print("\nSTEP 3: Updating Master Data")
        print("=" * 70 + "\n")

        updated_master_df = parser.update_master(parsed_data)

        if updated_master_df is None or len(updated_master_df) == 0:
            logger.error("No data was parsed or updated")
            print("\n[ERROR] No data was parsed or updated. Exiting.")
            sys.exit(1)

        print(f"[SUCCESS] Master data updated: {len(updated_master_df)} rows")
        print()

        logger.info(f"Successfully updated master with {len(updated_master_df)} rows")

        # Step 4: Generate output files
        print("\nSTEP 4: Generating Output Files")
        print("=" * 70 + "\n")

        generator = STEMGRADSFileGenerator()
        output_files = generator.generate_files(updated_master_df)

        if not output_files:
            logger.error("Failed to generate output files")
            print("\n[ERROR] Failed to generate output files. Exiting.")
            sys.exit(1)

        # Step 5: Summary
        print("\n" + "=" * 70)
        print(" EXECUTION COMPLETE")
        print("=" * 70 + "\n")

        print("Summary:")
        print(f"  Total rows in master: {len(updated_master_df)}")
        print(f"  Countries tracked: {len(config.COUNTRY_TO_CODE_MAP)}")
        print()

        print("Output files:")
        if output_files.get('data_file'):
            print(f"  DATA: {os.path.basename(output_files['data_file'])}")
        if output_files.get('meta_file'):
            print(f"  META: {os.path.basename(output_files['meta_file'])}")
        if output_files.get('zip_file'):
            print(f"  ZIP:  {os.path.basename(output_files['zip_file'])}")
        print()

        if output_files.get('data_file'):
            print(f"Output directory: {os.path.dirname(output_files['data_file'])}")
        print(f"Latest files: {config.LATEST_OUTPUT_DIR}")
        print(f"Master data: {config.MASTER_DATA_FILE}")
        print()

        print("=" * 70 + "\n")

        logger.info("Orchestrator completed successfully")

        return 0

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Process interrupted by user")
        logger.warning("Process interrupted by user")
        sys.exit(130)

    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        logger.exception("Unexpected error in orchestrator")
        sys.exit(1)


if __name__ == '__main__':
    sys.exit(main())
