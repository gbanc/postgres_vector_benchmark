import pandas as pd
import random

# Load the CSV file into a pandas DataFrame
df = pd.read_csv("vectors_noheader.csv", header=None)

# Generate a random sample of 10k rows
sample_size = 10000
random_indices = random.sample(range(len(df)), sample_size)

# Split the dataframe into two dataframes
df_10k = df.iloc[random_indices]
df_remaining = df.drop(random_indices)

# Write the two parts to separate CSV files
df_10k.to_csv("test_data/10k_rows.csv", index=False, header=False)
df_remaining.to_csv("test_data/remaining_rows.csv", index=False, header=False)