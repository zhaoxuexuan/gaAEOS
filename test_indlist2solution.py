#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 12 19:37:02 2018

@author: zhaoxx17
"""


from json import load
import random
from deap import tools
import torch
from torch.utils.data import Dataset
from torch.autograd import Variable
from tqdm import trange, tqdm
import os
import sys
import fnmatch
from gavrptw.core_ROADEF2003 import  shot2strip , transTime

def indlist2solution(indlist, instance):
    # indlist contains a list of individual
    # individual is a list containing a sequence of shotID selected
    # solution is a valid list, cut from individual

    solulist =[]
    for individual in indlist:
        solution =[]        
        k=individual[0]
        solution=[k]
        t_current = instance['Tmin_vector'][k-1]
        for k_next in individual[1:]:
            # cut individual : 1 shot for 1strip
            if k_next % 2 ==1:
                k_pair = k_next +1
            else:
                k_pair = k_next-1
            if k_pair in solution:
                break
            # cut individual : empty visibility window
            if instance['Tmin_vector'][k_next-1]> instance['Tmax_vector'][k_next-1]:
                break
            # cut individual : time 
            transitionTime = transTime(instance['distance_matrix'][k_next-1][k-1])
            durationTime = instance[shot2strip(k)]['strip-acquisition-duration']
            if t_current+transitionTime+durationTime <= instance['Tmax_vector'][k_next-1]:
                solution.append(k_next)
                t_current =max(instance['Tmin_vector'][k_next-1],t_current+transitionTime+durationTime)
                k = k_next
            else:
                break
        # cut individual : stereo violation
            #**************HERE NEED TO CHECK**************
        indicator =[]
        solution_indicator=[]
        for k in individual:
            
            if  instance[shot2strip(k)]['twin-strip-index'] != 0 :
                twin_strip = int(instance[shot2strip(k)]['twin-strip-ID'][6:])
                if k%2 == 0:
                    k_twin = 2*twin_strip
                else:
                    k_twin = 2*twin_strip -1
                if k_twin not in indicator:
                    indicator.append(k)
                else:
                    indicator.remove(k_twin)
            if indicator == []:
                solution_indicator.append(1)
            else:
                solution_indicator.append(0)
        
        if 1 not in solution_indicator:
            solution =[]
            return solution
        else:
            #print(solution_indicator)
            solution_indicator.reverse()
            solution = solution[:len(solution_indicator[solution_indicator.index(1):])]
        solulist.append(solution)
    indlen = len(indlist[0])
    new_solulist = list(map(lambda l:l + [0]*(indlen - len(l)), solulist))   
#    print('ind2solution:',solution)  
    return new_solulist

def main():


    with open('data/json_ROADEF2003/instance_2_9_170.json') as f:
        instance = load(f)
    indlist =[]
    ind1=[7, 10, 21, 20, 40, 16, 3, 12, 49, 19, 27, 15, 8, 14, 28, 30, 39, 50, 47, 24, 23, 29, 2, 18, 42, 34, 41, 38, 45, 36, 35, 11, 46, 5, 6, 48, 26, 1, 17, 43, 44, 33, 4, 13, 25, 37, 9, 31, 22, 32]
    ind2=[10, 3, 12, 7, 42, 34, 38, 49, 19, 27, 8, 41, 45, 21, 24, 20, 40, 14, 28, 30, 39, 50, 2, 47, 23, 36, 22, 46, 35, 33, 16, 15, 29, 18, 4, 5, 11, 6, 17, 48, 26, 1, 13, 44, 32, 25, 43, 37, 31, 9]
    indlist.append(ind1)
    indlist.append(ind2)
    print(indlist2solution(indlist,instance))

if __name__ == '__main__':
    main()
