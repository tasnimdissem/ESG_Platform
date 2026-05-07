import sys
sys.path.insert(0, '.')
from backend.extensions import bcrypt
from backend.app import create_app
import secrets

app = create_app()
with app.app_context():
    password = 'Admin@' + secrets.token_hex(8)
    hashed = bcrypt.generate_password_hash(password)
    print(f'Mot de passe: {password}')
    print(f'Hash: {hashed.decode("utf-8")}')
