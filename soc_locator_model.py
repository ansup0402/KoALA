
import os
import pathlib

cur_dir = pathlib.Path(__file__).parent

#
from qgis.core import (
                    QgsVectorLayer,
#                     QgsFeatureRequest,
#                     QgsVectorFileWriter,
#                     QgsProcessingMultiStepFeedback,
#                     QgsProcessingFeatureSourceDefinition
                    )

import networkx as nx
import pandas as pd
import numpy as np

# from pandas import DataFrame


# from processing.core.Processing import Processing
# Processing.initialize()
# import processing


class soc_locator_model:

    def __init__(self, feedback, context, debugmode=False):
        try:
            from .qgsprocssing_utils import qgsprocessUtils as qgsutils
        except ImportError:
            from qgsprocssing_utils import qgsprocessUtils as qgsutils

        self.qgsutils = qgsutils(feedback=feedback, context=context, debugmode=debugmode)

        self.debugging = debugmode
        self.feedback = feedback
        self.context = context



        self.allshortestnodes = {}
        self.nxGraph = None
        self.__nodelayer = None
        self.__nodeID = ''
        self.__linklayer = None
        self.__toNodefield = ''
        self.__fromNodefield = ''
        self.__linklenfield = ''
        self.__linkSpeed = None
        self.__boundarylayer = None
        self.__potentiallayer = None
        self.__populationLayer = None
        self.__popSinglepartlayer = None

        self.__currentSOClayer = None
        self.__popcntField = ''
        self.__livingareaLayer = None
        self.__livinglyrID = ''
        self.__cutoff = 0
        self.__outofcutoff = 0
        self.__dfPop = None
        self.__dictFinalwithScore = {}
        self.__dtFinalwithsScore = None

        self.__currentSOCID = ''
        self.__potentialID = ''
        self.__poplyrID = ''

        self.__classify_count = 10

        # if debugmode:
        #     if not os.path.exists(os.path.join(cur_dir, 'temp')):
        #         os.makedirs(os.path.join(cur_dir, 'temp'))
        #
        #     import logging
        #     self.__logger = logging.getLogger("my")
        #     self.__logger.setLevel(logging.INFO)
        #
        #     logpath = os.path.join(cur_dir, 'temp/debugging.log')
        #     file_handler = logging.FileHandler(logpath)
        #     self.__logger.addHandler(file_handler)


    @property
    def boundary(self):
        return (self.__boundarylayer)
    @boundary.setter
    def boundary(self, value):
        self.__boundarylayer = value

    @property
    def classify_count(self):
        return (self.__classify_count)

    @classify_count.setter
    def classify_count(self, value):
        self.__classify_count = value

    @property
    def cutoff(self):
        return (self.__cutoff)
    @cutoff.setter
    def cutoff(self, value):
        if value is None:
            self.__cutoff = 0
        else:
            self.__cutoff = value

    @property
    def outofcutoff(self):
        return (self.__outofcutoff)
    @outofcutoff.setter
    def outofcutoff(self, value):
        self.__outofcutoff = value

    @property
    def currentSOC(self):
        return (self.__currentSOClayer)
    @currentSOC.setter
    def currentSOC(self, value):
        self.__currentSOClayer = value

    @property
    def currentSOCID(self):
        return (self.__currentSOCID)
    @currentSOCID.setter
    def currentSOCID(self, value):
        self.__currentSOCID = value


    @property
    def potentiallayer(self):
        return (self.__potentiallayer)
    @potentiallayer.setter
    def potentiallayer(self, value):
        self.__potentiallayer = value

    @property
    def potentialID(self):
        return (self.__potentialID)
    @potentialID.setter
    def potentialID(self, value):
        self.__potentialID = value


    @property
    def populationLayer(self):
        return (self.__populationLayer)
    @populationLayer.setter
    def populationLayer(self, value):
        self.__populationLayer = value


    @property
    def popIDField(self):
        return (self.__poplyrID)
    @popIDField.setter
    def popIDField(self, value):
        self.__poplyrID = value


    @property
    def popcntField(self):
        return (self.__popcntField)
    @popcntField.setter
    def popcntField(self, value):
        self.__popcntField = value


    @property
    def livingareaLayer(self):
        return (self.__livingareaLayer)

    @livingareaLayer.setter
    def livingareaLayer(self, value):
        self.__livingareaLayer = value

    @property
    def livingareaIDField(self):
        return (self.__livinglyrID)

    @livingareaIDField.setter
    def livingareaIDField(self, value):
        self.__livinglyrID = value


    @property
    def nodelayer(self):
        return (self.__nodelayer)
    @nodelayer.setter
    def nodelayer(self, value):
        self.__nodelayer = value

    @property
    def nodeIDfield(self):
        return (self.__nodeID)
    @nodeIDfield.setter
    def nodeIDfield(self, value):
        self.__nodeID = value


    @property
    def linklayer(self):
        return (self.__linklayer)
    @linklayer.setter
    def linklayer(self, value):
        self.__linklayer = value

    @property
    def linkTonodefield(self):
        return (self.__toNodefield)
    @linkTonodefield.setter
    def linkTonodefield(self, value):
        self.__toNodefield = value

    @property
    def linkFromnodefield(self):
        return (self.__fromNodefield)
    @linkFromnodefield.setter
    def linkFromnodefield(self, value):
        self.__fromNodefield = value

    @property
    def linklengthfield(self):
        return (self.__linklenfield)
    @linklengthfield.setter
    def linklengthfield(self, value):
        self.__linklenfield = value

    @property
    def linkSpeed(self):
        return (self.__linkSpeed)

    @linkSpeed.setter
    def linkSpeed(self, value):
        self.__linkSpeed = value




    def setProgressSubMsg(self, msg):
        import datetime
        # using now() to get current time
        now = datetime.datetime.now()

        # snow = "%04d-%02d-%02d %02d:%02d:%02d:%02d" % (now.year, now.month, now.day, now.hour, now.minute, now.second, now.microsecond)
        snow = "%04d-%02d-%02d %02d:%02d:%02d" % (now.year, now.month, now.day, now.hour, now.minute, now.second)
        # self.feedback.pushInfo("%s..........  %s" % (snow, msg))
        self.feedback.pushDebugInfo("%s..........  %s" % (snow, msg))
        # self.feedback.pushConsoleInfo(msg)

    def initNXGraph(self, isoneway=True):
        if isoneway:
            self.nxGraph = nx.DiGraph()
        else:
            self.nxGraph = nx.Graph()



    # qgis의 내부 함수를 통해 데이터를 변형하는 부분
    def writeAsVectorLayer(self, layername):
        return self.qgsutils.writeAsVectorLayer(layername=layername)

    def bufferwithQgis(self, input, onlyselected, distance, output='TEMPORARY_OUTPUT'):
        return self.qgsutils.bufferwithQgis(input=input, onlyselected=onlyselected, distance=distance, output=output)

    def createGridfromLayer(self, sourcelayer, gridsize, output='TEMPORARY_OUTPUT'):
        return self.qgsutils.createGridfromLayer(sourcelayer=sourcelayer, gridsize=gridsize, output=output)

    def clipwithQgis(self, input, onlyselected, overlay, output='TEMPORARY_OUTPUT'):
        return self.qgsutils.clipwithQgis(input=input, onlyselected=onlyselected, overlay=overlay, output=output)


    def dissolvewithQgis(self, input, onlyselected, field=None, output='TEMPORARY_OUTPUT'):
        return self.qgsutils.dissolvewithQgis(input=input, onlyselected=onlyselected, field=field, output=output)

    def nearesthubpoints(self, input, onlyselected, sf_hub, hubfield, output='TEMPORARY_OUTPUT'):
        return self.qgsutils.nearesthubpoints(input=input, onlyselected=onlyselected, sf_hub=sf_hub, hubfield=hubfield, output=output)


    def countpointsinpolygon(self, polylayer, pointslayer, field, weight=None, classfield=None, output='TEMPORARY_OUTPUT'):
        return self.qgsutils.countpointsinpolygon(polygons=polylayer,
                                                  points=pointslayer,
                                                  field=field,
                                                  weight=weight,
                                                  classfield=classfield,
                                                  output=output)


    def intersection(self, input, inputfields, inputonlyseleceted, overlay, overayprefix, overlayer_fields=None, output='TEMPORARY_OUTPUT'):
        return self.qgsutils.intersection(input=input,
                                          inputfields=inputfields,
                                          inputonlyseleceted=inputonlyseleceted,
                                          overlay=overlay,
                                          overayprefix=overayprefix,
                                          overlayer_fields=overlayer_fields,
                                          output=output)

    def centroidlayer(self, input, allparts=False, output='TEMPORARY_OUTPUT'):
        return self.qgsutils.centroidlayer(input=input, onlyselected=False, allparts=allparts, output=output)

    def vectorlayer2ShapeFile(self, vectorlayer, output):
        return self.qgsutils.vectorlayer2ShapeFile(vectorlayer=vectorlayer, output=output, destCRS=vectorlayer.sourceCrs())

    def differencelayer(self, input, onlyselected, overlayer, overonlyselected, output):
        return self.qgsutils.differencelayer(input=input, onlyselected=onlyselected,
                                             overlay=overlayer, overonlyselected=overonlyselected,
                                             output=output)


    def addIDField(self, input, idfid, output='TEMPORARY_OUTPUT'):
        return self.qgsutils.fieldCalculate(input=input,
                                            fid=idfid,
                                            ftype=0,
                                            flen=10,
                                            fprecision=0,
                                            formula='$id',
                                            newfield=True,
                                            output=output)

    def createNodeEdgeInGraph(self):

        # Node layer를 이용한 node 추가 방법
        # allnodes = [feature.attribute(self.__nodeID) for feature in self.__nodelayer.getFeatures()]

        fnodes = []
        tnodes = []
        weights = []
        lengths = []

        tempNodes = []
        totalcnt = self.__linklayer.featureCount()
        i = 0
        for feature in self.__linklayer.getFeatures():
            i += 1
            if self.feedback.isCanceled(): return None
            self.feedback.setProgress(int(i / totalcnt * 100))

            tempNodes.append(feature.attribute(self.__fromNodefield))
            tempNodes.append(feature.attribute(self.__toNodefield))

            fnodes.append(feature.attribute(self.__fromNodefield))
            tnodes.append(feature.attribute(self.__toNodefield))

            length = feature.attribute(self.__linklenfield)

            if self.__linkSpeed is None:
                weights.append(length)
            else:
                speed = feature.attribute(self.__linkSpeed)
                if speed == 0: self.setProgressSubMsg("링크레이어의 속도 필드에 0값이 있습니다.")
                linktime = len/speed
                weights.append(linktime)

        allnodes = list(set(tempNodes))


        tmplink = tuple(zip(fnodes, tnodes, weights))
        self.nxGraph.add_nodes_from(allnodes)
        self.nxGraph.add_weighted_edges_from(tmplink)

        return self.nxGraph



    # Calculate the shortest distance and store the result in memory
    def shortestAllnodes(self, algorithm='dijkstra', output_alllink=None):
        self.feedback.setProgress(0)
        allNodes = None
        if output_alllink is not None: import pickle

        if self.__cutoff == 0:
            cutoff = None
        else:
            cutoff = self.__cutoff

        if self.debugging: self.setProgressSubMsg("[start] shortestAllnodes")

        if output_alllink is not None and os.path.exists(output_alllink):
            with open(output_alllink, 'rb') as handle:
                allNodes = pickle.load(handle)
        else:
            if algorithm.lower() == 'johnson':
                # johnson 는 cutoff 적용이 되지 않아 속도가 느림(차후 로직에서 한꺼번에 처리/해당 알고리즘 사용지 cutoff 로직 재확인 필요)
                allNodes = dict(nx.johnson(self.nxGraph, weight='weight'))
            elif algorithm.lower() == 'dijkstra':
                allNodes = dict(nx.all_pairs_dijkstra_path_length(self.nxGraph, weight='weight', cutoff=cutoff))
            elif algorithm.lower() == 'bellman':
                # bellman 는 cutoff 적용이 되지 않아 속도가 느림(차후 로직에서 한꺼번에 처리/해당 알고리즘 사용지 cutoff 로직 재확인 필요)
                allNodes = dict(nx.all_pairs_bellman_ford_path_length(self.nxGraph, weight='weight'))

            if output_alllink is not None:
                with open(output_alllink, 'wb') as handle:
                    pickle.dump(allNodes, handle, protocol=pickle.HIGHEST_PROTOCOL)

        if self.debugging: self.setProgressSubMsg("[END] shortestAllnodes")

        # 로그 파일을 쓰는 경우 일부 데이터만 쓸것(속도, 메모리 부분에서 상당히 분리함)
        # if self.debugging:
        #     self.__logger.info("allLink : %s" % str(allNodes))

        self.allshortestnodes = allNodes
        self.feedback.setProgress(100)
        return allNodes

    def get_Distance(self, fromNodeID, toNodeID):
        dis = None
        try:
            pairNode = self.allshortestnodes[fromNodeID]
            dis = pairNode[toNodeID]

            if (self.__cutoff is not None) and (self.__cutoff > 0) and (dis > self.__cutoff):
                dis = None
        except :
            dis = None

        return dis


    def get_alltargetSumofDistance(self, fromNodeID, svrNodeList):
        dis = None
        dict_distlist = self.get_allOfDistFromAlltarget(fromNodeID, svrNodeList)
        if len(dict_distlist) > 0: dis = sum(dict_distlist.values())
        return dis

    # 효율성과 접근성에서 사용 중
    def get_nearesttargetDistnace(self, fromNodeID, svrNodeList):

        dis = None

        dict_distlist = self.get_allOfDistFromAlltarget(fromNodeID, svrNodeList)

        if dict_distlist is not None:
            import operator
            sorteddict = sorted(dict_distlist.items(), key=operator.itemgetter(1))

            if len(sorteddict) > 0:
                if fromNodeID in svrNodeList:
                    # fromNode위치와 svrNode의 위치가 동일한 경우
                    dis = sorteddict[0][1]
                else:
                    if len(sorteddict) == 1:
                        # fromNode위치와 svrNode의 위치가 동일하지 않은 경우는 0번째는 자신 Node까지의 거리를 뜻함
                        dis = sorteddict[0][1]
                    else:
                        dis = sorteddict[1][1]

        return dis

    def get_allOfDistFromAlltarget(self, fromNodeID, alltargetNodeList):

        new_dict = {}
        try:
            pairNode = self.allshortestnodes[fromNodeID]
            if self.__cutoff == 0 or self.__cutoff is None:
                new_dict = {idx: val for idx, val in pairNode.items() if (idx in alltargetNodeList)}
            else:
                # new_dict = {idx: val for idx, val in pairNode.items() if (idx in alltargetNodeList) and (val <= self.__cutoff)}
                new_dict = {idx: self.__outofcutoff if val > self.__cutoff else val for idx, val in pairNode.items() if (idx in alltargetNodeList)}

        except:
            if self.debugging:
                # self.__logger.info("[get_AllDistanceFromNode] 노드 찾기 오류(디버깅용메시지) : %s" % fromNodeID)
                self.setProgressSubMsg("[get_AllDistanceFromNode] 노드 찾기 오류(디버깅용메시지) : %s" % fromNodeID)
            new_dict = None

        return new_dict



    def getPopdistmatrixDataLayer(self, targetlayer, targetlayerID, output):

        # 1) 싱글파트로 변경
        singlepop = self.__popSinglepartlayer
        singleTarget = targetlayer

        # # MultiPoint : 4
        if singlepop is None: singlepop = self.qgsutils.multiparttosingleparts(self.__populationLayer, False)
        if singleTarget.wkbType() == 4: singleTarget = self.qgsutils.multiparttosingleparts(targetlayer, False)

        # 잠재지역 분석시 활용하기 위해 저장
        self.__popSinglepartlayer = singlepop

        # 2) 거리 행렬 연산
        matrixtype = 2
        if (self.__cutoff is not None) and (self.__cutoff > 0): matrixtype = 0

        tmpoutput = ''
        if (self.debugging): tmpoutput = os.path.join(cur_dir, 'temp/popdistmatrix1_%s.shp' % targetlayer.sourceName())

        matrix_distance = self.qgsutils.distancematrix(input=singlepop,
                                                      inputonlyselected=False,
                                                      inputfield=self.popIDField,
                                                      target=singleTarget,
                                                      targetonlyseleted=False,
                                                      targetfield=targetlayerID,
                                                      matrixtype=matrixtype,
                                                      output=tmpoutput)

        resultlayer = matrix_distance

        # 3) 거리 조락 반영
        if(self.__cutoff is not None) and (self.__cutoff > 0):
            selecedlyr = self.qgsutils.selectbyexpression(input=matrix_distance,
                                                 expression='Distance <= %s' % (str(self.__cutoff)))

            resultlayer = self.qgsutils.saveselectedfeatrues(selecedlyr, output)

        return resultlayer



    def anal_AllCurSOC_straight(self):

        tmpoutput = ''
        if (self.debugging): tmpoutput = os.path.join(cur_dir, 'temp/AllCurSOC1.shp')
        matrixDisLayer = self.getPopdistmatrixDataLayer(targetlayer=self.__currentSOClayer,
                                                        targetlayerID=self.__currentSOCID,
                                                        output=tmpoutput)

        tmpoutput = ''
        if (self.debugging): tmpoutput = os.path.join(cur_dir, 'temp/AllCurSOC2')
        statstable = self.qgsutils.statisticsbycategories(input=matrixDisLayer,
                                                 onlyselected=False,
                                                 categoriesfields=['InputID'],
                                                 valuefield='Distance',
                                                 output=tmpoutput)

        tmpoutput = ''
        if (self.debugging): tmpoutput = os.path.join(cur_dir, 'temp/AllCurSOC3.shp')
        joinedpop = self.qgsutils.joinattributetable(input1=self.__popSinglepartlayer,
                                            input1onlyselected=False,
                                            field1=self.popIDField,
                                            input2=statstable,
                                            input2onlyselected=False,
                                            field2='InputID',
                                            prefix='M_',
                                            output=tmpoutput
                                            )

        if isinstance(joinedpop, str): joinedpop = self.qgsutils.writeAsVectorLayer(joinedpop)

        listPopID = []
        listPopCnt = []
        listPoptoSocDis = []

        singleTarget = self.__popSinglepartlayer
        targetcnt = singleTarget.featureCount()
        totalcnt = joinedpop.featureCount()
        i = 0

        for feature in joinedpop.getFeatures():
            i += 1
            if self.feedback.isCanceled(): return None
            self.feedback.setProgress(int(i / totalcnt * 100))

            listPopID.append(feature[self.popIDField])
            listPopCnt.append(feature[self.__popcntField])

            accval = 0
            if (self.__cutoff is not None) and (self.__cutoff > 0):
                accval = feature['M_SUM']
            else:
                accval = feature['M_MEAN'] * targetcnt

            # if str(accval).isnumeric() == False:
            if str(accval) is None or str(accval) == 'NULL':
                accval = 0

            # self.setProgressSubMsg("accval : %s[%s]" % (accval, type(accval)))
            listPoptoSocDis.append(accval)

        rawData = {self.__poplyrID: listPopID,
                   self.__popcntField: listPopCnt,
                   'ACC_SCORE': listPoptoSocDis}

        dfPopwidthDis = pd.DataFrame(rawData)

        # 왜 못찾지?
        dfPopwidthDis['ACC_SCORE'].fillna(0, inplace=True)
        # dfPopwidthDis.loc[dfPopwidthDis['ACC_SCORE'] == 'NULL', 'ACC_SCORE'] = 0

        if self.debugging:
            tempexcel = os.path.join(cur_dir, 'temp/matrix4_AllCurSOC.csv')
            dfPopwidthDis.to_csv(tempexcel)

        self.__dfPop = dfPopwidthDis

        return self.__dfPop






    def anal_AllCurSOC_network(self):
        dists = []
        i = 0
        errcnt = 0
        noerrcnt = 0

        svrNodeilst = [feature.attribute(self.__nodeID) for feature in self.__currentSOClayer.getFeatures()]
        if self.debugging:
            # self.__logger.info("svrNodeilst : %s" % str(svrNodeilst))
            self.setProgressSubMsg("svrNodeilst : %s" % str(svrNodeilst))

        listpopNode = []
        listpopCnt = []
        listpopAccscore = []
        calculatedNode = {}

        tmppoplayer = self.__populationLayer
        totalcnt = tmppoplayer.featureCount()
        for feature in tmppoplayer.getFeatures():
            i += 1
            if self.feedback.isCanceled(): return None
            self.feedback.setProgress(int(i / totalcnt * 100))

            popNodeid = str(feature[self.__nodeID])
            poppnt = feature[self.__popcntField]

            # get_AllDistanceFromNode 함수 적게 타도록 처리
            try:
                dis = calculatedNode[popNodeid]
            except:
                dis = self.get_alltargetSumofDistance(fromNodeID=popNodeid,
                                                      svrNodeList=svrNodeilst)
                if dis is None:
                    # todo 이 주석 내용 확인 후 삭제 필요
                    # get_alltargetSumofDistance함수 내에서 outofcutoff처리를 다 했기때문에, 분석지역안에 1건이라도 생활SOC가 있는 경우는 None알 수 없음
                    # self.__logger.info("[NODE-%s] 해당 인구데이터의 %sm 이내에는 현재 생활SOC가 없습니다." % (str(popNodeid), str(self.cutoff)))
                    self.setProgressSubMsg(
                        "[NODE-%s] 해당 인구데이터의 %sm 이내에는 현재 생활SOC가 없습니다." % (str(popNodeid), str(self.cutoff)))
                # if dis is None:
                #     errcnt += 1
                #     dis = 0
                # else:
                #     noerrcnt += 1

                calculatedNode[popNodeid] = dis

            listpopNode.append(popNodeid)
            listpopCnt.append(poppnt)
            listpopAccscore.append(dis)

        rawData = {self.nodeIDfield: listpopNode,
                   self.__popcntField: listpopCnt,
                   'ACC_SCORE': listpopAccscore}

        self.__dfPop = pd.DataFrame(rawData)

        if self.debugging: self.__dfPop.to_csv(os.path.join(cur_dir, 'temp/analyze_fromAllCurSOC.csv'))

        return self.__dfPop

    # todo [000] 너무 느리니 단계를 2개로 분리하자.
    # todo [000] 함수마다 임시파일명을 함수명_시리얼_일련번호로 통일시키지..
    def anal_AllPotenSOC_straight(self):

        # 1) 잠재적위치 레이어와 세생활권 인구레이어 distance matrix
        tmpoutput = ''
        if (self.debugging): tmpoutput = os.path.join(cur_dir, 'temp/AllPotenSOC1.shp')
        matrixDisLayer = self.getPopdistmatrixDataLayer(targetlayer=self.__potentiallayer,
                                                        targetlayerID=self.__potentialID,
                                                        output=tmpoutput)

        if isinstance(matrixDisLayer, str): matrixDisLayer = self.qgsutils.writeAsVectorLayer(matrixDisLayer)

        # 2) 거리 2차 dict 생성
        totalcnt = matrixDisLayer.featureCount()
        pot2popDists = {}
        i = 0
        # self.setProgressSubMsg(str(totalcnt))
        for feature in matrixDisLayer.getFeatures():
            i += 1
            if self.feedback.isCanceled(): return None
            self.feedback.setProgress(int(i / totalcnt * 100))

            potenID = int(feature['TargetID'])
            popID = int(feature['InputID'])
            if feature['Distance'] is None:
                distance = 0
            else:
                distance = int(feature['Distance'])

            try:
                toPopDists = pot2popDists[potenID]
                # 이미 있을 경우 현재값으로 변경한다..(실제로는 이런 경우 없음)
                toPopDists[popID] = distance
            except:
                toPopDists = {}
                toPopDists[popID] = distance
                pot2popDists[popID] = toPopDists

        # refac [999] 코드 리팩토링 필요
        try:
            tmppotenlayer = self.__potentiallayer
            potencnt = tmppotenlayer.featureCount()
            potenIDList = []
            potenEquityScore = []
            dictResultwithsScore = {}

            i = 0
            calculatedNode = {}
            tmpPopCopy = self.__dfPop.copy()

            for feature in tmppotenlayer.getFeatures():
                i += 1
                if self.feedback.isCanceled(): return None
                self.feedback.setProgress(int(i/potencnt * 100))

                ############# 이부분 다름 ##############################
                potenID = feature[self.__potentialID]
                potenIDList.append(potenID)
                ####################################################

                tmpPopCopy['NEW_DIS'] = 0
                try:
                    popDistances = pot2popDists[potenID]
                    # tmpPopCopy중에 해당되는 것만 값을 변경해주자..
                    for key, value in popDistances.items():
                        tmpPopCopy.loc[tmpPopCopy[self.__poplyrID] == key, "NEW_DIS"] = value

                except:
                    tmpPopCopy['NEW_DIS'] = 0

                dfsumOfacc = tmpPopCopy['ACC_SCORE'] + tmpPopCopy['NEW_DIS']

                tmpPopCopy['A'] = tmpPopCopy[self.__popcntField] * dfsumOfacc
                avg = tmpPopCopy['A'].mean()
                # tmpPopCopy['EQ_SCORE'] = np.sqrt((tmpPopCopy['A'] - avg) ** 2)
                tmpPopCopy['EQ_SCORE'] = ((tmpPopCopy['A'] - avg) ** 2) ** (1 / 2)

                sumofeqscore = tmpPopCopy['EQ_SCORE'].sum()
                potenEquityScore.append(int(sumofeqscore))
                dictResultwithsScore[potenID] = int(sumofeqscore)

            rawData = {self.__potentialID: potenIDList,
                       'EQ_SCORE': potenEquityScore}

            self.__dtFinalwithsScore = pd.DataFrame(rawData)
            self.__dictFinalwithScore = dictResultwithsScore

            return self.__dtFinalwithsScore

        except MemoryError as error:
            self.setProgressSubMsg(type(error))

    def anal_accessibilityCurSOC_straight(self):

        tmppoplayer = self.__populationLayer

        listpopID = []
        listpopCnt = []
        listlivingID = []
        listpopAccscore = []

        for feature in tmppoplayer.getFeatures():
            poplivingID = feature[self.__livinglyrID]
            popID = feature[self.__poplyrID]
            poppnt = feature[self.__popcntField]
            dis = feature['HubDist']

            if self.__cutoff > 0 and dis >= self.__cutoff:
                dis = self.__outofcutoff
            
            listlivingID.append(poplivingID)
            listpopID.append(popID)
            listpopCnt.append(poppnt)
            listpopAccscore.append(dis)

        rawData = {self.__poplyrID: listpopID,
                   self.__popcntField: listpopCnt,
                   self.__livinglyrID: listlivingID,
                   'DISTANCE': listpopAccscore}

        self.__dfPop = pd.DataFrame(rawData)

        return self.__dfPop


    def anal_accessibilityCurSOC_network(self):

        svrNodeilst = [feature.attribute(self.__nodeID) for feature in self.__currentSOClayer.getFeatures()]
        tmppoplayer = self.__populationLayer
        totalcnt = tmppoplayer.featureCount()

        listlivingID = []
        listpopID = []
        listpopNode = []
        listpopCnt = []
        listpopAccscore = []
        calculatedNode = {}

        i = 0
        errcnt = 0
        noerrcnt = 0
        for feature in tmppoplayer.getFeatures():
            i += 1
            if self.feedback.isCanceled(): return None
            self.feedback.setProgress(int(i / totalcnt * 100))

            poplivingID = feature[self.__livinglyrID]
            popID = feature[self.__poplyrID]
            popNodeid = feature[self.__nodeID]
            poppnt = feature[self.__popcntField]

            try:
                dis = calculatedNode[popNodeid]
            except:
                dis = self.get_nearesttargetDistnace(fromNodeID=popNodeid,
                                                     svrNodeList=svrNodeilst)
                if dis is None: dis = 0

                # if dis is None:
                #     self.setProgressSubMsg("[anal_NeartestCurSOC_network] 오류 : 세생활권의 %s노드 거리를 찾을 수 없음" % str(popNodeid))

                calculatedNode[popNodeid] = dis

            listlivingID.append(poplivingID)
            listpopID.append(popID)
            listpopNode.append(popNodeid)
            listpopCnt.append(poppnt)
            listpopAccscore.append(dis)

        rawData = {self.__poplyrID: listpopID,
                   self.__nodeID: listpopNode,
                   self.__popcntField: listpopCnt,
                   self.__livinglyrID: listlivingID,
                   'DISTANCE': listpopAccscore}

        self.__dfPop = pd.DataFrame(rawData)

        if self.debugging:
            self.setProgressSubMsg("count of unsearchable node : %s" % str(errcnt))
            self.setProgressSubMsg("count of success node : %s" % str(noerrcnt))
            # self.__logger.info("count of unsearchable node : %s" % str(errcnt))
            # self.__logger.info("count of success node : %s" % str(noerrcnt))
            tempexcel = os.path.join(cur_dir, 'temp/anal_NeartestCurSOC_network.csv')
            self.__dfPop.to_csv(tempexcel)
        # except MemoryError as error:
        #     self.setProgressSubMsg(type(error))

        return self.__dfPop


    def anal_AllPotenSOC_network(self):


        tmppotenlayer = self.__potentiallayer

        potencnt = tmppotenlayer.featureCount()
        potenNodeID = []
        potenEquityScore = []
        dictResultwithsScore = {}

        i = 0
        calculatedNode = {}
        for feature in tmppotenlayer.getFeatures():
            i += 1
            if self.feedback.isCanceled(): return None
            self.feedback.setProgress(int(i/potencnt * 100))
            nodeid = feature[self.__nodeID]
            potenNodeID.append(nodeid)

            dists = []
            try:
                dists = calculatedNode[nodeid]
            except:
                for idx, row in self.__dfPop.iterrows():
                    if self.feedback.isCanceled(): return None
                    popNodeID = row[self.__nodeID]
                    newdis = self.get_Distance(fromNodeID=popNodeID,
                                               toNodeID=nodeid)

                    # newdis를 찾지 못할 경우 최대값을 할당함
                    if newdis is None: newdis = self.__outofcutoff

                    dists.append(newdis)
                    calculatedNode[nodeid] = dists

            self.__dfPop['NEW_DIS'] = pd.DataFrame({'NEW_DIS': dists})

            dfsumOfacc = self.__dfPop['ACC_SCORE'] + self.__dfPop['NEW_DIS']

            self.__dfPop['A'] = self.__dfPop[self.__popcntField] * dfsumOfacc
            avg = self.__dfPop['A'].mean()

            # self.__dfPop['EQ_SCORE'] = np.sqrt((self.__dfPop['A'] - avg) ** 2)
            self.__dfPop['EQ_SCORE'] = ((self.__dfPop['A'] - avg)**2)**(1/2)

            sumofeqscore = self.__dfPop['EQ_SCORE'].sum()
            potenEquityScore.append(int(sumofeqscore))
            dictResultwithsScore[nodeid] = int(sumofeqscore)

        rawData = {self.nodeIDfield: potenNodeID,
                   'EQ_SCORE': potenEquityScore}

        self.__dtFinalwithsScore = pd.DataFrame(rawData)
        self.__dictFinalwithScore = dictResultwithsScore

        if self.debugging:
            tempexcel = os.path.join(cur_dir, 'temp/anal_AllPotenSOC_network.csv')
            self.__dtFinalwithsScore.to_csv(tempexcel)

        return self.__dtFinalwithsScore


    def make_Accessbillityscore(self, isNetwork=True, output=None):

        dfPop = self.__dfPop
        dfPop['ACC_SCORE'] = dfPop[self.__popcntField] * dfPop['DISTANCE']

        dfgroupy = dfPop.groupby([self.__livinglyrID])[self.__popcntField, 'DISTANCE', 'ACC_SCORE'].agg({'ACC_SCORE' : {'ACC_SCORE_SUM': 'sum'},
                                                                                                         self.__popcntField: {'POP_SUM': 'sum'}
                                                                                                         }).reset_index()
        dfgroupy['ACC_SCORE'] = dfgroupy['ACC_SCORE_SUM'] / dfgroupy['POP_SUM']


        # todo 이부분은 생각중...
        # 아래 부분은 잘 기억이 안남... 왜 여러개 였지? (아마 노드아이디로 할 시절에 여러개가 반환되므로..)
        # eqscore = tmpdfPOP["ACC_SCORE"].loc[tmpdfPOP[finalKeyID] == str(finalkey)].head(1)

        finanallayer = self.qgsutils.addField(input=self.__livingareaLayer,
                                     fid="AC_SCORE",
                                     ftype=1,  # 0 — Integer, 1 — Float, 2 — String
                                     flen=20,
                                     fprecision=8)
        finanallayer = self.qgsutils.addField(input=finanallayer,
                                              fid="AC_GRADE",
                                              ftype=0,  # 0 — Integer, 1 — Float, 2 — String
                                              flen=10,
                                              fprecision=8)


        i = 0

        if isNetwork:
            finalKeyID = self.__livinglyrID
        else:
            finalKeyID = self.__livinglyrID

        # tmpdfPOP = self.__dfPop.astype({finalKeyID: str})
        tmpdfPOP = dfgroupy.astype({finalKeyID: str})


        ###################### 등급 산정 부분 ######################
        scorefield = 'ACC_SCORE'
        step = 100 / self.__classify_count
        # 접근성 분석은 +지표, 이부분 지표 성격에 따라 다름(+지표 or 0지표)
        classRange = [cls * step for cls in reversed(range(0, self.__classify_count + 1))]
        clsfy = np.nanpercentile(tmpdfPOP[scorefield], classRange, interpolation='linear')
        # 접근성 분석은 +지표, 이부분 지표 성격에 따라 다름(+지표 or 0지표)
        clsfy[len(clsfy) - 1] = tmpdfPOP[scorefield].max(skipna=True) + 1
        clsfy[0] = tmpdfPOP[scorefield].min(skipna=True) - 1

        if self.debugging: self.setProgressSubMsg("classify count : {}".format(len(clsfy)))

        grade = 0
        prevalue = None
        for gradeval in clsfy:
            if prevalue is not None:
                if prevalue != gradeval:
                    # 접근성 분석은 +지표, 이부분 지표 성격에 따라 다름(+지표 or 0지표)
                    # print('{} > {} >= {}'.format(prevalue, i, gradeval))
                    tmpdfPOP.loc[(prevalue > tmpdfPOP[scorefield]) & (tmpdfPOP[scorefield] >= gradeval), 'AC_GRADE'] = grade
            prevalue = gradeval
            grade += 1
        ########################################################################################

        if self.debugging:
            tempexcel = os.path.join(cur_dir, 'temp/final_Accessbillityscore.csv')
            tmpdfPOP.to_csv(tempexcel)


        potencnt = finanallayer.featureCount()
        editstatus = finanallayer.startEditing()
        if self.debugging: self.setProgressSubMsg("editmode : %s" % str(editstatus))

        for feature in finanallayer.getFeatures():
            i += 1
            if self.feedback.isCanceled(): return None
            self.feedback.setProgress(int(i / potencnt * 100))

            finalkey = feature[finalKeyID]
            eqscore = None
            eqgrade = None

            if len(tmpdfPOP["ACC_SCORE"].loc[tmpdfPOP[finalKeyID] == str(finalkey)]) == 0:
                if self.debugging: self.setProgressSubMsg("세생활권에 속해 있는 인구 정보가 없습니다. [%s=%s]" % (finalKeyID, finalkey))
                # self.__logger.info("세생활권에 속해 있는 인구 정보가 없습니다. [%s=%s]" % (finalKeyID, finalkey))
            else:
                eqscore = tmpdfPOP["ACC_SCORE"].loc[tmpdfPOP[finalKeyID] == str(finalkey)].head(1)
                eqscore = float(eqscore)
                if float(eqscore) == 0.0: eqscore = 0.00000001

                eqgrade = tmpdfPOP["AC_GRADE"].loc[tmpdfPOP[finalKeyID] == str(finalkey)].head(1)
                eqgrade = int(eqgrade)

            # if self.debugging: self.setProgressSubMsg(str(eqscore))

            if self.debugging: feature["AC_SCORE"] = eqscore
            feature["AC_GRADE"] = eqgrade

            finanallayer.updateFeature(feature)

        editstatus = finanallayer.commitChanges()
        if self.debugging: self.setProgressSubMsg("commit : %s" % str(editstatus))

        if output is None:
            if self.debugging: self.setProgressSubMsg("output is none")
            resultlayer = finanallayer
        else:
            if self.debugging: self.setProgressSubMsg("output is not none")
            resultlayer = self.qgsutils.vectorlayer2ShapeFile(vectorlayer=finanallayer,
                                                              output=output,
                                                              destCRS=finanallayer.sourceCrs())

        return resultlayer



    def make_equityscore(self, isNetwork=True, output=None):
        # 계산식 확정시 적용
        self.setProgressSubMsg("****** 등급을 산정하기 위한 공식이 구현되지 않았음")

        tmppotenlayer = self.qgsutils.addField(input=self.__potentiallayer,
                                      fid="EQ_SCORE",
                                      ftype=1,  # 0 — Integer, 1 — Float, 2 — String
                                      flen=20,
                                      fprecision=8)
        finanallayer = self.qgsutils.addField(input=tmppotenlayer,
                                              fid="EQ_GRADE",
                                              ftype=0,  # 0 — Integer, 1 — Float, 2 — String
                                              flen=10,
                                              fprecision=8)
        if isNetwork:
            finalKeyID = self.__nodeID
        else:
            finalKeyID = self.__potentialID


        # todo [등급] __dictFinalwithScore, __dtFinalwithsScore 값을 이용하여 등급으로 치환
        # self.__dictFinalwithScore[potenVal]
        dfScore = self.__dtFinalwithsScore
        ###################### 등급 산정 부분 ######################
        scorefield = 'EQ_SCORE'
        step = 100 / self.__classify_count
        # 접근성 분석은 +지표, 이부분 지표 성격에 따라 다름(+지표 or 0지표)
        classRange = [cls * step for cls in range(0, self.__classify_count + 1)]
        # ex) 100, 90, 80, 70, ... 10, 0
        clsfy = np.nanpercentile(dfScore[scorefield], classRange, interpolation='linear')
        # 접근성 분석은 +지표, 이부분 지표 성격에 따라 다름(+지표 or 0지표)
        clsfy[0] = dfScore[scorefield].min(skipna=True) - 1
        clsfy[len(clsfy) - 1] = dfScore[scorefield].max(skipna=True) + 1


        if self.debugging: self.setProgressSubMsg("classify count : {}".format(len(clsfy)))
        if self.debugging: self.setProgressSubMsg("classify : {}".format(clsfy))

        grade = 0
        prevalue = None
        for gradeval in clsfy:
            if prevalue is not None:
                if prevalue != gradeval:
                    # 접근성 분석은 +지표, 이부분 지표 성격에 따라 다름(+지표 or 0지표)
                    # print('{} < {} <= {}'.format(prevalue, i, gradeval))
                    dfScore.loc[(prevalue < dfScore[scorefield]) & (dfScore[scorefield] <= gradeval), 'EQ_GRADE'] = grade
            prevalue = gradeval
            grade += 1
        ########################################################################################
        dictGrade = dict(zip(dfScore[finalKeyID].tolist(), dfScore['EQ_GRADE'].tolist()))


        i = 0
        finanallayer.startEditing()
        potencnt = finanallayer.featureCount()
        for feature in finanallayer.getFeatures():
            i += 1
            if self.feedback.isCanceled(): return None
            self.feedback.setProgress(int(i / potencnt * 100))

            potenVal = feature[finalKeyID]
            eqscore = self.__dictFinalwithScore[potenVal]
            if self.debugging: feature["EQ_SCORE"] = float(eqscore)

            try:
                eqgrade = dictGrade[potenVal]
                feature["EQ_GRADE"] = int(eqgrade)
            except:
                self.setProgressSubMsg('NODEKEY : {}, EQGRADE : {}'.format(potenVal, eqgrade))

            finanallayer.updateFeature(feature)

        finanallayer.commitChanges()

        if output is None:
            resultlayer = finanallayer
        else:
            resultlayer = self.qgsutils.vectorlayer2ShapeFile(vectorlayer=finanallayer,
                                                              output=output,
                                                              destCRS=finanallayer.sourceCrs())
        return resultlayer


    # 효율성에서만 쓰는 함수임
    def anal_nearestSOC_network(self, socNodeList, outdistfidnm, outissvredfidnm):

        tmppoplayer = self.__populationLayer
        totalcnt = tmppoplayer.featureCount()

        listpopID = []
        listpopNode = []
        listpopCnt = []
        listpopAccscore = []
        listissvrSOC = []
        calculatedNode = {}

        i = 0
        errcnt = 0
        noerrcnt = 0
        for feature in tmppoplayer.getFeatures():
            i += 1
            if self.feedback.isCanceled(): return None
            self.feedback.setProgress(int(i / totalcnt * 100))

            popID = feature[self.__poplyrID]
            popNodeid = feature[self.__nodeID]
            poppnt = feature[self.__popcntField]

            # dis는 서비스영역내 생활SOC 존재 여부. 있으면 0, 없으면 1
            try:
                dis = calculatedNode[popNodeid]
            except:
                dis = self.get_nearesttargetDistnace(fromNodeID=popNodeid,
                                                     svrNodeList=socNodeList)
                if dis is None: dis = self.__outofcutoff

                # if dis is None:
                #     self.setProgressSubMsg("[anal_NeartestCurSOC_network] 오류 : 세생활권의 %s노드 거리를 찾을 수 없음" % str(popNodeid))
                calculatedNode[popNodeid] = dis

            if dis > self.__cutoff:
                issvr = 0
            else:
                issvr = 1

            listpopID.append(popID)
            listpopNode.append(popNodeid)
            listpopCnt.append(poppnt)
            listissvrSOC.append(issvr)
            listpopAccscore.append(dis)


        rawData = {
            self.__poplyrID: listpopID,
            self.__nodeID: listpopNode,
            self.__popcntField: listpopCnt,
            outdistfidnm: listpopAccscore,
            outissvredfidnm: listissvrSOC}

        self.dfResult = pd.DataFrame(rawData)



        return self.dfResult




    def anal_efficiencyCurSOC_network(self):

        cursvrlist = [feature.attribute(self.__nodeID) for feature in self.__currentSOClayer.getFeatures()]
        dfCur = self.anal_nearestSOC_network(socNodeList=cursvrlist,
                                      outdistfidnm='CUR_DIST',
                                      outissvredfidnm='CUR_ISSVRED')

        # 기존SOC시설로 커버되는 인구데이터는 모두 제거(CUR_ISSVRED == 0)
        # dfNotSvrPop = dfCur.loc[dfCur['CUR_ISSVRED'] == 1]
        self.__dfPop = dfCur

        # self.__dfPop = pd.merge(dfCur, dfNew[[self.__nodeID, "NEW_DIST", "NEW_ISSVRED"]], on=self.__nodeID)

        if self.debugging:
            tempexcel = os.path.join(cur_dir, 'temp/anal_NeartestCurSOC_network.csv')
            self.__dfPop.to_csv(tempexcel)

        return self.__dfPop



    def anal_efficiencyPotenSOC_straight(self, relpotenID):

        potenID = None
        # popID = None
        popCnt = None
        # popNodeKey = None
        # potenNodeKey = None

        svrdPOPDict = {}
        # popenIDList = []


        i = 0
        tmpPOPlyr = self.__populationLayer
        popFeacnt = tmpPOPlyr.featureCount()
        for feature in tmpPOPlyr.getFeatures():
            i += 1
            if self.feedback.isCanceled(): return None
            self.feedback.setProgress(int(i / popFeacnt * 100))

            popCnt = feature[self.__popcntField]
            potenID = feature[relpotenID]

            try:
                addedpopCnt = svrdPOPDict[potenID]
            except:
                addedpopCnt = 0

            svrdPOPDict[potenID] = addedpopCnt + popCnt

        rawData = {self.__potentialID: list(svrdPOPDict.keys()),
                   'EF_SCORE': list(svrdPOPDict.values())
                   }

        self.__dictFinalwithScore = svrdPOPDict
        self.__dtFinalwithsScore = pd.DataFrame(rawData)

        if self.debugging:
            tempexcel = os.path.join(cur_dir, 'temp/efscore.csv')
            self.__dtFinalwithsScore.to_csv(tempexcel)

        return self.__dtFinalwithsScore




    def anal_efficiencyPotenSOC_network(self, relpotenID, relpotenNodeID):

        potenID = None
        popID = None
        popCnt = None
        popNodeKey = None
        potenNodeKey = None

        svrdPOPDict = {}
        # popenIDList = []


        i = 0
        tmpPOPlyr = self.__populationLayer
        popFeacnt = tmpPOPlyr.featureCount()
        self.setProgressSubMsg("tmpPOPlyr : {}개".format(popFeacnt))
        for feature in tmpPOPlyr.getFeatures():
            i += 1
            if self.feedback.isCanceled(): return None
            self.feedback.setProgress(int(i / popFeacnt * 100))

            popCnt = feature[self.__popcntField]
            popNodeKey = feature[self.__nodeID]
            potenID = feature[relpotenID]
            potenNodeKey = feature[relpotenNodeID]


            dist = self.get_Distance(potenNodeKey, popNodeKey)

            # 거리조락을 벗어나는 NODE들
            if dist is None: dist = self.__outofcutoff
            if dist > self.__cutoff: popCnt = 0


            try:
                addedpopCnt = svrdPOPDict[potenID]
            except:
                addedpopCnt = 0

            svrdPOPDict[potenID] = addedpopCnt + popCnt

        rawData = {self.__potentialID: list(svrdPOPDict.keys()),
                   'EF_SCORE': list(svrdPOPDict.values())
                   }

        self.__dictFinalwithScore = svrdPOPDict
        self.__dtFinalwithsScore = pd.DataFrame(rawData)

        if self.debugging: self.__dtFinalwithsScore.to_csv(os.path.join(cur_dir, 'temp/efscore.csv'))

        return self.__dtFinalwithsScore




    def make_efficiencyscore(self, output):
        # 계산식 확정시 적용
        self.setProgressSubMsg("****** 등급을 산정하기 위한 공식이 구현되지 않았음")

        dictScore = self.__dictFinalwithScore
        finalKeyID = self.__potentialID


        # todo [등급] __dictFinalwithScore, __dtFinalwithsScore 값 이용하여 등급 값 산정
        dfScore = self.__dtFinalwithsScore
        ###################### 등급 산정 부분 ######################
        step = 100 / self.__classify_count
        # 접근성 분석은 +지표, 이부분 지표 성격에 따라 다름(+지표 or 0지표)
        classRange = [cls * step for cls in reversed(range(0, self.__classify_count + 1))]
        clsfy = np.nanpercentile(dfScore['EF_SCORE'], classRange, interpolation='linear')
        # 접근성 분석은 +지표, 이부분 지표 성격에 따라 다름(+지표 or 0지표)
        clsfy[0] = dfScore['EF_SCORE'].max(skipna=True) + 1
        clsfy[len(clsfy) - 1] = dfScore['EF_SCORE'].min(skipna=True) - 1

        if self.debugging: self.setProgressSubMsg("classify count : {}".format(len(clsfy)))

        grade = 0
        prevalue = None
        for gradeval in clsfy:
            if prevalue is not None:
                if prevalue != gradeval:
                    # 접근성 분석은 +지표, 이부분 지표 성격에 따라 다름(+지표 or 0지표)
                    # print('{} > {} >= {}'.format(prevalue, i, gradeval))
                    dfScore.loc[
                        (prevalue > dfScore['EF_SCORE']) & (dfScore['EF_SCORE'] >= gradeval), 'EF_GRADE'] = grade
            prevalue = gradeval
            grade += 1
        ########################################################################################
        dictefGrade = dict(zip(dfScore[finalKeyID].tolist(), dfScore['EF_GRADE'].tolist()))

        tmppotenlayer = self.qgsutils.addField(input=self.__potentiallayer,
                                               fid="EF_SCORE",
                                               ftype=1,  # 0 — Integer, 1 — Float, 2 — String
                                               flen=20,
                                               fprecision=8)
        finanallayer = self.qgsutils.addField(input=tmppotenlayer,
                                              fid="EF_GRADE",
                                              ftype=0,  # 0 — Integer, 1 — Float, 2 — String
                                              flen=10,
                                              fprecision=8)

        i = 0


        finanallayer.startEditing()
        potencnt = finanallayer.featureCount()
        for feature in finanallayer.getFeatures():
            i += 1
            if self.feedback.isCanceled(): return None
            self.feedback.setProgress(int(i / potencnt * 100))

            finalkey = feature[finalKeyID]

            try:
                efscore = dictScore[finalkey]
                efgrade = dictefGrade[finalkey]
                # todo [CHECK] 같은 노드를 가지고 있는 경우는 0 (해당 노드 확인 필요)
                if efscore == 0:
                    efscore = 0.00000001
            except:
                efscore = 0.00000001


            if self.debugging: feature["EF_SCORE"] = float(efscore)
            feature["EF_GRADE"] = float(efgrade)

            finanallayer.updateFeature(feature)

        finanallayer.commitChanges()

        if output is None:
            resultlayer = finanallayer
        else:
            resultlayer = self.qgsutils.vectorlayer2ShapeFile(vectorlayer=finanallayer,
                                                              output=output,
                                                              destCRS=finanallayer.sourceCrs())
        return resultlayer

    def removeRelCurSOCInPoplayer(self):

        dfpopremovedSOC = self.__dfPop

        tmppoplayer = self.__populationLayer
        tmppoplayer.removeSelection()

        totalcnt = tmppoplayer.featureCount()
        tmppoplayer.startEditing()

        i = 0
        for feature in tmppoplayer.getFeatures():
            i += 1
            if self.feedback.isCanceled(): return None
            self.feedback.setProgress(int(i / totalcnt * 100))

            popID = feature[self.__poplyrID]

            isSvredCurSOC = dfpopremovedSOC['CUR_ISSVRED'].loc[dfpopremovedSOC[self.__poplyrID] == popID].values[0]

            if str(isSvredCurSOC) == '1':
                expression = "\"%s\"=%s" % (self.__poplyrID, str(popID))
                # if self.debugging: self.setProgressSubMsg("expression : %s" % expression)
                tmppoplayer.selectByExpression(expression, QgsVectorLayer.AddToSelection)

        if self.debugging: self.setProgressSubMsg("선택된 객체 : %s " % str(len(list(tmppoplayer.getSelectedFeatures()))))

        bsuccess = tmppoplayer.deleteSelectedFeatures()

        if self.debugging: self.setProgressSubMsg("삭제 결과 : %s" %str(bsuccess))

        if bsuccess:
            tmppoplayer.commitChanges()
            # self.__populationLayer = tmppoplayer
            return tmppoplayer
        else:
            tmppoplayer.rollback(deleteBuffer=True)
            return None



