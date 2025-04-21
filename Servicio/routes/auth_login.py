# routes/auth.py
from fastapi.responses import RedirectResponse
import os
from fastapi import APIRouter, HTTPException, Query
import httpx
from urllib.parse import urlencode
import webbrowser
from services.auth0_services import verificar_existencia_usuario

router = APIRouter()

@router.get("/auth-login")
async def auth_login(email: str = Query(...)):
    existe = await verificar_existencia_usuario(email)
    
    if not existe:
        raise HTTPException(status_code=404, detail="El usuario no está registrado")

    domain = os.getenv("AUTH0_DOMAIN")
    client_id = os.getenv("AUTH0_CLIENT_ID")
    redirect_uri = os.getenv("APP_LOGIN_URL")

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "openid profile email",
        "login_hint": email,
        "prompt": "login"  # Forzar login aunque tenga sesión
    }

    auth_url = f"https://{domain}/authorize?{urlencode(params)}"
    webbrowser.open(auth_url)
    return {"auth_url": auth_url}