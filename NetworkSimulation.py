#네트워크 세미나 시뮬레이션 환경 구성
#기존 EBO의 경우 우선 순위 범위가 RA-RU의 수만큼 사용
#응용 EBO의 경우 STA의 수만큼 RU와 관계를 로그 관계로 풀어서 우선 순위의 범위를 동적으로 적용
#
import random

NUM_STM = 1 #시뮬레이션 반복 수
NUM_DTI = 100000 #1번 시뮬레이션에서 수행될 Data Transmission Interval 수

#AP set
SIFS = 16
DIFS = 32
NUM_RU = 4 #AP에 정해져있는 RU의 수
PACKET_SIZE = 1000
TF_SIZE = 89
DATA_RATE = 1
BA_SIZE = 32
DTI = 32 #Data Transmission Interval 시간, 단위: us => 의미하는 바는 STA이 보내는 데이터의 길이가 각 STA마다 다르지만 정해진 시간만큼은 일정하기 때문에 DTI로 고정

# 기본 설정 파라미터 값
RU = 4  # STA에게 할당가능한 RU의 수
MIN_OCW = 8  # 최소 백오프 카운터
MAX_OCW = 64 # 최대 백오프 카운터
RETRY_BS = 6  # 백오프 스테이지 최댓값

# Transmission time in us
PKT_SZ_us = (PACKET_SIZE * 8) / (DATA_RATE * 1000) # 데이터 패킷 전송 시간, 단위: us
TF_SZ_us = (TF_SIZE * 8) / (DATA_RATE * 1000) # 트리거 프레임 전송 시간, 단위: us
BA_SZ_us = (BA_SIZE * 8) / (DATA_RATE * 1000) # 블록 ACK 전송 시간, 단위: us
TWT_INTERVAL = DIFS + TF_SZ_us + SIFS * 2 + DTI + BA_SZ_us #DIFS + 트리거 프레임 전송 시간 + SIFS + DTI + SIFS + Block Ack 전송 시간 => 전체 TWT 시간

#성능 변수
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

#station 관리 목록
stationList = []

class Station:
    def __init__(self):
        self.ru = 0 #할당된 RU
        self.cw = MIN_OCW #초기 OCW
        self.bo = random.randrange(0,self.cw) #Backoff Counter
        self.tx_status = False # True 전송 시도, False 전송 시도 X
        self.suc_status = False # True 전송 성공, False 전송 실패 [충돌]
        self.data_size = 0 #데이터 사이즈 (bytes)

def createSTA(USER):
    for i in range(0, USER):
        sta = Station()
        stationList.append(sta)

def allocationRA_RU():
    for sta in stationList:
        if(sta.bo <= 0): # 백오프 타이머가 0보다 작아졌을 때
            sta.tx_status = True #전송 시도
            sta.ru = random.randrange(1,NUM_RU+1) #랜덤으로 RU 할당 -> RARU[1] ~ RARU[NUM_RU]까지
        else:
            sta.bo -= NUM_RU #백오프타이머 감소 [RU의 수만큼 점차 감소]
            sta.tx_status = False # 전송 시도 하지 않음.

def setSuccess(ru):
    for sta in stationList:
        if(sta.tx_status == True): #만약 전송 시도를 했다면
            if(sta.ru != ru): #sta에 ru 할당 적용 -> 들어간 ru가 sta 다른 RU 라면?
                sta.suc_status = True  #전송 성공
                sta.bo = random.randrange(0, sta.cw) #전송 성공을 했기 때문에 기존 cw 범위 내에서 다시 값 재설정
def setCollision(ru):
    for sta in stationList:
        if (sta.tx_status == True):  # 만약 전송 시도를 했다면
            if (sta.ru == ru):  # sta에 ru 할당 적용 -> 들어간 ru가 sta 같은 RU 라면?
                sta.suc_status = False # 전송 실패 [충돌]
                sta.cw *= 2 #cw의 값을 2배로 증가 [OBO 범위 확대]
                if(sta.cw > MAX_OCW):
                    sta.cw = MAX_OCW #cw의 범위가 최대치보다 커질 때 최대치로 설정
                sta.bo = random.randrange(0, sta.cw) #전송 실패를 했기 때문에 기존 cw의 범위 * 2 내에서 다시 값 재설정


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

def main():
    USER_MAX = 100
    for i in range(1, USER_MAX) :
        for k in range(0, NUM_STM) : #시뮬레이션 횟수
            stationList.clear() # stationlist 초기화
            createSTA(i) #User의 수가 1일 때부터 100일 때까지 반복
        for j in range(0, NUM_DTI):
            print("시뮬레이션 내용 채우기")
    print("성능 print")

main()