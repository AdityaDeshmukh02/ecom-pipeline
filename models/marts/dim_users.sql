{{ config(materialized='table') }}
with order_agg as 
(
    select user_id ,
count(order_id) as lifetime_order_count,
sum(order_total) as total_spend,
min(created_at) as first_order_date,
max(created_at) as last_order_date
from {{ref('stg_orders')}}
group by user_id 
)

select 
u.user_id,
u.name,
u.email,
u.segment,
u.age_group,
u.signup_date,
u.is_verified,
coalesce(oa.lifetime_order_count, 0) as lifetime_order_count,
coalesce(oa.total_spend, 0) as total_spend,
oa.first_order_date,
oa.last_order_date,
case when oa.total_spend > 5000 then true else false end as is_high_value_user
from {{ref('stg_users')}} u 
left join order_agg oa 
on u.user_id = oa.user_id 