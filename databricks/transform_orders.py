# This script is designed to run on Databricks.
# On Databricks, 'spark' is provided automatically.
# To run locally, initialise SparkSession manually.

import subprocess
result = subprocess.run(['find', '/Volumes/workspace/default/raw_data', '-type', 'f'], 
                      capture_output=True, text=True)
print(result.stdout)

PRODUCTS_PATH = "/Volumes/workspace/default/raw_data/products.csv"
USERS_PATH    = "/Volumes/workspace/default/raw_data/users.json"
ORDERS_PATH   = "/Volumes/workspace/default/raw_data/orders.csv"
EVENTS_PATH   = "/Volumes/workspace/default/raw_data/events.json"

PROCESSED_PATH = "/Volumes/workspace/default/processed_data"

#Below block is used to read raw data

orders_df = spark.read\
    .option("Header","true")\
    .option("inferSchema","true")\
    .csv(ORDERS_PATH)

orders_df.printSchema()

orders_df.show(5)

#Below block is used to check the null count in the data

from pyspark.sql import functions as F
null_counts = orders_df.select([
    F.count(F.when(F.col(c).isNull(), c)).alias(c)
    for c in orders_df.columns
])
null_counts.show()

#Below block is used to check the distinct orders

total_rows = orders_df.count()
distinct_rows=orders_df.dropDuplicates(["order_id"]).count()
print(f"Total rows:{total_rows}")
print(f"Distinct order_ids:{distinct_rows}")

#Below block is used to drop the duplicate data

total_rows = orders_df.count()
distinct_rows=orders_df.dropDuplicates(["order_id"]).count()
print(f"Total rows:{total_rows}")
print(f"Distinct order_ids:{distinct_rows}")


#Below block is used to clean and transform the data

orders_cleaned = orders_df \
    .dropDuplicates(["order_id"]) \
    .withColumn("order_total", F.round(F.col("order_total"),2)) \
    .withColumn("created_at",F.to_timestamp(F.col("created_at"))) \
    .withColumn("updated_at",F.to_timestamp(F.col("updated_at"))) \
    .withColumn("year", F.year(F.col("created_at"))) \
    .withColumn("month", F.month(F.col("created_at")))\
    .filter(F.col("order_total")>0)

orders_cleaned.printSchema()
orders_cleaned.show(5)

#Below block is used to add business matrics to the data

orders_enriched = orders_cleaned \
    .withColumn("is_high_value", F.when(F.col("order_total")>2000, True).otherwise(False))\
    .withColumn("order_size", F.when(F.col("num_items")==1, "single")
                               .when(F.col("num_items")<=3,"small")
                               .otherwise("Large")) \
    .withColumn("is_completed", F.when(F.col("status")=="completed", 1).otherwise(0))


orders_enriched.show(5, vertical= True, truncate = False)
    

#Below block is used to save the transformed data to processed_data folder in parquet format
orders_enriched.write \
    .mode("overwrite")\
    .partitionBy("year","month") \
    .parquet("/Volumes/workspace/default/raw_data/orders")

print("Orders written successfully!")

#Below block is used to verify the data written to processed_data folder in parquet format

verification_df = spark.read.parquet("/Volumes/workspace/default/raw_data/orders")

print(f"Row count: {verification_df.count()}")
verification_df.show(3, vertical = True, truncate = False)


