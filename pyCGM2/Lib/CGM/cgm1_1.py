# -*- coding: utf-8 -*-
import logging

# pyCGM2 libraries
from pyCGM2.Tools import btkTools
from pyCGM2 import enums

from pyCGM2.Model import modelFilters, bodySegmentParameters
from pyCGM2.Model.CGM2 import cgm
from pyCGM2.Model.CGM2 import decorators
from pyCGM2.ForcePlates import forceplates
from pyCGM2.Processing import progressionFrame
from pyCGM2.Signal import signal_processing
from pyCGM2.Anomaly import AnomalyFilter, AnomalyDetectionProcedure


def calibrate(DATA_PATH,calibrateFilenameLabelled,translators,
              required_mp,optional_mp,
              leftFlatFoot,rightFlatFoot,headFlat,markerDiameter,
              pointSuffix,**kwargs):

    """
    Calibration of the CGM1.1

    :param DATA_PATH [str]: path to your data
    :param calibrateFilenameLabelled [str]: c3d file
    :param translators [dict]:  translators to apply
    :param required_mp [dict]: required anthropometric data
    :param optional_mp [dict]: optional anthropometric data (ex: LThighOffset,...)
    :param leftFlatFoot [bool]: enable of the flat foot option for the left foot
    :param rightFlatFoot [bool]: enable of the flat foot option for the right foot
    :param headFlat [bool]: enable of the head flat  option
    :param markerDiameter [double]: marker diameter (mm)
    :param pointSuffix [str]: suffix to add to model outputs

    """
    # --------------------------ACQUISITION ------------------------------------

    # ---btk acquisition---
    if "forceBtkAcq" in kwargs.keys():
        acqStatic = kwargs["forceBtkAcq"]
    else:
        acqStatic = btkTools.smartReader((DATA_PATH+calibrateFilenameLabelled))

    btkTools.checkMultipleSubject(acqStatic)
    if btkTools.isPointExist(acqStatic,"SACR"):
        translators["LPSI"] = "SACR"
        translators["RPSI"] = "SACR"
        logging.info("[pyCGM2] Sacrum marker detected")

    acqStatic =  btkTools.applyTranslators(acqStatic,translators)

    trackingMarkers = cgm.CGM1.LOWERLIMB_TRACKING_MARKERS + cgm.CGM1.THORAX_TRACKING_MARKERS+ cgm.CGM1.UPPERLIMB_TRACKING_MARKERS
    actual_trackingMarkers,phatoms_trackingMarkers = btkTools.createPhantoms(acqStatic, trackingMarkers)

    vff = acqStatic.GetFirstFrame()
    vlf = acqStatic.GetLastFrame()
    # vff,vlf = btkTools.getFrameBoundaries(acqStatic,actual_trackingMarkers)
    flag = btkTools.getValidFrames(acqStatic,actual_trackingMarkers,frameBounds=[vff,vlf])

    gapFlag = btkTools.checkGap(acqStatic,actual_trackingMarkers,frameBounds=[vff,vlf])
    if gapFlag:
        raise Exception("[pyCGM2] Calibration aborted. Gap find during interval [%i-%i]. Crop your c3d " %(vff,vlf))

    # --------------------ANOMALY------------------------------
    # --Check MP
    adap = AnomalyDetectionProcedure.AnthropoDataAnomalyProcedure( required_mp)
    adf = AnomalyFilter.AnomalyDetectionFilter(None,None,adap)
    anomaly = adf.run()

    # --marker presence
    markersets = [cgm.CGM1.LOWERLIMB_TRACKING_MARKERS , cgm.CGM1.THORAX_TRACKING_MARKERS, cgm.CGM1.UPPERLIMB_TRACKING_MARKERS]
    for markerset in markersets:
        mpdp = AnomalyDetectionProcedure.MarkerPresenceDetectionProcedure( markerset,verbose=False)
        adf = AnomalyFilter.AnomalyDetectionFilter(acqStatic,calibrateFilenameLabelled,mpdp)
        anomaly = adf.run()
        if anomaly["Output"]["In"] !=[] and anomaly["Output"]["Out"]!=[]:
            for markerOut in anomaly["Output"]["Out"]:
                logging.warning("[pyCGM2-Anomaly]  marker [%s] - not exist in the file [%s]"%(markerOut, calibrateFilenameLabelled))

        # --marker outliers
        # if anomaly["Output"]["In"] !=[]:
        #     madp = AnomalyDetectionProcedure.MarkerAnomalyDetectionRollingProcedure( anomaly["Output"]["In"], plot=False, window=10,threshold = 3)
        #     adf = AnomalyFilter.AnomalyDetectionFilter(acqStatic,calibrateFilenameLabelled,madp)
        #     anomaly = adf.run()
        #     anomalyIndexes = anomaly["Output"]


    # --------------------MODELLING------------------------------

    # ---detectedCalibrationMethods----
    dcm= cgm.CGM.detectCalibrationMethods(acqStatic)

    # ---definition---
    model=cgm.CGM1()
    model.setVersion("CGM1.1")
    model.configure(acq=acqStatic,detectedCalibrationMethods=dcm)
    model.addAnthropoInputParameters(required_mp,optional=optional_mp)

    if dcm["Left Knee"] == enums.JointCalibrationMethod.KAD: actual_trackingMarkers.append("LKNE")
    if dcm["Right Knee"] == enums.JointCalibrationMethod.KAD: actual_trackingMarkers.append("RKNE")
    model.setStaticTrackingMarkers(actual_trackingMarkers)

    # --store calibration parameters--
    model.setStaticFilename(calibrateFilenameLabelled)
    model.setCalibrationProperty("leftFlatFoot",leftFlatFoot)
    model.setCalibrationProperty("rightFlatFoot",rightFlatFoot)
    model.setCalibrationProperty("headFlat",headFlat)
    model.setCalibrationProperty("markerDiameter",markerDiameter)



    # --------------------------STATIC CALBRATION--------------------------
    scp=modelFilters.StaticCalibrationProcedure(model) # load calibration procedure

    # ---initial calibration filter----
    modelFilters.ModelCalibrationFilter(scp,acqStatic,model,
                                        leftFlatFoot = leftFlatFoot,
                                        rightFlatFoot = rightFlatFoot,
                                        headFlat= headFlat,
                                        markerDiameter = markerDiameter,
                                        ).compute()
    # ---- Decorators -----
    decorators.applyBasicDecorators(dcm, model,acqStatic,optional_mp,markerDiameter)

    # ----Final Calibration filter if model previously decorated -----
    if model.decoratedModel:
        # initial static filter
        modelFilters.ModelCalibrationFilter(scp,acqStatic,model,
                           leftFlatFoot = leftFlatFoot, rightFlatFoot = rightFlatFoot,
                           headFlat= headFlat,
                           markerDiameter=markerDiameter).compute()


    # ----------------------CGM MODELLING----------------------------------
    # ----motion filter----
    # notice : viconCGM1compatible option duplicate error on Construction of the foot coordinate system

    modMotion=modelFilters.ModelMotionFilter(scp,acqStatic,model,enums.motionMethod.Determinist,
                                              markerDiameter=markerDiameter)
    modMotion.compute()

    # ----progression Frame----
    progressionFlag = False
    if btkTools.isPointsExist(acqStatic, ['LASI', 'RASI', 'RPSI', 'LPSI'],ignorePhantom=False):
        logging.info("[pyCGM2] - progression axis detected from Pelvic markers ")
        pfp = progressionFrame.PelvisProgressionFrameProcedure()
        pff = progressionFrame.ProgressionFrameFilter(acqStatic,pfp)
        pff.compute()
        progressionAxis = pff.outputs["progressionAxis"]
        globalFrame = pff.outputs["globalFrame"]
        forwardProgression = pff.outputs["forwardProgression"]
        progressionFlag = True
    elif btkTools.isPointsExist(acqStatic, ['C7', 'T10', 'CLAV', 'STRN'],ignorePhantom=False) and not progressionFlag:
        logging.info("[pyCGM2] - progression axis detected from Thoracic markers ")
        pfp = progressionFrame.ThoraxProgressionFrameProcedure()
        pff = progressionFrame.ProgressionFrameFilter(acqStatic,pfp)
        pff.compute()
        progressionAxis = pff.outputs["progressionAxis"]
        globalFrame = pff.outputs["globalFrame"]
        forwardProgression = pff.outputs["forwardProgression"]

    else:
        globalFrame = "XYZ"
        progressionAxis = "X"
        forwardProgression = True
        logging.error("[pyCGM2] - impossible to detect progression axis - neither pelvic nor thoracic markers are present. Progression set to +X by default ")


    if "displayCoordinateSystem" in kwargs.keys() and kwargs["displayCoordinateSystem"]:
        csp = modelFilters.ModelCoordinateSystemProcedure(model)
        csdf = modelFilters.CoordinateSystemDisplayFilter(csp,model,acqStatic)
        csdf.setStatic(False)
        csdf.display()

    if "noKinematicsCalculation" in kwargs.keys() and kwargs["noKinematicsCalculation"]:
        logging.warning("[pyCGM2] No Kinematic calculation done for the static file")
        return model, acqStatic
    else:
        #---- Joint kinematics----
        # relative angles
        modelFilters.ModelJCSFilter(model,acqStatic).compute(description="vectoriel", pointLabelSuffix=pointSuffix)

        modelFilters.ModelAbsoluteAnglesFilter(model,acqStatic,
                                               segmentLabels=["Left Foot","Right Foot","Pelvis","Thorax","Head"],
                                                angleLabels=["LFootProgress", "RFootProgress","Pelvis","Thorax", "Head"],
                                                eulerSequences=["TOR","TOR", "ROT","YXZ","TOR"],
                                                globalFrameOrientation = globalFrame,
                                                forwardProgression = forwardProgression).compute(pointLabelSuffix=pointSuffix)

        # BSP model
        bspModel = bodySegmentParameters.Bsp(model)
        bspModel.compute()

        modelFilters.CentreOfMassFilter(model,acqStatic).compute(pointLabelSuffix=pointSuffix)

        return model, acqStatic



def fitting(model,DATA_PATH, reconstructFilenameLabelled,
    translators,
    markerDiameter,
    pointSuffix,
    mfpa,
    momentProjection,**kwargs):

    """
    Fitting of the CGM1.1

    :param model [str]: pyCGM2 model previously calibrated
    :param DATA_PATH [str]: path to your data
    :param reconstructFilenameLabelled [string list]: c3d files
    :param translators [dict]:  translators to apply
    :param mfpa [str]: manual force plate assignement
    :param markerDiameter [double]: marker diameter (mm)
    :param pointSuffix [str]: suffix to add to model outputs
    :param momentProjection [str]: Coordinate system in which joint moment is expressed

    """
    # --------------------------ACQUISITION ------------------------------------

    # --- btk acquisition ----
    if "forceBtkAcq" in kwargs.keys():
        acqGait = kwargs["forceBtkAcq"]
    else:
        acqGait = btkTools.smartReader((DATA_PATH + reconstructFilenameLabelled))

    btkTools.checkMultipleSubject(acqGait)
    if btkTools.isPointExist(acqGait,"SACR"):
        translators["LPSI"] = "SACR"
        translators["RPSI"] = "SACR"
        logging.info("[pyCGM2] Sacrum marker detected")

    acqGait =  btkTools.applyTranslators(acqGait,translators)

    trackingMarkers = cgm.CGM1.LOWERLIMB_TRACKING_MARKERS + cgm.CGM1.THORAX_TRACKING_MARKERS+ cgm.CGM1.UPPERLIMB_TRACKING_MARKERS
    actual_trackingMarkers,phatoms_trackingMarkers = btkTools.createPhantoms(acqGait, trackingMarkers)
    vff,vlf = btkTools.getFrameBoundaries(acqGait,actual_trackingMarkers)
    flag = btkTools.getValidFrames(acqGait,actual_trackingMarkers,frameBounds=[vff,vlf])

    # --------------------ANOMALY------------------------------

    for marker in actual_trackingMarkers:
        if marker not in model.getStaticTrackingMarkers():
            logging.warning("[pyCGM2-Anomaly]  marker [%s] - not used during static calibration - wrong kinematic for the segment attached to this marker. "%(marker))

    # --marker presence
    markersets = [cgm.CGM1.LOWERLIMB_TRACKING_MARKERS, cgm.CGM1.THORAX_TRACKING_MARKERS, cgm.CGM1.UPPERLIMB_TRACKING_MARKERS]
    for markerset in markersets:
        mpdp = AnomalyDetectionProcedure.MarkerPresenceDetectionProcedure( markerset,verbose=False)
        adf = AnomalyFilter.AnomalyDetectionFilter(acqGait,reconstructFilenameLabelled,mpdp)
        anomaly = adf.run()
        if anomaly["Output"]["In"] !=[] and anomaly["Output"]["Out"]!=[]:
            for markerOut in anomaly["Output"]["Out"]:
                logging.warning("[pyCGM2-Anomaly]  marker [%s] - not exist in the file [%s]"%(markerOut, reconstructFilenameLabelled))

        # --marker outliers
        # if anomaly["Output"]["In"] !=[]:
        #     madp = AnomalyDetectionProcedure.MarkerAnomalyDetectionRollingProcedure( anomaly["Output"]["In"], plot=False, window=10,threshold = 3)
        #     adf = AnomalyFilter.AnomalyDetectionFilter(acqGait,reconstructFilenameLabelled,madp, frameRange=[vff,vlf])
        #     anomaly = adf.run()
        #     anomalyIndexes = anomaly["Output"]

   # --------------------MODELLING------------------------------


    # filtering
    # -----------------------
    if "fc_lowPass_marker" in kwargs.keys() and kwargs["fc_lowPass_marker"]!=0 :
        fc = kwargs["fc_lowPass_marker"]
        order = 4
        if "order_lowPass_marker" in kwargs.keys():
            order = kwargs["order_lowPass_marker"]
        signal_processing.markerFiltering(acqGait,trackingMarkers,order=order, fc =fc)

    if "fc_lowPass_forcePlate" in kwargs.keys() and kwargs["fc_lowPass_forcePlate"]!=0 :
        fc = kwargs["fc_lowPass_forcePlate"]
        order = 4
        if "order_lowPass_forcePlate" in kwargs.keys():
            order = kwargs["order_lowPass_forcePlate"]
        signal_processing.forcePlateFiltering(acqGait,order=order, fc =fc)


    scp=modelFilters.StaticCalibrationProcedure(model) # procedure

    # ---Motion filter----
    modMotion=modelFilters.ModelMotionFilter(scp,acqGait,model,enums.motionMethod.Determinist,
                                              markerDiameter=markerDiameter)

    modMotion.compute()

    progressionFlag = False
    if btkTools.isPointExist(acqGait, 'LHEE',ignorePhantom=False) or btkTools.isPointExist(acqGait, 'RHEE',ignorePhantom=False):

        pfp = progressionFrame.PointProgressionFrameProcedure(marker="LHEE") \
            if btkTools.isPointExist(acqGait, 'LHEE',ignorePhantom=False) \
            else  progressionFrame.PointProgressionFrameProcedure(marker="RHEE")

        pff = progressionFrame.ProgressionFrameFilter(acqGait,pfp)
        pff.compute()
        progressionAxis = pff.outputs["progressionAxis"]
        globalFrame = pff.outputs["globalFrame"]
        forwardProgression = pff.outputs["forwardProgression"]
        progressionFlag = True

    elif btkTools.isPointsExist(acqGait, ['LASI', 'RASI', 'RPSI', 'LPSI'],ignorePhantom=False) and not progressionFlag:
        logging.info("[pyCGM2] - progression axis detected from Pelvic markers ")
        pfp = progressionFrame.PelvisProgressionFrameProcedure()
        pff = progressionFrame.ProgressionFrameFilter(acqGait,pfp)
        pff.compute()
        globalFrame = pff.outputs["globalFrame"]
        forwardProgression = pff.outputs["forwardProgression"]

        progressionFlag = True
    elif btkTools.isPointsExist(acqGait, ['C7', 'T10', 'CLAV', 'STRN'],ignorePhantom=False) and not progressionFlag:
        logging.info("[pyCGM2] - progression axis detected from Thoracic markers ")
        pfp = progressionFrame.ThoraxProgressionFrameProcedure()
        pff = progressionFrame.ProgressionFrameFilter(acqGait,pfp)
        pff.compute()
        progressionAxis = pff.outputs["progressionAxis"]
        globalFrame = pff.outputs["globalFrame"]
        forwardProgression = pff.outputs["forwardProgression"]

    else:
        globalFrame = "XYZ"
        progressionAxis = "X"
        forwardProgression = True
        logging.error("[pyCGM2] - impossible to detect progression axis - neither pelvic nor thoracic markers are present. Progression set to +X by default ")

    if "displayCoordinateSystem" in kwargs.keys() and kwargs["displayCoordinateSystem"]:
        csp = modelFilters.ModelCoordinateSystemProcedure(model)
        csdf = modelFilters.CoordinateSystemDisplayFilter(csp,model,acqGait)
        csdf.setStatic(False)
        csdf.display()

    if "NaimKneeCorrection" in kwargs.keys() and kwargs["NaimKneeCorrection"]:

        # Apply Naim 2019 method
        if type(kwargs["NaimKneeCorrection"]) is float:
            nmacp = modelFilters.Naim2019ThighMisaligmentCorrectionProcedure(model,"Both",threshold=(kwargs["NaimKneeCorrection"]))
        else:
            nmacp = modelFilters.Naim2019ThighMisaligmentCorrectionProcedure(model,"Both")
        mmcf = modelFilters.ModelMotionCorrectionFilter(nmacp)
        mmcf.correct()

        # btkTools.smartAppendPoint(acqGait,"LNaim",mmcf.m_procedure.m_virtual["Left"])
        # btkTools.smartAppendPoint(acqGait,"RNaim",mmcf.m_procedure.m_virtual["Right"])


    #---- Joint kinematics----
    # relative angles
    modelFilters.ModelJCSFilter(model,acqGait).compute(description="vectoriel", pointLabelSuffix=pointSuffix)


    modelFilters.ModelAbsoluteAnglesFilter(model,acqGait,
                                           segmentLabels=["Left Foot","Right Foot","Pelvis","Thorax","Head"],
                                            angleLabels=["LFootProgress", "RFootProgress","Pelvis","Thorax", "Head"],
                                            eulerSequences=["TOR","TOR", "ROT","YXZ","TOR"],
                                            globalFrameOrientation = globalFrame,
                                            forwardProgression = forwardProgression).compute(pointLabelSuffix=pointSuffix)

    #---- Body segment parameters----
    bspModel = bodySegmentParameters.Bsp(model)
    bspModel.compute()


    modelFilters.CentreOfMassFilter(model,acqGait).compute(pointLabelSuffix=pointSuffix)

    # Inverse dynamics
    if btkTools.checkForcePlateExist(acqGait):
        if model.m_bodypart != enums.BodyPart.UpperLimb:
            # --- force plate handling----
            # find foot  in contact
            mappedForcePlate = forceplates.matchingFootSideOnForceplate(acqGait,mfpa=mfpa)
            forceplates.addForcePlateGeneralEvents(acqGait,mappedForcePlate)
            logging.warning("Manual Force plate assignment : %s" %mappedForcePlate)

            # assembly foot and force plate
            modelFilters.ForcePlateAssemblyFilter(model,acqGait,mappedForcePlate,
                                     leftSegmentLabel="Left Foot",
                                     rightSegmentLabel="Right Foot").compute(pointLabelSuffix=pointSuffix)

            #---- Joint kinetics----
            idp = modelFilters.CGMLowerlimbInverseDynamicProcedure()
            modelFilters.InverseDynamicFilter(model,
                                 acqGait,
                                 procedure = idp,
                                 projection = momentProjection,
                                 globalFrameOrientation = globalFrame,
                                 forwardProgression = forwardProgression
                                 ).compute(pointLabelSuffix=pointSuffix)


            #---- Joint energetics----
            modelFilters.JointPowerFilter(model,acqGait).compute(pointLabelSuffix=pointSuffix)

    btkTools.cleanAcq(acqGait)
    btkTools.applyOnValidFrames(acqGait,flag)
    #---- zero unvalid frames ---
    # btkTools.applyValidFramesOnOutput(acqGait,validFrames)

    return acqGait
