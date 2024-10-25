# create_keypair.py

import argparse
import sys
from tools import save_private_key, save_public_key, generate_rsa_key_pair

def main():
    # 명령줄 인자 파싱 설정
    parser = argparse.ArgumentParser(description="Generate RSA key pair for a user.")
    parser.add_argument("user_id", help="User ID for which to generate the key pair.")
    
    args = parser.parse_args()
    
    user_id = args.user_id
    
    # user_id 검증 (선택 사항)
    if not user_id.isalnum():
        print("Error: user_id must be an alphanumeric string.")
        sys.exit(1)
    
    # 키 페어 생성
    private_key_file = f'private_key_{user_id}.pem'
    public_key_file = f'public_key_{user_id}.pem'
    
    private_key, public_key = generate_rsa_key_pair()
    
    # 키 저장
    save_private_key(private_key, private_key_file)
    print(f"Private key saved to {private_key_file}.")
    
    save_public_key(public_key, public_key_file)
    print(f"Public key saved to {public_key_file}.")

if __name__ == "__main__":
    main()
