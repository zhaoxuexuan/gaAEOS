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

    instName = 'instance_2_9_170'

    exportCSV = False

    gaROADEF2003(
        instName=instName,
        indSize = 0,
        popSize =100,
        cxPb = 0.85,
        mutPb = 0.5,
        NGen = 100,
        Mul_Flag = True,
        exportCSV=exportCSV
        
    )


if __name__ == '__main__':
    main()
