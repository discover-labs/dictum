from typing import Literal, Optional

from pydantic import BaseModel

from nestor.store.schema.config import CalculationFormat
from nestor.store.schema.types import DimensionType


class CalculationMetadata(BaseModel):
    name: str
    kind: Literal["measure", "dimension"]
    type: Optional[DimensionType]
    format: Optional[CalculationFormat]
