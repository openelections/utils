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

## License

See LICENSE file for details.

## Contributing

Submit issues and pull requests to this repository.
