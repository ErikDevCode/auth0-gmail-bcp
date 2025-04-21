# routes/user.py
from fastapi import APIRouter, Request, Query, HTTPException
from auth import requires_auth
import os
from urllib.parse import urlencode
import webbrowser
from services.auth0_services import verificar_existencia_usuario

router = APIRouter()

@router.get("/me")
@requires_auth
async def get_me(request: Request):
    user = request.state.user
    return {
        "email": user.get("email"),
        "name": user.get("name"),
        "picture": user.get("picture")
    }

@router.get("/register")
async def registrar_con_gmail(email: str = Query(...)):
    # Verificar si ya está registrado
    existe = await verificar_existencia_usuario(email)
    if existe:
        raise HTTPException(status_code=409, detail="El usuario ya está registrado en Auth0")

    domain = os.getenv("AUTH0_DOMAIN")
    client_id = os.getenv("AUTH0_CLIENT_ID")
    redirect_uri = os.getenv("APP_LOGIN_URL")

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "openid profile email",
        "login_hint": email,
        "prompt": "login"
    }

    auth_url = f"https://{domain}/authorize?{urlencode(params)}"
    webbrowser.open(auth_url)
    return {"auth_url": auth_url}