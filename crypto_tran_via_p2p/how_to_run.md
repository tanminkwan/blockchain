## **1. 필요한 파이썬 패키지 설치**

터미널에서 다음 명령어를 실행하여 필요한 패키지를 설치합니다:
```bash
pip install aiortc kademlia cryptography
```

---

## **2. RSA 키 쌍 생성**

터미널에서 다음 명령어를 실행하여 `badgirl`과 `goodboy`의 개인 키를 생성합니다:

```bash
python create_keypair.py badgirl
python create_keypair.py goodboy
```

## **3. DHT 서버 실행**

터미널에서 다음 명령어를 실행하여 DHT 서버를 시작합니다:

```bash
python dht_server.py
```

DHT 서버가 성공적으로 실행되면 다음과 같은 메시지가 표시됩니다:

```
DHT 서버가 포트 8468에서 실행 중입니다.
```

> **주의**: DHT 서버는 항상 활성화 상태를 유지해야 합니다. 별도의 터미널 창에서 실행 상태를 유지하세요.

---

## **4. 스크립트 실행 및 테스트**

이제 `send_transaction.py`와 `receive_transaction.py`를 실행하여 트랜잭션을 테스트할 수 있습니다. **동일한 6자리 코드를 인자로 사용**하여 스크립트를 실행해야 합니다.

### **A. 6자리 코드 결정**

테스트를 위해 사전에 약속된 6자리 숫자 코드를 선택하세요. 예를 들어 `123456`을 사용한다고 가정하겠습니다.

### **B. `receive_transaction.py` 실행 (수신자)**

`receive_transaction.py`과 `send_transaction.py` 의 실행 순서는 중요하지 않습니다.
여기서는 먼저, `receive_transaction.py` 스크립트를 실행하여 DHT에서 Offer SDP를 기다립니다.

```bash
python receive_transaction.py 123456
```

**출력 예시:**

```
Ledger loaded.
DHT client initialized and connected.
DHT keys set as webrtc-offer-123456 and webrtc-answer-123456.
Waiting for Offer SDP in DHT...
```

### **C. `send_transaction.py` 실행 (송신자)**

다른 터미널 창을 열고, `send_transaction.py` 스크립트를 실행하여 Offer SDP를 DHT에 저장하고 Answer SDP를 기다립니다. 

```bash
python send_transaction.py 123456
```

**출력 예시:**

```
DHT client initialized and connected.
Sender's public key and transaction ID embedded in SDP.
Offer SDP with public key stored in DHT.
Waiting for Answer SDP in DHT...
Answer SDP received.
Recipient's public key extracted from answer SDP.
Remote description set. WebRTC connection established.
Data channel 'transaction' is open.
Encrypted transaction data sent over data channel.
WebRTC connection closed and DHT client stopped.
```

### **D. `receive_transaction.py`의 출력 확인 (수신자)**

`receive_transaction.py`의 터미널 창에서 다음과 같은 출력이 추가로 나타납니다:

```
Offer SDP received.
Sender's public key extracted from SDP.
Answerer's public key and transaction ID embedded in SDP.
Answer SDP with public key stored in DHT.
Remote description set with offer SDP.
Received data channel: transaction
Received encrypted transaction data.
Symmetric key decrypted.
Transaction data decrypted:
{'sender_id': 'badgirl',
 'recipient_id': 'goodboy',
 'amount': 10.5,
 'prev_hash': '0000000000000000000000000000000000000000000000000000000000000000',
 'signature': '...'}
Transaction signature verified.
Transaction added to ledger.
Ledger integrity verified.
Ledger saved.
WebRTC connection closed and DHT client stopped.
```

---

## **5. 결과 확인**

### **A. Ledger 파일 확인**

다른 터미널 창을 열고, `send_transaction.py` 스크립트를 실행하여 Offer SDP를 DHT에 저장하고 Answer SDP를 기다립니다. 

```bash
python view_transactions.py
```

```bash
--- Transaction 1 ---
Sender ID: badgirl
Recipient ID: goodboy
Amount: 10.5
Timestamp: 2024-10-25T03:04:20.744229
Previous Hash: 0000000000000000000000000000000000000000000000000000000000000000
Current Hash: b581347e01b2f78dba488693071990fb1a035ce38dc36a787e7e9a51617f5e60
Signature: 2d17f99a1d4e4f1483b2e231b2529c6f27b585bd112067d63aaa7bcf1243e0a4805913b611dcfa82789d4196b270d896d07f9c0a121c9ebfb36fe899bdc4db923a8ac8b8d0b229424a69452d18d4413f97abb1b0e10751153374597ed864715b2d48ee50d6088d9b1048096fca38c0cc8abc923eb5931ee9d890f42b55223c67ef05147ab64c193eddb24bc8857e87259d3a12db15abf9bbe06b43be9963add03ba7b62270fe57898d2e5b89230e7bff578f4a2b290a2105e159eb51fcc811b902e3b515925a29ef073a2054bd38a5b7ca408d948b7c746361d029eee41f41e4719ba32b60e89149b0a9619e6facf6e55b2b3144c93bfb3a8ad9c4b9881eefe0
-------------------------

--- Transaction 2 ---
Sender ID: badgirl
Recipient ID: goodboy
Amount: 10.5
Timestamp: 2024-10-25T04:18:59.618405
Previous Hash: b581347e01b2f78dba488693071990fb1a035ce38dc36a787e7e9a51617f5e60
Current Hash: ae502732696f321db1cdce99dacb67bd0dd2c6ff1b92cc71deb4083a2c9355f3
Signature: 169934612f674981efff6de9ea51cb919d3346da10d49168ae1a98e908923825358d9bf108573514adb1c1cc1cc69054b55301a6ae1be7e1368c6e2032c7c77f0b436e55d8566daf15ab091cfb0fe60f04ea7e1d4b39dd3dd8a0d659fd806e88ec617b96efc586493dcda6a52eb2283c9eaec0c30057f7efe4f356738093d202256a9ddd1e2f3d69d73f618e455aef1607e6b6df722ae67524ab168d301147a6cd58cb17604bd29953019c8329c2669c89a980959588bff75284a17d0ffc452d3e37356e437ed22dd284cfb06fa01690c1d1233ea850b4c8c82043c17871685cab77f0c7385e1339afcacfe8b8b734fdb0119b2617c40fefb5c7b7fefd7c9852
-------------------------
```

### **B. 로그 및 출력 메시지 확인**

두 스크립트의 출력 메시지를 통해 모든 단계가 성공적으로 완료되었는지 확인하세요. 오류 메시지가 발생한 경우, 해당 메시지를 기반으로 문제를 해결해야 합니다.

---

위의 단계들을 따라 `send_transaction.py`와 `receive_transaction.py` 스크립트를 성공적으로 실행하고 테스트할 수 있습니다. 추가적인 도움이 필요하거나 문제가 발생한 경우, `tiffanie.kim`에게 연락주세요.