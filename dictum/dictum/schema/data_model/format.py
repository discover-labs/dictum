from typing import Literal, Optional, Union

from pydantic import BaseModel, root_validator

from dictum.schema import utils

FormatKind = Literal["number", "decimal", "percent", "currency", "date", "datetime"]


class FormatConfig(BaseModel):
    kind: FormatKind
    pattern: Optional[str]
    currency: Optional[str]

    @root_validator(skip_on_failure=True)
    def validate_currency(cls, values):
        if values["kind"] != "currency":
            if values.get("currency") is not None:
                raise ValueError(
                    "'currency' format option is only valid with 'currency' format kind"
                )
            return values
        if values.get("currency") is None:
            raise ValueError(
                "'currency' formatting option is required if format kind is 'currency'"
            )
        if values["currency"] not in utils.currencies:
            raise ValueError(f"{values['currency']} is not a supported currency")
        return values


Format = Union[FormatKind, FormatConfig]
