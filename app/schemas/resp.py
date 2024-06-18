from typing import Generic, TypeVar

from pydantic import BaseModel


DataT = TypeVar("DataT")  # 定义泛型


class RESPModel(BaseModel, Generic[DataT]):
    code: int
    message: str
    result: DataT
