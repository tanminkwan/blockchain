import os
import json
from tools import load_private_key, load_public_key, Transaction, sign_transaction\
    , encrypt_transaction_data, encrypt_symmetric_key

# 사용자 정보
sender_id = 'badgirl'

#################################
# Load user's RSA Private Key 
#################################
private_key_file = f'private_key_{sender_id}.pem'
private_key = load_private_key(private_key_file)

# 수신자 공개키 로드 (수신자가 미리 공개키를 제공했다고 가정)
recipient_id = 'goodboy'
recipient_public_key = load_public_key(f'public_key_{recipient_id}.pem')

# 새로운 트랜잭션 생성
amount = 10.5
transaction = Transaction(
    sender_id=sender_id,
    recipient_id=recipient_id,
    amount=amount,
)

# 트랜잭션 서명
sign_transaction(private_key, transaction)

# 트랜잭션 내용 출력
import pprint
pprint.pprint(transaction.to_dict())

# 대칭키 생성
symmetric_key = os.urandom(32)  # 256비트 대칭키 생성

# 트랜잭션 데이터 암호화
encrypted_transaction_data = encrypt_transaction_data(transaction, symmetric_key, output_format='hex')

# 대칭키 암호화
encrypted_symmetric_key = encrypt_symmetric_key(symmetric_key, recipient_public_key)

# 암호화된 데이터 전송 (네트워크 전송 시 이 데이터들을 전송)
data_to_send = {
    'encrypted_transaction_data': encrypted_transaction_data,
    'encrypted_symmetric_key': encrypted_symmetric_key.hex(),
}

# 여기서는 예시로 파일에 저장
with open('encrypted_transaction.dat', 'w') as f:
    json.dump(data_to_send, f)