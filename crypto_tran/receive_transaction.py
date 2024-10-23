import json
from tools import derive_key_from_password, Ledger, load_private_key, decrypt_symmetric_key\
    , decrypt_transaction_data, load_public_key, Transaction, verify_signature

# 수신자 정보
user_id = 'goodboy'

#################################
# Load Ledger
#################################
password = 'goodboy_password'
salt = 'i_am_a_boy'  # 사용자별 고유 솔트

# 암호화 키 생성
encryption_key = derive_key_from_password(password, salt)

# 원장 초기화 및 로드
ledger = Ledger(ledger_id=user_id, encryption_key=encryption_key)
ledger.load_from_file()

# 마지막 트랜잭션의 해시 가져오기
if ledger.transactions:
    prev_hash = ledger.transactions[-1].current_hash
else:
    prev_hash = '0' * 64  # 첫 트랜잭션의 prev_hash는 0으로 채움

#################################
# Load user's RSA Private Key 
#################################

private_key_file = f'private_key_{user_id}.pem'
private_key = load_private_key(private_key_file)

#################################
# Read a transaction
#################################

# 암호화된 데이터 로드
with open('encrypted_transaction.dat', 'r') as f:
    data_received = json.load(f)

# 암호화된 대칭키를 헥스 문자열에서 바이트로 변환
encrypted_symmetric_key_hex = data_received['encrypted_symmetric_key']
encrypted_symmetric_key = bytes.fromhex(encrypted_symmetric_key_hex)

# 수신자 비밀키로 대칭키 복호화
symmetric_key = decrypt_symmetric_key(encrypted_symmetric_key, private_key)

# 트랜잭션 데이터 복호화
encrypted_transaction_data = data_received['encrypted_transaction_data']
transaction_dict = decrypt_transaction_data(encrypted_transaction_data, symmetric_key, input_format='hex')

# 트랜잭션 내용 출력
import pprint
pprint.pprint(transaction_dict)

# 송신자 공개키 로드
sender_id = transaction_dict.get('sender_id')
sender_public_key = load_public_key(f'public_key_{sender_id}.pem')

# 트랜잭션 객체 생성
transaction = Transaction(**transaction_dict)

# 서명 검증 수행
is_valid = verify_signature(sender_public_key, transaction)
if is_valid:
    print("트랜잭션 서명이 검증되었습니다.")
    # 여기서 트랜잭션 처리 로직을 추가할 수 있습니다.
else:
    print("트랜잭션 서명 검증에 실패했습니다.")
    exit(1)

#################################
# add transaction into Ledger
#################################

# 트랜잭션 객체에 해시 생성
transaction.put_hash(prev_hash)

# 트랜잭션을 원장에 추가
if ledger.add_transaction(transaction):
    print("트랜잭션이 원장에 추가되었습니다.")

# 원장 무결성 검증
ledger.verify_integrity()

# 원장 저장
ledger.save_to_file()