# CostOptimizer

A serverless AWS solution to automatically clean up idle resources and schedule EC2 start‑stop actions for cost optimization.

## 🚀 Features

- **Idle resource cleaner**: detects and optionally deletes:
  - Unattached EBS volumes
  - Orphaned EC2 snapshots (with configurable age threshold)
  - Idle Elastic IP addresses
- **Auto Start/Stop scheduler**: start or stop EC2 and RDS resources based on tags (`AutoSchedule=true`, `Env=Dev`) at specified times.
- Fully deployed via **Terraform**, including IAM roles/policies, Lambda functions and EventBridge rules.

---

## 🧩 Architecture

1. **Lambda: cleaner**  
   Runs daily to clean idle resources and sends a summary via SNS.

2. **Lambda: auto-start-stop**  
   Triggered by EventBridge rules to start or stop instances at scheduled times.

3. **IAM Roles & Policies**  
   Grant least-privilege permissions to Lambda functions.

---

## 🛠️ Getting Started

### Prerequisites

- AWS account & CLI configured (`aws configure`)
- Terraform installed (v1.0+)
- Python 3.9+ for local testing (optional)

### Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/ArmanNavodia/CostOptimizer.git
   cd CostOptimizer
2. Deploy with Terraform:
    ```bash
    terraform init
    terraform apply
### ⏰ Scheduled Events
| Schedule	| Purpose |	EventBridge Cron |
|-----------|---------|------------------|
|Daily cleaner|	02:00 UTC|cron(30 17 * * ? *) (11:00 PM IST)|
|Start instances|02:30 UTC|cron(30 2 * * ? *) (8:00 AM IST)|
|Stop instances|16:30 UTC|cron(30 16 * * ? *) (10:00 PM IST)|


### ⚙️ Configuration Options
Threshold: (default 30) — snapshots older than this are cleaned up.

Tags: uses AutoSchedule=true and Env=Dev to scope instance operations.

Tags: uses Retain=true and Days=45 to retain volumes and snapshot for specific number of days. Use Days=-1 to retain forever

### ✅ Next Steps

**SNS Topic + Subscription**  
   Sends daily operation summaries to configured email.
