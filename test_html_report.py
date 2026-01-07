#!/usr/bin/env python3
"""
Test the enhanced HTML comparison report functionality.
"""

import csv
import os
from precinct_results import compare_csv_files

# Create test data
def create_test_files():
    """Create sample CSV files for testing"""

    # File A - Original data
    data_a = [
        ['county', 'precinct', 'office', 'district', 'candidate', 'party', 'votes', 'early_voting'],
        ['Travis', '101', 'President', '', 'John Smith', 'DEM', '1200', '450'],
        ['Travis', '101', 'President', '', 'Jane Doe', 'REP', '1100', '400'],
        ['Travis', '102', 'President', '', 'John Smith', 'DEM', '900', '350'],
        ['Travis', '102', 'President', '', 'Jane Doe', 'REP', '850', '300'],
        ['Travis', '103', 'President', '', 'John Smith', 'DEM', '1500', '600'],
    ]

    # File B - Modified data with differences
    data_b = [
        ['county', 'precinct', 'office', 'district', 'candidate', 'party', 'votes', 'early_voting'],
        ['Travis', '101', 'President', '', 'John Smith', 'DEM', '1205', '450'],  # votes changed
        ['Travis', '101', 'President', '', 'Jane Doe', 'REP', '1100', '405'],   # early_voting changed
        ['Travis', '102', 'President', '', 'John Smith', 'DEM', '900', '350'],  # unchanged
        # Row missing: Travis 102 Jane Doe
        ['Travis', '103', 'President', '', 'John Smith', 'DEM', '1500', '600'],  # unchanged
        ['Travis', '104', 'President', '', 'John Smith', 'DEM', '800', '300'],   # extra row
    ]

    # Write File A
    with open('test_file_a.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data_a)

    # Write File B
    with open('test_file_b.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data_b)

    print("Created test files: test_file_a.csv and test_file_b.csv")


def test_html_report():
    """Test the HTML comparison report generation"""

    print("\n" + "="*70)
    print("Testing Enhanced HTML Comparison Report")
    print("="*70 + "\n")

    # Create test files
    create_test_files()

    # Test 1: Generate HTML report
    print("Test 1: Generating HTML report...")
    results = compare_csv_files(
        'test_file_a.csv',
        'test_file_b.csv',
        output_format='web',
        output_file='test_comparison_report.html',
        verbose=True
    )

    # Verify HTML file was created
    if os.path.exists('test_comparison_report.html'):
        print("\n✓ HTML report created successfully: test_comparison_report.html")

        # Check file size (should be substantial)
        file_size = os.path.getsize('test_comparison_report.html')
        print(f"  File size: {file_size:,} bytes")

        if file_size > 10000:  # Should be at least 10KB with all the styling and content
            print("  ✓ File size looks good")
        else:
            print("  ✗ Warning: File size seems small")
    else:
        print("\n✗ ERROR: HTML report was not created")
        return False

    # Test 2: Generate both CLI and web reports
    print("\nTest 2: Generating both CLI and web reports...")
    compare_csv_files(
        'test_file_a.csv',
        'test_file_b.csv',
        output_format='both',
        output_file='test_comparison_both.html',
        csv_export='test_differences.csv',
        verbose=False  # Suppress verbose output for this test
    )

    if os.path.exists('test_comparison_both.html'):
        print("✓ HTML report (both format) created successfully")

    if os.path.exists('test_differences.csv'):
        print("✓ CSV export created successfully")

    # Verify the results
    print("\n" + "="*70)
    print("Test Results Summary")
    print("="*70)
    print(f"Match Rate: {results['summary']['percentage_match']:.1f}%")
    print(f"Missing Rows: {results['summary']['missing_rows']}")
    print(f"Extra Rows: {results['summary']['extra_rows']}")
    print(f"Value Mismatches: {results['summary']['value_mismatches']}")
    print(f"Total Differences: {results['summary']['total_differences']}")

    # Expected results
    expected = {
        'missing_rows': 1,  # Travis 102 Jane Doe
        'extra_rows': 1,    # Travis 104 John Smith
        'value_mismatches': 2  # votes and early_voting changes
    }

    print("\nValidating expected results...")
    all_passed = True

    if results['summary']['missing_rows'] == expected['missing_rows']:
        print(f"✓ Missing rows: {expected['missing_rows']} (correct)")
    else:
        print(f"✗ Missing rows: expected {expected['missing_rows']}, got {results['summary']['missing_rows']}")
        all_passed = False

    if results['summary']['extra_rows'] == expected['extra_rows']:
        print(f"✓ Extra rows: {expected['extra_rows']} (correct)")
    else:
        print(f"✗ Extra rows: expected {expected['extra_rows']}, got {results['summary']['extra_rows']}")
        all_passed = False

    if results['summary']['value_mismatches'] == expected['value_mismatches']:
        print(f"✓ Value mismatches: {expected['value_mismatches']} (correct)")
    else:
        print(f"✗ Value mismatches: expected {expected['value_mismatches']}, got {results['summary']['value_mismatches']}")
        all_passed = False

    print("\n" + "="*70)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("\nGenerated files:")
        print("  - test_comparison_report.html (open in browser to view)")
        print("  - test_comparison_both.html")
        print("  - test_differences.csv")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*70)

    return all_passed


if __name__ == '__main__':
    test_html_report()
