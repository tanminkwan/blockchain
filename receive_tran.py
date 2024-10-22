import json
from tools import load_private_key, decrypt_symmetric_key, decrypt_transaction_data\
    , verify_signature, load_public_key

# 암호화된 데이터 로드
with open('encrypted_transaction.dat', 'r') as f:
    data_received = json.load(f)

# 암호화된 대칭키를 헥스 문자열에서 바이트로 변환
encrypted_symmetric_key_hex = data_received['encrypted_symmetric_key']
encrypted_symmetric_key = bytes.fromhex(encrypted_symmetric_key_hex)

# 수신자 비밀키 로드
user_id = 'goodboy'
recipient_private_key = load_private_key(f'private_key_{user_id}.pem')
# 대칭키 복호화
symmetric_key = decrypt_symmetric_key(encrypted_symmetric_key, recipient_private_key)

# 트랜잭션 데이터 복호화
encrypted_transaction_data = data_received['encrypted_transaction_data']
transaction_dict = decrypt_transaction_data(encrypted_transaction_data, symmetric_key, input_format='hex')

# 트랜잭션 내용 출력
import pprint
pprint.pprint(transaction_dict)

# 트랜잭션 서명과 해시 추출
signature_hex = transaction_dict.get('signature')
signature = bytes.fromhex(signature_hex) if signature_hex else None
current_hash = transaction_dict.get('current_hash')

# 송신자의 공개키 로드
sender_id = transaction_dict.get('sender_id')
sender_public_key = load_public_key(sender_id)

# 서명 검증 수행
is_valid = verify_signature(sender_public_key, signature, current_hash)
if is_valid:
    print("트랜잭션 서명이 검증되었습니다.")
    # 여기서 트랜잭션 처리 로직을 추가할 수 있습니다.
else:
    print("트랜잭션 서명 검증에 실패했습니다.")