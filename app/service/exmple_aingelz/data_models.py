from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# Models for request validation: ---------------------------------

class PatientProxy(BaseModel):
    relation_to_patient: str = Field(..., example="parent")
    gender: str = Field(..., example="M")

class Patient(BaseModel):
    id: str = Field(..., example="67hy-75u6-ju56-jrygt")
    age: int = Field(..., example=13, ge=0)
    gender: str = Field(..., example="M")
    patient_proxy: Optional[PatientProxy] = None

class Service(BaseModel):
    id: str = Field(..., example="uy75-juj63-k93g-8474")
    type: str = Field(..., example="serviceline")

class DataTransmit(BaseModel):
    agent: str = Field(..., example="symptom")
    user: str = Field(..., example="cough")

class TaskData(BaseModel):
    patient: Patient
    services: List[Service]

class StartSessionRequest(BaseModel):
    task: str = Field(..., example="Service Routing")
    language: str = Field(..., example="EN")
    interactions_limit: int = Field(..., example=7, ge=1)
    task_data: TaskData
    data_transmit: DataTransmit

class SendMessageRequest(BaseModel):
    task_transaction_id: UUID = Field(..., example="550e8400-e29b-41d4-a716-446655440000")
    data_transmit: DataTransmit


# Models for response validation: ----------------------------------------

class ResponseData(BaseModel):
    agent: str = Field(..., example="I understand, and for how long have you been coughing?")

class ResponseResult(BaseModel):
    services: List[Service] = []
    status: str = Field(..., example="ongoing")

class StartSessionResponse(BaseModel):
    task_transaction_id: UUID = Field(..., example="550e8400-e29b-41d4-a716-446655440000")
    data: ResponseData
    result: ResponseResult

class SendMessageResponse(BaseModel):
    task_transaction_id: UUID = Field(..., example="550e8400-e29b-41d4-a716-446655440000")
    data: ResponseData
    result: ResponseResult
