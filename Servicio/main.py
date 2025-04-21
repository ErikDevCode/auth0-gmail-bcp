# main.py
from fastapi import FastAPI
import os
from routes.consumo import router as consumo_router
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel, OAuth2 as OAuth2Model
from fastapi.security import OAuth2
from fastapi.openapi.utils import get_openapi
from dotenv import load_dotenv

load_dotenv()

class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(self):
        flows = OAuthFlowsModel(authorizationCode={
            "authorizationUrl": f"https://{os.getenv('AUTH0_DOMAIN')}/authorize",
            "tokenUrl": f"https://{os.getenv('AUTH0_DOMAIN')}/oauth/token",
            "scopes": {
                "openid": "OpenID Connect",
                "profile": "User profile",
                "email": "User email"
            }
        })
        super().__init__(flows=flows)

oauth2_scheme = OAuth2PasswordBearerWithCookie()

# Instancia de la aplicación
app = FastAPI(
    title="Servicio de Consumos Gmail + Auth0",
    description="API protegida con Auth0 que extrae consumos desde correos Gmail (BCP)",
    version="1.0.0",
    openapi_tags=[{"name": "Consumos", "description": "Extracción de datos de Gmail"}]
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Servicio de Consumos Gmail + Auth0",
        version="1.0.0",
        description="API protegida con Auth0 que extrae consumos desde correos Gmail (BCP)",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    # Aplica Bearer por defecto en todos los endpoints
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return openapi_schema

app.openapi = custom_openapi

from routes.auth_login import router as auth_login_router
app.include_router(auth_login_router, prefix="/api", tags=["Auth"])

from routes.login import router as auth_router
app.include_router(auth_router, prefix="/api", tags=["Login"])

from routes.user import router as user_router
app.include_router(user_router, prefix="/api", tags=["Usuario"])

# Registrar rutas
app.include_router(consumo_router, prefix="/api", tags=["Consumos"])



