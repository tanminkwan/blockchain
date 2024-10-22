import os
import json
import hashlib
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.fernet import Fernet

# RSA 비밀키, 공개키 생성
def generate_rsa_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,  # 또는 보안을 위해 3072 또는 4096 사용 가능
    )
    public_key = private_key.public_key()
    return private_key, public_key

# Transaction 클래스 정의
class Transaction:
    def __init__(self, sender_id, recipient_id, amount, prev_hash):
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.amount = amount
        self.timestamp = datetime.utcnow().isoformat()
        self.prev_hash = prev_hash
        self.signature = None
        self.current_hash = self.calculate_hash()

    def to_dict(self):
        return {
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'amount': self.amount,
            'timestamp': self.timestamp,
            'prev_hash': self.prev_hash,
            'signature': self.signature.hex() if self.signature else None,
            'current_hash': self.current_hash if hasattr(self, 'current_hash') else None,
        }

    def calculate_hash(self):
        tx_dict = self.to_dict()
        # 서명과 current_hash는 해시 계산에서 제외
        tx_dict_copy = tx_dict.copy()
        tx_dict_copy['signature'] = None
        tx_dict_copy['current_hash'] = None
        tx_string = json.dumps(tx_dict_copy, sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()

# Ledger 클래스 정의
class Ledger:
    def __init__(self, ledger_id, encryption_key=None):
        self.ledger_id = ledger_id
        self.transactions = []
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.cipher_suite = Fernet(self.encryption_key)

    def add_transaction(self, transaction):
        # 무결성 검증
        if self.transactions:
            last_tx = self.transactions[-1]
            if transaction.prev_hash != last_tx.current_hash:
                print("오류: 트랜잭션의 이전 해시가 일치하지 않습니다.")
                return False
        else:
            if transaction.prev_hash != '0' * 64:
                print("오류: 첫 트랜잭션의 이전 해시는 0이어야 합니다.")
                return False
        # 트랜잭션 서명 검증
        sender_public_key = load_public_key(transaction.sender_id)
        if not verify_signature(sender_public_key, transaction.signature, transaction.current_hash):
            print("오류: 트랜잭션의 서명이 유효하지 않습니다.")
            return False
        # 트랜잭션 추가
        self.transactions.append(transaction)
        return True

    def verify_integrity(self):
        for i in range(len(self.transactions)):
            current_tx = self.transactions[i]
            # 현재 트랜잭션의 해시 재계산
            if current_tx.current_hash != current_tx.calculate_hash():
                print(f"오류: 트랜잭션 {i}의 해시가 일치하지 않습니다.")
                return False
            # 이전 해시 검증
            if i > 0:
                prev_tx = self.transactions[i - 1]
                if current_tx.prev_hash != prev_tx.current_hash:
                    print(f"오류: 트랜잭션 {i}의 이전 해시가 일치하지 않습니다.")
                    return False
            else:
                # 첫 번째 트랜잭션의 prev_hash는 0으로 설정
                if current_tx.prev_hash != '0' * 64:
                    print("오류: 첫 트랜잭션의 이전 해시는 0이어야 합니다.")
                    return False
        print("원장의 무결성이 확인되었습니다.")
        return True

    def save_to_file(self, filename=None):
        # 트랜잭션을 JSON으로 직렬화
        tx_list = [tx.to_dict() for tx in self.transactions]
        tx_json = json.dumps(tx_list).encode('utf-8')
        # 데이터 암호화
        encrypted_data = self.cipher_suite.encrypt(tx_json)
        # 파일로 저장
        if filename is None:
            filename = f'ledger_{self.ledger_id}.dat'
        with open(filename, 'wb') as f:
            f.write(encrypted_data)

    def load_from_file(self, filename=None):
        if filename is None:
            filename = f'ledger_{self.ledger_id}.dat'
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                encrypted_data = f.read()
            # 데이터 복호화
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            # 트랜잭션 복원
            tx_list = json.loads(decrypted_data.decode('utf-8'))
            self.transactions = []
            for tx_dict in tx_list:
                tx = Transaction(
                    sender_id=tx_dict['sender_id'],
                    recipient_id=tx_dict['recipient_id'],
                    amount=tx_dict['amount'],
                    prev_hash=tx_dict['prev_hash'],
                )
                tx.timestamp = tx_dict['timestamp']
                tx.signature = bytes.fromhex(tx_dict['signature']) if tx_dict['signature'] else None
                # current_hash 설정
                if 'current_hash' in tx_dict and tx_dict['current_hash']:
                    tx.current_hash = tx_dict['current_hash']
                else:
                    tx.current_hash = tx.calculate_hash()
                self.transactions.append(tx)
        else:
            # 기존 원장 파일이 없는 경우
            pass

    def get_transactions(self, sender_id=None, recipient_id=None):
        """
        원장에 저장된 트랜잭션 목록을 반환합니다.
        옵션으로 송신자 ID 또는 수신자 ID를 기준으로 필터링할 수 있습니다.
        """
        filtered_transactions = self.transactions
        if sender_id:
            filtered_transactions = [tx for tx in filtered_transactions if tx.sender_id == sender_id]
        if recipient_id:
            filtered_transactions = [tx for tx in filtered_transactions if tx.recipient_id == recipient_id]
        return filtered_transactions

    def print_transactions(self, transactions=None):
        """
        트랜잭션 목록을 이해하기 쉽게 출력합니다.
        """
        transactions = transactions or self.transactions
        if not transactions:
            print("원장에 저장된 트랜잭션이 없습니다.")
            return
        for i, tx in enumerate(transactions):
            print(f"--- Transaction {i+1} ---")
            print(f"Sender ID: {tx.sender_id}")
            print(f"Recipient ID: {tx.recipient_id}")
            print(f"Amount: {tx.amount}")
            print(f"Timestamp: {tx.timestamp}")
            print(f"Previous Hash: {tx.prev_hash}")
            print(f"Current Hash: {tx.current_hash}")
            print(f"Signature: {tx.signature.hex() if tx.signature else 'None'}")
            print("-------------------------\n")

# 공개키/비밀키 로드 및 저장 함수
def save_private_key(private_key, filename):
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    with open(filename, 'wb') as f:
        f.write(pem)

def load_private_key(filename):
    with open(filename, 'rb') as f:
        pem_data = f.read()
    private_key = serialization.load_pem_private_key(pem_data, password=None)
    return private_key

def save_public_key(public_key, filename):
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(filename, 'wb') as f:
        f.write(pem)

def load_public_key(user_id):
    filename = f'public_key_{user_id}.pem'
    with open(filename, 'rb') as f:
        pem_data = f.read()
    public_key = serialization.load_pem_public_key(pem_data)
    return public_key

# 대칭키로 transaction 정보 암호화
def encrypt_transaction_data(transaction, symmetric_key, output_format='bytes'):
    """
    트랜잭션 데이터를 대칭키로 암호화하고 지정된 형식으로 반환합니다.

    :param transaction: 트랜잭션 객체
    :param symmetric_key: 대칭키 (bytes)
    :param output_format: 'bytes' 또는 'hex' 중 선택 (기본값: 'bytes')
    :return: 암호화된 데이터 딕셔너리
    """
    # 트랜잭션 데이터를 JSON으로 직렬화
    tx_data = json.dumps(transaction.to_dict(), sort_keys=True).encode('utf-8')
    # 대칭키 암호화 (AES-GCM 사용)
    iv = os.urandom(12)  # 초기화 벡터
    encryptor = Cipher(
        algorithms.AES(symmetric_key),
        modes.GCM(iv)
    ).encryptor()
    ciphertext = encryptor.update(tx_data) + encryptor.finalize()

    encrypted_data = {
        'ciphertext': ciphertext,
        'iv': iv,
        'tag': encryptor.tag
    }

    if output_format == 'hex':
        # 바이트 데이터를 헥스 문자열로 변환
        encrypted_data = {
            'ciphertext': ciphertext.hex(),
            'iv': iv.hex(),
            'tag': encryptor.tag.hex()
        }
    elif output_format != 'bytes':
        raise ValueError("output_format은 'bytes' 또는 'hex' 중 하나여야 합니다.")

    return encrypted_data

# 대칭키를 recipient의 public key로 암호화
def encrypt_symmetric_key(symmetric_key, recipient_public_key):
    encrypted_symmetric_key = recipient_public_key.encrypt(
        symmetric_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted_symmetric_key

# recipient의 public key로 sender가 보낸 암호화된 대칭키를 recipient의 private key로 복호화
def decrypt_symmetric_key(encrypted_symmetric_key, recipient_private_key):
    symmetric_key = recipient_private_key.decrypt(
        encrypted_symmetric_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return symmetric_key

# sender의 대칭키로 transaction 복호화
def decrypt_transaction_data(encrypted_data, symmetric_key, input_format='bytes'):
    """
    대칭키로 암호화된 트랜잭션 데이터를 복호화하고, 트랜잭션 딕셔너리를 반환합니다.

    :param encrypted_data: 암호화된 데이터 딕셔너리 (ciphertext, iv, tag)
    :param symmetric_key: 대칭키 (bytes)
    :param input_format: 'bytes' 또는 'hex' 중 선택 (기본값: 'bytes')
    :return: 복호화된 트랜잭션 데이터 (dict)
    """
    if input_format == 'hex':
        # 헥스 문자열을 바이트로 변환
        iv = bytes.fromhex(encrypted_data['iv'])
        tag = bytes.fromhex(encrypted_data['tag'])
        ciphertext = bytes.fromhex(encrypted_data['ciphertext'])
    elif input_format == 'bytes':
        iv = encrypted_data['iv']
        tag = encrypted_data['tag']
        ciphertext = encrypted_data['ciphertext']
    else:
        raise ValueError("input_format은 'bytes' 또는 'hex' 중 하나여야 합니다.")

    decryptor = Cipher(
        algorithms.AES(symmetric_key),
        modes.GCM(iv, tag)
    ).decryptor()
    tx_data = decryptor.update(ciphertext) + decryptor.finalize()
    return json.loads(tx_data.decode('utf-8'))

# 트랜잭션 서명 함수(RSA 키용)
def sign_transaction(private_key, transaction):
    tx_hash = transaction.current_hash.encode()
    signature = private_key.sign(
        tx_hash,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256()
    )
    transaction.signature = signature

# 서명 검증 함수 정의
def verify_signature(public_key, signature, current_hash):
    try:
        public_key.verify(
            signature,
            current_hash.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        print(f"서명 검증 실패: {e}")
        return False

# 암호화 키 파생 함수
def derive_key_from_password(password, salt):
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    import base64

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt.encode(),
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

#대칭키 복호화: 자신의 비밀키로 암호화된 대칭키를 복호화합니다.
def decrypt_symmetric_key(encrypted_symmetric_key, recipient_private_key):
    symmetric_key = recipient_private_key.decrypt(
        encrypted_symmetric_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return symmetric_key