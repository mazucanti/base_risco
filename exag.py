import pandas as pd


retorno = pd.read_excel('saídas/retorno.xls', index_col=0)
retorno.to_excel("ret_ori.xls")

for col, val in retorno.iteritems():
        if col == "Unnamed: 0": continue
        desv = val.std()
        media = val.mean()
        lim_pos = media + 5 * desv
        lim_neg = media - 5 * desv
        print(lim_neg, lim_pos)
        retorno[val > lim_pos] = 0 
        retorno[val < lim_neg] = 0
retorno.to_excel('ret_nov.xls')