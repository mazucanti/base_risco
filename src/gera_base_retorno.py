#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  6 17:39:36 2020

@author: mazucanti
"""

import pandas as pd
from pathlib import Path
import numpy as np
import datetime as dt
import locale
locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")


def importa_bases_negocios():
    bases_negocios = []
    diretorios = Path('entradas/').glob('**/*')
    arquivos = [diretorio for diretorio in diretorios if diretorio.suffix == '.xlsx']
    for arquivo in arquivos:
        df = pd.read_excel(arquivo)
        bases_negocios.append(df)
    return bases_negocios


def separa_produtos():
    bases = importa_bases_negocios()
    men = []
    tri = []
    sem = []
    anu = []
    out = []
    for i, base in enumerate(bases):
        bases[i] = base[base['Produto'].str.contains('(?=^SE CON.*)(?=.*Preço Fixo$)')]
        out.append(base[base['Produto'].str.contains('(?=^SE CON.*)(?!.*MEN.*|.*TRI.*|.*SEM.*|.*ANU.*)(?=.*Preço Fixo$)')])
        men.append(base[base['Produto'].str.contains('(?=^SE CON.*)(?=.*MEN.*)(?=.*Preço Fixo$)')])
        tri.append(base[base['Produto'].str.contains('(?=^SE CON.*)(?=.*TRI.*)(?=.*Preço Fixo$)')])
        sem.append(base[base['Produto'].str.contains('(?=^SE CON.*)(?=.*SEM.*)(?=.*Preço Fixo$)')])
        anu.append(base[base['Produto'].str.contains('(?=^SE CON.*)(?=.*ANU.*)(?=.*Preço Fixo$)')])
    bases = pd.concat(bases, axis=0, ignore_index=True)
    out = pd.concat(out, axis=0, ignore_index=True)
    men = pd.concat(men, axis=0, ignore_index=True)
    tri = pd.concat(tri, axis=0, ignore_index=True)
    sem = pd.concat(sem, axis=0, ignore_index=True)
    anu = pd.concat(anu, axis=0, ignore_index=True)
    return [bases, men, tri, sem, anu, out]


def calcula_ponderada():
    norm_tab_vol = []
    norm_tab_pon = []
    produtos = separa_produtos()
    for i in range(len(produtos)):
        indices = produtos[i][produtos[i]['Cancelado'] == 'Sim'].index
        produtos[i].drop(indices, axis=0, inplace=True)
        produtos[i]['Data/Hora'] = pd.to_datetime(produtos[i]["Data/Hora"], format="%d/%m/%Y %H:%M:%S")
        produtos[i]["Data/Hora"] = produtos[i]["Data/Hora"].dt.strftime("%Y-%m-%d")
        ponderada = (produtos[i]['MWh'] * produtos[i]['Preço (R$)'])
        ponderada.name = "Ponderada"
        produtos[i] = pd.concat([produtos[i], ponderada], axis=1)
        norm_tab_pon.append(pd.pivot_table(produtos[i], values = ['Ponderada'], index=['Data/Hora'], columns=['Produto']))
        norm_tab_vol.append(pd.pivot_table(produtos[i], values = ['MWh'], index=['Data/Hora'], columns=['Produto']))
        norm_tab_pon[i] = norm_tab_pon[i].groupby(level=0).sum()
        norm_tab_pon[i] = norm_tab_pon[i].T.reset_index(0, drop=True)
        norm_tab_pon[i] = norm_tab_pon[i].T
        norm_tab_vol[i] = norm_tab_vol[i].groupby(level=0).sum()
        norm_tab_vol[i] = norm_tab_vol[i].T.reset_index(0, drop=True)
        norm_tab_vol[i] = norm_tab_vol[i].T
        produtos[i].drop(["Preço (R$)", "Tipo Contrato", "MWm", "Cancelado"], axis=1, inplace=True)
        norm_tab_pon[i] = norm_tab_pon[i]/norm_tab_vol[i]
    return norm_tab_pon


def adiciona_produto(valores, base, tipo):
    datas = valores.index.tolist()
    produtos = valores.columns.tolist()
    
    if tipo == "MEN":
        for i in range(len(produtos)):
            produtos[i] = produtos[i].split()
            if produtos[i][3][len(produtos[i][3])-1] == '-': produtos[i][3] = produtos[i][3][:-1]
            produtos[i] = dt.datetime.strptime(produtos[i][3], "%b/%y").date()
        for j in range(len(datas)):
            datas[j] = str(datas[j])
            datas[j] = dt.datetime.strptime(datas[j], "%Y-%m-%d").date()
        for i in range(len(produtos)):
            for j in range(len(datas)):
                maturidade = produtos[i].month - datas[j].month + (12 *( produtos[i].year - datas[j].year))
                maturidade =  maturidade if maturidade >= 0 and maturidade <= 24 else "dump"
                if maturidade == "dump": continue
                base.loc[datas[j], maturidade] = valores.iloc[j,i]

    elif tipo == "TRI":
        for i in range(len(produtos)):
            produtos[i] = produtos[i].split()
            produtos[i] = dt.datetime.strptime(produtos[i][4], "%b/%y").date()
            produtos[i] = (produtos[i] - dt.timedelta(weeks=8),
                           produtos[i] - dt.timedelta(weeks=4),
                           produtos[i])
        for j in range(len(datas)):
            datas[j] = str(datas[j])
            datas[j] = dt.datetime.strptime(datas[j], "%Y-%m-%d").date()
        for i in range(len(produtos)):
            for j in range(len(datas)):
                for k in range(len(produtos[i])):
                    maior_maturidade = base.columns.tolist()
                    maior_maturidade = maior_maturidade[len(maior_maturidade)-1]
                    maturidade = produtos[i][k].month - datas[j].month + (12 *(produtos[i][k].year - datas[j].year))
                    maturidade =  maturidade if maturidade >= 0 and maturidade <= 24 else "dump"
                    if maturidade == "dump": continue
                    if maturidade > maior_maturidade or np.isnan(base.loc[datas[j], maturidade]):
                        base.loc[datas[j], maturidade] = valores.iloc[j,i]
                    else:
                        continue
        
    elif tipo == "SEM":
        for i in range(len(produtos)):
            produtos[i] = produtos[i].split()
            produtos[i] = dt.datetime.strptime(produtos[i][4], "%b/%y").date()
            produtos[i] = ((produtos[i] - dt.timedelta(weeks=20)).replace(day=1), 
                           (produtos[i] - dt.timedelta(weeks=16)).replace(day=1),
                           (produtos[i] - dt.timedelta(weeks=12)).replace(day=1), 
                           (produtos[i] - dt.timedelta(weeks=8)).replace(day=1),
                           (produtos[i] - dt.timedelta(weeks=4)).replace(day=1),
                           produtos[i])
        for j in range(len(datas)):
            datas[j] = str(datas[j])
            datas[j] = dt.datetime.strptime(datas[j], "%Y-%m-%d").date()
        for i in range(len(produtos)):
            for j in range(len(datas)):
                for k in range(len(produtos[i])):
                    maior_maturidade = base.columns.tolist()
                    maior_maturidade = maior_maturidade[len(maior_maturidade)-1]
                    maturidade = produtos[i][k].month - datas[j].month + (12 * (produtos[i][k].year - datas[j].year))
                    maturidade =  maturidade if maturidade >= 0 and maturidade <= 24 else "dump"
                    if maturidade == "dump": continue
                    if maturidade > maior_maturidade or np.isnan(base.loc[datas[j], maturidade]):
                        base.loc[datas[j], maturidade] = valores.iloc[j,i]
                    else:
                        continue                
    
    elif tipo == "ANU":
        for i in range(len(produtos)):
            produtos[i] = produtos[i].split()
            data = dt.datetime.strptime(produtos[i][4], "%b/%y").date()
            produtos[i] = []
            for k in range(1,13):
                data_str = "%d-%d-01" % (data.year, k)
                produtos[i].append(dt.datetime.strptime(data_str, "%Y-%m-%d").date())
        for j in range(len(datas)):
            datas[j] = str(datas[j])
            datas[j] = dt.datetime.strptime(datas[j], "%Y-%m-%d").date()
        for i in range(len(produtos)):
            for j in range(len(datas)):
                for k in range(len(produtos[i])):
                    maior_maturidade = base.columns.tolist()
                    maior_maturidade = maior_maturidade[len(maior_maturidade)-1]
                    maturidade = produtos[i][k].month - datas[j].month + (12 * (produtos[i][k].year - datas[j].year))
                    maturidade =  maturidade if maturidade >= 0 and maturidade <= 24 else "dump"
                    if maturidade == "dump": continue
                    if maturidade > maior_maturidade or np.isnan(base.loc[datas[j], maturidade]):
                        base.loc[datas[j], maturidade] = valores.iloc[j,i]
                    else:
                        continue                
    
    base = base.T
    base.sort_index(inplace=True)
    base = base.T
    return base


def organiza_maturidade():
    maturidades = []
    valores_pond = calcula_ponderada()
    datas = valores_pond[0].index.tolist()
    for i in range(len(datas)):
        datas[i] = str(datas[i])
        datas[i] = dt.datetime.strptime(datas[i], "%Y-%m-%d").date()
    base = pd.DataFrame(index = datas, columns = maturidades)
    base = adiciona_produto(valores_pond[1], base, "MEN")
    base = adiciona_produto(valores_pond[2], base, "TRI")
    base = adiciona_produto(valores_pond[3], base, "SEM")
    base = adiciona_produto(valores_pond[4], base, "ANU")
    return base


def trata_retorno():
    base = organiza_maturidade()
    datas = base.index.tolist()
    retorno = pd.DataFrame()
    for k in range(len(datas)):
        datas[k] = str(datas[k])
        datas[k] = dt.datetime.strptime(datas[k], "%Y-%m-%d").date()
    for i in range(25):
        for j in range(len(datas)):
            if np.isnan(base.loc[datas[j], i]) and j > 0:
                base.loc[datas[j], i] = base.loc[datas[j-1],i]
                if datas[j].month != datas[j-1].month: 
                    base.loc[datas[j],i] = 0
            if datas[j].month != datas[j-1].month: retorno.loc[datas[j],i] = 0
            elif base.loc[datas[j-1],i] != 0: retorno.loc[datas[j],i] = (base.loc[datas[j], i] / float(base.loc[datas[j-1],i])) - 1.0
    datas = retorno.index.tolist()
    for k in range(len(datas)):
        if retorno.loc[datas[k],:].sum() == 0: retorno.drop(datas[k], axis=0, inplace=True)
    retorno.fillna(0, inplace=True)
    return base, retorno