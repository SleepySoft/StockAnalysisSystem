import pandas as pd
from datetime import datetime


df = pd.DataFrame({
    'time': [datetime(2020, 1, 1, 12, 30, 0),
             datetime(2020, 1, 1, 1, 45, 0),
             datetime(2020, 1, 3, 15, 30, 0),
             datetime(2020, 1, 4, 12, 13, 0),
             datetime(2020, 1, 4, 20, 54, 0),
             datetime(2020, 1, 5, 8, 30, 0),
             ],
    'A': ['A1', 'A2', 'A3', 'A4', 'A5', 'A6'],
    'B': ['B1', 'B2', 'B3', 'B4', 'B5', 'B6'],
})

print(df)

df['normalised_time'] = df['time'].dt.normalize()
df_grouped = df.groupby('normalised_time')

for group, df in df_grouped:
    print(group)
    print(df)





