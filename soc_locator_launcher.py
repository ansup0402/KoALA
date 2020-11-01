import os

class soc_locator_launcher:

    def __init__(self, feedback, context, parameters, debugging=False, workpath=None):
        self.debugging = debugging
        self.feedback = feedback
        self.context = context
        self.parameters = parameters

        # 'OUTPUT': 'ogr:dbname=\'C:/Users/ansup/Downloads/aaaaa.gpkg\' table=\"bbbb\" (geom)', 'SEGMENTS': 5}

        self.workpath = workpath

        self.cutoffconst_acc = 1000000
        self.cutoffconst_eff = 1000000
        self.cutoffconst_equ = 1000000

        self.enablelogmsg = False

    def setDebugProgressMsg(self, msg, output=None):
        if self.debugging or self.enablelogmsg:
            import time
            now = time.localtime()

            snow = "%04d-%02d-%02d %02d:%02d:%02d" % (
            now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)

            # self.feedback.pushConsoleInfo("\n%s %s" % (snow, msg))
            outputmessage = "{} [debug] {}".format(snow, msg)
            if not output is None:
                outputmessage = outputmessage + "\n{}".format(output)

            # self.feedback.pushCommandInfo(outputmessage)
            self.feedback.pushDebugInfo(outputmessage)
            # self.feedback.pushInfo("\n%s %s" % (snow, msg))
            # self.feedback.pushConsoleInfo("\n%s %s" % (snow, msg))
            # self.feedback.pushDebugInfo("\n%s %s" % (snow, msg))

    def setProgressMsg(self, msg):
        import time
        now = time.localtime()

        snow = "%04d-%02d-%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)

        # self.feedback.pushConsoleInfo("\n%s %s" % (snow, msg))
        self.feedback.pushCommandInfo("\n%s %s" % (snow, msg))
        # self.feedback.pushInfo("\n%s %s" % (snow, msg))
        # self.feedback.pushConsoleInfo("\n%s %s" % (snow, msg))
        # self.feedback.pushDebugInfo("\n%s %s" % (snow, msg))

    def execute_accessibility_in_straight(self):

        try:
            from .soc_locator_model import soc_locator_model
        except ImportError:
            from soc_locator_model import soc_locator_model
        model = soc_locator_model(feedback=self.feedback, context=self.context, debugmode=self.debugging, workpath=self.workpath)

        livingID = 'LIV_ID'
        curSOCID = 'CSOC_ID'
        popID = 'POP_ID'


        #
        #
        ################# [1 단계] 분석 위한 데이터 초기화 : 분석 영역 데이터 추출 #################
        self.setProgressMsg('[1 단계] 분석을 위한 데이터를 초기화 합니다......')
        # self.setProgressMsg('..... 분석 영역 데이터 생성')
        if self.feedback.isCanceled(): return None
        # out_path = os.path.join(self.workpath, 'boundary.gpkg')
        out_path = os.path.join(self.workpath, 'boundary')

        self.setDebugProgressMsg("대상지 레이어에서 분석 영역을 추출합니다...", out_path)
        # Create Spatial Index
        model.createspatialindex(self.parameters['IN_SITE'].sourceName())
        boundary = model.dissolvewithQgis(input=self.parameters['IN_SITE'].sourceName(),
                                          onlyselected=self.parameters['IN_SITE_ONLYSELECTED'],
                                          output=out_path)

        if isinstance(boundary, str):
            model.boundary = model.writeAsVectorLayer(boundary)
        else:
            model.boundary = boundary


        # 1-2 분석 지역 데이터 추출 : 인구데이터
        # self.setProgressMsg('..... 분석 지역 데이터 추출 : 인구 데이터')
        if self.feedback.isCanceled(): return None
        self.setDebugProgressMsg("분석 영역에 해당하는 인구 데이터를 추출합니다...")
        # Create Spatial Index
        model.createspatialindex(self.parameters['IN_POP'].sourceName())
        clipedpop = model.clipwithQgis(input=self.parameters['IN_POP'].sourceName(),
                                       onlyselected=self.parameters['IN_POP_ONLYSELECTED'],
                                       overlay=model.boundary)

        out_path = os.path.join(self.workpath, 'cliped_pop_tmp.gpkg')
        self.setDebugProgressMsg("인구 데이터에 ID필드({})를 추가합니다...".format(popID), out_path)
        clipedpop = model.addIDField(input=clipedpop, idfid=popID, output=out_path)
        model.popIDField = popID
        model.popcntField = self.parameters['IN_POP_CNTFID']

        # 불필요한 필드 값 제거(IN_POP)
        out_path = os.path.join(self.workpath, 'cliped_pop.gpkg')
        self.setDebugProgressMsg("인구 데이터에 필수 필드({},{})를 제외한 데이터를 삭제합니다...".format(popID, self.parameters['IN_POP_CNTFID']), out_path)
        clipedpop = model.deleteFields(input=clipedpop, requredfields=[popID, self.parameters['IN_POP_CNTFID']],
                                       output=out_path)

        # 1-3 분석 지역 데이터 추출 : 세생활권
###### Case1 세생활권 데이터를 "레이어(폴리곤) 타입"으로 받을 경우
        # # self.setProgressMsg('..... 분석 지역 데이터 추출 : 세생활권')
        # if self.feedback.isCanceled(): return None
        # clipedliving = model.clipwithQgis(input=self.parameters['IN_LIVINGAREA'].sourceName(),
        #                                   onlyselected=self.parameters['IN_LIVINGAREA_ONLYSELECTED'],
        #                                   overlay=boundary)


###### Case2 세생활권 데이터를 "격자크기(숫자) 타입"으로 받을 경우
        # 세생활권 레이어 생성 : 분석 영역을 기준으로 Fishnet 레이어 생성
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'fishnetliving.gpkg')
        self.setDebugProgressMsg("세생활권 레이어(Polygon)를 생성합니다.", out_path)
        fishnetliving = model.createGridfromLayer(sourcelayer=model.boundary,
                                              gridsize=self.parameters['IN_LIVINGAREA'],
                                              type=2,
                                              output=out_path)


        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_fishnetliving.gpkg')
        self.setDebugProgressMsg("분석 영역에 해당하는 세생활권 레이어(Polygon)를 추출합니다...", out_path)
        # Create Spatial Index
        model.createspatialindex(fishnetliving)
        clipedfishnetliving = model.clipwithQgis(input=fishnetliving,
                                        onlyselected=False,
                                        overlay=model.boundary,
                                        output=out_path)


        # ID 추가
        out_path = os.path.join(self.workpath, 'cliped_living.gpkg')
        self.setDebugProgressMsg("세생활권 레이어(Polygon)에 ID필드({})를 추가합니다...".format(livingID), out_path)
        clipedfishnetliving2 = model.addIDField(input=clipedfishnetliving, idfid=livingID, output=out_path)

        # 세생활권 레이어 정리 : 인구 레이어와의 Spatial Join을 통해 연계되지 않은 피처 제거
        out_path = os.path.join(self.workpath, 'cliped_fishnetliving_discarded.gpkg')
        self.setDebugProgressMsg("세생활권 레이어(Polygon)와 인구레이어를 공간 조인하고, 조인되지 않는 데이터는 삭제합니다...", out_path)
        # Create Spatial Index
        model.createspatialindex(clipedfishnetliving2)
        model.createspatialindex(clipedpop)
        tmpliving = model.joinattributesbylocation(input=clipedfishnetliving2,
                                                       join=clipedpop,
                                                       joinfiels=[],
                                                       discardnomatching=True,
                                                       output=out_path
                                                       )

######################################################################################################
        out_path = os.path.join(self.workpath, 'only_living_has_pop.gpkg')
        self.setDebugProgressMsg('인구와 조인된 세생활권 레이어(Polygon)를 PK필드({})로 Dissolve 하여 중복데이터를 제거합니다'.format(livingID), out_path)
        # Create Spatial Index
        model.createspatialindex(tmpliving)
        clipedliving = model.dissolvewithQgis(input=tmpliving, onlyselected=False, field=[livingID], output=out_path)



        # 불필요한 필드 값 제거(IN_LIVINGAREA)
        out_path = os.path.join(self.workpath, 'cliped_living2.gpkg')
        self.setDebugProgressMsg("세생활권 레이어(Polygon)에 필수 필드({})를 제외한 데이터를 삭제합니다...".format(livingID), out_path)
        clipedliving = model.deleteFields(input=clipedliving, requredfields=[livingID], output=out_path)

        if isinstance(clipedliving, str):
            model.livingareaLayer = model.writeAsVectorLayer(clipedliving)
        else:
            model.livingareaLayer = clipedliving
        model.livingareaIDField = livingID










        # 1-4 분석 지역 데이터 추출 : 기존 생활 SOC 시설
        # self.setProgressMsg('..... 분석 지역 데이터 추출 : 기존 생활 SOC 시설\n')
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_curSOC.gpkg')
        self.setDebugProgressMsg("분석 영역에 해당하는 기존시설데이터를 추출합니다...", out_path)
        # Create Spatial Index
        model.createspatialindex(self.parameters['IN_CURSOC'].sourceName())
        clipedCurSOC = model.clipwithQgis(input=self.parameters['IN_CURSOC'].sourceName(),
                                          onlyselected=self.parameters['IN_CURSOC_ONLYSELECTED'],
                                          overlay=boundary,
                                          output=out_path)


        out_path = os.path.join(self.workpath, 'cliped_curSOC1.gpkg')
        self.setDebugProgressMsg("기존시설데이터에 ID필드({})를 추가합니다...".format(curSOCID), out_path)
        # Create Spatial Index
        model.createspatialindex(clipedCurSOC)
        clipedCurSOC = model.addIDField(input=clipedCurSOC, idfid=curSOCID, output=out_path)


        # 불필요한 필드 값 제거(IN_CURSOC)
        out_path = os.path.join(self.workpath, 'cliped_curSOC2.gpkg')
        self.setDebugProgressMsg("기존시설데이터에 필수 필드({})를 제외한 데이터를 삭제합니다...".format(curSOCID), out_path)
        clipedCurSOC = model.deleteFields(input=clipedCurSOC, requredfields=[curSOCID], output=out_path)



        model.currentSOCID = curSOCID
        model.cutoff = self.parameters['IN_LIMIT_DIST']
        model.outofcutoff = self.parameters['IN_LIMIT_DIST'] * self.cutoffconst_acc

        if isinstance(clipedCurSOC, str):
            model.currentSOC = model.writeAsVectorLayer(clipedCurSOC)
        else:
            model.currentSOC = clipedCurSOC
        #
        #
        #
        #
        ################# [2 단계] 세생활권 인구정보와 생활SOC정보 분석 #################
        self.setProgressMsg('[2 단계] 세생활권 인구정보와 생활SOC 분석......')
        # self.setProgressMsg('..... 거주인구 지점의 최근린 생활SOC지점 검색')
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'popwithnearestSOC.gpkg')
        self.setDebugProgressMsg("기존 인구데이터에서 최근린 기존시설데이터를 찾습니다...", out_path)
        # Create Spatial Index
        model.createspatialindex(clipedpop)
        model.createspatialindex(model.currentSOC)
        popwithNearSOC = model.nearesthubpoints(input=clipedpop,
                                                onlyselected=False,
                                                sf_hub=model.currentSOC,
                                                hubfield=model.currentSOCID,
                                                output=out_path
                                                )

        # 2-2 개별거주인구와 생활SOC intersection : 개별 거주인구와 모든 생활SOC까지의 거리 계산
        # self.setProgressMsg('..... 거주인구 데이터와 생활 SOC 데이터 거리 분석\n')
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_popaddedlivingarea.gpkg')
        self.setDebugProgressMsg(
            "각 인구데이터에 교차(intersection)하는 세생활권데이터를 연산하고, 필수 필드({},{},{},{})만 남겨놓습니다...".format(popID, model.popcntField, "HubDist",
                                                                                model.livingareaIDField), out_path)
        # Create Spatial Index
        model.createspatialindex(popwithNearSOC)
        model.createspatialindex(model.livingareaLayer)
        popWithNodeaddedliving = model.intersection(input=popwithNearSOC,
                                                    inputfields=[popID,
                                                                 model.popcntField,
                                                                 'HubDist'],
                                                    inputonlyseleceted=False,
                                                    overlay=model.livingareaLayer,
                                                    overayprefix='',
                                                    overlayer_fields=[model.livingareaIDField],
                                                    output=out_path
                                                    )

        if isinstance(popWithNodeaddedliving, str):
            model.populationLayer = model.writeAsVectorLayer(popWithNodeaddedliving)
        else:
            model.populationLayer = popWithNodeaddedliving
        #
        #
        #
        #
        #
        ################# [3 단계] 접근성 분석(직선거리) #################
        # 3-1 세생활권의 접근성 분석
        self.setProgressMsg('[3 단계] 접근성 분석(직선거리)......')
        # self.setProgressMsg('....... 세생활권 접근성 분석')
        if self.feedback.isCanceled(): return None

        output = os.path.join(self.workpath, 'analyze_fromAllCurSOC.csv')
        self.setDebugProgressMsg("세생활권의 최근린 SOC 시설을 찾습니다...")
        self.setDebugProgressMsg("anal_accessibilityCurSOC_straight 실행...", output)
        dfPop = model.anal_accessibilityCurSOC_straight()
        if self.debugging: dfPop.to_csv(output)


        # 3-2 접근성 분석 결과 평가
        if self.feedback.isCanceled(): return None
        self.setDebugProgressMsg("접근성 지수를 계산합니다...")
        self.setDebugProgressMsg("make_Accessbillityscore 실행...")
        finallayer = model.make_Accessbillityscore(isNetwork=False, output=self.parameters["OUTPUT"])

        return finallayer

    def execute_tools_point2polygone(self):
        try:
            from .soc_locator_model import soc_locator_model
        except ImportError:
            from soc_locator_model import soc_locator_model
        model = soc_locator_model(feedback=self.feedback, context=self.context, debugmode=self.debugging, workpath=self.workpath)

        pointlayer = self.parameters['IN_ORGPOINT'].sourceName()
        onlyselectedfeatureinpointlayer = self.parameters['IN_ORGPOINT_ONLYSELECTED']
        gridsize = self.parameters['IN_GRID_SIZE']
        output = self.parameters["OUTPUT"]

        self.setProgressMsg("선택한 레이어를 폴리곤 레이어로 변환 합니다.")
        polylayer = model.rectanglesovalsdiamonds(input=pointlayer, onlyselected=onlyselectedfeatureinpointlayer,
                                                  width=gridsize, height=gridsize,
                                                  output=output)

        return polylayer

    def execute_equity_in_straight(self):
        try:
            from .soc_locator_model import soc_locator_model
        except ImportError:
            from soc_locator_model import soc_locator_model
        model = soc_locator_model(feedback=self.feedback, context=self.context, debugmode=self.debugging, workpath=self.workpath)

        curStep = 0
        curSOCID = 'CSOC_ID'
        popID = 'POP_ID'
        livingID = 'LIV_ID'
        #
        #
        #
        #
        #
        ################# [1 단계] 분석 위한 데이터 초기화 : 분석 영역 데이터 추출 #################
        curStep += 1
        self.setProgressMsg('[{} 단계] 분석을 위한 데이터를 초기화 합니다......'.format(curStep))
        # 1-1 분석 영역 데이터 생성
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'boundary.gpkg')
        self.setDebugProgressMsg("대상지 레이어에서 분석 영역을 추출합니다...", out_path)
        boundary = model.dissolvewithQgis(input=self.parameters['IN_SITE'].sourceName(),
                                          onlyselected=self.parameters['IN_SITE_ONLYSELECTED'],
                                          output=out_path)

        if isinstance(boundary, str):
            model.boundary = model.writeAsVectorLayer(boundary)
        else:
            model.boundary = boundary





        # 1-3 분석 지역 데이터 추출 : 인구데이터
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_pop.gpkg')
        self.setDebugProgressMsg("분석 영역에 해당하는 인구 데이터를 추출합니다...", out_path)
        clipedpop = model.clipwithQgis(input=self.parameters['IN_POP'].sourceName(),
                                       onlyselected=self.parameters['IN_POP_ONLYSELECTED'],
                                       overlay=model.boundary,
                                       output=out_path)

        # 불필요한 필드 값 제거(IN_POP)
        out_path = os.path.join(self.workpath, 'cliped_pop2.gpkg')
        self.setDebugProgressMsg("인구 데이터에 필수 필드({})를 제외한 데이터를 삭제합니다...".format(self.parameters['IN_POP_CNTFID']), out_path)
        clipedpop = model.deleteFields(input=clipedpop, requredfields=[self.parameters['IN_POP_CNTFID']], output=out_path)

        out_path = os.path.join(self.workpath, 'cliped_pop3_withID.gpkg')
        self.setDebugProgressMsg("인구 데이터에 ID필드({})를 추가합니다...".format(popID), out_path)
        clipedpop = model.addIDField(input=clipedpop, idfid=popID, output=out_path)
        model.populationLayer = clipedpop
        model.popcntField = self.parameters['IN_POP_CNTFID']
        model.popIDField = popID



        # 1-4 분석 지역 데이터 추출 : 기존 생활 SOC 시설
        if self.feedback.isCanceled(): return None
        self.setDebugProgressMsg("분석 영역에 해당하는 기존시설데이터를 추출합니다...", out_path)
        clipedCurSOC = model.clipwithQgis(input=self.parameters['IN_CURSOC'].sourceName(),
                                          onlyselected=self.parameters['IN_CURSOC_ONLYSELECTED'],
                                          overlay=model.boundary)

        out_path = os.path.join(self.workpath, 'cliped_curSOC.gpkg')
        self.setDebugProgressMsg("기존시설데이터에 ID필드({})를 추가합니다...".format(curSOCID), out_path)
        clipedCurSOC = model.addIDField(input=clipedCurSOC, idfid=curSOCID, output=out_path)
        model.currentSOCID = curSOCID

        # 불필요한 필드 값 제거(IN_CURSOC)
        out_path = os.path.join(self.workpath, 'cliped_curSOC2.gpkg')
        self.setDebugProgressMsg("기존시설데이터에 필수 필드({})를 제외한 데이터를 삭제합니다...".format(curSOCID), out_path)
        clipedCurSOC = model.deleteFields(input=clipedCurSOC, requredfields=[curSOCID], output=out_path)


        if isinstance(clipedCurSOC, str):
            model.currentSOC = model.writeAsVectorLayer(clipedCurSOC)
        else:
            model.currentSOC = clipedCurSOC

        #
        #
        #
        #
        #
        ################# [2 단계] 세생활권 인구정보와 생활SOC정보 분석 #################
        if False:   # 세생활권 인구를 적용 할 경우(주석만 제거 하면 바로 활용 가능)
            curStep += 1
            self.setProgressMsg('[{} 단계] 세생활권 인구정보와 생활SOC 분석......'.format(curStep))

            # 2-1 분석 지역 데이터 추출 : 세생활권
            if self.feedback.isCanceled(): return None
            if self.debugging: self.setProgressMsg('세생활권 레이어를 초기화 합니다.....')
            clipedliving = model.clipwithQgis(input=self.parameters['IN_LIVINGAREA'].sourceName(),
                                            onlyselected=self.parameters['IN_LIVINGAREA_ONLYSELECTED'],
                                            overlay=model.boundary)
            out_path = os.path.join(self.workpath, 'cliped_living.gpkg')
            clipedliving = model.addIDField(input=clipedliving, idfid=livingID, output=out_path)

            # 불필요한 필드 값 제거(IN_LIVINGAREA)
            out_path = os.path.join(self.workpath, 'cliped_living2.gpkg')
            clipedliving = model.deleteFields(input=clipedliving, requredfields=[livingID], output=out_path)

            if isinstance(clipedliving, str):
                clipedliving = model.writeAsVectorLayer(clipedliving)
            else:
                clipedliving = clipedliving

            model.livingareaIDField = livingID

            # 2-2 세생활권내 인구 분석
            # 인구 계산
            if self.feedback.isCanceled(): return None
            out_path = os.path.join(self.workpath, 'cliped_livingwithpop.gpkg')
            clipelivingwithpop = model.countpointsinpolygon(polylayer=clipedliving,
                                                            pointslayer=clipedpop,
                                                            field=self.parameters['IN_POP_CNTFID'],
                                                            weight=self.parameters['IN_POP_CNTFID'],
                                                            classfield=None,
                                                            output=out_path)

            if isinstance(clipelivingwithpop, str):
                clipelivingwithpop = model.writeAsVectorLayer(clipelivingwithpop)
            else:
                clipelivingwithpop = clipelivingwithpop

            # 세생활권(인구수)레이어를 Point레이어로 변경
            if self.feedback.isCanceled(): return None
            out_path = os.path.join(self.workpath, 'cliped_pointlivingwithpop.gpkg')
            clipepointlivingwithpop = model.centroidlayer(input=clipelivingwithpop,
                                                     output=out_path)

            if isinstance(clipepointlivingwithpop, str):
                model.populationLayer = model.writeAsVectorLayer(clipepointlivingwithpop)
            else:
                model.populationLayer = clipepointlivingwithpop
            model.popcntField = self.parameters['IN_POP_CNTFID']
            model.popIDField = livingID






        #
        #
        #
        #
        #
        ################# [3 단계] 생활 SOC 잠재적 위치 데이터 생성 #################
        curStep += 1
        self.setProgressMsg('[{} 단계] 생활 SOC 잠재적 위치 데이터 생성......'.format(curStep))
        # 3-1  잠재적 위치 데이터 생성
        if self.feedback.isCanceled(): return None


        usergrid = self.parameters['IN_USERGRID']

        gridlayer = None
        onlyselected = False
        if usergrid == None:
            out_path = os.path.join(self.workpath, 'grid.gpkg')
            self.setDebugProgressMsg("잠재적 후보지 데이터(Point-{}m)를 생성합니다..".format(self.parameters['IN_GRID_SIZE']), out_path)
            gridlayer = model.createGridfromLayer(sourcelayer=model.boundary,
                                                  gridsize=self.parameters['IN_GRID_SIZE'],
                                                  output=out_path)
        else:
            gridlayer = self.parameters['IN_USERGRID'].sourceName()
            onlyselected = self.parameters['IN_USERGRID_ONLYSELECTED']


        # 3-2 분석 지역 데이터 추출 : 잠재적 위치
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_grid.gpkg')
        self.setDebugProgressMsg("분석 영역에 해당하는 잠재적 후보지 데이터를 추출합니다...", out_path)
        clipedgrid = model.clipwithQgis(input=gridlayer,
                                        onlyselected=onlyselected,
                                        overlay=model.boundary,
                                        output=out_path)

        if isinstance(clipedgrid, str):
            grid = model.writeAsVectorLayer(clipedgrid)
        else:
            grid = clipedgrid


        out_path = os.path.join(self.workpath, 'cliped_grid_single.gpkg')
        self.setDebugProgressMsg("잠재적 후보지 데이터를 싱글파트로 변환합니다...", out_path)
        grid = model.multiparttosingleparts(grid, output=out_path)


        #add grid id : 코드 일관성 유지를 위해 자동으로 생성되는 id사용안함(사용자 후보지 고려)
        gridid = "GRID_ID"
        out_path = os.path.join(self.workpath, 'final_grid.gpkg')
        self.setDebugProgressMsg("후보지 데이터에 ID필드({})를 추가합니다...".format(gridid), out_path)
        grid = model.addIDField(input=grid, idfid=gridid, output=out_path)
        model.potentialID = gridid


        if isinstance(grid, str):
            model.potentiallayer = model.writeAsVectorLayer(grid)
        else:
            model.potentiallayer = grid


        #
        #
        #


        # 10. 분석 실행(기존 시설 거리 분석)
        model.cutoff = self.parameters['IN_LIMIT_DIST']
        model.outofcutoff = self.parameters['IN_LIMIT_DIST'] * self.cutoffconst_equ
        #
        #
        #
        #
        #
        ################# [4 단계] 형평성 분석(직선거리) #################
        curStep += 1
        self.setProgressMsg('[{} 단계] 형평성 분석(직선거리)......'.format(curStep))

        # 4-1 형평성 분석 : 기존 생활 SOC 시설
        if self.feedback.isCanceled(): return None
        self.setDebugProgressMsg("기존 시설의 형평성 점수를 계산합니다...")
        self.setDebugProgressMsg("anal_AllCurSOC_straight 실행...")
        dfPop = model.anal_AllCurSOC_straight()


        # 4-2 형평성 분석 : 잠재적 위치
        if self.feedback.isCanceled(): return None
        self.setDebugProgressMsg("후보지의 형평성 점수를 계산합니다...")
        self.setDebugProgressMsg("anal_AllPotenSOC_straight 실행...")
        potengpd = model.anal_AllPotenSOC_straight()

        # 4-3 형평성 분석 결과 평가
        if self.feedback.isCanceled(): return None
        self.setDebugProgressMsg("형평성 지수를 계산합니다...")
        out_path = os.path.join(self.workpath, 'analyzed_layer.gpkg')
        finallayer = model.make_equityscore(isNetwork=False, output=out_path)


        self.setDebugProgressMsg("최종결과를 폴리곤({})으로 변환합니다...".format(self.parameters['IN_GRID_SIZE']))
        finallayer2 = model.rectanglesovalsdiamonds(input=finallayer, onlyselected=False,
                                                    width=self.parameters['IN_GRID_SIZE'],
                                                    height=self.parameters['IN_GRID_SIZE'],
                                                    output=self.parameters["OUTPUT"])


        return finallayer2


    def execute_accessbillity_in_network(self):

        try:
            from .soc_locator_model import soc_locator_model
        except ImportError:
            from soc_locator_model import soc_locator_model
        model = soc_locator_model(feedback=self.feedback, context=self.context, debugmode=self.debugging, workpath=self.workpath)

        livingID = 'LIV_ID'
        popID = 'POP_ID'
        nodeID = self.parameters['IN_NODE_ID']
        #
        #
        #
        #
        #
        model.classify_count =  self.parameters['IN_CALSSIFYNUM']
        ################# [1 단계] 분석 위한 데이터 초기화 : 분석 영역 데이터 추출 #################
        self.setProgressMsg('[1 단계] 분석을 위한 데이터를 초기화 합니다......')




        # 1-1 분석 영역 데이터 생성
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'boundary.gpkg')
        self.setDebugProgressMsg("대상지 레이어에서 분석 영역을 추출합니다...", out_path)
        # Create Spatial Index
        model.createspatialindex(self.parameters['IN_SITE'].sourceName())
        boundary = model.dissolvewithQgis(input=self.parameters['IN_SITE'].sourceName(),
                                          onlyselected=self.parameters['IN_SITE_ONLYSELECTED'],
                                          output=out_path)

        if isinstance(boundary, str):
            model.boundary = model.writeAsVectorLayer(boundary)
        else:
            model.boundary = boundary



        # 1-2 분석 지역 데이터 추출 : 노드
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_node.gpkg')
        self.setDebugProgressMsg("분석 영역에 해당하는 노드 데이터를 추출합니다...", out_path)
        # Create Spatial Index
        model.createspatialindex(self.parameters['IN_NODE'].sourceName())
        clipednode = model.clipwithQgis(input=self.parameters['IN_NODE'].sourceName(),
                                        onlyselected=self.parameters['IN_NODE_ONLYSELECTED'],
                                        overlay=boundary,
                                        output=out_path)

        if isinstance(clipednode, str):
            model.nodelayer = model.writeAsVectorLayer(clipednode)
        else:
            model.nodelayer = clipednode
        model.nodeIDfield = nodeID


        # 1-3 분석 지역 데이터 추출 : 링크
        if self.feedback.isCanceled(): return None
        self.setDebugProgressMsg("분석 영역의 버퍼(2000m)데이터를 생성합니다...")

        # Create Spatial Index
        model.createspatialindex(boundary)
        boundary2000 = model.bufferwithQgis(input=boundary,
                                           onlyselected=False,
                                           distance=2000)

        out_path = os.path.join(self.workpath, 'cliped_link.gpkg')
        self.setDebugProgressMsg("분석 영역(2000m)에 해당하는 링크 데이터를 추출합니다...", out_path)
        # Create Spatial Index
        model.createspatialindex(self.parameters['IN_LINK'].sourceName())
        clipedlink = model.clipwithQgis(input=self.parameters['IN_LINK'].sourceName(),
                                        onlyselected=self.parameters['IN_LINK_ONLYSELECTED'],
                                        overlay=boundary2000,
                                        output=out_path)

        if isinstance(clipedlink, str):
            model.linklayer = model.writeAsVectorLayer(clipedlink)
        else:
            model.linklayer = clipedlink
        model.linkFromnodefield = self.parameters['IN_LINK_FNODE']
        model.linkTonodefield = self.parameters['IN_LINK_TNODE']
        model.linklengthfield = self.parameters['IN_LINK_LENGTH']
        model.linkSpeed = self.parameters['IN_LINK_SPEED']



        # 1-2 분석 지역 데이터 추출 : 인구데이터
        # self.setProgressMsg('..... 분석 지역 데이터 추출 : 인구 데이터')
        if self.feedback.isCanceled(): return None
        self.setDebugProgressMsg("분석 영역에 해당하는 인구 데이터를 추출합니다...")
        # Create Spatial Index
        model.createspatialindex(input=self.parameters['IN_POP'].sourceName())
        clipedpop = model.clipwithQgis(input=self.parameters['IN_POP'].sourceName(),
                                       onlyselected=self.parameters['IN_POP_ONLYSELECTED'],
                                       overlay=model.boundary)

        out_path = os.path.join(self.workpath, 'cliped_pop.gpkg')
        self.setDebugProgressMsg("인구 데이터에 ID필드({})를 추가합니다...".format(popID), out_path)
        clipedpop = model.addIDField(input=clipedpop, idfid=popID, output=out_path)
        model.popIDField = popID
        model.popcntField = self.parameters['IN_POP_CNTFID']

        # 불필요한 필드 값 제거(IN_POP)
        out_path = os.path.join(self.workpath, 'cliped_pop2.gpkg')
        self.setDebugProgressMsg("인구 데이터에 필수 필드({},{})를 제외한 데이터를 삭제합니다...".format(popID, self.parameters['IN_POP_CNTFID']), out_path)
        clipedpop = model.deleteFields(input=clipedpop, requredfields=[popID, self.parameters['IN_POP_CNTFID']],
                                       output=out_path)



        # 1-4 분석 지역 데이터 추출 : 세생활권
###### Case1 세생활권 데이터를 "레이어(폴리곤) 타입"으로 받을 경우
        # # self.setProgressMsg('..... 분석 지역 데이터 추출 : 세생활권')
        # if self.feedback.isCanceled(): return None
        # clipedliving = model.clipwithQgis(input=self.parameters['IN_LIVINGAREA'].sourceName(),
        #                                   onlyselected=self.parameters['IN_LIVINGAREA_ONLYSELECTED'],
        #                                   overlay=boundary)


###### Case2 세생활권 데이터를 "격자크기(숫자) 타입"으로 받을 경우
        # 세생활권 레이어 생성 : 분석 영역을 기준으로 Fishnet 레이어 생성
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'fishnetliving.gpkg')
        self.setDebugProgressMsg("세생활권 레이어(Polygon)를 생성합니다.", out_path)
        fishnetliving = model.createGridfromLayer(sourcelayer=model.boundary,
                                                  gridsize=self.parameters['IN_LIVINGAREA'],
                                                  type=2,
                                                  output=out_path)

        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_fishnetliving.gpkg')
        self.setDebugProgressMsg("분석 영역에 해당하는 세생활권 레이어(Polygon)를 추출합니다...", out_path)
        # Create Spatial Index
        model.createspatialindex(fishnetliving)
        clipedfishnetliving = model.clipwithQgis(input=fishnetliving,
                                                 onlyselected=False,
                                                 overlay=model.boundary,
                                                 output=out_path)

        # ID 추가
        out_path = os.path.join(self.workpath, 'cliped_living.gpkg')
        self.setDebugProgressMsg("세생활권 레이어(Polygon)에 ID필드({})를 추가합니다...".format(livingID), out_path)
        clipedfishnetliving2 = model.addIDField(input=clipedfishnetliving, idfid=livingID, output=out_path)


        # 세생활권 레이어 정리 : 인구 레이어와의 Spatial Join을 통해 연계되지 않은 피처 제거
        out_path = os.path.join(self.workpath, 'cliped_fishnetliving_discarded.gpkg')
        self.setDebugProgressMsg("세생활권 레이어(Polygon)와 인구레이어를 공간 조인하고, 조인되지 않는 데이터는 삭제합니다...", out_path)
        # Create Spatial Index
        model.createspatialindex(clipedfishnetliving2)
        model.createspatialindex(clipedpop)
        tmpliving = model.joinattributesbylocation(input=clipedfishnetliving2,
                                                      join=clipedpop,
                                                      joinfiels=[],
                                                      discardnomatching=True,
                                                      output=out_path
                                                      )

        ######################################################################################################
        out_path = os.path.join(self.workpath, 'only_living_has_pop.gpkg')
        self.setDebugProgressMsg('인구와 조인된 세생활권 레이어(Polygon)를 PK필드({})로 Dissolve 하여 중복데이터를 제거합니다'.format(livingID), out_path)
        # Create Spatial Index
        model.createspatialindex(tmpliving)
        clipedliving = model.dissolvewithQgis(input=tmpliving, onlyselected=False, field=[livingID], output=out_path)




        # 불필요한 필드 값 제거(IN_LIVINGAREA)
        out_path = os.path.join(self.workpath, 'cliped_living2.gpkg')
        self.setDebugProgressMsg("세생활권 레이어(Polygon)에 필수 필드({})를 제외한 데이터를 삭제합니다...".format(livingID), out_path)
        clipedliving = model.deleteFields(input=clipedliving, requredfields=[livingID], output=out_path)


        if isinstance(clipedliving, str):
            model.livingareaLayer = model.writeAsVectorLayer(clipedliving)
        else:
            model.livingareaLayer = clipedliving
        model.livingareaIDField = livingID


        # # 1-5 분석 지역 데이터 추출 : 인구데이터
        # if self.feedback.isCanceled(): return None
        # clipedpop = model.clipwithQgis(input=self.parameters['IN_POP'].sourceName(),
        #                                onlyselected=self.parameters['IN_NODE_ONLYSELECTED'],
        #                                overlay=boundary)
        #
        # out_path = ''
        # if self.debugging: out_path = os.path.join(self.workpath, 'cliped_pop.gpkg')
        # clipedpop = model.addIDField(input=clipedpop, idfid=popID, output=out_path)
        # model.popIDField = popID
        # model.popcntField = self.parameters['IN_POP_CNTFID']
        #
        #
        # # 불필요한 필드 값 제거(IN_POP)
        # out_path = ''
        # if self.debugging: out_path = os.path.join(self.workpath, 'cliped_pop2.gpkg')
        # # if isinstance(clipedpop, str):
        # #     tmplyr = model.writeAsVectorLayer(clipedpop)
        # # else:
        # #     tmplyr = clipedpop
        # clipedpop = model.deleteFields(input=clipedpop, requredfields=[popID, self.parameters['IN_POP_CNTFID']], output=out_path)


        # 1-6 분석 지역 데이터 추출 : 기존 생활 SOC 시설
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_curSOCWithNode.gpkg')
        self.setDebugProgressMsg("분석 영역에 해당하는 기존시설데이터를 추출합니다...", out_path)
        # Create Spatial Index
        model.createspatialindex(self.parameters['IN_CURSOC'].sourceName())
        clipedCurSOC = model.clipwithQgis(input=self.parameters['IN_CURSOC'].sourceName(),
                                          onlyselected=self.parameters['IN_CURSOC_ONLYSELECTED'],
                                          overlay=boundary,
                                          output=out_path)

        # 불필요한 필드 값 제거(IN_CURSOC)
        out_path = os.path.join(self.workpath, 'cliped_curSOCWithNode2.gpkg')
        self.setDebugProgressMsg("기존시설데이터에 필수 필드({})를 제외한 데이터를 삭제합니다...".format("NONE"), out_path)
        clipedCurSOC = model.deleteFields(input=clipedCurSOC, requredfields=[], output=out_path)


        #
        #
        #
        #
        #
        ################# [2 단계] 세생활권 인구정보와 생활SOC정보 분석 #################
        self.setProgressMsg('[2 단계] 세생활권 인구정보와 생활SOC 분석......')
        # 2-1 거주인구 지점의 최근린 생활SOC지점 검색
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'curSOCwithNode.gpkg')
        self.setDebugProgressMsg("기존시설데이터에 최근린 NODE를 찾습니다...", out_path)
        # Create Spatial Index
        model.createspatialindex(clipedCurSOC)
        model.createspatialindex(model.nodelayer)
        curSocwithNode = model.nearesthubpoints(input=clipedCurSOC,
                                                onlyselected=False,
                                                sf_hub=model.nodelayer,
                                                hubfield=nodeID,
                                                output=out_path
                                                )
        if isinstance(curSocwithNode, str):
            model.currentSOC = model.writeAsVectorLayer(curSocwithNode)
        else:
            model.currentSOC = curSocwithNode

        # 2-2 거주인구 지점의 최근린 노드 검색
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'popwithNode.gpkg')
        self.setDebugProgressMsg("인구데이터의 최근린 NODE를 찾습니다...", out_path)
        # Create Spatial Index
        model.createspatialindex(clipedpop)
        model.createspatialindex(model.nodelayer)
        popWithNode = model.nearesthubpoints(input=clipedpop,
                                            onlyselected=False,
                                            sf_hub=model.nodelayer,
                                            hubfield=model.nodeIDfield,
                                            output=out_path
                                            )


        # 2-3 개별거주인구와 세생활권 intersection : 개별 거주인구와 모든 세생활권까지의 거리 계산
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_popaddedlivingarea.gpkg')
        self.setDebugProgressMsg(
            "각 인구데이터에 교차(intersection)하는 세생활권데이터를 연산하고, 필수 필드({},{},{},{})만 남겨놓습니다...".format(model.popIDField, model.nodeIDfield,
                                                                                 model.popcntField,
                                                                                 model.livingareaIDField), out_path)
        # Create Spatial Index
        model.createspatialindex(popWithNode)
        model.createspatialindex(clipedliving)
        popWithNodeaddedliving = model.intersection(input=popWithNode,
                                                    inputfields=[model.popIDField,
                                                                 model.nodeIDfield,
                                                                 model.popcntField],
                                                    inputonlyseleceted=False,
                                                    overlay=clipedliving,
                                                    overayprefix='',
                                                    overlayer_fields=[model.livingareaIDField],
                                                    output=out_path
                                                    )

        if isinstance(popWithNodeaddedliving, str):
            model.populationLayer = model.writeAsVectorLayer(popWithNodeaddedliving)
        else:
            model.populationLayer = popWithNodeaddedliving

        #
        #
        #
        #
        #
        ################# [3 단계] 최단거리 분석을 위한 네트워크 데이터 생성 #################
        self.setProgressMsg('[3 단계] 최단거리 분석을 위한 네트워크 데이터 생성......\n(분석 조건에 따라 10분~60분 이상 소요됩니다...)')
        # 3-1 networkx 객체 생성
        if self.feedback.isCanceled(): return None
        isoneway = (self.parameters['IN_LINK_TYPE'] == 0)
        

        model.initNXGraph(isoneway=isoneway)
        self.setDebugProgressMsg("링크데이터를 활용하여 networkx의 graph객체를 생성합니다...")
        graph = model.createNodeEdgeInGraph()

        # 3-2 모든 노드간의 최단 거리 분석
        if self.feedback.isCanceled(): return None
        alllink = None
        # if self.debugging: alllink = os.path.join(self.workpath, 'alllink.pickle')
        model.cutoff = self.parameters['IN_LIMIT_DIST']
        model.outofcutoff = self.parameters['IN_LIMIT_DIST'] * self.cutoffconst_acc

        self.setDebugProgressMsg("{} 최단거리 알고리즘을 통해 네트워크분석을 수행하여 메모리에 저장합니다...".format("dijkstra"))
        allshortestnodes = model.shortestAllnodes(algorithm='dijkstra',
                                                  output_alllink=alllink)

        #
        #
        #
        #
        #
        ################# [4 단계] 접근성 분석(네트워크) #################
        self.setProgressMsg('[4 단계] 접근성 분석(네트워크)......')
        # 4-1 세생활권의 접근성 분석
        if self.feedback.isCanceled(): return None
        self.setDebugProgressMsg("세생활권의 최근린 SOC 시설을 찾습니다...")
        self.setDebugProgressMsg("anal_accessibilityCurSOC_network 실행...")
        dfPop = model.anal_accessibilityCurSOC_network()

        # 4-2 접근성 분석 결과 평가
        if self.feedback.isCanceled(): return None
        self.setDebugProgressMsg("접근성 지수를 계산합니다...")
        self.setDebugProgressMsg("make_Accessbillityscore 실행...")
        finallayer = model.make_Accessbillityscore(isNetwork=True, output=self.parameters["OUTPUT"])

        return finallayer




    def execute_efficiency_in_straight(self):
        try:
            from .soc_locator_model import soc_locator_model
        except ImportError:
            from soc_locator_model import soc_locator_model
        model = soc_locator_model(feedback=self.feedback, context=self.context, debugmode=self.debugging, workpath=self.workpath)

        #
        #
        #
        #
        #
        ################# [1 단계] 분석 위한 데이터 초기화 : 분석 영역 데이터 추출 #################
        self.setProgressMsg('[1 단계] 분석을 위한 데이터를 초기화 합니다......')
        # 1-1 분석 영역 데이터 생성
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'boundary.gpkg')
        self.setDebugProgressMsg("대상지 레이어에서 분석 영역을 추출합니다...", out_path)
        boundary = model.dissolvewithQgis(input=self.parameters['IN_SITE'].sourceName(),
                                          onlyselected=self.parameters['IN_SITE_ONLYSELECTED'],
                                          output=out_path)
        if isinstance(boundary, str):
            model.boundary = model.writeAsVectorLayer(boundary)
        else:
            model.boundary = boundary

        # 1-2 분석 지역 데이터 추출 : 인구데이터
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_pop.gpkg')
        self.setDebugProgressMsg("분석 영역에 해당하는 인구 데이터를 추출합니다...", out_path)
        clipedpop = model.clipwithQgis(input=self.parameters['IN_POP'].sourceName(),
                                       onlyselected=self.parameters['IN_POP_ONLYSELECTED'],
                                       overlay=boundary,
                                       output=out_path)

        # 불필요한 필드 값 제거(IN_POP)
        out_path = os.path.join(self.workpath, 'cliped_pop2.gpkg')
        self.setDebugProgressMsg("인구 데이터에 필수 필드({})를 제외한 데이터를 삭제합니다...".format(self.parameters['IN_POP_CNTFID']), out_path)
        clipedpop = model.deleteFields(input=clipedpop, requredfields=[self.parameters['IN_POP_CNTFID']],
                                       output=out_path)

        # 1-3 분석 지역 데이터 추출 : 기존 생활 SOC 시설
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_curSOC.gpkg')
        self.setDebugProgressMsg("분석 영역에 해당하는 기존시설데이터를 추출합니다...", out_path)
        clipedCurSOC = model.clipwithQgis(input=self.parameters['IN_CURSOC'].sourceName(),
                                          onlyselected=self.parameters['IN_CURSOC_ONLYSELECTED'],
                                          overlay=boundary,
                                          output=out_path)

        # 불필요한 필드 값 제거(IN_CURSOC)
        out_path = os.path.join(self.workpath, 'cliped_curSOC2.gpkg')
        self.setDebugProgressMsg("기존시설데이터에 필수 필드({})를 제외한 데이터를 삭제합니다...".format("NONE"), out_path)
        clipedCurSOC = model.deleteFields(input=clipedCurSOC, requredfields=[], output=out_path)

        if isinstance(clipedCurSOC, str):
            model.currentSOC = model.writeAsVectorLayer(clipedCurSOC)
        else:
            model.currentSOC = clipedCurSOC

        model.cutoff = self.parameters['IN_LIMIT_DIST']
        model.outofcutoff = self.parameters['IN_LIMIT_DIST'] * self.cutoffconst_eff
        #
        #
        #
        #
        #
        ################# [2 단계] 생활 SOC 잠재적 위치 데이터 생성 #################
        curStep = 2
        self.setProgressMsg('[{} 단계] 생활 SOC 잠재적 위치 데이터 생성......'.format(curStep))
        # 3-1  잠재적 위치 데이터 생성
        if self.feedback.isCanceled(): return None
        usergrid = self.parameters['IN_USERGRID']

        gridlayer = None
        onlyselected = False
        if usergrid == None:
            self.setDebugProgressMsg("잠재적 후보지 데이터(Point-{}m)를 생성합니다..".format(self.parameters['IN_GRID_SIZE']), out_path)
            out_path = os.path.join(self.workpath, 'grid.gpkg')
            gridlayer = model.createGridfromLayer(sourcelayer=model.boundary,
                                                  gridsize=self.parameters['IN_GRID_SIZE'],
                                                  output=out_path)
        else:
            gridlayer = self.parameters['IN_USERGRID'].sourceName()
            onlyselected = self.parameters['IN_USERGRID_ONLYSELECTED']



        # 3-2 분석 지역 데이터 추출 : 잠재적 위치
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_grid.gpkg')
        self.setDebugProgressMsg("분석 영역에 해당하는 잠재적 후보지 데이터를 추출합니다...", out_path)
        clipedgrid = model.clipwithQgis(input=gridlayer,
                                        onlyselected=onlyselected,
                                        overlay=model.boundary,
                                        output=out_path)

        if isinstance(clipedgrid, str):
            grid = model.writeAsVectorLayer(clipedgrid)
        else:
            grid = clipedgrid


        out_path = os.path.join(self.workpath, 'cliped_grid_single.gpkg')
        self.setDebugProgressMsg("잠재적 후보지 데이터를 싱글파트로 변환합니다...", out_path)
        grid = model.multiparttosingleparts(grid, output=out_path)



        #add grid id : 코드 일관성 유지를 위해 자동으로 생성되는 id사용안함(사용자 후보지 고려)
        gridid = "GRID_ID"
        out_path = os.path.join(self.workpath, 'final_grid.gpkg')
        self.setDebugProgressMsg("후보지 데이터에 ID필드({})를 추가합니다...".format(gridid), out_path)
        grid = model.addIDField(input=grid, idfid=gridid, output=out_path)
        model.potentialID = gridid


        if isinstance(grid, str):
            model.potentiallayer = model.writeAsVectorLayer(grid)
        else:
            model.potentiallayer = grid


        if self.debugging: self.setProgressMsg("잠재적 후보지 : {}개 ".format(len(model.potentiallayer)))



        #
        #
        #
        #
        #
        ################# [3 단계] 효율성 분석(직선거리) #################
        self.setProgressMsg('[3 단계] 효율성 분석(직선거리)......')
        # 5-1 효율성 분석 : 기존 생활 SOC 시설
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'bufferedCurSOC.gpkg')
        self.setDebugProgressMsg("기존시설 레이어에 버퍼({}m)데이터를 생성합니다...".format(model.cutoff), out_path)
        bufferedSOC = model.bufferwithQgis(input=model.currentSOC,
                                           onlyselected=False,
                                           distance=model.cutoff,
                                           output=out_path)

        # # 5-2 효율성 분석 : 기존 생활 SOC 시설(기 서비스 지역 배제 비율 적)
        model.popcntField = self.parameters['IN_POP_CNTFID']
        popexlusrate = self.parameters['IN_POP_EXCLUSION']

        # self.setDebugProgressMsg("인구 레이어의 공간인덱스를 생성합니다")
        # clipedpop = model.createspatialindex(clipedpop)


        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'selbyloc.gpkg')
        self.setDebugProgressMsg("인구 배제율({}%)이 적용된 인구데이터를 생성합니다...".format(popexlusrate), out_path)
        poplyr = model.applypopratioinselectedEuclidean(input=clipedpop,
                                                      popfield=self.parameters['IN_POP_CNTFID'],
                                                      exlusrate=popexlusrate,
                                                      applyArea=bufferedSOC,
                                                      output=out_path)

        # # 5-2 효율성 분석 : 기존 생활 SOC 시설(기 서비스 지역 제거)
        # if self.feedback.isCanceled(): return None
        # if self.debugging: self.setProgressMsg('기존서비스되는 인구 삭제.......')
        # out_path = ''
        # if self.debugging: out_path = os.path.join(self.workpath, 'popremovedCurSOC.gpkg')
        # poplyr = model.differencelayer(input=clipedpop,용
        #                                onlyselected=False,
        #                                overlayer=bufferedSOC,
        #                                overonlyselected=False,
        #                                output=out_path)
        if isinstance(poplyr, str):
            model.populationLayer = model.writeAsVectorLayer(poplyr)
        else:
            model.populationLayer = poplyr



        # 5-3 효율성 분석 : 잠재적 위치(서비스 영역 설정)
        out_path = os.path.join(self.workpath, 'popenSvrArea.gpkg')
        self.setDebugProgressMsg("후보지 레이어에 버퍼({}m)데이터를 생성합니다...".format(model.cutoff), out_path)
        potenSvrArea = model.bufferwithQgis(input=model.potentiallayer,
                                            onlyselected=False,
                                            distance=model.cutoff,
                                            output=out_path)


        self.setDebugProgressMsg("후보지 레이어의 공간인덱스를 생성합니다")
        potenSvrArea = model.createspatialindex(potenSvrArea)


        # 5-4 효율성 분석 : 잠재적 위치(잠재적 위치 서비스 지역 분석)
        out_path = os.path.join(self.workpath, 'popaddedpotenid.gpkg')
        self.setDebugProgressMsg("후보지 레이어와 인구레이어를 공간 조인합니다...", out_path)
        popaddedpoten = model.joinattributesbylocation(input=potenSvrArea,
                                                       join=model.populationLayer,
                                                       joinfiels=[model.popcntField],
                                                       output=out_path
                                                       )




        # 해당 인구레이어는 잠재적레이어와 outter join 된 결과임
        if isinstance(popaddedpoten, str):
            model.populationLayer = model.writeAsVectorLayer(popaddedpoten)
        else:
            model.populationLayer = popaddedpoten


        # 5-5 효율성 분석 : 잠재적 위치 분석 실행
        if self.feedback.isCanceled(): return None
        # 각 잠재적 위치의 서비스 영역내 포함되는 인구수
        self.setDebugProgressMsg("효율성 점수를 계산합니다...")
        self.setDebugProgressMsg("anal_efficiencyPotenSOC_straight 실행...")
        potengpd = model.anal_efficiencyPotenSOC_straight()



        # 5-6 효율성 분석 결과 평가
        if self.feedback.isCanceled(): return None
        self.setDebugProgressMsg("효율성 지수를 계산합니다...")
        out_path = os.path.join(self.workpath, 'analyzed_layer.gpkg')
        finallayer = model.make_efficiencyscore(output=out_path)





        self.setDebugProgressMsg("최종결과를 폴리곤({})으로 변환합니다...".format(self.parameters['IN_GRID_SIZE']))
        finallayer2 = model.rectanglesovalsdiamonds(input=finallayer, onlyselected=False,
                                                    width=self.parameters['IN_GRID_SIZE'],
                                                    height=self.parameters['IN_GRID_SIZE'],
                                                    output=self.parameters["OUTPUT"])



        return finallayer2

    def execute_efficiency_in_network(self):
        try:
            from .soc_locator_model import soc_locator_model
        except ImportError:
            from soc_locator_model import soc_locator_model
        model = soc_locator_model(feedback=self.feedback, context=self.context, debugmode=self.debugging, workpath=self.workpath)

        popID = 'POP_ID'
        #
        #
        #
        #
        #
        model.classify_count = self.parameters['IN_CALSSIFYNUM']
        ################# [1 단계] 분석 위한 데이터 초기화 : 분석 영역 데이터 추출 #################
        self.setProgressMsg('[1 단계] 분석을 위한 데이터를 초기화 합니다......')
        # 1-1 분석 영역 데이터 생성
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'boundary.gpkg')
        self.setDebugProgressMsg("대상지 레이어에서 분석 영역을 추출합니다...", out_path)
        # Create Spatial Index
        model.createspatialindex(self.parameters['IN_SITE'].sourceName())
        boundary = model.dissolvewithQgis(input=self.parameters['IN_SITE'].sourceName(),
                                          onlyselected=self.parameters['IN_SITE_ONLYSELECTED'],
                                          output=out_path)

        if isinstance(boundary, str):
            model.boundary = model.writeAsVectorLayer(boundary)
        else:
            model.boundary = boundary

        # 1-2 분석 지역 데이터 추출 : 노드
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_node.gpkg')
        self.setDebugProgressMsg("분석 영역에 해당하는 노드 데이터를 추출합니다...", out_path)
        # Create Spatial Index
        model.createspatialindex(self.parameters['IN_NODE'].sourceName())
        model.createspatialindex(boundary)
        clipednode = model.clipwithQgis(input=self.parameters['IN_NODE'].sourceName(),
                                        onlyselected=self.parameters['IN_NODE_ONLYSELECTED'],
                                        overlay=boundary,
                                        output=out_path)

        # 최종 노드, 링크 레이어 클래스에 할당
        if isinstance(clipednode, str):
            model.nodelayer = model.writeAsVectorLayer(clipednode)
        else:
            model.nodelayer = clipednode
        model.nodeIDfield = self.parameters['IN_NODE_ID']


        # 1-3 분석 지역 데이터 추출 : 링크
        if self.feedback.isCanceled(): return None
        self.setDebugProgressMsg("분석 영역의 버퍼(2000m)데이터를 생성합니다...")
        boundary2000 = model.bufferwithQgis(input=boundary,
                                            onlyselected=False,
                                            distance=2000)

        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_link.gpkg')
        self.setDebugProgressMsg("분석 영역(2000m)에 해당하는 링크 데이터를 추출합니다...", out_path)
        # Create Spatial Index
        model.createspatialindex(self.parameters['IN_LINK'].sourceName())
        model.createspatialindex(boundary2000)
        clipedlink = model.clipwithQgis(input=self.parameters['IN_LINK'].sourceName(),
                                        onlyselected=self.parameters['IN_LINK_ONLYSELECTED'],
                                        overlay=boundary2000,
                                        output=out_path)


        if isinstance(clipedlink, str):
            model.linklayer = model.writeAsVectorLayer(clipedlink)
        else:
            model.linklayer = clipedlink
        model.linkFromnodefield = self.parameters['IN_LINK_FNODE']
        model.linkTonodefield = self.parameters['IN_LINK_TNODE']
        model.linklengthfield = self.parameters['IN_LINK_LENGTH']
        model.linkSpeed = self.parameters['IN_LINK_SPEED']


        # 1-4 분석 지역 데이터 추출 : 인구데이터
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_pop.gpkg')
        self.setDebugProgressMsg("분석 영역에 해당하는 인구 데이터를 추출합니다...", out_path)
        # Create Spatial Index
        model.createspatialindex(self.parameters['IN_POP'].sourceName())
        clipedpop = model.clipwithQgis(input=self.parameters['IN_POP'].sourceName(),
                                       onlyselected=self.parameters['IN_NODE_ONLYSELECTED'],
                                       overlay=boundary,
                                       output=out_path)
        # 불필요한 필드 값 제거(IN_POP)
        out_path = os.path.join(self.workpath, 'cliped_pop2.gpkg')
        self.setDebugProgressMsg("인구 데이터에 필수 필드({})를 제외한 데이터를 삭제합니다...".format(self.parameters['IN_POP_CNTFID']), out_path)
        clipedpop = model.deleteFields(input=clipedpop, requredfields=[self.parameters['IN_POP_CNTFID']],
                                       output=out_path)


        # 1-5 분석 지역 데이터 추출 : 기존 생활 SOC 시설
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_curSOC.gpkg')
        self.setDebugProgressMsg("분석 영역에 해당하는 기존시설데이터를 추출합니다...", out_path)
        # Create Spatial Index
        model.createspatialindex(self.parameters['IN_CURSOC'].sourceName())
        clipedCurSOC = model.clipwithQgis(input=self.parameters['IN_CURSOC'].sourceName(),
                                          onlyselected=self.parameters['IN_CURSOC_ONLYSELECTED'],
                                          overlay=boundary,
                                          output=out_path)

        out_path = os.path.join(self.workpath, 'cliped_curSOC2.gpkg')
        self.setDebugProgressMsg("기존시설데이터에 필수 필드({})를 제외한 데이터를 삭제합니다...".format("NONE"), out_path)
        clipedCurSOC = model.deleteFields(input=clipedCurSOC, requredfields=[], output=out_path)

        #
        #
        #
        #
        #
        ################# [2 단계]  인구정보와 생활SOC정보 분석 #################
        self.setProgressMsg('[2 단계] 인구정보와 생활SOC 분석......')
        # 2-1 거주인구 지점의 최근린 생활SOC지점 검색
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'curSOCwithNode.gpkg')
        self.setDebugProgressMsg("기존시설데이터에 최근린 NODE를 찾습니다...", out_path)
        # Create Spatial Index
        model.createspatialindex(clipedCurSOC)
        model.createspatialindex(model.nodelayer)
        curSocwithNode = model.nearesthubpoints(input=clipedCurSOC,
                                                onlyselected=False,
                                                sf_hub=model.nodelayer,
                                                hubfield=model.nodeIDfield,
                                                output=out_path
                                                )

        if isinstance(curSocwithNode, str):
            model.currentSOC = model.writeAsVectorLayer(curSocwithNode)
        else:
            model.currentSOC = curSocwithNode

        # 2-2 거주인구 지점의 최근린 노드  검색
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'popwithNode.gpkg')
        self.setDebugProgressMsg("인구데이터의 최근린 NODE를 찾습니다...", out_path)
        # Create Spatial Index
        model.createspatialindex(clipedpop)
        model.createspatialindex(model.nodelayer)
        popWithNode = model.nearesthubpoints(input=clipedpop,
                                             onlyselected=False,
                                             sf_hub=model.nodelayer,
                                             hubfield=model.nodeIDfield,
                                             output=out_path
                                             )

        # ID 만들어 넣기 $id
        out_path = os.path.join(self.workpath, 'popwithNode1.gpkg')
        self.setDebugProgressMsg("인구 데이터에 ID필드({})를 추가합니다...".format(popID), out_path)
        popwthNode2 = model.addIDField(input=popWithNode, idfid=popID, output=out_path)

        model.popIDField = popID
        model.popcntField = self.parameters['IN_POP_CNTFID']
        if isinstance(popwthNode2, str):
            model.populationLayer = model.writeAsVectorLayer(popwthNode2)
        else:
            model.populationLayer = popwthNode2
        #
        #
        #
        #
        #
        ################# [3 단계] 생활 SOC 잠재적 위치 데이터 생성 #################
        curStep = 3
        self.setProgressMsg('[{} 단계] 생활 SOC 잠재적 위치 데이터 생성......'.format(curStep))
        # 3-1  잠재적 위치 데이터 생성
        if self.feedback.isCanceled(): return None

        usergrid = self.parameters['IN_USERGRID']

        gridlayer = None
        onlyselected = False
        if usergrid == None:
            self.setDebugProgressMsg("잠재적 후보지 데이터(Point-{}m)를 생성합니다..".format(self.parameters['IN_GRID_SIZE']), out_path)
            out_path = os.path.join(self.workpath, 'grid.gpkg')
            gridlayer = model.createGridfromLayer(sourcelayer=model.boundary,
                                                  gridsize=self.parameters['IN_GRID_SIZE'],
                                                  output=out_path)
        else:
            gridlayer = self.parameters['IN_USERGRID'].sourceName()
            onlyselected = self.parameters['IN_USERGRID_ONLYSELECTED']


        # 3-2 분석 지역 데이터 추출 : 잠재적 위치
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_grid.gpkg')
        self.setDebugProgressMsg("분석 영역에 해당하는 잠재적 후보지 데이터를 추출합니다...", out_path)
        # Create Spatial Index
        model.createspatialindex(gridlayer)
        clipedgrid = model.clipwithQgis(input=gridlayer,
                                        onlyselected=onlyselected,
                                        overlay=model.boundary,
                                        output=out_path)

        if isinstance(clipedgrid, str):
            grid = model.writeAsVectorLayer(clipedgrid)
        else:
            grid = clipedgrid

        out_path = os.path.join(self.workpath, 'cliped_grid_single.gpkg')
        self.setDebugProgressMsg("잠재적 후보지 데이터를 싱글파트로 변환합니다...", out_path)
        # Create Spatial Index
        model.createspatialindex(grid)
        grid = model.multiparttosingleparts(grid, output=out_path)


        # add grid id : 코드 일관성 유지를 위해 자동으로 생성되는 id사용안함(사용자 후보지 고려)
        gridid = "GRID_ID"
        out_path = os.path.join(self.workpath, 'final_grid.gpkg')
        self.setDebugProgressMsg("후보지 데이터에 ID필드({})를 추가합니다...".format(gridid), out_path)
        grid = model.addIDField(input=grid, idfid=gridid, output=out_path)
        model.potentialID = gridid

        # 3-3 잠재적 위치의 최근린 노드  검색
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'gridwithNode.gpkg')
        self.setDebugProgressMsg("후보지 데이터의 최근린 NODE를 찾습니다...", out_path)
        # Create Spatial Index
        model.createspatialindex(model.nodelayer)
        gridwithNode = model.nearesthubpoints(input=grid,
                                              onlyselected=False,
                                              sf_hub=model.nodelayer,
                                              hubfield=model.nodeIDfield,
                                              output=out_path
                                              )
        if isinstance(gridwithNode, str):
            model.potentiallayer = model.writeAsVectorLayer(gridwithNode)
        else:
            model.potentiallayer = gridwithNode
        #
        #
        #
        #
        #
        ################# [3 단계] 최단거리 분석을 위한 네트워크 데이터 생성 #################
        self.setProgressMsg('[3 단계] 최단거리 분석을 위한 네트워크 데이터 생성......\n(분석 조건에 따라 10분~60분 이상 소요됩니다...)')
        # 3-1 networkx 객체 생성
        if self.feedback.isCanceled(): return None
        isoneway = (self.parameters['IN_LINK_TYPE'] == 0)
        model.initNXGraph(isoneway=isoneway)
        self.setDebugProgressMsg("링크데이터를 활용하여 networkx의 graph객체를 생성합니다...")
        graph = model.createNodeEdgeInGraph()

        # 3-2 모든 노드간의 최단 거리 분석
        if self.feedback.isCanceled(): return None
        alllink = None
        # if self.debugging: alllink = os.path.join(self.workpath, 'alllink.pickle')
        model.cutoff = self.parameters['IN_LIMIT_DIST']
        model.outofcutoff = self.parameters['IN_LIMIT_DIST'] * self.cutoffconst_eff

        self.setDebugProgressMsg("{} 최단거리 알고리즘을 통해 네트워크분석을 수행하여 메모리에 저장합니다...".format("dijkstra"))
        allshortestnodes = model.shortestAllnodes(algorithm='dijkstra',
                                                  output_alllink=alllink)

        #
        #
        #
        #
        #
        ################# [4 단계] 효율성 분석(네트워크) #################
        self.setProgressMsg('[4 단계] 효율성 분석(네트워크)......')
        # 5-1 효율성 분석 : 기존 생활 SOC 시설
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'poptable_afteranalcursoc.csv')

        self.setDebugProgressMsg("개별 인구데이터의 최근린 SOC 시설을 찾습니다...", out_path)
        self.setDebugProgressMsg("anal_efficiencyCurSOC_network 실행...")

        dfPop = model.anal_efficiencyCurSOC_network()
        if self.debugging: dfPop.to_csv(out_path)


        # # 5-2 효율성 분석 : 기존 생활 SOC 시설(기 서비스 지역 배제 비율 적)
        model.popcntField = self.parameters['IN_POP_CNTFID']
        popexlusrate = self.parameters['IN_POP_EXCLUSION']

        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'selbyloc.gpkg')
        self.setDebugProgressMsg("인구 배제율({}%)이 적용된 인구데이터를 생성합니다...".format(popexlusrate), out_path)
        # Create Spatial Index
        model.createspatialindex(clipedpop)
        poplayerwithCurSOC = model.applypopratioinselectedNetwork(input=clipedpop,
                                                        popfield=self.parameters['IN_POP_CNTFID'],
                                                        exlusrate=popexlusrate,
                                                        output=out_path)


        # # 5-2 효율성 분석 : 기존 생활 SOC 시설(기 서비스 지역 제거)
        # if self.feedback.isCanceled(): return None
        # if self.debugging: self.setProgressMsg('이미 서비스 되고 있는 인구데이터를 제거합니다.....')
        # poplayerwithCurSOC = model.removeRelCurSOCInPoplayer()


        if isinstance(poplayerwithCurSOC, str):
            model.populationLayer = model.writeAsVectorLayer(poplayerwithCurSOC)
        else:
            model.populationLayer = poplayerwithCurSOC

        out_path = os.path.join(self.workpath, 'popwithNoderemovedCurSOC.gpkg')
        poplyr = model.vectorlayer2ShapeFile(model.populationLayer, output=out_path)



        # 5-3 효율성 분석 : 잠재적 위치(서비스 영역 설정)
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'popenSvrArea.gpkg')
        self.setDebugProgressMsg("후보지 레이어에 버퍼({}m)데이터를 생성합니다...".format(model.cutoff), out_path)
        # Create Spatial Index
        model.createspatialindex(model.potentiallayer)
        potenSvrArea = model.bufferwithQgis(input=model.potentiallayer,
                                            onlyselected=False,
                                            distance=model.cutoff,
                                            output=out_path)


        # 5-4 효율성 분석 : 잠재적 위치(잠재적 위치 서비스 지역 분석)
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'popaddedpotenid.gpkg')
        self.setDebugProgressMsg("후보지 레이어와 인구레이어를 공간 조인합니다...", out_path)
        overprefix = 'JN_'
        # Create Spatial Index
        model.createspatialindex(potenSvrArea)
        model.createspatialindex(model.populationLayer)
        popWithNodeaddedpoten = model.joinattributesbylocation(input=potenSvrArea,
                                                               join=model.populationLayer,
                                                               prefix=overprefix,
                                                               joinfiels=[model.popcntField, model.nodeIDfield],
                                                               output=out_path
                                                               )

        # 해당 인구레이어는 잠재적레이어와 outter join 된 결과임
        if isinstance(popWithNodeaddedpoten, str):
            model.populationLayer = model.writeAsVectorLayer(popWithNodeaddedpoten)
        else:
            model.populationLayer = popWithNodeaddedpoten

        # 5-5 효율성 분석 : 잠재적 위치 분석 실행
        if self.feedback.isCanceled(): return None

        # shape file의 필드명 최대길이는 10자리 / 메모리에 있을때는 상관없음
        relpopNodeID = overprefix + model.nodeIDfield
        # if self.debugging: relpopNodeID = relpopNodeID[0:10]
        popcntfield = overprefix + model.popcntField
        # if self.debugging: popcntfield = popcntfield[0: 10]

        # 각 잠재적 위치의 서비스 영역내 포함되는 인구수
        self.setDebugProgressMsg("효율성 점수를 계산합니다...")
        self.setDebugProgressMsg("anal_efficiencyPotenSOC_network 실행...")
        potengpd = model.anal_efficiencyPotenSOC_network(relpopNodeID=relpopNodeID,
                                                         relpopcntfid=popcntfield)

        # 5-6 효율성 분석 결과 평가
        if self.feedback.isCanceled(): return None
        self.setDebugProgressMsg("효율성 지수를 계산합니다...")
        out_path = os.path.join(self.workpath, 'analyzed_layer.gpkg')
        finallayer = model.make_efficiencyscore(output=out_path)


        self.setDebugProgressMsg("최종결과를 폴리곤({})으로 변환합니다...".format(self.parameters['IN_GRID_SIZE']))
        finallayer2 = model.rectanglesovalsdiamonds(input=finallayer, onlyselected=False,
                                                    width=self.parameters['IN_GRID_SIZE'],
                                                    height=self.parameters['IN_GRID_SIZE'],
                                                    output=self.parameters["OUTPUT"])

        return finallayer2


    def execute_equity_in_network(self):
        try:
            from .soc_locator_model import soc_locator_model
        except ImportError:
            from soc_locator_model import soc_locator_model
        model = soc_locator_model(feedback=self.feedback, context=self.context, debugmode=self.debugging, workpath=self.workpath)

        curStep = 0
        curSOCID = 'CSOC_ID'
        popID = 'POP_ID'
        livingID = 'LIV_ID'

        #
        #
        #
        #
        #
        model.classify_count = self.parameters['IN_CALSSIFYNUM']

        ################# [1 단계] 분석 위한 데이터 초기화 : 분석 영역 데이터 추출 #################
        curStep += 1
        self.setProgressMsg('[{} 단계] 분석을 위한 데이터를 초기화 합니다......'.format(curStep))
        # 1-1 분석 영역 데이터 생성
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'boundary.gpkg')
        self.setDebugProgressMsg("대상지 레이어에서 분석 영역을 추출합니다...", out_path)
        boundary = model.dissolvewithQgis(input=self.parameters['IN_SITE'].sourceName(),
                                          onlyselected=self.parameters['IN_SITE_ONLYSELECTED'],
                                          output=out_path)
        if isinstance(boundary, str):
            model.boundary = model.writeAsVectorLayer(boundary)
        else:
            model.boundary = boundary

        # 1-2 분석 지역 데이터 추출 : 노드
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_node.gpkg')
        self.setDebugProgressMsg("분석 영역에 해당하는 노드 데이터를 추출합니다...", out_path)
        clipednode = model.clipwithQgis(input=self.parameters['IN_NODE'].sourceName(),
                                        onlyselected=self.parameters['IN_NODE_ONLYSELECTED'],
                                        overlay=boundary,
                                        output=out_path)

        if isinstance(clipednode, str):
            model.nodelayer = model.writeAsVectorLayer(clipednode)
        else:
            model.nodelayer = clipednode
        model.nodeIDfield = self.parameters['IN_NODE_ID']


        # 1-3 분석 지역 데이터 추출 : 링크
        if self.feedback.isCanceled(): return None
        self.setDebugProgressMsg("분석 영역의 버퍼(2000m)데이터를 생성합니다...")
        boundary2000 = model.bufferwithQgis(input=boundary,
                                            onlyselected=False,
                                            distance=2000)

        out_path = os.path.join(self.workpath, 'cliped_link.gpkg')
        self.setDebugProgressMsg("분석 영역(2000m)에 해당하는 링크 데이터를 추출합니다...", out_path)
        clipedlink = model.clipwithQgis(input=self.parameters['IN_LINK'].sourceName(),
                                        onlyselected=self.parameters['IN_LINK_ONLYSELECTED'],
                                        overlay=boundary2000,
                                        output=out_path)

        if isinstance(clipedlink, str):
            model.linklayer = model.writeAsVectorLayer(clipedlink)
        else:
            model.linklayer = clipedlink
        model.linkFromnodefield = self.parameters['IN_LINK_FNODE']
        model.linkTonodefield = self.parameters['IN_LINK_TNODE']
        model.linklengthfield = self.parameters['IN_LINK_LENGTH']
        model.linkSpeed = self.parameters['IN_LINK_SPEED']




        # 1-5 분석 지역 데이터 추출 : 인구데이터
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_pop.gpkg')
        self.setDebugProgressMsg("분석 영역에 해당하는 인구 데이터를 추출합니다...")
        clipedpop = model.clipwithQgis(input=self.parameters['IN_POP'].sourceName(),
                                       onlyselected=self.parameters['IN_NODE_ONLYSELECTED'],
                                       overlay=boundary,
                                       output=out_path)


        # 불필요한 필드 값 제거(IN_POP)
        out_path = os.path.join(self.workpath, 'cliped_pop2.gpkg')
        self.setDebugProgressMsg("인구 데이터에 필수 필드({})를 제외한 데이터를 삭제합니다...".format(self.parameters['IN_POP_CNTFID']), out_path)
        clipedpop = model.deleteFields(input=clipedpop, requredfields=[self.parameters['IN_POP_CNTFID']], output=out_path)

        out_path = os.path.join(self.workpath, 'cliped_pop3_withID.gpkg')
        self.setDebugProgressMsg("인구 데이터에 ID필드({})를 추가합니다...".format(popID), out_path)
        clipedpop = model.addIDField(input=clipedpop, idfid=popID, output=out_path)

        #

        # 1-6 분석 지역 데이터 추출 : 기존 생활 SOC 시설
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_curSOC.gpkg')
        self.setDebugProgressMsg("분석 영역에 해당하는 기존시설데이터를 추출합니다...", out_path)
        clipedCurSOC = model.clipwithQgis(input=self.parameters['IN_CURSOC'].sourceName(),
                                          onlyselected=self.parameters['IN_CURSOC_ONLYSELECTED'],
                                          overlay=boundary,
                                          output=out_path)

        # 불필요한 필드 값 제거(IN_CURSOC)
        out_path = os.path.join(self.workpath, 'cliped_curSOC2.gpkg')
        self.setDebugProgressMsg("기존시설데이터에 필수 필드({})를 제외한 데이터를 삭제합니다...".format("NONE"), out_path)
        clipedCurSOC = model.deleteFields(input=clipedCurSOC, requredfields=[], output=out_path)
        #
        #
        #
        #

        # 5. 기존시설 노드 찾기
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'curSOCwithNode.gpkg')
        self.setDebugProgressMsg("기존시설데이터에 최근린 NODE를 찾습니다...", out_path)
        curSocwithNode = model.nearesthubpoints(input=clipedCurSOC,
                                                onlyselected=False,
                                                sf_hub=model.nodelayer,
                                                hubfield=self.parameters['IN_NODE_ID'],
                                                output=out_path
                                                )

        if isinstance(curSocwithNode, str):
            model.currentSOC = model.writeAsVectorLayer(curSocwithNode)
        else:
            model.currentSOC = curSocwithNode

        #
        #
        #
        #
        #

        ################# [2 단계] 세생활권 인구정보와 생활SOC정보 분석 #################
        curStep += 1
        if False:
            self.setProgressMsg('[{} 단계] 세생활권 인구정보와 생활SOC 분석......'.format(curStep))
            # 2-1 분석 지역 데이터 추출 : 세생활권
            if self.feedback.isCanceled(): return None
            if self.debugging: self.setProgressMsg('세생활권 레이어를 초기화 합니다.....')
            clipedliving = model.clipwithQgis(input=self.parameters['IN_LIVINGAREA'].sourceName(),
                                              onlyselected=self.parameters['IN_LIVINGAREA_ONLYSELECTED'],
                                              overlay=model.boundary)
            out_path = os.path.join(self.workpath, 'cliped_living.gpkg')
            clipedliving = model.addIDField(input=clipedliving, idfid=livingID, output=out_path)

            # 불필요한 필드 값 제거(IN_LIVINGAREA)
            out_path = os.path.join(self.workpath, 'cliped_living2.gpkg')
            clipedliving = model.deleteFields(input=clipedliving, requredfields=[livingID], output=out_path)

            if isinstance(clipedliving, str):
                clipedliving = model.writeAsVectorLayer(clipedliving)
            else:
                clipedliving = clipedliving

            model.livingareaIDField = livingID



            # 2-1 세생활권내 인구 분석
            if self.feedback.isCanceled(): return None
            out_path = os.path.join(self.workpath, 'cliped_livingwithpop.gpkg')
            clipelivingwithpop = model.countpointsinpolygon(polylayer=clipedliving,
                                                            pointslayer=clipedpop,
                                                            field=self.parameters['IN_POP_CNTFID'],
                                                            weight=self.parameters['IN_POP_CNTFID'],
                                                            classfield=None,
                                                            output=out_path)

            if isinstance(clipelivingwithpop, str):
                clipelivingwithpop = model.writeAsVectorLayer(clipelivingwithpop)
            else:
                clipelivingwithpop = clipelivingwithpop

            # 2-2 거주인구 지점의 최근린 노드  검색
            if self.debugging: self.setProgressMsg('세생활권(인구) 인근 노드 찾기......')
            if self.feedback.isCanceled(): return None
            out_path = os.path.join(self.workpath, 'popwithNode.gpkg')
            popWithNode = model.nearesthubpoints(input=clipelivingwithpop,
                                                 onlyselected=False,
                                                 sf_hub=model.nodelayer,
                                                 hubfield=self.parameters['IN_NODE_ID'],
                                                 output=out_path
                                                 )
        else:
            if self.debugging: self.setProgressMsg('인구레이어의 인근 노드 찾기......')
            if self.feedback.isCanceled(): return None
            out_path = os.path.join(self.workpath, 'popwithNode.gpkg')
            self.setDebugProgressMsg("인구데이터의 최근린 NODE를 찾습니다...", out_path)
            popWithNode = model.nearesthubpoints(input=clipedpop,
                                                 onlyselected=False,
                                                 sf_hub=model.nodelayer,
                                                 hubfield=self.parameters['IN_NODE_ID'],
                                                 output=out_path
                                                 )


        if isinstance(popWithNode, str):
            model.populationLayer = model.writeAsVectorLayer(popWithNode)
        else:
            model.populationLayer = popWithNode
        model.popcntField = self.parameters['IN_POP_CNTFID']

        #
        #
        #
        #
        #
        ################# [3 단계] 생활 SOC 잠재적 위치 데이터 생성 #################
        curStep += 1
        self.setProgressMsg('[{} 단계] 생활 SOC 잠재적 위치 데이터 생성......'.format(curStep))
        # 3-1  잠재적 위치 데이터 생성
        if self.feedback.isCanceled(): return None

        usergrid = self.parameters['IN_USERGRID']
        gridlayer = None
        onlyselected = False
        if usergrid == None:
            out_path = os.path.join(self.workpath, 'grid.gpkg')
            self.setDebugProgressMsg("잠재적 후보지 데이터(Point-{}m)를 생성합니다..".format(self.parameters['IN_GRID_SIZE']), out_path)
            gridlayer = model.createGridfromLayer(sourcelayer=model.boundary,
                                                  gridsize=self.parameters['IN_GRID_SIZE'],
                                                  output=out_path)
        else:
            gridlayer = self.parameters['IN_USERGRID'].sourceName()
            onlyselected = self.parameters['IN_USERGRID_ONLYSELECTED']


        # 3-2 분석 지역 데이터 추출 : 잠재적 위치
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_grid.gpkg')
        self.setDebugProgressMsg("분석 영역에 해당하는 잠재적 후보지 데이터를 추출합니다...", out_path)
        clipedgrid = model.clipwithQgis(input=gridlayer,
                                        onlyselected=onlyselected,
                                        overlay=model.boundary,
                                        output=out_path)

        if isinstance(clipedgrid, str):
            grid = model.writeAsVectorLayer(clipedgrid)
        else:
            grid = clipedgrid

        out_path = os.path.join(self.workpath, 'cliped_grid_single.gpkg')
        self.setDebugProgressMsg("잠재적 후보지 데이터를 싱글파트로 변환합니다...", out_path)
        grid = model.multiparttosingleparts(grid, output=out_path)


        # add grid id : 코드 일관성 유지를 위해 자동으로 생성되는 id사용안함(사용자 후보지 고려)
        gridid = "GRID_ID"
        out_path = os.path.join(self.workpath, 'final_grid.gpkg')
        self.setDebugProgressMsg("후보지 데이터에 ID필드({})를 추가합니다...".format(gridid), out_path)
        grid = model.addIDField(input=grid, idfid=gridid, output=out_path)
        model.potentialID = gridid

        # 3-3 잠재적 위치의 최근린 노드  검색
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'gridwithNode.gpkg')
        self.setDebugProgressMsg("후보지 데이터의 최근린 NODE를 찾습니다...", out_path)
        gridwithNode = model.nearesthubpoints(input=grid,
                                              onlyselected=False,
                                              sf_hub=model.nodelayer,
                                              hubfield=self.parameters['IN_NODE_ID'],
                                              output=out_path
                                              )
        if isinstance(gridwithNode, str):
            model.potentiallayer = model.writeAsVectorLayer(gridwithNode)
        else:
            model.potentiallayer = gridwithNode


        if self.debugging: self.setProgressMsg("잠재적 후보지 : {}개 ".format(len(model.potentiallayer)))

        #
        #
        #
        #
        #
        ################# [4 단계] 최단거리 분석을 위한 네트워크 데이터 생성 #################
        curStep += 1
        self.setProgressMsg('[{} 단계] 최단거리 분석을 위한 네트워크 데이터 생성......\n(분석 조건에 따라 10분~60분 이상 소요됩니다...)'.format(curStep))
        # 4-1 networkx 객체 생성
        if self.feedback.isCanceled(): return None
        isoneway = (self.parameters['IN_LINK_TYPE'] == 0)
        model.initNXGraph(isoneway=isoneway)
        self.setDebugProgressMsg("링크데이터를 활용하여 networkx의 graph객체를 생성합니다...")
        graph = model.createNodeEdgeInGraph()

        # 5-2 모든 노드간의 최단 거리 분석
        if self.feedback.isCanceled(): return None
        alllink = None
        # if self.debugging: alllink = os.path.join(self.workpath, 'alllink.pickle')
        model.cutoff = self.parameters['IN_LIMIT_DIST']
        model.outofcutoff = self.parameters['IN_LIMIT_DIST'] * self.cutoffconst_equ
        self.setDebugProgressMsg("{} 최단거리 알고리즘을 통해 네트워크분석을 수행하여 메모리에 저장합니다...".format("dijkstra"))
        allshortestnodes = model.shortestAllnodes(algorithm='dijkstra',
                                                  output_alllink=alllink)

        #
        #
        #
        #
        #
        ################# [5 단계] 형평성 분석(네트워크) #################
        curStep += 1
        self.setProgressMsg('[{} 단계] 형평성 분석(네트워크)......'.format(curStep))
        # 5-1 형평성 분석 : 기존 생활 SOC 시설
        if self.feedback.isCanceled(): return None
        self.setDebugProgressMsg("기존 시설의 형평성 점수를 계산합니다...")
        self.setDebugProgressMsg("anal_AllCurSOC_network 실행...")
        dfPop = model.anal_AllCurSOC_network()

        # 5-3 형평성 분석 : 잠재적 위치
        if self.feedback.isCanceled(): return None
        self.setDebugProgressMsg("후보지의 형평성 점수를 계산합니다...")
        self.setDebugProgressMsg("anal_AllPotenSOC_network 실행...")
        potengpd = model.anal_AllPotenSOC_network()

        # 5-3 형평성 분석 결과 평가
        if self.feedback.isCanceled(): return None
        self.setDebugProgressMsg("형평성 지수를 계산합니다...")
        out_path = os.path.join(self.workpath, 'analyzed_layer.gpkg')
        finallayer = model.make_equityscore(isNetwork=True, output=out_path)



        self.setDebugProgressMsg("최종결과를 폴리곤({})으로 변환합니다...".format(self.parameters['IN_GRID_SIZE']))
        finallayer2 = model.rectanglesovalsdiamonds(input=finallayer, onlyselected=False,
                                                    width=self.parameters['IN_GRID_SIZE'],
                                                    height=self.parameters['IN_GRID_SIZE'],
                                                    output=self.parameters["OUTPUT"])



        return finallayer2



