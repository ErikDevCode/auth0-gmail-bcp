import httpx
import os
from jose import jwt

async def validar_usuario_auth0(id_token: str) -> bool:
    # Decodificar el ID Token para extraer el email
    decoded = jwt.get_unverified_claims(id_token)
    email = decoded.get("email")
    
    if not email:
        return False

    # Usar token de la Management API de Auth0
    domain = os.getenv("AUTH0_DOMAIN")
    mgmt_token_url = f"https://{domain}/oauth/token"
    
    mgmt_data = {
        "grant_type": "client_credentials",
        "client_id": os.getenv("AUTH0_MGMT_CLIENT_ID"),
        "client_secret": os.getenv("AUTH0_MGMT_CLIENT_SECRET"),
        "audience": f"https://{domain}/api/v2/"
    }

    async with httpx.AsyncClient() as client:
        mgmt_token_resp = await client.post(mgmt_token_url, json=mgmt_data)
        mgmt_token = mgmt_token_resp.json().get("access_token")

        # Consultar si el usuario existe
        headers = {"Authorization": f"Bearer {mgmt_token}"}
        users_url = f"https://{domain}/api/v2/users-by-email?email={email}"

        user_resp = await client.get(users_url, headers=headers)
        users = user_resp.json()

        return len(users) > 0

async def verificar_existencia_usuario(email: str) -> bool:
    domain = os.getenv("AUTH0_DOMAIN")
    mgmt_client_id = os.getenv("AUTH0_MGMT_CLIENT_ID")
    mgmt_client_secret = os.getenv("AUTH0_MGMT_CLIENT_SECRET")

    # Obtener token de management
    data = {
        "grant_type": "client_credentials",
        "client_id": mgmt_client_id,
        "client_secret": mgmt_client_secret,
        "audience": f"https://{domain}/api/v2/"
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"https://{domain}/oauth/token", json=data)
        access_token = resp.json().get("access_token")
        if not access_token:
            return False

        headers = {"Authorization": f"Bearer {access_token}"}
        users_url = f"https://{domain}/api/v2/users-by-email?email={email}"

        user_resp = await client.get(users_url, headers=headers)
        users = user_resp.json()

        return isinstance(users, list) and len(users) > 0