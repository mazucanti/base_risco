#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  6 17:39:36 2020

@author: mazucanti
"""

import pandas as pd
from pathlib import Path


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
    return bases, men, tri, sem, anu, out


def exporta_produtos():
    b, m, t, s, a, o = separa_produtos()
    produtos = [b, m, t, s, a, o]
    diretorios = ["base.csv", "mensal.csv", "trimestral.csv", "semestral.csv", "anual.csv", "outros.csv"]
    local = Path('saídas')
    for i, produto in enumerate(produtos):
        local_prod = local / diretorios[i]
        produto.to_csv(local_prod)

exporta_produtos()