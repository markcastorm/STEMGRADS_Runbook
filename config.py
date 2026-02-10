# config.py
# STEMGRADS - UNESCO STEM Field Graduates Data Configuration

import os
from datetime import datetime

# =============================================================================
# DATA SOURCE CONFIGURATION
# =============================================================================

# UNESCO Data Portal
BASE_URL = 'http://data.uis.unesco.org/'
PROVIDER_NAME = 'UNESCO - United Nations Educational, Scientific and Cultural Organization'
DATASET_NAME = 'STEMGRADS'
DATASET_DESCRIPTION = 'STEM Field Graduates - Distribution of tertiary graduates by field of study'
FREQUENCY = 'Annual'

# Indicator to select
INDICATOR_NAME = 'Percentage of graduates from Science, Technology, Engineering and Mathematics programmes in tertiary education, both sexes (%)'

# =============================================================================
# TIME RANGE CONFIGURATION
# =============================================================================

# Time range is dynamically read from the website slider
# The slider provides: min="XXXX" max="XXXX" which changes over time
# No hardcoded years needed - scraper reads from slider attributes

# =============================================================================
# COUNTRY CODE MAPPING
# =============================================================================

# Maps country names (as they appear in UNESCO data) to output codes
COUNTRY_TO_CODE_MAP = {
    'Marshall Islands': 'STEMGRADS.MHL.A',
    'Azerbaijan': 'STEMGRADS.AZE.A',
    'Colombia': 'STEMGRADS.COL.A',
    'United Arab Emirates': 'STEMGRADS.ARE.A',
    'Czechia': 'STEMGRADS.CZE.A',
    'Gibraltar': 'STEMGRADS.GIB.A',
    'France': 'STEMGRADS.FRA.A',
    'Georgia': 'STEMGRADS.GEO.A',
    'Mongolia': 'STEMGRADS.MNG.A',
    'Sweden': 'STEMGRADS.SWE.A',
    'Turkey': 'STEMGRADS.TUR.A',
    'Ghana': 'STEMGRADS.GHA.A',
    'Hungary': 'STEMGRADS.HUN.A',
    'India': 'STEMGRADS.IND.A',
    'Jordan': 'STEMGRADS.JOR.A',
    'Lithuania': 'STEMGRADS.LTU.A',
    'El Salvador': 'STEMGRADS.SLV.A',
    'Ukraine': 'STEMGRADS.UKR.A',
    'Belarus': 'STEMGRADS.BLR.A',
    'Algeria': 'STEMGRADS.DZA.A',
    'Estonia': 'STEMGRADS.EST.A',
    'Mexico': 'STEMGRADS.MEX.A',
    'New Zealand': 'STEMGRADS.NZL.A',
    'Qatar': 'STEMGRADS.QAT.A',
    'Albania': 'STEMGRADS.ALB.A',
    'Bosnia and Herzegovina': 'STEMGRADS.BIH.A',
    'Sri Lanka': 'STEMGRADS.LKA.A',
    'Israel': 'STEMGRADS.ISR.A',
    'Rwanda': 'STEMGRADS.RWA.A',
    'Saudi Arabia': 'STEMGRADS.SAU.A',
    'Singapore': 'STEMGRADS.SGP.A',
    'Trinidad and Tobago': 'STEMGRADS.TTO.A',
    'Slovenia': 'STEMGRADS.SVN.A',
    'Tunisia': 'STEMGRADS.TUN.A',
    'Bulgaria': 'STEMGRADS.BGR.A',
    'Costa Rica': 'STEMGRADS.CRI.A',
    'Cuba': 'STEMGRADS.CUB.A',
    'Uzbekistan': 'STEMGRADS.UZB.A',
    'Armenia': 'STEMGRADS.ARM.A',
    'Burkina Faso': 'STEMGRADS.BFA.A',
    'Botswana': 'STEMGRADS.BWA.A',
    'Luxembourg': 'STEMGRADS.LUX.A',
    'Morocco': 'STEMGRADS.MAR.A',
    'North Macedonia': 'STEMGRADS.MKD.A',
    'Malta': 'STEMGRADS.MLT.A',
    'Panama': 'STEMGRADS.PAN.A',
    'Turks and Caicos Islands': 'STEMGRADS.TCA.A',
    'Canada': 'STEMGRADS.CAN.A',
    'Andorra': 'STEMGRADS.AND.A',
    'Denmark': 'STEMGRADS.DNK.A',
    'Greece': 'STEMGRADS.GRC.A',
    'Iceland': 'STEMGRADS.ISL.A',
    'Syrian Arab Republic': 'STEMGRADS.SYR.A',
    'Dominican Republic': 'STEMGRADS.DOM.A',
    'Egypt': 'STEMGRADS.EGY.A',
    'Sint Maarten (Dutch part)': 'STEMGRADS.SXM.A',
    'Oman': 'STEMGRADS.OMN.A',
    'Ecuador': 'STEMGRADS.ECU.A',
    'Croatia': 'STEMGRADS.HRV.A',
    'Philippines': 'STEMGRADS.PHL.A',
    'Samoa': 'STEMGRADS.WSM.A',
    'Turkmenistan': 'STEMGRADS.TKM.A',
    'Chad': 'STEMGRADS.TCD.A',
    'Madagascar': 'STEMGRADS.MDG.A',
    'Bermuda': 'STEMGRADS.BMU.A',
    'San Marino': 'STEMGRADS.SMR.A',
    'Slovakia': 'STEMGRADS.SVK.A',
    'Seychelles': 'STEMGRADS.SYC.A',
    'British Virgin Islands': 'STEMGRADS.VGB.A',
    'South Africa': 'STEMGRADS.ZAF.A',
    'Cyprus': 'STEMGRADS.CYP.A',
    'Ireland': 'STEMGRADS.IRL.A',
    'Kyrgyzstan': 'STEMGRADS.KGZ.A',
    'Australia': 'STEMGRADS.AUS.A',
    'Austria': 'STEMGRADS.AUT.A',
    'Belgium': 'STEMGRADS.BEL.A',
    'Switzerland': 'STEMGRADS.CHE.A',
    'Netherlands': 'STEMGRADS.NLD.A',
    'Poland': 'STEMGRADS.POL.A',
    'Palestine': 'STEMGRADS.PSE.A',
    'United States of America': 'STEMGRADS.USA.A',
    'Germany': 'STEMGRADS.DEU.A',
    'Spain': 'STEMGRADS.ESP.A',
    'United Kingdom of Great Britain and Northern Ireland': 'STEMGRADS.GBR.A',
    'Finland': 'STEMGRADS.FIN.A',
    'Italy': 'STEMGRADS.ITA.A',
    'Republic of Moldova': 'STEMGRADS.MDA.A',
    'Latvia': 'STEMGRADS.LVA.A',
    'Monaco': 'STEMGRADS.MCO.A',
    'Malaysia': 'STEMGRADS.MYS.A',
    'Mauritius': 'STEMGRADS.MUS.A',
    'Norway': 'STEMGRADS.NOR.A',
    'Romania': 'STEMGRADS.ROU.A',
    'Portugal': 'STEMGRADS.PRT.A',
    'Argentina': 'STEMGRADS.ARG.A',
    'Bahrain': 'STEMGRADS.BHR.A',
    'Belize': 'STEMGRADS.BLZ.A',
    'Chile': 'STEMGRADS.CHL.A',
    'Republic of Korea': 'STEMGRADS.KOR.A',
    'Lebanon': 'STEMGRADS.LBN.A',
    'China, Macao Special Administrative Region': 'STEMGRADS.MAC.A',
    'Serbia': 'STEMGRADS.SRB.A',
    'Uruguay': 'STEMGRADS.URY.A',
    'Thailand': 'STEMGRADS.THA.A',
    'Brazil': 'STEMGRADS.BRA.A',
    'Liechtenstein': 'STEMGRADS.LIE.A',
    'Benin': 'STEMGRADS.BEN.A',
    'Namibia': 'STEMGRADS.NAM.A',
}

# Column order in master file (matching existing master)
COLUMN_ORDER = [
    'STEMGRADS.MHL.A', 'STEMGRADS.AZE.A', 'STEMGRADS.COL.A', 'STEMGRADS.ARE.A',
    'STEMGRADS.CZE.A', 'STEMGRADS.GIB.A', 'STEMGRADS.FRA.A', 'STEMGRADS.GEO.A',
    'STEMGRADS.MNG.A', 'STEMGRADS.SWE.A', 'STEMGRADS.TUR.A', 'STEMGRADS.GHA.A',
    'STEMGRADS.HUN.A', 'STEMGRADS.IND.A', 'STEMGRADS.JOR.A', 'STEMGRADS.LTU.A',
    'STEMGRADS.SLV.A', 'STEMGRADS.UKR.A', 'STEMGRADS.BLR.A', 'STEMGRADS.DZA.A',
    'STEMGRADS.EST.A', 'STEMGRADS.MEX.A', 'STEMGRADS.NZL.A', 'STEMGRADS.QAT.A',
    'STEMGRADS.ALB.A', 'STEMGRADS.BIH.A', 'STEMGRADS.LKA.A', 'STEMGRADS.ISR.A',
    'STEMGRADS.RWA.A', 'STEMGRADS.SAU.A', 'STEMGRADS.SGP.A', 'STEMGRADS.TTO.A',
    'STEMGRADS.SVN.A', 'STEMGRADS.TUN.A', 'STEMGRADS.BGR.A', 'STEMGRADS.CRI.A',
    'STEMGRADS.CUB.A', 'STEMGRADS.UZB.A', 'STEMGRADS.ARM.A', 'STEMGRADS.BFA.A',
    'STEMGRADS.BWA.A', 'STEMGRADS.LUX.A', 'STEMGRADS.MAR.A', 'STEMGRADS.MKD.A',
    'STEMGRADS.MLT.A', 'STEMGRADS.PAN.A', 'STEMGRADS.TCA.A', 'STEMGRADS.CAN.A',
    'STEMGRADS.AND.A', 'STEMGRADS.DNK.A', 'STEMGRADS.GRC.A', 'STEMGRADS.ISL.A',
    'STEMGRADS.SYR.A', 'STEMGRADS.DOM.A', 'STEMGRADS.EGY.A', 'STEMGRADS.SXM.A',
    'STEMGRADS.OMN.A', 'STEMGRADS.ECU.A', 'STEMGRADS.HRV.A', 'STEMGRADS.PHL.A',
    'STEMGRADS.WSM.A', 'STEMGRADS.TKM.A', 'STEMGRADS.TCD.A', 'STEMGRADS.MDG.A',
    'STEMGRADS.BMU.A', 'STEMGRADS.SMR.A', 'STEMGRADS.SVK.A', 'STEMGRADS.SYC.A',
    'STEMGRADS.VGB.A', 'STEMGRADS.ZAF.A', 'STEMGRADS.CYP.A', 'STEMGRADS.IRL.A',
    'STEMGRADS.KGZ.A', 'STEMGRADS.AUS.A', 'STEMGRADS.AUT.A', 'STEMGRADS.BEL.A',
    'STEMGRADS.CHE.A', 'STEMGRADS.NLD.A', 'STEMGRADS.POL.A', 'STEMGRADS.PSE.A',
    'STEMGRADS.USA.A', 'STEMGRADS.DEU.A', 'STEMGRADS.ESP.A', 'STEMGRADS.GBR.A',
    'STEMGRADS.FIN.A', 'STEMGRADS.ITA.A', 'STEMGRADS.MDA.A', 'STEMGRADS.LVA.A',
    'STEMGRADS.MCO.A', 'STEMGRADS.MYS.A', 'STEMGRADS.MUS.A', 'STEMGRADS.NOR.A',
    'STEMGRADS.ROU.A', 'STEMGRADS.PRT.A', 'STEMGRADS.ARG.A', 'STEMGRADS.BHR.A',
    'STEMGRADS.BLZ.A', 'STEMGRADS.CHL.A', 'STEMGRADS.KOR.A', 'STEMGRADS.LBN.A',
    'STEMGRADS.MAC.A', 'STEMGRADS.SRB.A', 'STEMGRADS.URY.A', 'STEMGRADS.THA.A',
    'STEMGRADS.BRA.A', 'STEMGRADS.LIE.A', 'STEMGRADS.BEN.A', 'STEMGRADS.NAM.A',
]

# Code to description mapping for row 2 of master
CODE_TO_DESCRIPTION_MAP = {code: f"Percentage of graduates from Science, Technology, Engineering and Mathematics programmes in tertiary education, both sexes (%), {country}"
                           for country, code in COUNTRY_TO_CODE_MAP.items()}

# Reverse mapping: code to country name
CODE_TO_COUNTRY_MAP = {v: k for k, v in COUNTRY_TO_CODE_MAP.items()}

# =============================================================================
# TIMESTAMPED FOLDERS CONFIGURATION
# =============================================================================

RUN_TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
USE_TIMESTAMPED_FOLDERS = True

# =============================================================================
# DIRECTORY CONFIGURATION
# =============================================================================

# Project root
PROJECT_ROOT = r'D:\Projects\SIMBA-RUNBOOKS\STEMGRADS_Runbook'

# Master data file
MASTER_DATA_DIR = os.path.join(PROJECT_ROOT, 'Master Data')
MASTER_DATA_FILE = os.path.join(MASTER_DATA_DIR, 'Master_STEMGRADS_DATA.csv')

# Downloads directory (timestamped subfolders)
BASE_DOWNLOADS_DIR = os.path.join(PROJECT_ROOT, 'downloads')
if USE_TIMESTAMPED_FOLDERS:
    DOWNLOADS_DIR = os.path.join(BASE_DOWNLOADS_DIR, RUN_TIMESTAMP)
else:
    DOWNLOADS_DIR = BASE_DOWNLOADS_DIR

# Output directory
BASE_OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')
if USE_TIMESTAMPED_FOLDERS:
    OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, RUN_TIMESTAMP)
else:
    OUTPUT_DIR = BASE_OUTPUT_DIR

# Latest output directory
LATEST_OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, 'latest')

# Log directory
BASE_LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')
if USE_TIMESTAMPED_FOLDERS:
    LOG_DIR = os.path.join(BASE_LOG_DIR, RUN_TIMESTAMP)
else:
    LOG_DIR = BASE_LOG_DIR

# =============================================================================
# FILE NAMING PATTERNS
# =============================================================================

# Output file patterns (using YYYYMMDD format as per requirements)
DATE_STAMP = datetime.now().strftime('%Y%m%d')
DATA_FILE_PATTERN = 'STEMGRADS_DATA_{timestamp}.xls'
META_FILE_PATTERN = 'STEMGRADS_META_{timestamp}.xls'
ZIP_FILE_PATTERN = 'STEMGRADS_{timestamp}.zip'
LOG_FILE_PATTERN = 'stemgrads_{timestamp}.log'

# =============================================================================
# BROWSER CONFIGURATION
# =============================================================================

HEADLESS_MODE = False  # Set to False for debugging - see browser actions
DEBUG_MODE = True
WAIT_TIMEOUT = 60
PAGE_LOAD_DELAY = 5
DOWNLOAD_WAIT_TIMEOUT = 120
ELEMENT_WAIT_TIMEOUT = 30

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOG_LEVEL = 'DEBUG' if DEBUG_MODE else 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_TO_CONSOLE = True
LOG_TO_FILE = True

# =============================================================================
# ERROR HANDLING
# =============================================================================

CONTINUE_ON_ERROR = True
MAX_RETRIES = 3
RETRY_DELAY = 5.0
