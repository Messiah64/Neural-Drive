import pandas as pd

# Load the YES and NO data
yes_data = pd.read_csv('jyes.csv')
no_data = pd.read_csv('jno.csv')

# Add a new column to indicate the label
yes_data['Label'] = 'YES'
no_data['Label'] = 'NO'

# Combine the two DataFrame
all_data = pd.concat([yes_data, no_data], ignore_index=True)

# Create DataFrame and save to CSV
all_data.to_csv('cdata.csv', index=False)
print("Data saved to data.csv")
