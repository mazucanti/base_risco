import pandas as pd
import numpy as np


retorno = pd.read_excel('saídas/retorno.xls', index_col=0)

curvas = []

for col, val in retorno.iteritems():
    std_dev = val.std()
    med = val.mean()
    curvas.append(np.random.normal(med, std_dev, 1000))
    print(curvas[col])

