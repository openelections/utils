# OpenElections Utils

General data processing utilities for OpenElections projects.

## Precinct Results Generator

A Python utility for consolidating county-level precinct CSV files into statewide precinct results files.

### Overview

This module provides functionality to merge multiple county-level precinct result CSV files into a single statewide file. It automatically introspects vote type columns (such as `early_voting`, `election_day`, `mail`, `absentee`, `provisional`, etc.) and handles varying data structures across counties.

**Based on:** [openelections-data-tx statewide_generator.py](https://github.com/openelections/openelections-data-tx/blob/master/statewide_generator.py)

### Features

- **Automatic column introspection**: Discovers vote type columns by excluding standard columns (`county`, `precinct`, `office`, `district`, `party`, `candidate`)
- **Flexible data handling**: Works with any combination of vote type columns across different counties
- **Office filtering**: Optionally include only specific offices
- **Custom file patterns**: Support for different file naming conventions
- **Reporting**: Generate reports showing which vote columns are present in each county
- **Reusable**: Designed to be imported into any OpenElections state repository

### Installation

Copy `precinct_results.py` to your OpenElections data repository:

```bash
# From your openelections-data-XX repository
curl -O https://raw.githubusercontent.com/openelections/utils/main/precinct_results.py
```

### Quick Start

```python
from precinct_results import generate_statewide_precinct_file

generate_statewide_precinct_file(
    state_abbr='tx',
    election_date='20201103',
    source_directory='2020/counties',
    output_file='20201103__tx__general__precinct.csv'
)
```

### Usage Examples

#### With Office Filtering

```python
offices = ['President', 'U.S. Senate', 'U.S. House', 'Governor']

generate_statewide_precinct_file(
    state_abbr='tx',
    election_date='20201103',
    source_directory='2020/counties',
    output_file='20201103__tx__general__precinct.csv',
    offices_filter=offices
)
```

#### Custom File Pattern

```python
generate_statewide_precinct_file(
    state_abbr='ca',
    election_date='20201103',
    source_directory='2020/counties',
    output_file='20201103__ca__general__precinct.csv',
    file_pattern='*_precinct_results.csv'
)
```

#### Generate Vote Columns Report

```python
from precinct_results import generate_vote_columns_report

generate_vote_columns_report(
    source_directory='2020/counties',
    file_pattern='20201103*precinct.csv',
    output_file='vote_columns_report.csv'
)
```

See `example_usage.py` for more comprehensive examples.

### API Reference

#### `generate_statewide_precinct_file()`

Generate a consolidated statewide precinct results file from county CSV files.

**Parameters:**

- `state_abbr` (str): Two-letter state abbreviation (e.g., 'tx', 'ca')
- `election_date` (str): Election date in YYYYMMDD format (e.g., '20201103')
- `source_directory` (str): Directory containing county precinct CSV files
- `output_file` (str): Path for the output consolidated CSV file
- `file_pattern` (str, optional): Glob pattern for matching files. Defaults to `'{election_date}*precinct.csv'`
- `offices_filter` (list, optional): List of office names to include. If None, includes all offices
- `verbose` (bool, optional): If True, print progress messages. Defaults to True

#### `generate_vote_columns_report()`

Generate a report showing which vote type columns are present in each county file.

**Parameters:**

- `source_directory` (str): Directory containing county precinct CSV files
- `file_pattern` (str): Glob pattern for matching files
- `output_file` (str): Path for the output report CSV file
- `verbose` (bool, optional): If True, print progress messages. Defaults to True

### How It Works

1. **Column Discovery**: Scans all matching CSV files and identifies vote type columns by excluding standard columns
2. **Column Unification**: Collects all unique vote type columns across all counties
3. **Data Consolidation**: Reads each county file and consolidates into the output with consistent column ordering
4. **Missing Data Handling**: Fills `None` for vote type columns not present in a particular county

### Input Format

County-level CSV files should have:

**Required columns:**
- `county`, `precinct`, `office`, `district`, `candidate`, `party`

**Vote type columns (any combination):**
- `votes`, `early_voting`, `election_day`, `mail`, `absentee`, `provisional`, etc.

### Output Format

- Standard columns first: `county`, `precinct`, `office`, `district`, `candidate`, `party`
- All discovered vote type columns in sorted order
- One row per precinct/office/candidate combination

## Party Variation Checker

Utilities to detect inconsistent party naming conventions in CSV files.

### Overview

These functions help identify variations in party values (e.g., "DEM", "Democratic", "Democrat") that likely refer to the same political party. This is useful for:

- Data quality assurance
- Identifying data entry inconsistencies
- Standardizing party names before processing

### Features

- **Single file analysis**: Check party variations in a single CSV file
- **Directory-wide analysis**: Check party variations across multiple files
- **Similarity detection**: Uses string similarity to identify potential variations
- **Frequency reporting**: Shows occurrence counts for each party value
- **Optional CSV reports**: Export detailed analysis to CSV files

### Quick Start

#### Check a Single CSV File

```python
from precinct_results import check_party_variations

results = check_party_variations('20201103__tx__general__precinct.csv')
print(results['unique_parties'])
print(results['potential_variations'])
```

#### Check Multiple Files in a Directory

```python
from precinct_results import check_party_variations_directory

results = check_party_variations_directory(
    source_directory='2020/counties',
    file_pattern='20201103*precinct.csv',
    output_file='party_variations_report.csv'
)
```

### API Reference

#### `check_party_variations()`

Check for variations in party values within a single CSV file.

**Parameters:**

- `csv_path` (str): Path to the CSV file to analyze
- `similarity_threshold` (float, optional): Minimum similarity (0.0-1.0) for variation detection. Default: 0.7
- `output_file` (str, optional): Path to write detailed variation report
- `verbose` (bool, optional): If True, print summary and variations found. Default: True

**Returns:**

Dictionary with:
- `unique_parties`: Set of all unique party values found
- `total_count`: Total number of party occurrences
- `party_counts`: Dict mapping party value to occurrence count
- `potential_variations`: List of (party1, party2, similarity) tuples
- `empty_count`: Number of rows with empty/missing party values

#### `check_party_variations_directory()`

Check for party value variations across multiple CSV files in a directory.

**Parameters:**

- `source_directory` (str): Directory containing CSV files
- `file_pattern` (str): Glob pattern for matching files (e.g., '20201103*precinct.csv')
- `similarity_threshold` (float, optional): Minimum similarity (0.0-1.0) for variation detection. Default: 0.7
- `output_file` (str, optional): Path to write detailed variation report
- `verbose` (bool, optional): If True, print summary and variations found. Default: True

**Returns:**

Dictionary with:
- `all_parties`: Set of all unique party values across all files
- `by_file`: Dict mapping filename to set of party values in that file
- `potential_variations`: List of (party1, party2, similarity) tuples
- `file_count`: Number of files processed

### Example Output

```
Party Value Analysis:
  Total rows with party values: 125000
  Empty/missing party values: 150
  Unique party values found: 8

Party value frequency:
    DEM: 55000
    REP: 52000
    Democratic: 8500
    Republican: 7200
    LIB: 1800
    GRN: 450
    IND: 50

Potential variations detected: 2
    'DEM' (n=55000) ↔ 'Democratic' (n=8500) - similarity: 0.82
    'REP' (n=52000) ↔ 'Republican' (n=7200) - similarity: 0.79
```

## Precinct Name Comparison

See the `compare_precinct_names()` function for comparing precinct names between elections.

## CSV File Comparison

A comprehensive utility for comparing two CSV election files to identify and report differences.

### Overview

The `compare_csv_files()` function compares two CSV files from the same state, county, and election to detect:
- Missing rows (rows in File A but not in File B)
- Extra rows (rows in File B but not in File A)
- Value mismatches in matching rows
- Structural differences (missing/extra columns)
- Vote total discrepancies

This is useful for:
- Data validation and quality assurance
- Verifying corrections were applied correctly
- Comparing original source data vs. processed data
- Migration testing and format validation

### Features

- **Flexible row identification**: Auto-detects key columns or accepts custom column specification
- **Multiple output formats**: Terminal (CLI), HTML web report, or both
- **CSV export**: Export detailed differences for further analysis
- **Numeric tolerance**: Optionally ignore small numeric differences
- **Column filtering**: Exclude specific columns from comparison
- **Vote total analysis**: Automatic calculation and comparison of vote totals
- **Color-coded output**: Easy-to-read terminal output with ANSI colors
- **Detailed reporting**: Summary statistics plus detailed difference listings

### Quick Start

#### Basic Comparison
```python
from precinct_results import compare_csv_files

# Compare two files
results = compare_csv_files(
    'original.csv',
    'corrected.csv',
    verbose=True
)

# Check if files match
if results['summary']['percentage_match'] == 100.0:
    print("Files are identical!")
```

#### Generate Web Report
```python
compare_csv_files(
    'file_a.csv',
    'file_b.csv',
    output_format='web',
    output_file='comparison_report.html'
)
# Open comparison_report.html in a browser
```

#### Export Differences to CSV
```python
compare_csv_files(
    'file_a.csv',
    'file_b.csv',
    csv_export='differences.csv',
    verbose=True
)
# Opens in Excel or can be imported for analysis
```

### API Reference

#### `compare_csv_files()`

Compare two CSV files and report differences.

**Parameters:**

- `file_a` (str): Path to first CSV file
- `file_b` (str): Path to second CSV file
- `key_columns` (list, optional): Columns to use as row identifier. If None, auto-detects from standard election columns (county, precinct, office, district, candidate, party)
- `ignore_columns` (list, optional): Columns to exclude from comparison
- `tolerance` (float, optional): Numeric comparison tolerance (default: 0.0)
- `max_differences` (int, optional): Stop after N differences (default: unlimited)
- `output_format` (str, optional): Output format - 'cli', 'web', or 'both' (default: 'cli')
- `output_file` (str, optional): Output file path (HTML for web, text for cli)
- `csv_export` (str, optional): Export detailed differences to CSV file
- `verbose` (bool, optional): Print detailed output (default: True)
- `color` (bool, optional): Use colored terminal output (default: True)

**Returns:**

Dictionary with comparison results containing:
- `metadata`: File information and timestamps
- `summary`: High-level statistics (match percentage, difference counts)
- `column_differences`: Missing/extra columns
- `row_differences`: Missing/extra rows
- `value_differences`: Value mismatches with details
- `vote_totals`: Vote totals and differences by vote type

### Usage Examples

#### Compare with Custom Key Columns
```python
# If your CSV has different structure, specify key columns
results = compare_csv_files(
    'file_a.csv',
    'file_b.csv',
    key_columns=['county', 'precinct', 'office', 'candidate']
)
```

#### Ignore Specific Columns
```python
# Exclude columns you know will differ
compare_csv_files(
    'file_a.csv',
    'file_b.csv',
    ignore_columns=['provisional', 'absentee']
)
```

#### Use Numeric Tolerance
```python
# Ignore differences of 5 votes or less
compare_csv_files(
    'file_a.csv',
    'file_b.csv',
    tolerance=5.0
)
```

#### Quiet Mode for Automation
```python
# For use in scripts/CI pipelines
results = compare_csv_files(
    'file_a.csv',
    'file_b.csv',
    verbose=False,
    color=False
)

if results['summary']['total_differences'] > 0:
    print(f"FAIL: {results['summary']['total_differences']} differences")
    exit(1)
else:
    print("PASS: Files match")
    exit(0)
```

#### Analyze Specific Difference Types
```python
results = compare_csv_files('file_a.csv', 'file_b.csv', verbose=False)

# Analyze vote total discrepancies
for vote_type, diff in results['vote_totals']['differences'].items():
    if diff != 0:
        print(f"{vote_type}: {diff:+,} vote difference")

# Count mismatches by column
mismatches_by_column = {}
for diff in results['value_differences']:
    col = diff['column']
    mismatches_by_column[col] = mismatches_by_column.get(col, 0) + 1

for col, count in sorted(mismatches_by_column.items()):
    print(f"{col}: {count} mismatch(es)")
```

#### Data Quality Validation Workflow
```python
# Complete validation workflow
results = compare_csv_files(
    'original.csv',
    'processed.csv',
    csv_export='validation_differences.csv',
    verbose=False
)

acceptable_error_rate = 1.0  # 1%
error_rate = 100.0 - results['summary']['percentage_match']

if error_rate <= acceptable_error_rate:
    print("✓ PASS: Error rate within acceptable threshold")
else:
    print("✗ FAIL: Error rate exceeds threshold")
    # Generate detailed HTML report for review
    compare_csv_files(
        'original.csv',
        'processed.csv',
        output_format='web',
        output_file='validation_report.html',
        verbose=False
    )
```

### Output Examples

#### Terminal Output (CLI)
```
CSV Comparison Report
======================================================================

Files:
  File A: original.csv
  File B: corrected.csv

Structure:
  Rows:    1,234 vs 1,235 (+1)
  Columns: 12 vs 12 (identical)

Results:
  ✓ Identical rows:      1,180 (95.6%)
  ✗ Missing rows:        10   (0.8%)
  ✗ Extra rows:          11   (0.9%)
  ✗ Value mismatches:    34   (2.7%)

Vote Totals:
  early_voting         File A: 125,432  File B: 125,450  (Δ +18)
  election_day         File A: 234,567  File B: 234,567  (✓ Match)
  mail                 File A: 45,678   File B: 45,680   (Δ +2)

Overall Match: 95.6%
```

#### Web Report
The HTML report includes:
- Summary dashboard with match rate and difference counts
- Interactive tables showing all differences
- Vote total comparison charts
- Sortable and filterable difference listings
- Responsive design for desktop/mobile

#### CSV Export
Exported CSV includes columns:
- `type`: Type of difference (missing_row, extra_row, value_mismatch)
- `county`, `precinct`, `office`, `district`, `candidate`, `party`: Row identification
- `column`: Column with difference (for value mismatches)
- `value_a`, `value_b`: Values from each file
- `difference`: Numeric difference (if applicable)
- `notes`: Additional information

### Integration with Existing Workflows

```python
# Example: Compare before and after correction
from precinct_results import compare_csv_files

# Step 1: Make corrections
# ... your correction code ...

# Step 2: Validate corrections
results = compare_csv_files(
    'before_correction.csv',
    'after_correction.csv',
    csv_export='corrections_applied.csv',
    output_format='web',
    output_file='correction_report.html'
)

# Step 3: Verify expected changes
print(f"Corrections applied: {results['summary']['value_mismatches']}")
print(f"Match rate: {results['summary']['percentage_match']:.1f}%")
```

See `example_usage.py` for more comprehensive examples.

## License

See LICENSE file for details.

## Contributing

Submit issues and pull requests to this repository.
