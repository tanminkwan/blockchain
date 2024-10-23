# dht_node.py

import asyncio
from kademlia.network import Server
from kademlia.protocol import KademliaProtocol

class LoggingKademliaProtocol(KademliaProtocol):
    def rpc_store(self, sender, nodeid, key, value):
        print(f"데이터 저장 요청을 받았습니다: 보낸이 {sender}, 키: {key}, 값: {value}")
        return super().rpc_store(sender, nodeid, key, value)
    
    def rpc_find_value(self, sender, nodeid, key):
        print(f"데이터 요청을 받았습니다: 보낸이 {sender}, 키: {key}")
        return super().rpc_find_value(sender, nodeid, key)

async def run():
    server = Server()
    await server.listen(8468)
    # 프로토콜 인스턴스를 생성하여 설정
    server.protocol = LoggingKademliaProtocol(server.node, server.storage, ksize=server.ksize)
    print("DHT 노드가 포트 8468에서 실행 중입니다.")
    while True:
        await asyncio.sleep(3600)

asyncio.run(run())
