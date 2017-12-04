# -*- coding: utf-8 -*-
#import ipdb
import logging
import argparse
import matplotlib.pyplot as plt

# pyCGM2 settings
import pyCGM2
pyCGM2.CONFIG.setLoggingLevel(logging.INFO)



# pyCGM2 libraries
from pyCGM2.Tools import btkTools
from pyCGM2.Model.CGM2.coreApps import cgmUtils, cgm1
from pyCGM2.Utils import files

if __name__ == "__main__":
    DEBUG = False

    parser = argparse.ArgumentParser(description='CGM1 Fitting')
    parser.add_argument('--trial', type=str, help='static c3d')
    parser.add_argument('--proj', type=str, help='Moment Projection. Choice : Distal, Proximal, Global')
    parser.add_argument('-mfpa',type=str,  help='manual assignment of force plates')
    parser.add_argument('-md','--markerDiameter', type=float, help='marker diameter')
    parser.add_argument('-ps','--pointSuffix', type=str, help='suffix of model outputs')
    parser.add_argument('--check', action='store_true', help='force model output suffix')
    parser.add_argument('-fs','--fileSuffix', type=str, help='suffix of output file')
    args = parser.parse_args()

    # --------------------------GLOBAL SETTINGS ------------------------------------
    # global setting ( in user/AppData)
    settings = files.openJson(pyCGM2.CONFIG.PYCGM2_APPDATA_PATH,"CGM1-pyCGM2.settings")

    # --------------------------CONFIG ------------------------------------
    argsManager = cgmUtils.argsManager_cgm1(settings,args)
    markerDiameter = argsManager.getMarkerDiameter()
    pointSuffix = argsManager.getPointSuffix("cgm1")
    momentProjection =  argsManager.getMomentProjection()
    mfpa = argsManager.getManualForcePlateAssign()

    # --------------------------LOADING ------------------------------------
    if DEBUG:
        DATA_PATH = pyCGM2.CONFIG.TEST_DATA_PATH + "Datasets Tests\\fraser\\New Session\\"
        reconstructFilenameLabelled = "15KUFC01_Trial04.c3d"
        args.fileSuffix="TEST"

    else:
        DATA_PATH =os.getcwd()+"\\"
        reconstructFilenameLabelled = args.trial

    logging.info( "data Path: "+ DATA_PATH )
    logging.info( "calibration file: "+ reconstructFilenameLabelled)

    # --------------------pyCGM2 MODEL ------------------------------
    model = files.loadModel(DATA_PATH,None)

    # --------------------------CHECKING -----------------------------------
    # check model is the CGM1
    logging.info("loaded model : %s" %(model.version ))
    if model.version != "CGM1.0":
        raise Exception ("%s-pyCGM2.model file was not calibrated from the CGM1.0 calibration pipeline"%model.version)

        # --------------------------SESSION INFOS ------------------------------------

    #  translators management
    translators = files.getTranslators(DATA_PATH,"CGM1.translators")
    if not translators:  translators = settings["Translators"]

    # --------------------------MODELLING PROCESSING -----------------------
    acqGait = cgm1.fitting(model,DATA_PATH, reconstructFilenameLabelled,
        translators,
        markerDiameter,
        pointSuffix,
        mfpa,momentProjection)

    # ----------------------SAVE-------------------------------------------
    # Todo: pyCGM2 model :  cpickle doesn t work. Incompatibility with Swig. ( see about BTK wrench)

    # new static file
    if args.fileSuffix is not None:
        btkTools.smartWriter(acqGait, str(DATA_PATH+reconstructFilenameLabelled[:-4]+"-modelled-"+args.fileSuffix+".c3d"))
    else:
        btkTools.smartWriter(acqGait, str(DATA_PATH+reconstructFilenameLabelled[:-4]+"-modelled.c3d"))
