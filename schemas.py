from pydantic import BaseModel

class LinkCreate(BaseModel):
    long_url: str

class LinkResponse(BaseModel):
    short_code: str
    long_url: str

    class Config:
        from_attributes = True