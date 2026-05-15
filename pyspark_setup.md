# PySpark Environment Setup (Windows + Conda + VS Code)

## 1. Prerequisites

Install the following:

- Miniconda or Anaconda
- Visual Studio Code
- Python extension for VS Code
- Jupyter extension for VS Code

Recommended:
- Windows 10/11 64-bit

---

# 2. Create Conda Environment

Open Anaconda Prompt:

```bash
conda create -n pyspark_env python=3.10 -y
```

Activate environment:

```bash
conda activate pyspark_env
```

---

# 3. Install Required Packages

Install stable Spark ecosystem packages:

```bash
pip install pyspark==3.5.5 pandas scikit-learn pyarrow jupyterlab ipykernel findspark
```

Optional but recommended:

```bash
pip install delta-spark
```

---

# 4. Configure Jupyter Kernel

```bash
python -m ipykernel install --user --name pyspark_env --display-name "PySpark (pyspark_env)"
```

---

# 5. Java Installation and Configuration

## Recommended Version

Use:

- Java 11 (LTS)

Recommended distribution:

https://adoptium.net/en-GB/temurin/releases/?version=11

Install:
- Windows x64 MSI installer

Example install location:

```text
C:\Program Files\Eclipse Adoptium\jdk-11.x.x
```

---

# 6. Configure JAVA_HOME

Open:

```text
Edit the system environment variables
```

Create System Variable:

```text
JAVA_HOME = C:\Program Files\Eclipse Adoptium\jdk-11.x.x
```

Add to PATH:

```text
%JAVA_HOME%\bin
```

Restart VS Code / terminal after configuration.

---

# 7. Configure Hadoop for Windows

## Create Hadoop Directory

Create:

```text
C:\hadoop
```

Inside it create:

```text
C:\hadoop\bin
```

---

## Download Hadoop Windows Binaries

Download Hadoop 3.3.x Windows binaries from:

https://github.com/cdarlint/winutils

Navigate to:

```text
hadoop-3.3.5/bin
```

Download BOTH:

```text
winutils.exe
hadoop.dll
```

Place them inside:

```text
C:\hadoop\bin
```

Final structure:

```text
C:\hadoop
│
└── bin
    ├── winutils.exe
    └── hadoop.dll
```

---

# 8. Configure HADOOP_HOME

Create System Variable:

```text
HADOOP_HOME = C:\hadoop
```

Add to PATH:

```text
C:\hadoop\bin
```

Restart system after configuration.

---

# 9. Configure PySpark Environment Variables

Optional but recommended:

```powershell
setx PYSPARK_PYTHON "python"
setx PYSPARK_DRIVER_PYTHON "python"
```

---

# 10. Verify Installation

## Check Java

```powershell
java -version
```

Expected:

```text
openjdk version "11..."
```

---

## Check Python

```powershell
where python
```

---

## Check Hadoop

```powershell
winutils.exe
```

If recognized, Hadoop native setup is correct.

---

# 11. Verify PySpark Environment

Run the following script:

```python
import os
import sys
import subprocess

import pyspark
import pandas
import sklearn

from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

print("Python Version:", sys.version)
print("PySpark Version:", pyspark.__version__)
print("Spark Version:", spark.version)
print("Pandas Version:", pandas.__version__)
print("Sklearn Version:", sklearn.__version__)
print("HADOOP_HOME:", os.environ.get("HADOOP_HOME"))

java_version = subprocess.check_output(
    ["java", "-version"],
    stderr=subprocess.STDOUT
).decode()

print("\nJava Version:")
print(java_version)

print("\nSpark Test:")
spark.range(5).show()
```

---

# 12. Test Parquet Read/Write

## Write Parquet using PySpark

```python
df = spark.range(10)

df.write.mode("overwrite").parquet("test_parquet")
```

---

## Read Parquet using PySpark

```python
df2 = spark.read.parquet("test_parquet")

df2.show()
```

---

## Read Spark-generated Parquet using Pandas

```python
import pandas as pd

df_pd = pd.read_parquet("test_parquet")

print(df_pd.head())
```

---

# 13. Launch JupyterLab

```bash
jupyter lab
```

Choose kernel:

```text
PySpark (pyspark_env)
```

---

# Final Stable Environment

| Component | Version |
|---|---|
| Python | 3.10 |
| PySpark | 3.5.5 |
| Spark | 3.5.5 |
| Java | 11 |
| Hadoop Native | 3.3.5 |
| Pandas | 2.x |
| Scikit-learn | 1.x |

This setup is:
- stable on Windows
- compatible with Parquet workflows
- suitable for PySpark ETL
- compatible with most enterprise Spark 3.x environments
- close to Databricks Spark workflows locally
