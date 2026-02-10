# STEMGRADS Runbook

Automated data collection pipeline for UNESCO STEM Field Graduates data.

Scrapes the [UNESCO Institute for Statistics Data Browser](http://data.uis.unesco.org/), downloads the STEM graduates indicator, and updates a master CSV used to produce output files for downstream reporting.

---

## Indicator

**Percentage of graduates from Science, Technology, Engineering and Mathematics programmes in tertiary education, both sexes (%)**

- Source: UNESCO UIS Data Browser
- Indicator code: `FOSGP.5T8.F500600700`
- Frequency: Annual
- Coverage: 108 countries, years 1970–present (data available from 1998)

---

## Project Structure

```
STEMGRADS_Runbook/
│
├── orchestrator.py          # Main entry point — runs the full pipeline
├── scraper.py               # Selenium scraper — navigates UNESCO and downloads data
├── parser.py                # Parses downloaded Excel and updates master CSV
├── file_generator.py        # Generates output DATA, META, and ZIP files
├── config.py                # All configuration: paths, country mappings, browser settings
├── logger_setup.py          # Logging setup (console + timestamped log file)
│
├── Master Data/
│   └── Master_STEMGRADS_DATA.csv   # Cumulative master dataset (do not delete)
│
├── downloads/               # Raw downloads from UNESCO (timestamped subfolders)
├── output/                  # Generated output files (timestamped subfolders)
│   └── latest/              # Always contains the most recent output files
├── logs/                    # Run logs (timestamped subfolders)
└── project_information/     # Reference documents and sample data
```

---

## Setup

### Requirements

- Python 3.11+
- Google Chrome (matching version of ChromeDriver will be managed automatically)

### Install dependencies

```bash
pip install pandas numpy openpyxl xlwt selenium undetected-chromedriver
```

### Configuration

Edit [`config.py`](config.py) to adjust:

| Setting | Default | Description |
|---|---|---|
| `HEADLESS_MODE` | `False` | Set `True` to run Chrome without a visible window |
| `PROJECT_ROOT` | `D:\Projects\...` | Absolute path to this folder |
| `DOWNLOAD_WAIT_TIMEOUT` | `120` | Seconds to wait for the zip download to complete |
| `WAIT_TIMEOUT` | `60` | Selenium element wait timeout (seconds) |

---

## Running

```bash
python orchestrator.py
```

The pipeline runs 4 steps:

1. **Download** — Launches Chrome, navigates to the UNESCO Data Browser, selects the STEM indicator and all available years, exports as Excel, and downloads the zip file.
2. **Parse** — Extracts `data.xlsx` from the zip, reads the `geoUnit`/`year`/`value` columns, and maps ISO country codes to master column codes.
3. **Update Master** — Merges new data into `Master Data/Master_STEMGRADS_DATA.csv`. New values are added; existing values are updated only if they differ; unchanged values are skipped.
4. **Generate Output** — Produces `STEMGRADS_DATA_YYYYMMDD.xls`, `STEMGRADS_META_YYYYMMDD.xls`, and a ZIP, saved to `output/<timestamp>/` and copied to `output/latest/`.

---

## Output Files

| File | Description |
|---|---|
| `STEMGRADS_DATA_YYYYMMDD.xls` | Wide-format data: rows = years, columns = country codes |
| `STEMGRADS_META_YYYYMMDD.xls` | Metadata: indicator descriptions and country names |
| `STEMGRADS_YYYYMMDD.zip` | ZIP of both files above |

The `output/latest/` folder always contains the most recent set of files.

---

## Master CSV Format

`Master Data/Master_STEMGRADS_DATA.csv` has a fixed structure:

| Row | Content |
|---|---|
| Row 1 | Column codes (`STEMGRADS.AZE.A`, `STEMGRADS.FRA.A`, …) |
| Row 2 | Full indicator descriptions per country |
| Row 3+ | Year rows — column 1 is the year (integer), remaining columns are percentage values |

Values are stored at full float64 precision as downloaded from UNESCO. Empty cells indicate no data available for that country/year combination.

---

## Country Coverage

108 countries tracked, identified by ISO 3166-1 alpha-3 codes (e.g. `AZE`, `FRA`, `USA`). The mapping from ISO code to master column code is defined in `config.py` (`COUNTRY_TO_CODE_MAP`, `COLUMN_ORDER`).

Countries in the UNESCO export that are not in `COLUMN_ORDER` are silently skipped (logged as "Unmapped countries").

---

## Logs

Each run writes a timestamped log to `logs/<YYYYMMDD_HHMMSS>/stemgrads_<timestamp>.log` and also prints to the console. Log level is `DEBUG` when `DEBUG_MODE = True` in `config.py`.
