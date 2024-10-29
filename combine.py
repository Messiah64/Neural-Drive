import pandas as pd

# Load the YES and NO data
yes_data = pd.read_csv('nyes.csv')
no_data = pd.read_csv('nno.csv')

# Add a new column to indicate the label
yes_data['Label'] = 'YES'
no_data['Label'] = 'NO'

# Combine the two DataFrame
all_data = pd.concat([yes_data, no_data], ignore_index=True)

# Create DataFrame and save to CSV
all_data.to_csv('ndata.csv', index=False)
print("Data saved to ndata.csv")
