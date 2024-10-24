import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription

async def run_answer():
    # Create peer connection
    pc = RTCPeerConnection()

    # Receive data channel
    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            print(f"Received message from Peer A: {message}")
            # Respond back
            channel.send("Hello from Peer B!")

    # Read Offer SDP from file
    with open("offer_sdp.txt", "r") as f:
        offer_sdp = f.read()

    await pc.setRemoteDescription(RTCSessionDescription(offer_sdp, "offer"))

    # Create answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    # Write Answer SDP to file
    with open("answer_sdp.txt", "w") as f:
        f.write(pc.localDescription.sdp)
    
    print("Answer SDP saved to answer_sdp.txt")

    # Keep connection open
    await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(run_answer())
