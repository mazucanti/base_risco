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


# def exporta_produtos():
#     b, m, t, s, a, o = separa_produtos()
#     produtos = [b, m, t, s, a, o]
#     diretorios = ["base.csv", "mensal.csv", "trimestral.csv", "semestral.csv", "anual.csv", "outros.csv"]
#     local = Path('saídas')
#     for i, produto in enumerate(produtos):
#         local_prod = local / diretorios[i]
#         produto.to_csv(local_prod)


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
            produtos[i] = dt.datetime.strptime(produtos[i][3], "%b/%y").date()
        for j in range(len(datas)):
            datas[j] = str(datas[j])
            datas[j] = dt.datetime.strptime(datas[j], "%Y-%m-%d").date()
        for i in range(len(produtos)):
            for j in range(len(datas)):
                maturidade = produtos[i].month - datas[j].month + (12 *( produtos[i].year - datas[j].year))
                maturidade =  maturidade if maturidade >= 0 else "dump"
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
                    maturidade = produtos[i][k].month - datas[j].month + (12 *( produtos[i][k].year - datas[j].year))
                    if maturidade > i+k or np.isnan(base.loc[datas[j], maturidade]):
                        maturidade =  maturidade if maturidade >= 0 else "dump"
                        base.loc[datas[j], maturidade] = valores.iloc[j,i]
                    else:
                        continue
    return base

def organiza_maturidade():
    maturidades = []
    valores_pond = calcula_ponderada()
    datas = valores_pond[1].index.tolist()
    produtos = valores_pond[1].columns.tolist()
    for i in range(len(produtos)):
        produtos[i] = produtos[i].split()
        produtos[i] = dt.datetime.strptime(produtos[i][3], "%b/%y").date()
    for j in range(len(datas)):
        datas[j] = str(datas[j])
        datas[j] = dt.datetime.strptime(datas[j], "%Y-%m-%d").date()
    base = pd.DataFrame(index = datas, columns = maturidades)
    base = adiciona_produto(valores_pond[1], base, "MEN")
    base = adiciona_produto(valores_pond[2], base, "TRI")
    base.drop(['dump'], axis=1, inplace=True)
    base = base.T
    base.sort_index(inplace=True)
    base = base.T
    return base
