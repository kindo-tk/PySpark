# PySpark Tutorial for Beginners

A comprehensive guide to Apache PySpark fundamentals with practical examples and hands-on notebooks covering data processing, transformation, and machine learning operations.

## Table of Contents

- [What is PySpark?](#what-is-pyspark)
- [Why Use PySpark?](#why-use-pyspark)
- [Installation and Setup](#installation-and-setup)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Cheat Sheet](#cheat-sheet)
- [Tutorial Notebooks](#tutorial-notebooks)
- [Datasets](#datasets)

## What is PySpark?

Apache PySpark is the Python API for Apache Spark, a unified analytics engine designed for large-scale data processing. It allows you to write Spark applications using Python and provides high-level APIs for distributed data processing.

PySpark abstracts the complexity of distributed computing and provides a user-friendly interface to work with structured data through DataFrames, similar to pandas but optimized for distributed systems.

Key Components:
- **RDD (Resilient Distributed Dataset)**: Immutable, distributed collection of objects
- **DataFrame**: Distributed collection of data organized into named columns
- **SQL**: Support for SQL queries on distributed data
- **MLlib**: Machine learning library for distributed learning algorithms
- **Spark Streaming**: Real-time data processing

## Why Use PySpark?

1. **Distributed Processing**: Handle large datasets across multiple machines seamlessly
2. **Performance**: Up to 100x faster than traditional MapReduce for iterative algorithms
3. **Ease of Use**: Simple Python API similar to pandas for familiar workflows
4. **Language Support**: Multiple language APIs (Python, Scala, SQL, R)
5. **Unified Platform**: Single engine for batch processing, streaming, and machine learning
6. **In-Memory Processing**: Caches data in memory for faster computations
7. **Fault Tolerance**: Automatic recovery from node failures
8. **Integration**: Works well with Hadoop, HDFS, Hive, and other ecosystems

## Installation and Setup

For detailed installation and configuration instructions, please refer to the setup guide:

**[PySpark Setup Guide](pyspark_setup.md)**

This guide includes:
- Environment creation with Conda
- Required package installation
- Jupyter kernel configuration
- Java installation and setup
- Environment variable configuration
- Installation verification

## Quick Start

### Initialize a Spark Session

The entry point to any PySpark application is the SparkSession. Always start your PySpark code with this:

```python
from pyspark.sql import SparkSession

# Create SparkSession
spark = SparkSession.builder \
    .appName("MyApp") \
    .master("local[*]") \
    .getOrCreate()

# Get Spark Context
sc = spark.sparkContext
```

Parameters:
- `appName`: Name of your Spark application
- `master`: Master URL (local[*] uses all available cores)

## Core Concepts

### 1. Creating DataFrames

From CSV:
```python
df = spark.read.csv("path/to/file.csv", header=True, inferSchema=True)
```

From Pandas:
```python
import pandas as pd
pandas_df = pd.read_csv("path/to/file.csv")
spark_df = spark.createDataFrame(pandas_df)
```

From List of Tuples:
```python
data = [("Alice", 25), ("Bob", 30), ("Charlie", 35)]
df = spark.createDataFrame(data, ["Name", "Age"])
```

### 2. Viewing Data

```python
df.show()                    # Display first 20 rows
df.show(5)                   # Display first 5 rows
df.head(3)                   # Get first 3 rows as list
df.take(2)                   # Get first 2 rows as list
df.display()                 # Notebook display (Databricks)
```

### 3. Schema and Column Information

```python
df.printSchema()             # Show data types
df.dtypes                    # Get list of (column, type) tuples
df.columns                   # Get column names
df.count()                   # Get row count
df.describe().show()         # Statistical summary (min, max, mean, etc.)
df.info()                    # DataFrame information
```

## Cheat Sheet

### Reading Data

```python
# CSV
df = spark.read.csv("file.csv", header=True, inferSchema=True)

# Parquet
df = spark.read.parquet("file.parquet")

# JSON
df = spark.read.json("file.json")

# SQL Table
df = spark.sql("SELECT * FROM table_name")

# With custom delimiter and encoding
df = spark.read.csv("file.csv", sep=",", header=True, encoding="UTF-8")
```

### Selecting Columns

```python
# Select single column
df.select("Name").show()

# Select multiple columns
df.select(["Name", "Age"]).show()

# Select using col()
from pyspark.sql.functions import col
df.select(col("Name"), col("Salary")).show()

# Drop column
df.drop("Age").show()
df = df.drop("Age")  # Assign to persist

# Rename column
df = df.withColumnRenamed("OldName", "NewName")
df = df.withColumnRenamed("old1", "new1") \
       .withColumnRenamed("old2", "new2")
```

### Adding and Modifying Columns

```python
# Add new column with constant value
df = df.withColumn("Country", lit("USA"))

# Add column with calculation
df = df.withColumn("Salary_Double", df.Salary * 2)

# Add column from expression
from pyspark.sql.functions import expr
df = df.withColumn("Age_Group", 
    expr("CASE WHEN Age < 30 THEN 'Young' ELSE 'Senior' END"))

# Add column using when/otherwise
from pyspark.sql.functions import when
df = df.withColumn("Status", 
    when(df.Salary > 50000, "High").otherwise("Low"))

# Cast column type
df = df.withColumn("Age_str", df.Age.cast("string"))
```

### Filtering Data

```python
# Filter with string expression
df.filter("Salary > 50000").show()

# Filter with column comparison
df.filter(df.Salary > 50000).show()

# Multiple conditions (AND - use &)
df.filter((df.Salary > 50000) & (df.Age < 40)).show()

# Multiple conditions (OR - use |)
df.filter((df.Department == "Sales") | (df.Department == "IT")).show()

# NOT condition (use ~)
df.filter(~(df.Salary < 30000)).show()

# Filter with isin()
df.filter(df.Department.isin(["Sales", "IT"])).show()

# Filter with between()
df.filter(df.Salary.between(40000, 60000)).show()

# Filter NULL values
df.filter(df.Age.isNull()).show()
df.filter(df.Age.isNotNull()).show()

# Filter string patterns
df.filter(df.Name.like("A%")).show()  # Starts with A
df.filter(df.Name.contains("Smith")).show()  # Contains Smith
```

### Merging DataFrames

```python
# Union (combine rows) - same schema required
df_combined = df1.union(df2)
df_combined = df1.unionByName(df2)  # Match by column names

# Union All (with duplicates)
df_combined = df1.unionAll(df2)

# Inner Join
df_join = df1.join(df2, on="common_column", how="inner")
df_join = df1.join(df2, df1.key == df2.key, "inner")

# Left Join
df_join = df1.join(df2, on="common_column", how="left")

# Right Join
df_join = df1.join(df2, on="common_column", how="right")

# Full Outer Join
df_join = df1.join(df2, on="common_column", how="outer")

# Left Semi Join (keeps only columns from df1)
df_join = df1.join(df2, on="common_column", how="leftsemi")

# Left Anti Join (opposite of semi)
df_join = df1.join(df2, on="common_column", how="leftanti")

# Join with multiple columns
df_join = df1.join(df2, 
    (df1.id == df2.id) & (df1.date == df2.date), "inner")
```

### GroupBy and Aggregation

```python
# Simple groupby
df.groupby("Department").sum().show()

# Groupby with multiple columns
df.groupby("Department", "Country").sum().show()

# Groupby with aggregation
df.groupby("Department").agg({
    "Salary": "sum",
    "Age": "mean"
}).show()

# Using agg with functions
from pyspark.sql.functions import sum, mean, count, max, min
df.groupby("Department").agg(
    sum("Salary").alias("TotalSalary"),
    mean("Age").alias("AvgAge"),
    count("*").alias("NumEmployees"),
    max("Salary").alias("MaxSalary")
).show()

# Groupby with multiple aggregations
df.groupby("Department").agg(
    mean("Salary").alias("AvgSalary"),
    sum("Salary").alias("TotalSalary"),
    count("*").alias("Count"),
    min("Age").alias("MinAge"),
    max("Age").alias("MaxAge")
).show()

# Window functions
from pyspark.sql.functions import row_number, rank, dense_rank
from pyspark.sql.window import Window

window = Window.partitionBy("Department").orderBy("Salary")
df.withColumn("RowNum", row_number().over(window)).show()
```

### Handling Missing Values

```python
# Check for null values
df.filter(df.Age.isNull()).show()

# Drop rows with any null
df.na.drop().show()
df.dropna().show()

# Drop rows with all nulls
df.na.drop(how="all").show()

# Drop with threshold (minimum non-null values)
df.na.drop(thresh=2).show()  # Keep rows with at least 2 non-null values

# Drop rows where specific column is null
df.na.drop(subset=["Age"]).show()
df.na.drop(subset=["Age", "Salary"]).show()

# Fill null values with constant
df.na.fill(0).show()  # Fill all numeric nulls with 0
df.na.fill("Unknown").show()  # Fill string nulls

# Fill specific columns
df.na.fill(0, subset=["Age", "Salary"]).show()

# Fill with mean/median imputation
from pyspark.ml.feature import Imputer

imputer = Imputer(
    inputCols=["Age", "Salary"],
    outputCols=["Age_imputed", "Salary_imputed"]
).setStrategy("mean")

df_imputed = imputer.fit(df).transform(df)
df_imputed.show()

# Forward fill and backward fill (using lag/lead)
from pyspark.sql.functions import lag
from pyspark.sql.window import Window

window = Window.orderBy("Date")
df = df.withColumn("Age_filled", 
    lag("Age").over(window))
```

### Sorting and Ordering

```python
# Sort ascending
df.sort("Age").show()
df.orderBy("Age").show()

# Sort descending
df.sort(col("Age").desc()).show()

# Sort by multiple columns
df.sort("Department", col("Salary").desc()).show()

# Limit results
df.limit(5).show()
df.sort("Salary").tail(3)
```

### DataFrame Operations

```python
# Distinct/Unique rows
df.distinct().show()

# Sample (fraction or count)
df.sample(fraction=0.5).show()  # 50% of data
df.sample(fraction=0.1, seed=42).show()

# Count rows
df.count()

# Repartition
df_repartitioned = df.repartition(4)

# Coalesce
df_coalesced = df.coalesce(1)

# Cache in memory
df.cache()
df.persist()

# Remove from cache
df.unpersist()

# Show execution plan
df.explain()
df.explain(True)

# Convert to Pandas
pandas_df = df.toPandas()

# Convert to dict
list_of_dicts = df.toJSON().collect()
```

### String Functions

```python
from pyspark.sql.functions import *

df.withColumn("Name_Upper", upper("Name")).show()
df.withColumn("Name_Lower", lower("Name")).show()
df.withColumn("Name_Length", length("Name")).show()
df.withColumn("Name_Substring", substring("Name", 1, 3)).show()
df.withColumn("Name_Concat", concat("FirstName", lit(" "), "LastName")).show()
df.withColumn("Trimmed", trim("Name")).show()
df.withColumn("Replaced", regexp_replace("Name", "a", "x")).show()
```

### Numeric Functions

```python
from pyspark.sql.functions import *

df.withColumn("Rounded", round("Salary", 2)).show()
df.withColumn("Ceil", ceil("Salary")).show()
df.withColumn("Floor", floor("Salary")).show()
df.withColumn("Absolute", abs("Value")).show()
df.withColumn("Power", pow("Value", 2)).show()
df.withColumn("Square_Root", sqrt("Value")).show()
```

### Date Functions

```python
from pyspark.sql.functions import *
from datetime import datetime

# Current date/timestamp
df.withColumn("Today", current_date()).show()
df.withColumn("Now", current_timestamp()).show()

# Parse date
df.withColumn("ParsedDate", to_date("DateString", "yyyy-MM-dd")).show()

# Format date
df.withColumn("FormattedDate", date_format("DateColumn", "dd-MM-yyyy")).show()

# Date arithmetic
df.withColumn("NextDay", date_add("DateColumn", 1)).show()
df.withColumn("DayDiff", datediff("Date2", "Date1")).show()

# Extract from date
df.withColumn("Year", year("DateColumn")).show()
df.withColumn("Month", month("DateColumn")).show()
df.withColumn("Day", dayofmonth("DateColumn")).show()
df.withColumn("Quarter", quarter("DateColumn")).show()
```

### Statistical Functions

```python
from pyspark.sql.functions import *

df.agg(
    count("*").alias("Count"),
    sum("Salary").alias("Total"),
    mean("Salary").alias("Mean"),
    min("Salary").alias("Min"),
    max("Salary").alias("Max"),
    stddev("Salary").alias("StdDev"),
    variance("Salary").alias("Variance")
).show()
```

### Writing Data

```python
# CSV
df.write.mode("overwrite").csv("output/path", header=True)

# Parquet
df.write.mode("overwrite").parquet("output/path")

# JSON
df.write.mode("overwrite").json("output/path")

# Modes: overwrite, append, ignore, error

# Single file
df.coalesce(1).write.mode("overwrite").csv("output/path", header=True)
```

## Tutorial Notebooks

### 1. pyspark_tut.ipynb
**Basic PySpark Operations**
- Initializing Spark Session
- Reading CSV data
- Viewing and exploring data
- Selecting columns
- Adding new columns
- Dropping and renaming columns
- Statistical summary

Topics covered:
```python
# Reading data
df = spark.read.csv("path/to/file.csv", header=True, inferSchema=True)

# Viewing data
df.show()
df.head(5)
df.printSchema()

# Selecting columns
df.select('column_name').show()
df.select(['col1', 'col2']).show()

# Adding columns
df = df.withColumn('new_col', df.existing_col * 2)

# Dropping columns
df = df.drop('column_to_drop')

# Renaming columns
df = df.withColumnRenamed('old_name', 'new_name')
```

### 2. pyspark_filter_operations.ipynb
**Filtering and Selecting Data**
- Basic filter operations
- Multiple conditions (AND, OR, NOT)
- Filtering with expressions
- Selecting specific columns after filtering
- Inverse filters

Topics covered:
```python
# Single condition
df.filter("Salary <= 20000").show()
df.filter(df.Salary <= 20000).show()

# Multiple conditions
df.filter((df.Salary <= 20000) & (df.Salary >= 15000)).show()

# Inverse filter
df.filter(~(df.Salary <= 20000)).show()

# Filter and select
df.filter(df.Salary <= 20000).select(['Name', 'Salary']).show()
```

### 3. pyspark_groupby_aggregation.ipynb
**GroupBy and Aggregation Operations**
- Groupby with sum
- Groupby with mean and count
- Multiple column groupby
- Using agg() function
- Common aggregation functions (sum, mean, min, max, count)

Topics covered:
```python
# Groupby with aggregation
df.groupby('Name').sum().show()
df.groupby('Department').mean().show()

# Count employees per department
df.groupby('Department').count().show()

# Using agg() for custom aggregations
df.agg({'Salary': 'sum'}).show()
df.groupby('Department').agg({'Salary': 'sum'}).show()
```

### 4. pyspark_handling_missing_values.ipynb
**Handling Missing and Null Values**
- Dropping rows with null values
- Dropping with threshold
- Dropping specific columns with nulls
- Filling missing values with constants
- Imputing with mean and median
- Using Imputer from ml.feature

Topics covered:
```python
# Drop rows
df.na.drop().show()  # Drop any null
df.na.drop(how='all').show()  # Drop all nulls
df.na.drop(thresh=2).show()  # At least 2 non-null

# Fill values
df.na.fill('Unknown').show()
df.na.fill(0, subset=['Age']).show()

# Imputation
from pyspark.ml.feature import Imputer
imputer = Imputer(
    inputCols=['Age', 'Salary'],
    outputCols=['Age_imputed', 'Salary_imputed']
).setStrategy('mean')
imputer.fit(df).transform(df).show()
```

### 5. pyspark_lr.ipynb
**Machine Learning: Linear Regression**
- Feature engineering with VectorAssembler
- Preparing data for ML models
- Train-test split
- Training linear regression model
- Making predictions
- Model evaluation (MAE, MSE)

Topics covered:
```python
# Feature engineering
from pyspark.ml.feature import VectorAssembler
assembler = VectorAssembler(
    inputCols=['Age', 'Experience'],
    outputCol='features'
)
df_features = assembler.transform(df)

# Train-test split
train_data, test_data = df_features.randomSplit([0.75, 0.25])

# Train model
from pyspark.ml.regression import LinearRegression
lr = LinearRegression(featuresCol='features', labelCol='Salary')
model = lr.fit(train_data)

# Make predictions
predictions = model.evaluate(test_data)
predictions.predictions.show()

# Evaluate
print(f"MAE: {predictions.meanAbsoluteError}")
print(f"MSE: {predictions.meanSquaredError}")
```

## Datasets

The repository includes sample datasets for practice:

- **Sample_data.csv**: Basic transaction data with account information
- **sample_data_3.csv**: Employee salary data for filtering operations
- **sample_data_groupby.csv**: Department and salary data for aggregations
- **sample_data_lr.csv**: Age, experience, and salary data for ML training
- **Sample_data_with_missing_values.csv**: Data with null/missing values for cleaning practice

## Common Use Cases

### Data Cleaning
```python
df = spark.read.csv("raw_data.csv", header=True, inferSchema=True)
df = df.na.drop()
df = df.dropDuplicates()
df.write.csv("cleaned_data.csv", header=True)
```

### Data Transformation
```python
from pyspark.sql.functions import *

df = df.withColumn("Amount_Category",
    when(df.Amount > 1000, "High")
    .when(df.Amount > 500, "Medium")
    .otherwise("Low"))
```

### Aggregation and Reporting
```python
report = df.groupby("Department").agg(
    count("*").alias("Count"),
    mean("Salary").alias("AvgSalary"),
    max("Salary").alias("MaxSalary")
)
report.show()
```

### Join Operations
```python
employees = spark.read.csv("employees.csv", header=True)
departments = spark.read.csv("departments.csv", header=True)

result = employees.join(departments, 
    on="department_id", 
    how="left")
result.show()
```

## Performance Tips

1. **Cache frequently accessed DataFrames**: Use `.cache()` for repeatedly used data
2. **Repartition strategically**: Optimize partition count based on cluster resources
3. **Use pushdown predicates**: Filter early in the pipeline
4. **Avoid shuffles**: Try to minimize join and groupby operations
5. **Use Parquet format**: Columnar storage is more efficient than CSV
6. **Broadcast small DataFrames**: For small lookup tables in joins
7. **Monitor execution plans**: Use `.explain()` to understand Spark operations

## References

- [Official PySpark Documentation](https://spark.apache.org/docs/latest/api/python/)
- [PySpark SQL Functions](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql.html)
- [Spark MLlib Guide](https://spark.apache.org/docs/latest/ml-guide.html)
- [PySpark on Windows Setup](https://spark.apache.org/docs/latest/index.html)

## Notes for Beginners

- Always create a SparkSession before processing data
- PySpark operations are lazy; they execute only when an action (`.show()`, `.collect()`, `.write`) is called
- Transformations (like `.select()`, `.filter()`) return new DataFrames; they don't modify the original
- Use meaningful variable names to track your data pipeline
- Save your processed data in efficient formats like Parquet
- Start with small datasets for testing before scaling to production
- Monitor memory usage with large datasets

---

Last Updated: 2024
For questions or contributions, refer to the official PySpark documentation and community forums.
