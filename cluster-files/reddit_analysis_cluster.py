#!/usr/bin/env python3
"""
Problem 3: Reddit Subreddit Analysis (CLUSTER VERSION)

This script analyzes Reddit comments from January 2024 to find:
1. Top 10 most popular subreddits by comment count
2. Peak commenting hours (UTC) across all subreddits
"""

import os
import sys
import time
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, hour, from_unixtime,
    desc
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s,p%(process)s,{%(filename)s:%(lineno)d},%(levelname)s,%(message)s",
)

logger = logging.getLogger(__name__)


def create_spark_session(master_url):
    """Create a Spark session optimized for cluster execution."""

    spark = (
        SparkSession.builder
        .appName("Problem3_RedditAnalysis_Cluster")

        # Cluster Configuration
        .master(master_url)  # Connect to Spark cluster

        # Memory Configuration
        .config("spark.executor.memory", "4g")
        .config("spark.driver.memory", "4g")
        .config("spark.driver.maxResultSize", "2g")

        # Executor Configuration
        .config("spark.executor.cores", "2")
        .config("spark.cores.max", "6")  # Use all available cores across cluster

        # S3 Configuration - Use S3A for AWS S3 access
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "com.amazonaws.auth.InstanceProfileCredentialsProvider")

        # Performance settings for cluster execution
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")

        # Serialization
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")

        .getOrCreate()
    )

    logger.info("Spark session created successfully for cluster execution")
    return spark


def analyze_popular_subreddits(spark, data_path):
    """
    Analyze Reddit data to find top 10 most popular subreddits by comment count.

    Args:
        spark: SparkSession object
        data_path: S3 path to Reddit parquet files

    Returns:
        Spark DataFrame with top 10 subreddits
    """

    logger.info("Starting analysis: Top 10 Most Popular Subreddits")
    print("\n" + "=" * 70)
    print("ANALYSIS 1: Top 10 Most Popular Subreddits")
    print("=" * 70)

    start_time = time.time()

    # Read Reddit comments from S3
    logger.info(f"Reading Reddit data from: {data_path}")
    print(f"\nReading Reddit comments from S3...")
    print(f"Path: {data_path}")

    reddit_df = spark.read.parquet(data_path)

    total_comments = reddit_df.count()
    logger.info(f"Loaded {total_comments:,} total comments")
    print(f"✅ Loaded {total_comments:,} total comments")

    # Count comments per subreddit
    logger.info("Counting comments per subreddit")
    print("\nCounting comments per subreddit...")

    subreddit_counts = (reddit_df
        .groupBy("subreddit")
        .agg(count("*").alias("comment_count"))
        .orderBy(desc("comment_count"))
        .limit(10)
    )

    # Show results
    logger.info("Displaying top 10 subreddits")
    print("\nTop 10 Most Active Subreddits:")
    print("-" * 70)
    subreddit_counts.show(10, truncate=False)

    # Save to CSV
    output_file = "top_subreddits.csv"
    logger.info(f"Saving results to {output_file}")
    print(f"\n✅ Saving results to {output_file}")

    # Convert to Pandas for local CSV save
    pandas_df = subreddit_counts.toPandas()
    pandas_df.to_csv(output_file, index=False)

    # Calculate execution time
    end_time = time.time()
    execution_time = end_time - start_time
    logger.info(f"Analysis 1 completed in {execution_time:.2f} seconds")
    print(f"⏱️  Execution time: {execution_time:.2f} seconds")

    # Print summary
    print("\n" + "=" * 70)
    print("ANALYSIS 1 SUMMARY")
    print("=" * 70)
    print(f"Total comments analyzed: {total_comments:,}")
    print(f"Total unique subreddits: {reddit_df.select('subreddit').distinct().count():,}")
    print(f"Top subreddit: {pandas_df.iloc[0]['subreddit']} ({pandas_df.iloc[0]['comment_count']:,} comments)")
    print(f"Results saved to: {output_file}")
    print("=" * 70)

    return subreddit_counts


def analyze_peak_hours(spark, data_path):
    """
    Analyze Reddit data to identify peak commenting hours (UTC).

    Args:
        spark: SparkSession object
        data_path: S3 path to Reddit parquet files

    Returns:
        Spark DataFrame with hourly comment counts
    """

    logger.info("Starting analysis: Peak Commenting Hours")
    print("\n" + "=" * 70)
    print("ANALYSIS 2: Peak Commenting Hours (UTC)")
    print("=" * 70)

    start_time = time.time()

    # Read Reddit comments from S3
    logger.info(f"Reading Reddit data from: {data_path}")
    print(f"\nReading Reddit comments from S3...")
    print(f"Path: {data_path}")

    reddit_df = spark.read.parquet(data_path)

    total_comments = reddit_df.count()
    logger.info(f"Loaded {total_comments:,} total comments")
    print(f"✅ Loaded {total_comments:,} total comments")

    # Extract hour from created_utc timestamp
    logger.info("Extracting hour from created_utc timestamp")
    print("\nExtracting hour from timestamps...")

    # created_utc is Unix timestamp, convert to datetime and extract hour
    reddit_with_hour = reddit_df.withColumn(
        "hour_utc",
        hour(from_unixtime(col("created_utc")))
    )

    # Count comments per hour
    logger.info("Counting comments per hour")
    print("Counting comments per hour...")

    hourly_counts = (reddit_with_hour
        .groupBy("hour_utc")
        .agg(count("*").alias("comment_count"))
        .orderBy("hour_utc")
    )

    # Show results
    logger.info("Displaying hourly comment distribution")
    print("\nComment Distribution by Hour (UTC):")
    print("-" * 70)
    hourly_counts.show(24, truncate=False)

    # Find peak hour
    peak_hour_df = hourly_counts.orderBy(desc("comment_count")).limit(1)
    peak_hour_data = peak_hour_df.collect()[0]
    peak_hour = peak_hour_data['hour_utc']
    peak_count = peak_hour_data['comment_count']

    # Save to CSV
    output_file = "peak_hours.csv"
    logger.info(f"Saving results to {output_file}")
    print(f"\n✅ Saving results to {output_file}")

    # Convert to Pandas for local CSV save
    pandas_df = hourly_counts.toPandas()
    pandas_df.to_csv(output_file, index=False)

    # Calculate execution time
    end_time = time.time()
    execution_time = end_time - start_time
    logger.info(f"Analysis 2 completed in {execution_time:.2f} seconds")
    print(f"⏱️  Execution time: {execution_time:.2f} seconds")

    # Print summary
    print("\n" + "=" * 70)
    print("ANALYSIS 2 SUMMARY")
    print("=" * 70)
    print(f"Total comments analyzed: {total_comments:,}")
    print(f"Peak hour: {peak_hour}:00 UTC ({peak_count:,} comments)")
    print(f"Average comments per hour: {pandas_df['comment_count'].mean():.0f}")
    print(f"Results saved to: {output_file}")
    print("=" * 70)

    return hourly_counts


def main():
    """Main function for Problem 3 - Reddit Analysis (Cluster Version)."""

    logger.info("Starting Problem 3: Reddit Subreddit Analysis (Cluster Mode)")
    print("=" * 70)
    print("PROBLEM 3: Reddit Subreddit Analysis (CLUSTER MODE)")
    print("Reddit Comments Data Analysis (January 2024)")
    print("=" * 70)

    # Get master URL from command line or environment variable
    if len(sys.argv) > 1:
        master_url = sys.argv[1]
    else:
        # Try to get from environment variable
        master_private_ip = os.getenv("MASTER_PRIVATE_IP")
        if master_private_ip:
            master_url = f"spark://{master_private_ip}:7077"
        else:
            print("❌ Error: Master URL not provided")
            print("Usage: python reddit_analysis.py spark://MASTER_IP:7077")
            print("   or: export MASTER_PRIVATE_IP=xxx.xxx.xxx.xxx")
            return 1

    print(f"Connecting to Spark Master at: {master_url}")
    logger.info(f"Using Spark master URL: {master_url}")

    overall_start = time.time()

    # Create Spark session
    logger.info("Initializing Spark session for cluster execution")
    spark = create_spark_session(master_url)

    # S3 path to Reddit data
    # Students should update this to their own bucket
    data_path = "s3a://aa1603-reddit/reddit/comments/yyyy=2024/mm=01/*.parquet"

    print(f"\n📁 Data source: {data_path}")
    print("⚠️  Note: Update 'your-netid' in the script to match your S3 bucket name")
    print("⚠️  Make sure you copied data from s3://dsan6000-datasets with --request-payer requester")
    logger.info(f"Using data path: {data_path}")

    # Run analyses
    success = True
    try:
        # Analysis 1: Top 10 Subreddits
        logger.info("Starting Analysis 1: Top Subreddits")
        subreddit_results = analyze_popular_subreddits(spark, data_path)

        # Analysis 2: Peak Hours
        logger.info("Starting Analysis 2: Peak Hours")
        hourly_results = analyze_peak_hours(spark, data_path)

        logger.info("All analyses completed successfully")

    except Exception as e:
        logger.exception(f"Error occurred during analysis: {str(e)}")
        print(f"\n❌ Error during analysis: {str(e)}")
        success = False

    # Clean up
    logger.info("Stopping Spark session")
    spark.stop()

    # Overall timing
    overall_end = time.time()
    total_time = overall_end - overall_start
    logger.info(f"Total execution time: {total_time:.2f} seconds")

    print("\n" + "=" * 70)
    if success:
        print("✅ PROBLEM 3 COMPLETED SUCCESSFULLY!")
        print(f"\nTotal execution time: {total_time:.2f} seconds")
        print("\nFiles created:")
        print("  - top_subreddits.csv (Top 10 most popular subreddits)")
        print("  - peak_hours.csv (Hourly comment distribution)")
        print("\nNext steps:")
        print("  1. Download the CSV files from the master node:")
        print("     scp -i <key>.pem ubuntu@<master-ip>:~/spark-cluster/*.csv .")
        print("  2. Commit and push the results to your repository")
        print("  3. Take screenshots of Spark Web UI and Application UI")
        print("  4. Write a brief report with your findings")
    else:
        print("❌ Problem 3 failed - check error messages above")
    print("=" * 70)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
