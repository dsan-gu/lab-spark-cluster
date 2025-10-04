# Lab: Spark Cluster Setup on AWS EC2

Step-by-step guide for setting up a 3-node Apache Spark cluster on AWS EC2 for running the [lab-spark-on-ec2](https://github.com/dsan-gu/lab-spark-on-ec2) assignments.

## Overview

This repository contains comprehensive instructions for students to set up a distributed Apache Spark cluster on Amazon EC2. The cluster consists of:
- 1 Master node (Spark Master)
- 2 Worker nodes (Spark Workers)
- All nodes running Ubuntu 24.04 on t3.large instances

Each node will be configured with:
- Java 17 (required for PySpark 4.x)
- Python 3.10+
- uv package manager
- PySpark 4.x and all lab dependencies
- The lab-spark-on-ec2 repository cloned and ready to run

## Prerequisites

- AWS Account with appropriate IAM permissions
- Access to an EC2 instance (Linux) to run the setup commands
- Basic familiarity with terminal/command line
- AWS CLI configured with credentials

## What You'll Learn

By following this guide, you will:
1. Create and configure EC2 instances using AWS CLI
2. Set up network security groups for Spark cluster communication
3. Install and configure Java 17 and Python 3.10+
4. Set up a distributed Spark cluster with 1 master and 2 worker nodes
5. Configure passwordless SSH between cluster nodes
6. Run PySpark jobs in both local and distributed modes
7. Monitor Spark jobs via web UIs

## Getting Started

Follow the detailed instructions in [SPARK_CLUSTER_SETUP.md](SPARK_CLUSTER_SETUP.md).

## Quick Start

```bash
# Clone this repository
git clone https://github.com/dsan-gu/lab-spark-cluster.git
cd lab-spark-cluster

# Follow the step-by-step instructions in SPARK_CLUSTER_SETUP.md
```

## Cost Estimate

**Important:** Running this cluster will incur AWS costs.

- Instance type: t3.large
- Number of instances: 3 (1 master + 2 workers)
- Approximate cost: $0.25/hour or $6/day

**Always remember to terminate your instances when done to avoid unnecessary charges.**

## Repository Structure

```
lab-spark-cluster/
├── README.md                    # This file
├── SPARK_CLUSTER_SETUP.md       # Detailed setup instructions
├── pyproject.toml               # Python dependencies (for local testing)
└── .gitignore                   # Git ignore file
```

## Support

If you encounter issues:
1. Check the Troubleshooting section in [SPARK_CLUSTER_SETUP.md](SPARK_CLUSTER_SETUP.md)
2. Verify all environment variables are set correctly
3. Check the Spark logs on master and worker nodes
4. Ensure security group rules are properly configured

## Related Resources

- [lab-spark-on-ec2](https://github.com/dsan-gu/lab-spark-on-ec2) - The lab assignments to run on this cluster
- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [PySpark API Reference](https://spark.apache.org/docs/latest/api/python/)
- [AWS EC2 User Guide](https://docs.aws.amazon.com/ec2/)

## License

MIT License
