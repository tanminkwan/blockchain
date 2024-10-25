# dht_server.py
from kademlia.network import Server
import asyncio
import sys

async def run_server(port=8468, bootstrap_node=None):
    server = Server()
    await server.listen(port)
    
    if bootstrap_node:
        host, port = bootstrap_node.split(':')
        await server.bootstrap([(host, int(port))])
        print(f"Bootstrapped with node at {host}:{port}")
    
    print(f"DHT Server running on port {port}")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        server.stop()

if __name__ == "__main__":
    # 포트를 고정하여 입력받지 않도록 수정
    bootstrap_node = None
    if len(sys.argv) > 1:
        bootstrap_node = sys.argv[1]
    
    asyncio.run(run_server())
