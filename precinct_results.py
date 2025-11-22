"""
OpenElections Statewide Precinct Results Generator

This module provides functionality to consolidate county-level precinct CSV files
into a single statewide precinct results file. It automatically introspects vote
type columns and handles varying data structures across counties.

Based on: https://github.com/openelections/openelections-data-tx/blob/master/statewide_generator.py
"""

import os
import glob
import csv
from typing import List, Dict, Set, Optional


# Standard columns that are not vote type columns
STANDARD_COLUMNS = {'county', 'precinct', 'office', 'district', 'party', 'candidate'}


def discover_vote_columns(csv_path: str) -> Set[str]:
    """
    Discover vote type columns in a CSV file by excluding standard columns.

    Args:
        csv_path: Path to the CSV file to introspect

    Returns:
        Set of vote type column names found in the file
    """
    with open(csv_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        try:
            row = next(reader)
            headers = set(row.keys())
            # Vote columns are everything except standard columns
            vote_columns = headers - STANDARD_COLUMNS
            return vote_columns
        except StopIteration:
            return set()


def collect_all_vote_columns(directory: str, file_pattern: str) -> List[str]:
    """
    Scan all matching CSV files and collect all unique vote type columns.

    Args:
        directory: Directory containing the CSV files
        file_pattern: Glob pattern to match CSV files (e.g., '20201103*precinct.csv')

    Returns:
        Sorted list of all unique vote type column names found across all files
    """
    all_vote_columns = set()

    original_dir = os.getcwd()
    try:
        os.chdir(directory)
        for fname in glob.glob(file_pattern):
            vote_columns = discover_vote_columns(fname)
            all_vote_columns.update(vote_columns)
    finally:
        os.chdir(original_dir)

    # Sort for consistent ordering
    return sorted(all_vote_columns)


def generate_statewide_precinct_file(
    state_abbr: str,
    election_date: str,
    source_directory: str,
    output_file: str,
    file_pattern: Optional[str] = None,
    offices_filter: Optional[List[str]] = None,
    verbose: bool = True
) -> None:
    """
    Generate a consolidated statewide precinct results file from county CSV files.

    This function:
    1. Scans all matching CSV files in the source directory
    2. Automatically discovers all vote type columns across all files
    3. Consolidates data with consistent column ordering
    4. Handles missing vote columns by filling with None

    Args:
        state_abbr: Two-letter state abbreviation (e.g., 'tx', 'ca')
        election_date: Election date in YYYYMMDD format (e.g., '20201103')
        source_directory: Directory containing county precinct CSV files
        output_file: Path for the output consolidated CSV file
        file_pattern: Optional glob pattern for matching files.
                     Defaults to '{election_date}*precinct.csv'
        offices_filter: Optional list of office names to include.
                       If None, includes all offices.
        verbose: If True, print progress messages

    Example:
        >>> generate_statewide_precinct_file(
        ...     state_abbr='tx',
        ...     election_date='20201103',
        ...     source_directory='2020/counties',
        ...     output_file='20201103__tx__general__precinct.csv'
        ... )
    """
    if file_pattern is None:
        file_pattern = f'{election_date}*precinct.csv'

    if verbose:
        print(f"Scanning files matching pattern: {file_pattern}")
        print(f"Source directory: {source_directory}")

    # First pass: discover all vote type columns across all files
    vote_columns = collect_all_vote_columns(source_directory, file_pattern)

    if verbose:
        print(f"Discovered vote type columns: {vote_columns}")

    # Define output column order: standard columns + vote columns
    standard_cols = ['county', 'precinct', 'office', 'district', 'candidate', 'party']
    output_columns = standard_cols + vote_columns

    # Second pass: read and consolidate data
    results = []
    original_dir = os.getcwd()

    try:
        os.chdir(source_directory)

        for fname in glob.glob(file_pattern):
            if verbose:
                print(f"Processing: {fname}")

            with open(fname, 'r') as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    # Apply office filter if specified
                    if offices_filter is not None:
                        if row.get('office', '').strip() not in offices_filter:
                            continue

                    # Build result row with consistent column ordering
                    result_row = []

                    # Add standard columns
                    for col in standard_cols:
                        result_row.append(row.get(col, ''))

                    # Add vote columns (with None if not present in this file)
                    for col in vote_columns:
                        result_row.append(row.get(col, None))

                    results.append(result_row)

    finally:
        os.chdir(original_dir)

    # Write consolidated output
    if verbose:
        print(f"Writing {len(results)} rows to {output_file}")

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(output_columns)
        writer.writerows(results)

    if verbose:
        print(f"Successfully created: {output_file}")


def generate_vote_columns_report(
    source_directory: str,
    file_pattern: str,
    output_file: str,
    verbose: bool = True
) -> None:
    """
    Generate a report showing which vote type columns are present in each county file.

    Args:
        source_directory: Directory containing county precinct CSV files
        file_pattern: Glob pattern for matching files
        output_file: Path for the output report CSV file
        verbose: If True, print progress messages

    Example:
        >>> generate_vote_columns_report(
        ...     source_directory='2020/counties',
        ...     file_pattern='20201103*precinct.csv',
        ...     output_file='vote_columns_report.csv'
        ... )
    """
    # Discover all possible vote columns
    all_vote_columns = collect_all_vote_columns(source_directory, file_pattern)

    if verbose:
        print(f"Discovered vote type columns: {all_vote_columns}")

    # Scan each file and record which columns it has
    report_rows = []
    original_dir = os.getcwd()

    try:
        os.chdir(source_directory)

        for fname in glob.glob(file_pattern):
            if verbose:
                print(f"Analyzing: {fname}")

            with open(fname, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                try:
                    row = next(reader)
                    county = row.get('county', fname)

                    # Create report row: county name + boolean for each vote column
                    report_row = {'county': county}
                    for col in all_vote_columns:
                        report_row[col] = col in row

                    report_rows.append(report_row)
                except StopIteration:
                    if verbose:
                        print(f"  Warning: {fname} is empty")

    finally:
        os.chdir(original_dir)

    # Write report
    report_columns = ['county'] + all_vote_columns

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=report_columns)
        writer.writeheader()
        writer.writerows(sorted(report_rows, key=lambda x: x['county']))

    if verbose:
        print(f"Report written to: {output_file}")


if __name__ == '__main__':
    # Example usage
    print("OpenElections Statewide Precinct Results Generator")
    print("=" * 60)
    print("\nThis module provides functions to consolidate county-level")
    print("precinct CSV files into statewide results.")
    print("\nMain function: generate_statewide_precinct_file()")
    print("\nExample:")
    print("  from precinct_results import generate_statewide_precinct_file")
    print()
    print("  generate_statewide_precinct_file(")
    print("      state_abbr='tx',")
    print("      election_date='20201103',")
    print("      source_directory='2020/counties',")
    print("      output_file='20201103__tx__general__precinct.csv'")
    print("  )")
