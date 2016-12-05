# -*- coding: utf-8 -*-
"""
Created on Thu Sep 08 18:03:03 2016

@author: aaa34169
"""
import logging

import sys

# ------------------- CONSTANT ------------------------------------------------

# [REQUIRED] ----------------------------------
MAIN_PYCGM2_PATH = "C:\\Users\\AAA34169\\Documents\\Programming\\API\\pyCGM2\\pyCGM2\\" # path toward your pyCGM2 folder ( dont forget \\ ending)  
PYTHON_PACKAGES =  'C:\\Anaconda32\\Lib\\site-packages' # site-package in your python environnement


# configure if you want to run processes from Nexus   
NEXUS_SDK_WIN32 = 'C:/Program Files (x86)/Vicon/Nexus2.5/SDK/Win32'
NEXUS_SDK_PYTHON = 'C:/Program Files (x86)/Vicon/Nexus2.5/SDK/Python'
PYTHON_NEXUS = 'C:\\Program Files (x86)\\Vicon\\Nexus2.5\\Python'


# [OPTIONAL] ----------------------------------
 
# [Optional]: openMA binding
OPENMA_BINDING_PATH = MAIN_PYCGM2_PATH + "third party\\" # By default, use openMA distribution included in third party folder  

# [Optional] Normative data base. 
NORMATIVE_DATABASE_PATH = MAIN_PYCGM2_PATH +"Data\\normativeData\\"  # By default, use pyCGM2-embedded normative data ( Schartz - Pinzone )  

# [Optional] main folder containing osim model 
OPENSIM_PREBUILD_MODEL_PATH = MAIN_PYCGM2_PATH + "Extern\\opensim\\" 

# [Optional] path pointing at Data Folders used for Tests
TEST_DATA_PATH = "C:\\Users\\AAA34169\\Documents\\VICON DATA\\pyCGM2-Data\\"
MAIN_BENCHMARK_PATH = "C:\\Users\\AAA34169\\Documents\\VICON DATA\\pyCGM2-benchmarks\\Gait patterns\\"

# ------------------- METHODS ------------------------------------------------

def setLoggingLevel(level):
    logging.basicConfig(format = "[pyCGM2-%(levelname)s]-%(module)s-%(funcName)s : %(message)s",level = level) 

    
def addNexusPythonSdk():
    
    if NEXUS_SDK_WIN32  not in sys.path:
        sys.path.append( NEXUS_SDK_WIN32)
        print NEXUS_SDK_WIN32 + " added to the python path"
    if NEXUS_SDK_PYTHON  not in sys.path:
        sys.path.append( NEXUS_SDK_PYTHON)
        print NEXUS_SDK_WIN32 + " added to the python path"

    NEXUS_PYTHON_USE = True if PYTHON_NEXUS in sys.path else False
    if NEXUS_PYTHON_USE:
        raise Exception("untick Use nexus Python in your python pipeline operation. pyCGA apps recommand anaconda Packages ")
        

def addOpenma(branch=None):

    if branch is None:
        sys.path.append(OPENMA_BINDING_PATH + "\\openma")
        sys.path.append(OPENMA_BINDING_PATH + "\\openma\\ma")
    else:
        if branch=="master":
            sys.path.append("C:\\Users\\AAA34169\\Documents\\Programming\\openMA\\distribuable\\OpenMA\\openma")
            sys.path.append("C:\\Users\\AAA34169\\Documents\\Programming\\openMA\\distribuable\\OpenMA\\openma\\ma")
            
            # method 1 : with path definition
            # need definition in the PATH, I appended these two folders: 
            # C:\Users\AAA34169\Documents\Programming\openMA\Build\master\bin;
            # C:\Users\AAA34169\Documents\Programming\openMA\Build\master\bin\swig\python\openma\ma;
            #sys.path.append("C:\\Users\\AAA34169\\Documents\\Programming\\openMA\\Build\\master\\bin\\swig\\python\\openma")
            #sys.path.append("C:\\Users\\AAA34169\\Documents\\Programming\\openMA\\Build\\master\\bin\\swig\\python\\openma\\ma")
            
            # method 2 : with openMA distribution made manually 
            sys.path.append("C:\\Users\\AAA34169\\Documents\\Programming\\openMA\\distribuable\\OpenMA\\openma")
            sys.path.append("C:\\Users\\AAA34169\\Documents\\Programming\\openMA\\distribuable\\OpenMA\\openma\\ma")
    
        elif branch=="plugin-gait-kad":
            
            # method 2 : with openMA distribution made manually 
            sys.path.append("C:\\Users\\AAA34169\\Documents\\Programming\\openMA\\distribuable\\OpenMA-KAD\\openma")
            sys.path.append("C:\\Users\\AAA34169\\Documents\\Programming\\openMA\\distribuable\\OpenMA-KAD\\openma\\ma")
            
            
def checkConfig():

    for it in sys.path: 
        if "pyCGM2" in it: 
            print "OK"    
    try:
        import pyCGM2
        import pyCGM2.pyCGM2_CONFIG
        pyCGM2.pyCGM2_CONFIG.setLoggingLevel(logging.DEBUG)
        logging.info("pyCGM2 ---> OK")
    except ImportError:
        raise Exception ("[pyCGM2] : pyCGM2 module not in your python path")
    
    
    # vicon nexus
    pyCGM2.pyCGM2_CONFIG.addNexusPythonSdk()
    try:
        import ViconNexus
        logging.info("vicon API ---> OK" )
    except ImportError:
        raise Exception ("[pyCGM2] : viconNexus is not in your python path. Check pyCGM2_CONFIG")
    
    
    # openMA
    pyCGM2.pyCGM2_CONFIG.addOpenma()
    try:
        import ma.io
        import ma.body
        logging.info("openMA API ---> OK" )        
    except ImportError:
        raise Exception ("[pyCGM2] : openma is not in your python path. Check pyCGM2_CONFIG")