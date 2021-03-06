# -*- coding: utf-8 -*-

"""
/***************************************************************************
 SAOLA
                                 A QGIS plugin
Spatial accessibility and optimal location analysis tool (SAOLA)
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-08-15
        copyright            : (C) 2019 by Ansup
        email                : ansup0402@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Ansup'
__date__ = '2019-08-15'
__copyright__ = '(C) 2019 by Ansup'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       # QgsFeatureSink,
                       QgsProcessingParameterVectorDestination,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterNumber,
                       QgsProject,
                       QgsProcessingParameterString,
                       QgsProcessingParameterFeatureSink)

# import tempfile
# import os
# import pathlib

# cur_dir = pathlib.Path(__file__).parent
# debugging = os.path.exists(os.path.join(cur_dir, 'debugmode'))
# if debugging:
#     file = open(os.path.join(cur_dir, 'debugmode'), "r")
#     cur_dir = file.readline()

class LivingSOCAccessibilitystraightAlgorithm(QgsProcessingAlgorithm):

    IN_CURSOC = 'IN_CURSOC'
    # IN_CURSOC_ID = 'IN_CURSOC_ID'

    IN_LIVINGAREA = 'IN_LIVINGAREA'
    # IN_LIVINGAREA_ID = 'IN_LIVINGAREA_ID'

    IN_POP = 'IN_POP'
    # IN_POP_ID = 'IN_POP_ID'
    IN_POP_CNTFID = 'IN_POP_CNTFID'
    IN_SITE = 'IN_SITE'

    IN_LIMIT_DIST = 'IN_LIMIT_DIST'
    OUTPUT = 'OUTPUT'

    IN_CALSSIFYNUM = 'IN_CALSSIFYNUM'

    # TEMP_DIR = None
    #
    #
    # debugging = False
    __debugging = False
    __cur_dir = None

    @property
    def debugmode(self):
        global __debugging
        return __debugging
        # return self.__debugging

    @debugmode.setter
    def debugmode(self, value):
        global __debugging
        __debugging = value
        # self.__debugging = value

    @property
    def temporaryDirectory(self):
        global __cur_dir
        return __cur_dir


    @temporaryDirectory.setter
    def temporaryDirectory(self, value):
        global __cur_dir
        __cur_dir = value





    def initAlgorithm(self, config):


        #분석지역
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.IN_SITE,
                '❖ ' + self.tr('Analysis Site'),
                [QgsProcessing.TypeVectorPolygon],
                optional=False)
        )

        # # 세생활권 인구 레이어
        # self.addParameter(
        #     QgsProcessingParameterFeatureSource(
        #         self.IN_LIVINGAREA,
        #         '❖ ' + self.tr('Sub-Neighborhood Unit'),
        #         [QgsProcessing.TypeVectorPolygon],
        #         optional=debugging)
        # )

        # 세생활권 인구 레이어
        self.addParameter(
            QgsProcessingParameterNumber(
                self.IN_LIVINGAREA,
                # "❖ " + self.tr('Facility Effective Service Coverage : If you input 0, it is regarded as the whole area'),
                "❖ " + self.tr('Sub-Neighborhood Unit(m)'),
                QgsProcessingParameterNumber.Integer,
                200, False, 10, 10000)  # 디폴트, 옵션, 미니멈, 맥시멈
        )



        # 기존 SOC 시설 레이어
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.IN_CURSOC,
                '❖ ' + self.tr('Located Neighborhood Facility'),
                [QgsProcessing.TypeVectorPoint],
                optional=False)
        )


        # 거주 인구 레이어
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.IN_POP,
                '❖ ' + self.tr('Resident Population'),
                [QgsProcessing.TypeVectorPoint],
                optional=False)
        )

        # 인구 필드
        self.addParameter(
            QgsProcessingParameterField(
                self.IN_POP_CNTFID,
                self.tr('Population Field'),
                None,
                self.IN_POP,
                QgsProcessingParameterField.Numeric,
                optional=False)
        )


        # 거리 조날
        self.addParameter(
            QgsProcessingParameterNumber(
                self.IN_LIMIT_DIST,
                # "❖ " + self.tr('Facility Effective Service Coverage : If you input 0, it is regarded as the whole area'),
                "❖ " + self.tr('Facility Effective Service Coverage'),
                QgsProcessingParameterNumber.Integer,
                1000, False, 0, 1000000)        #디폴트, 옵션, 미니멈, 맥시멈
        )

        # 등급
        self.addParameter(
            QgsProcessingParameterNumber(
                self.IN_CALSSIFYNUM,
                '❖ ' + self.tr('Analysis result grade number of sections: configurable range (2 ~ 100)'),
                QgsProcessingParameterNumber.Integer,
                10, False, 2, 100)  # 디폴트, 옵션, 미니멈, 맥시멈
        )

        # 최종 결과
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.OUTPUT,
                self.tr('Accessibility Analysis Results(Euclidean)')
            )
        )

    def onlyselectedfeature(self, parameters, context, paramID):
        layersource = self.parameterAsSource(parameters, paramID, context)
        layervertor = self.parameterAsVectorLayer(parameters, paramID, context)
        onlyselectedFeature = (layersource.featureCount() >= 0 and layervertor is None)
        return onlyselectedFeature

    def getLayerfromParameter(self, parameters, context, paramID):
        if self.onlyselectedfeature(parameters, context, paramID):
            return self.parameterAsSource(parameters, paramID, context), True
        else:
            return self.parameterAsSource(parameters, paramID, context), False

    def parameter2Dict(self, parameters, context):
        keyword = {}
        keyword['IN_CURSOC'], keyword['IN_CURSOC_ONLYSELECTED'] = self.getLayerfromParameter(parameters, context, self.IN_CURSOC)
        # keyword['IN_CURSOC_ID'] = self.parameterAsFields(parameters, self.IN_CURSOC_ID, context)[0]

        # keyword['IN_LIVINGAREA'], keyword['IN_LIVINGAREA_ONLYSELECTED'] = self.getLayerfromParameter(parameters,
        #                                                                                              context,
        #                                                                                              self.IN_LIVINGAREA)

        keyword['IN_LIVINGAREA'] = self.parameterAsInt(parameters, self.IN_LIVINGAREA, context)



        # keyword['IN_LIVINGAREA_ID'] = self.parameterAsFields(parameters, self.IN_LIVINGAREA_ID, context)[0]

        keyword['IN_POP'], keyword['IN_POP_ONLYSELECTED'] = self.getLayerfromParameter(parameters, context, self.IN_POP)
        # keyword['IN_POP_ID'] = self.parameterAsFields(parameters, self.IN_POP_ID, context)[0]
        keyword['IN_POP_CNTFID'] = self.parameterAsFields(parameters, self.IN_POP_CNTFID, context)[0]

        keyword['IN_SITE'], keyword['IN_SITE_ONLYSELECTED'] = self.getLayerfromParameter(parameters, context,
                                                                                         self.IN_SITE)


        keyword['IN_LIMIT_DIST'] = self.parameterAsInt(parameters, self.IN_LIMIT_DIST, context)
        keyword['IN_CALSSIFYNUM'] = self.parameterAsInt(parameters, self.IN_CALSSIFYNUM, context)
        keyword['OUTPUT'] = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)

        return keyword

    def check_userinput(self, parameters):
        # 사용자가 자주 실수하는 부분 파악하여 해당 함수 완성 할 것(노드, 링크 관계, PK필드 누락 등)
        isvailid = True
        return isvailid

    def processAlgorithm(self, parameters, context, feedback):

        params = self.parameter2Dict(parameters, context)

        # if self.check_userinput(parameters=params) == False: return None

        try:
            from .soc_locator_launcher import soc_locator_launcher
        except ImportError:
            from soc_locator_launcher import soc_locator_launcher

        # global debugging
        # global cur_dir

        # feedback.pushInfo("debug :{}".format(str(self.debugmode)))

        if self.debugmode:
            feedback.pushInfo("****** [START DEBUG] ******")
            feedback.pushInfo(self.temporaryDirectory)
            # feedback.pushInfo(self.TEMP_DIR)

        # launcher = soc_locator_launcher(feedback=feedback, context=context, parameters=params, debugging=debugging,
        #                                 workpath=cur_dir)
        launcher = soc_locator_launcher(feedback=feedback, context=context, parameters=params, debugging=self.debugmode,
                                        workpath=self.temporaryDirectory)

        out_vector = launcher.execute_accessibility_in_straight()
        return {self.OUTPUT: out_vector}


    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        # return 'Accessibility Analysis Model'
        return 'Accessibility Analysis(Euclidean)'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        # return 'Life-Friendly SOC Locator'
        # return 'Priority Supply Area Analysis'
        return 'Neighborhood Facility Accessibility Analysis'
    def tr(self, string):
        return QCoreApplication.translate('koala', string)

    def createInstance(self):
        return LivingSOCAccessibilitystraightAlgorithm()


