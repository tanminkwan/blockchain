from tools import derive_key_from_password, save_private_key, save_public_key, generate_rsa_key_pair

# 사용자 정보
user_id = 'badgirl'

# 키 페어 생성
private_key_file = f'private_key_{user_id}.pem'
public_key_file = f'public_key_{user_id}.pem'

private_key, public_key = generate_rsa_key_pair()
save_private_key(private_key, private_key_file)
save_public_key(public_key, public_key_file)