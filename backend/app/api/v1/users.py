"""用户管理接口（含权限控制）。"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DbDep, get_current_admin, get_current_user
from app.models.user import User
from app.schemas.auth import UpdateUserStatus, UserOut

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("/me", response_model=UserOut, summary="获取当前用户信息")
def read_me(current_user: User = Depends(get_current_user)) -> User:
    """返回当前登录用户的信息。"""
    return current_user


@router.get("", response_model=list[UserOut], summary="用户列表（管理员）")
def list_users(
    db: DbDep, _: User = Depends(get_current_admin)
) -> list[User]:
    """管理员查看全部用户。"""
    return db.query(User).order_by(User.id).all()


@router.patch(
    "/{user_id}/status",
    response_model=UserOut,
    summary="启用/禁用用户（管理员）",
)
def update_user_status(
    user_id: int,
    payload: UpdateUserStatus,
    db: DbDep,
    _: User = Depends(get_current_admin),
) -> User:
    """管理员设置用户状态：1 启用、0 禁用。"""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
        )
    user.status = payload.status
    db.commit()
    db.refresh(user)
    return user
