{{config(materialized='table')}}
select o.* , 
u.name,
u.segment,
u.age_group 
from {{ref('stg_orders')}} o  
left join {{ref('stg_users')}} u 
on o.user_id = u.user_id 