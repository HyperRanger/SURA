from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.models import Commitment, CommitmentBeneficiary, CommitmentMember, Contribution, Institution, ScoreHistory, User, Vendor
from app.routers.commitments import router as commitments_router
from app.routers.score import router as score_router
from app.routers.vendors import router as vendors_router

app = FastAPI(title="Sura API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(commitments_router)
app.include_router(vendors_router)
app.include_router(score_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
