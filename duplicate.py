# Function to check for duplicates in the "entity:read-group_id" column
def check_duplicates_in_column(file_path, column_index):
    seen_values = set()
    duplicate_values = set()

    with open(file_path, 'r') as tsv_file:
        next(tsv_file)  # Skip the header line
        for line_number, line in enumerate(tsv_file, 2):  # Start line numbering from 2
            values = line.strip().split('\t')
            
            if column_index < len(values):
                value = values[column_index]
                if value in seen_values:
                    duplicate_values.add(value)
                else:
                    seen_values.add(value)

    return duplicate_values

# Specify the path to your TSV file
tsv_file_path = './reads.tsv'

# Specify the column index (zero-based) of "entity:read-group_id"
column_index = 0  # The "entity:read-group_id" is in the first column

# Call the function to check for duplicates in the specified column
duplicate_values = check_duplicates_in_column(tsv_file_path, column_index)

if duplicate_values:
    print("Duplicate values found in the 'entity:read-group_id' column:")
    for value in duplicate_values:
        print(f"Duplicate value: {value}")
else:
    print("No duplicate values found in the 'entity:read-group_id' column.")
