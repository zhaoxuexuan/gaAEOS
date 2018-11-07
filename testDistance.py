#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 24 19:03:47 2018

@author: zhaoxx17
"""

from json import load
import random
from deap import tools



def transTime(distance):    
    Hs =633000.0 # satellite altitude in meters
    Vr = 0.05 # the maximum speed of rotation in rad/s
    Dmin = 2.5 # incompressible transition time in seconds
    return(2*math.atan(distance/(2*Hs))/Vr + Dmin)
    
def shot2strip(k):
    return('strip_%d' % int((k+1)/2))
    
 
def verifySolution(solution,instance):
    #solution is a list containing a sequence of shotID selected
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
    
    
def ind2solution(individual, instance):
    # individual is a list containing a sequence of shotID selected
    # solution is a valid list, cut from individual
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
        # cut indibidual : stereo violation
        #**************HERE NEED TO ADD**************
      
    #print('ind2solution:',solution)  
    return solution



def printTrack(track, merge=False):
    trackStr = ' '
    subTrackCount = 0
    for subTrack in track:
        subTrackCount += 1
        subTrackStr = ' '
        for k in subTrack:
            subTrackStr = subTrackStr + ' - ' + str(k)
            trackStr = trackStr + ' - ' + str(k)
        subTrackStr = subTrackStr + ' - '
        if not merge:
            print('  subTrack %d\: %s' % (subTrackCount, subTrackStr))
        trackStr = trackStr + ' - '
    if merge:
        print(trackStr)
    return



def evalROADEF2003(individual, instance):
    def Piecewise(x):
        if x<0.4:
            return(x/4.0)
        elif x<0.7:
            return(x-0.3)
        else:
            return(2*x-1)
    solution = ind2solution(individual,instance)        
    fr={}
    for requestIndex in fnmatch.filter(instance.keys(),'request_*'):
        fr[requestIndex] = 0
        
    for k in solution:
        ri = instance[shot2strip(k)]['associated-request-index']
        fr['request_%d' % ri] = fr['request_%d' % ri] + instance[shot2strip(k)]['strip-useful-surface']/ \
            (instance['request_%d' % ri]['request-surface']*(instance['request_%d' % ri]['request-stereo']+1))

    gain=0       
    for requestIndex in fnmatch.filter(instance.keys(),'request_*'):
        gain = gain + instance[requestIndex]['request-gain']*instance[requestIndex]['request-surface']* \
            (instance[requestIndex]['request-stereo']+1)*Piecewise(fr[requestIndex])
    #print('Total gain:',gain)
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
    print(cxpoint1,cxpoint2)
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

    This function uses the :func:`~random.randint` function from the python base
    :mod:`random` module.
    
    .. [Goldberg1985] Goldberg and Lingel, "Alleles, loci, and the traveling
       salesman problem", 1985.
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
    print(start,stop)
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

def initHRHS(container, func1,func2, n):
    """ 
    initRNDS(list, toolbox.individual,toolbox.evaluate,n)
    # to replace initRepeat
    :param container: The type to put in the data from func.
    :param func: The function that will be called more thann times to fill the
                 container.
    :param n: The number of times to repeat func.
    :returns: An instance of the container filled with data from func.
    """
#    returntemp =container()
#    evaltemp =[]
#    while len(returntemp)<n:
#        tempfunc1=func1()
#        if func2(tempfunc1) not in evaltemp:
#            evaltemp.append(func2(tempfunc1))
#            returntemp.append(tempfunc1)
#    return returntemp

def Heuristic(instance):
    # To replace toobox.indexes
    # generate one individual
    size = instance['strip-number']*2
    fr =list()
    for k in range(1,1+size):
        ri = instance[shot2strip(k)]['associated-request-index']
        coordi_start = (k+1)%2
        coordi_end = k%2
        strip =instance[shot2strip(k)]
        fr.append({'shot': k,
            'earliest-start-time':strip['coordinates_%s' % coordi_start]['te'],
            'shot-gain' :instance['request_%d' % ri]['request-gain']*instance[shot2strip(k)]['strip-useful-surface'],
            'unit-gain':instance['request_%d' % ri]['request-gain'],            
            'duration': strip['strip-acquisition-duration'],
            'VT': strip['coordinates_%s' % coordi_end]['tl']-strip['coordinates_%s' % coordi_start]['te'],
            'blank-VT':strip['coordinates_%s' % coordi_end]['tl'] \
                -strip['coordinates_%s' % coordi_start]['te']-strip['strip-acquisition-duration'],
            })
    inds = list()
    fr.sort(key=lambda x:x['earliest-start-time'],reverse=False) #ascending
    inds.append({'name': 'ind1', 'individual':[x['shot'] for x in fr],
                 'gain': evalROADEF2003([x['shot'] for x in fr],instance)[0]})
    fr.sort(key=lambda x:x['shot-gain'],reverse=True) #descending
    inds.append({'name': 'ind2', 'individual':[x['shot'] for x in fr],
                 'gain': evalROADEF2003([x['shot'] for x in fr],instance)[0]})
    fr.sort(key=lambda x:x['unit-gain'],reverse=True) 
    inds.append({'name': 'ind3', 'individual':[x['shot'] for x in fr],
                 'gain': evalROADEF2003([x['shot'] for x in fr],instance)[0]})
    fr.sort(key=lambda x:x['duration'],reverse=False) 
    inds.append({'name': 'ind4', 'individual':[x['shot'] for x in fr],
                 'gain': evalROADEF2003([x['shot'] for x in fr],instance)[0]})
    fr.sort(key=lambda x:x['VT'],reverse=False) 
    inds.append({'name': 'ind5', 'individual':[x['shot'] for x in fr],
                 'gain': evalROADEF2003([x['shot'] for x in fr],instance)[0]})
    fr.sort(key=lambda x:x['blank-VT'],reverse=False) 
    inds.append({'name': 'ind6', 'individual':[x['shot'] for x in fr],
                 'gain': evalROADEF2003([x['shot'] for x in fr],instance)[0]})
    
    print(x['individual'] for x in inds)
    
    inds.sort(key=lambda x:x['gain'],reverse=True) 
    sum_gain = sum([x['gain'] for x in inds ])
    individual =[]
    for k in range(size):
        u = random.random() * sum_gain
        sum_= 0
        for ind in inds:
            sum_ += evalROADEF2003(ind['individual'],instance)[0]
            if sum_ > u:
                for x1 in ind['individual']:
                    if not x1 in individual:
                        individual.append(x1)
                        break
                else:
                    continue
                break
                
    return(individual)

def main():


    with open('data/json_ROADEF2003/instance_2_9_66.json') as f:
        instance = load(f)
#    
#    strip1 = instance['strip_529']
#    strip2 = instance['strip_524']
#    print(distance(1058,1047,strip1, strip2))
    ind1=[1,10,9,8,7,6, 3, 4, 2,5]
    ind2=[1,7,8,9,10,5, 3, 6, 2,4]
    print(Heuristic(instance))

if __name__ == '__main__':
    main()
