import uuid
import json
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_admin, get_current_user
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserRead
from app.worker import get_queue

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/ping")
def update_user_status(
    action: str = Query("idle"),
    current_user=Depends(get_current_user)
) -> dict:
    r = get_queue().connection
    data = {
        "username": current_user.username,
        "is_admin": current_user.is_admin,
        "action": action,
        "last_seen": int(time.time())
    }
    r.hset("online_users", current_user.id, json.dumps(data))
    return {"status": "ok"}


@router.get("/online-users", dependencies=[Depends(get_current_active_admin)])
def get_online_users() -> list[dict]:
    r = get_queue().connection
    users_data = r.hgetall("online_users")
    
    online = []
    now = int(time.time())
    for uid, ujson in users_data.items():
        try:
            udict = json.loads(ujson)
            # consider offline if not seen in 15 seconds
            if now - udict.get("last_seen", 0) < 15:
                online.append(udict)
            else:
                # Cleanup stale
                r.hdel("online_users", uid)
        except:
            pass
            
    # sort by username
    online.sort(key=lambda x: x["username"])
    return online

@router.post("/register", response_model=UserRead, dependencies=[Depends(get_current_active_admin)])
def register_user(user_in: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    user_exists = db.query(User).filter(User.username == user_in.username).first()
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    new_user = User(
        id=uuid.uuid4().hex,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        is_admin=False,  # You can extend this logic if you want to create more admins
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=Token)
def login_user(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Token:
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token = create_access_token(subject=user.id)
    
    return Token(
        access_token=access_token,
        user=user
    )
