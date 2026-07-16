select 
"email" as email,
"is_verified" as is_verified,
"name" as name,
"segment" as segment,
"signup_date" as signup_date,
"user_id" as user_id,
"age_group" as age_group,
"account_age_days" as account_age_days,
"signup_year" as signup_year,
"signup_month" as signup_month
 from {{ source('raw','users')}}