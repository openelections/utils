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
from typing import List, Dict, Set, Optional, Tuple, Any
from difflib import SequenceMatcher
from datetime import datetime
from enum import Enum


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


def collect_precinct_names(
    source_directory: str,
    file_pattern: str,
    county_filter: Optional[str] = None,
    normalize_case: bool = False,
    verbose: bool = False
) -> Dict[str, Set[str]]:
    """
    Collect all unique precinct names from CSV files, organized by county.

    Args:
        source_directory: Directory containing county precinct CSV files
        file_pattern: Glob pattern for matching files (e.g., '20201103*precinct.csv')
        county_filter: Optional county name to filter by. If None, includes all counties.
        normalize_case: If True, convert all precinct names to lowercase for comparison
        verbose: If True, print progress messages

    Returns:
        Dictionary mapping county names to sets of precinct names

    Example:
        >>> precincts = collect_precinct_names(
        ...     source_directory='2020/counties',
        ...     file_pattern='20201103*precinct.csv',
        ...     county_filter='Travis'
        ... )
        >>> print(precincts['Travis'])
        {'101', '102', '103', ...}
    """
    precinct_data = {}
    original_dir = os.getcwd()

    try:
        os.chdir(source_directory)

        for fname in glob.glob(file_pattern):
            if verbose:
                print(f"Scanning: {fname}")

            with open(fname, 'r') as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    county = row.get('county', '').strip()
                    precinct = row.get('precinct', '').strip()

                    if not county or not precinct:
                        continue

                    # Apply county filter if specified
                    if county_filter and county.lower() != county_filter.lower():
                        continue

                    if county not in precinct_data:
                        precinct_data[county] = set()

                    # Normalize case if requested
                    if normalize_case:
                        precinct = precinct.lower()

                    precinct_data[county].add(precinct)

    finally:
        os.chdir(original_dir)

    return precinct_data


def _calculate_similarity(str1: str, str2: str) -> float:
    """Calculate similarity ratio between two strings (0.0 to 1.0)."""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def _find_similar_precincts(
    precinct: str,
    candidates: Set[str],
    threshold: float = 0.6
) -> List[Tuple[str, float]]:
    """
    Find precincts in candidates that are similar to the given precinct.

    Args:
        precinct: The precinct name to match
        candidates: Set of candidate precinct names
        threshold: Minimum similarity ratio (0.0 to 1.0)

    Returns:
        List of (precinct_name, similarity_score) tuples, sorted by score descending
    """
    matches = []
    for candidate in candidates:
        similarity = _calculate_similarity(precinct, candidate)
        if similarity >= threshold:
            matches.append((candidate, similarity))

    return sorted(matches, key=lambda x: x[1], reverse=True)


def compare_precinct_names(
    election1_dir: str,
    election1_pattern: str,
    election2_dir: str,
    election2_pattern: str,
    county_filter: Optional[str] = None,
    normalize_case: bool = True,
    similarity_threshold: float = 0.6,
    output_file: Optional[str] = None,
    verbose: bool = True
) -> Dict[str, Dict]:
    """
    Compare precinct names between two elections for a given county or statewide.

    This function identifies:
    - Precincts that exist only in election 1 (removed/renamed)
    - Precincts that exist only in election 2 (new/renamed)
    - Precincts that exist in both elections (unchanged)
    - Potential renames based on name similarity
    - Case-only differences (when normalize_case=True)

    Args:
        election1_dir: Directory containing first election's CSV files
        election1_pattern: Glob pattern for first election files
        election2_dir: Directory containing second election's CSV files
        election2_pattern: Glob pattern for second election files
        county_filter: Optional county name. If None, compares all counties.
        normalize_case: If True, ignore case differences. Will report any
                       case-only mismatches found. Default: True.
        similarity_threshold: Minimum similarity (0.0-1.0) for rename detection
        output_file: Optional CSV file path to write detailed comparison report
        verbose: If True, print summary statistics

    Returns:
        Dictionary mapping county names to comparison results:
        {
            'county_name': {
                'only_in_election1': set of precinct names,
                'only_in_election2': set of precinct names,
                'in_both': set of precinct names,
                'potential_renames': list of (old_name, new_name, similarity) tuples,
                'case_mismatches': list of (election1_name, election2_name) tuples,
                'stats': {
                    'election1_count': int,
                    'election2_count': int,
                    'unchanged_count': int,
                    'removed_count': int,
                    'added_count': int,
                    'change_percentage': float,
                    'case_mismatch_count': int
                }
            }
        }

    Example:
        >>> results = compare_precinct_names(
        ...     election1_dir='2020/counties',
        ...     election1_pattern='20201103*precinct.csv',
        ...     election2_dir='2022/counties',
        ...     election2_pattern='20221108*precinct.csv',
        ...     county_filter='Travis'
        ... )
    """
    # First, collect without normalization to detect case mismatches
    if verbose:
        print(f"Collecting precinct names from election 1...")
    election1_precincts_raw = collect_precinct_names(
        election1_dir, election1_pattern, county_filter, normalize_case=False, verbose=False
    )

    if verbose:
        print(f"Collecting precinct names from election 2...")
    election2_precincts_raw = collect_precinct_names(
        election2_dir, election2_pattern, county_filter, normalize_case=False, verbose=False
    )

    # If normalize_case is True, also collect normalized versions
    if normalize_case:
        election1_precincts_normalized = collect_precinct_names(
            election1_dir, election1_pattern, county_filter, normalize_case=True, verbose=False
        )
        election2_precincts_normalized = collect_precinct_names(
            election2_dir, election2_pattern, county_filter, normalize_case=True, verbose=False
        )
        # Use normalized for comparison
        election1_precincts = election1_precincts_normalized
        election2_precincts = election2_precincts_normalized
    else:
        # Use raw for comparison
        election1_precincts = election1_precincts_raw
        election2_precincts = election2_precincts_raw

    # Get all counties to compare
    all_counties = set(election1_precincts.keys()) | set(election2_precincts.keys())

    comparison_results = {}
    csv_rows = []

    for county in sorted(all_counties):
        precincts1 = election1_precincts.get(county, set())
        precincts2 = election2_precincts.get(county, set())

        only_in_1 = precincts1 - precincts2
        only_in_2 = precincts2 - precincts1
        in_both = precincts1 & precincts2

        # Detect case-only mismatches if normalization is enabled
        case_mismatches = []
        if normalize_case:
            # Check for precincts that match when normalized but differ in case
            precincts1_raw = election1_precincts_raw.get(county, set())
            precincts2_raw = election2_precincts_raw.get(county, set())

            # Build mapping from lowercase to original case
            p1_lower_to_orig = {p.lower(): p for p in precincts1_raw}
            p2_lower_to_orig = {p.lower(): p for p in precincts2_raw}

            # Find precincts that are in both when normalized
            for precinct_lower in in_both:
                orig1 = p1_lower_to_orig.get(precinct_lower, precinct_lower)
                orig2 = p2_lower_to_orig.get(precinct_lower, precinct_lower)

                # If the original forms differ, it's a case mismatch
                if orig1 != orig2:
                    case_mismatches.append((orig1, orig2))

        # Find potential renames
        potential_renames = []
        for old_precinct in only_in_1:
            similar = _find_similar_precincts(
                old_precinct, only_in_2, similarity_threshold
            )
            for new_precinct, similarity in similar:
                potential_renames.append((old_precinct, new_precinct, similarity))

        # Calculate statistics
        total1 = len(precincts1)
        total2 = len(precincts2)
        unchanged = len(in_both)
        removed = len(only_in_1)
        added = len(only_in_2)
        case_mismatch_count = len(case_mismatches)

        # Calculate change percentage
        if total1 > 0:
            change_pct = ((removed + added) / total1) * 100
        else:
            change_pct = 100.0 if total2 > 0 else 0.0

        comparison_results[county] = {
            'only_in_election1': only_in_1,
            'only_in_election2': only_in_2,
            'in_both': in_both,
            'potential_renames': potential_renames,
            'case_mismatches': case_mismatches,
            'stats': {
                'election1_count': total1,
                'election2_count': total2,
                'unchanged_count': unchanged,
                'removed_count': removed,
                'added_count': added,
                'change_percentage': change_pct,
                'case_mismatch_count': case_mismatch_count
            }
        }

        if verbose:
            print(f"\n{county} County:")
            print(f"  Election 1 precincts: {total1}")
            print(f"  Election 2 precincts: {total2}")
            print(f"  Unchanged: {unchanged}")
            print(f"  Removed/renamed: {removed}")
            print(f"  Added/new: {added}")
            print(f"  Change: {change_pct:.1f}%")

            if case_mismatches:
                print(f"  Case mismatches detected: {case_mismatch_count}")
                for orig1, orig2 in case_mismatches[:5]:  # Show top 5
                    print(f"    '{orig1}' vs '{orig2}'")
                if len(case_mismatches) > 5:
                    print(f"    ... and {len(case_mismatches) - 5} more")

            if potential_renames:
                print(f"  Potential renames detected: {len(potential_renames)}")
                for old, new, sim in potential_renames[:5]:  # Show top 5
                    print(f"    '{old}' → '{new}' (similarity: {sim:.2f})")
                if len(potential_renames) > 5:
                    print(f"    ... and {len(potential_renames) - 5} more")

        # Prepare CSV rows if output file is requested
        if output_file:
            for precinct in in_both:
                csv_rows.append({
                    'county': county,
                    'precinct': precinct,
                    'status': 'unchanged',
                    'similarity': 1.0,
                    'notes': ''
                })
            for precinct in only_in_1:
                csv_rows.append({
                    'county': county,
                    'precinct': precinct,
                    'status': 'removed',
                    'similarity': None,
                    'notes': ''
                })
            for precinct in only_in_2:
                csv_rows.append({
                    'county': county,
                    'precinct': precinct,
                    'status': 'added',
                    'similarity': None,
                    'notes': ''
                })
            for orig1, orig2 in case_mismatches:
                csv_rows.append({
                    'county': county,
                    'precinct': f"{orig1} | {orig2}",
                    'status': 'case_mismatch',
                    'similarity': 1.0,
                    'notes': 'Same precinct, different casing'
                })
            for old, new, sim in potential_renames:
                csv_rows.append({
                    'county': county,
                    'precinct': f"{old} → {new}",
                    'status': 'potential_rename',
                    'similarity': sim,
                    'notes': ''
                })

    # Write CSV report if requested
    if output_file:
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['county', 'precinct', 'status', 'similarity', 'notes']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)

        if verbose:
            print(f"\nDetailed comparison written to: {output_file}")

    return comparison_results


def check_party_variations(
    csv_path: str,
    similarity_threshold: float = 0.7,
    output_file: Optional[str] = None,
    verbose: bool = True
) -> Dict[str, any]:
    """
    Check for variations in party values within a CSV file.

    This function identifies all unique party values and detects potential
    variations (e.g., "Democratic", "Democrat", "DEM", "Dem" that likely
    refer to the same party).

    Args:
        csv_path: Path to the CSV file to analyze
        similarity_threshold: Minimum similarity (0.0-1.0) for variation detection.
                            Default: 0.7
        output_file: Optional CSV file path to write detailed variation report
        verbose: If True, print summary and variations found

    Returns:
        Dictionary with analysis results:
        {
            'unique_parties': set of all unique party values found,
            'total_count': total number of party occurrences,
            'party_counts': dict mapping party value to occurrence count,
            'potential_variations': list of (party1, party2, similarity) tuples,
            'empty_count': number of rows with empty/missing party values
        }

    Example:
        >>> results = check_party_variations('20201103__tx__general__precinct.csv')
        >>> print(results['unique_parties'])
        {'DEM', 'Democratic', 'REP', 'Republican', 'LIB', 'Libertarian', ...}
        >>> print(results['potential_variations'])
        [('DEM', 'Democratic', 0.85), ('REP', 'Republican', 0.82), ...]
    """
    party_values = []
    empty_count = 0

    if verbose:
        print(f"Analyzing party values in: {csv_path}")

    # Collect all party values
    with open(csv_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            party = row.get('party', '').strip()

            if not party:
                empty_count += 1
            else:
                party_values.append(party)

    # Get unique parties and counts
    unique_parties = set(party_values)
    party_counts = {}
    for party in party_values:
        party_counts[party] = party_counts.get(party, 0) + 1

    # Detect potential variations
    potential_variations = []
    parties_list = sorted(unique_parties)

    for i, party1 in enumerate(parties_list):
        for party2 in parties_list[i + 1:]:
            similarity = _calculate_similarity(party1, party2)
            if similarity >= similarity_threshold:
                potential_variations.append((party1, party2, similarity))

    # Sort variations by similarity (highest first)
    potential_variations.sort(key=lambda x: x[2], reverse=True)

    results = {
        'unique_parties': unique_parties,
        'total_count': len(party_values),
        'party_counts': party_counts,
        'potential_variations': potential_variations,
        'empty_count': empty_count
    }

    if verbose:
        print(f"\nParty Value Analysis:")
        print(f"  Total rows with party values: {len(party_values)}")
        print(f"  Empty/missing party values: {empty_count}")
        print(f"  Unique party values found: {len(unique_parties)}")
        print(f"\nParty value frequency:")

        # Show parties sorted by count
        sorted_parties = sorted(party_counts.items(), key=lambda x: x[1], reverse=True)
        for party, count in sorted_parties:
            print(f"    {party}: {count}")

        if potential_variations:
            print(f"\nPotential variations detected: {len(potential_variations)}")
            for party1, party2, sim in potential_variations:
                count1 = party_counts.get(party1, 0)
                count2 = party_counts.get(party2, 0)
                print(f"    '{party1}' (n={count1}) ↔ '{party2}' (n={count2}) - similarity: {sim:.2f}")
        else:
            print("\nNo potential variations detected.")

    # Write detailed report if requested
    if output_file:
        csv_rows = []

        # Add party frequency rows
        for party, count in sorted(party_counts.items(), key=lambda x: x[1], reverse=True):
            csv_rows.append({
                'party': party,
                'count': count,
                'status': 'unique_value',
                'similar_to': '',
                'similarity': ''
            })

        # Add variation rows
        for party1, party2, sim in potential_variations:
            csv_rows.append({
                'party': f"{party1} ↔ {party2}",
                'count': f"{party_counts.get(party1, 0)} / {party_counts.get(party2, 0)}",
                'status': 'potential_variation',
                'similar_to': '',
                'similarity': f"{sim:.3f}"
            })

        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['party', 'count', 'status', 'similar_to', 'similarity']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)

        if verbose:
            print(f"\nDetailed report written to: {output_file}")

    return results


def check_party_variations_directory(
    source_directory: str,
    file_pattern: str,
    similarity_threshold: float = 0.7,
    output_file: Optional[str] = None,
    verbose: bool = True
) -> Dict[str, Set[str]]:
    """
    Check for party value variations across multiple CSV files in a directory.

    This function scans all matching CSV files, collects all unique party values
    across files, and detects potential variations that may indicate inconsistent
    party naming conventions.

    Args:
        source_directory: Directory containing CSV files
        file_pattern: Glob pattern for matching files (e.g., '20201103*precinct.csv')
        similarity_threshold: Minimum similarity (0.0-1.0) for variation detection
        output_file: Optional CSV file path to write detailed variation report
        verbose: If True, print summary and variations found

    Returns:
        Dictionary with analysis results:
        {
            'all_parties': set of all unique party values across all files,
            'by_file': dict mapping filename to set of party values in that file,
            'potential_variations': list of (party1, party2, similarity) tuples,
            'file_count': number of files processed
        }

    Example:
        >>> results = check_party_variations_directory(
        ...     source_directory='2020/counties',
        ...     file_pattern='20201103*precinct.csv'
        ... )
    """
    all_parties = set()
    by_file = {}
    original_dir = os.getcwd()

    if verbose:
        print(f"Scanning files matching pattern: {file_pattern}")
        print(f"Source directory: {source_directory}")

    try:
        os.chdir(source_directory)

        for fname in glob.glob(file_pattern):
            if verbose:
                print(f"  Processing: {fname}")

            file_parties = set()

            with open(fname, 'r') as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    party = row.get('party', '').strip()
                    if party:
                        file_parties.add(party)
                        all_parties.add(party)

            by_file[fname] = file_parties

    finally:
        os.chdir(original_dir)

    # Detect potential variations
    potential_variations = []
    parties_list = sorted(all_parties)

    for i, party1 in enumerate(parties_list):
        for party2 in parties_list[i + 1:]:
            similarity = _calculate_similarity(party1, party2)
            if similarity >= similarity_threshold:
                potential_variations.append((party1, party2, similarity))

    # Sort variations by similarity (highest first)
    potential_variations.sort(key=lambda x: x[2], reverse=True)

    results = {
        'all_parties': all_parties,
        'by_file': by_file,
        'potential_variations': potential_variations,
        'file_count': len(by_file)
    }

    if verbose:
        print(f"\nDirectory-wide Party Analysis:")
        print(f"  Files processed: {len(by_file)}")
        print(f"  Unique party values across all files: {len(all_parties)}")
        print(f"\nAll party values found:")
        for party in sorted(all_parties):
            file_count = sum(1 for parties in by_file.values() if party in parties)
            print(f"    {party} (in {file_count} file(s))")

        if potential_variations:
            print(f"\nPotential variations detected: {len(potential_variations)}")
            for party1, party2, sim in potential_variations:
                print(f"    '{party1}' ↔ '{party2}' - similarity: {sim:.2f}")
        else:
            print("\nNo potential variations detected.")

    # Write detailed report if requested
    if output_file:
        csv_rows = []

        # Add party rows showing which files contain each party value
        for party in sorted(all_parties):
            files_with_party = [f for f, parties in by_file.items() if party in parties]
            csv_rows.append({
                'party': party,
                'file_count': len(files_with_party),
                'status': 'unique_value',
                'similarity': '',
                'files': '; '.join(files_with_party)
            })

        # Add variation rows
        for party1, party2, sim in potential_variations:
            csv_rows.append({
                'party': f"{party1} ↔ {party2}",
                'file_count': '',
                'status': 'potential_variation',
                'similarity': f"{sim:.3f}",
                'files': ''
            })

        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['party', 'file_count', 'status', 'similarity', 'files']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)

        if verbose:
            print(f"\nDetailed report written to: {output_file}")

    return results


class DifferenceType(Enum):
    """Types of differences that can be detected between CSV files."""
    MISSING_ROW = "missing_row"
    EXTRA_ROW = "extra_row"
    VALUE_MISMATCH = "value_mismatch"
    MISSING_COLUMN = "missing_column"
    EXTRA_COLUMN = "extra_column"


def _generate_row_key(
    row: Dict[str, Any],
    key_columns: List[str]
) -> Tuple[str, ...]:
    """
    Generate a unique key for a row based on key columns.

    Args:
        row: Row data as dictionary
        key_columns: List of column names to use as key

    Returns:
        Tuple of values forming the unique key
    """
    return tuple(str(row.get(col, '')).strip().lower() for col in key_columns)


def _load_and_validate_csv(
    file_path: str,
    key_columns: Optional[List[str]] = None
) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    """
    Load and validate a CSV file.

    Args:
        file_path: Path to CSV file
        key_columns: Expected key columns (optional validation)

    Returns:
        Tuple of (rows, all_columns, standard_columns)

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is invalid or missing required columns
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    rows = []
    all_columns = []

    try:
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            if reader.fieldnames is None:
                raise ValueError(f"CSV file has no headers: {file_path}")

            all_columns = list(reader.fieldnames)

            # Validate key columns if specified
            if key_columns:
                missing_cols = set(key_columns) - set(all_columns)
                if missing_cols:
                    raise ValueError(
                        f"Missing required columns in {file_path}: {missing_cols}"
                    )

            for row in reader:
                rows.append(row)

    except csv.Error as e:
        raise ValueError(f"Error reading CSV file {file_path}: {e}")

    # Identify standard columns (key columns for election data)
    standard_cols = [col for col in all_columns if col in STANDARD_COLUMNS]

    return rows, all_columns, standard_cols


def _build_row_index(
    rows: List[Dict[str, Any]],
    key_columns: List[str],
    file_name: str = "file"
) -> Dict[Tuple[str, ...], Dict[str, Any]]:
    """
    Build an index of rows by their unique keys.

    Args:
        rows: List of row dictionaries
        key_columns: Columns to use for generating keys
        file_name: Name of file (for warning messages)

    Returns:
        Dictionary mapping row keys to row data

    Note:
        If duplicate keys are found, the last occurrence is kept and a warning
        is printed.
    """
    index = {}
    duplicates = []

    for i, row in enumerate(rows):
        key = _generate_row_key(row, key_columns)

        if key in index:
            duplicates.append((key, i))

        index[key] = row

    if duplicates:
        print(f"Warning: {file_name} has {len(duplicates)} duplicate row(s)")
        if len(duplicates) <= 5:
            for key, row_num in duplicates:
                print(f"  Duplicate at row {row_num}: {key}")

    return index


def _compare_structures(
    columns_a: List[str],
    columns_b: List[str]
) -> Dict[str, Any]:
    """
    Compare the structure (columns) of two CSV files.

    Args:
        columns_a: Columns from first file
        columns_b: Columns from second file

    Returns:
        Dictionary with structure comparison results
    """
    set_a = set(columns_a)
    set_b = set(columns_b)

    missing_in_b = sorted(set_a - set_b)
    extra_in_b = sorted(set_b - set_a)
    common_columns = sorted(set_a & set_b)

    return {
        'missing_in_b': missing_in_b,
        'extra_in_b': extra_in_b,
        'common_columns': common_columns,
        'columns_a': columns_a,
        'columns_b': columns_b
    }


def _compare_rows(
    index_a: Dict[Tuple[str, ...], Dict[str, Any]],
    index_b: Dict[Tuple[str, ...], Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Compare rows between two indexed datasets.

    Args:
        index_a: Row index from first file
        index_b: Row index from second file

    Returns:
        Dictionary with row comparison results
    """
    keys_a = set(index_a.keys())
    keys_b = set(index_b.keys())

    missing_keys = keys_a - keys_b  # In A but not B
    extra_keys = keys_b - keys_a    # In B but not A
    common_keys = keys_a & keys_b   # In both

    # Convert keys back to row data for reporting
    missing_rows = [index_a[key] for key in missing_keys]
    extra_rows = [index_b[key] for key in extra_keys]

    return {
        'missing_keys': missing_keys,
        'extra_keys': extra_keys,
        'common_keys': common_keys,
        'missing_rows': missing_rows,
        'extra_rows': extra_rows
    }


def _compare_values(
    index_a: Dict[Tuple[str, ...], Dict[str, Any]],
    index_b: Dict[Tuple[str, ...], Dict[str, Any]],
    common_keys: Set[Tuple[str, ...]],
    common_columns: List[str],
    key_columns: List[str],
    tolerance: float = 0.0,
    max_differences: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Compare values for rows that exist in both files.

    Args:
        index_a: Row index from first file
        index_b: Row index from second file
        common_keys: Keys present in both files
        common_columns: Columns present in both files
        key_columns: Columns used for row identification
        tolerance: Numeric comparison tolerance
        max_differences: Stop after N differences (None = unlimited)

    Returns:
        List of value difference dictionaries
    """
    differences = []

    # Only compare non-key columns
    compare_columns = [col for col in common_columns if col not in key_columns]

    for key in common_keys:
        row_a = index_a[key]
        row_b = index_b[key]

        for column in compare_columns:
            value_a = row_a.get(column, '')
            value_b = row_b.get(column, '')

            # Normalize empty values
            if value_a is None:
                value_a = ''
            if value_b is None:
                value_b = ''

            value_a = str(value_a).strip()
            value_b = str(value_b).strip()

            # Check if values differ
            if value_a != value_b:
                # Try numeric comparison with tolerance
                numeric_diff = None
                if tolerance > 0:
                    try:
                        num_a = float(value_a) if value_a else 0.0
                        num_b = float(value_b) if value_b else 0.0
                        diff = abs(num_a - num_b)

                        if diff <= tolerance:
                            continue  # Within tolerance, skip

                        numeric_diff = num_b - num_a
                    except (ValueError, TypeError):
                        pass  # Not numeric, treat as string difference

                # Build row key dict for reporting
                row_key_dict = {col: row_a.get(col, '') for col in key_columns}

                differences.append({
                    'row_key': row_key_dict,
                    'column': column,
                    'value_a': value_a,
                    'value_b': value_b,
                    'difference': numeric_diff
                })

                # Check max differences limit
                if max_differences and len(differences) >= max_differences:
                    return differences

    return differences


def _calculate_vote_totals(
    rows: List[Dict[str, Any]],
    vote_columns: List[str]
) -> Dict[str, int]:
    """
    Calculate total votes for each vote type column.

    Args:
        rows: List of row dictionaries
        vote_columns: List of vote type column names

    Returns:
        Dictionary mapping vote column name to total votes
    """
    totals = {col: 0 for col in vote_columns}

    for row in rows:
        for col in vote_columns:
            value = row.get(col, '')
            if value:
                try:
                    totals[col] += int(float(str(value).strip()))
                except (ValueError, TypeError):
                    pass  # Skip non-numeric values

    return totals


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

    This function compares two CSV election files and identifies:
    - Structural differences (missing/extra columns)
    - Missing rows (in file A but not in file B)
    - Extra rows (in file B but not in file A)
    - Value mismatches in matching rows
    - Vote total discrepancies

    Args:
        file_a: Path to first CSV file
        file_b: Path to second CSV file
        key_columns: Columns to use as row identifier. If None, uses standard
                    election columns (county, precinct, office, district,
                    candidate, party)
        ignore_columns: Columns to exclude from comparison
        tolerance: Numeric comparison tolerance (default: 0.0)
        max_differences: Stop after N differences (default: unlimited)
        output_format: Output format - 'cli', 'web', or 'both' (default: 'cli')
        output_file: Output file path (HTML for web, text for cli)
        csv_export: Export detailed differences to CSV file
        verbose: Print detailed output (default: True)
        color: Use colored terminal output (default: True)

    Returns:
        Dictionary with comparison results containing:
        - metadata: File info and timestamps
        - summary: High-level statistics
        - column_differences: Missing/extra columns
        - row_differences: Missing/extra rows
        - value_differences: Value mismatches
        - vote_totals: Vote totals and differences

    Raises:
        FileNotFoundError: If either file doesn't exist
        ValueError: If files are invalid or incompatible

    Example:
        >>> results = compare_csv_files(
        ...     'original.csv',
        ...     'corrected.csv',
        ...     verbose=True
        ... )
        >>> print(f"Match rate: {results['summary']['percentage_match']:.1f}%")
    """
    if verbose:
        print(f"Comparing CSV files...")
        print(f"  File A: {file_a}")
        print(f"  File B: {file_b}")
        print()

    # Load and validate files
    if verbose:
        print("Loading files...")

    rows_a, columns_a, std_cols_a = _load_and_validate_csv(file_a, key_columns)
    rows_b, columns_b, std_cols_b = _load_and_validate_csv(file_b, key_columns)

    # Determine key columns
    if key_columns is None:
        # Use standard election columns that exist in both files
        key_columns = [
            col for col in ['county', 'precinct', 'office', 'district', 'candidate', 'party']
            if col in columns_a and col in columns_b
        ]
        if not key_columns:
            raise ValueError(
                "Cannot determine key columns. Please specify key_columns parameter."
            )

    if verbose:
        print(f"Using key columns: {key_columns}")
        print(f"File A: {len(rows_a)} rows, {len(columns_a)} columns")
        print(f"File B: {len(rows_b)} rows, {len(columns_b)} columns")
        print()

    # Compare structures
    if verbose:
        print("Comparing structures...")

    structure_diff = _compare_structures(columns_a, columns_b)

    if structure_diff['missing_in_b']:
        print(f"Warning: {len(structure_diff['missing_in_b'])} column(s) in File A but not File B")
    if structure_diff['extra_in_b']:
        print(f"Warning: {len(structure_diff['extra_in_b'])} column(s) in File B but not File A")

    # Build row indices
    if verbose:
        print("Indexing rows...")

    index_a = _build_row_index(rows_a, key_columns, "File A")
    index_b = _build_row_index(rows_b, key_columns, "File B")

    # Compare rows
    if verbose:
        print("Comparing rows...")

    row_diff = _compare_rows(index_a, index_b)

    # Compare values
    if verbose:
        print("Comparing values...")

    value_diffs = _compare_values(
        index_a,
        index_b,
        row_diff['common_keys'],
        structure_diff['common_columns'],
        key_columns,
        tolerance,
        max_differences
    )

    # Calculate vote totals
    if verbose:
        print("Calculating vote totals...")

    # Identify vote columns (non-standard columns common to both files)
    vote_columns = [
        col for col in structure_diff['common_columns']
        if col not in STANDARD_COLUMNS
    ]

    # Apply ignore_columns filter
    if ignore_columns:
        vote_columns = [col for col in vote_columns if col not in ignore_columns]

    totals_a = _calculate_vote_totals(rows_a, vote_columns)
    totals_b = _calculate_vote_totals(rows_b, vote_columns)
    total_diffs = {
        col: totals_b.get(col, 0) - totals_a.get(col, 0)
        for col in vote_columns
    }

    # Calculate summary statistics
    total_missing = len(row_diff['missing_rows'])
    total_extra = len(row_diff['extra_rows'])
    total_value_diffs = len(value_diffs)
    total_common = len(row_diff['common_keys'])
    total_col_diffs = len(structure_diff['missing_in_b']) + len(structure_diff['extra_in_b'])

    total_differences = total_missing + total_extra + total_value_diffs + total_col_diffs

    # Calculate percentage match
    if len(rows_a) > 0:
        percentage_match = (total_common / len(rows_a)) * 100
    else:
        percentage_match = 100.0 if len(rows_b) == 0 else 0.0

    # Build results dictionary
    results = {
        'metadata': {
            'file_a': file_a,
            'file_b': file_b,
            'compared_at': datetime.now().isoformat(),
            'row_count_a': len(rows_a),
            'row_count_b': len(rows_b),
            'column_count_a': len(columns_a),
            'column_count_b': len(columns_b),
            'key_columns': key_columns,
        },
        'summary': {
            'total_differences': total_differences,
            'missing_rows': total_missing,
            'extra_rows': total_extra,
            'value_mismatches': total_value_diffs,
            'missing_columns': len(structure_diff['missing_in_b']),
            'extra_columns': len(structure_diff['extra_in_b']),
            'identical_rows': total_common,
            'percentage_match': percentage_match,
        },
        'column_differences': structure_diff,
        'row_differences': row_diff,
        'value_differences': value_diffs,
        'vote_totals': {
            'file_a': totals_a,
            'file_b': totals_b,
            'differences': total_diffs,
        }
    }

    # Generate output
    if output_format in ['cli', 'both']:
        output_text = _format_cli_output(results, verbose, color)
        print(output_text)

        if output_file and output_format == 'cli':
            with open(output_file, 'w') as f:
                # Strip color codes for file output
                f.write(output_text)
            if verbose:
                print(f"\nReport saved to: {output_file}")

    if output_format in ['web', 'both']:
        if not output_file:
            output_file = 'comparison_report.html'
        html_output = _format_web_output(results)
        with open(output_file, 'w') as f:
            f.write(html_output)
        if verbose:
            print(f"\nWeb report saved to: {output_file}")

    # Export differences to CSV if requested
    if csv_export:
        _export_differences_csv(results, csv_export)
        if verbose:
            print(f"Differences exported to: {csv_export}")

    return results


def _format_cli_output(
    results: Dict[str, Any],
    verbose: bool = True,
    color: bool = True
) -> str:
    """
    Format comparison results for command-line output.

    Args:
        results: Comparison results dictionary
        verbose: Include detailed output
        color: Use ANSI color codes

    Returns:
        Formatted string for terminal output
    """
    # Color codes (ANSI)
    if color:
        GREEN = '\033[92m'
        RED = '\033[91m'
        YELLOW = '\033[93m'
        CYAN = '\033[96m'
        BOLD = '\033[1m'
        RESET = '\033[0m'
    else:
        GREEN = RED = YELLOW = CYAN = BOLD = RESET = ''

    lines = []

    # Header
    lines.append(f"{BOLD}{CYAN}CSV Comparison Report{RESET}")
    lines.append("=" * 70)
    lines.append("")

    # Files
    lines.append(f"{BOLD}Files:{RESET}")
    lines.append(f"  File A: {results['metadata']['file_a']}")
    lines.append(f"  File B: {results['metadata']['file_b']}")
    lines.append("")

    # Structure
    lines.append(f"{BOLD}Structure:{RESET}")
    row_a = results['metadata']['row_count_a']
    row_b = results['metadata']['row_count_b']
    row_diff = row_b - row_a
    row_diff_str = f"({row_diff:+d})" if row_diff != 0 else "(identical)"

    col_a = results['metadata']['column_count_a']
    col_b = results['metadata']['column_count_b']
    col_diff = col_b - col_a
    col_diff_str = f"({col_diff:+d})" if col_diff != 0 else "(identical)"

    lines.append(f"  Rows:    {row_a:,} vs {row_b:,} {row_diff_str}")
    lines.append(f"  Columns: {col_a} vs {col_b} {col_diff_str}")
    lines.append("")

    # Results summary
    lines.append(f"{BOLD}Results:{RESET}")
    summary = results['summary']

    match_pct = summary['percentage_match']
    if match_pct == 100.0:
        match_symbol = f"{GREEN}✓{RESET}"
    else:
        match_symbol = f"{YELLOW}~{RESET}"

    lines.append(f"  {match_symbol} Identical rows:      {summary['identical_rows']:,} ({match_pct:.1f}%)")

    if summary['missing_rows'] > 0:
        lines.append(f"  {RED}✗{RESET} Missing rows:        {summary['missing_rows']:,}")

    if summary['extra_rows'] > 0:
        lines.append(f"  {RED}✗{RESET} Extra rows:          {summary['extra_rows']:,}")

    if summary['value_mismatches'] > 0:
        lines.append(f"  {RED}✗{RESET} Value mismatches:    {summary['value_mismatches']:,}")

    if summary['missing_columns'] > 0:
        lines.append(f"  {RED}✗{RESET} Missing columns:     {summary['missing_columns']}")

    if summary['extra_columns'] > 0:
        lines.append(f"  {RED}✗{RESET} Extra columns:       {summary['extra_columns']}")

    lines.append("")

    # Vote totals
    vote_totals = results['vote_totals']
    if vote_totals['file_a'] or vote_totals['file_b']:
        lines.append(f"{BOLD}Vote Totals:{RESET}")

        all_vote_cols = sorted(set(vote_totals['file_a'].keys()) | set(vote_totals['file_b'].keys()))

        for col in all_vote_cols:
            total_a = vote_totals['file_a'].get(col, 0)
            total_b = vote_totals['file_b'].get(col, 0)
            diff = vote_totals['differences'].get(col, 0)

            if diff == 0:
                diff_str = f"{GREEN}(✓ Match){RESET}"
            else:
                diff_str = f"{YELLOW}(Δ {diff:+,}){RESET}"

            lines.append(f"  {col:20s} File A: {total_a:,}  File B: {total_b:,}  {diff_str}")

        lines.append("")

    # Overall match rate
    if match_pct == 100.0:
        lines.append(f"{GREEN}{BOLD}Overall Match: 100% - Files are identical!{RESET}")
    else:
        lines.append(f"{BOLD}Overall Match: {match_pct:.1f}%{RESET}")

    if not verbose and summary['total_differences'] > 0:
        lines.append("")
        lines.append("For detailed differences, use --verbose flag or check CSV export.")

    # Detailed output if verbose
    if verbose and summary['total_differences'] > 0:
        lines.append("")
        lines.append("=" * 70)
        lines.append(f"{BOLD}Detailed Differences{RESET}")
        lines.append("")

        # Missing rows
        if summary['missing_rows'] > 0:
            lines.append(f"{BOLD}Missing Rows ({summary['missing_rows']}):{RESET}")
            lines.append("-" * 70)

            for i, row in enumerate(results['row_differences']['missing_rows'][:10], 1):
                key_str = " | ".join([f"{k}: {row.get(k, '')}" for k in results['metadata']['key_columns']])
                lines.append(f"{i}. {key_str}")

            if summary['missing_rows'] > 10:
                lines.append(f"... and {summary['missing_rows'] - 10} more")

            lines.append("")

        # Extra rows
        if summary['extra_rows'] > 0:
            lines.append(f"{BOLD}Extra Rows ({summary['extra_rows']}):{RESET}")
            lines.append("-" * 70)

            for i, row in enumerate(results['row_differences']['extra_rows'][:10], 1):
                key_str = " | ".join([f"{k}: {row.get(k, '')}" for k in results['metadata']['key_columns']])
                lines.append(f"{i}. {key_str}")

            if summary['extra_rows'] > 10:
                lines.append(f"... and {summary['extra_rows'] - 10} more")

            lines.append("")

        # Value mismatches
        if summary['value_mismatches'] > 0:
            lines.append(f"{BOLD}Value Mismatches ({summary['value_mismatches']}):{RESET}")
            lines.append("-" * 70)

            for i, diff in enumerate(results['value_differences'][:20], 1):
                key_str = " | ".join([f"{k}: {v}" for k, v in diff['row_key'].items()])
                lines.append(f"{i}. {key_str}")
                lines.append(f"   Column: {diff['column']}")
                lines.append(f"     File A: {diff['value_a']}")
                lines.append(f"     File B: {diff['value_b']}")

                if diff['difference'] is not None:
                    lines.append(f"     Diff:   {diff['difference']:+}")

                lines.append("")

            if summary['value_mismatches'] > 20:
                lines.append(f"... and {summary['value_mismatches'] - 20} more")

    return "\n".join(lines)


def _export_differences_csv(results: Dict[str, Any], output_file: str) -> None:
    """
    Export differences to a CSV file.

    Args:
        results: Comparison results dictionary
        output_file: Path to output CSV file
    """
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['type', 'county', 'precinct', 'office', 'district',
                     'candidate', 'party', 'column', 'value_a', 'value_b',
                     'difference', 'notes']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        key_columns = results['metadata']['key_columns']

        # Missing rows
        for row in results['row_differences']['missing_rows']:
            row_data = {
                'type': 'missing_row',
                **{k: row.get(k, '') for k in key_columns},
                'column': '',
                'value_a': 'present',
                'value_b': 'missing',
                'difference': '',
                'notes': 'Row exists in File A but not in File B'
            }
            writer.writerow(row_data)

        # Extra rows
        for row in results['row_differences']['extra_rows']:
            row_data = {
                'type': 'extra_row',
                **{k: row.get(k, '') for k in key_columns},
                'column': '',
                'value_a': 'missing',
                'value_b': 'present',
                'difference': '',
                'notes': 'Row exists in File B but not in File A'
            }
            writer.writerow(row_data)

        # Value mismatches
        for diff in results['value_differences']:
            row_data = {
                'type': 'value_mismatch',
                **diff['row_key'],
                'column': diff['column'],
                'value_a': diff['value_a'],
                'value_b': diff['value_b'],
                'difference': diff['difference'] if diff['difference'] is not None else '',
                'notes': ''
            }
            writer.writerow(row_data)


def _format_web_output(results: Dict[str, Any]) -> str:
    """
    Format comparison results as an interactive HTML report.

    Args:
        results: Comparison results dictionary

    Returns:
        HTML string
    """
    import json
    from html import escape

    metadata = results['metadata']
    summary = results['summary']
    col_diff = results['column_differences']
    row_diff = results['row_differences']
    value_diffs = results['value_differences']
    vote_totals = results['vote_totals']
    key_columns = metadata['key_columns']

    # Build JavaScript data for interactive features
    js_value_diffs = []
    for diff in value_diffs:
        row_key_str = ' | '.join([f"{k}: {v}" for k, v in diff['row_key'].items()])
        js_value_diffs.append({
            'row_key': row_key_str,
            'row_key_dict': diff['row_key'],
            'column': diff['column'],
            'value_a': diff['value_a'],
            'value_b': diff['value_b'],
            'difference': diff['difference']
        })

    js_missing_rows = []
    for row in row_diff['missing_rows']:
        row_key_str = ' | '.join([f"{k}: {row.get(k, '')}" for k in key_columns])
        js_missing_rows.append({
            'row_key': row_key_str,
            'data': {k: row.get(k, '') for k in key_columns}
        })

    js_extra_rows = []
    for row in row_diff['extra_rows']:
        row_key_str = ' | '.join([f"{k}: {row.get(k, '')}" for k in key_columns])
        js_extra_rows.append({
            'row_key': row_key_str,
            'data': {k: row.get(k, '') for k in key_columns}
        })

    # Calculate match icon
    match_pct = summary['percentage_match']
    if match_pct == 100.0:
        match_icon = "✓"
        match_class = "perfect-match"
    elif match_pct >= 95.0:
        match_icon = "~"
        match_class = "good-match"
    else:
        match_icon = "✗"
        match_class = "poor-match"

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSV Comparison Report</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header p {{
            opacity: 0.9;
            font-size: 1.1em;
        }}

        .content {{
            padding: 30px;
        }}

        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}

        .card {{
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.2s;
        }}

        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }}

        .card h3 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .card p {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .card.perfect-match {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
        }}

        .card.perfect-match p {{
            color: rgba(255,255,255,0.9);
        }}

        .card.good-match {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }}

        .card.good-match p {{
            color: rgba(255,255,255,0.9);
        }}

        .card.poor-match {{
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            color: white;
        }}

        .card.poor-match p {{
            color: rgba(255,255,255,0.9);
        }}

        .card.info {{
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        }}

        .card.warning {{
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        }}

        .section {{
            margin: 40px 0;
        }}

        .section-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 20px;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            cursor: pointer;
            user-select: none;
            border-radius: 5px;
            margin-bottom: 15px;
        }}

        .section-header:hover {{
            background: #e9ecef;
        }}

        .section-header h2 {{
            font-size: 1.5em;
            color: #333;
        }}

        .section-header .badge {{
            background: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }}

        .section-header .toggle {{
            font-size: 1.2em;
            color: #667eea;
        }}

        .section-content {{
            padding: 20px;
            background: #f8f9fa;
            border-radius: 5px;
            margin-bottom: 20px;
        }}

        .section-content.collapsed {{
            display: none;
        }}

        .filters {{
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}

        .filter-input {{
            flex: 1;
            min-width: 200px;
            padding: 10px 15px;
            border: 2px solid #e9ecef;
            border-radius: 5px;
            font-size: 1em;
        }}

        .filter-input:focus {{
            outline: none;
            border-color: #667eea;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 5px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 1px;
        }}

        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e9ecef;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        .value-diff {{
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 10px;
            align-items: center;
        }}

        .value-a {{
            background: #fff5f5;
            padding: 8px 12px;
            border-radius: 4px;
            border-left: 3px solid #e53e3e;
            font-family: 'Courier New', monospace;
        }}

        .value-b {{
            background: #f0fff4;
            padding: 8px 12px;
            border-radius: 4px;
            border-left: 3px solid #38a169;
            font-family: 'Courier New', monospace;
        }}

        .arrow {{
            color: #667eea;
            font-size: 1.2em;
            font-weight: bold;
        }}

        .file-info {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}

        .file-info p {{
            margin: 5px 0;
        }}

        .file-path {{
            font-family: 'Courier New', monospace;
            background: white;
            padding: 5px 10px;
            border-radius: 3px;
            display: inline-block;
            margin-left: 10px;
        }}

        .vote-totals {{
            display: grid;
            gap: 15px;
        }}

        .vote-row {{
            background: white;
            padding: 15px;
            border-radius: 5px;
            display: grid;
            grid-template-columns: 200px 1fr 1fr auto;
            gap: 15px;
            align-items: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }}

        .vote-label {{
            font-weight: 600;
            color: #333;
        }}

        .vote-value {{
            font-family: 'Courier New', monospace;
            font-size: 1.1em;
        }}

        .vote-diff {{
            font-weight: bold;
            padding: 5px 15px;
            border-radius: 20px;
            text-align: center;
        }}

        .vote-diff.match {{
            background: #d4edda;
            color: #155724;
        }}

        .vote-diff.different {{
            background: #fff3cd;
            color: #856404;
        }}

        .no-data {{
            text-align: center;
            padding: 40px;
            color: #666;
            font-style: italic;
        }}

        .metadata {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}

        .metadata-item {{
            background: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }}

        .metadata-label {{
            font-weight: 600;
            color: #667eea;
            margin-bottom: 5px;
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .metadata-value {{
            font-size: 1.1em;
            color: #333;
        }}

        .export-btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            transition: background 0.2s;
        }}

        .export-btn:hover {{
            background: #5568d3;
        }}

        .column-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}

        .column-tag {{
            background: #e9ecef;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
        }}

        .column-tag.missing {{
            background: #fff5f5;
            color: #e53e3e;
        }}

        .column-tag.extra {{
            background: #f0fff4;
            color: #38a169;
        }}

        @media (max-width: 768px) {{
            .summary-cards {{
                grid-template-columns: 1fr;
            }}

            .vote-row {{
                grid-template-columns: 1fr;
            }}

            .value-diff {{
                grid-template-columns: 1fr;
            }}

            .arrow {{
                text-align: center;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 CSV Comparison Report</h1>
            <p>Generated on {escape(metadata['compared_at'])}</p>
        </div>

        <div class="content">
            <!-- Summary Cards -->
            <div class="summary-cards">
                <div class="card {match_class}">
                    <h3>{match_icon} {match_pct:.1f}%</h3>
                    <p>Match Rate</p>
                </div>
                <div class="card info">
                    <h3>{summary['identical_rows']:,}</h3>
                    <p>Identical Rows</p>
                </div>
                <div class="card warning">
                    <h3>{summary['total_differences']:,}</h3>
                    <p>Total Differences</p>
                </div>
                <div class="card warning">
                    <h3>{summary['value_mismatches']:,}</h3>
                    <p>Value Mismatches</p>
                </div>
            </div>

            <!-- File Information -->
            <div class="section">
                <div class="section-header" onclick="toggleSection('files')">
                    <h2>📁 File Information</h2>
                    <span class="toggle" id="files-toggle">▼</span>
                </div>
                <div class="section-content" id="files-content">
                    <div class="metadata">
                        <div class="metadata-item">
                            <div class="metadata-label">File A</div>
                            <div class="metadata-value file-path">{escape(metadata['file_a'])}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">File B</div>
                            <div class="metadata-value file-path">{escape(metadata['file_b'])}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Rows in File A</div>
                            <div class="metadata-value">{metadata['row_count_a']:,}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Rows in File B</div>
                            <div class="metadata-value">{metadata['row_count_b']:,}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Columns in File A</div>
                            <div class="metadata-value">{metadata['column_count_a']}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Columns in File B</div>
                            <div class="metadata-value">{metadata['column_count_b']}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Key Columns</div>
                            <div class="metadata-value">{', '.join(key_columns)}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Comparison Time</div>
                            <div class="metadata-value">{escape(metadata['compared_at'])}</div>
                        </div>
                    </div>
                </div>
            </div>
"""

    # Column Differences Section
    if col_diff['missing_in_b'] or col_diff['extra_in_b']:
        html += f"""
            <!-- Column Differences -->
            <div class="section">
                <div class="section-header" onclick="toggleSection('columns')">
                    <h2>📋 Column Differences</h2>
                    <span class="badge">{len(col_diff['missing_in_b']) + len(col_diff['extra_in_b'])}</span>
                    <span class="toggle" id="columns-toggle">▼</span>
                </div>
                <div class="section-content" id="columns-content">
"""
        if col_diff['missing_in_b']:
            html += f"""
                    <h3>Missing in File B ({len(col_diff['missing_in_b'])})</h3>
                    <div class="column-list">
"""
            for col in col_diff['missing_in_b']:
                html += f'                        <span class="column-tag missing">{escape(col)}</span>\n'
            html += """
                    </div>
                    <br>
"""

        if col_diff['extra_in_b']:
            html += f"""
                    <h3>Extra in File B ({len(col_diff['extra_in_b'])})</h3>
                    <div class="column-list">
"""
            for col in col_diff['extra_in_b']:
                html += f'                        <span class="column-tag extra">{escape(col)}</span>\n'
            html += """
                    </div>
"""

        html += """
                </div>
            </div>
"""

    # Vote Totals Section
    if vote_totals['file_a'] or vote_totals['file_b']:
        all_vote_cols = sorted(set(vote_totals['file_a'].keys()) | set(vote_totals['file_b'].keys()))
        html += f"""
            <!-- Vote Totals -->
            <div class="section">
                <div class="section-header" onclick="toggleSection('votes')">
                    <h2>🗳️ Vote Totals</h2>
                    <span class="badge">{len(all_vote_cols)}</span>
                    <span class="toggle" id="votes-toggle">▼</span>
                </div>
                <div class="section-content" id="votes-content">
                    <div class="vote-totals">
"""

        for col in all_vote_cols:
            total_a = vote_totals['file_a'].get(col, 0)
            total_b = vote_totals['file_b'].get(col, 0)
            diff = vote_totals['differences'].get(col, 0)
            diff_class = "match" if diff == 0 else "different"
            diff_text = "✓ Match" if diff == 0 else f"Δ {diff:+,}"

            html += f"""
                        <div class="vote-row">
                            <div class="vote-label">{escape(col)}</div>
                            <div class="vote-value">File A: {total_a:,}</div>
                            <div class="vote-value">File B: {total_b:,}</div>
                            <div class="vote-diff {diff_class}">{diff_text}</div>
                        </div>
"""

        html += """
                    </div>
                </div>
            </div>
"""

    # Missing Rows Section
    if summary['missing_rows'] > 0:
        html += f"""
            <!-- Missing Rows -->
            <div class="section">
                <div class="section-header" onclick="toggleSection('missing')">
                    <h2>❌ Missing Rows</h2>
                    <span class="badge">{summary['missing_rows']:,}</span>
                    <span class="toggle" id="missing-toggle">▼</span>
                </div>
                <div class="section-content" id="missing-content">
                    <div class="filters">
                        <input type="text" class="filter-input" id="missing-filter"
                               placeholder="Filter missing rows..."
                               onkeyup="filterTable('missing-table', 'missing-filter')">
                    </div>
                    <table id="missing-table">
                        <thead>
                            <tr>
"""
        for col in key_columns:
            html += f"                                <th>{escape(col)}</th>\n"
        html += """
                            </tr>
                        </thead>
                        <tbody>
"""

        for row in row_diff['missing_rows'][:1000]:  # Limit to 1000 rows for performance
            html += "                            <tr>\n"
            for col in key_columns:
                html += f"                                <td>{escape(str(row.get(col, '')))}</td>\n"
            html += "                            </tr>\n"

        if summary['missing_rows'] > 1000:
            html += f"""
                            <tr>
                                <td colspan="{len(key_columns)}" style="text-align: center; font-style: italic; color: #666;">
                                    ... and {summary['missing_rows'] - 1000:,} more rows (showing first 1,000)
                                </td>
                            </tr>
"""

        html += """
                        </tbody>
                    </table>
                </div>
            </div>
"""

    # Extra Rows Section
    if summary['extra_rows'] > 0:
        html += f"""
            <!-- Extra Rows -->
            <div class="section">
                <div class="section-header" onclick="toggleSection('extra')">
                    <h2>➕ Extra Rows</h2>
                    <span class="badge">{summary['extra_rows']:,}</span>
                    <span class="toggle" id="extra-toggle">▼</span>
                </div>
                <div class="section-content" id="extra-content">
                    <div class="filters">
                        <input type="text" class="filter-input" id="extra-filter"
                               placeholder="Filter extra rows..."
                               onkeyup="filterTable('extra-table', 'extra-filter')">
                    </div>
                    <table id="extra-table">
                        <thead>
                            <tr>
"""
        for col in key_columns:
            html += f"                                <th>{escape(col)}</th>\n"
        html += """
                            </tr>
                        </thead>
                        <tbody>
"""

        for row in row_diff['extra_rows'][:1000]:  # Limit to 1000 rows for performance
            html += "                            <tr>\n"
            for col in key_columns:
                html += f"                                <td>{escape(str(row.get(col, '')))}</td>\n"
            html += "                            </tr>\n"

        if summary['extra_rows'] > 1000:
            html += f"""
                            <tr>
                                <td colspan="{len(key_columns)}" style="text-align: center; font-style: italic; color: #666;">
                                    ... and {summary['extra_rows'] - 1000:,} more rows (showing first 1,000)
                                </td>
                            </tr>
"""

        html += """
                        </tbody>
                    </table>
                </div>
            </div>
"""

    # Value Mismatches Section
    if summary['value_mismatches'] > 0:
        html += f"""
            <!-- Value Mismatches -->
            <div class="section">
                <div class="section-header" onclick="toggleSection('mismatches')">
                    <h2>⚠️ Value Mismatches</h2>
                    <span class="badge">{summary['value_mismatches']:,}</span>
                    <span class="toggle" id="mismatches-toggle">▼</span>
                </div>
                <div class="section-content" id="mismatches-content">
                    <div class="filters">
                        <input type="text" class="filter-input" id="mismatch-filter"
                               placeholder="Filter value mismatches..."
                               onkeyup="filterTable('mismatch-table', 'mismatch-filter')">
                    </div>
                    <table id="mismatch-table">
                        <thead>
                            <tr>
                                <th>Row</th>
                                <th>Column</th>
                                <th>Values</th>
                            </tr>
                        </thead>
                        <tbody>
"""

        for diff in value_diffs[:1000]:  # Limit to 1000 for performance
            row_key_str = ' | '.join([f"{k}: {v}" for k, v in diff['row_key'].items()])
            diff_display = ""
            if diff['difference'] is not None:
                diff_display = f" (Δ {diff['difference']:+})"

            html += f"""
                            <tr>
                                <td>{escape(row_key_str)}</td>
                                <td><strong>{escape(diff['column'])}</strong></td>
                                <td>
                                    <div class="value-diff">
                                        <div class="value-a">File A: {escape(diff['value_a'])}</div>
                                        <div class="arrow">→</div>
                                        <div class="value-b">File B: {escape(diff['value_b'])}{diff_display}</div>
                                    </div>
                                </td>
                            </tr>
"""

        if summary['value_mismatches'] > 1000:
            html += f"""
                            <tr>
                                <td colspan="3" style="text-align: center; font-style: italic; color: #666;">
                                    ... and {summary['value_mismatches'] - 1000:,} more mismatches (showing first 1,000)
                                </td>
                            </tr>
"""

        html += """
                        </tbody>
                    </table>
                </div>
            </div>
"""

    # If no differences
    if summary['total_differences'] == 0:
        html += """
            <div class="no-data">
                <h2>🎉 Perfect Match!</h2>
                <p>The two CSV files are identical. No differences found.</p>
            </div>
"""

    # Footer with JavaScript
    html += """
        </div>
    </div>

    <script>
        function toggleSection(sectionId) {
            const content = document.getElementById(sectionId + '-content');
            const toggle = document.getElementById(sectionId + '-toggle');

            if (content.classList.contains('collapsed')) {
                content.classList.remove('collapsed');
                toggle.textContent = '▼';
            } else {
                content.classList.add('collapsed');
                toggle.textContent = '▶';
            }
        }

        function filterTable(tableId, filterId) {
            const input = document.getElementById(filterId);
            const filter = input.value.toLowerCase();
            const table = document.getElementById(tableId);
            const rows = table.getElementsByTagName('tr');

            for (let i = 1; i < rows.length; i++) {
                const row = rows[i];
                const text = row.textContent.toLowerCase();

                if (text.includes(filter)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            }
        }
    </script>
</body>
</html>
"""

    return html


def compare_county_to_precinct_totals(
    election_prefix: str,
    county_name: str,
    directory: str = '.',
    tolerance: float = 0.0,
    verbose: bool = True,
    output_format: str = 'cli',
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compare county-level summary totals to aggregated precinct-level totals.

    This function reads both a county-level summary file and its corresponding
    precinct-level file, aggregates the precinct data, and reports any differences
    between the county summary and the aggregated precinct totals.

    Args:
        election_prefix: Election prefix (e.g., "20251104__pa__general")
        county_name: County name (e.g., "adams")
        directory: Directory containing the CSV files (default: current directory)
        tolerance: Numeric comparison tolerance (default: 0.0)
        verbose: Print detailed output (default: True)
        output_format: Output format - 'cli', 'web', or 'both' (default: 'cli')
        output_file: Optional output file path

    Returns:
        Dictionary with comparison results containing:
        - metadata: File info and comparison details
        - summary: High-level statistics
        - differences: List of rows with mismatches
        - vote_totals: Aggregated vote totals and differences

    Raises:
        FileNotFoundError: If either file doesn't exist
        ValueError: If files are invalid or incompatible

    Example:
        >>> results = compare_county_to_precinct_totals(
        ...     election_prefix='20251104__pa__general',
        ...     county_name='adams',
        ...     directory='data/2025'
        ... )
        >>> if results['summary']['total_differences'] == 0:
        ...     print("County and precinct totals match!")
    """
    # Normalize county name to lowercase
    county_lower = county_name.lower()

    # Build file paths
    county_file = os.path.join(directory, f"{election_prefix}__{county_lower}__county.csv")
    precinct_file = os.path.join(directory, f"{election_prefix}__{county_lower}__precinct.csv")

    if verbose:
        print(f"County vs Precinct Totals Comparison")
        print("=" * 70)
        print(f"Election: {election_prefix}")
        print(f"County: {county_name}")
        print(f"County file: {county_file}")
        print(f"Precinct file: {precinct_file}")
        print()

    # Check if files exist
    if not os.path.exists(county_file):
        raise FileNotFoundError(f"County file not found: {county_file}")
    if not os.path.exists(precinct_file):
        raise FileNotFoundError(f"Precinct file not found: {precinct_file}")

    # Load county file
    if verbose:
        print("Loading county-level summary...")

    county_rows, county_columns, _ = _load_and_validate_csv(county_file)

    # Load precinct file
    if verbose:
        print("Loading precinct-level data...")

    precinct_rows, precinct_columns, _ = _load_and_validate_csv(precinct_file)

    # Identify vote columns (non-standard columns)
    county_vote_cols = [col for col in county_columns if col not in STANDARD_COLUMNS]
    precinct_vote_cols = [col for col in precinct_columns if col not in STANDARD_COLUMNS]

    # Check that vote columns match
    county_vote_set = set(county_vote_cols)
    precinct_vote_set = set(precinct_vote_cols)

    if county_vote_set != precinct_vote_set:
        missing_in_precinct = county_vote_set - precinct_vote_set
        extra_in_precinct = precinct_vote_set - county_vote_set

        if missing_in_precinct or extra_in_precinct:
            print("Warning: Vote column mismatch between files")
            if missing_in_precinct:
                print(f"  Missing in precinct file: {missing_in_precinct}")
            if extra_in_precinct:
                print(f"  Extra in precinct file: {extra_in_precinct}")

    # Use common vote columns
    vote_columns = sorted(county_vote_set & precinct_vote_set)

    if verbose:
        print(f"County file: {len(county_rows)} rows")
        print(f"Precinct file: {len(precinct_rows)} rows")
        print(f"Vote columns: {vote_columns}")
        print()

    # Determine key columns for aggregation (everything except precinct and vote columns)
    key_columns = [col for col in precinct_columns if col in STANDARD_COLUMNS and col != 'precinct']

    if verbose:
        print(f"Aggregating precinct data by: {key_columns}")
        print()

    # Aggregate precinct data
    aggregated_precinct = {}

    for row in precinct_rows:
        # Build key from non-precinct standard columns
        key_values = tuple(str(row.get(col, '')).strip().lower() for col in key_columns)

        if key_values not in aggregated_precinct:
            # Initialize aggregation
            aggregated_precinct[key_values] = {
                **{col: row.get(col, '') for col in key_columns},
                **{vote_col: 0 for vote_col in vote_columns}
            }

        # Add vote totals
        for vote_col in vote_columns:
            value = row.get(vote_col, '')
            if value:
                try:
                    aggregated_precinct[key_values][vote_col] += int(float(str(value).strip()))
                except (ValueError, TypeError):
                    pass  # Skip non-numeric values

    if verbose:
        print(f"Aggregated to {len(aggregated_precinct)} unique rows")
        print()

    # Build index of county data
    county_index = {}
    for row in county_rows:
        key_values = tuple(str(row.get(col, '')).strip().lower() for col in key_columns)
        county_index[key_values] = row

    # Compare aggregated precinct data to county data
    if verbose:
        print("Comparing totals...")
        print()

    differences = []
    all_keys = set(county_index.keys()) | set(aggregated_precinct.keys())

    missing_in_precinct = []
    missing_in_county = []

    for key in sorted(all_keys):
        county_row = county_index.get(key)
        precinct_row = aggregated_precinct.get(key)

        # Build readable key dict
        key_dict = dict(zip(key_columns, key)) if county_row or precinct_row else {}

        if county_row and precinct_row:
            # Both exist - compare vote totals
            for vote_col in vote_columns:
                county_val = county_row.get(vote_col, '')
                precinct_val = precinct_row.get(vote_col, 0)

                # Normalize county value
                if county_val:
                    try:
                        county_val = int(float(str(county_val).strip()))
                    except (ValueError, TypeError):
                        county_val = 0
                else:
                    county_val = 0

                # Check if values differ
                diff = precinct_val - county_val

                if tolerance > 0:
                    if abs(diff) <= tolerance:
                        continue  # Within tolerance

                if diff != 0:
                    # Get original (non-lowercased) values for display
                    display_key = {col: county_row.get(col, precinct_row.get(col, '')) for col in key_columns}

                    differences.append({
                        'row_key': display_key,
                        'vote_type': vote_col,
                        'county_total': county_val,
                        'precinct_total': precinct_val,
                        'difference': diff
                    })

        elif county_row and not precinct_row:
            # In county but not in aggregated precinct data
            display_key = {col: county_row.get(col, '') for col in key_columns}
            missing_in_precinct.append(display_key)

        elif precinct_row and not county_row:
            # In aggregated precinct but not in county
            display_key = {col: precinct_row.get(col, '') for col in key_columns}
            missing_in_county.append(display_key)

    # Calculate summary statistics
    total_diffs = len(differences)
    total_missing_in_precinct = len(missing_in_precinct)
    total_missing_in_county = len(missing_in_county)
    total_issues = total_diffs + total_missing_in_precinct + total_missing_in_county

    # Build results
    results = {
        'metadata': {
            'election_prefix': election_prefix,
            'county_name': county_name,
            'county_file': county_file,
            'precinct_file': precinct_file,
            'compared_at': datetime.now().isoformat(),
            'county_rows': len(county_rows),
            'precinct_rows': len(precinct_rows),
            'aggregated_rows': len(aggregated_precinct),
            'key_columns': key_columns,
            'vote_columns': vote_columns,
        },
        'summary': {
            'total_differences': total_issues,
            'value_mismatches': total_diffs,
            'missing_in_precinct': total_missing_in_precinct,
            'missing_in_county': total_missing_in_county,
            'match_percentage': 100.0 if total_issues == 0 else 0.0,
        },
        'differences': differences,
        'missing_in_precinct': missing_in_precinct,
        'missing_in_county': missing_in_county,
    }

    # Output results
    if output_format in ['cli', 'both']:
        output_text = _format_county_precinct_output(results, verbose)
        print(output_text)

        if output_file and output_format == 'cli':
            with open(output_file, 'w') as f:
                f.write(output_text)
            if verbose:
                print(f"\nReport saved to: {output_file}")

    if output_format in ['web', 'both']:
        if not output_file:
            output_file = f'county_precinct_comparison_{county_lower}.html'
        html_output = _format_county_precinct_web_output(results)
        with open(output_file, 'w') as f:
            f.write(html_output)
        if verbose:
            print(f"\nWeb report saved to: {output_file}")

    return results


def _format_county_precinct_output(
    results: Dict[str, Any],
    verbose: bool = True
) -> str:
    """
    Format county vs precinct comparison results for CLI output.

    Args:
        results: Comparison results dictionary
        verbose: Include detailed output

    Returns:
        Formatted string for terminal output
    """
    lines = []

    # Header
    lines.append("\nCounty vs Precinct Totals Comparison Results")
    lines.append("=" * 70)
    lines.append("")

    # Summary
    summary = results['summary']
    metadata = results['metadata']

    lines.append(f"Election: {metadata['election_prefix']}")
    lines.append(f"County: {metadata['county_name']}")
    lines.append("")

    lines.append(f"County file rows: {metadata['county_rows']:,}")
    lines.append(f"Precinct file rows: {metadata['precinct_rows']:,}")
    lines.append(f"Aggregated unique rows: {metadata['aggregated_rows']:,}")
    lines.append("")

    # Results
    if summary['total_differences'] == 0:
        lines.append("✓ MATCH: County and precinct totals match perfectly!")
    else:
        lines.append(f"✗ MISMATCH: Found {summary['total_differences']} issue(s)")
        lines.append("")

        if summary['value_mismatches'] > 0:
            lines.append(f"  Value mismatches: {summary['value_mismatches']}")

        if summary['missing_in_precinct'] > 0:
            lines.append(f"  Rows in county file but not in precinct data: {summary['missing_in_precinct']}")

        if summary['missing_in_county'] > 0:
            lines.append(f"  Rows in precinct data but not in county file: {summary['missing_in_county']}")

    lines.append("")

    # Detailed differences
    if verbose and summary['value_mismatches'] > 0:
        lines.append("Value Mismatches:")
        lines.append("-" * 70)

        for i, diff in enumerate(results['differences'][:50], 1):
            key_str = " | ".join([f"{k}: {v}" for k, v in diff['row_key'].items()])
            lines.append(f"\n{i}. {key_str}")
            lines.append(f"   Vote type: {diff['vote_type']}")
            lines.append(f"   County total:   {diff['county_total']:>10,}")
            lines.append(f"   Precinct total: {diff['precinct_total']:>10,}")
            lines.append(f"   Difference:     {diff['difference']:>10,}")

        if summary['value_mismatches'] > 50:
            lines.append(f"\n... and {summary['value_mismatches'] - 50} more")

        lines.append("")

    if verbose and summary['missing_in_precinct'] > 0:
        lines.append(f"Rows in County File but Missing in Precinct Data ({summary['missing_in_precinct']}):")
        lines.append("-" * 70)

        for i, row in enumerate(results['missing_in_precinct'][:20], 1):
            key_str = " | ".join([f"{k}: {v}" for k, v in row.items()])
            lines.append(f"{i}. {key_str}")

        if summary['missing_in_precinct'] > 20:
            lines.append(f"... and {summary['missing_in_precinct'] - 20} more")

        lines.append("")

    if verbose and summary['missing_in_county'] > 0:
        lines.append(f"Rows in Precinct Data but Missing in County File ({summary['missing_in_county']}):")
        lines.append("-" * 70)

        for i, row in enumerate(results['missing_in_county'][:20], 1):
            key_str = " | ".join([f"{k}: {v}" for k, v in row.items()])
            lines.append(f"{i}. {key_str}")

        if summary['missing_in_county'] > 20:
            lines.append(f"... and {summary['missing_in_county'] - 20} more")

        lines.append("")

    return "\n".join(lines)


def _format_county_precinct_web_output(results: Dict[str, Any]) -> str:
    """
    Format county vs precinct comparison as an interactive HTML report.

    Args:
        results: Comparison results dictionary

    Returns:
        HTML string
    """
    from html import escape

    metadata = results['metadata']
    summary = results['summary']

    match_class = "perfect-match" if summary['total_differences'] == 0 else "poor-match"
    match_icon = "✓" if summary['total_differences'] == 0 else "✗"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>County vs Precinct Comparison - {escape(metadata['county_name'])}</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2em;
            margin-bottom: 10px;
        }}

        .content {{
            padding: 30px;
        }}

        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}

        .card {{
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}

        .card h3 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .card.perfect-match {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
        }}

        .card.poor-match {{
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            color: white;
        }}

        .card.info {{
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            margin: 20px 0;
        }}

        th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
        }}

        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e9ecef;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        .mismatch {{
            color: #e53e3e;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>County vs Precinct Comparison</h1>
            <p>{escape(metadata['election_prefix'])} - {escape(metadata['county_name'])} County</p>
        </div>

        <div class="content">
            <div class="summary-cards">
                <div class="card {match_class}">
                    <h3>{match_icon}</h3>
                    <p>{"Match" if summary['total_differences'] == 0 else "Mismatch"}</p>
                </div>
                <div class="card info">
                    <h3>{summary['total_differences']:,}</h3>
                    <p>Total Issues</p>
                </div>
                <div class="card info">
                    <h3>{summary['value_mismatches']:,}</h3>
                    <p>Value Mismatches</p>
                </div>
            </div>
"""

    if summary['value_mismatches'] > 0:
        html += """
            <h2>Value Mismatches</h2>
            <table>
                <thead>
                    <tr>
                        <th>Row</th>
                        <th>Vote Type</th>
                        <th>County Total</th>
                        <th>Precinct Total</th>
                        <th>Difference</th>
                    </tr>
                </thead>
                <tbody>
"""
        for diff in results['differences'][:500]:
            key_str = ' | '.join([f"{k}: {v}" for k, v in diff['row_key'].items()])
            html += f"""
                    <tr>
                        <td>{escape(key_str)}</td>
                        <td>{escape(diff['vote_type'])}</td>
                        <td>{diff['county_total']:,}</td>
                        <td>{diff['precinct_total']:,}</td>
                        <td class="mismatch">{diff['difference']:+,}</td>
                    </tr>
"""
        html += """
                </tbody>
            </table>
"""

    if summary['total_differences'] == 0:
        html += """
            <div style="text-align: center; padding: 40px;">
                <h2>🎉 Perfect Match!</h2>
                <p>County and precinct totals match perfectly.</p>
            </div>
"""

    html += """
        </div>
    </div>
</body>
</html>
"""

    return html


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
