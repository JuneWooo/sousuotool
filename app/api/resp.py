# -*- coding:utf-8 -*-

from enum import Enum
from app.schemas.resp import RESPModel


class RespStatus(Enum):
    success = 200
    successTip = 201
    warning = 400
    noAuth = 403
    error = 500


def resp(
    status_code: RespStatus = RespStatus.success, msg: str = "ok", data=None
):
    if data is None:
        data = []
    return RESPModel(code=status_code.value, message=msg, result=data)
