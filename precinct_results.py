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
from typing import List, Dict, Set, Optional, Tuple
from difflib import SequenceMatcher


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
