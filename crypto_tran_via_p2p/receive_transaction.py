# receive_transaction.py

import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription
from kademlia.network import Server
import json
import base64
from tools import (
    derive_key_from_password, Ledger, load_private_key,
    decrypt_symmetric_key, decrypt_transaction_data,
    verify_signature, Transaction
)
from cryptography.hazmat.primitives import serialization
import pprint
import argparse
import sys

# 스크립트 시작 부분에 추가
parser = argparse.ArgumentParser(description="Receive a secure transaction over WebRTC with a unique 6-digit code.")
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

async def run_receive_transaction():
    # User information
    user_id = 'goodboy'
    sender_id = 'badgirl'

    #################################
    # Load Ledger
    #################################
    password = 'goodboy_password'
    salt = 'i_am_a_boy'  # Unique per user

    encryption_key = derive_key_from_password(password, salt)

    ledger = Ledger(ledger_id=user_id, encryption_key=encryption_key)
    ledger.load_from_file()
    print("Ledger loaded.")

    #################################
    # Initialize DHT Client
    #################################
    dht_client = Server()
    await dht_client.listen(0)  # Bind to a random available port
    await dht_client.bootstrap([(DHT_SERVER_HOST, DHT_SERVER_PORT)])
    print("DHT client initialized and connected.")

    #################################
    # Wait for Offer SDP
    #################################
    print("Waiting for Offer SDP in DHT...")
    offer_sdp = None
    while not offer_sdp:
        offer_sdp = await get_sdp_from_dht(dht_client, DHT_KEY_OFFER)
        if not offer_sdp:
            await asyncio.sleep(1)  # Wait before retrying

    print("Offer SDP received.")

    #################################
    # Extract Sender's Public Key from SDP
    #################################
    sdp_lines = offer_sdp.splitlines()
    sender_public_key_b64 = None
    for line in sdp_lines:
        if line.startswith('a=pubkey:'):
            sender_public_key_b64 = line[len('a=pubkey:'):].strip()
            break

    if not sender_public_key_b64:
        print("Error: Sender's public key not found in SDP.")
        return

    # Decode Sender's Public Key
    sender_public_key_pem = base64.b64decode(sender_public_key_b64)
    sender_public_key = serialization.load_pem_public_key(sender_public_key_pem)
    print("Sender's public key extracted from SDP.")

    #################################
    # Initialize WebRTC PeerConnection as Answerer
    #################################
    pc = RTCPeerConnection()

    @pc.on("datachannel")
    def on_datachannel(channel):
        print(f"Received data channel: {channel.label}")

        @channel.on("message")
        async def on_message(message):
            print("Received encrypted transaction data.")
            data_received = json.loads(message)

            encrypted_transaction_data = data_received['encrypted_transaction_data']
            encrypted_symmetric_key_hex = data_received['encrypted_symmetric_key']
            encrypted_symmetric_key = bytes.fromhex(encrypted_symmetric_key_hex)

            #################################
            # Load Recipient's Private Key
            #################################
            private_key_file = f'private_key_{user_id}.pem'
            private_key = load_private_key(private_key_file)

            #################################
            # Decrypt Symmetric Key
            #################################
            symmetric_key = decrypt_symmetric_key(encrypted_symmetric_key, private_key)
            print("Symmetric key decrypted.")

            #################################
            # Decrypt Transaction Data
            #################################
            transaction_dict = decrypt_transaction_data(encrypted_transaction_data, symmetric_key, input_format='hex')
            print("Transaction data decrypted:")
            pprint.pprint(transaction_dict)

            #################################
            # Create Transaction Object
            #################################
            transaction = Transaction(**transaction_dict)

            #################################
            # Verify Signature
            #################################
            is_valid = verify_signature(sender_public_key, transaction)
            if is_valid:
                print("Transaction signature verified.")

                #################################
                # Add Transaction to Ledger
                #################################
                # Determine previous hash
                if ledger.transactions:
                    prev_hash = ledger.transactions[-1].current_hash
                else:
                    prev_hash = '0' * 64

                # Set previous hash and calculate current hash
                transaction.put_hash(prev_hash)

                # Add to ledger
                if ledger.add_transaction(transaction):
                    print("Transaction added to ledger.")

                #################################
                # Verify Ledger Integrity
                #################################
                ledger.verify_integrity()

                #################################
                # Save Ledger
                #################################
                ledger.save_to_file()
                print("Ledger saved.")
            else:
                print("Transaction signature verification failed.")

    #################################
    # Set Remote Description with Offer SDP
    #################################
    remote_description = RTCSessionDescription(sdp=offer_sdp, type='offer')
    await pc.setRemoteDescription(remote_description)
    print("Remote description set with offer SDP.")

    #################################
    # Embed Answerer's Public Key in SDP
    #################################
    # Load Answerer's (recipient's) private key to get the public key
    private_key_file = f'private_key_{user_id}.pem'
    private_key = load_private_key(private_key_file)
    answer_public_key = private_key.public_key()
    answer_public_key_pem = answer_public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    answer_public_key_b64 = base64.b64encode(answer_public_key_pem).decode('utf-8')

    #################################
    # Create and Set Answer SDP
    #################################
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    # Append custom SDP attribute for public key
    answer_sdp_with_pubkey = pc.localDescription.sdp + f"\r\na=pubkey:{answer_public_key_b64}"
    print("Answerer's public key embedded in SDP.")

    #################################
    # Store Answer SDP in DHT
    #################################
    await store_sdp_in_dht(dht_client, DHT_KEY_ANSWER, answer_sdp_with_pubkey)
    print("Answer SDP with public key stored in DHT.")

    #################################
    # Keep Connection Alive to Receive Data
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

    asyncio.run(run_receive_transaction())
