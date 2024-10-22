import json
from tools import load_private_key, decrypt_symmetric_key, decrypt_transaction_data

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

import pprint
pprint.pprint(transaction_dict)