#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 23 16:35:41 2018

@author: zhaoxx17
"""
# -*- coding: utf-8 -*-

import os
import random
import math
import fnmatch
from json import load
from csv import DictWriter
from deap import base, creator, tools
from . import BASE_DIR
from .utils import makeDirsForFile, exist

def transTime(distance):    
    Hs =633000.0 # satellite altitude in meters
    Vr = 0.05 # the maximum speed of rotation in rad/s
    Dmin = 2.5 # incompressible transition time in seconds
    return(2*math.atan(distance/(2*Hs))/Vr + Dmin)
    
def shot2strip(k):
    return('strip_%d' % int((k+1)/2))
    
def readsolution2striplist(textFile,instance):
    '''
    strip_flag = True
    '''
    striplist =[]
    with open(textFile) as f:
        for lineNum, line in enumerate(f, start=1):
                if lineNum >= 3:
                    values = line.strip().split()
                    for stripID in fnmatch.filter(instance.keys(),'strip_*'):
                        if instance[stripID]['strip-index']==int(values[0]):
                            striplist.append(int(stripID[6:]))
                        
    print('read solution file: ',textFile) 
    print('get solution: \n',striplist)                           
    return(striplist)
    
def verifySolution(solution,instance):
    #solution is a list containing a sequence of shotID selected
    if solution==[]:return(True)
    k=solution[0]
    t_current = instance['Tmin_vector'][k-1]
    for k_next in solution[1:]:
        transitionTime =transTime(instance['distance_matrix'][k_next-1][k-1])
        durationTime = instance[shot2strip(k)]['strip-acquisition-duration']
        if t_current+transitionTime+durationTime > instance['Tmax_vector'][k_next-1]:
            print('***Error in verifySolution:  time')
            print('k:',k)
            print('t_current:',t_current)
            print('transitionTime:', transitionTime)
            print('durationTime:',durationTime)
            print('Tmax for k_next:',instance['Tmax_vector'][k_next-1])
        k = k_next
        t_current =max(instance['Tmin_vector'][k-1],t_current+transitionTime+durationTime)
    durationTime = instance[shot2strip(k)]['strip-acquisition-duration']
    t_current = t_current + durationTime
    print('Final time:',t_current)  
    
    for k in solution:
        if k%2 ==1:
            k_pair = k+1
        else:
            k_pair = k-1
        if k_pair in solution:
            print('***Error in verifySolution: 2 shot for 1 strip')
            print(k)
                    
        if instance[shot2strip(k)]['twin-strip-index'] != 0:
            twinStripID = int(instance[shot2strip(k)]['twin-strip-ID'][6:])
            if k%2 ==1:
                if not (2*twinStripID-1) in solution:
                    print('***Error in verifySoluiton: stereo violation')
                    print(k)  
            else:
                if not  (2*twinStripID) in solution:
                    print('***Error in verifySoluiton: stereo violation')
                    print(k)
        
        if instance['Tmin_vector'][k-1]> instance['Tmax_vector'][k-1]:
            print('***Error in verifySolution: empty visibility window')
            print(solution,k)
    return(True)
            
def ind2solution(individual,instance, simple_flag = False, strip_flag = False,track_flag=False,time_flag =False):
    # individual is a list containing a sequence of shotID selected
    # solution is a valid list, cut from individual
    if track_flag:
        trackCapacity = 2 #instance['track-number']
        solution =[]
        time =[]
        # Initialize a sub-solution
        subSolution = []
        subTime =[]
        for k in individual:
            # cut individual : empty visibility window
            if instance['Tmin0_vector'][k-1]>instance['Tmax0_vector'][k-1]:
                break
            # cut individual : transition time
            if len(subSolution)==0:           
                subSolution.append(k)
                t_current = instance['Tmin0_vector'][k-1]
                subTime.append(t_current)
                k_last = k
            else:           
                transitionTime = transTime(instance['distance10_matrix'][k-1][k_last-1])
                durationTime = instance['strip_%s' % k_last]['strip-acquisition-duration']
                if t_current+transitionTime+durationTime <= instance['Tmax0_vector'][k-1]:
                    subSolution.append(k)
                    t_current =max(instance['Tmin0_vector'][k-1],t_current+transitionTime+durationTime)
                    subTime.append(t_current)
                    k_last = k
                else:
                    solution.append(subSolution)
                    time.append(subTime)
                    if len(solution)==trackCapacity:
                        subSolution =[]
                        subTime =[]
                        break
                    subSolution=[k]
                    t_current = instance['Tmin0_vector'][k-1]
                    subTime=[t_current]
                    k_last = k
        if len(subSolution)!=0:
            solution.append(subSolution)
            time.append(subTime)
    elif strip_flag:
        strips = individual
        solution =[] 
        time =[]
        k=strips[0]
        solution=[k]
        t_current = instance['Tmin0_vector'][k-1]
        time.append(t_current)
        for k_next in strips[1:]:
            # cut individual : empty visibility window
            if instance['Tmin0_vector'][k_next-1]> instance['Tmax0_vector'][k_next-1]:
                break
            # cut individual : transition time 
            transitionTime = transTime(instance['distance10_matrix'][k_next-1][k-1])
            durationTime = instance['strip_%s' % k]['strip-acquisition-duration']
            if t_current+transitionTime+durationTime <= instance['Tmax0_vector'][k_next-1]:
                solution.append(k_next)
                t_current =max(instance['Tmin0_vector'][k_next-1],t_current+transitionTime+durationTime)
                k = k_next
                time.append(t_current)
            else:
                break

    elif simple_flag:
        solution =[]        
        k=individual[0]
        solution=[k]
        t_current = instance['Tmin_vector'][k-1]
        for k_next in individual[1:]:
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
    else:
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
        for k in solution:
            
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
        else:
            #print(solution_indicator)
            solution_indicator.reverse()
            solution = solution[:len(solution_indicator[solution_indicator.index(1):])]
    if time_flag:
        return solution, time
    else:
        return solution   


def evalMulROADEF2003(individual, instance, simple_flag = False, strip_flag = False):

    solution = ind2solution(individual,instance, simple_flag = simple_flag, strip_flag = strip_flag)
    (gain,) = evalROADEF2003(individual, instance, simple_flag = simple_flag, strip_flag = strip_flag)

    time_off_set =[]
    if strip_flag:
        if solution != []:
            k = solution[0]
            t_current = instance['Tmin0_vector'][k-1]
            best_time = (instance['Tmin0_vector'][k-1]+instance['Tmax0_vector'][k-1])/2.0
            time_off_set.append(t_current-best_time)
        for k_next in solution[1:]:
            transitionTime =transTime(instance['distance10_matrix'][k_next-1][k-1])
            durationTime = instance['strip_%s' % k]['strip-acquisition-duration']
            k = k_next
            t_current =max(instance['Tmin0_vector'][k-1],t_current+transitionTime+durationTime)
            best_time = (instance['Tmin0_vector'][k-1]+instance['Tmax0_vector'][k-1])/2.0
            time_off_set.append(t_current-best_time)  
    else:
        if solution != []:
            k = solution[0]
            t_current = instance['Tmin_vector'][k-1]
            best_time = (instance['Tmin_vector'][k-1]+instance['Tmax_vector'][k-1])/2.0
            time_off_set.append(t_current-best_time)
        for k_next in solution[1:]:
            transitionTime =transTime(instance['distance_matrix'][k_next-1][k-1])
            durationTime = instance[shot2strip(k)]['strip-acquisition-duration']
            k = k_next
            t_current =max(instance['Tmin_vector'][k-1],t_current+transitionTime+durationTime)
            best_time = (instance['Tmin_vector'][k-1]+instance['Tmax_vector'][k-1])/2.0
            time_off_set.append(t_current-best_time)

    sum_time = sum([abs(x) for x in time_off_set])
    
    return(int(gain),sum_time)   



def evalROADEF2003(individual, instance, simple_flag = False, strip_flag = False,track_flag=False):
    def Piecewise(x):
        if x<0.4:
            return(x/4.0)
        elif x<0.7:
            return(x-0.3)
        else:
            return(2*x-1)
    gain=0
#    if track_flag:
#        solution = ind2solution_track(individual,instance)
#
#    else:
    solution = ind2solution(individual,instance, simple_flag = simple_flag, 
                            strip_flag = strip_flag, track_flag = track_flag)  
    if track_flag:
        for subSolution in solution:
            for strip in subSolution:
                gain += instance['stripgain_vector'][strip-1]
    elif strip_flag:
        for strip in solution:
            gain += instance['stripgain_vector'][strip-1]
# below is the picewise gain calculation
#        fr={}
#        for requestIndex in fnmatch.filter(instance.keys(),'request_*'):
#            fr[requestIndex] = 0
#            
#        for k in solution:
#            ri = instance['strip_%d' % k]['associated-request-index']
#            fr['request_%d' % ri] = fr['request_%d' % ri] + instance['strip_%d' % k]['strip-useful-surface']/ \
#                (instance['request_%d' % ri]['request-surface']*(instance['request_%d' % ri]['request-stereo']+1))          
#        for requestIndex in fnmatch.filter(instance.keys(),'request_*'):
#            gain = gain + instance[requestIndex]['request-gain']*instance[requestIndex]['request-surface']* \
#                (instance[requestIndex]['request-stereo']+1)*Piecewise(fr[requestIndex]) 
                
    elif simple_flag:
        for shot in solution:
            gain += instance['shotgain_vector'][shot-1]            
    else:
        fr={}
        for requestIndex in fnmatch.filter(instance.keys(),'request_*'):
            fr[requestIndex] = 0
            
        for k in solution:
            ri = instance[shot2strip(k)]['associated-request-index']
            fr['request_%d' % ri] = fr['request_%d' % ri] + instance[shot2strip(k)]['strip-useful-surface']/ \
                (instance['request_%d' % ri]['request-surface']*(instance['request_%d' % ri]['request-stereo']+1))
    
          
        for requestIndex in fnmatch.filter(instance.keys(),'request_*'):
            gain = gain + instance[requestIndex]['request-gain']*instance[requestIndex]['request-surface']* \
                (instance[requestIndex]['request-stereo']+1)*Piecewise(fr[requestIndex])
                #(instance[requestIndex]['request-stereo']+1)*fr[requestIndex]
            

    return(int(gain),)        
        
    
def readsolution2solution(textFile,instance):
    solution =[]
    with open(textFile) as f:
        for lineNum, line in enumerate(f, start=1):
                if lineNum >= 3:
                    values = line.strip().split()
                    for stripID in fnmatch.filter(instance.keys(),'strip_*'):
                        if instance[stripID]['strip-index']==int(values[0]):
                            if int(values[1]) == 0:
                                solution.append(2*int(stripID[6:])-1)
                            elif int(values[1]) == 1:
                                solution.append(2*int(stripID[6:]))
                        
    print('read solution file: ',textFile) 
    print('get solution:',solution)                           
    return(solution)



def cxSameSitCopyFirst(ind1,ind2):
    if len(ind1)!= len(ind2):print('***Error in Length of ind1 and ind2 are different')
    size = min(len(ind1), len(ind2))
    cxpoint1, cxpoint2 = sorted(random.sample(range(size), 2))
#    print(cxpoint1,cxpoint2)
    temp1 = [0]*len(ind1)
    temp2 = [0]*len(ind2)
    for x1,x2,i in zip(ind1,ind2,range(size)):
        if x1==x2 or ((i>=cxpoint1) and (i<=cxpoint2)): 
            temp1[i]=x2
            temp2[i]=x1
    for x1 in ind1:
        if x1 not in temp1:
            temp1[temp1.index(0)]=x1

    for x2 in ind2:
        if x2 not in temp2:
            temp2[temp2.index(0)]=x2 
    if (0 in temp1) or (0 in temp2):print('***Error in crossover')
    for i in range(len(ind1)):
        ind1[i]=temp1[i]
    for i in range(len(ind2)):
        ind2[i]=temp2[i]
    return ind1,ind2



def cxPartialyMatched(ind1, ind2):
    """Executes a partially matched crossover (PMX) on the input individuals.
    The two individuals are modified in place. This crossover expects
    :term:`sequence` individuals of indices, the result for any other type of
    individuals is unpredictable.
    
    :param ind1: The first individual participating in the crossover.
    :param ind2: The second individual participating in the crossover.
    :returns: A tuple of two individuals.

    Moreover, this crossover generates two children by matching
    pairs of values in a certain range of the two parents and swapping the values
    of those indexes. For more details see [Goldberg1985]_.

    """
    size = min(len(ind1), len(ind2))
    p1, p2 = [0]*size, [0]*size

    # Initialize the position of each indices in the individuals
    for i in range(size):
        p1[ind1[i]-1] = i
        p2[ind2[i]-1] = i
    # Choose crossover points
    cxpoint1 = random.randint(0, size)
    cxpoint2 = random.randint(0, size - 1)
    if cxpoint2 >= cxpoint1:
        cxpoint2 += 1
    else: # Swap the two cx points
        cxpoint1, cxpoint2 = cxpoint2, cxpoint1
#    print(cxpoint1,cxpoint2)
   
    # Apply crossover between cx points
    for i in range(cxpoint1, cxpoint2):
        # Keep track of the selected values
        temp1 = ind1[i]
        temp2 = ind2[i]
        # Swap the matched value
        ind1[i], ind1[p1[temp2-1]] = temp2, temp1
        ind2[i], ind2[p2[temp1-1]] = temp1, temp2
        # Position bookkeeping
        p1[temp1-1], p1[temp2-1] = p1[temp2-1], p1[temp1-1]
        p2[temp1-1], p2[temp2-1] = p2[temp2-1], p2[temp1-1]
    
    return ind1, ind2

def checkPopValidity(population):
    for ind in population:
        for indx in ind:
            if ind.count(indx)>=2:
                print('Not a valid pop !!!')
                print(ind)
                return(False)
    return(True)


def mutInverseIndexes(individual):
    start, stop = sorted(random.sample(range(len(individual)), 2))
    individual = individual[:start] + individual[stop:start-1:-1] + individual[stop+1:]
    return individual,

def mutExchangeLocation(individual):
    start, stop = sorted(random.sample(range(len(individual)), 2))
#    print(start,stop)
    individual[start], individual[stop] = individual[stop], individual[start]
    return individual,

def initRNDS(container, func1,func2, n):
    """ 
    initRNDS(list, toolbox.individual,toolbox.evaluate,n)
    # to replace initRepeat
    :param container: The type to put in the data from func.
    :param func: The function that will be called more thann times to fill the
                 container.
    :param n: The number of times to repeat func.
    :returns: An instance of the container filled with data from func.
    """
    returntemp =container()
    evaltemp =[]
    while len(returntemp)<n:
        tempfunc1=func1()
        if func2(tempfunc1) not in evaltemp:
            evaltemp.append(func2(tempfunc1))
            returntemp.append(tempfunc1)
    return returntemp

def Heuristic(instance, simple_flag =False, strip_flag = False):
    # To replace toobox.indexes
    # generate one individual
    if strip_flag:
        size = instance['strip-number']
    else:
        size = instance['strip-number']*2
    fr =list()
    for k in range(1,1+size):
        strip = instance['strip_%s' % k] if strip_flag else instance[shot2strip(k)] 
        ri = strip['associated-request-index'] 
        coordi_start = 0 if strip_flag else (k+1)%2
        coordi_end = 0 if strip_flag else k%2
        fr.append({'shot': k,
            'earliest-start-time':strip['coordinates_%s' % coordi_start]['te'],
            'shot-gain' :instance['request_%d' % ri]['request-gain']*strip['strip-useful-surface'],
            'unit-gain':instance['request_%d' % ri]['request-gain'],            
            'duration': strip['strip-acquisition-duration'],
            'VT': strip['coordinates_%s' % coordi_end]['tl']-strip['coordinates_%s' % coordi_start]['te'],
            'blank-VT':strip['coordinates_%s' % coordi_end]['tl'] \
                -strip['coordinates_%s' % coordi_start]['te']-strip['strip-acquisition-duration'],
            })
    inds = list()
    fr.sort(key=lambda x:x['earliest-start-time'],reverse=False) #ascending
    inds.append({'name': 'ind1', 'individual':[x['shot'] for x in fr],
                 'gain': evalROADEF2003([x['shot'] for x in fr],instance, simple_flag = simple_flag, strip_flag = strip_flag)[0]})
    fr.sort(key=lambda x:x['shot-gain'],reverse=True) #descending
    inds.append({'name': 'ind2', 'individual':[x['shot'] for x in fr],
                 'gain': evalROADEF2003([x['shot'] for x in fr],instance,simple_flag = simple_flag, strip_flag = strip_flag)[0]})
    fr.sort(key=lambda x:x['unit-gain'],reverse=True) 
    inds.append({'name': 'ind3', 'individual':[x['shot'] for x in fr],
                 'gain': evalROADEF2003([x['shot'] for x in fr],instance,simple_flag = simple_flag, strip_flag = strip_flag)[0]})
    fr.sort(key=lambda x:x['duration'],reverse=False) 
    inds.append({'name': 'ind4', 'individual':[x['shot'] for x in fr],
                 'gain': evalROADEF2003([x['shot'] for x in fr],instance,simple_flag = simple_flag, strip_flag = strip_flag)[0]})
    fr.sort(key=lambda x:x['VT'],reverse=False) 
    inds.append({'name': 'ind5', 'individual':[x['shot'] for x in fr],
                 'gain': evalROADEF2003([x['shot'] for x in fr],instance,simple_flag = simple_flag, strip_flag = strip_flag)[0]})
    fr.sort(key=lambda x:x['blank-VT'],reverse=False) 
    inds.append({'name': 'ind6', 'individual':[x['shot'] for x in fr],
                 'gain': evalROADEF2003([x['shot'] for x in fr],instance,simple_flag = simple_flag, strip_flag = strip_flag)[0]})
    
#    print(x['individual'] for x in inds)
    
    inds.sort(key=lambda x:x['gain'],reverse=True) 
    sum_gain = sum([x['gain'] for x in inds ])
    individual =[]
    for k in range(size):
        u = random.random() * sum_gain
        sum_= 0
        for ind in inds:
            sum_ += evalROADEF2003(ind['individual'],instance,simple_flag = simple_flag, strip_flag = strip_flag)[0]
            if sum_ > u:
                for x1 in ind['individual']:
                    if not x1 in individual:
                        individual.append(x1)
                        break
                else:
                    continue
                break
                
    return(individual)

def selRoulette(individuals, k, fit_attr="fitness"):
    """Select *k* individuals using *k* spins of a roulette. The selection is made by looking only at the first
    objective of each individual. The list returned contains references to
    the input *individuals*.
    
    :param individuals: A list of individuals to select from.
    :param k: The number of individuals to select.
    :param fit_attr: The attribute of individuals to use as selection criterion
    :returns: A list of selected individuals.
        
    .. warning::
       The roulette selection by definition cannot be used for minimization 
       or when the fitness can be smaller or equal to 0.
    """

    s_inds = sorted(individuals, key=attrgetter(fit_attr), reverse=True)
    sum_fits = sum(getattr(ind, fit_attr).values[0] for ind in individuals)
    chosen = []
    for i in range(k):
        u = random.random() * sum_fits
        sum_ = 0
        for ind in s_inds:
            sum_ += getattr(ind, fit_attr).values[0]
            if sum_ > u:
                chosen.append(ind)
                break
    
    return chosen


def gaROADEF2003(instName,iniMethod = 'RS',indSize=0,popSize = 100, cxPb=0.5, mutPb=0.05, NGen=100, \
                 simple_flag = False, Mul_Flag = False, strip_flag =False,track_flag = False, exportCSV=False):
    '''
    :param iniMethod: one from ['RS', 'RNDS', 'HRHS', 'FS']
    :param simple_flag:  True for no stereo constraint and pair constraint
    :param strip_flag: True for strip instance for customized data
    :param Mul_Flag: True for NSGA2
        [Deb2002] Deb, Pratab, Agarwal, and Meyarivan, "A fast elitist
        non-dominated sorting genetic algorithm for multi-objective
        optimization: NSGA-II", 2002.
    '''
    
    if strip_flag or track_flag:
        jsonDataDir = os.path.join(BASE_DIR,'data', 'json_customize')
        jsonFile = os.path.join(jsonDataDir, '%s.json' % instName)
        with open(jsonFile) as f:
            instance = load(f)
        indSize = instance['strip-number']
    else:
        jsonDataDir = os.path.join(BASE_DIR,'data', 'json_ROADEF2003')
        jsonFile = os.path.join(jsonDataDir, '%s.json' % instName)
        with open(jsonFile) as f:
            instance = load(f)
        indSize = instance['strip-number']*2
        
    creator.create('FitnessMax', base.Fitness, weights=(1.0,-1.0) if Mul_Flag else (1.0,))
    creator.create('Individual', list, fitness=creator.FitnessMax)
    toolbox = base.Toolbox()
    # Attribute generator
    toolbox.register('indexes', random.sample, range(1, indSize + 1), indSize)
    # Evaluate define
    toolbox.register('evaluate', evalMulROADEF2003 if Mul_Flag else evalROADEF2003, \
                     simple_flag = simple_flag, strip_flag = strip_flag, \
                     track_flag = track_flag, instance=instance)
    # Structure initializers
    toolbox.register('individual', tools.initIterate, creator.Individual, toolbox.indexes)
    toolbox.register('heuristic',Heuristic,instance, simple_flag = simple_flag, strip_flag = strip_flag)
    toolbox.register('individual_heuri',tools.initIterate,creator.Individual,toolbox.heuristic)
    if iniMethod =='RS' :
        # STRATEGY 1: RS
        toolbox.register('population', tools.initRepeat, list, toolbox.individual)
        pop = toolbox.population(n=popSize)
    elif iniMethod == 'RNDS':
        # STRATEGY 2: RNDS
        toolbox.register('population', initRNDS, list, toolbox.individual,toolbox.evaluate)
        pop = toolbox.population(n=popSize)
    elif iniMethod == 'HRHS':
        # STRATEGY 3: HRHS
        toolbox.register('population', tools.initRepeat, list, toolbox.individual_heuri)
        pop = toolbox.population(n=popSize)
    elif iniMethod == 'FS':
        # STRATEGY 4 : FS
        toolbox.register('population', tools.initRepeat, list, toolbox.individual)           
        omega = 2
        pop_big =toolbox.population(n=omega* popSize)
        fitnesses = list(map(toolbox.evaluate, pop_big))
        for ind, fit in zip(pop_big, fitnesses):
            ind.fitness.values = fit    
        pop = tools.selBest(pop_big, popSize)
    else:
        print('Currently unsupported initialization method!')
        exit(1)
    # Operator registering    
    toolbox.register('select',tools.selNSGA2 if Mul_Flag else tools.selRoulette)
    toolbox.register('mate', cxSameSitCopyFirst)
    toolbox.register('mutate', mutExchangeLocation)


    if iniMethod == 'RNDS':
        # check if the pop successfully initialized with RNDS 
        fitnesses = list(map(toolbox.evaluate, pop))
        for fitness in fitnesses:
            if fitnesses.count(fitness)>1:
                print('***Error for same fitness value')  
    
    # check the validity of pop initialization
    if not checkPopValidity(pop):print('not a valid pop initialization!!!')
    csvData = []    
    print('Start of evolution')
    # Evaluate the entire population
    fitnesses = list(map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit
    print('  Evaluated %d individuals' % len(pop))
    # Begin the evolution
    for g in range(NGen):
        print('-- Generation %d --' % g)                
        # Select the next generation individuals
        offspring = toolbox.select(pop, len(pop))
        # Clone the selected individuals
        offspring = list(map(toolbox.clone, offspring))
        # Apply crossover and mutation on the offspring
        for child1, child2,i in zip(offspring[::2], offspring[1::2],range(1, len(offspring), 2)):
            if random.random() < cxPb and child1 != child2:
#                print(offspring[i - 1], offspring[i])                 
                child1_oldFit = 0
                child2_olfFit = 0
                count = 0 
                #  Preserve the solution with greater fitness
                while (child1_oldFit <= child1.fitness.values[0] or child2_olfFit <= child2.fitness.values[0]) \
                and count < 10 :                    
                    child1_oldFit=child1.fitness.values[0]
                    child2_olfFit=child2.fitness.values[0]
                    toolbox.mate(child1, child2)
                    count = count +1
#                if not count < 10: print('crossover 10 times')
                del child1.fitness.values
                del child2.fitness.values
#                print (offspring[i - 1], offspring[i] ) 
                # check the validity of pop
                if not checkPopValidity(offspring):print('not a valid pop after cross over!!!')

        for mutant in offspring :
            if random.random() < mutPb and mutant.fitness.valid:
#                print(mutant)
                mutant_oldFit = 0
                count = 0
                while (mutant_oldFit <= mutant.fitness.values[0]) \
                and count < 10:
                    mutant_oldFit = mutant.fitness.values[0]
                    toolbox.mutate(mutant)
                    count =  count+1
#                if not count < 10: print('mutation 10 times')
                del mutant.fitness.values
#                print(mutant)                
                # check the validity of pop
                if not checkPopValidity(offspring):print('not a valid pop after mutation!!!')
                        
        # Evaluate the individuals with an invalid fitness
        invalidInd = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = map(toolbox.evaluate, invalidInd)
        for ind, fit in zip(invalidInd, fitnesses):
            ind.fitness.values = fit
        print('  Evaluated %d individuals' % len(invalidInd))
        # The population is entirely replaced by the offspring
        pop[:] =toolbox.select( offspring + pop, popSize)
        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in pop] #if not [0], returns tuple instead of float
        length = len(pop)
        mean = sum(fits) / length
        sum2 = sum(x*x for x in fits)
        std = abs(sum2 / length - mean**2)**0.5
        print('  Min %s' % min(fits))
        print('  Max %s' % max(fits))
        print('  Avg %s' % mean)
        print('  Std %s' % std)
        # Write data to holders for exporting results to CSV file
        if exportCSV:
            csvRow = {
                'generation': g,
                'evaluated_individuals': len(invalidInd),
                'min_fitness': min(fits),
                'max_fitness': max(fits),
                'avg_fitness': mean,
                'std_fitness': std,
            }
            csvData.append(csvRow)

    print('-- End of (successful) evolution --')
    bestInd = tools.selBest(pop, 1)[0]
    print('Best individual: %s' % bestInd)
    print('Fitness: ' , bestInd.fitness.values) 
    print(ind2solution(bestInd, instance, simple_flag = simple_flag, 
                       strip_flag = strip_flag, track_flag=track_flag))
    print('Total cost: %s' % (1 / bestInd.fitness.values[0]))
    print('End of evolution')

    if not strip_flag:
        solutionFile= os.path.join(BASE_DIR,'Solutions','solution'+instName[8:])
        #testSolution = [4, 6, 8, 2, 10, 12, 14]
        testSolution = readsolution2solution(solutionFile,instance)
        verifySolution(testSolution,instance)  
        print(toolbox.evaluate(testSolution))
    if exportCSV:
        csvFilename = '%s_iS%s_pS%s_cP%s_mP%s_nG%s.csv' % (instName, indSize, popSize, cxPb, mutPb, NGen)
        csvPathname = os.path.join(BASE_DIR, 'results', csvFilename)
        print('Write to file: %s' % csvPathname)
        makeDirsForFile(pathname=csvPathname)
        if not exist(pathname=csvPathname, overwrite=True):
            with open(csvPathname, 'w') as f:
                fieldnames = ['generation', 'evaluated_individuals', 'min_fitness', 'max_fitness', 'avg_fitness', 'std_fitness']
                writer = DictWriter(f, fieldnames=fieldnames, dialect='excel')
                writer.writeheader()
                for csvRow in csvData:
                    writer.writerow(csvRow)
