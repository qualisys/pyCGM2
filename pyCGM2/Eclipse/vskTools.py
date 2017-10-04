# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import string
import logging


def checkSetReadOnly(vskfilename):
    file0 = open(vskfilename,'r')
    content = file0.read()

    flag=True  if content.find('READONLY="true"') !=-1 else False
    print flag

    file0.close()

    if flag:
        logging.warning("read Only found")
        content2 = string.replace(content, 'READONLY="true"', 'READONLY="false"')

        with open(vskfilename, "w") as text_file:
            text_file.write(content2)



class Vsk(object):
    """

    """

    def __init__(self,file):

        self.m_file=file

        infile = open(file,"r")
        contents = infile.read()
        soup = BeautifulSoup(contents,'xml')

        self.m_soup = soup



    def getStaticParameterValue(self, label):

        staticParameters = self.m_soup.find_all('StaticParameter')
        for sp in staticParameters:
            if sp.attrs["NAME"] == label:
                return sp.attrs["VALUE"]


def getFromVskSubjectMp(vskInstance, resetFlag=False):

    required_mp={
    'Bodymass'   : float(vskInstance.getStaticParameterValue("Bodymass")),
    'LeftLegLength' :float(vskInstance.getStaticParameterValue("LeftLegLength")),
    'RightLegLength' : float(vskInstance.getStaticParameterValue("RightLegLength")),
    'LeftKneeWidth' : float(vskInstance.getStaticParameterValue("LeftKneeWidth")),
    'RightKneeWidth' : float(vskInstance.getStaticParameterValue("RightKneeWidth")),
    'LeftAnkleWidth' : float(vskInstance.getStaticParameterValue("LeftAnkleWidth")),
    'RightAnkleWidth' : float(vskInstance.getStaticParameterValue("RightAnkleWidth")),
    'LeftSoleDelta' : float(vskInstance.getStaticParameterValue("LeftSoleDelta")),
    'RightSoleDelta' : float(vskInstance.getStaticParameterValue("RightSoleDelta"))
    }

    if resetFlag:

        optional_mp={
        'InterAsisDistance'   : 0,
        'LeftAsisTrocanterDistance' : 0,
        'LeftTibialTorsion' : 0 ,
        'LeftThighRotation' : 0,
        'LeftShankRotation' : 0,
        'RightAsisTrocanterDistance' : 0,
        'RightTibialTorsion' :0 ,
        'RightThighRotation' : 0,
        'RightShankRotation' : 0
        }
    else:
        optional_mp={
        'InterAsisDistance'   : float(vskInstance.getStaticParameterValue("InterAsisDistance")),#0,
        'LeftAsisTrocanterDistance' : 0,#float(vskInstance.getStaticParameterValue("LeftAsisTrocanterDistance")),#0,
        'LeftTibialTorsion' : float(vskInstance.getStaticParameterValue("LeftTibialTorsion")),#0 ,
        'LeftThighRotation' : float(vskInstance.getStaticParameterValue("LeftThighRotation")),#0,
        'LeftShankRotation' : float(vskInstance.getStaticParameterValue("LeftShankRotation")),#0,
        'RightAsisTrocanterDistance' : 0,#float(vskInstance.getStaticParameterValue("RightAsisTrocanterDistance")),#0,
        'RightTibialTorsion' : float(vskInstance.getStaticParameterValue("RightTibialTorsion")),#0 ,
        'RightThighRotation' : float(vskInstance.getStaticParameterValue("RightThighRotation")),#0,
        'RightShankRotation' : float(vskInstance.getStaticParameterValue("RightShankRotation")),#0,
        }

    return required_mp,optional_mp