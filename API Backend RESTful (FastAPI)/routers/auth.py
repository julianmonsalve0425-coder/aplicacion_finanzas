# ============================================================
# routers/auth.py — Endpoints de Autenticación y Autorización JWT
# Rutas: /api/auth/register, /api/auth/login, /api/auth/refresh, /api/auth/me
# ============================================================

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db
from models import Usuario, Categoria
from schemas import (
    UsuarioCreate,
    UsuarioResponse,
    Token,
    TokenRefreshRequest,
    LoginRequest,
)
from core.security import (
    hashear_contrasena,
    verificar_contrasena,
    crear_access_token,
    crear_refresh_token,
    decodificar_token,
    get_current_user,
)

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])


def _generar_tokens_usuario(usuario: Usuario) -> Token:
    """Genera access_token y refresh_token para el usuario dado."""
    token_data = {
        "sub": usuario.correo,
        "id_usuario": usuario.id_usuario,
        "nombre": usuario.nombre,
    }
    access_token = crear_access_token(data=token_data)
    refresh_token = crear_refresh_token(data=token_data)
    return Token(
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token,
        usuario=UsuarioResponse.model_validate(usuario),
    )


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una nueva cuenta de usuario",
)
def register(payload: UsuarioCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo usuario en la plataforma:
    - Valida que el correo no esté registrado previamente.
    - Hashea la contraseña con Bcrypt.
    - Crea categorías por defecto (Salario, Alimentación, Transporte, etc.).
    - Retorna el token JWT listo para iniciar sesión.
    """
    existente = db.query(Usuario).filter(Usuario.correo == payload.correo).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El correo electrónico '{payload.correo}' ya está registrado.",
        )

    nuevo_usuario = Usuario(
        nombre=payload.nombre,
        correo=payload.correo,
        contrasena_hash=hashear_contrasena(payload.contrasena),
        is_active=True,
    )

    try:
        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)

        # Crear categorías iniciales por defecto para el usuario nuevo
        categorias_base = [
            ("Salario", "ingreso"),
            ("Honorarios / Freelance", "ingreso"),
            ("Alimentación", "gasto"),
            ("Transporte", "gasto"),
            ("Vivienda y Servicios", "gasto"),
            ("Entretenimiento", "gasto"),
            ("Salud", "gasto"),
        ]
        for nombre_cat, tipo_cat in categorias_base:
            cat = Categoria(nombre=nombre_cat, tipo=tipo_cat, id_usuario=nuevo_usuario.id_usuario)
            db.add(cat)
        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error al registrar el usuario en la base de datos.",
        )

    return _generar_tokens_usuario(nuevo_usuario)


@router.post(
    "/login",
    response_model=Token,
    summary="Iniciar sesión con credenciales OAuth2 (Form Data)",
)
def login_oauth(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Endpoint de login estándar compatible con OAuth2 / Swagger UI.
    Recibe `username` (correo) y `password`.
    """
    usuario = db.query(Usuario).filter(Usuario.correo == form_data.username).first()
    if not usuario or not verificar_contrasena(form_data.password, usuario.contrasena_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not usuario.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta de usuario está inactiva o bloqueada",
        )

    return _generar_tokens_usuario(usuario)


@router.post(
    "/login-json",
    response_model=Token,
    summary="Iniciar sesión con JSON Body",
)
def login_json(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Endpoint alternativo de login para clientes JavaScript / SPA usando JSON.
    """
    usuario = db.query(Usuario).filter(Usuario.correo == payload.correo).first()
    if not usuario or not verificar_contrasena(payload.contrasena, usuario.contrasena_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not usuario.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta de usuario está inactiva o bloqueada",
        )

    return _generar_tokens_usuario(usuario)


@router.post(
    "/refresh",
    response_model=Token,
    summary="Renovar access token usando refresh token",
)
def refresh_token(
    payload: TokenRefreshRequest,
    db: Session = Depends(get_db),
):
    """
    Valida un refresh token JWT válido y emite un nuevo access token.
    """
    token_payload = decodificar_token(payload.refresh_token, expected_type="refresh")
    id_usuario = token_payload.get("id_usuario")

    if not id_usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario or not usuario.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no válido o inactivo",
        )

    return _generar_tokens_usuario(usuario)


@router.get(
    "/me",
    response_model=UsuarioResponse,
    summary="Obtener perfil del usuario autenticado",
)
def get_me(current_user: Usuario = Depends(get_current_user)):
    """Retorna los datos del usuario actualmente autenticado mediante JWT."""
    return current_user
