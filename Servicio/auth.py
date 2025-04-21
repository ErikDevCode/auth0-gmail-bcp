# auth.py
import os
import jwt
import requests
from fastapi import Request, HTTPException
from functools import wraps
from dotenv import load_dotenv
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64

load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
API_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
ALGORITHMS = ["RS256"]

# Obtener las llaves públicas de Auth0
jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
jwks_response = requests.get(jwks_url)

if jwks_response.status_code != 200:
    raise Exception("No se pudo obtener las JWKS de Auth0")

jwks = jwks_response.json()

def get_token_auth_header(request: Request) -> str:
    auth = request.headers.get("Authorization")
    if not auth:
        raise HTTPException(status_code=401, detail="Falta el encabezado Authorization")

    parts = auth.split()
    if parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="El encabezado debe ser un token Bearer")
    elif len(parts) == 1:
        raise HTTPException(status_code=401, detail="Token no encontrado")
    elif len(parts) > 2:
        raise HTTPException(status_code=401, detail="Encabezado malformado")

    return parts[1]

def pad_base64(b64_string):
    return b64_string + '=' * (-len(b64_string) % 4)


def decode_jwt_token(token: str):
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header.get("kid"):
            n = int.from_bytes(base64.urlsafe_b64decode(pad_base64(key["n"])), "big")
            e = int.from_bytes(base64.urlsafe_b64decode(pad_base64(key["e"])), "big")
            public_key = rsa.RSAPublicNumbers(e, n).public_key(default_backend())
            break
    else:
        raise HTTPException(status_code=401, detail="No se encontró la clave adecuada")

    try:
        payload = jwt.decode(
            token,
            key=public_key,
            algorithms=ALGORITHMS,
            audience=CLIENT_ID,
            issuer=f"https://{AUTH0_DOMAIN}/"
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidAudienceError:
        raise HTTPException(status_code=401, detail="Audiencia inválida")
    except jwt.InvalidIssuerError:
        raise HTTPException(status_code=401, detail="Issuer inválido")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"No se pudo validar el token: {str(e)}")


def requires_auth(endpoint):
    @wraps(endpoint)
    async def wrapper(request: Request, *args, **kwargs):
        token = get_token_auth_header(request)
        payload = decode_jwt_token(token)
        request.state.user = payload
        return await endpoint(request, *args, **kwargs)

    return wrapper