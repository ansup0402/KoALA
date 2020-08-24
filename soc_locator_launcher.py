import os

class soc_locator_launcher:

    def __init__(self, feedback, context, parameters, debugging=False, workpath=None):
        self.debugging = debugging
        self.feedback = feedback
        self.context = context
        self.parameters = parameters
        self.workpath = workpath

        self.cutoffconst_acc = 1000000
        self.cutoffconst_eff = 1000000
        self.cutoffconst_equ = 1000000
        
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
        boundary = model.dissolvewithQgis(input=self.parameters['IN_SITE'].sourceName(),
                                          onlyselected=self.parameters['IN_SITE_ONLYSELECTED'])

        if isinstance(boundary, str):
            model.boundary = model.writeAsVectorLayer(boundary)
        else:
            model.boundary = boundary


        # 1-2 분석 지역 데이터 추출 : 인구데이터
        # self.setProgressMsg('..... 분석 지역 데이터 추출 : 인구 데이터')
        if self.feedback.isCanceled(): return None
        clipedpop = model.clipwithQgis(input=self.parameters['IN_POP'].sourceName(),
                                       onlyselected=self.parameters['IN_POP_ONLYSELECTED'],
                                       overlay=model.boundary)
        out_path = os.path.join(self.workpath, 'cliped_pop_tmp.shp')
        clipedpop = model.addIDField(input=clipedpop, idfid=popID, output=out_path)
        model.popIDField = popID
        model.popcntField = self.parameters['IN_POP_CNTFID']

        # 불필요한 필드 값 제거(IN_POP)
        out_path = os.path.join(self.workpath, 'cliped_pop.shp')
        if self.debugging: self.setProgressMsg("대상지역 인구 클립(필드 정리)(인구2) : \n{}\n\n".format(out_path))
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
        if self.debugging: self.setProgressMsg('세생활권 레이어 생성 : \n{}\n\n'.format(out_path))
        out_path = os.path.join(self.workpath, 'fishnetliving.shp')
        fishnetliving = model.createGridfromLayer(sourcelayer=model.boundary,
                                              gridsize=self.parameters['IN_LIVINGAREA'],
                                              type=2,
                                              output=out_path)


        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_fishnetliving.shp')
        if self.debugging:self.setProgressMsg('생성된 세생활권 클립 : \n{}\n\n'.format(out_path))
        clipedfishnetliving = model.clipwithQgis(input=fishnetliving,
                                        onlyselected=False,
                                        overlay=model.boundary,
                                        output=out_path)


        # ID 추가
        out_path = os.path.join(self.workpath, 'cliped_living.shp')
        clipedfishnetliving2 = model.addIDField(input=clipedfishnetliving, idfid=livingID, output=out_path)




        # 세생활권 레이어 정리 : 인구 레이어와의 Spatial Join을 통해 연계되지 않은 피처 제거
        out_path = os.path.join(self.workpath, 'cliped_fishnetliving_discarded.shp')
        if self.debugging: self.setProgressMsg('인구-세생활권(세생활권2) 공간 조인 : \n{}\n\n'.format(out_path))
        tmpliving = model.joinattributesbylocation(input=clipedfishnetliving2,
                                                       join=clipedpop,
                                                       joinfiels=[],
                                                       discardnomatching=True,
                                                       output=out_path
                                                       )

######################################################################################################
        out_path = os.path.join(self.workpath, 'only_living_has_pop.shp')
        if self.debugging: self.setProgressMsg('인구포인트 있는 세생활권만 추출(dissolve = {}) : \n{}\n\n'.format(livingID, out_path))
        clipedliving = model.dissolvewithQgis(input=tmpliving, onlyselected=False, field=[livingID], output=out_path)



        # 불필요한 필드 값 제거(IN_LIVINGAREA)
        out_path = os.path.join(self.workpath, 'cliped_living2.shp')
        if self.debugging: self.setProgressMsg('세생활권2 필드 정리 : \n{}\n\n'.format(out_path))
        clipedliving = model.deleteFields(input=clipedliving, requredfields=[livingID], output=out_path)

        if isinstance(clipedliving, str):
            model.livingareaLayer = model.writeAsVectorLayer(clipedliving)
        else:
            model.livingareaLayer = clipedliving
        model.livingareaIDField = livingID










        # 1-4 분석 지역 데이터 추출 : 기존 생활 SOC 시설
        # self.setProgressMsg('..... 분석 지역 데이터 추출 : 기존 생활 SOC 시설\n')
        if self.feedback.isCanceled(): return None
        clipedCurSOC = model.clipwithQgis(input=self.parameters['IN_CURSOC'].sourceName(),
                                          onlyselected=self.parameters['IN_CURSOC_ONLYSELECTED'],
                                          overlay=boundary)

        out_path = os.path.join(self.workpath, 'cliped_curSOC.shp')
        clipedCurSOC = model.addIDField(input=clipedCurSOC, idfid=curSOCID, output=out_path)

        # 불필요한 필드 값 제거(IN_CURSOC)
        out_path = os.path.join(self.workpath, 'cliped_curSOC2.shp')
        if self.debugging: self.setProgressMsg('기존 SOC 클립(필드 정리) : \n{}\n\n'.format(out_path))
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
        #
        ################# [2 단계] 세생활권 인구정보와 생활SOC정보 분석 #################
        self.setProgressMsg('[2 단계] 세생활권 인구정보와 생활SOC 분석......')
        # self.setProgressMsg('..... 거주인구 지점의 최근린 생활SOC지점 검색')
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'popwithnearestSOC.shp')
        if self.debugging: self.setProgressMsg('인구2 최근린 기존 SOC ID(인구3) : \n{}\n\n'.format(out_path))
        popwithNearSOC = model.nearesthubpoints(input=clipedpop,
                                                onlyselected=False,
                                                sf_hub=model.currentSOC,
                                                hubfield=model.currentSOCID,
                                                output=out_path
                                                )

        # 2-2 개별거주인구와 생활SOC intersection : 개별 거주인구와 모든 생활SOC까지의 거리 계산
        # self.setProgressMsg('..... 거주인구 데이터와 생활 SOC 데이터 거리 분석\n')
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_popaddedlivingarea.shp')
        if self.debugging: self.setProgressMsg('인구3에 인터섹션 with 세생활권2(인구4) : \n{}\n\n'.format(out_path))
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
        if self.debugging: self.setProgressMsg("거리조락 밖의 SOC 거리 일괄처리(인구 최종) {}m : \n{}\n\n".format(str(model.outofcutoff), output))
        dfPop = model.anal_accessibilityCurSOC_straight()
        dfPop.to_csv(output)


        # 3-2 접근성 분석 결과 평가
        # self.setProgressMsg('....... 접근성 분석 결과 평가')
        if self.feedback.isCanceled(): return None

        finallayer = model.make_Accessbillityscore(isNetwork=False, output=self.parameters["OUTPUT"])

        return finallayer


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
        out_path = os.path.join(self.workpath, 'boundary.shp')
        boundary = model.dissolvewithQgis(input=self.parameters['IN_SITE'].sourceName(),
                                          onlyselected=self.parameters['IN_SITE_ONLYSELECTED'],
                                          output=out_path)

        if isinstance(boundary, str):
            model.boundary = model.writeAsVectorLayer(boundary)
        else:
            model.boundary = boundary





        # 1-3 분석 지역 데이터 추출 : 인구데이터
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_pop.shp')
        clipedpop = model.clipwithQgis(input=self.parameters['IN_POP'].sourceName(),
                                       onlyselected=self.parameters['IN_POP_ONLYSELECTED'],
                                       overlay=model.boundary,
                                       output=out_path)

        # 불필요한 필드 값 제거(IN_POP)
        out_path = os.path.join(self.workpath, 'cliped_pop2.shp')
        clipedpop = model.deleteFields(input=clipedpop, requredfields=[self.parameters['IN_POP_CNTFID']], output=out_path)

        out_path = os.path.join(self.workpath, 'cliped_pop3_withID.shp')
        clipedpop = model.addIDField(input=clipedpop, idfid=popID, output=out_path)
        model.populationLayer = clipedpop
        model.popcntField = self.parameters['IN_POP_CNTFID']
        model.popIDField = popID



        # 1-4 분석 지역 데이터 추출 : 기존 생활 SOC 시설
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('기존의 생활SOC 레이어를 초기화 합니다.....')
        clipedCurSOC = model.clipwithQgis(input=self.parameters['IN_CURSOC'].sourceName(),
                                          onlyselected=self.parameters['IN_CURSOC_ONLYSELECTED'],
                                          overlay=model.boundary)

        out_path = os.path.join(self.workpath, 'cliped_curSOC.shp')
        clipedCurSOC = model.addIDField(input=clipedCurSOC, idfid=curSOCID, output=out_path)
        model.currentSOCID = curSOCID

        # 불필요한 필드 값 제거(IN_CURSOC)
        out_path = os.path.join(self.workpath, 'cliped_curSOC2.shp')
        # if isinstance(clipedCurSOC, str):
        #     tmplyr = model.writeAsVectorLayer(clipedCurSOC)
        # else:
        #     tmplyr = clipedCurSOC
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
            out_path = os.path.join(self.workpath, 'cliped_living.shp')
            clipedliving = model.addIDField(input=clipedliving, idfid=livingID, output=out_path)

            # 불필요한 필드 값 제거(IN_LIVINGAREA)
            out_path = os.path.join(self.workpath, 'cliped_living2.shp')
            clipedliving = model.deleteFields(input=clipedliving, requredfields=[livingID], output=out_path)

            if isinstance(clipedliving, str):
                clipedliving = model.writeAsVectorLayer(clipedliving)
            else:
                clipedliving = clipedliving

            model.livingareaIDField = livingID

            # 2-2 세생활권내 인구 분석
            # 인구 계산
            if self.feedback.isCanceled(): return None
            out_path = os.path.join(self.workpath, 'cliped_livingwithpop.shp')
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
            out_path = os.path.join(self.workpath, 'cliped_pointlivingwithpop.shp')
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
        if self.debugging: self.setProgressMsg('사용자 후보지 레이어 : {}'.format(str(usergrid)))

        gridlayer = None
        onlyselected = False
        if usergrid == None:
            if self.debugging: self.setProgressMsg('잠재적 후보지 그리드 데이터를 생성합니다.....')
            out_path = os.path.join(self.workpath, 'grid.shp')
            gridlayer = model.createGridfromLayer(sourcelayer=model.boundary,
                                                  gridsize=self.parameters['IN_GRID_SIZE'],
                                                  output=out_path)
        else:
            gridlayer = self.parameters['IN_USERGRID'].sourceName()
            onlyselected = self.parameters['IN_USERGRID_ONLYSELECTED']


        if self.debugging: self.setProgressMsg('분석할 후보지 타입 : {}({})'.format(type(gridlayer), len(gridlayer)))


        # 3-2 분석 지역 데이터 추출 : 잠재적 위치
        if self.feedback.isCanceled(): return None
        if self.debugging:self.setProgressMsg('잠재적 후보지 데이터를 초기화 합니다.....')
        out_path = os.path.join(self.workpath, 'cliped_grid.shp')
        clipedgrid = model.clipwithQgis(input=gridlayer,
                                        onlyselected=onlyselected,
                                        overlay=model.boundary,
                                        output=out_path)

        if isinstance(clipedgrid, str):
            grid = model.writeAsVectorLayer(clipedgrid)
        else:
            grid = clipedgrid

        #add grid id : 코드 일관성 유지를 위해 자동으로 생성되는 id사용안함(사용자 후보지 고려)
        gridid = "GRID_ID"
        out_path = os.path.join(self.workpath, 'final_grid.shp')
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
        if self.debugging: self.setProgressMsg('기존 SOC 시설의 직선거리를 분석합니다.....')
        dfPop = model.anal_AllCurSOC_straight()


        # 4-2 형평성 분석 : 잠재적 위치
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('잠재적 위치의 직선거리를 분석합니다.....')
        potengpd = model.anal_AllPotenSOC_straight()

        # 4-3 형평성 분석 결과 평가
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('형평성 지수를 계산합니다.....')
        finallayer = model.make_equityscore(isNetwork=False, output=self.parameters["OUTPUT"])


        return finallayer


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
        out_path = os.path.join(self.workpath, 'boundary.shp')
        boundary = model.dissolvewithQgis(input=self.parameters['IN_SITE'].sourceName(),
                                          onlyselected=self.parameters['IN_SITE_ONLYSELECTED'],
                                          output=out_path)

        if isinstance(boundary, str):
            model.boundary = model.writeAsVectorLayer(boundary)
        else:
            model.boundary = boundary

        # 1-2 분석 지역 데이터 추출 : 노드
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_node.shp')
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
        if self.debugging: self.setProgressMsg('링크 데이터를 초기화 합니다.....')
        boundary2000 = model.bufferwithQgis(input=boundary,
                                           onlyselected=False,
                                           distance=2000)

        out_path = os.path.join(self.workpath, 'cliped_link.shp')
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
        clipedpop = model.clipwithQgis(input=self.parameters['IN_POP'].sourceName(),
                                       onlyselected=self.parameters['IN_POP_ONLYSELECTED'],
                                       overlay=model.boundary)

        out_path = os.path.join(self.workpath, 'cliped_pop.shp')
        clipedpop = model.addIDField(input=clipedpop, idfid=popID, output=out_path)
        model.popIDField = popID
        model.popcntField = self.parameters['IN_POP_CNTFID']

        # 불필요한 필드 값 제거(IN_POP)
        out_path = os.path.join(self.workpath, 'cliped_pop2.shp')
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
        out_path = os.path.join(self.workpath, 'fishnetliving.shp')
        if self.debugging: self.setProgressMsg('세생활권 레이어 생성.....')
        fishnetliving = model.createGridfromLayer(sourcelayer=model.boundary,
                                                  gridsize=self.parameters['IN_LIVINGAREA'],
                                                  type=2,
                                                  output=out_path)

        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('세생활권 데이터를 초기화 합니다.....')
        out_path = os.path.join(self.workpath, 'cliped_fishnetliving.shp')
        clipedfishnetliving = model.clipwithQgis(input=fishnetliving,
                                                 onlyselected=False,
                                                 overlay=model.boundary,
                                                 output=out_path)

        # 세생활권 레이어 정리 : 인구 레이어와의 Spatial Join을 통해 연계되지 않은 피처 제거
        out_path = os.path.join(self.workpath, 'cliped_fishnetliving_discarded.shp')
        clipedliving = model.joinattributesbylocation(input=clipedfishnetliving,
                                                      join=clipedpop,
                                                      joinfiels=[],
                                                      discardnomatching=True,
                                                      output=out_path
                                                      )

        ######################################################################################################







        out_path = os.path.join(self.workpath, 'cliped_living.shp')
        clipedliving = model.addIDField(input=clipedliving, idfid=livingID, output=out_path)

        # 불필요한 필드 값 제거(IN_LIVINGAREA)
        out_path = os.path.join(self.workpath, 'cliped_living2.shp')
        # if isinstance(clipedliving, str):
        #     tmplyr = model.writeAsVectorLayer(clipedliving)
        # else:
        #     tmplyr = clipedliving
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
        # if self.debugging: out_path = os.path.join(self.workpath, 'cliped_pop.shp')
        # clipedpop = model.addIDField(input=clipedpop, idfid=popID, output=out_path)
        # model.popIDField = popID
        # model.popcntField = self.parameters['IN_POP_CNTFID']
        #
        #
        # # 불필요한 필드 값 제거(IN_POP)
        # out_path = ''
        # if self.debugging: out_path = os.path.join(self.workpath, 'cliped_pop2.shp')
        # # if isinstance(clipedpop, str):
        # #     tmplyr = model.writeAsVectorLayer(clipedpop)
        # # else:
        # #     tmplyr = clipedpop
        # clipedpop = model.deleteFields(input=clipedpop, requredfields=[popID, self.parameters['IN_POP_CNTFID']], output=out_path)


        # 1-6 분석 지역 데이터 추출 : 기존 생활 SOC 시설
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('기존의 생활SOC 레이어의 인근 노드를 찾습니다.....')
        out_path = os.path.join(self.workpath, 'cliped_curSOCWithNode.shp')
        clipedCurSOC = model.clipwithQgis(input=self.parameters['IN_CURSOC'].sourceName(),
                                          onlyselected=self.parameters['IN_CURSOC_ONLYSELECTED'],
                                          overlay=boundary,
                                          output=out_path)

        # 불필요한 필드 값 제거(IN_CURSOC)
        out_path = os.path.join(self.workpath, 'cliped_curSOCWithNode2.shp')
        # if isinstance(clipedCurSOC, str):
        #     tmplyr = model.writeAsVectorLayer(clipedCurSOC)
        # else:
        #     tmplyr = clipedCurSOC
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
        out_path = os.path.join(self.workpath, 'curSOCwithNode.shp')
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
        out_path = os.path.join(self.workpath, 'popwithNode.shp')
        popWithNode = model.nearesthubpoints(input=clipedpop,
                                            onlyselected=False,
                                            sf_hub=model.nodelayer,
                                            hubfield=model.nodeIDfield,
                                            output=out_path
                                            )


        # 2-3 개별거주인구와 세생활권 intersection : 개별 거주인구와 모든 세생활권까지의 거리 계산
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_popaddedlivingarea.shp')
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
        if self.debugging: self.setProgressMsg('최단거리 분석을 위한 노드링크 객체를 생성합니다.....')
        isoneway = (self.parameters['IN_LINK_TYPE'] == 0)
        

        model.initNXGraph(isoneway=isoneway)
        graph = model.createNodeEdgeInGraph()

        # 3-2 모든 노드간의 최단 거리 분석
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('최단거리 분석 위한 기초자료를 생성합니다.....')
        alllink = None
        if self.debugging: alllink = os.path.join(self.workpath, 'alllink.pickle')
        model.cutoff = self.parameters['IN_LIMIT_DIST']
        model.outofcutoff = self.parameters['IN_LIMIT_DIST'] * self.cutoffconst_acc
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
        if self.debugging: self.setProgressMsg('세생활권의 최근린 SOC 시설을 찾습니다.....')
        dfPop = model.anal_accessibilityCurSOC_network()

        # 4-2 접근성 분석 결과 평가
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('접근성 지수를 계산합니다.....')
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
        if self.debugging: self.setProgressMsg('바운더리 초기화 합니다.....')
        out_path = os.path.join(self.workpath, 'boundary.shp')
        boundary = model.dissolvewithQgis(input=self.parameters['IN_SITE'].sourceName(),
                                          onlyselected=self.parameters['IN_SITE_ONLYSELECTED'],
                                          output=out_path)
        if isinstance(boundary, str):
            model.boundary = model.writeAsVectorLayer(boundary)
        else:
            model.boundary = boundary

        # 1-2 분석 지역 데이터 추출 : 인구데이터
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('주거인구 레이어를 초기화 합니다.....')
        out_path = os.path.join(self.workpath, 'cliped_pop.shp')
        clipedpop = model.clipwithQgis(input=self.parameters['IN_POP'].sourceName(),
                                       onlyselected=self.parameters['IN_POP_ONLYSELECTED'],
                                       overlay=boundary,
                                       output=out_path)

        # 불필요한 필드 값 제거(IN_POP)
        out_path = os.path.join(self.workpath, 'cliped_pop2.shp')
        clipedpop = model.deleteFields(input=clipedpop, requredfields=[self.parameters['IN_POP_CNTFID']],
                                       output=out_path)

        # 1-3 분석 지역 데이터 추출 : 기존 생활 SOC 시설
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_curSOC.shp')
        clipedCurSOC = model.clipwithQgis(input=self.parameters['IN_CURSOC'].sourceName(),
                                          onlyselected=self.parameters['IN_CURSOC_ONLYSELECTED'],
                                          overlay=boundary,
                                          output=out_path)

        # 불필요한 필드 값 제거(IN_CURSOC)
        out_path = os.path.join(self.workpath, 'cliped_curSOC2.shp')
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
        if self.debugging: self.setProgressMsg('사용자 후보지 레이어 : {}'.format(str(usergrid)))

        gridlayer = None
        onlyselected = False
        if usergrid == None:
            if self.debugging: self.setProgressMsg('잠재적 후보지 그리드 데이터를 생성합니다.....')
            out_path = os.path.join(self.workpath, 'grid.shp')
            gridlayer = model.createGridfromLayer(sourcelayer=model.boundary,
                                                  gridsize=self.parameters['IN_GRID_SIZE'],
                                                  output=out_path)
        else:
            gridlayer = self.parameters['IN_USERGRID'].sourceName()
            onlyselected = self.parameters['IN_USERGRID_ONLYSELECTED']


        if self.debugging: self.setProgressMsg('분석할 후보지 타입 : {}({})'.format(type(gridlayer), len(gridlayer)))


        # 3-2 분석 지역 데이터 추출 : 잠재적 위치
        if self.feedback.isCanceled(): return None
        if self.debugging:self.setProgressMsg('잠재적 후보지 데이터를 초기화 합니다.....')
        out_path = os.path.join(self.workpath, 'cliped_grid.shp')
        clipedgrid = model.clipwithQgis(input=gridlayer,
                                        onlyselected=onlyselected,
                                        overlay=model.boundary,
                                        output=out_path)

        if isinstance(clipedgrid, str):
            grid = model.writeAsVectorLayer(clipedgrid)
        else:
            grid = clipedgrid

        #add grid id : 코드 일관성 유지를 위해 자동으로 생성되는 id사용안함(사용자 후보지 고려)
        gridid = "GRID_ID"
        out_path = os.path.join(self.workpath, 'final_grid.shp')
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
        if self.debugging: self.setProgressMsg('생활SOC 버퍼......')
        out_path = os.path.join(self.workpath, 'bufferedCurSOC.shp')
        bufferedSOC = model.bufferwithQgis(input=model.currentSOC,
                                           onlyselected=False,
                                           distance=model.cutoff,
                                           output=out_path)

        # # 5-2 효율성 분석 : 기존 생활 SOC 시설(기 서비스 지역 배제 비율 적)
        model.popcntField = self.parameters['IN_POP_CNTFID']
        popexlusrate = self.parameters['IN_POP_EXCLUSION']

        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('기 서비스 지역 인구 배제 처리 중......({}% 배제)'.format(popexlusrate))
        out_path = os.path.join(self.workpath, 'selbyloc.shp')
        poplyr = model.applypopratioinselectedEuclidean(input=clipedpop,
                                                      popfield=self.parameters['IN_POP_CNTFID'],
                                                      exlusrate=popexlusrate,
                                                      applyArea=bufferedSOC,
                                                      output=out_path)

        # # 5-2 효율성 분석 : 기존 생활 SOC 시설(기 서비스 지역 제거)
        # if self.feedback.isCanceled(): return None
        # if self.debugging: self.setProgressMsg('기존서비스되는 인구 삭제.......')
        # out_path = ''
        # if self.debugging: out_path = os.path.join(self.workpath, 'popremovedCurSOC.shp')
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
        out_path = os.path.join(self.workpath, 'popenSvrArea.shp')
        potenSvrArea = model.bufferwithQgis(input=model.potentiallayer,
                                            onlyselected=False,
                                            distance=model.cutoff,
                                            output=out_path)

        # 5-4 효율성 분석 : 잠재적 위치(잠재적 위치 서비스 지역 분석)
        out_path = os.path.join(self.workpath, 'popaddedpotenid.shp')
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
        if self.debugging: self.setProgressMsg('잠재적 위치의 최단거리를 분석합니다.....')
        # 각 잠재적 위치의 서비스 영역내 포함되는 인구수
        potengpd = model.anal_efficiencyPotenSOC_straight()



        # 5-6 효율성 분석 결과 평가
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('효율성 지수를 계산합니다.....')
        finallayer = model.make_efficiencyscore(output=self.parameters["OUTPUT"])

        self.setProgressMsg("666666")

        return finallayer

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
        if self.debugging: self.setProgressMsg('노드/링크 데이터를 초기화 합니다.....')
        out_path = os.path.join(self.workpath, 'boundary.shp')
        boundary = model.dissolvewithQgis(input=self.parameters['IN_SITE'].sourceName(),
                                          onlyselected=self.parameters['IN_SITE_ONLYSELECTED'],
                                          output=out_path)

        if isinstance(boundary, str):
            model.boundary = model.writeAsVectorLayer(boundary)
        else:
            model.boundary = boundary

        # 1-2 분석 지역 데이터 추출 : 노드
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_node.shp')
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
        if self.debugging: self.setProgressMsg('링크 데이터를 초기화 합니다.....')
        boundary2000 = model.bufferwithQgis(input=boundary,
                                            onlyselected=False,
                                            distance=2000)

        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_link.shp')
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
        out_path = os.path.join(self.workpath, 'cliped_pop.shp')
        clipedpop = model.clipwithQgis(input=self.parameters['IN_POP'].sourceName(),
                                       onlyselected=self.parameters['IN_NODE_ONLYSELECTED'],
                                       overlay=boundary,
                                       output=out_path)
        # 불필요한 필드 값 제거(IN_POP)
        out_path = os.path.join(self.workpath, 'cliped_pop2.shp')
        clipedpop = model.deleteFields(input=clipedpop, requredfields=[self.parameters['IN_POP_CNTFID']],
                                       output=out_path)


        # 1-5 분석 지역 데이터 추출 : 기존 생활 SOC 시설
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_curSOC.shp')
        clipedCurSOC = model.clipwithQgis(input=self.parameters['IN_CURSOC'].sourceName(),
                                          onlyselected=self.parameters['IN_CURSOC_ONLYSELECTED'],
                                          overlay=boundary,
                                          output=out_path)

        out_path = os.path.join(self.workpath, 'cliped_curSOC2.shp')
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
        if self.debugging: self.setProgressMsg('기존의 생활SOC 레이어의 인근 노드를 찾습니다.....')
        out_path = os.path.join(self.workpath, 'curSOCwithNode.shp')
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
        out_path = ''
        popWithNode = model.nearesthubpoints(input=clipedpop,
                                             onlyselected=False,
                                             sf_hub=model.nodelayer,
                                             hubfield=model.nodeIDfield,
                                             output=out_path
                                             )

        # ID 만들어 넣기 $id
        if self.debugging: out_path = os.path.join(self.workpath, 'popwithNode.shp')
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
        if self.debugging: self.setProgressMsg('사용자 후보지 레이어 : {}'.format(str(usergrid)))

        gridlayer = None
        onlyselected = False
        if usergrid == None:
            if self.debugging: self.setProgressMsg('잠재적 후보지 그리드 데이터를 생성합니다.....')
            out_path = os.path.join(self.workpath, 'grid.shp')
            gridlayer = model.createGridfromLayer(sourcelayer=model.boundary,
                                                  gridsize=self.parameters['IN_GRID_SIZE'],
                                                  output=out_path)
        else:
            gridlayer = self.parameters['IN_USERGRID'].sourceName()
            onlyselected = self.parameters['IN_USERGRID_ONLYSELECTED']

        if self.debugging: self.setProgressMsg('분석할 후보지 타입 : {}({})'.format(type(gridlayer), len(gridlayer)))

        # 3-2 분석 지역 데이터 추출 : 잠재적 위치
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('잠재적 후보지 데이터를 초기화 합니다.....')
        out_path = os.path.join(self.workpath, 'cliped_grid.shp')
        clipedgrid = model.clipwithQgis(input=gridlayer,
                                        onlyselected=onlyselected,
                                        overlay=model.boundary,
                                        output=out_path)

        if isinstance(clipedgrid, str):
            grid = model.writeAsVectorLayer(clipedgrid)
        else:
            grid = clipedgrid

        # add grid id : 코드 일관성 유지를 위해 자동으로 생성되는 id사용안함(사용자 후보지 고려)
        gridid = "GRID_ID"
        out_path = os.path.join(self.workpath, 'final_grid.shp')
        grid = model.addIDField(input=grid, idfid=gridid, output=out_path)
        model.potentialID = gridid

        # 3-3 잠재적 위치의 최근린 노드  검색
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('잠재적 후보지 레이어의 인근 노드를 찾습니다.....')
        out_path = os.path.join(self.workpath, 'gridwithNode.shp')
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
        if self.debugging: self.setProgressMsg('최단거리 분석을 위한 노드링크 객체를 생성합니다.....')
        isoneway = (self.parameters['IN_LINK_TYPE'] == 0)
        model.initNXGraph(isoneway=isoneway)
        graph = model.createNodeEdgeInGraph()

        # 3-2 모든 노드간의 최단 거리 분석
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('최단거리 분석 위한 기초자료를 생성합니다.....')
        alllink = None
        if self.debugging: alllink = os.path.join(self.workpath, 'alllink.pickle')
        model.cutoff = self.parameters['IN_LIMIT_DIST']
        model.outofcutoff = self.parameters['IN_LIMIT_DIST'] * self.cutoffconst_eff
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
        if self.debugging: self.setProgressMsg('기존 SOC 시설을 분석합니다.....')
        dfPop = model.anal_efficiencyCurSOC_network()

        # # 5-2 효율성 분석 : 기존 생활 SOC 시설(기 서비스 지역 배제 비율 적)
        model.popcntField = self.parameters['IN_POP_CNTFID']
        popexlusrate = self.parameters['IN_POP_EXCLUSION']

        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('기 서비스 지역 인구 배제 처리 중......({}% 배제)'.format(popexlusrate))
        out_path = os.path.join(self.workpath, 'selbyloc.shp')
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

        out_path = os.path.join(self.workpath, 'popwithNoderemovedCurSOC.shp')
        poplyr = model.vectorlayer2ShapeFile(model.populationLayer, output=out_path)



        # 5-3 효율성 분석 : 잠재적 위치(서비스 영역 설정)
        if self.feedback.isCanceled(): return None
        out_path = ''
        if self.debugging: out_path = os.path.join(self.workpath, 'popenSvrArea.shp')
        potenSvrArea = model.bufferwithQgis(input=model.potentiallayer,
                                            onlyselected=False,
                                            distance=model.cutoff,
                                            output=out_path)

        # 5-4 효율성 분석 : 잠재적 위치(잠재적 위치 서비스 지역 분석)
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'popaddedpotenid.shp')
        overprefix = 'JN_'
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
        if self.debugging: self.setProgressMsg('잠재적 위치의 최단거리를 분석합니다.....')

        # shape file의 필드명 최대길이는 10자리 / 메모리에 있을때는 상관없음
        relpopNodeID = overprefix + model.nodeIDfield
        if self.debugging: relpopNodeID = relpopNodeID[0:10]
        popcntfield = overprefix + model.popcntField
        if self.debugging: popcntfield = popcntfield[0: 10]

        # 각 잠재적 위치의 서비스 영역내 포함되는 인구수
        potengpd = model.anal_efficiencyPotenSOC_network(relpopNodeID=relpopNodeID,
                                                         relpopcntfid=popcntfield)

        # 5-6 효율성 분석 결과 평가
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('효율성 지수를 계산합니다.....')
        finallayer = model.make_efficiencyscore(output=self.parameters["OUTPUT"])

        return finallayer


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
        out_path = os.path.join(self.workpath, 'boundary.shp')
        boundary = model.dissolvewithQgis(input=self.parameters['IN_SITE'].sourceName(),
                                          onlyselected=self.parameters['IN_SITE_ONLYSELECTED'],
                                          output=out_path)
        if isinstance(boundary, str):
            model.boundary = model.writeAsVectorLayer(boundary)
        else:
            model.boundary = boundary

        # 1-2 분석 지역 데이터 추출 : 노드
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('노드/링크 데이터를 초기화 합니다.....')
        out_path = os.path.join(self.workpath, 'cliped_node.shp')
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
        if self.debugging: self.setProgressMsg('링크 데이터를 초기화 합니다.....')
        boundary2000 = model.bufferwithQgis(input=boundary,
                                            onlyselected=False,
                                            distance=2000)

        out_path = os.path.join(self.workpath, 'cliped_link.shp')
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
        out_path = os.path.join(self.workpath, 'cliped_pop.shp')
        clipedpop = model.clipwithQgis(input=self.parameters['IN_POP'].sourceName(),
                                       onlyselected=self.parameters['IN_NODE_ONLYSELECTED'],
                                       overlay=boundary,
                                       output=out_path)


        # 불필요한 필드 값 제거(IN_POP)
        out_path = os.path.join(self.workpath, 'cliped_pop2.shp')
        clipedpop = model.deleteFields(input=clipedpop, requredfields=[self.parameters['IN_POP_CNTFID']], output=out_path)

        out_path = os.path.join(self.workpath, 'cliped_pop3_withID.shp')
        clipedpop = model.addIDField(input=clipedpop, idfid=popID, output=out_path)

        #

        # 1-6 분석 지역 데이터 추출 : 기존 생활 SOC 시설
        if self.feedback.isCanceled(): return None
        out_path = os.path.join(self.workpath, 'cliped_curSOC.shp')
        clipedCurSOC = model.clipwithQgis(input=self.parameters['IN_CURSOC'].sourceName(),
                                          onlyselected=self.parameters['IN_CURSOC_ONLYSELECTED'],
                                          overlay=boundary,
                                          output=out_path)

        # 불필요한 필드 값 제거(IN_CURSOC)
        out_path = os.path.join(self.workpath, 'cliped_curSOC2.shp')
        # if isinstance(clipedCurSOC, str):
        #     tmplyr = model.writeAsVectorLayer(clipedCurSOC)
        # else:
        #     tmplyr = clipedCurSOC
        clipedCurSOC = model.deleteFields(input=clipedCurSOC, requredfields=[], output=out_path)
        #
        #
        #
        #

        # 5. 기존시설 노드 찾기
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('기존의 생활SOC 레이어의 인근 노드를 찾습니다.....')

        out_path = os.path.join(self.workpath, 'curSOCwithNode.shp')
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
            out_path = os.path.join(self.workpath, 'cliped_living.shp')
            clipedliving = model.addIDField(input=clipedliving, idfid=livingID, output=out_path)

            # 불필요한 필드 값 제거(IN_LIVINGAREA)
            out_path = os.path.join(self.workpath, 'cliped_living2.shp')
            clipedliving = model.deleteFields(input=clipedliving, requredfields=[livingID], output=out_path)

            if isinstance(clipedliving, str):
                clipedliving = model.writeAsVectorLayer(clipedliving)
            else:
                clipedliving = clipedliving

            model.livingareaIDField = livingID



            # 2-1 세생활권내 인구 분석
            if self.feedback.isCanceled(): return None
            out_path = os.path.join(self.workpath, 'cliped_livingwithpop.shp')
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
            out_path = os.path.join(self.workpath, 'popwithNode.shp')
            popWithNode = model.nearesthubpoints(input=clipelivingwithpop,
                                                 onlyselected=False,
                                                 sf_hub=model.nodelayer,
                                                 hubfield=self.parameters['IN_NODE_ID'],
                                                 output=out_path
                                                 )
        else:
            if self.debugging: self.setProgressMsg('인구레이어의 인근 노드 찾기......')
            if self.feedback.isCanceled(): return None
            out_path = os.path.join(self.workpath, 'popwithNode.shp')

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
        if self.debugging: self.setProgressMsg('사용자 후보지 레이어 : {}'.format(str(usergrid)))

        gridlayer = None
        onlyselected = False
        if usergrid == None:
            if self.debugging: self.setProgressMsg('잠재적 후보지 그리드 데이터를 생성합니다.....')
            out_path = os.path.join(self.workpath, 'grid.shp')
            gridlayer = model.createGridfromLayer(sourcelayer=model.boundary,
                                                  gridsize=self.parameters['IN_GRID_SIZE'],
                                                  output=out_path)
        else:
            gridlayer = self.parameters['IN_USERGRID'].sourceName()
            onlyselected = self.parameters['IN_USERGRID_ONLYSELECTED']

        if self.debugging: self.setProgressMsg('분석할 후보지 타입 : {}({})'.format(type(gridlayer), len(gridlayer)))

        # 3-2 분석 지역 데이터 추출 : 잠재적 위치
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('잠재적 후보지 데이터를 초기화 합니다.....')
        out_path = os.path.join(self.workpath, 'cliped_grid.shp')
        clipedgrid = model.clipwithQgis(input=gridlayer,
                                        onlyselected=onlyselected,
                                        overlay=model.boundary,
                                        output=out_path)

        if isinstance(clipedgrid, str):
            grid = model.writeAsVectorLayer(clipedgrid)
        else:
            grid = clipedgrid

        # add grid id : 코드 일관성 유지를 위해 자동으로 생성되는 id사용안함(사용자 후보지 고려)
        gridid = "GRID_ID"
        out_path = os.path.join(self.workpath, 'final_grid.shp')
        grid = model.addIDField(input=grid, idfid=gridid, output=out_path)
        model.potentialID = gridid

        # 3-3 잠재적 위치의 최근린 노드  검색
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('잠재적 후보지 레이어의 인근 노드를 찾습니다.....')
        out_path = os.path.join(self.workpath, 'gridwithNode.shp')
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
        if self.debugging: self.setProgressMsg('최단거리 분석을 위한 노드링크 객체를 생성합니다.....')
        isoneway = (self.parameters['IN_LINK_TYPE'] == 0)
        model.initNXGraph(isoneway=isoneway)
        graph = model.createNodeEdgeInGraph()

        # 5-2 모든 노드간의 최단 거리 분석
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('최단거리 분석 위한 기초자료를 생성합니다.....\n(분석 조건에 따라 10분~60분 이상 소요됩니다...)')
        alllink = None
        if self.debugging: alllink = os.path.join(self.workpath, 'alllink.pickle')
        model.cutoff = self.parameters['IN_LIMIT_DIST']
        model.outofcutoff = self.parameters['IN_LIMIT_DIST'] * self.cutoffconst_equ
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
        if self.debugging: self.setProgressMsg('기존 SOC 시설의 최단거리를 분석합니다.....')
        dfPop = model.anal_AllCurSOC_network()

        # 5-3 형평성 분석 : 잠재적 위치
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('잠재적 위치의 최단거리를 분석합니다.....')
        potengpd = model.anal_AllPotenSOC_network()

        # 5-3 형평성 분석 결과 평가
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('형평성 지수를 계산합니다.....')
        finallayer = model.make_equityscore(isNetwork=True, output=self.parameters["OUTPUT"])


        return finallayer



