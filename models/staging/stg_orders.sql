select 
    "order_id" as order_id,
    "user_id" as user_id,
    "status" as status,
    "order_total" as order_total,
    "num_items" as num_items,
    "payment_method" as payment_method,
    "created_at" as created_at,
    "updated_at" as updated_at,
    "is_high_value" as is_high_value,
    "order_size" as order_size,
    "is_completed" as is_completed,
    "year" as year,
    "month" as month
from {{ source('raw', 'orders') }}