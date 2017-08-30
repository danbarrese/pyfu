"""
Print combinations of elements from multiple buckets.
"""

import argparse

__author__ = 'Dan Barrese'
__pythonver__ = '3.5'

parser = argparse.ArgumentParser(description='Print combinations of elements chosen from buckets of varying sizes.')
parser.add_argument('--buckets', '-b', type=str, nargs=1,
                    dest='buckets', default=[None],
                    help='Buckets of elements separated by spaces.  Buckets separated by delimiter (set with --bucket-delimiter).  Example: "a b; c; d e f"')
parser.add_argument('--bucket-delimiter', '-i', type=str, nargs=1,
                    dest='bucket_delim', default=[';'],
                    help='String that separates buckets of input elements.  Defaults to ;.')
parser.add_argument('--output-delimiter', '-o', type=str, nargs=1,
                    dest='output_delim', default=['_'],
                    help='String to put between the options chosen from each bucket.  Defaults to _.')
parser.add_argument('-q', type=str, nargs=1,
                    dest='quote', default=[''],
                    help='Quote results with the given string.  Defaults to "".')
args = parser.parse_args()

output_delim = args.output_delim[0]
bucket_delim = args.bucket_delim[0]
quote = args.quote[0]


def combos(list_of_lists):
    combo_count = 1
    for lizst in list_of_lists:
        combo_count *= len(lizst)
    combinations = []
    for i in range(0, combo_count):
        combination = []
        j = 1
        for lizst in list_of_lists:
            idx = int(i / j % len(lizst))
            combination.append(lizst[idx])
            j *= len(lizst)
        combinations.append(combination)
    return combinations


# Split the input into buckets.
buckets = [s.strip(' ').split(' ') for s in args.buckets[0].split(bucket_delim) if s]

# Get the results.
results = combos(buckets)

# If we have a small number of results, sort them.
if len(results) < 10000:
    results = sorted(results)

# Print results.
for combo in results:
    print('{}{}{}'.format(quote, output_delim.join(combo), quote))
