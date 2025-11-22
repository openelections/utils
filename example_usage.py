"""
Example usage of the precinct_results module for OpenElections data repositories.

This shows how to import and use the statewide precinct results generator
in various OpenElections state repositories (openelections-data-tx, etc.)
"""

from precinct_results import generate_statewide_precinct_file, generate_vote_columns_report


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

    print("\nTo use this in your openelections-data-* repository:")
    print("1. Copy precinct_results.py to your repository")
    print("2. Import the function: from precinct_results import generate_statewide_precinct_file")
    print("3. Call it with your state's parameters")
