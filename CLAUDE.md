# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenElections Utils is a collection of Python utilities for processing and validating election data, specifically for the OpenElections project. The utilities are designed to be imported into state-specific OpenElections data repositories (e.g., openelections-data-tx, openelections-data-ca).

## Core Module: precinct_results.py

All functionality is contained in a single module `precinct_results.py` with no external dependencies beyond Python's standard library. The module uses these standard library modules:
- `csv` - CSV file reading/writing
- `glob` - File pattern matching
- `os` - File system operations
- `typing` - Type hints
- `difflib` - String similarity calculations
- `datetime` - Timestamp generation
- `enum` - Enumeration types

### Key Constants

- `STANDARD_COLUMNS`: Set of standard election CSV columns - `{'county', 'precinct', 'office', 'district', 'party', 'candidate'}`
- These columns are used to identify rows and distinguish vote type columns from metadata columns

## Main Utilities

### 1. Statewide Precinct Results Generator
**Function**: `generate_statewide_precinct_file()`

Consolidates county-level precinct CSV files into a single statewide file. The key insight is that different counties may have different vote type columns (e.g., some have `early_voting`, others have `mail`, etc.), so the utility:
1. First scans all files to discover all unique vote type columns
2. Then consolidates data, filling `None` for missing vote columns in each county

### 2. Party Variation Checker
**Functions**: `check_party_variations()`, `check_party_variations_directory()`

Detects inconsistent party naming (e.g., "DEM" vs "Democratic" vs "Democrat") using string similarity matching (`difflib.SequenceMatcher`). The `similarity_threshold` parameter (default 0.7) controls how strict the matching is.

### 3. Precinct Name Comparison
**Function**: `compare_precinct_names()`

Compares precinct names between two elections to identify:
- Removed precincts (only in election 1)
- Added precincts (only in election 2)
- Potential renames (based on string similarity)
- Case-only differences when `normalize_case=True`

### 4. CSV File Comparison
**Function**: `compare_csv_files()`

Comprehensive diff tool for election CSV files that:
- Auto-detects key columns from standard election columns
- Supports `exclude_from_key` parameter to exclude specific columns (e.g., 'candidate') from the row identifier
- Identifies missing/extra rows and columns
- Detects value mismatches with optional numeric tolerance
- Calculates vote totals and discrepancies
- Outputs to CLI (with ANSI colors), HTML web report, or both
- Can export differences to CSV for further analysis

**Important**: Uses row indexing with `_build_row_index()` to create a dictionary keyed by tuples of identifier columns. This allows O(1) lookups when comparing rows.

**Key Use Cases for `exclude_from_key`**:
- `exclude_from_key=['candidate']`: Compare rows based on precinct/office/party but across all candidates. Useful for verifying the same races appear in both files regardless of candidate name variations.
- `exclude_from_key=['candidate', 'party']`: Compare by precinct/office only. Useful for verifying total vote counts per race are consistent.

## Architecture Patterns

### Directory Change Pattern
Many functions temporarily change the working directory to scan files:
```python
original_dir = os.getcwd()
try:
    os.chdir(source_directory)
    for fname in glob.glob(file_pattern):
        # process files
finally:
    os.chdir(original_dir)
```
This pattern ensures the original directory is restored even if an exception occurs.

### Row Key Generation
The `_generate_row_key()` function creates a normalized tuple key from row data:
- Converts values to strings
- Strips whitespace
- Converts to lowercase
This ensures consistent matching even with minor formatting differences.

### Column Discovery
Vote type columns are discovered by set subtraction:
```python
headers = set(row.keys())
vote_columns = headers - STANDARD_COLUMNS
```

### Value Comparison with Tolerance
The `_compare_values()` function supports numeric tolerance:
- Attempts to parse values as floats
- If successful and difference is within tolerance, skips the difference
- If parsing fails, treats as string comparison
- Stores numeric difference for reporting

## Common Development Tasks

### Testing a Utility
All utilities can be tested using the example functions in `example_usage.py`. To test:
```bash
python3 -c "from example_usage import example_function_name; example_function_name()"
```

### Running the Module Directly
```bash
python3 precinct_results.py
```
This displays usage information and examples.

### Importing into State Repositories
The module is designed to be copied directly into state data repositories:
```bash
curl -O https://raw.githubusercontent.com/openelections/utils/main/precinct_results.py
```

## Development Conventions

### Type Hints
All functions use type hints for parameters and return values. Common types:
- `Optional[str]` for optional string parameters
- `List[str]` for lists of strings
- `Dict[str, Any]` for dictionaries with string keys and mixed values
- `Set[str]` for sets of strings
- `Tuple[str, ...]` for variable-length tuples

### Verbose Parameter
Most functions accept a `verbose: bool` parameter (default `True`) that controls progress output. Set to `False` when using in automation scripts.

### Return Value Structure
Functions that perform analysis typically return structured dictionaries with keys like:
- `metadata` - File info, timestamps, configuration
- `summary` - High-level statistics
- Detailed results by category (e.g., `value_differences`, `row_differences`)

### Output File Parameters
Many functions accept an optional `output_file` parameter to export detailed results to CSV. This allows programmatic analysis while keeping console output clean.

## File Naming Conventions

The utilities expect OpenElections standard naming:
- Precinct files: `{election_date}__{state}__{county}__precinct.csv`
- Example: `20201103__tx__travis__precinct.csv`
- File pattern matching: `{election_date}*precinct.csv`

## Data Format Expectations

### Input CSV Structure
- Must have headers
- Required columns depend on the function:
  - Statewide generator: `county`, `precinct`, `office`, `district`, `candidate`, `party` + vote columns
  - Comparison: At least some of the standard columns for row identification
- Vote columns can be any non-standard columns (e.g., `votes`, `early_voting`, `election_day`, `mail`)

### CSV Encoding
All CSV operations use UTF-8 encoding (explicitly specified in `_load_and_validate_csv()`).

## Color Output

The CLI comparison output uses ANSI color codes when `color=True`:
- Green (`\033[92m`) - Success, matches
- Red (`\033[91m`) - Errors, differences
- Yellow (`\033[93m`) - Warnings, partial matches
- Cyan (`\033[96m`) - Headers
- Bold (`\033[1m`) - Emphasis
- Reset (`\033[0m`) - End formatting

## Web Report Generation

The `_format_web_output()` function generates HTML reports with:
- Embedded CSS (no external dependencies)
- Responsive design
- Summary statistics cards
- Detailed difference tables

Note: The current implementation is basic (as noted in the function). Full interactive features (sorting, filtering) are planned for future enhancements.

## Error Handling Philosophy

- File operations: Raise `FileNotFoundError` or `ValueError` with descriptive messages
- CSV parsing: Catch `csv.Error` and wrap in `ValueError`
- Duplicate rows: Print warnings but continue processing (keeping last occurrence)
- Empty CSVs: Return empty sets/lists rather than raising errors
- Missing columns: Raise `ValueError` if required columns are missing

## Key Algorithm: Row Comparison

The CSV comparison uses a three-pass algorithm:
1. **Structure comparison**: Compare column sets to find missing/extra columns
2. **Row comparison**: Build indexes by key columns, find missing/extra rows using set operations
3. **Value comparison**: For common rows, compare non-key column values

This approach is efficient because:
- Indexing is O(n) for each file
- Set operations for finding differences are O(n)
- Value comparison only processes common rows

## Typical Workflows

### Creating Statewide File
1. Call `collect_all_vote_columns()` to discover all vote types
2. Define output column order (standard + vote columns)
3. Process each county file, adding rows with consistent column order
4. Write consolidated output

### Validating Data Changes
1. Use `compare_csv_files()` with original and modified files
2. Review summary statistics for acceptable error rates
3. Export differences to CSV if manual review needed
4. Generate HTML report for detailed analysis

### Checking Data Quality
1. Use `check_party_variations()` to identify naming inconsistencies
2. Use `compare_precinct_names()` between elections to validate precinct changes
3. Use `compare_csv_files()` to verify processing didn't introduce errors
