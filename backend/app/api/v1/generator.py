"""测试数据生成器接口。"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DbDep, get_current_user
from app.models.user import User
from app.schemas.generator import TestDataRequest, TestDataResponse
from app.services.test_data_generator import generate_test_data

router = APIRouter(prefix="/generator", tags=["测试数据生成器"])

CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post(
    "/test-data",
    response_model=TestDataResponse,
    summary="生成测试数据（自动识别字段类型）",
)
def generate(data: TestDataRequest, _: CurrentUser = None) -> TestDataResponse:
    """根据字段名称自动识别类型并生成 10 类测试数据。"""
    try:
        result = generate_test_data(data.field, data.type, data.count)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return TestDataResponse(**result)
