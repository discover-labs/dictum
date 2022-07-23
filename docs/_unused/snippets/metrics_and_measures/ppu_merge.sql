select coalesce(sessions_measures."date", orders_measures."date") as "date",
    sessions_measures.unique_active_users as unique_active_users,
    orders.unique_paying_users / sessions_measures.unique_active_users as ppu
from (
    ...
) as sessions_measures
full outer join (
    ...
) as orders_measures
    on sessions_measures."date" = orders_measures."date"
