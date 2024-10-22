from tools import derive_key_from_password, Ledger, load_private_key, load_public_key\
    , Transaction, sign_transaction

# 사용자 정보
sender_id = 'badgirl'
password = 'badgirl_password'
salt = 'i_am_a_girl'  # 사용자별 고유 솔트

# 암호화 키 생성
encryption_key = derive_key_from_password(password, salt)

# 원장 초기화 및 로드
ledger = Ledger(ledger_id=sender_id, encryption_key=encryption_key)
ledger.load_from_file()

# 키 페어 로드
private_key_file = f'private_key_{sender_id}.pem'
public_key_file = f'public_key_{sender_id}.pem'

private_key = load_private_key(private_key_file)
public_key = load_public_key(sender_id)


# 수신자 공개키 로드 (수신자가 미리 공개키를 제공했다고 가정)
recipient_id = 'goodboy'
recipient_public_key = load_public_key(recipient_id)

# 마지막 트랜잭션의 해시 가져오기
if ledger.transactions:
    prev_hash = ledger.transactions[-1].current_hash
else:
    prev_hash = '0' * 64  # 첫 트랜잭션의 prev_hash는 0으로 채움

# 새로운 트랜잭션 생성
amount = 10.5
transaction = Transaction(
    sender_id=sender_id,
    recipient_id=recipient_id,
    amount=amount,
    prev_hash=prev_hash
)

# 트랜잭션 서명
sign_transaction(private_key, transaction)

# 트랜잭션을 원장에 추가
if ledger.add_transaction(transaction):
    print("트랜잭션이 원장에 추가되었습니다.")

# 원장 무결성 검증
ledger.verify_integrity()

# 원장 저장
ledger.save_to_file()