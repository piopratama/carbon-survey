from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.sentinel import router as sentinel_router
from app.api.context import router as context_router
from app.api.survey import router as survey_router
from app.api.project import router as project_router
from app.api.sampling import router as sampling_router
from app.api.user import router as user_router
from app.api.tree_species import router as tree_species_router
from app.api.upload import router as upload_router
from app.api.auth import router as auth_router

app = FastAPI(title="Sentinel Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health():
    return {"status": "ok"}

# ===== API PREFIX DI SINI =====
app.include_router(context_router, prefix="/api")
app.include_router(sentinel_router, prefix="/api")
app.include_router(survey_router, prefix="/api")
app.include_router(project_router, prefix="/api")
app.include_router(sampling_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(tree_species_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(auth_router, prefix="/api")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")