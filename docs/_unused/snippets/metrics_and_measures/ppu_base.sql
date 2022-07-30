select date_trunc('month', started_at) as "date",
    count(distinct user_id) as unique_active_users
from user_sessions
group by 1;

select date_trunc('month', created_at) as "date",
    count(distinct user_id) as unique_paying_users
from orders
group by 1;
