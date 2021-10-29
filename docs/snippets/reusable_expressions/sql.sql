select sum(amount) as revenue,
    count(distinct user_id) as unique_paying_users,
    sum(amount) / count(distinct user_id) as arppu
from orders
