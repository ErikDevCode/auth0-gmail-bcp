from fastapi import APIRouter, Request, Query, HTTPException
import httpx
import os
from services.auth0_services import validar_usuario_auth0

router = APIRouter()

@router.get("/login")
async def login(code: str = Query(..., description="Authorization code")):
    token_url = f"https://{os.getenv('AUTH0_DOMAIN')}/oauth/token"
    client_id = os.getenv("AUTH0_CLIENT_ID")
    client_secret = os.getenv("AUTH0_CLIENT_SECRET")
    redirect_uri = os.getenv("APP_LOGIN_URL")

    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
        token_data = response.json()

        if "error" in token_data:
            raise HTTPException(status_code=400, detail=token_data.get("error_description", "Error en la autenticación"))

        id_token = token_data.get("id_token")

        # Validar existencia del usuario en Auth0
        existe = await validar_usuario_auth0(id_token)
        if not existe:
            raise HTTPException(status_code=403, detail="El usuario no está registrado en Auth0")

        return {
            "access_token": token_data.get("id_token"),
            "expires_in": token_data.get("expires_in")
        }
