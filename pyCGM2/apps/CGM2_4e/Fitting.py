# -*- coding: utf-8 -*-
import os
import logging
import argparse
import matplotlib.pyplot as plt

# pyCGM2 settings
import pyCGM2
pyCGM2.CONFIG.setLoggingLevel(logging.INFO)



# pyCGM2 libraries
from pyCGM2.Tools import btkTools
from pyCGM2.Model.CGM2.coreApps import cgmUtils, cgm2_4e
from pyCGM2.Utils import files

if __name__ == "__main__":
    DEBUG = False

    parser = argparse.ArgumentParser(description='cgm2.4e Fitting')
    parser.add_argument('--trial', type=str,  required=True, help='static c3d')
    parser.add_argument('--subject',type=str, required=True,  help='subject')
    parser.add_argument('--proj', type=str, help='Moment Projection. Choice : Distal, Proximal, Global')
    parser.add_argument('-mfpa',type=str,  help='manual assignment of force plates')
    parser.add_argument('-md','--markerDiameter', type=float, help='marker diameter')
    parser.add_argument('-ps','--pointSuffix', type=str, help='suffix of model outputs')
    parser.add_argument('--check', action='store_true', help='force model output suffix')
    parser.add_argument('--noIk', action='store_true', help='cancel inverse kinematic')
    parser.add_argument('-fs','--fileSuffix', type=str, help='suffix of output file')
    parser.add_argument('--DEBUG', action='store_true', help='debug model')
    args = parser.parse_args()

    # --------------------------GLOBAL SETTINGS ------------------------------------
    # global setting ( in user/AppData)
    settings = files.openJson(pyCGM2.CONFIG.PYCGM2_APPDATA_PATH,"CGM2_4-Expert-pyCGM2.settings")

    # --------------------------CONFIG ------------------------------------
    subject = args.subject

    argsManager = cgmUtils.argsManager_cgm(settings,args)
    markerDiameter = argsManager.getMarkerDiameter()
    pointSuffix = argsManager.getPointSuffix("cgm2_4e")
    momentProjection =  argsManager.getMomentProjection()
    mfpa = argsManager.getManualForcePlateAssign()

    # --------------------------LOADING ------------------------------------
    if args.DEBUG:
        DATA_PATH = pyCGM2.CONFIG.TEST_DATA_PATH + "CGM2\\cgm2.4\\medial\\"
        reconstructFilenameLabelled = "Gait Trial 01.c3d"
        args.fileSuffix="cgm2_4e"

    else:
        DATA_PATH =os.getcwd()+"\\"
        reconstructFilenameLabelled = args.trial

    logging.info( "data Path: "+ DATA_PATH )
    logging.info( "calibration file: "+ reconstructFilenameLabelled)

    # --------------------pyCGM2 MODEL ------------------------------
    model = files.loadModel(DATA_PATH,subject)

    # --------------------------CHECKING -----------------------------------
    # check model is the CGM1
    logging.info("loaded model : %s" %(model.version ))
    if model.version != "CGM2.4e":
        raise Exception ("%s-pyCGM2.model file was not calibrated from the CGM2.4e calibration pipeline"%model.version)

        # --------------------------SESSION INFOS ------------------------------------

    #  translators management
    translators = files.getTranslators(DATA_PATH,"CGM2_4.translators")
    if not translators:  translators = settings["Translators"]

    # --------------------------MODELLING PROCESSING -----------------------
    finalAcqGait = cgm2_4e.fitting(model,DATA_PATH, reconstructFilenameLabelled,
            translators,settings,
            ik_flag,markerDiameter,
            pointSuffix,
            mfpa,
            momentProjection)

    # ----------------------SAVE-------------------------------------------
    # Todo: pyCGM2 model :  cpickle doesn t work. Incompatibility with Swig. ( see about BTK wrench)

    # new static file
    if args.fileSuffix is not None:
        btkTools.smartWriter(finalAcqGait, str(DATA_PATH+reconstructFilenameLabelled[:-4]+"-modelled-"+args.fileSuffix+".c3d"))
    else:
        btkTools.smartWriter(finalAcqGait, str(DATA_PATH+reconstructFilenameLabelled[:-4]+"-modelled.c3d"))