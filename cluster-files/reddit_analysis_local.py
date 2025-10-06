#!/usr/bin/env python3
"""
Problem 3: Reddit Subreddit Analysis (LOCAL VERSION)

This script analyzes Reddit comments from January 2024 to find:
1. Top 10 most popular subreddits by comment count
2. Peak commenting hours (UTC) across all subreddits

This is the LOCAL development version that works with a sample file.
"""

import os
import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, hour, from_unixtime,
    desc
)

# Set JAVA_HOME if not already set
if not os.environ.get('JAVA_HOME'):
    # Try common Java installation paths
    java_paths = [
        '/usr/lib/jvm/java-17-openjdk-amd64',
        '/usr/lib/jvm/java-11-openjdk-amd64',
        '/usr/lib/jvm/default-java',
    ]
    for path in java_paths:
        if os.path.exists(path):
            os.environ['JAVA_HOME'] = path
            print(f"✅ Set JAVA_HOME to: {path}")
            break
    else:
        print("⚠️  Warning: Could not find Java installation. Please set JAVA_HOME manually.")


def create_spark_session():
    """Create a local Spark session for development."""

    spark = (
        SparkSession.builder
        .appName("Problem3_RedditAnalysis_Local")
        .getOrCreate()
    )

    print("✅ Spark session created (local mode)")
    return spark


def analyze_popular_subreddits(spark, data_path):
    """
    Analyze Reddit data to find top 10 most popular subreddits by comment count.

    Args:
        spark: SparkSession object
        data_path: Path to Reddit parquet file

    Returns:
        Spark DataFrame with top 10 subreddits
    """

    print("\n" + "=" * 70)
    print("ANALYSIS 1: Top 10 Most Popular Subreddits")
    print("=" * 70)

    start_time = time.time()

    # Read Reddit comments
    print(f"\nReading Reddit comments from: {data_path}")
    reddit_df = spark.read.parquet(data_path)

    total_comments = reddit_df.count()
    print(f"✅ Loaded {total_comments:,} total comments")

    # Count comments per subreddit
    print("\nCounting comments per subreddit...")

    subreddit_counts = (reddit_df
        .groupBy("subreddit")
        .agg(count("*").alias("comment_count"))
        .orderBy(desc("comment_count"))
        .limit(10)
    )

    # Show results
    print("\nTop 10 Most Active Subreddits:")
    print("-" * 70)
    subreddit_counts.show(10, truncate=False)

    # Save to CSV
    output_file = "top_subreddits_local.csv"
    print(f"\n✅ Saving results to {output_file}")

    # Convert to Pandas for local CSV save
    pandas_df = subreddit_counts.toPandas()
    pandas_df.to_csv(output_file, index=False)

    # Calculate execution time
    end_time = time.time()
    execution_time = end_time - start_time
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
        data_path: Path to Reddit parquet file

    Returns:
        Spark DataFrame with hourly comment counts
    """

    print("\n" + "=" * 70)
    print("ANALYSIS 2: Peak Commenting Hours (UTC)")
    print("=" * 70)

    start_time = time.time()

    # Read Reddit comments
    print(f"\nReading Reddit comments from: {data_path}")
    reddit_df = spark.read.parquet(data_path)

    total_comments = reddit_df.count()
    print(f"✅ Loaded {total_comments:,} total comments")

    # Extract hour from created_utc timestamp
    print("\nExtracting hour from timestamps...")

    # created_utc is Unix timestamp, convert to datetime and extract hour
    reddit_with_hour = reddit_df.withColumn(
        "hour_utc",
        hour(from_unixtime(col("created_utc")))
    )

    # Count comments per hour
    print("Counting comments per hour...")

    hourly_counts = (reddit_with_hour
        .groupBy("hour_utc")
        .agg(count("*").alias("comment_count"))
        .orderBy("hour_utc")
    )

    # Show results
    print("\nComment Distribution by Hour (UTC):")
    print("-" * 70)
    hourly_counts.show(24, truncate=False)

    # Find peak hour
    peak_hour_df = hourly_counts.orderBy(desc("comment_count")).limit(1)
    peak_hour_data = peak_hour_df.collect()[0]
    peak_hour = peak_hour_data['hour_utc']
    peak_count = peak_hour_data['comment_count']

    # Save to CSV
    output_file = "peak_hours_local.csv"
    print(f"\n✅ Saving results to {output_file}")

    # Convert to Pandas for local CSV save
    pandas_df = hourly_counts.toPandas()
    pandas_df.to_csv(output_file, index=False)

    # Calculate execution time
    end_time = time.time()
    execution_time = end_time - start_time
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
    """Main function for Problem 3 - Reddit Analysis (Local Version)."""

    print("=" * 70)
    print("PROBLEM 3: Reddit Subreddit Analysis (LOCAL MODE)")
    print("Reddit Comments Data Analysis - Sample File")
    print("=" * 70)

    overall_start = time.time()

    # Create local Spark session
    spark = create_spark_session()

    # Path to local sample file (in current directory)
    # Students should download this file first:
    # aws s3 cp s3://dsan6000-datasets/reddit/parquet/comments/yyyy=2024/mm=01/comments_RC_2024-01.zst_97.parquet \
    #   reddit_sample.parquet --request-payer requester

    data_path = "reddit_sample.parquet"

    print(f"\n📁 Data source: {data_path}")
    print("⚠️  Make sure you downloaded the sample file first!")
    print("   Command: aws s3 cp s3://dsan6000-datasets/reddit/parquet/comments/yyyy=2024/mm=01/comments_RC_2024-01.zst_97.parquet reddit_sample.parquet --request-payer requester")

    # Run analyses
    success = True
    try:
        # Analysis 1: Top 10 Subreddits
        subreddit_results = analyze_popular_subreddits(spark, data_path)

        # Analysis 2: Peak Hours
        hourly_results = analyze_peak_hours(spark, data_path)

        print("\n✅ All analyses completed successfully!")

    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        success = False

    # Clean up
    spark.stop()

    # Overall timing
    overall_end = time.time()
    total_time = overall_end - overall_start

    print("\n" + "=" * 70)
    if success:
        print("✅ PROBLEM 3 LOCAL VERSION COMPLETED SUCCESSFULLY!")
        print(f"\nTotal execution time: {total_time:.2f} seconds")
        print("\nFiles created:")
        print("  - top_subreddits_local.csv (Top 10 most popular subreddits)")
        print("  - peak_hours_local.csv (Hourly comment distribution)")
        print("\nNext steps:")
        print("  1. Review the output files to verify your analysis logic")
        print("  2. Once confirmed working, create the cluster version:")
        print("     - Copy this script to reddit_analysis_cluster.py")
        print("     - Add cluster configuration (see nyc_tlc_problem1_cluster.py)")
        print("     - Change data path to S3A: s3a://your-netid-spark-reddit/...")
        print("     - Add command line argument for master URL")
        print("  3. Copy full dataset to S3 and run on cluster")
    else:
        print("❌ Problem 3 failed - check error messages above")
    print("=" * 70)

    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
