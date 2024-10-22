from tools import derive_key_from_password, Ledger

# 사용자 정보
sender_id = 'badgirl'
password = 'badgirl_password'
salt = 'i_am_a_girl'  # 사용자별 고유 솔트

# 암호화 키 생성
encryption_key = derive_key_from_password(password, salt)

# 원장 초기화 및 로드
ledger = Ledger(ledger_id=sender_id, encryption_key=encryption_key)
ledger.load_from_file()

ledger.print_transactions()