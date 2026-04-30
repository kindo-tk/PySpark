# PySpark Learning Repository

This repository serves as a structured, hands-on learning environment for Apache PySpark. It contains a comprehensive collection of Jupyter Notebooks and corresponding datasets designed to guide you through PySpark concepts, ranging from fundamental DataFrame operations to advanced machine learning pipelines. 

## Repository Structure

- `notebooks/`: Contains Jupyter Notebooks, each focusing on specific PySpark topics and operations.
- `datasets/`: Contains various CSV datasets utilized across the notebooks for practical exercises.
- `pyspark_setup.md`: A detailed guide on how to configure your local PySpark environment.

## Topics Covered and Notebook Mapping

The repository is divided into logical topics, each covered by a dedicated notebook and supported by specific datasets.

### 1. PySpark Fundamentals
- **Notebooks**: 
  - `notebooks/pyspark_basics.ipynb`
  - `notebooks/pyspark_tut.ipynb`
- **Topics**: Initializing a Spark Session, reading CSV data, viewing DataFrames, basic schema exploration, and selecting/dropping columns.
- **Datasets Used**: `datasets/transactions.csv`, `datasets/Sample_data.csv`

### 2. Data Manipulation and Transformations
- **Notebook**: `notebooks/pyspark_derived_features_typecasting.ipynb`
- **Topics**: Adding derived columns, typecasting data types, renaming columns, and applying column-level operations.
- **Datasets Used**: `datasets/transactions_v2.csv`

### 3. Data Filtering and Advanced Queries
- **Notebooks**: 
  - `notebooks/pyspark_filter_operations.ipynb`
  - `notebooks/pyspark_filtering_adv_queries.ipynb`
- **Topics**: Basic filtering, multiple logical conditions (AND/OR), inverse filters, string pattern matching, and complex querying.
- **Datasets Used**: `datasets/sample_data_3.csv`, `datasets/transactions.csv`

### 4. Handling Missing Data
- **Notebook**: `notebooks/pyspark_handling_missing_values.ipynb`
- **Topics**: Identifying nulls, dropping rows/columns with missing values based on thresholds, filling nulls with constant values, and employing imputation strategies (mean/median).
- **Datasets Used**: `datasets/Sample_data_with_missing_values.csv`, `datasets/transactions_missing.csv`

### 5. Aggregations and Grouping
- **Notebook**: `notebooks/pyspark_groupby_aggregation.ipynb`
- **Topics**: Using `groupBy`, applying standard aggregation functions (sum, mean, min, max, count), and using the `agg` function for custom aggregations.
- **Datasets Used**: `datasets/transactions_v3.csv`, `datasets/sample_data_groupby.csv`

### 6. Merging and Joins
- **Notebook**: `notebooks/pyspark_merge_joins.ipynb`
- **Topics**: Combining DataFrames using various join types including inner, outer, left, and right joins.
- **Datasets Used**: `datasets/banking/branches.csv`, `datasets/banking/customers.csv`, `datasets/banking/transactions.csv`, `datasets/banking/credit_scores.csv`, `datasets/banking/loans.csv`

### 7. Window Functions
- **Notebook**: `notebooks/pyspark_window_function.ipynb`
- **Topics**: Advanced analytical functions including partitioning, ordering within partitions, row numbering, ranking, dense ranking, lead, and lag operations.
- **Datasets Used**: `datasets/transactions_windows.csv`

### 8. Machine Learning: Feature Engineering Pipelines
- **Notebook**: `notebooks/feature_engineering_pipeline.ipynb`
- **Topics**: Preparing data for machine learning models using PySpark ML features such as `StringIndexer`, `VectorAssembler`, `OneHotEncoder`, and building robust ML pipelines.
- **Datasets Used**: Multiple datasets from the `datasets/banking/` directory and `datasets/transactions_windows.csv`

### 9. Machine Learning: Linear Regression
- **Notebook**: `notebooks/pyspark_lr.ipynb`
- **Topics**: Performing train-test splits, training Linear Regression models, making predictions, and evaluating model performance using metrics like MAE and MSE.
- **Datasets Used**: `datasets/sample_data_lr.csv`

## Setup Instructions

To get started with the notebooks, you will need a properly configured PySpark environment. Please refer to the [PySpark Setup Guide](pyspark_setup.md) for detailed, step-by-step instructions on:
- Creating a Conda environment
- Installing required packages
- Configuring the Jupyter kernel
- Installing and setting up Java
- Configuring environment variables

## Conclusion

This repository is intended to be worked through sequentially or used as a reference for specific PySpark operations. By following the notebooks and experimenting with the provided datasets, you will gain a strong, practical foundation in distributed data processing with Apache PySpark.
