# ============================================================
# routers/usuarios.py — Endpoints para gestión de usuarios y perfil
# Ruta base: /api/usuarios
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db
from models import Usuario
from schemas import UsuarioCreate, UsuarioResponse, UsuarioUpdate, MensajeResponse
from core.security import (
    hashear_contrasena,
    verificar_contrasena,
    get_current_user,
)

router = APIRouter(prefix="/api/usuarios", tags=["Usuarios"])


@router.post(
    "",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario (Endpoint directo)",
)
def crear_usuario(payload: UsuarioCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo usuario en el sistema.
    - La contraseña se almacena con hash Bcrypt.
    - Retorna 409 si el correo ya existe.
    """
    existente = db.query(Usuario).filter(Usuario.correo == payload.correo).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El correo '{payload.correo}' ya está registrado",
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
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error de integridad al registrar el usuario",
        )

    return nuevo_usuario


@router.get(
    "/perfil",
    response_model=UsuarioResponse,
    summary="Obtener perfil del usuario autenticado",
)
def obtener_perfil(current_user: Usuario = Depends(get_current_user)):
    """Retorna los datos del usuario logueado en la sesión actual."""
    return current_user


@router.put(
    "/perfil",
    response_model=UsuarioResponse,
    summary="Actualizar perfil o cambiar contraseña",
)
def actualizar_perfil(
    payload: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Permite cambiar el nombre y/o la contraseña del usuario autenticado.
    Si se desea cambiar la contraseña, se exige la contraseña actual.
    """
    if payload.nombre:
        current_user.nombre = payload.nombre.strip()

    if payload.contrasena_nueva:
        if not payload.contrasena_actual:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debes proporcionar la contraseña actual para establecer una nueva",
            )
        if not verificar_contrasena(payload.contrasena_actual, current_user.contrasena_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña actual proporcionada es incorrecta",
            )
        if len(payload.contrasena_nueva) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La nueva contraseña debe tener al menos 8 caracteres",
            )
        current_user.contrasena_hash = hashear_contrasena(payload.contrasena_nueva)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.get(
    "/{id_usuario}",
    response_model=UsuarioResponse,
    summary="Obtener datos de un usuario por ID",
)
def obtener_usuario(
    id_usuario: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Retorna los datos de un usuario si corresponde al usuario autenticado."""
    if current_user.id_usuario != id_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para consultar la información de este usuario",
        )
    return current_user
