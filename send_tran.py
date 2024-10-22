import os
import json
from tools import derive_key_from_password, Ledger, load_public_key\
    , encrypt_transaction_data, encrypt_symmetric_key

# 사용자 정보
sender_id = 'badgirl'
password = 'badgirl_password'
salt = 'i_am_a_girl'  # 사용자별 고유 솔트

# 원장 열기용 암호화 키 생성
encryption_key = derive_key_from_password(password, salt)

# 원장 초기화 및 로드
ledger = Ledger(ledger_id=sender_id, encryption_key=encryption_key)
ledger.load_from_file()

# 수신자 정보
recipient_id = 'goodboy'
# 수신자 공개키 로드
recipient_public_key = load_public_key(recipient_id)

# 수신자의 마지막 transaction 담기
transactions = ledger.get_transactions(recipient_id=recipient_id)
transaction = transactions[-1]

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
