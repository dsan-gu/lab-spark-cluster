# Lab: Spark Cluster Setup on AWS EC2

Step-by-step guide for setting up a 3-node Apache Spark cluster on AWS EC2.

## Overview

This lab provides hands-on experience with setting up and managing a distributed Apache Spark cluster on Amazon EC2. You will learn how to create, configure, and use a Spark cluster through three progressive steps:

1. **Manual Setup** - Build cluster step-by-step to understand all components
2. **Automated Setup** - Use automation scripts for rapid deployment
3. **Data Analysis** - Run real-world data processing jobs on your cluster

## What You'll Learn

By completing this lab, you will gain practical experience with:
- Creating and configuring EC2 instances using AWS CLI
- Setting up network security groups for cluster communication
- Configuring SSH keys and passwordless access between nodes
- Installing and configuring Apache Spark in distributed mode
- Monitoring Spark jobs via Web UIs
- Running PySpark jobs on a distributed cluster
- Processing large-scale data stored in Amazon S3
- Proper cluster resource cleanup and cost management

## Prerequisites

- AWS Account with appropriate IAM permissions
- Access to an EC2 instance (Linux) to run the setup commands
- Basic familiarity with terminal/command line
- AWS CLI configured with credentials
- Your laptop's public IP address (get from https://ipchicken.com/)

## Three-Step Learning Approach

### Step 1: Manual Cluster Setup (Learning the Fundamentals) - 20 Points

**Objective:** Gain hands-on understanding of every component involved in creating a Spark cluster.

Follow the detailed instructions in [SPARK_CLUSTER_SETUP.md](SPARK_CLUSTER_SETUP.md) to:
- Manually create EC2 instances
- Configure security groups and network rules
- Set up SSH keys and passwordless authentication
- Install Java, Python, and Spark on each node
- Configure master and worker nodes
- Start the Spark cluster
- Verify cluster operation through Web UIs

**Deliverables:**
- Working 3-node Spark cluster (1 master + 2 workers)
- Screenshots of:
  - Spark Master Web UI showing connected workers (placeholder - to be provided)
  - Spark Application UI showing a running job (placeholder - to be provided)
- Download result files from master node to your EC2 instance:
  ```bash
  scp -i spark-cluster-key.pem ubuntu@$MASTER_PUBLIC_IP:~/spark-cluster/problem1_cluster.txt .
  ```
- Commit and push the following files:
  - `cluster-config.txt`
  - `cluster-ips.txt`
  - `problem1_cluster.txt` (cluster run output)

**Cleanup:** After completing Step 1, manually delete resources in this order:
1. Terminate EC2 instances
2. Delete key pair
3. Delete security group

**⚠️ WARNING: If you do not delete your cluster, you will exhaust the funds in your account. Always delete your cluster when done!**

### Step 2: Automated Cluster Setup (Scripted Deployment) - 20 Points

**Objective:** Learn how to automate cluster deployment for rapid provisioning.

Follow the instructions in [AUTOMATION_README.md](AUTOMATION_README.md) to:
- Run the automated setup script `setup-spark-cluster.sh`
- Create a 4-node cluster (1 master + 3 workers) automatically
- Understand the automation workflow
- Submit a Spark job to the cluster
- Use the automated cleanup script

**Key Script:**
```bash
./setup-spark-cluster.sh <YOUR_LAPTOP_IP>
```

This script automates everything from Step 1, including:
- Security group creation
- Key pair generation
- EC2 instance provisioning
- Software installation on all nodes
- Spark configuration
- Cluster startup

**Deliverables:**
- Download result files from master node to your EC2 instance:
  ```bash
  # Use the SSH key from the setup (check cluster-config.txt for KEY_FILE name)
  source cluster-config.txt
  scp -i $KEY_FILE ubuntu@$MASTER_PUBLIC_IP:~/spark-cluster/*.txt .
  ```
- Commit and push the following files:
  - `cluster-config.txt`
  - `cluster-ips.txt`
  - `ssh_to_master_node.sh`
  - Output files from running the NYC TLC job (downloaded from master node)

**Cleanup:** Use the automated cleanup script:
```bash
./cleanup-spark-cluster.sh
```

Or manually delete resources as in Step 1.

**⚠️ WARNING: If you do not delete your cluster, you will exhaust the funds in your account. Always delete your cluster when done! Use [cleanup-spark-cluster.sh](cleanup-spark-cluster.sh) for automated cleanup or manual deletion.**

### Step 3: Real-World Data Analysis (Reddit Data Processing) - 10 Points

**Objective:** Apply your Spark cluster skills to analyze real-world social media data.

#### Setup

1. **Create S3 bucket for your data:**
```bash
aws s3 mb s3://your-netid-spark-reddit
```

2. **Copy Reddit data from shared dataset:**
```bash
aws s3 cp s3://dsan6000-datasets/reddit/parquet/comments/yyyy=2024/mm=01/ \
  s3://your-netid-spark-reddit/reddit/comments/yyyy=2024/mm=01/ \
  --recursive
```

#### Problem 3: Reddit Subreddit Analysis

**Dataset:** Reddit comments from January 2024 (Parquet format)
- Source: `s3://dsan6000-datasets/reddit/parquet/comments/yyyy=2024/mm=01/*.parquet`
- Format: Parquet files with columns including `subreddit`, `body`, `author`, `created_utc`, etc.

**Task:** Analyze the Reddit comments data to answer the following questions:

1. **Most Popular Subreddits:** Find the top 10 most active subreddits by comment count
2. **Temporal Analysis:** Identify peak commenting hours (UTC) across all subreddits

**Deliverables:**
- PySpark script (`reddit_analysis.py`) that performs the analysis
- Output files saved to your S3 bucket
- Screenshots of:
  - Spark Web UI showing the job execution
  - Application UI showing the DAG (Directed Acyclic Graph)
- Brief report with findings

**Hints:**
- Use `spark.read.parquet()` to load data from S3
- Configure AWS credentials in Spark configuration
- Use DataFrame operations for efficient processing
- Consider using `repartition()` for better parallelism
- Save results using `df.write.csv()`

**⚠️ WARNING: If you do not delete your cluster, you will exhaust the funds in your account. Always delete your cluster when done! Use [cleanup-spark-cluster.sh](cleanup-spark-cluster.sh) for automated cleanup.**

## Cost Estimate

**Important:** Running this cluster will incur AWS costs.

- **Instance type:** t3.large
- **Number of instances:**
  - Step 1: 3 instances (1 master + 2 workers) ≈ $0.20/hour
  - Step 2: 4 instances (1 master + 3 workers) ≈ $0.25/hour
  - Step 3: 4 instances + S3 storage ≈ $0.25/hour + minimal storage costs
- **Estimated total cost:** $6-8 for completing all three steps

**Always remember to terminate your instances and delete S3 data when done to avoid unnecessary charges.**

## Repository Structure

```
lab-spark-cluster/
├── README.md                      # This file - overview and 3-step guide
├── SPARK_CLUSTER_SETUP.md         # Step 1: Manual setup instructions
├── AUTOMATION_README.md           # Step 2: Automated setup guide
├── setup-spark-cluster.sh         # Automated cluster creation script
├── cleanup-spark-cluster.sh       # Automated cluster cleanup script
├── cluster-files/                 # Configuration files for cluster nodes
├── pyproject.toml                 # Python dependencies
└── .gitignore                     # Git ignore file (includes *.pem)
```

## Getting Started

1. **Clone this repository** (if in a git environment) or navigate to the project directory:
```bash
cd /home/ubuntu/lab-spark-cluster
```

2. **Start with Step 1** - Follow [SPARK_CLUSTER_SETUP.md](SPARK_CLUSTER_SETUP.md) for manual setup

3. **Progress to Step 2** - Follow [AUTOMATION_README.md](AUTOMATION_README.md) for automated setup

4. **Complete Step 3** - Work on the Reddit data analysis problem

## Support

If you encounter issues:
1. Check the Troubleshooting sections in the respective guides
2. Verify all environment variables are set correctly
3. Check the Spark logs on master and worker nodes: `$SPARK_HOME/logs/`
4. Ensure security group rules are properly configured
5. Verify AWS credentials and S3 bucket permissions

## Important Security Notes

- **Never commit `.pem` files** - They are in `.gitignore`
- **Limit security group access** - Only allow your IP addresses
- **Use IAM roles** - Instances use `LabInstanceProfile` for S3 access
- **Delete resources** - Always clean up when done

## Related Resources

- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [PySpark API Reference](https://spark.apache.org/docs/latest/api/python/)
- [AWS EC2 User Guide](https://docs.aws.amazon.com/ec2/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)

## License

MIT License
