# answerer.py

import asyncio
import json
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
from aiortc import RTCPeerConnection, RTCSessionDescription
from kademlia.network import Server
from queue import Queue
import logging

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)

SERVICE_NAME = "chat_service"  # 연결하고자 하는 서비스 이름

# 메시지 전송을 위한 큐
message_queue = Queue()

# 데이터 채널을 저장할 리스트
data_channels = []

# Tkinter GUI 설정
def create_gui(send_callback):
    root = tk.Tk()
    root.title("Answerer - Chat")

    # 수신 메시지 표시 영역
    received_label = tk.Label(root, text="Received Messages:")
    received_label.pack(pady=5)

    received_text = scrolledtext.ScrolledText(root, width=50, height=10, state='disabled')
    received_text.pack(padx=10, pady=5)

    # 메시지 입력 영역
    input_frame = tk.Frame(root)
    input_frame.pack(padx=10, pady=5)

    message_entry = tk.Entry(input_frame, width=40)
    message_entry.pack(side=tk.LEFT, padx=(0, 10))

    send_button = tk.Button(input_frame, text="Send", command=lambda: send_callback(message_entry, received_text))
    send_button.pack(side=tk.LEFT)

    return root, received_text, message_entry

# 메시지 전송 버튼 콜백
def send_message(message_entry, received_text):
    message = message_entry.get().strip()
    if message:
        message_queue.put(message)
        message_entry.delete(0, tk.END)

# 메시지 수신 시 GUI 업데이트
def display_received_message(received_text, message):
    received_text.config(state='normal')
    received_text.insert(tk.END, f"Offerer: {message}\n")
    received_text.config(state='disabled')
    messagebox.showinfo("New Message", f"Offerer says: {message}")

# Asyncio를 실행할 함수
async def run_answerer(received_text):
    global data_channels  # 전역 데이터 채널 리스트 사용

    # DHT 서버 설정 및 부트스트랩
    dht_server = Server()
    await dht_server.listen(8470)
    bootstrap_nodes = [("127.0.0.1", 8468)]  # 실제 DHT 노드의 IP로 변경
    print(f"DHT 부트스트랩 중: {bootstrap_nodes}")
    try:
        await dht_server.bootstrap(bootstrap_nodes)
        print("DHT 부트스트랩 완료")
    except Exception as e:
        print(f"DHT 부트스트랩 실패: {e}")
        return

    # 연결된 노드 수 계산
    total_contacts = sum(len(bucket.nodes) for bucket in dht_server.protocol.router.buckets)
    print(f"DHT에 연결된 노드 수: {total_contacts}")

    # WebRTC 피어 연결 설정
    pc = RTCPeerConnection()

    @pc.on("datachannel")
    def on_datachannel(channel):
        print("데이터 채널을 받았습니다.")
        data_channels.append(channel)  # 데이터 채널 리스트에 추가

        @channel.on("open")
        def on_open():
            print("데이터 채널이 열렸습니다.")

        @channel.on("message")
        def on_message(message):
            print(f"받은 메시지: {message}")
            # Tkinter GUI에 메시지 표시
            received_text.after(0, display_received_message, received_text, message)

    # 서비스 이름을 통해 제안자의 ID 가져오기
    print(f"서비스 '{SERVICE_NAME}'를 제공하는 제안자를 검색 중...")
    service_key = f"service_{SERVICE_NAME}"
    attempt = 0
    target_peer_id = None
    while True:
        attempt += 1
        target_peer_id = await dht_server.get(service_key)
        if target_peer_id:
            print(f"제안자의 ID를 찾았습니다: {target_peer_id}")
            break
        print(f"제안자를 찾는 중... 시도 횟수: {attempt}")
        await asyncio.sleep(1)

    # Offer SDP 가져오기
    offer_key = f"offer_sdp_{target_peer_id}"
    print(f"Offer SDP를 DHT에서 가져오는 중... 키: {offer_key}")
    offer_json = None
    while True:
        offer_json = await dht_server.get(offer_key)
        if offer_json:
            offer = json.loads(offer_json)
            offer_sdp = RTCSessionDescription(sdp=offer["sdp"], type=offer["type"])
            await pc.setRemoteDescription(offer_sdp)
            print("Offer SDP를 받았습니다.")
            break
        print("Offer SDP를 기다리는 중...")
        await asyncio.sleep(1)

    # Answer SDP 생성 및 로컬 디스크립션 설정
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    # Answer SDP를 DHT에 저장
    answer_key = f"answer_sdp_{target_peer_id}"
    try:
        await dht_server.set(answer_key, json.dumps({
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        }))
        print(f"Answer SDP를 DHT에 저장했습니다. 키: {answer_key}")
    except Exception as e:
        print(f"Answer SDP 저장 중 예외 발생: {e}")
        return

    # 메시지 전송 대기
    while True:
        if not message_queue.empty():
            message = message_queue.get()
            # 열린 데이터 채널을 찾아 메시지 전송
            for channel in data_channels:
                if channel.readyState == 'open':
                    channel.send(message)
                    print(f"보낸 메시지: {message}")
                    # GUI에 보낸 메시지 표시
                    received_text.after(0, lambda: received_text.config(state='normal') or received_text.insert(tk.END, f"You: {message}\n") or received_text.config(state='disabled'))
        await asyncio.sleep(0.1)

# Asyncio 스레드 함수
def start_asyncio_loop(root, received_text):
    asyncio.run(run_answerer(received_text))

if __name__ == "__main__":
    # GUI 생성
    root, received_text, message_entry = create_gui(send_message)

    # Asyncio 루프를 별도의 스레드에서 실행
    asyncio_thread = threading.Thread(target=start_asyncio_loop, args=(root, received_text), daemon=True)
    asyncio_thread.start()

    # GUI 메인 루프 시작
    root.mainloop()
