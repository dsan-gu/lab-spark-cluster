# Apache Spark Cluster Setup on AWS EC2 for lab-spark-on-ec2
*Created: 2025-10-04*
*Updated for PySpark 4.x with Java 17 and uv package management*

## Overview
This guide provides step-by-step instructions for setting up a 3-node Apache Spark cluster on AWS EC2 using t3.large instances. The cluster will be configured to run the code from the `lab-spark-on-ec2` repository.

The cluster will consist of:
- 1 Master node (Spark Master)
- 2 Worker nodes (Spark Workers)

Each node will have:
- Java 17 (required for PySpark 4.x)
- Python 3.10+
- uv package manager
- PySpark 4.x and all dependencies
- The lab-spark-on-ec2 repository

## Prerequisites
- AWS Account with appropriate permissions
- EC2 instance (Linux) to run these commands from
- Basic understanding of terminal/command line

---

## Part 1: AWS CLI Setup and Configuration

### Step 1.1: Install AWS CLI (if not already installed)

```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**Verify installation:**
```bash
aws --version
```

### Step 1.2: Configure AWS CLI

Run the configuration command:
```bash
aws configure
```

You will be prompted to enter:
- AWS Access Key ID: `[Your Access Key]`
- AWS Secret Access Key: `[Your Secret Key]`
- Default region name: `us-east-1` (or your preferred region)
- Default output format: `json`

### Step 1.3: Set Your Region as Environment Variable

```bash
export AWS_REGION=us-east-1
echo "export AWS_REGION=us-east-1" >> ~/.bashrc
```

---

## Part 2: Network Setup (VPC and Security Group)

### Step 2.1: Create a Security Group

Create a security group for the Spark cluster:
```bash
aws ec2 create-security-group \
  --group-name spark-cluster-sg \
  --description "Security group for Spark cluster" \
  --region $AWS_REGION
```

Save the Security Group ID from the output (format: `sg-xxxxxxxxx`):
```bash
export SPARK_SG_ID=sg-xxxxxxxxx
```

Replace `sg-xxxxxxxxx` with the actual Security Group ID from the output above.

### Step 2.2: Configure Security Group Rules

**Allow SSH access (port 22) from your IP:**
```bash
MY_IP=$(curl -s https://checkip.amazonaws.com)
aws ec2 authorize-security-group-ingress \
  --group-id $SPARK_SG_ID \
  --protocol tcp \
  --port 22 \
  --cidr ${MY_IP}/32 \
  --region $AWS_REGION
```

**Allow all traffic within the security group (for cluster communication):**
```bash
aws ec2 authorize-security-group-ingress \
  --group-id $SPARK_SG_ID \
  --protocol -1 \
  --source-group $SPARK_SG_ID \
  --region $AWS_REGION
```

**Allow Spark Web UI access (port 8080 for Master, 8081 for Workers):**
```bash
aws ec2 authorize-security-group-ingress \
  --group-id $SPARK_SG_ID \
  --protocol tcp \
  --port 8080-8081 \
  --cidr ${MY_IP}/32 \
  --region $AWS_REGION
```

**Allow Spark application UI (port 4040):**
```bash
aws ec2 authorize-security-group-ingress \
  --group-id $SPARK_SG_ID \
  --protocol tcp \
  --port 4040 \
  --cidr ${MY_IP}/32 \
  --region $AWS_REGION
```

---

## Part 3: Create SSH Key Pair

### Step 3.1: Create Key Pair

```bash
aws ec2 create-key-pair \
  --key-name spark-cluster-key \
  --query 'KeyMaterial' \
  --output text \
  --region $AWS_REGION > spark-cluster-key.pem
```

### Step 3.2: Set Correct Permissions

```bash
chmod 400 spark-cluster-key.pem
```

---

## Part 4: Launch EC2 Instances

### Step 4.1: Get Latest Ubuntu 24.04 (Noble) AMI ID

```bash
export AMI_ID=$(aws ec2 describe-images \
  --owners 099720109477 \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*" \
  --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
  --output text \
  --region $AWS_REGION)

echo "Using AMI: $AMI_ID"
```

This will get the latest Ubuntu 24.04 (Noble) AMI with GP3 storage.

### Step 4.2: Launch Master Node

```bash
aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t3.large \
  --key-name spark-cluster-key \
  --security-group-ids $SPARK_SG_ID \
  --count 1 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=spark-master},{Key=Role,Value=master}]' \
  --region $AWS_REGION
```

### Step 4.3: Launch Worker Nodes

```bash
aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t3.large \
  --key-name spark-cluster-key \
  --security-group-ids $SPARK_SG_ID \
  --count 2 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=spark-worker},{Key=Role,Value=worker}]' \
  --region $AWS_REGION
```

### Step 4.4: Wait for Instances to be Running

```bash
aws ec2 wait instance-running \
  --filters "Name=tag:Name,Values=spark-master,spark-worker" \
  --region $AWS_REGION

echo "All instances are now running!"
```

### Step 4.5: Get Instance Information

```bash
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=spark-master,spark-worker" \
  --query 'Reservations[*].Instances[*].[Tags[?Key==`Name`].Value | [0], InstanceId, PublicIpAddress, PrivateIpAddress]' \
  --output table \
  --region $AWS_REGION
```

**Save the IP addresses:**
```bash
export MASTER_PUBLIC_IP=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=spark-master" "Name=instance-state-name,Values=running" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text \
  --region $AWS_REGION)

export MASTER_PRIVATE_IP=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=spark-master" "Name=instance-state-name,Values=running" \
  --query 'Reservations[0].Instances[0].PrivateIpAddress' \
  --output text \
  --region $AWS_REGION)

echo "Master Public IP: $MASTER_PUBLIC_IP"
echo "Master Private IP: $MASTER_PRIVATE_IP"
```

**Get Worker IPs and save them:**
```bash
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=spark-worker" "Name=instance-state-name,Values=running" \
  --query 'Reservations[*].Instances[*].[PublicIpAddress, PrivateIpAddress]' \
  --output text \
  --region $AWS_REGION
```

Save the worker IPs from the output:
```bash
export WORKER1_PUBLIC_IP=[paste first worker public IP here]
export WORKER1_PRIVATE_IP=[paste first worker private IP here]
export WORKER2_PUBLIC_IP=[paste second worker public IP here]
export WORKER2_PRIVATE_IP=[paste second worker private IP here]
```

---

## Part 5: Setup Master Node

### Step 5.1: Connect to Master Node

```bash
ssh -i spark-cluster-key.pem ubuntu@$MASTER_PUBLIC_IP
```

### Step 5.2: Update System and Install Java 17

Once connected to the master node, run:
```bash
sudo apt-get update
sudo apt-get install -y openjdk-17-jdk
java -version
```

You should see output like: `openjdk version "17.x.x"`

### Step 5.3: Install uv Package Manager

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

Verify uv installation:
```bash
uv --version
```

### Step 5.4: Clone the Lab Repository

```bash
cd ~
git clone https://github.com/dsan-gu/lab-spark-on-ec2.git
cd lab-spark-on-ec2
```

### Step 5.5: Install Python Dependencies with uv

```bash
uv sync
```

This will create a virtual environment and install all dependencies from pyproject.toml including:
- PySpark 4.x
- Boto3
- Pandas
- Jupyter
- NLTK
- and more

### Step 5.6: Configure Environment Variables

```bash
echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64' >> ~/.bashrc
echo 'export SPARK_HOME=$(uv run python -c "import pyspark; import os; print(os.path.dirname(os.path.dirname(pyspark.__file__)))")' >> ~/.bashrc
echo 'export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin' >> ~/.bashrc
source ~/.bashrc
```

### Step 5.7: Verify Installation

```bash
cd ~/lab-spark-on-ec2
uv run python spark_installation_test.py
```

You should see all tests pass with green checkmarks.

### Step 5.8: Configure Spark for Cluster Mode

```bash
cd $SPARK_HOME/conf
sudo cp spark-env.sh.template spark-env.sh
```

Edit spark-env.sh:
```bash
sudo nano spark-env.sh
```

Add these lines at the end (replace `[MASTER_PRIVATE_IP]` with your actual master private IP):
```
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export SPARK_MASTER_HOST=[MASTER_PRIVATE_IP]
export SPARK_MASTER_PORT=7077
export PYSPARK_PYTHON=/home/ubuntu/lab-spark-on-ec2/.venv/bin/python
export PYSPARK_DRIVER_PYTHON=/home/ubuntu/lab-spark-on-ec2/.venv/bin/python
```

Save and exit (Ctrl+O, Enter, Ctrl+X).

### Step 5.9: Configure Workers

```bash
sudo cp workers.template workers
sudo nano workers
```

Remove localhost and add worker private IPs:
```
[WORKER1_PRIVATE_IP]
[WORKER2_PRIVATE_IP]
```

Replace with your actual worker private IPs. Save and exit.

### Step 5.10: Exit Master Node

```bash
exit
```

---

## Part 6: Setup Worker Node 1

### Step 6.1: Connect to Worker 1

```bash
ssh -i spark-cluster-key.pem ubuntu@$WORKER1_PUBLIC_IP
```

### Step 6.2: Install Java 17 and uv

```bash
sudo apt-get update
sudo apt-get install -y openjdk-17-jdk
java -version

curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
uv --version
```

### Step 6.3: Clone Lab Repository and Install Dependencies

```bash
cd ~
git clone https://github.com/dsan-gu/lab-spark-on-ec2.git
cd lab-spark-on-ec2
uv sync
```

### Step 6.4: Configure Environment Variables

```bash
echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64' >> ~/.bashrc
echo 'export SPARK_HOME=$(uv run python -c "import pyspark; import os; print(os.path.dirname(os.path.dirname(pyspark.__file__)))")' >> ~/.bashrc
echo 'export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin' >> ~/.bashrc
source ~/.bashrc
```

### Step 6.5: Configure Spark Environment

```bash
cd $SPARK_HOME/conf
sudo cp spark-env.sh.template spark-env.sh
sudo nano spark-env.sh
```

Add these lines:
```
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PYSPARK_PYTHON=/home/ubuntu/lab-spark-on-ec2/.venv/bin/python
export PYSPARK_DRIVER_PYTHON=/home/ubuntu/lab-spark-on-ec2/.venv/bin/python
```

Save and exit.

### Step 6.6: Exit Worker 1

```bash
exit
```

---

## Part 7: Setup Worker Node 2

### Step 7.1: Connect to Worker 2

```bash
ssh -i spark-cluster-key.pem ubuntu@$WORKER2_PUBLIC_IP
```

### Step 7.2: Install Java 17 and uv

```bash
sudo apt-get update
sudo apt-get install -y openjdk-17-jdk
java -version

curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
uv --version
```

### Step 7.3: Clone Lab Repository and Install Dependencies

```bash
cd ~
git clone https://github.com/dsan-gu/lab-spark-on-ec2.git
cd lab-spark-on-ec2
uv sync
```

### Step 7.4: Configure Environment Variables

```bash
echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64' >> ~/.bashrc
echo 'export SPARK_HOME=$(uv run python -c "import pyspark; import os; print(os.path.dirname(os.path.dirname(pyspark.__file__)))")' >> ~/.bashrc
echo 'export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin' >> ~/.bashrc
source ~/.bashrc
```

### Step 7.5: Configure Spark Environment

```bash
cd $SPARK_HOME/conf
sudo cp spark-env.sh.template spark-env.sh
sudo nano spark-env.sh
```

Add these lines:
```
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PYSPARK_PYTHON=/home/ubuntu/lab-spark-on-ec2/.venv/bin/python
export PYSPARK_DRIVER_PYTHON=/home/ubuntu/lab-spark-on-ec2/.venv/bin/python
```

Save and exit.

### Step 7.6: Exit Worker 2

```bash
exit
```

---

## Part 8: Setup SSH Keys for Passwordless Access

### Step 8.1: Copy Private Key to Master

From your EC2 instance (where you have the spark-cluster-key.pem file):
```bash
scp -i spark-cluster-key.pem spark-cluster-key.pem ubuntu@$MASTER_PUBLIC_IP:~/.ssh/
```

### Step 8.2: Connect to Master and Configure SSH

```bash
ssh -i spark-cluster-key.pem ubuntu@$MASTER_PUBLIC_IP
```

Set permissions on the key:
```bash
chmod 400 ~/.ssh/spark-cluster-key.pem
```

Create an SSH config file to use this key for worker connections:
```bash
cat >> ~/.ssh/config <<EOF
Host *
    IdentityFile ~/.ssh/spark-cluster-key.pem
    StrictHostKeyChecking no
EOF

chmod 600 ~/.ssh/config
```

---

## Part 9: Start Spark Cluster

### Step 9.1: Start Master Node

On the master node (should still be connected):
```bash
$SPARK_HOME/sbin/start-master.sh
```

Verify master is running:
```bash
jps
```

You should see `Master` in the output.

### Step 9.2: Start Worker Nodes from Master

```bash
$SPARK_HOME/sbin/start-workers.sh
```

### Step 9.3: Verify Cluster Status

```bash
jps
```

Check the Spark Master Web UI. Open a browser and navigate to:
```
http://[MASTER_PUBLIC_IP]:8080
```

Replace `[MASTER_PUBLIC_IP]` with your actual master public IP.

You should see 2 workers connected.

---

## Part 10: Test the Cluster with Lab Code

### Step 10.1: Test Spark Installation

Still on master node:
```bash
cd ~/lab-spark-on-ec2
uv run python spark_installation_test.py
```

All tests should pass.

### Step 10.2: Run Problem 1 (Example Solution)

```bash
uv run python nyc_tlc_problem1.py 2>&1 | tee problem1.txt
```

This will:
- Download NYC taxi data from S3
- Process it using Spark
- Generate `daily_averages.csv`

### Step 10.3: Run Problem 1 on the Cluster

To run on the cluster instead of local mode, you need to modify the script to use the cluster master URL:

```bash
# First, find out your Spark master URL
echo "spark://$MASTER_PRIVATE_IP:7077"
```

Then edit the Python script to use this URL instead of local mode, or run with spark-submit:

```bash
spark-submit --master spark://$MASTER_PRIVATE_IP:7077 nyc_tlc_problem1.py 2>&1 | tee problem1_cluster.txt
```

### Step 10.4: Monitor Jobs

While jobs are running, you can monitor them in the Spark Web UI:
- Master UI: `http://[MASTER_PUBLIC_IP]:8080`
- Application UI: `http://[MASTER_PUBLIC_IP]:4040`

---

## Part 11: Cluster Management

### Stop the Cluster

On master node:
```bash
$SPARK_HOME/sbin/stop-workers.sh
$SPARK_HOME/sbin/stop-master.sh
```

### Start the Cluster Again

```bash
$SPARK_HOME/sbin/start-master.sh
$SPARK_HOME/sbin/start-workers.sh
```

### Check Cluster Logs

Master logs:
```bash
tail -f $SPARK_HOME/logs/spark-*-master-*.out
```

Worker logs (on worker nodes):
```bash
tail -f $SPARK_HOME/logs/spark-*-worker-*.out
```

---

## Part 12: Running Lab Assignments on the Cluster

### Modifying Scripts for Cluster Execution

To run the lab scripts on your cluster, you need to modify the SparkSession creation to use the cluster master URL.

**Original (local mode):**
```python
spark = SparkSession.builder \
    .appName("NYC TLC Analysis") \
    .getOrCreate()
```

**Modified (cluster mode):**
```python
spark = SparkSession.builder \
    .appName("NYC TLC Analysis") \
    .master("spark://[MASTER_PRIVATE_IP]:7077") \
    .config("spark.executor.memory", "4g") \
    .config("spark.executor.cores", "2") \
    .getOrCreate()
```

Replace `[MASTER_PRIVATE_IP]` with your actual master private IP.

### Running with spark-submit

Alternatively, use spark-submit without modifying the code:
```bash
spark-submit \
  --master spark://[MASTER_PRIVATE_IP]:7077 \
  --executor-memory 4g \
  --executor-cores 2 \
  --total-executor-cores 4 \
  nyc_tlc_problem1.py
```

---

## Part 13: Cleanup (When Done)

### Terminate EC2 Instances

From your EC2 instance:
```bash
aws ec2 terminate-instances \
  --instance-ids $(aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=spark-master,spark-worker" "Name=instance-state-name,Values=running" \
    --query 'Reservations[*].Instances[*].InstanceId' \
    --output text \
    --region $AWS_REGION) \
  --region $AWS_REGION
```

### Delete Security Group

Wait for instances to fully terminate (takes a few minutes), then:
```bash
aws ec2 delete-security-group \
  --group-id $SPARK_SG_ID \
  --region $AWS_REGION
```

### Delete Key Pair

```bash
aws ec2 delete-key-pair \
  --key-name spark-cluster-key \
  --region $AWS_REGION

rm spark-cluster-key.pem
```

---

## Troubleshooting

### Workers Not Connecting

1. Check security group rules allow all traffic within the group
2. Verify private IPs in workers file on master: `cat $SPARK_HOME/conf/workers`
3. Check worker logs: `tail -f $SPARK_HOME/logs/spark-*-worker-*.out`
4. Verify SSH access from master to workers: `ssh ubuntu@[WORKER_PRIVATE_IP]`

### Cannot Access Web UI

1. Verify security group allows port 8080 from your IP
2. Check your current IP: `curl https://checkip.amazonaws.com`
3. Update security group if IP changed

### SSH Connection Issues

1. Verify key permissions: `chmod 400 spark-cluster-key.pem`
2. Check instance is running: `aws ec2 describe-instances --instance-ids [ID]`
3. Verify security group allows SSH from your IP

### Java Version Issues

If you see Java version errors:
```bash
java -version  # Should show version 17.x.x
echo $JAVA_HOME  # Should point to Java 17
```

If not set correctly:
```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64' >> ~/.bashrc
```

### Python/PySpark Issues

Verify Python environment:
```bash
cd ~/lab-spark-on-ec2
uv run python --version  # Should be 3.10+
uv run python -c "import pyspark; print(pyspark.__version__)"  # Should be 4.x
```

### Out of Memory Errors

If you get OOM errors when running lab scripts:
1. Reduce the number of months of data processed
2. Increase executor memory: `--executor-memory 6g`
3. Reduce executor cores: `--executor-cores 1`

---

## Additional Resources

- Apache Spark Documentation: https://spark.apache.org/docs/latest/
- PySpark Documentation: https://spark.apache.org/docs/latest/api/python/
- Spark Cluster Mode Overview: https://spark.apache.org/docs/latest/cluster-overview.html
- AWS EC2 User Guide: https://docs.aws.amazon.com/ec2/
- Lab Repository: https://github.com/dsan-gu/lab-spark-on-ec2

---

## Cost Estimate

**t3.large pricing (us-east-1):**
- On-Demand: ~$0.0832 per hour per instance
- 3 instances: ~$0.25 per hour
- Daily cost: ~$6.00

**Remember to terminate instances when not in use to avoid unnecessary charges!**

---

## Summary

You now have a 3-node Spark cluster running on EC2 with:
- Java 17 for PySpark 4.x compatibility
- Python 3.10+ with uv package management
- All dependencies from lab-spark-on-ec2 installed
- Cluster configured and ready to run lab assignments
- Ability to run both local and distributed Spark jobs

To run lab code on the cluster, either:
1. Modify scripts to include `.master("spark://[MASTER_PRIVATE_IP]:7077")` in SparkSession creation
2. Use `spark-submit` with `--master` flag

Monitor your jobs via the web UIs at ports 8080 (cluster) and 4040 (application).
