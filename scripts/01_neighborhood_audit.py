import pandas as pd
from pathlib import Path

# 1. Get the path of the current file (__file__)
# 2. Get its parent directory (.parent)
# 3. If your script is in a subfolder like /scripts, go up one more (.parent)
# 4. Then navigate to the data
base_path = Path(__file__).parent.parent
data_path = base_path / "data" / "raw" / "locations.csv"

# Now read the file using the dynamic path
locations = pd.read_csv(data_path)
print(f"Successfully loaded {len(locations)} rows from {data_path.name}")