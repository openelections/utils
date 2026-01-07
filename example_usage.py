"""
Example usage of the precinct_results module for OpenElections data repositories.

This shows how to import and use the statewide precinct results generator
in various OpenElections state repositories (openelections-data-tx, etc.)
"""

from precinct_results import (
    generate_statewide_precinct_file,
    generate_vote_columns_report,
    compare_precinct_names,
    collect_precinct_names,
    check_party_variations,
    check_party_variations_directory,
    compare_csv_files,
    compare_county_to_precinct_totals
)


# Example 1: Basic usage for Texas 2020 General Election
def example_texas_2020():
    """Generate statewide file for Texas 2020 General Election"""
    generate_statewide_precinct_file(
        state_abbr='tx',
        election_date='20201103',
        source_directory='2020/counties',
        output_file='20201103__tx__general__precinct.csv'
    )


# Example 2: With office filtering
def example_with_office_filter():
    """Generate statewide file including only specific offices"""
    offices_to_include = [
        'President',
        'U.S. Senate',
        'U.S. House',
        'Governor',
        'Lieutenant Governor',
        'Attorney General',
        'State Senate',
        'State Representative'
    ]

    generate_statewide_precinct_file(
        state_abbr='tx',
        election_date='20201103',
        source_directory='2020/counties',
        output_file='20201103__tx__general__precinct_filtered.csv',
        offices_filter=offices_to_include
    )


# Example 3: Custom file pattern
def example_custom_pattern():
    """Generate statewide file with custom file matching pattern"""
    generate_statewide_precinct_file(
        state_abbr='ca',
        election_date='20201103',
        source_directory='2020/counties',
        output_file='20201103__ca__general__precinct.csv',
        file_pattern='*_precinct_results.csv'  # Different naming convention
    )


# Example 4: Generate report of vote columns by county
def example_generate_report():
    """Generate a report showing which vote type columns each county has"""
    generate_vote_columns_report(
        source_directory='2020/counties',
        file_pattern='20201103*precinct.csv',
        output_file='vote_columns_report.csv'
    )


# Example 5: Quiet mode (no verbose output)
def example_quiet_mode():
    """Generate statewide file without printing progress messages"""
    generate_statewide_precinct_file(
        state_abbr='tx',
        election_date='20201103',
        source_directory='2020/counties',
        output_file='20201103__tx__general__precinct.csv',
        verbose=False
    )


# Example 6: Multiple elections
def example_multiple_elections():
    """Process multiple elections in a loop"""
    elections = [
        ('20201103', '2020', 'general'),
        ('20220308', '2022', 'primary'),
        ('20220524', '2022', 'primary_runoff'),
    ]

    for date, year, election_type in elections:
        output_file = f"{date}__tx__{election_type}__precinct.csv"

        generate_statewide_precinct_file(
            state_abbr='tx',
            election_date=date,
            source_directory=f'{year}/counties',
            output_file=output_file
        )


# Example 7: Compare precinct names for a specific county between two elections
def example_compare_precincts_county():
    """Compare precinct names for a specific county between two elections"""
    results = compare_precinct_names(
        election1_dir='2020/counties',
        election1_pattern='20201103*precinct.csv',
        election2_dir='2022/counties',
        election2_pattern='20221108*precinct.csv',
        county_filter='Travis',  # Compare only Travis County
        output_file='travis_precinct_comparison.csv'
    )

    # Access results programmatically
    travis_results = results.get('Travis', {})
    stats = travis_results.get('stats', {})
    print(f"\nTravis County had {stats.get('change_percentage', 0):.1f}% precinct changes")


# Example 8: Compare precinct names statewide between two elections
def example_compare_precincts_statewide():
    """Compare precinct names across all counties between two elections"""
    results = compare_precinct_names(
        election1_dir='2020/counties',
        election1_pattern='20201103*precinct.csv',
        election2_dir='2022/counties',
        election2_pattern='20221108*precinct.csv',
        county_filter=None,  # Compare all counties
        similarity_threshold=0.7,  # Higher threshold for rename detection
        output_file='statewide_precinct_comparison.csv'
    )

    # Find counties with the most changes
    counties_by_change = sorted(
        results.items(),
        key=lambda x: x[1]['stats']['change_percentage'],
        reverse=True
    )

    print("\nTop 5 counties with most precinct changes:")
    for county, data in counties_by_change[:5]:
        pct = data['stats']['change_percentage']
        print(f"  {county}: {pct:.1f}%")


# Example 9: Just collect precinct names for analysis
def example_collect_precincts():
    """Collect precinct names for a single election"""
    precincts = collect_precinct_names(
        source_directory='2020/counties',
        file_pattern='20201103*precinct.csv',
        county_filter='Harris'  # Optional: filter by county
    )

    # Display results
    for county, precinct_set in precincts.items():
        print(f"{county} County: {len(precinct_set)} precincts")
        # Print first 5 precinct names
        for precinct in sorted(precinct_set)[:5]:
            print(f"  - {precinct}")


# Example 10: Compare same election type across years
def example_compare_general_elections():
    """Compare precinct names between general elections in different years"""
    compare_precinct_names(
        election1_dir='2018/counties',
        election1_pattern='20181106*precinct.csv',  # 2018 General
        election2_dir='2020/counties',
        election2_pattern='20201103*precinct.csv',  # 2020 General
        county_filter=None,
        output_file='general_election_precinct_comparison_2018_2020.csv'
    )


# Example 11: Compare with case normalization to detect case inconsistencies
def example_case_normalization():
    """Compare precincts with case normalization, reporting case mismatches"""
    results = compare_precinct_names(
        election1_dir='2020/counties',
        election1_pattern='20201103*precinct.csv',
        election2_dir='2022/counties',
        election2_pattern='20221108*precinct.csv',
        normalize_case=True,  # Ignore case differences (default)
        output_file='precinct_comparison_with_case_detection.csv'
    )

    # Check for case mismatches across all counties
    total_case_mismatches = sum(
        data['stats']['case_mismatch_count']
        for data in results.values()
    )

    if total_case_mismatches > 0:
        print(f"\nFound {total_case_mismatches} case mismatches across all counties")
        print("\nCounties with case mismatches:")
        for county, data in results.items():
            if data['case_mismatches']:
                print(f"  {county}: {len(data['case_mismatches'])} mismatches")


# Example 12: Strict case-sensitive comparison
def example_case_sensitive():
    """Compare precincts with strict case-sensitive matching"""
    results = compare_precinct_names(
        election1_dir='2020/counties',
        election1_pattern='20201103*precinct.csv',
        election2_dir='2022/counties',
        election2_pattern='20221108*precinct.csv',
        normalize_case=False,  # Strict case-sensitive comparison
        county_filter='Travis'
    )

    # With normalize_case=False, "Precinct 101" and "PRECINCT 101" are different


# Example 13: Check party variations in a single statewide file
def example_check_party_variations_single_file():
    """Check for party value variations in a single CSV file"""
    results = check_party_variations(
        csv_path='20201103__tx__general__precinct.csv',
        similarity_threshold=0.7,  # Adjust to be more/less strict
        output_file='party_variations_report.csv'
    )

    # Access results programmatically
    print(f"\nFound {len(results['unique_parties'])} unique party values")
    print(f"Detected {len(results['potential_variations'])} potential variations")

    # Check if there are variations to investigate
    if results['potential_variations']:
        print("\nParties that may need standardization:")
        for party1, party2, similarity in results['potential_variations']:
            count1 = results['party_counts'][party1]
            count2 = results['party_counts'][party2]
            print(f"  '{party1}' (n={count1}) vs '{party2}' (n={count2})")


# Example 14: Check party variations across county files
def example_check_party_variations_directory():
    """Check for party value variations across multiple county files"""
    results = check_party_variations_directory(
        source_directory='2020/counties',
        file_pattern='20201103*precinct.csv',
        similarity_threshold=0.7,
        output_file='party_variations_by_county.csv'
    )

    print(f"\nAnalyzed {results['file_count']} files")
    print(f"Found {len(results['all_parties'])} unique party values across all files")

    # Show which files use which party values
    if results['potential_variations']:
        print("\nPotential standardization needed:")
        for party1, party2, similarity in results['potential_variations']:
            files_with_party1 = [f for f, parties in results['by_file'].items() if party1 in parties]
            files_with_party2 = [f for f, parties in results['by_file'].items() if party2 in parties]
            print(f"  '{party1}' (in {len(files_with_party1)} files) vs '{party2}' (in {len(files_with_party2)} files)")


# Example 15: Check party variations with custom threshold
def example_party_variations_strict():
    """Check for party variations with a stricter similarity threshold"""
    # Higher threshold = more strict (only very similar strings are flagged)
    results = check_party_variations(
        csv_path='20201103__tx__general__precinct.csv',
        similarity_threshold=0.85,  # Only flag very similar variations
        verbose=True
    )

    # This would catch "DEM" vs "Democratic" but might miss "Democrat" vs "Dem"


# Example 16: Quiet party variation check
def example_party_variations_quiet():
    """Check for party variations without verbose output"""
    results = check_party_variations(
        csv_path='20201103__tx__general__precinct.csv',
        verbose=False  # No console output
    )

    # Process results programmatically
    if results['potential_variations']:
        # Handle variations in code
        for party1, party2, sim in results['potential_variations']:
            # Custom processing logic here
            pass


# Example 17: Party variation analysis for data quality report
def example_party_quality_report():
    """Generate a comprehensive party data quality report"""
    # Check single consolidated file
    results = check_party_variations(
        csv_path='20201103__tx__general__precinct.csv',
        output_file='party_quality_report.csv',
        verbose=True
    )

    # Generate summary statistics
    total_rows = results['total_count'] + results['empty_count']
    data_quality_score = (results['total_count'] / total_rows * 100) if total_rows > 0 else 0

    print(f"\n=== Party Data Quality Report ===")
    print(f"Total rows: {total_rows}")
    print(f"Rows with party values: {results['total_count']}")
    print(f"Rows with empty party: {results['empty_count']}")
    print(f"Data completeness: {data_quality_score:.1f}%")
    print(f"Unique party values: {len(results['unique_parties'])}")
    print(f"Standardization needed: {len(results['potential_variations'])} potential issues")


# Example 18: Compare two CSV files - basic comparison
def example_compare_csv_basic():
    """Compare two CSV files and display results in terminal"""
    results = compare_csv_files(
        'original_data.csv',
        'corrected_data.csv',
        verbose=True
    )

    # Check results programmatically
    if results['summary']['percentage_match'] == 100.0:
        print("\n✓ Files are identical!")
    else:
        print(f"\n⚠ Files differ: {results['summary']['total_differences']} differences found")


# Example 19: Generate web-based comparison report
def example_compare_csv_web_report():
    """Generate an interactive HTML comparison report"""
    compare_csv_files(
        '20201103__tx__travis__precinct.csv',
        '20201103__tx__travis__precinct_corrected.csv',
        output_format='web',
        output_file='comparison_report.html',
        verbose=True
    )
    print("\nOpen comparison_report.html in your browser to view the report")


# Example 20: Export differences to CSV for further analysis
def example_compare_csv_export():
    """Compare files and export all differences to CSV"""
    results = compare_csv_files(
        'file_a.csv',
        'file_b.csv',
        csv_export='differences.csv',
        verbose=True
    )

    # The differences.csv file can be opened in Excel or imported for analysis
    print(f"\nDifferences exported to differences.csv")
    print(f"Found {len(results['value_differences'])} value mismatches")


# Example 21: Compare with custom key columns
def example_compare_csv_custom_keys():
    """Compare files using custom key columns"""
    # If your CSV has different structure, specify key columns explicitly
    results = compare_csv_files(
        'file_a.csv',
        'file_b.csv',
        key_columns=['county', 'precinct', 'office', 'candidate'],
        verbose=True
    )


# Example 22: Compare with column exclusions
def example_compare_csv_ignore_columns():
    """Compare files while ignoring certain columns"""
    # Useful when you know certain columns will differ and don't care
    results = compare_csv_files(
        'file_a.csv',
        'file_b.csv',
        ignore_columns=['provisional', 'absentee'],  # Don't compare these
        verbose=True
    )


# Example 23: Compare with numeric tolerance
def example_compare_csv_with_tolerance():
    """Compare files with tolerance for small numeric differences"""
    # Ignore differences of 5 votes or less
    results = compare_csv_files(
        'file_a.csv',
        'file_b.csv',
        tolerance=5.0,
        verbose=True
    )

    # This is useful when comparing aggregated data that may have
    # rounding differences


# Example 24: Quiet comparison for automation
def example_compare_csv_quiet():
    """Compare files quietly for use in scripts/automation"""
    results = compare_csv_files(
        'file_a.csv',
        'file_b.csv',
        verbose=False,
        color=False
    )

    # Check results programmatically
    if results['summary']['total_differences'] > 0:
        print(f"FAIL: {results['summary']['total_differences']} differences")
        exit(1)
    else:
        print("PASS: Files match")
        exit(0)


# Example 25: Analyze specific types of differences
def example_compare_csv_analyze_differences():
    """Compare files and analyze specific types of differences"""
    results = compare_csv_files(
        'file_a.csv',
        'file_b.csv',
        verbose=False
    )

    # Check for vote total discrepancies
    print("\n=== Vote Total Analysis ===")
    for vote_type, diff in results['vote_totals']['differences'].items():
        if diff != 0:
            total_a = results['vote_totals']['file_a'][vote_type]
            total_b = results['vote_totals']['file_b'][vote_type]
            pct_diff = (diff / total_a * 100) if total_a > 0 else 0
            print(f"{vote_type}:")
            print(f"  File A: {total_a:,}")
            print(f"  File B: {total_b:,}")
            print(f"  Difference: {diff:+,} ({pct_diff:+.2f}%)")

    # Analyze value mismatches by column
    print("\n=== Value Mismatches by Column ===")
    mismatches_by_column = {}
    for diff in results['value_differences']:
        col = diff['column']
        mismatches_by_column[col] = mismatches_by_column.get(col, 0) + 1

    for col, count in sorted(mismatches_by_column.items()):
        print(f"{col}: {count} mismatch(es)")


# Example 26: Generate both CLI and web reports
def example_compare_csv_both_outputs():
    """Generate both terminal output and HTML report"""
    compare_csv_files(
        'file_a.csv',
        'file_b.csv',
        output_format='both',
        output_file='comparison_report.html',
        csv_export='differences.csv',
        verbose=True
    )


# Example 27: Data quality validation workflow
def example_compare_csv_quality_workflow():
    """Complete data quality validation workflow"""
    print("=== Data Quality Validation Workflow ===\n")

    # Step 1: Compare original vs processed
    print("Step 1: Comparing original vs processed data...")
    results = compare_csv_files(
        'original.csv',
        'processed.csv',
        csv_export='validation_differences.csv',
        verbose=False
    )

    # Step 2: Check if differences are within acceptable thresholds
    acceptable_error_rate = 1.0  # 1% error rate acceptable
    error_rate = 100.0 - results['summary']['percentage_match']

    print(f"Match rate: {results['summary']['percentage_match']:.2f}%")
    print(f"Error rate: {error_rate:.2f}%")

    if error_rate <= acceptable_error_rate:
        print("✓ PASS: Error rate within acceptable threshold")
    else:
        print("✗ FAIL: Error rate exceeds threshold")
        print(f"\nDifferences:")
        print(f"  Missing rows: {results['summary']['missing_rows']}")
        print(f"  Extra rows: {results['summary']['extra_rows']}")
        print(f"  Value mismatches: {results['summary']['value_mismatches']}")

    # Step 3: Generate detailed report for review
    if error_rate > acceptable_error_rate:
        print("\nGenerating detailed report for manual review...")
        compare_csv_files(
            'original.csv',
            'processed.csv',
            output_format='web',
            output_file='validation_report.html',
            verbose=False
        )
        print("Report saved to: validation_report.html")


# Example 28: Compare statewide files before publishing
def example_compare_csv_publication_check():
    """Compare statewide files before publishing to ensure quality"""
    # Compare the new statewide file against the previous version
    results = compare_csv_files(
        '20201103__tx__general__precinct.csv',
        '20221108__tx__general__precinct.csv',
        output_format='both',
        output_file='publication_check.html',
        csv_export='changes.csv',
        verbose=True
    )

    # Generate a summary report
    print("\n=== Publication Readiness Check ===")
    print(f"Files compared: ")
    print(f"  2020 Election: {results['metadata']['row_count_a']:,} rows")
    print(f"  2022 Election: {results['metadata']['row_count_b']:,} rows")
    print(f"\nStructure check:")
    print(f"  Columns match: {results['summary']['missing_columns'] == 0 and results['summary']['extra_columns'] == 0}")


# Example 29: Compare county summary to aggregated precinct totals
def example_compare_county_precinct_basic():
    """Compare county-level summary to aggregated precinct totals"""
    results = compare_county_to_precinct_totals(
        election_prefix='20251104__pa__general',
        county_name='adams',
        directory='data/2025',
        verbose=True
    )

    # Check results
    if results['summary']['total_differences'] == 0:
        print("\n✓ County and precinct totals match perfectly!")
    else:
        print(f"\n✗ Found {results['summary']['total_differences']} discrepancies")


# Example 30: Generate web report for county vs precinct comparison
def example_compare_county_precinct_web():
    """Generate HTML report comparing county to precinct totals"""
    compare_county_to_precinct_totals(
        election_prefix='20251104__pa__general',
        county_name='adams',
        directory='data/2025',
        output_format='web',
        output_file='adams_county_check.html',
        verbose=True
    )


# Example 31: Compare with tolerance for small differences
def example_compare_county_precinct_tolerance():
    """Compare county to precinct with tolerance for rounding errors"""
    results = compare_county_to_precinct_totals(
        election_prefix='20251104__pa__general',
        county_name='adams',
        directory='data/2025',
        tolerance=5.0,  # Ignore differences of 5 votes or less
        verbose=True
    )


# Example 32: Automated quality check for multiple counties
def example_county_precinct_batch_check():
    """Check multiple counties in a batch"""
    counties = ['adams', 'allegheny', 'beaver', 'berks', 'blair']
    election_prefix = '20251104__pa__general'

    issues_found = []

    for county in counties:
        print(f"\nChecking {county} County...")
        try:
            results = compare_county_to_precinct_totals(
                election_prefix=election_prefix,
                county_name=county,
                directory='data/2025',
                verbose=False
            )

            if results['summary']['total_differences'] > 0:
                issues_found.append({
                    'county': county,
                    'differences': results['summary']['total_differences']
                })
                print(f"  ✗ {results['summary']['total_differences']} issue(s) found")
            else:
                print(f"  ✓ Match")

        except FileNotFoundError as e:
            print(f"  ⚠ Files not found: {e}")

    # Summary
    print("\n" + "=" * 70)
    if issues_found:
        print(f"Counties with issues: {len(issues_found)}")
        for item in issues_found:
            print(f"  {item['county']}: {item['differences']} differences")
    else:
        print("✓ All counties match perfectly!")


if __name__ == '__main__':
    # Run the basic example
    print("Running basic Texas 2020 example...")
    print("(Modify the paths to match your actual directory structure)")
    print()

    # Uncomment the example you want to run:
    # example_texas_2020()
    # example_with_office_filter()
    # example_custom_pattern()
    # example_generate_report()
    # example_quiet_mode()
    # example_multiple_elections()
    # example_compare_precincts_county()
    # example_compare_precincts_statewide()
    # example_collect_precincts()
    # example_compare_general_elections()
    # example_case_normalization()
    # example_case_sensitive()
    # example_check_party_variations_single_file()
    # example_check_party_variations_directory()
    # example_party_variations_strict()
    # example_party_variations_quiet()
    # example_party_quality_report()
    # example_compare_csv_basic()
    # example_compare_csv_web_report()
    # example_compare_csv_export()
    # example_compare_csv_custom_keys()
    # example_compare_csv_ignore_columns()
    # example_compare_csv_with_tolerance()
    # example_compare_csv_quiet()
    # example_compare_csv_analyze_differences()
    # example_compare_csv_both_outputs()
    # example_compare_csv_quality_workflow()
    # example_compare_csv_publication_check()
    # example_compare_county_precinct_basic()
    # example_compare_county_precinct_web()
    # example_compare_county_precinct_tolerance()
    # example_county_precinct_batch_check()

    print("\nTo use this in your openelections-data-* repository:")
    print("1. Copy precinct_results.py to your repository")
    print("2. Import the functions you need:")
    print("   from precinct_results import generate_statewide_precinct_file")
    print("   from precinct_results import compare_precinct_names")
    print("   from precinct_results import check_party_variations")
    print("   from precinct_results import compare_csv_files")
    print("   from precinct_results import compare_county_to_precinct_totals")
    print("3. Call them with your state's parameters")
