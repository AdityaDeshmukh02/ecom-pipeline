#Reading the raw data

from pyspark.sql import functions as F
EVENTS_PATH ="/Volumes/workspace/default/ecom_pipeline/events.json"
PROCESSED_PATH = "/Volumes/workspace/default/ecom_pipeline/processed/events"

events_df = spark.read \
    .option("multiline","true")\
    .json(EVENTS_PATH)
events_df.printSchema()
events_df.show(5,vertical=True, truncate=False)


#-----------------------------------------------------------------------------------------------------------------
#To check the data quality.

#Null_count
null_counts = events_df.select([
    F.count(F.when(F.col(c).isNull(),c)).alias(c)
    for c in events_df.columns
])
null_counts.show()

#Duplicates
total = events_df.count()
distinct = events_df.dropDuplicates(["event_id"]).count()
print(f"Total:  {total}, Distinct: {distinct} , Duplicates: {total - distinct}")

#To check the types of events

print("\n Event type distribution")
events_df.groupBy("event_type").count().orderBy("count", ascending=False).show()

#-----------------------------------------------------------------------------------------------------------------

#cleaning and enrich the data

events_cleaned =events_df\
    .dropDuplicates(["event_id"])\
    .withColumn("timestamp", F.to_timestamp(F.col("timestamp")))\
    .withColumn("date", F.to_date(F.col("timestamp")))\
    .withColumn("year", F.year(F.col("timestamp")))\
    .withColumn("month", F.month(F.col("timestamp")))\
    .withColumn("hour", F.hour(F.col("timestamp")))\
    .withColumn("is_purchase", F.when(F.col("event_type")=="purchase",1).otherwise(0))\
    .withColumn("has_product", F.when(F.col("product_id").isNotNull(), 1).otherwise (0))

events_cleaned.printSchema()
events_cleaned.show(5,vertical=True, truncate=False)

#-----------------------------------------------------------------------------------------------------------------

#Write the processed data

events_cleaned.write\
    .mode("overwrite")\
    .partitionBy("year","month")\
    .parquet(PROCESSED_PATH)

print("Events written successfully!")

#Verify

verification_df = spark.read.parquet(PROCESSED_PATH)
print(F"Row count: {verification_df.count()}")

verification_df.show(3, vertical=True, truncate=False)