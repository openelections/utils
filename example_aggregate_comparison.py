"""
Example: Using aggregate_votes to compare files by office/party
"""
from precinct_results import compare_csv_files

# Example 1: Compare vote totals by precinct/office/party (ignoring candidate)
results = compare_csv_files(
    '/Users/dwillis/code/openelections-data-pa/20241105__pa__general__potter__precinct.csv',
    '/Users/dwillis/code/openelections-data-pa/2024/counties/20241105__pa__general__potter__precinct.csv',
    exclude_from_key=['candidate'],  # Don't use candidate as part of the row identifier
    aggregate_votes=True,             # Sum votes across all candidates
    output_format='web',
    output_file='potter_aggregated_comparison.html',
    verbose=True
)

print(f"\n{'=' * 70}")
print("AGGREGATED COMPARISON RESULTS")
print(f"{'=' * 70}")
print(f"Match rate: {results['summary']['percentage_match']:.1f}%")
print(f"Identical aggregated rows: {results['summary']['identical_rows']}")
print(f"Value mismatches: {results['summary']['value_mismatches']}")
print(f"\nThis comparison aggregates all candidates within each")
print(f"precinct/office/party combination and compares the totals.")
