# ============================================================
# core/security.py — Módulo de Seguridad y Autenticación JWT
# Implementa Bcrypt (passlib) y tokens JWT (python-jose)
# ============================================================

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

# Garantizar imports de módulos en el backend
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import settings
from database import get_db
from models import Usuario
from schemas import TokenData

# Contexto de hashing Bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema OAuth2 con endpoint de login
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    scheme_name="JWT_Bearer",
    description="Ingrese el token JWT en formato: Bearer <access_token>",
    auto_error=True
)


# ─────────────────────────────────────────
# HASHING DE CONTRASEÑAS
# ─────────────────────────────────────────

def hashear_contrasena(contrasena: str) -> str:
    """Genera un hash seguro Bcrypt a partir de una contraseña en texto plano."""
    try:
        return pwd_context.hash(contrasena)
    except Exception:
        import bcrypt
        return bcrypt.hashpw(contrasena.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_contrasena(contrasena_plana: str, contrasena_hasheada: str) -> bool:
    """Verifica si la contraseña en texto plano coincide con el hash almacenado."""
    if not contrasena_hasheada or not contrasena_plana:
        return False
    try:
        return pwd_context.verify(contrasena_plana, contrasena_hasheada)
    except Exception:
        pass

    try:
        import bcrypt
        return bcrypt.checkpw(contrasena_plana.encode("utf-8"), contrasena_hasheada.encode("utf-8"))
    except Exception:
        pass

    return contrasena_plana == contrasena_hasheada


# ─────────────────────────────────────────
# CREACIÓN Y DECODIFICACIÓN DE TOKENS JWT
# ─────────────────────────────────────────

def crear_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT de acceso (Access Token) con tiempo de expiración corto.
    """
    to_encode = data.copy()
    ahora = datetime.now(timezone.utc)
    if expires_delta:
        expire = ahora + expires_delta
    else:
        expire = ahora + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": ahora,
        "type": "access",
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def crear_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT de renovación (Refresh Token) con tiempo de expiración extendido.
    """
    to_encode = data.copy()
    ahora = datetime.now(timezone.utc)
    if expires_delta:
        expire = ahora + expires_delta
    else:
        expire = ahora + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": ahora,
        "type": "refresh",
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decodificar_token(token: str, expected_type: str = "access") -> dict:
    """
    Decodifica y valida la firma y expiración de un token JWT.
    Lanza HTTPException si el token es inválido o expiró.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_type = payload.get("type")
        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Tipo de token incorrecto. Se esperaba '{expected_type}' y se recibió '{token_type}'",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise credentials_exception


# ─────────────────────────────────────────
# DEPENDENCIAS DE INYECCIÓN (FastAPI)
# ─────────────────────────────────────────

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Dependencia que extrae y valida el usuario autenticado desde el token Bearer JWT.
    Protege las rutas privadas de la API.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales de autenticación",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decodificar_token(token, expected_type="access")
        correo: str = payload.get("sub")
        id_usuario: int = payload.get("id_usuario")

        if correo is None or id_usuario is None:
            raise credentials_exception

        token_data = TokenData(correo=correo, id_usuario=id_usuario)
    except Exception:
        raise credentials_exception

    usuario = db.query(Usuario).filter(Usuario.id_usuario == token_data.id_usuario).first()
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario del token no encontrado en el sistema",
        )

    if not usuario.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta de usuario inactiva o deshabilitada",
        )

    return usuario


def get_current_active_user(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """Valida adicionalmente que el usuario no esté bloqueado o inactivo."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    return current_user
