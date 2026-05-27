import csv

def write_results(results, file):
    fieldnames = results[0].keys()

    with open(file, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

