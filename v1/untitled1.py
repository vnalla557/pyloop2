import numpy as np
import pandas as pd

s = pd.Series([1, 3, 5, np.nan, 6, 8])



p = pd.DataFrame(

    {
     "a":[1,2,3],
     "b":[4,5,6],
     },
    
    )


q = pd.DataFrame(

    {
     "a":[7,8,9,22],
     "b":[10,11,12,23],
     "c":[13,14,15,24],
     },
    
    )


print( pd.concat([p,q],axis=0).sort_index()   )