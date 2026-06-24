from pydantic import BaseModel

class chatRequest(BaseModel):
    question:str