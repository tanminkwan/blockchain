# send_transaction.py

import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCDataChannel
from kademlia.network import Server
import json
import base64
from tools import (
    load_private_key, Transaction, sign_transaction,
    encrypt_transaction_data, encrypt_symmetric_key
)
from cryptography.hazmat.primitives import serialization
import os
import pprint
import argparse
import sys

# 명령줄 인자 파싱 추가
parser = argparse.ArgumentParser(description="Send a secure transaction over WebRTC with a unique 6-digit code.")
parser.add_argument("code", help="A pre-agreed 6-digit numeric code for the transaction.")

args = parser.parse_args()

# 6자리 코드 검증
code = args.code
if not code.isdigit() or len(code) != 6:
    print("Error: The code must be a 6-digit numeric string.")
    sys.exit(1)

# DHT server information
DHT_SERVER_HOST = "127.0.0.1"
DHT_SERVER_PORT = 8468

# 기존 DHT_KEY_OFFER와 DHT_KEY_ANSWER 정의 부분을 다음과 같이 수정
DHT_KEY_OFFER = f"webrtc-offer-{code}"
DHT_KEY_ANSWER = f"webrtc-answer-{code}"

async def store_sdp_in_dht(server, key, sdp):
    """Stores the SDP in DHT under the specified key."""
    combined_data = json.dumps({"sdp": sdp}).encode('utf-8')
    await server.set(key, combined_data)

async def get_sdp_from_dht(server, key):
    """Retrieves the SDP from DHT for the specified key."""
    data = await server.get(key)
    if data:
        obj = json.loads(data.decode('utf-8'))
        sdp = obj["sdp"]
        return sdp
    return None

async def run_send_transaction():
    # User information
    sender_id = 'badgirl'
    recipient_id = 'goodboy'

    #################################
    # Load Sender's RSA Private Key
    #################################
    private_key_file = f'private_key_{sender_id}.pem'
    private_key = load_private_key(private_key_file)

    #################################
    # Initialize DHT Client
    #################################
    dht_client = Server()
    await dht_client.listen(0)  # Bind to a random available port
    await dht_client.bootstrap([(DHT_SERVER_HOST, DHT_SERVER_PORT)])
    print("DHT client initialized and connected.")

    #################################
    # Initialize WebRTC PeerConnection as Offerer
    #################################
    pc = RTCPeerConnection()
    channel = pc.createDataChannel("transaction")

    # Placeholder for recipient's public key
    recipient_public_key = None

    async def send_transaction():
        nonlocal recipient_public_key

        if recipient_public_key is None:
            print("Recipient's public key not available.")
            return

        #################################
        # Create and Sign Transaction
        #################################
        amount = 10.5
        transaction = Transaction(
            sender_id=sender_id,
            recipient_id=recipient_id,
            amount=amount,
            prev_hash=None  # To be set when adding to ledger
        )

        # Sign the transaction
        sign_transaction(private_key, transaction)

        #################################
        # Encrypt Transaction Data
        #################################
        symmetric_key = os.urandom(32)  # 256-bit symmetric key
        encrypted_transaction_data = encrypt_transaction_data(transaction, symmetric_key, output_format='hex')

        # Encrypt symmetric key with recipient's public key
        encrypted_symmetric_key = encrypt_symmetric_key(symmetric_key, recipient_public_key)

        # Prepare data to send
        data_to_send = {
            'encrypted_transaction_data': encrypted_transaction_data,
            'encrypted_symmetric_key': encrypted_symmetric_key.hex(),
        }

        # Send data over data channel
        channel.send(json.dumps(data_to_send))
        print("Encrypted transaction data sent over data channel.")

    @channel.on("open")
    def on_open():
        print("Data channel 'transaction' is open.")
        asyncio.create_task(send_transaction())

    @channel.on("message")
    def on_message(message):
        print(f"Received message on 'transaction' channel: {message}")

    # Create and set the local offer
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    #################################
    # Embed Sender's Public Key in SDP
    #################################
    sender_public_key = private_key.public_key()
    sender_public_key_pem = sender_public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    sender_public_key_b64 = base64.b64encode(sender_public_key_pem).decode('utf-8')

    # Append custom SDP attribute for public key
    offer_sdp_with_pubkey = pc.localDescription.sdp + f"\r\na=pubkey:{sender_public_key_b64}"
    print("Sender's public key embedded in SDP.")

    #################################
    # Store Offer SDP in DHT
    #################################
    await store_sdp_in_dht(dht_client, DHT_KEY_OFFER, offer_sdp_with_pubkey)
    print("Offer SDP with public key stored in DHT.")

    #################################
    # Wait for Answer SDP
    #################################
    print("Waiting for Answer SDP in DHT...")
    answer_sdp = None
    while not answer_sdp:
        answer_sdp = await get_sdp_from_dht(dht_client, DHT_KEY_ANSWER)
        if not answer_sdp:
            await asyncio.sleep(1)  # Wait before retrying

    print("Answer SDP received.")

    #################################
    # Set Remote Description with Answer SDP
    #################################
    # Extract recipient's public key from answer SDP
    sdp_lines = answer_sdp.splitlines()
    recipient_public_key_b64 = None
    for line in sdp_lines:
        if line.startswith('a=pubkey:'):
            recipient_public_key_b64 = line[len('a=pubkey:'):].strip()
            break

    if not recipient_public_key_b64:
        print("Error: Recipient's public key not found in answer SDP.")
        return

    # Decode Recipient's Public Key
    recipient_public_key_pem = base64.b64decode(recipient_public_key_b64)
    recipient_public_key = serialization.load_pem_public_key(recipient_public_key_pem)
    print("Recipient's public key extracted from answer SDP.")

    # Now set the remote description
    remote_description = RTCSessionDescription(sdp=answer_sdp, type='answer')
    await pc.setRemoteDescription(remote_description)
    print("Remote description set. WebRTC connection established.")

    #################################
    # Keep Connection Alive to Ensure Data Transfer
    #################################
    try:
        await asyncio.sleep(10)  # Adjust the sleep duration as needed
    finally:
        await pc.close()
        dht_client.stop()
        print("WebRTC connection closed and DHT client stopped.")

if __name__ == "__main__":
    # Ensure compatibility with Windows event loop policy
    if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(run_send_transaction())
