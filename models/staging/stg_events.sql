select 
"device" as device,
"event_id" as event_id,
"event_type" as event_type,
"order_id" as order_id,
"product_id" as product_id,
"session_id" as session_id,
"timestamp" as timestamp,
"user_id" as user_id,
"date" as date,
"hour" as hour,
"is_purchase" as is_purchase,
"has_product" as has_product,
"year" as year,
"month" as month
from {{source('raw', 'events')}}