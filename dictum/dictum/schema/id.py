reserved = {
    "Time",
    "Year",
    "Quarter",
    "Month",
    "Week",
    "Day",
    "Date",
    "Hour",
    "Minute",
    "Second",
}


class ID(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value: str):
        if not isinstance(value, str):
            raise TypeError(f"Invalid object ID: {value}. Object ID must be a string.")
        if not value.isidentifier():
            raise ValueError(
                f"Invalid object ID: {value}. "
                "Object ID must be a valid Python identifier."
            )
        if value.startswith("__"):
            raise ValueError(
                f"Invalid object ID: {value}. "
                "IDs starting with double underscore (__) "
                "are reserved for internal use."
            )
        if value in reserved:
            raise ValueError(
                f"Invalid object ID: {value}. IDs {reserved} are reserved."
            )
        return cls(value)
