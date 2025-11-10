from fastapi import FastAPI
from ..core.config import settings
from .api.v1.endpoints import fines, defenses

app = FastAPI(title=settings.APP_NAME)

app.include_router(fines.router, prefix="/api/v1", tags=["fines"])
app.include_router(defenses.router, prefix="/api/v1", tags=["defenses"])

@app.get("/")
async def root():
    """
    Root endpoint for the API.
    """
    return {"message": f"Welcome to {settings.APP_NAME}"}
