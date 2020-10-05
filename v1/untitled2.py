import pyarrow as pa
import numpy as np
import pandas as pd

df = pd.DataFrame({'one': [-1, np.nan, 2.5],
                   'two': ['foo', 'bar', 'baz'],
                   'three': [True, False, True]},
                   index=list('abc'))





table = pa.Table.from_pandas(df)

print(table)

import pyarrow.parquet as pq
pq.write_table(table, r'C:\Users\www\Desktop\dynamics\example.parquet')


table2 = pq.read_table('example.parquet', columns=['one'])


t2=table2.to_pandas()

print(t2)