#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 23 13:10:50 2018

@author: zhaoxx17
"""

# -*- coding: utf-8 -*-

import os
import fnmatch
from json import dump
from . import BASE_DIR

def makeDirsForFile(pathname):
    try:
        os.makedirs(os.path.dirname(pathname))
    except:
        pass


def exist(pathname, overwrite=False, displayInfo=True):
    def __pathType(pathname):
        if os.path.isfile(pathname):
            return 'File'
        if os.path.isdir(pathname):
            return 'Directory'
        if os.path.islink(pathname):
            return 'Symbolic Link'
        if os.path.ismount(pathname):
            return 'Mount Point'
        return 'Path'
    if os.path.exists(pathname):
        if overwrite:
            if displayInfo:
                print('%s: %s exists. Overwrite.' % (__pathType(pathname), pathname))
            os.remove(pathname)
            return False
        else:
            if displayInfo:
                print('%s: %s exists.' % (__pathType(pathname), pathname))
            return True
    else:
        if displayInfo:
            print('%s: %s does not exist.' % (__pathType(pathname), pathname))
        return False
    
def readsolution(textFile):
    solution ={}
    with open(textFile) as f:
        for lineNum, line in enumerate(f, start=1):
                if lineNum >= 3:
                    values = line.strip().split()
                    solution[int(values[0])] = int(values[1])                 
    print('read solution file: ',textFile) 
    print('get solution:',solution)                           
    return(solution)

def text2json(customize= 0):
    '''
     customize : 0 ROADEF2003 data (consider both 01 and 10 direction)
                 1 ROADEF2003 data customized (by hand) (strip_flag = True)
                 2 4U EOS data  (strip_flag = True)
                 3 strip data with the best solution included (strip_flag = True)
    '''
    def distance(k1,k2,strip1, strip2):
        j1=int((k1+1)/2)
        i1= k1 % 2
        j2=int((k2+1)/2)
        i2=(k2+1)%2
        return (((strip1['coordinates_%s' % i1]['x'] - strip2['coordinates_%s' % i2]['x'] )**2 + (strip1['coordinates_%s' % i1]['y'] - strip2['coordinates_%s' % i2]['y'] )**2 )**0.5)
    def shot2strip(k):
        return('strip_%d' % int((k+1)/2))
    def strip2request(strip):
        return('request_%d' % int(strip['associated-request-index']))  

    def Tmin(k,strip):
        #Tmin(k,jsonData[shot2strip(k) )
        j1=int((k+1)/2)
        i1=(k+1)%2 
        i2=k%2
        return(max(strip['coordinates_%s' % i1]['te'],strip['coordinates_%s' % i2]['te']-strip['strip-acquisition-duration']))
    def Tmax(k,strip):
        #Tmax(k,jsonData[shot2strip(k) )
        j1=int((k+1)/2)
        i1=(k+1)%2 
        i2=k%2
        return(min(strip['coordinates_%s' % i1]['tl'],strip['coordinates_%s' % i2]['tl']-strip['strip-acquisition-duration']))   
    def Tmin_0(strip):
        return(max(strip['coordinates_0' ]['te'],strip['coordinates_1' ]['te']-strip['strip-acquisition-duration']))    
    def Tmax_0(strip):
        return(min(strip['coordinates_0' ]['tl'],strip['coordinates_1' ]['tl']-strip['strip-acquisition-duration']))  
    def distance10(strip1, strip2):
        return (((strip1['coordinates_1' ]['x'] - strip2['coordinates_0' ]['x'] )**2 + (strip1['coordinates_1' ]['y'] - strip2['coordinates_0' ]['y'] )**2 )**0.5)
  
    def shotgain(k,strip,request):
        return(strip['strip-useful-surface']*request['request-gain'])
    def stripgain(strip,request):
        return(strip['strip-useful-surface']*request['request-gain'])
    if customize == 1: 
        textDataDir = os.path.join(BASE_DIR, 'data', 'text_customize')
        jsonDataDir = os.path.join(BASE_DIR, 'data', 'json_customize')
    elif customize == 2:
        textDataDir = os.path.join(BASE_DIR, 'data', 'text_4U_EOS')
        jsonDataDir = os.path.join(BASE_DIR, 'data', 'json_4U_EOS')
    elif customize == 3:
        textDataDir = os.path.join(BASE_DIR, 'data', 'text_ROADEF2003')
        jsonDataDir = os.path.join(BASE_DIR, 'data', 'json_customize')       
    else:
        textDataDir = os.path.join(BASE_DIR, 'data', 'text_ROADEF2003')
        jsonDataDir = os.path.join(BASE_DIR, 'data', 'json_ROADEF2003')

    for textFile in map(lambda textFilename: os.path.join(textDataDir, textFilename), os.listdir(textDataDir)):
        jsonData = {}
        j = 0
        print("read text file: " + textFile)
        with open(textFile) as f:
            for lineNum, line in enumerate(f, start=1):
                if lineNum in [3]:
                    pass
                elif lineNum == 1:
                    # instance-information ::= data-set-number grid-number track-number
                    values = line.strip().split()
                    if customize != 2:                        
                        jsonData['instance_name'] = ('instance_%s_%s_%s' % (values[0],values[1],values[2]))
                    jsonData['data-set-number'] = int(values[0])
                    jsonData['grid-number'] = int(values[1])
                    jsonData['track-number'] = int(values[2])
                elif lineNum == 2:
                    # request-strip-numbers ::= request-number strip-number
                    values = line.strip().split()
                    jsonData['request-number'] = int(values[0])
                    jsonData['strip-number'] = int(values[1])
                    if customize == 2:
                       jsonData['instance_name'] = ('instance_%s_%s' % (values[0],values[1])) 
                    if customize == 3:  
                        solutionFile = os.path.join('/media/zhaoxx17/新加卷/py-ga-VRPTW','Solutions','solution'+jsonData['instance_name'][8:])                    
                        solutionDict = readsolution(solutionFile)
                elif lineNum <= jsonData['request-number']+3:
                    # request ::= request-index request-gain request-surface request-type request-stereo
                    values = line.strip().split()
                    if customize == 2:                   
                        jsonData['request_%s' % values[0]] = {
                            'user-number' : int(values[1]),
                            'request-gain': int(values[2]),
                            'request-surface': float(values[3]),
                            'request-type': int(values[4]),
                            'request-stereo': int(values[5]),
                        }
                    else:
                        jsonData['request_%s' % values[0]] = {                        
                            'request-gain': int(values[1]),
                            'request-surface': float(values[2]),
                            'request-type': int(values[3]),
                            'request-stereo': int(values[4]),
                        }
                elif int((lineNum-jsonData['request-number']-3)%5)==1:
                     # index-information ::= strip-index associated-request-index to-be-ignored twin-strip-index 
                    values = line.strip().split()  
                    j= j+1
                    jsonData['strip_%s' % j] = {
                        'strip-index': int(values[0]),
                        'associated-request-index': int(values[1]),
                        'twin-strip-index': int(values[3]),                        
                    }
                    stripIndex = int(values[0])
                    if customize == 3 and stripIndex in solutionDict.keys():
                        direct = [solutionDict[stripIndex], (solutionDict[stripIndex]+1)%2]
                    else:
                        direct = [0, 1]
                elif int((lineNum-jsonData['request-number']-3)%5)==3:
                    # strip-information ::= strip-useful-surface strip-acquisition-duration
                    values = line.strip().split()  
                    jsonData['strip_%s' % j] ['strip-useful-surface'] = float(values[0])
                    jsonData['strip_%s' % j] ['strip-acquisition-duration'] = float(values[1])
                elif int((lineNum-jsonData['request-number']-3)%5)==4:
                    # end0-information ::= end0-x-coordinate end0-y-coordinate end0-earliest-visibility end0-latest-visibility
                    values = line.strip().split()  
                    jsonData['strip_%s' % j] ['coordinates_%s' % direct[0]] = {
                            'x': int(values[0]),
                            'y': int(values[1]),
                            'te': float(values[2]),
                            'tl': float(values[3]),
                        }
                elif int((lineNum-jsonData['request-number']-3)%5)==0:
                    # end1-information ::= end1-x-coordinate end1-y-coordinate end1-earliest-visibility end1-latest-visibility
                    values = line.strip().split()  
                    jsonData['strip_%s' % j] ['coordinates_%s' % direct[1]] = {
                            'x': int(values[0]),
                            'y': int(values[1]),
                            'te': float(values[2]),
                            'tl': float(values[3]),
                        }
                else:
                    # selection-information ::= to-be-ignored to-be-ignored

                    pass

        if customize:
            strips = [x for x in range(1,j+1)]
            jsonData['distance10_matrix']=[[ distance10(jsonData['strip_%s' % k1], jsonData['strip_%s' % k2]) for k1 in strips] for k2 in strips]
            jsonData['Tmin0_vector']=[Tmin_0(jsonData['strip_%s' % k]) for k in strips]
            jsonData['Tmax0_vector']=[Tmax_0(jsonData['strip_%s' % k]) for k in strips]
            jsonData['stripgain_vector']=[stripgain(jsonData['strip_%s' % k],jsonData[strip2request(jsonData['strip_%s' %k])]) for k in strips]
            jsonData['stripgain_vector'].append(0.0)
            jsonFilename = 'instance_%s.json' % j
        else:
            shots = [x for x in range(1, 2*j +1)]
            jsonData['distance_matrix'] = [[ distance(k1,k2,jsonData[shot2strip(k1)], jsonData[shot2strip(k2)]) for k1 in shots] for k2 in shots]
            jsonData['Tmin_vector']=[ Tmin(k,jsonData[shot2strip(k)]) for k in shots]
            jsonData['Tmax_vector']=[ Tmax(k,jsonData[shot2strip(k)]) for k in shots]
            jsonData['shotgain_vector']=[ shotgain(k,jsonData[shot2strip(k)],jsonData[strip2request(jsonData[shot2strip(k)])] )  for k in shots]
            jsonData['shotgain_vector'].append(0.0)
            for k in shots:
                if jsonData[shot2strip(k)]['twin-strip-index']!= 0:
                    for stripID in fnmatch.filter(jsonData.keys(),'strip_*'):
                        if jsonData[stripID]['strip-index'] == jsonData[shot2strip(k)]['twin-strip-index']:
                            jsonData[shot2strip(k)]['twin-strip-ID'] = stripID
                else:
                    jsonData[shot2strip(k)]['twin-strip-ID'] = ''
                    
            jsonFilename = '%s.json' % jsonData['instance_name']
        jsonPathname = os.path.join(jsonDataDir, jsonFilename)
        print('Write to file: %s' % jsonPathname)
        makeDirsForFile(pathname=jsonPathname)
        with open(jsonPathname, 'w') as f:
            dump(jsonData, f, sort_keys=True, indent=4, separators=(',', ': '))
