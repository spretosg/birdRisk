import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Generate a random DataFrame for the heatmap
np.random.seed(42)
data = np.random.rand(10, 10) * 100  # 10x10 matrix with random values between 0-100
df = pd.DataFrame(data)

# Create a heatmap using seaborn
plt.figure(figsize=(10, 8))
heatmap = sns.heatmap(df, annot=True, cmap="YlGnBu")

# Identify the highest value in the DataFrame
max_value = df.values.max()
max_index = np.unravel_index(np.argmax(df.values), df.shape)  # Get the row and column index of the max value

# Get the x and y coordinates for the highest value
max_row, max_col = max_index

# Draw lines to the x and y axes from the max value
plt.axvline(x=max_col + 0.5, color='red', linestyle='--')  # Vertical line to x-axis
plt.axhline(y=max_row + 0.5, color='red', linestyle='--')  # Horizontal line to y-axis

# Highlight the cell with the maximum value
heatmap.add_patch(plt.Rectangle((max_col, max_row), 1, 1, fill=False, edgecolor='red', lw=3))

# Display the plot
plt.title(f"Heatmap with Highest Value ({max_value:.2f}) Highlighted")
plt.show()
