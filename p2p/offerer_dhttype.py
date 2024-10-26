# offerer_dhttype.py
import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCDataChannel
from kademlia.network import Server
import json

# DHT 서버 정보
DHT_SERVER_HOST = "127.0.0.1"
DHT_SERVER_PORT = 8468
DHT_KEY_OFFER = "webrtc-offer"
DHT_KEY_ANSWER = "webrtc-answer"

async def store_sdp_in_dht(server, key, sdp):
    """
    SDP를 JSON 형식으로 저장하고 바이트로 인코딩하여 DHT에 저장합니다.
    """
    combined_data = json.dumps({"sdp": sdp}).encode('utf-8')
    await server.set(key, combined_data)

async def get_sdp_from_dht(server, key):
    """
    DHT에서 SDP를 가져오고 JSON을 파싱하여 반환합니다.
    """
    data = await server.get(key)
    if data:
        obj = json.loads(data.decode('utf-8'))
        sdp = obj["sdp"]
        return sdp
    return None

async def run_offer():
    # Kademlia 클라이언트 초기화 (포트=0으로 설정하여 서버 역할을 하지 않음)
    dht_client = Server()
    await dht_client.listen(0)  # 포트를 0으로 설정하여 OS가 임의의 포트를 할당
    # 중앙 DHT 서버에 부트스트랩
    await dht_client.bootstrap([(DHT_SERVER_HOST, DHT_SERVER_PORT)])

    # WebRTC PeerConnection 초기화
    pc = RTCPeerConnection()
    channel = pc.createDataChannel("chat")

    @channel.on("open")
    def on_open():
        print("Data channel 'chat' is open")
        channel.send("Hello from Peer A!")

    @channel.on("message")
    def on_message(message):
        print(f"Received message from Peer B: {message}")

    # Offer SDP 생성 및 로컬 설명 설정
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    # DHT 서버에 Offer SDP 저장
    await store_sdp_in_dht(dht_client, DHT_KEY_OFFER, pc.localDescription.sdp)
    print("Offer SDP stored in DHT.")

    # DHT 서버에서 Answer SDP 대기
    print("Waiting for Answer SDP in DHT...")
    answer_sdp = None
    while not answer_sdp:
        answer_sdp = await get_sdp_from_dht(dht_client, DHT_KEY_ANSWER)
        if not answer_sdp:
            await asyncio.sleep(1)

    # Remote Description 설정
    await pc.setRemoteDescription(RTCSessionDescription(answer_sdp, "answer"))
    print("Remote description set. WebRTC connection established.")

    # 연결 유지 (데이터 교환)
    try:
        await asyncio.sleep(30)  # 필요에 따라 조정
    finally:
        await pc.close()
        dht_client.stop()

if __name__ == "__main__":
    # Windows 호환성 설정
    if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(run_offer())
