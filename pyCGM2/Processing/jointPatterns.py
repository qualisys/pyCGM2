# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import logging
import matplotlib.pyplot as plt
from collections import OrderedDict

from pyCGM2.Tools import exportTools
from pyCGM2.Signal.detect_peaks import detect_peaks
from pyCGM2.Math import derivation

from pyCGM2.Processing import analysisHandler
import re

class JointPatternFilter(object):
    """
    """

    def __init__(self, jointPatternProcedure, analysis):

        self.m_procedure = jointPatternProcedure
        self.m_analysis = analysis


    def getValues(self):
        dataframeData = self.m_procedure.detectValue(self.m_analysis)
        return dataframeData

    def getPatterns(self):
        data = self.m_procedure.detectValue(self.m_analysis)
        dataframePattern = self.m_procedure.detectPattern()
        return dataframePattern


class XlsJointPatternProcedure(object):


    def __init__(self,xlsFiles,pointSuffix=None):

        self.pointSuffix = str("_"+pointSuffix)  if pointSuffix is not None else ""
        self.m_xls = pd.ExcelFile(xlsFiles)
        self.data = None
        self.patterns = None

    def _getFrameLimits(self,cyclePeriod,context,data):

        phases = analysisHandler.getPhases(data)

        if cyclePeriod == "CYCLE":
            frameLimits = [0, 100]
        elif cyclePeriod in ["ST","SW","DS1","SS","eSS","mSS","lSS","eSW","mSW","lSW"]:
            frameLimits = phases[context,cyclePeriod]
        elif ("->" in cyclePeriod):
            separator = cyclePeriod.find("->")
            before = cyclePeriod[:separator]
            after = cyclePeriod[separator+2:]
            frameLimits = [phases[context, before][0], phases[context, after][1]]
        return frameLimits

    def _applyStatus(self,value,limits,status):

        limits = limits.split(",")
        status = status.split(",")

        if value<float(limits[0]):
            return status[0]
        elif value>float(limits[0]) and value<float(limits[1]):
            return status[1]
        elif value>float(limits[1]):
            return status[2]


    def _applyMethod(self,values,method,iArgs,frame0):
        if method == "mean":
            val = np.mean(values)
        elif method == "range":
            val = np.abs( np.max(values) - np.min(values))
        elif method == "min":
            val = np.min(values)
        elif method == "max":
            val = np.max(values)
        elif method == "timing-find":
            arg = float(iArgs)
            f = values
            g = np.ones(len(values))*arg
            idx = np.argwhere(np.diff(np.sign(f - g)) != 0).reshape(-1) + 0

            # -- display curve
            # x = np.arange(0, len(values))
            # plt.plot( f, '-+')
            # plt.plot( g, '-')
            # plt.plot(x[idx], f[idx], 'ro')
            # plt.show()

            if idx.shape[0] == 0:
                val = "NA"
            else:
                val= frame0 + idx[0]


        elif method == "threshold":
            args = iArgs.split(",")
            n = len(values)
            count=0
            val = "False"
            for value in values:
                if args[1] == "greater":
                    if value > float(args[0]):
                        count+=1
                if args[1] == "lesser":
                    if value < float(args[0]):
                        count+=1

            percentage = (count/n)/100
            if percentage >= float(args[2]):
                val = "True"

        elif method == "getValue":
            index = int(iArgs)
            val = values[index]

        elif method == "timing-min":
            val = frame0+np.argmin(values)

        elif method == "timing-max":
            val = frame0+ np.argmax(values)

        elif method == "slope":
            val = values[-1] - values[0]


        elif method == "peak":
            args = iArgs.split(",")
            indexes = detect_peaks(values, mph=float(args[0]), mpd=float(args[1]),  show = False, valley=False)
            if indexes.shape[0]  > 2:
                val = "True"
            else:
                val = "False"
        else:
            val = "NA"
        return val




    def detectValue(self,analysis):

        xlsData = self.m_xls.parse("data")

        # init new collumns
        xlsData["Value"] = "NA"
        xlsData["ValueStatus"] = "NA"

        for index in xlsData.index:
            row = xlsData.iloc[index,:]

            context = row["Context"] # str
            variable = row["Variable"]+self.pointSuffix
            plan = int(row["Plan"])
            derivate = int(row["derivate"])
            cyclePeriod = row["CyclePeriod"]
            method = row["Method"]
            args = row["MethodArgument"]
            limits = row["Ranges"]
            status = row["status [lesser,within,greater]"]

            if row["Domain"] == "Kinematics":
                data = analysis.kinematicStats
            elif row["Domain"] == "Kinetics":
                data = analysis.kineticStats

            value = "NA"
            if data.data!={}:
                if (variable,context) in data.data:
                    frames = self._getFrameLimits(cyclePeriod,context,data)
                    values  = data.data[variable,context]["mean"][frames[0]:frames[1]+1,plan]
                    value = self._applyMethod(values,method,args,frames[0])
                else:
                    logging.warning("[pyGM2] :row (%i) -  key [%s,%s] not found in analysis data instance" %(index,variable,context) )


            if value is not "NA":
                if (value == "False" or value == "True"):
                    valueStatus = value
                else:
                    valueStatus = self._applyStatus(value,limits,status)
            else:
                valueStatus = "NA"

            xlsData.set_value(index,"Value", value)
            xlsData.set_value(index,"ValueStatus", valueStatus)

            self.data = xlsData

        return xlsData

    def detectPattern(self):

        xlsPatterns = self.m_xls.parse("patterns")
        xlsPatterns["Success"] = "NA"

        #index = 1
        for index in xlsPatterns.index:
            row = xlsPatterns.iloc[index,:]

            primaries=list()
            secondaries=list()

            criteria = row["Criteria"]

            criterias = criteria.split("+")
            for it in criterias:
                if  "(" not in it:
                    status = re.findall( "\[(.*?)\]" ,it )[0]
                    ide = re.findall("\#(\d)",it)[0]
                    primaries.append({'status': status, 'ide': int(ide)})
                else:
                    bracket =  re.findall( "\((.*?)\)" ,it )[0]
                    score = re.findall(",(\d)", bracket)[0]
                    dict2 = {"score":int(score), "case" : list()}
                    casesStr = re.findall("(.*?),",bracket)[0]
                    cases = casesStr.split("|")
                    for case in cases:
                        status = re.findall( "\[(.*?)\]" ,it )[0]
                        ide = re.findall("\#(\d)",it)[0]
                        dict2["case"].append( {'status': status, 'ide': int(ide)})
                    secondaries.append(dict2)

            # criteria test
            flag1=True
            if primaries != []:
                for dict1It in primaries:
                    rowData = self.data[self.data["Id"] == dict1It["ide"]]
                    indexSelect = rowData.index[0]
                    if not rowData["ValueStatus"][indexSelect] !=  dict1It["status"]:
                        flag1= False
                        break

            if secondaries != []:
                flag2 = True
                for it in secondaries:
                    score = it["score"]
                    count =0
                    for dict2It in it["case"]:
                        rowData = self.data[self.data["Id"] == dict2It["ide"]]
                        indexSelect = rowData.index[0]
                        if rowData["ValueStatus"][indexSelect] ==  dict2It["status"]:
                            count+=1
                    if count<score:
                        flag2 = False
                        break

            # final
            if secondaries == []:
                if flag1:
                    xlsPatterns.set_value(index,"Success", "TRUE")
                else:
                    xlsPatterns.set_value(index,"Success", "FALSE")

            if primaries == []:
                if flag2:
                    xlsPatterns.set_value(index,"Success", "TRUE")
                else:
                    xlsPatterns.set_value(index,"Success", "FALSE")

            if primaries != [] and secondaries != []:
                if flag1 and flag2:
                    xlsPatterns.set_value(index,"Success", "TRUE")
                if flag1 and not flag2:
                    xlsPatterns.set_value(index,"Success", "partial-primary")
                if not flag1 and flag2:
                    xlsPatterns.set_value(index,"Success", "partial-secondary")
                if not flag1 and not flag2:
                    xlsPatterns.set_value(index,"Success", "FALSE")

        self.patterns = xlsPatterns

        return  self.patterns