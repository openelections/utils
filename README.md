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

## License

See LICENSE file for details.

## Contributing

Submit issues and pull requests to this repository.
