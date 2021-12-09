from babel.numbers import list_currencies

currencies = set(list_currencies())


def set_ids(data: dict):
    for k, v in data.items():
        v["id"] = k
    return data
