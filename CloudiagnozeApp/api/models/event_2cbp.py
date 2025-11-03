# from pydantic import BaseModel, Field, validator
# from typing import Any, Union
# from datetime import datetime
# import json
# import pytz

# class Event2CBP(BaseModel):
#     """
#     Modèle d'événement selon le protocole 2CBP
#     Chaque information devient un événement atomique
#     """
#     client_id: str = Field(..., description="Identifiant du client")
#     timestamp: str = Field(..., description="Timestamp ISO 8601")
#     resource_id: str = Field(..., description="Identifiant unique de la ressource (ARN de préférence)")
#     metric_type: str = Field(..., description="Type de métrique (fournisseur.categorie.service.detail_metrique)")
#     metric_value: Union[int, float, str, bool, dict, list] = Field(..., description="Valeur de la métrique")
    
#     @validator('timestamp')
#     def validate_timestamp(cls, v):
#         """Valide le format ISO 8601"""
#         try:
#             datetime.fromisoformat(v.replace('Z', '+00:00'))
#             return v
#         except ValueError:
#             raise ValueError('timestamp doit être au format ISO 8601')
    
#     @validator('metric_type')
#     def validate_metric_type(cls, v):
#         """Valide la nomenclature fournisseur.categorie.service.detail_metrique"""
#         parts = v.split('.')
#         if len(parts) < 4:
#             raise ValueError('metric_type doit suivre le format: fournisseur.categorie.service.detail_metrique')
#         return v
    
#     @classmethod
#     def create_event(cls, client_id: str, resource_id: str, metric_type: str, metric_value: Any):
#         """Factory method avec timezone Paris"""
#         paris_tz = pytz.timezone('Europe/Paris')
#         paris_time = datetime.now(paris_tz)
        
#         return cls(
#             client_id=client_id,
#             timestamp=paris_time.isoformat(),
#             resource_id=resource_id,
#             metric_type=metric_type,
#             metric_value=metric_value
#         )
    
#     def to_json(self) -> str:
#         """Convertit l'événement en JSON pour envoi"""
#         return self.model_dump_json()
    
#     class Config:
#         json_encoders = {
#             datetime: lambda v: v.isoformat() + 'Z'
#         }


from pydantic import BaseModel, Field, field_validator
from typing import Any, Union
from datetime import datetime
import json
import pytz

class Event2CBP(BaseModel):
    """
    Modèle d'événement selon le protocole 2CBP
    Chaque information devient un événement atomique
    """
    client_id: str = Field(..., description="Identifiant du client")
    timestamp: str = Field(..., description="Timestamp ISO 8601")
    resource_id: str = Field(..., description="Identifiant unique de la ressource (ARN de préférence)")
    metric_type: str = Field(..., description="Type de métrique (fournisseur.categorie.service.detail_metrique)")
    metric_value: Union[int, float, str, bool, dict, list] = Field(..., description="Valeur de la métrique")
    
    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v):
        """Valide le format ISO 8601"""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError('timestamp doit être au format ISO 8601')
    
    @field_validator('metric_type')
    @classmethod
    def validate_metric_type(cls, v):
        """Valide la nomenclature fournisseur.categorie.service.detail_metrique"""
        parts = v.split('.')
        if len(parts) < 4:
            raise ValueError('metric_type doit suivre le format: fournisseur.categorie.service.detail_metrique')
        return v
    
    @classmethod
    def create_event(cls, client_id: str, resource_id: str, metric_type: str, metric_value: Any):
        """Factory method avec timezone Paris"""
        paris_tz = pytz.timezone('Europe/Paris')
        paris_time = datetime.now(paris_tz)
        
        return cls(
            client_id=client_id,
            timestamp=paris_time.isoformat(),
            resource_id=resource_id,
            metric_type=metric_type,
            metric_value=metric_value
        )
    
    def to_json(self) -> str:
        """Convertit l'événement en JSON pour envoi"""
        return self.model_dump_json()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z'
        }