from typing import Optional

from pydantic import BaseModel
# from pydantic import HttpUrl


class SearchData(BaseModel):
    content: Optional[str] = None
    metadata: Optional[dict] = None
