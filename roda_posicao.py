#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  2 14:57:02 2020

@author: mazucanti
"""


import pandas as pd
from calendar import monthrange
from datetime import date
from numpy import arange
from src import gera_base_retorno


def gera_sim(prod, retorno):
    hoje = date.today()
    dias_mes = monthrange(prod[2].year, prod[2].month)
    maturidade = prod[2].month - hoje.month + (prod[2].year - hoje.year) * 12
    sim = (retorno[maturidade]) * prod[1] * dias_mes[1] * 24 * prod[0]
    sim.sort_values(inplace=True)
    tam = sim.index.size
    sim.index = arange(tam)
    return sim


def calc_var5(sim):
    pos_5 = round(sim.index.size * 0.05)
    var5 = sim[pos_5]
    var5 = round(var5,2)
    return var5


def main():
    base, retorno = gera_base_retorno.trata_retorno()
    base.to_excel('saídas/base.xls')
    retorno.to_excel('saídas/retorno.xls')
    

    # vol = float(input("Digite o volume comprado (em MWmed): "))
    # pre = float(input("Digite o preço do MWmed (em R$): "))
    # mes = int(input("Digite o mês do produto: "))
    # ano = int(input("Digite o ano do produto: "))

    vol = 1
    pre = 100
    mes = 5
    ano = 2020

    prod = (vol, pre, date(ano,mes,1))
    sim = gera_sim(prod, retorno)
    sim.to_excel('debug.xls')
    var5 = calc_var5(sim)
    print(var5)
    

main()