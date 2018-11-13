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


def text2json(customize=False):
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
    def shotgain(k,strip,request):
        return(strip['strip-useful-surface']*request['request-gain'])
    if customize:
        textDataDir = os.path.join(BASE_DIR, 'data', 'text_customize')
        jsonDataDir = os.path.join(BASE_DIR, 'data', 'json_customize')
    else:
        textDataDir = os.path.join(BASE_DIR, 'data', 'text_ROADEF2003')
        jsonDataDir = os.path.join(BASE_DIR, 'data', 'json_ROADEF2003')
    for textFile in map(lambda textFilename: os.path.join(textDataDir, textFilename), os.listdir(textDataDir)):
        jsonData = {}
        j = 0
        with open(textFile) as f:
            for lineNum, line in enumerate(f, start=1):
                if lineNum in [3]:
                    pass
                elif lineNum == 1:
                    # instance-information ::= data-set-number grid-number track-number
                    values = line.strip().split()
                    jsonData['instance_name'] = ('instance_%s_%s_%s' % (values[0],values[1],values[2]))
                    jsonData['data-set-number'] = int(values[0])
                    jsonData['grid-number'] = int(values[1])
                    jsonData['track-number'] = int(values[2])
                elif lineNum == 2:
                    # request-strip-numbers ::= request-number strip-number
                    values = line.strip().split()
                    jsonData['request-number'] = int(values[0])
                    jsonData['strip-number'] = int(values[1])
                elif lineNum <= jsonData['request-number']+3:
                    # request ::= request-index request-gain request-surface request-type request-stereo
                    values = line.strip().split()
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
                elif int((lineNum-jsonData['request-number']-3)%5)==3:
                    # strip-information ::= strip-useful-surface strip-acquisition-duration
                    values = line.strip().split()  
                    jsonData['strip_%s' % j] ['strip-useful-surface'] = float(values[0])
                    jsonData['strip_%s' % j] ['strip-acquisition-duration'] = float(values[1])
                elif int((lineNum-jsonData['request-number']-3)%5)==4:
                    # end0-information ::= end0-x-coordinate end0-y-coordinate end0-earliest-visibility end0-latest-visibility
                    values = line.strip().split()  
                    jsonData['strip_%s' % j] ['coordinates_0'] = {
                            'x': int(values[0]),
                            'y': int(values[1]),
                            'te': float(values[2]),
                            'tl': float(values[3]),
                        }
                elif int((lineNum-jsonData['request-number']-3)%5)==0:
                    # end1-information ::= end1-x-coordinate end1-y-coordinate end1-earliest-visibility end1-latest-visibility
                    values = line.strip().split()  
                    jsonData['strip_%s' % j] ['coordinates_1'] = {
                            'x': int(values[0]),
                            'y': int(values[1]),
                            'te': float(values[2]),
                            'tl': float(values[3]),
                        }
                else:
                    # selection-information ::= to-be-ignored to-be-ignored

                    pass


        shots = [x for x in range(1, 2*j +1)]
#                    distance(k1,k2,jsonData[shot2strip(k1)], jsonData[shot2strip(k2)])
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
