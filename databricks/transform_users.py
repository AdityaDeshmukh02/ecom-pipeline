
# This script is designed to run on Databricks.
# On Databricks, 'spark' is provided automatically.
# To run locally, initialise SparkSession manually.

USERS_PATH = "/Volumes/workspace/default/raw_data/users.json"

users_df = spark.read \
    .option("multiline","true") \
    .json(USERS_PATH)

users_df.printSchema()
users_df.show(5, vertical=True, truncate=False)

#----------------------------------------------------------------------------------------------------
#To check data quality, we will check for null values and duplicates in the data. We will also check the data types of the columns to ensure they are correct.


from pyspark.sql import functions as F

null_counts = users_df.select([F.count(F.when(F.col(c).isNull(),c)).alias(c)
for c in users_df.columns
])
null_counts.show()

total = users_df.count()
distinct = users_df.dropDuplicates(["user_id"]).count()
print(f"Total:{total}, Distinct: {distinct}, Duplicates: {total-distinct}")

#------------------------------------------------------------------------------------
#To clean and enrich users

users_cleaned = users_df \
    .dropDuplicates(["user_id"]) \
    .withColumn("signup_date", F.to_date(F.col("signup_date"), "yyyy-MM-dd")) \
    .withColumn("name", F.trim(F.col("name"))) \
    .withColumn("city", F.trim(F.col("city"))) \
    .withColumn("email", F.lower(F.col("email")))

users_cleaned.printSchema()
users_cleaned.show(5)

#------------------------------------------------------------------------------------
#Add business enrichment
users_enriched = users_cleaned \
    .withColumn("age_group", F.when(F.col("age") < 25, "18-24")
                              .when(F.col("age") < 35, "25-34")
                              .when(F.col("age") < 50, "35-49")
                              .otherwise("50+")) \
    .withColumn("signup_year",  F.year(F.col("signup_date"))) \
    .withColumn("signup_month", F.month(F.col("signup_date"))) \
    .withColumn("account_age_days", F.datediff(F.current_date(), F.col("signup_date")))

users_enriched.select("user_id", "age", "age_group", "signup_date", "account_age_days").show(5)

#- -----------------------------------------------------------------------------------
#Write the cleaned and enriched data back to storage in Parquet format
users_enriched.write \
    .mode("overwrite") \
    .partitionBy("signup_year", "signup_month") \
    .parquet("/Volumes/workspace/default/raw_data/processed/users")

print("Users written successfully!")

#------------------------------------------------------------------------------------
#Verify the data written to storage
verification_df = spark.read.parquet("/Volumes/workspace/default/raw_data/processed/users")

print(f"Row count: {verification_df.count()}")
verification_df.show(3, vertical=True, truncate=False)
