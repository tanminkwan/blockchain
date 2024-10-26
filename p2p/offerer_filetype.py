# offerer_filetype.py
import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription

async def run_offer():
    # Create peer connection
    pc = RTCPeerConnection()

    # Create data channel
    channel = pc.createDataChannel("chat")

    # Send message on open
    @channel.on("open")
    def on_open():
        channel.send("Hello from Peer A!")

    # Receive message
    @channel.on("message")
    def on_message(message):
        print(f"Received message from Peer B: {message}")

    # Create offer
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    
    # Write offer SDP to file
    with open("offer_sdp.txt", "w") as f:
        f.write(pc.localDescription.sdp)
    
    print("Offer SDP saved to offer_sdp.txt")

    # Wait for Answer SDP from file
    input("Press Enter after putting Answer SDP in 'answer_sdp.txt'...")

    # Read Answer SDP from file
    with open("answer_sdp.txt", "r") as f:
        answer_sdp = f.read()
    
    await pc.setRemoteDescription(RTCSessionDescription(answer_sdp, "answer"))

    # Keep connection open
    await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(run_offer())
