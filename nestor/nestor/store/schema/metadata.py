from typing import Dict, Optional

from pydantic import BaseModel


class CalculationMetadata(BaseModel):
    name: str
    format: Optional[str]  # d3-format
    locale_patch: Optional[Dict]  # patches current locale, used for currencies
