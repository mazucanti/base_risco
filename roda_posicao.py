#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  2 14:57:02 2020

@author: mazucanti
"""


import pandas as pd
from datetime import date
from numpy import arange
import locale
from pathlib import Path
from src import gera_base_retorno

locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")

def trata_port():
    entrada = Path("entradas/portfolio.xls")
    port = pd.read_excel(entrada,index_col=[0,1])
    port.fillna(0, inplace=True)

    port.loc[("Venda","Volume"),:] *= port.columns.days_in_month * 24
    port.loc[("Compra","Volume"),:] *= port.columns.days_in_month * 24

    total_port = (port.loc[("Venda","Preço"),:] * port.loc[("Venda","Volume"),:]).sum()
    total_port -= (port.loc[("Compra","Preço"),:] * port.loc[("Compra","Volume"),:]).sum()
    total_port = round(total_port,2)

    return total_port


def gera_sim(posi, retorno):
    
    hoje = date.today()
    maturidade = posi.columns.month - hoje.month + (posi.columns.year - hoje.year) * 12
    dias_mes = posi.columns.days_in_month
    posi.columns = maturidade
    dias_mes = dias_mes.to_series(index=maturidade)
    posi.drop(maturidade[maturidade < 0], axis=1, inplace=True)
    maturidade = posi.columns
    dias_mes = dias_mes.drop(maturidade[maturidade < 0])
    sim = (retorno[maturidade]) * posi.loc["Preço",:]
    sim *= posi.loc["Volume",:]
    sim *= dias_mes 
    sim *= 24
    sim = sim.sum(axis=1)
    sim.sort_values(inplace=True)
    tam = sim.index.size
    sim.index = arange(tam)
    vol = (posi.loc["Volume"]*dias_mes).sum() * 24
    return sim, vol


def calc_casos(sim):
    pos_5 = round(sim.index.size * 0.05)
    var5 = sim[pos_5]
    var5 = round(var5,2)
    cvar5 = round(sim[0:pos_5].mean(),2)
    pior = round(sim[0],2)
    pos_50 = sim.index.size // 2
    var_50 = round(sim[pos_50],2)
    return [var_50, var5, cvar5, pior]


def main():
    loc_ret = Path("saídas/retorno.xls")
    if not loc_ret.is_file():
        gera_base_retorno.exporta()
    retorno = pd.read_excel(loc_ret)
    
    entrada = Path("entradas/posição.xls")
    posi = pd.read_excel(entrada, index_col=0)

    sim, vol = gera_sim(posi, retorno)
    dados_var = calc_casos(sim)
    total_port = trata_port()

    final = pd.DataFrame(index=["Base", "VaR 5%", "CVaR", "Pior Caso"],columns=["Portfólio", "Variação Diária", "Variação Semanal", "R$/MWh"])
    final.iloc[0,0] = total_port
    final["Variação Diária"] = dados_var
    final["Variação Semanal"] = round(final["Variação Diária"] * (5**0.5), 2)
    final.iloc[1:4,0] = total_port + final.iloc[1:4,1]
    final["R$/MWh"] = final["Variação Semanal"] / (vol)

    saida = Path("saídas/risco.xls")
    final.to_excel(saida)


    
main()