from fastapi import FastAPI

app = FastAPI(
    title="BreastAI API",
    version="0.1.0",
)


@app.get("/")
def read_root() -> dict:
    return {
        "project": "BreastAI",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
def health_check() -> dict:
    return {
        "status": "healthy",
    }
