#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  2 14:57:02 2020

@author: mazucanti
"""


import pandas as pd
import numpy as np
from src import gera_base_retorno

base, retorno = gera_base_retorno.trata_retorno()
base.to_excel('saídas/base.xls')
retorno.to_excel('saídas/retorno.xls')
