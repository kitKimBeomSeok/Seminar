# 충돌 정의 변경
# - MORA-01: VRU(패킷) 단위로 충돌 계산
# - MORA-02: RU 단위로 충돌 계산 (하나의 VRU에서 충돌 발생시 해당 RU 충돌로 계산)

import random

NUM_SIM = 1  # 시뮬레이션 반복 수
NUM_DTI = 100000  # 한 번 시뮬레이션에서 수행될 Data Transmission Interval 수

# 기본 설정 파라미터 값
USER = 110  # 사용자 수
ANTENNA = 4  # AP의 안테나 수
RU = 8  # 사용가능한 RU
VRU = 5  # 사용가능한 VRU
MIN_OCW = 32  # 최소 백오프 카운터
MAX_OCW = 1024  # 최대 백오프 카운터
RETRY_BS = 6  # 백오프 스테이지 최댓값

DATA_RATE = 1  # 데이터 전송 속도, 단위: Gbps
PKT_SZ = 1000  # 데이터 패킷 크기, 단위: byte
PREAMBLE_SZ = 40  # 프리앰블 크기, 단위: byte
TF_SZ = 89  # 트리거 프레임 크기, 단위: byte
BA_SZ = 32  # 블록 ACK 크기, 단위: byte
BEACON = 10  # 비콘 주기, 단위: ms
SLOT = 9  # 슬롯 크기, 단위: us
SIFS = 16  # SIFS 시간, 단위: us
DIFS = 18  # DIFS 시간, 단위: us
DTI = 32  # Data Transmission Interval 시간, 단위: us

# Transmission time in us
PKT_SZ_us = (PKT_SZ * 8) / (DATA_RATE * 1000)  # 데이터 패킷 전송 시간, 단위: us
PREAMBLE_SZ_us = (PREAMBLE_SZ * 8) / (DATA_RATE * 1000)  # 프리앰블 전송 시간, 단위: us
TF_SZ_us = (TF_SZ * 8) / (DATA_RATE * 1000)  # 트리거 프레임 전송 시간, 단위: us
BA_SZ_us = (BA_SZ * 8) / (DATA_RATE * 1000)  # 블록 ACK 전송 시간, 단위: us
TWT_INTERVAL = DIFS + TF_SZ_us + SIFS * 2 + DTI + BA_SZ_us

# 성능 변수
# 패킷 단위 성능
Stats_PKT_TX_Trial = 0  # 전송 시도 수
Stats_PKT_Success = 0  # 전송 성공 수
Stats_PKT_Collision = 0  # 충돌 발생 수
Stats_PKT_Delay = 0  # 패킷 당 전송 시도 DTI 수
# RU 단위 성능
Stats_RU_TX_Trial = 0  # 전송 시도 수
Stats_RU_Idle = 0  # 빈 RU 수
Stats_RU_Success = 0  # 전송 성공 RU 수
Stats_RU_Collision = 0  # 충돌 발생 RU 수

# 노드 관리 목록
stationList = []


class station:
    def __init__(self):
        self.ru = 0  # 할당된 RU
        self.vru = 0  # 할당된 VRU
        self.cw = MIN_OCW  # 초기 OCW
        self.bo = random.randrange(0, self.cw)  # backoffCounter
        self.tx_status = False  # True 전송 시도, False 전송 시도 않음
        self.suc_status = False  # True 전송 성공, False 전송 실패(충돌)
        self.delay = 0
        self.retry = 0
        self.data_sz = 0  # 데이터 사이즈 (bytes)


def createSTA():
    for i in range(0, USER):
        sta = station()
        stationList.append(sta)


def allocateRUandVRU():
    for sta in stationList:
        if (sta.bo < ANTENNA * RU):
            sta.tx_status = True  # 전송 시도
            sta.ru = sta.bo % RU
            sta.vru = (sta.bo - sta.ru) / RU
        else:
            sta.bo -= (ANTENNA * RU)
            sta.tx_status = False  # 전송 시도 않음


def setSuccess(ru):
    for sta in stationList:
        if (sta.tx_status == True):  # 전송 시도
            if (sta.ru == ru):
                sta.suc_status = True  # 전송 성공


def setCollision(ru):
    for sta in stationList:
        if (sta.tx_status == True):  # 전송 시도
            if (sta.ru == ru):
                sta.suc_status = False  # 전송 실패 (충돌)


def incRUTX():
    global Stats_RU_TX_Trial  # 전송 시도 수
    Stats_RU_TX_Trial += 1


def incRUCollision():
    global Stats_RU_Collision  # 충돌 발생 RU 수
    Stats_RU_Collision += 1


def incRUSuccess():
    global Stats_RU_Success  # 전송 성공 RU 수
    Stats_RU_Success += 1


def incRUIdle():
    global Stats_RU_Idle  # 빈 RU 수
    Stats_RU_Idle += 1


def checkCollision():
    # 충돌 확인을 위한 비트맵 초기화
    coll_map = []  # RU 및 VRU에서 전송 시도된 노드 수를 추적하기 위한 비트맵 초기화
    for i in range(0, RU):
        line = []
        for j in range(0, ANTENNA):
            line.append(0)
        coll_map.append(line)
    # 여기까지가 안테나 수에 따라서 VRU까지 세팅해준 부분

    for sta in stationList:
        if (sta.tx_status == True):  # 전송 시도 중인 노드만 확인
            # 해당 RU 및 VRU에서 전송 시도된 노드 수 증가
            coll_map[int(sta.ru)][int(sta.vru)] += 1

    # RU 단위로 충돌 여부 확인
    for i in range(0, RU):
        incRUTX()  # RU 전송 시도 수 증가
        cnt_coll = 0  # RU 내에서의 충돌 수
        cnt_busy = 0  # RU 내에서의 전송 시도된 VRU 수
        for j in range(0, ANTENNA):
            if (coll_map[i][j] >= 1):  # 한 VRU에 전송 시도 노드 1개 이상 있음
                cnt_busy += 1
            if (coll_map[i][j] >= 2):  # 한 VRU에 전송 시도 노드 2개 이상 있음 - 즉, 전송 실패 (충돌)
                cnt_coll += 1
                break

        if (cnt_coll >= 1):  # 충돌 발생한 VRU 있음 - 즉, 해당 RU에서 전송 실패
            setCollision(i)  # 해당 RU에서 전송 실패로 표시
            incRUCollision()  # RU 충돌 수 증가
        else:
            if (cnt_busy >= 1):  # 충돌 발생한 VRU 없음 - 즉, 해당 RU에서 전송 성공
                setSuccess(i)  # 해당 RU에서 전송 성공으로 표시
                incRUSuccess()  # RU 성공 수 증가
            else:
                incRUIdle()  # 해당 RU에서 전송 시도한 노드 없음 - 해당 RU는 빈 RU임을 표시


def addStats():
    global Stats_PKT_TX_Trial  # 전송 시도 수
    global Stats_PKT_Success  # 전송 성공 수
    global Stats_PKT_Collision  # 충돌 발생 수
    global Stats_PKT_Delay  # 패킷 당 전송 시도 DTI 수

    for sta in stationList:
        if (sta.tx_status == True):  # 전송 시도
            Stats_PKT_TX_Trial += 1  # 전송 시도 수
            if (sta.suc_status == True):  # 전송 성공
                Stats_PKT_Success += 1  # 전송 성공 수
                Stats_PKT_Delay += sta.delay  # 패킷 당 전송 시도 DTI 수
            else:  # 전송 실패 (충돌)
                Stats_PKT_Collision += 1  # 충돌 발생 수


def incTrial():
    for sta in stationList:
        sta.delay += 1  # 전송 시도 수 1 증가


def changeStaVariables():
    for sta in stationList:
        if (sta.tx_status == True):  # 전송 시도
            if (sta.suc_status == True):  # 전송 성공
                sta.ru = 0  # 할당된 RU
                sta.vru = 0  # 할당된 VRU
                sta.cw = MIN_OCW  # 초기 OCW
                sta.bo = random.randrange(0, sta.cw)  # backoffCounter
                sta.tx_status = False  # True 전송 시도, False 전송 시도 않음
                sta.suc_status = False  # True 전송 성공, False 전송 실패(충돌)
                sta.delay = 0
                sta.retry = 0
                sta.data_sz = 0  # 데이터 사이즈 (bytes)
            else:  # 전송 실패 (충돌)
                sta.ru = 0  # 할당된 RU
                sta.vru = 0  # 할당된 VRU
                sta.retry += 1
                if (sta.retry >= RETRY_BS):  # 해당 패킷 폐기 및 변수 값 초기화
                    sta.cw = MIN_OCW  # 초기 OCW
                    sta.retry = 0
                    sta.delay = 0
                    sta.data_sz = 0  # 데이터 사이즈 (bytes)
                else:
                    sta.cw *= 2
                    if (sta.cw > MAX_OCW):
                        sta.cw = MAX_OCW  # 최대 OCW
                sta.bo = random.randrange(0, sta.cw)  # backoffCounter
                sta.tx_status = False  # True 전송 시도, False 전송 시도 않음
                sta.suc_status = False  # True 전송 성공, False 전송 실패(충돌)


def print_Performance():
    print("패킷 단위 성능")
    print("전송 시도 수 : ", Stats_PKT_TX_Trial)
    print("전송 성공 수 : ", Stats_PKT_Success)
    print("전송 실패 수 : ", Stats_PKT_Collision)
    print("충돌율 : ", (Stats_PKT_Collision / Stats_PKT_TX_Trial) * 100)
    print("지연 : ", Stats_PKT_Delay / Stats_PKT_Success)

    # Transmission time in us
    print(">> 통신 속도 : ", (Stats_PKT_Success * PKT_SZ * 8) / (NUM_SIM * NUM_DTI * TWT_INTERVAL))  # 단위: Mbps
    print(">> 지연 : ", (Stats_PKT_Delay / Stats_PKT_Success) * TWT_INTERVAL)  # 단위: us

    # print(TWT_INTERVAL)

    print("RU 단위 성능")
    print("전송 시도 수 : ", Stats_RU_TX_Trial)
    print("전송 성공 수 : ", Stats_RU_Success)
    print("전송 실패 수 : ", Stats_RU_Collision)
    print("Idle 수 : ", Stats_RU_Idle)
    print("Idle 비율 : ", (Stats_RU_Idle / Stats_RU_TX_Trial) * 100)
    print("성공율 : ", (Stats_RU_Success / Stats_RU_TX_Trial) * 100)
    print(">> 충돌율 : ", (Stats_RU_Collision / Stats_RU_TX_Trial) * 100)


def main():
    for i in range(0, NUM_SIM):
        # 시뮬레이션 반복할 때마다 모든 노드 삭제 후 재 생성
        stationList.clear()  # 모든 노드 삭제
        createSTA()  # 노드 생성

        for j in range(0, NUM_DTI):
            # k = 0
            # for sta in stationList:
            #    print("ID: ", k, "BO: ", sta.bo)
            #    k += 1

            incTrial()
            allocateRUandVRU()
            checkCollision()
            addStats()
            changeStaVariables()

    print_Performance()


main()
