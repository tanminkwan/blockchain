# offerer.py

import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription
import json
import uuid
from kademlia.network import Server

SERVICE_NAME = "chat_service"  # 제공하는 서비스 이름

async def run_offer():
    # DHT 서버 설정 및 부트스트랩
    dht_server = Server()
    await dht_server.listen(8469)
    await dht_server.bootstrap([("127.0.0.1", 8468)])

    # 고유 ID 생성
    unique_id = str(uuid.uuid4())
    offer_key = f"offer_sdp_{unique_id}"

    pc = RTCPeerConnection()

    # 데이터 채널 생성
    channel = pc.createDataChannel("chat")

    @channel.on("open")
    def on_open():
        print("데이터 채널이 열렸습니다!")
        channel.send("제안자로부터의 메시지입니다.")

    @channel.on("message")
    def on_message(message):
        print("받은 메시지:", message)

    # Offer 생성 및 로컬 디스크립션 설정
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    # 서비스 이름을 키로 하여 자신의 ID를 DHT에 등록
    await dht_server.set(f"service_{SERVICE_NAME}", unique_id)
    print(f"서비스 '{SERVICE_NAME}'에 자신을 등록했습니다. ID: {unique_id}")

    # Offer SDP를 DHT에 저장
    await dht_server.set(offer_key, json.dumps({
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    }))
    print(f"Offer SDP를 DHT에 저장했습니다. 키: {offer_key}")

    # Answer SDP 기다리기
    print("Answer SDP를 기다리는 중...")
    answer_key = f"answer_sdp_{unique_id}"
    while True:
        answer_json = await dht_server.get(answer_key)
        if answer_json:
            answer = json.loads(answer_json)
            answer_sdp = RTCSessionDescription(sdp=answer["sdp"], type=answer["type"])
            await pc.setRemoteDescription(answer_sdp)
            print("Answer SDP를 받았습니다.")
            break
        await asyncio.sleep(1)

    # 연결 유지
    await asyncio.Future()

asyncio.run(run_offer())
