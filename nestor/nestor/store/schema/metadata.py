from typing import Literal, Optional

from pydantic import BaseModel

from nestor.store.schema.types import CalculationType


class CalculationMetadata(BaseModel):
    name: str
    kind: Literal["measure", "dimension"]
    type: Optional[CalculationType]
