#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 23 16:40:18 2018

@author: zhaoxx17
"""

# -*- coding: utf-8 -*-
# sample_R101.py

import random
from gavrptw.core_ROADEF2003 import gaROADEF2003


def main():
    random.seed(16)

    instName = 'instance_25'

    exportCSV = False

    gaROADEF2003(
        instName=instName,
        iniMethod= 'RS', #['RS', 'RNDS', 'HRHS', 'FS']
        indSize = 0,
        popSize =100,
        cxPb = 0.85,
        mutPb = 0.5,
        NGen = 5,
        Mul_Flag = False,
        simple_flag = True,
        strip_flag = True,
        exportCSV=exportCSV
        
    )


if __name__ == '__main__':
    main()
