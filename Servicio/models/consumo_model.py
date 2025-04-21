# models/consumo_model.py
from pydantic import BaseModel
from datetime import datetime

class Consumo(BaseModel):
    fecha: datetime
    empresa: str
    monto: float
    numero_operacion: str
    tipo: str
    categoria: str
    periodo: str
