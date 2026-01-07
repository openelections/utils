# CSV Election Comparison Utility - Implementation Plan

## Executive Summary

This document outlines the design and implementation plan for a utility that compares two CSV files from the same state, county, and election to identify and report differences. The utility will support both command-line and web-based output formats.

## Background

### Context
OpenElections processes election data from multiple sources. It's common to need to compare:
- Original source data vs. processed data
- Pre-correction vs. post-correction versions
- Data from different collection methods
- Merged files vs. individual county files

### Use Cases
1. **Data Validation**: Verify that data processing didn't introduce errors
2. **Quality Assurance**: Identify discrepancies before publishing
3. **Correction Verification**: Ensure corrections were applied correctly
4. **Migration Testing**: Validate data integrity after format changes

## Requirements

### Functional Requirements

#### FR1: File Input
- Accept two CSV file paths as input
- Validate that both files exist and are readable
- Support files of varying sizes (from small county files to large statewide files)

#### FR2: Difference Detection
The utility must detect and report:
1. **Structural differences**:
   - Column differences (columns in one file but not the other)
   - Row count differences
2. **Row-level differences**:
   - Missing rows (in File A but not File B)
   - Extra rows (in File B but not File A)
3. **Value differences**:
   - Cell value mismatches for the same logical row
   - Vote total discrepancies
4. **Data quality issues**:
   - Empty/null value differences
   - Data type inconsistencies

#### FR3: Command-Line Output
Provide a terminal-based output that includes:
- High-level summary statistics
- Detailed difference listings
- Optional verbosity levels
- Color-coded output for better readability
- Export to CSV for further analysis

#### FR4: Web-Based Output
Generate an HTML report that includes:
- Interactive summary dashboard
- Sortable and filterable tables
- Visual charts and graphs
- Side-by-side comparison view
- Export capabilities (CSV, JSON)

#### FR5: Configuration Options
- Specify key columns for row identification
- Filter differences by type
- Set tolerance thresholds for numeric comparisons
- Control output detail level

### Non-Functional Requirements

#### NFR1: Performance
- Process files with 100K+ rows in reasonable time (<30 seconds)
- Memory-efficient for large files (streaming where possible)

#### NFR2: Usability
- Clear, actionable error messages
- Progress indicators for large files
- Intuitive command-line interface

#### NFR3: Maintainability
- Follow existing codebase patterns
- Well-documented code
- Comprehensive examples

#### NFR4: Compatibility
- Python 3.7+
- Minimal external dependencies
- Cross-platform (Linux, macOS, Windows)

## Design

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                  CSV Comparison Utility              │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌─────────────────┐                                │
│  │  File Loader    │  - Read CSV files               │
│  │  & Validator    │  - Validate structure           │
│  └────────┬────────┘                                 │
│           │                                           │
│  ┌────────▼────────┐                                │
│  │  Row Identifier │  - Generate unique keys         │
│  │  & Indexer      │  - Build lookup indices         │
│  └────────┬────────┘                                 │
│           │                                           │
│  ┌────────▼────────┐                                │
│  │  Comparison     │  - Detect differences           │
│  │  Engine         │  - Categorize changes           │
│  └────────┬────────┘                                 │
│           │                                           │
│  ┌────────▼────────┐  ┌──────────────────┐          │
│  │  CLI Reporter   │  │  Web Reporter    │          │
│  │  - Summary      │  │  - HTML output   │          │
│  │  - Details      │  │  - Interactive   │          │
│  │  - CSV export   │  │  - Charts        │          │
│  └─────────────────┘  └──────────────────┘          │
└─────────────────────────────────────────────────────┘
```

### Data Model

#### Row Identification
A row is uniquely identified by combining:
- `county`: County name
- `precinct`: Precinct identifier
- `office`: Office name
- `district`: District identifier
- `candidate`: Candidate name
- `party`: Party affiliation

This combination forms a **row key** used for matching rows between files.

#### Difference Types

```python
class DifferenceType(Enum):
    MISSING_ROW = "missing_row"           # Row in File A, not in File B
    EXTRA_ROW = "extra_row"               # Row in File B, not in File A
    VALUE_MISMATCH = "value_mismatch"     # Same row, different value
    MISSING_COLUMN = "missing_column"     # Column in File A, not in File B
    EXTRA_COLUMN = "extra_column"         # Column in File B, not in File A
    EMPTY_VALUE = "empty_value"           # Value is empty in one file
```

#### Comparison Result Structure

```python
{
    "metadata": {
        "file_a": str,
        "file_b": str,
        "compared_at": datetime,
        "row_count_a": int,
        "row_count_b": int,
        "column_count_a": int,
        "column_count_b": int,
    },
    "summary": {
        "total_differences": int,
        "missing_rows": int,
        "extra_rows": int,
        "value_mismatches": int,
        "missing_columns": int,
        "extra_columns": int,
        "identical_rows": int,
        "percentage_match": float,
    },
    "column_differences": {
        "missing_in_b": List[str],
        "extra_in_b": List[str],
        "common_columns": List[str],
    },
    "row_differences": {
        "missing_rows": List[Dict],     # Rows only in File A
        "extra_rows": List[Dict],       # Rows only in File B
    },
    "value_differences": [
        {
            "row_key": Dict,             # Key columns identifying the row
            "column": str,               # Column with difference
            "value_a": Any,              # Value in File A
            "value_b": Any,              # Value in File B
            "difference": Any,           # Calculated difference (for numbers)
        }
    ],
    "vote_totals": {
        "file_a": Dict[str, int],       # Total votes by vote type
        "file_b": Dict[str, int],       # Total votes by vote type
        "differences": Dict[str, int],   # Differences by vote type
    }
}
```

### Algorithm

#### Main Comparison Algorithm

```
1. Load and Validate Files
   a. Read both CSV files
   b. Validate required columns exist
   c. Store metadata (row counts, columns)

2. Identify Columns
   a. Standard columns: county, precinct, office, district, candidate, party
   b. Vote columns: all other columns
   c. Detect column differences

3. Build Row Indices
   a. For each file, create a dictionary:
      key = (county, precinct, office, district, candidate, party)
      value = full row data
   b. Handle duplicate keys (report as warning)

4. Compare Rows
   a. Find keys only in File A (missing rows)
   b. Find keys only in File B (extra rows)
   c. Find keys in both files (compare values)

5. Compare Values (for matching rows)
   a. For each common key:
      - Compare each column value
      - Record mismatches
      - Calculate numeric differences where applicable

6. Calculate Vote Totals
   a. Sum all vote columns in each file
   b. Compare totals
   c. Report discrepancies

7. Generate Results
   a. Compile all differences
   b. Calculate summary statistics
   c. Return structured result
```

#### Optimization Strategies
- **Streaming for large files**: Use iterative CSV reading for memory efficiency
- **Indexed lookups**: Use dictionaries for O(1) row lookups
- **Early exit**: Optionally stop after N differences found
- **Parallel processing**: Compare value differences in parallel for large datasets

### Command-Line Interface

#### Command Structure
```bash
python precinct_results.py compare-csv <file-a> <file-b> [options]
```

#### Options
```
Positional Arguments:
  file_a                  First CSV file path
  file_b                  Second CSV file path

Optional Arguments:
  -o, --output FORMAT     Output format: 'cli', 'web', 'both' (default: cli)
  -r, --report FILE       Save report to file (HTML for web, CSV for cli)
  -v, --verbose           Increase output verbosity
  -q, --quiet             Minimal output (summary only)
  --max-diffs N           Stop after N differences (default: unlimited)
  --tolerance FLOAT       Numeric tolerance for comparisons (default: 0)
  --ignore-columns LIST   Comma-separated columns to ignore
  --key-columns LIST      Comma-separated key columns (default: auto-detect)
  --no-color              Disable colored output
  --csv-export FILE       Export differences to CSV file
```

#### Example Commands
```bash
# Basic comparison with CLI output
python precinct_results.py compare-csv file1.csv file2.csv

# Generate web report
python precinct_results.py compare-csv file1.csv file2.csv -o web -r report.html

# Verbose comparison with CSV export
python precinct_results.py compare-csv file1.csv file2.csv -v --csv-export diffs.csv

# Quick summary only
python precinct_results.py compare-csv file1.csv file2.csv -q

# Ignore specific columns
python precinct_results.py compare-csv file1.csv file2.csv --ignore-columns votes,absentee
```

### Command-Line Output Format

#### Summary View (Default)
```
CSV Comparison Report
═══════════════════════════════════════════════════════════════

Files:
  File A: 20201103__tx__travis__precinct.csv
  File B: 20201103__tx__travis__precinct_corrected.csv

Structure:
  Rows:    1,234 vs 1,235 (+1)
  Columns: 12 vs 12 (identical)

Results:
  ✓ Identical rows:      1,180 (95.6%)
  ✗ Missing rows:        10   (0.8%)
  ✗ Extra rows:          11   (0.9%)
  ✗ Value mismatches:    34   (2.7%)

Vote Totals:
  early_voting:   File A: 125,432  File B: 125,450  (Δ +18)
  election_day:   File A: 234,567  File B: 234,567  (✓ Match)
  mail:           File A: 45,678   File B: 45,680   (Δ +2)

Overall Match: 95.6%

For detailed differences, use --verbose flag.
```

#### Verbose Output
```
CSV Comparison Report (Detailed)
═══════════════════════════════════════════════════════════════

[... Summary section as above ...]

Missing Rows (10):
─────────────────────────────────────────────────────────────
1. County: Travis | Precinct: 101 | Office: President
   Candidate: John Doe (DEM)
   Values: early_voting=150, election_day=200, mail=50

2. County: Travis | Precinct: 102 | Office: President
   Candidate: Jane Smith (REP)
   Values: early_voting=175, election_day=225, mail=60

[... more rows ...]

Extra Rows (11):
─────────────────────────────────────────────────────────────
1. County: Travis | Precinct: 101A | Office: President
   Candidate: John Doe (DEM)
   Values: early_voting=150, election_day=200, mail=50

[... more rows ...]

Value Mismatches (34):
─────────────────────────────────────────────────────────────
1. County: Travis | Precinct: 103 | Office: President
   Candidate: John Doe (DEM)
   Column: early_voting
     File A: 250
     File B: 252
     Diff:   +2

2. County: Travis | Precinct: 103 | Office: President
   Candidate: Jane Smith (REP)
   Column: mail
     File A: 100
     File B: 98
     Diff:   -2

[... more differences ...]
```

#### Color Coding (Terminal)
- **Green (✓)**: Matches, identical values
- **Red (✗)**: Differences, mismatches
- **Yellow (Δ)**: Numeric differences with values
- **Cyan**: Headers and section titles
- **White**: Regular text

### Web-Based Output Format

#### HTML Report Structure

```html
<!DOCTYPE html>
<html>
<head>
    <title>CSV Comparison Report</title>
    <style>
        /* Modern, clean styling */
        /* Responsive design */
        /* Print-friendly styles */
    </style>
    <script>
        /* Interactive filtering */
        /* Sortable tables */
        /* Chart rendering (using Chart.js or similar) */
    </script>
</head>
<body>
    <div class="container">
        <!-- Header with metadata -->
        <header>
            <h1>CSV Comparison Report</h1>
            <div class="metadata">...</div>
        </header>

        <!-- Summary Dashboard -->
        <section class="dashboard">
            <div class="summary-cards">
                <div class="card match">
                    <h3>95.6%</h3>
                    <p>Match Rate</p>
                </div>
                <div class="card differences">
                    <h3>55</h3>
                    <p>Total Differences</p>
                </div>
                <!-- More cards -->
            </div>

            <!-- Visual Charts -->
            <div class="charts">
                <canvas id="differenceChart"></canvas>
                <canvas id="voteTotalChart"></canvas>
            </div>
        </section>

        <!-- Detailed Differences Sections -->
        <section class="differences">
            <!-- Tabs for different difference types -->
            <div class="tabs">
                <button class="tab active">Overview</button>
                <button class="tab">Missing Rows</button>
                <button class="tab">Extra Rows</button>
                <button class="tab">Value Mismatches</button>
                <button class="tab">Column Differences</button>
            </div>

            <!-- Tab content -->
            <div class="tab-content">
                <!-- Sortable, filterable tables -->
                <table class="difference-table">
                    <thead>...</thead>
                    <tbody>...</tbody>
                </table>
            </div>
        </section>

        <!-- Export Options -->
        <section class="export">
            <button onclick="exportCSV()">Export to CSV</button>
            <button onclick="exportJSON()">Export to JSON</button>
            <button onclick="window.print()">Print Report</button>
        </section>
    </div>
</body>
</html>
```

#### Interactive Features
1. **Sortable Tables**: Click column headers to sort
2. **Filtering**: Filter by county, precinct, office, difference type
3. **Search**: Full-text search across all differences
4. **Expandable Rows**: Click to see full row details
5. **Side-by-Side View**: Toggle between difference view and side-by-side comparison
6. **Export**: Download differences as CSV or JSON
7. **Charts**:
   - Pie chart: Distribution of difference types
   - Bar chart: Vote total comparisons
   - Line chart: Differences by precinct (if many precincts)

#### Responsive Design
- Desktop: Multi-column layout with charts
- Tablet: Stacked layout, collapsible sections
- Mobile: Single column, simplified tables

### Implementation Details

#### Module Structure
```
precinct_results.py (existing)
├── [existing functions...]
└── [new functions:]
    ├── compare_csv_files()
    ├── _load_and_validate_csv()
    ├── _build_row_index()
    ├── _generate_row_key()
    ├── _compare_structures()
    ├── _compare_rows()
    ├── _compare_values()
    ├── _calculate_vote_totals()
    ├── _format_cli_output()
    ├── _format_web_output()
    └── _export_differences_csv()
```

#### Key Function Signatures

```python
def compare_csv_files(
    file_a: str,
    file_b: str,
    key_columns: Optional[List[str]] = None,
    ignore_columns: Optional[List[str]] = None,
    tolerance: float = 0.0,
    max_differences: Optional[int] = None,
    output_format: str = 'cli',
    output_file: Optional[str] = None,
    csv_export: Optional[str] = None,
    verbose: bool = True,
    color: bool = True
) -> Dict[str, Any]:
    """
    Compare two CSV files and report differences.

    Args:
        file_a: Path to first CSV file
        file_b: Path to second CSV file
        key_columns: Columns to use as row identifier (default: auto-detect)
        ignore_columns: Columns to exclude from comparison
        tolerance: Numeric comparison tolerance
        max_differences: Stop after N differences
        output_format: 'cli', 'web', or 'both'
        output_file: Output file path (for web HTML or summary CSV)
        csv_export: Export detailed differences to CSV
        verbose: Print detailed output
        color: Use colored terminal output

    Returns:
        Dictionary with comparison results
    """
    pass
```

#### Dependencies
**Standard Library Only** (preferred):
- `csv`: CSV file operations
- `argparse`: Command-line interface
- `json`: JSON export
- `collections`: Data structures
- `typing`: Type hints
- `datetime`: Timestamps

**Optional External Dependencies**:
- `colorama`: Cross-platform colored terminal output (optional, graceful fallback)
- None required for core functionality

#### Error Handling
```python
class CSVComparisonError(Exception):
    """Base exception for CSV comparison errors"""
    pass

class FileValidationError(CSVComparisonError):
    """File cannot be read or validated"""
    pass

class StructureMismatchError(CSVComparisonError):
    """CSV structures are incompatible"""
    pass
```

## Implementation Plan

### Phase 1: Core Comparison Engine (High Priority)
**Estimated Effort**: 4-6 hours

1. Implement core comparison functions:
   - `_load_and_validate_csv()`: Load and validate CSV files
   - `_build_row_index()`: Build row lookup indices
   - `_generate_row_key()`: Generate unique row identifiers
   - `_compare_structures()`: Compare columns and structure
   - `_compare_rows()`: Find missing/extra rows
   - `_compare_values()`: Find value mismatches
   - `_calculate_vote_totals()`: Calculate and compare vote totals

2. Implement main function:
   - `compare_csv_files()`: Orchestrate the comparison

3. Testing:
   - Create test CSV files with known differences
   - Unit tests for each component
   - Integration tests for full comparison

### Phase 2: CLI Output (High Priority)
**Estimated Effort**: 2-3 hours

1. Implement CLI formatting:
   - `_format_cli_output()`: Format results for terminal
   - Color coding (with fallback for non-color terminals)
   - Summary and detailed views
   - Progress indicators for large files

2. Implement CSV export:
   - `_export_differences_csv()`: Export differences to CSV

3. Testing:
   - Test output formatting
   - Test color handling
   - Test CSV export

### Phase 3: Command-Line Interface (Medium Priority)
**Estimated Effort**: 1-2 hours

1. Add argument parsing:
   - Use argparse for CLI arguments
   - Validate arguments
   - Handle errors gracefully

2. Create wrapper script or add to existing module:
   - Either standalone script or add to precinct_results.py
   - Entry point for command-line usage

3. Documentation:
   - Update README with usage examples
   - Add help text

### Phase 4: Web Output (Medium Priority)
**Estimated Effort**: 4-6 hours

1. Implement HTML generation:
   - `_format_web_output()`: Generate HTML report
   - Template with CSS styling
   - Responsive design

2. Add interactive features:
   - JavaScript for sorting, filtering, search
   - Chart generation (consider Chart.js or inline SVG)
   - Export functionality

3. Testing:
   - Test HTML generation
   - Test in multiple browsers
   - Test responsive behavior
   - Test with large datasets

### Phase 5: Polish and Documentation (Low Priority)
**Estimated Effort**: 2-3 hours

1. Performance optimization:
   - Profile with large files
   - Optimize bottlenecks
   - Add streaming for very large files if needed

2. Documentation:
   - Add comprehensive docstrings
   - Create usage examples
   - Add to README
   - Create example_usage.py examples

3. Testing:
   - Edge cases
   - Performance tests
   - User acceptance testing

## Testing Strategy

### Unit Tests
```python
# Test individual components
test_load_csv()
test_build_row_index()
test_generate_row_key()
test_compare_structures()
test_compare_rows()
test_compare_values()
test_calculate_vote_totals()
```

### Integration Tests
```python
# Test full comparison workflows
test_compare_identical_files()
test_compare_with_missing_rows()
test_compare_with_value_differences()
test_compare_with_column_differences()
test_compare_large_files()
```

### Test Data
Create synthetic test files:
1. `test_identical_a.csv` and `test_identical_b.csv`: Identical files
2. `test_missing_rows_a.csv` and `test_missing_rows_b.csv`: 10 missing rows
3. `test_value_diff_a.csv` and `test_value_diff_b.csv`: 20 value mismatches
4. `test_column_diff_a.csv` and `test_column_diff_b.csv`: Different columns
5. `test_large_a.csv` and `test_large_b.csv`: 100K+ rows for performance testing

## Usage Examples

### Example 1: Basic Comparison
```python
from precinct_results import compare_csv_files

results = compare_csv_files(
    'original.csv',
    'corrected.csv',
    verbose=True
)

# Check if files match
if results['summary']['percentage_match'] == 100.0:
    print("Files are identical!")
else:
    print(f"Files differ: {results['summary']['total_differences']} differences found")
```

### Example 2: Web Report Generation
```python
from precinct_results import compare_csv_files

compare_csv_files(
    'original.csv',
    'corrected.csv',
    output_format='web',
    output_file='comparison_report.html',
    verbose=True
)
print("Web report generated: comparison_report.html")
```

### Example 3: Programmatic Analysis
```python
from precinct_results import compare_csv_files

results = compare_csv_files(
    'file_a.csv',
    'file_b.csv',
    verbose=False
)

# Analyze value mismatches
for diff in results['value_differences']:
    if diff['column'] == 'votes':
        print(f"Vote mismatch in {diff['row_key']}: {diff['value_a']} vs {diff['value_b']}")

# Check vote totals
vote_totals = results['vote_totals']
for vote_type, diff in vote_totals['differences'].items():
    if diff != 0:
        print(f"{vote_type}: {diff:+d} vote difference")
```

### Example 4: Command Line
```bash
# Simple comparison
python precinct_results.py compare-csv original.csv corrected.csv

# Generate web report
python precinct_results.py compare-csv original.csv corrected.csv \
    -o web -r report.html

# Export differences to CSV
python precinct_results.py compare-csv original.csv corrected.csv \
    --csv-export differences.csv

# Ignore certain columns
python precinct_results.py compare-csv original.csv corrected.csv \
    --ignore-columns provisional,absentee
```

## Future Enhancements

### Potential Phase 6+ Features
1. **Three-way comparison**: Compare three files simultaneously
2. **Directory comparison**: Compare all matching files in two directories
3. **Diff-style output**: Generate unified diff format
4. **Automatic correction suggestions**: AI-powered suggestions for resolving differences
5. **Integration with git**: Track CSV changes over time
6. **API endpoint**: Expose comparison as REST API
7. **Batch processing**: Compare multiple file pairs in batch
8. **Custom comparison rules**: User-defined comparison logic
9. **Statistical analysis**: Distribution of differences, outlier detection
10. **Audit trail**: Track who made what changes when

## Conclusion

This plan provides a comprehensive design for a CSV comparison utility that:
- Follows existing codebase patterns
- Provides both CLI and web output
- Handles large files efficiently
- Is extensible for future enhancements
- Includes thorough testing strategy

The phased approach allows for incremental development and testing, with core functionality (Phases 1-2) delivering immediate value while advanced features (Phases 3-4) enhance usability.
