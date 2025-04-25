from fastapi import APIRouter, Request
from models.consumo_model import Consumo
from services.gmail_services import extraer_consumos_desde_gmail
from auth import requires_auth
from typing import List

router = APIRouter()

@router.get("/consumos", response_model=List[Consumo])
@requires_auth
async def obtener_consumos(request: Request):
    user = request.state.user
    email = user["email"]
    print("Usuario autenticado:", email)
    return await extraer_consumos_desde_gmail(email)
