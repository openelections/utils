"""
Example usage of the precinct_results module for OpenElections data repositories.

This shows how to import and use the statewide precinct results generator
in various OpenElections state repositories (openelections-data-tx, etc.)
"""

from precinct_results import (
    generate_statewide_precinct_file,
    generate_vote_columns_report,
    compare_precinct_names,
    collect_precinct_names
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

    print("\nTo use this in your openelections-data-* repository:")
    print("1. Copy precinct_results.py to your repository")
    print("2. Import the functions you need:")
    print("   from precinct_results import generate_statewide_precinct_file")
    print("   from precinct_results import compare_precinct_names")
    print("3. Call them with your state's parameters")
