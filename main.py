from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from database import init_database
from api.route import router
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse



# ─── Lifespan: runs on startup ───
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting Hotel Management AI Agent...")
    init_database()
    print("✅ Database initialized!")
    yield
    print("👋 Shutting down...") 


# ─── Create FastAPI App ───
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# ─── CORS (allow frontend access) ───
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes ───
app.include_router(router, prefix="/api/v1", tags=["Hotel Management"])
app.mount("/static", StaticFiles(directory="."), name="static")


# ─── Health Check ───
@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "✅ Running"
    }


@app.get("/frontend")
def serve_frontend():
    return FileResponse("index.html")


@app.get("/health")
def health():
    return {"status": "healthy"}


# ─── Run directly ───
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.debug) 
