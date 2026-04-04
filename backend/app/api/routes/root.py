from fastapi import APIRouter


router = APIRouter(tags=["root"])


@router.get("/")
def read_root() -> dict[str, object]:
    return {
        "name": "Bambam Converter Suite Web API",
        "phase": "phase-1",
        "services": ["api", "worker", "redis", "frontend"],
    }
