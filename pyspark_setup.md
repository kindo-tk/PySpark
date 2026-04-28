# PySpark Environment Setup (Windows + Conda + VS Code)

## 1. Prerequisites

-   Miniconda or Anaconda
-   Visual Studio Code
-   Python extension in VS Code

------------------------------------------------------------------------

## 2. Create Conda Environment

``` bash
conda create -n pyspark_env python=3.10 -y
conda activate pyspark_env
```

------------------------------------------------------------------------

## 3. Install Required Packages

``` bash
pip install pyspark jupyter ipykernel findspark
```

------------------------------------------------------------------------

## 4. Configure Jupyter Kernel

``` bash
python -m ipykernel install --user --name pyspark_env --display-name "PySpark (pyspark_env)"
```

------------------------------------------------------------------------

## 5. Java Installation and Configuration

### Recommended Version

Java 17 (LTS)

### Set JAVA_HOME

``` powershell
setx JAVA_HOME "C:\Program Files\Eclipse Adoptium\jdk-17.x.x"
```

### Update PATH

``` powershell
setx PATH "%JAVA_HOME%\bin;%PATH%"
```

Restart VS Code after setting variables.

------------------------------------------------------------------------

## 6. Configure PySpark Environment Variables

``` powershell
setx PYSPARK_PYTHON "python"
setx PYSPARK_DRIVER_PYTHON "python"
```

------------------------------------------------------------------------

## 7. Verify Installation

### Check Java

``` powershell
java -version
```

### Check Python Path

``` powershell
where python
```

------------------------------------------------------------------------

## 8. Test PySpark in Terminal

``` bash
python -c "from pyspark.sql import SparkSession; print('starting'); SparkSession.builder.master('local[1]').appName('test').getOrCreate(); print('done')"
```
