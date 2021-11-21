from pathlib import Path

import numpy as np
import pandas as pd
from numpy.random import Generator

from dictum import CachedProject

rng = np.random.default_rng(42)


def generate_random_dates(rng: Generator, start, end, n: int) -> pd.Series:
    s = start.value // 10 ** 9
    e = end.value // 10 ** 9
    return pd.to_datetime(rng.integers(s, e, n), unit="s")


categories = [
    "Kebab",
    "Skiing",
    "Wombat Thoughts",
    "Genetic Dynasty",
    "Gas Giant Trivia",
]
channels = [
    "Mastodon Ads",
    "Silkroad Spam",
    "[Object object]",
    "Imaginary Voices",
    "Word of Mouth",
]

n_orders = 19298
n_users = int(n_orders * 0.79)
n_sessions = int(n_orders * 6.8)


def generate_orders(rng: Generator):

    channels_p = np.random.lognormal(size=len(channels))
    channels_p = channels_p / channels_p.sum()

    categories_p = np.random.lognormal(size=len(categories))
    categories_p = categories_p / categories_p.sum()

    users_p = np.random.lognormal(size=n_users)
    users_p = users_p / users_p.sum()

    created_at = generate_random_dates(
        rng, pd.to_datetime("2019-04-12"), pd.to_datetime("2022-03-08"), n_orders
    ).sort_values()
    return pd.DataFrame(
        {
            "id": range(n_orders),
            "created_at": created_at,
            "amount": np.round(rng.lognormal(5, 1, n_orders), 2),
            "channel": rng.choice(channels, n_orders, p=channels_p),
            "category_id": rng.choice(
                list(range(len(categories))), n_orders, p=categories_p
            ),
            "user_id": rng.choice(list(range(n_users)), n_orders, p=users_p),
        }
    )


def generate_categories():
    return pd.DataFrame({"id": range(len(categories)), "name": categories})


def generate_users(rng: Generator):
    channels_p = np.random.lognormal(size=len(channels))
    channels_p = channels_p / channels_p.sum()
    created_at = generate_random_dates(
        rng, pd.to_datetime("2019-03-31"), pd.to_datetime("2022-03-08"), n_users
    ).sort_values()
    return pd.DataFrame(
        {
            "id": range(n_users),
            "created_at": created_at,
            "channel": rng.choice(channels, n_users, p=channels_p),
        }
    )


def generate_sessions(rng: Generator):
    users_p = np.random.lognormal(size=n_users)
    users_p = users_p / users_p.sum()
    starated_at = generate_random_dates(
        rng, pd.to_datetime("2019-03-31"), pd.to_datetime("2022-03-08"), n_sessions
    ).sort_values()
    return pd.DataFrame(
        {
            "id": range(n_sessions),
            "started_at": starated_at,
            "user_id": rng.choice(list(range(n_users)), n_sessions, p=users_p),
        }
    )


def generate():
    base = Path(__file__).parent
    path = base / "project.yml"
    project = CachedProject(path)

    # generate random data
    rng = np.random.default_rng(42)

    with project.connection.engine.connect() as conn:
        generate_orders(rng).to_sql("orders", conn)
        generate_categories().to_sql("categories", conn)
        generate_users(rng).to_sql("users", conn)
        generate_sessions(rng).to_sql("user_sessions", conn)

    return project
