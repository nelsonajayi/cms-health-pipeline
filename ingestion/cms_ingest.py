"""
CMS Healthcare Data Ingestion Script
=====================================
This script reads CMS Medicare CSV files and loads them into Snowflake.

How it works:
1. Reads each CSV file into a pandas DataFrame
2. Cleans up column names to be Snowflake-compatible
3. Uses the Snowflake Python connector to load the data
4. Prints progress and row counts so you know it's working

Run this script from the project root directory:
    python ingestion/cms_ingest.py
"""

import os
import sys
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()


def get_snowflake_connection():
    """
    Create and return a connection to Snowflake.
    
    Reads credentials from environment variables so
    nothing sensitive is hardcoded in this file.
    
    Returns:
        snowflake.connector.connection: Active Snowflake connection
    """
    account = os.getenv('SNOWFLAKE_ACCOUNT')
    user = os.getenv('SNOWFLAKE_USER')
    password = os.getenv('SNOWFLAKE_PASSWORD')
    database = os.getenv('SNOWFLAKE_DATABASE')
    schema = os.getenv('SNOWFLAKE_SCHEMA')
    warehouse = os.getenv('SNOWFLAKE_WAREHOUSE')
    role = os.getenv('SNOWFLAKE_ROLE')
    
    # Check that all required variables are set
    missing = [var for var, val in {
        'SNOWFLAKE_ACCOUNT': account,
        'SNOWFLAKE_USER': user,
        'SNOWFLAKE_PASSWORD': password
    }.items() if not val]
    
    if missing:
        print(f"ERROR: Missing environment variables: {missing}")
        print("Make sure your .env file exists and has the right values.")
        sys.exit(1)
    
    print(f"Connecting to Snowflake account: {account}")
    
    conn = snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        database=database,
        schema=schema,
        warehouse=warehouse,
        role=role
    )
    
    print("Connected to Snowflake successfully.")
    return conn


def clean_column_names(df):
    """
    Standardize DataFrame column names for Snowflake compatibility.
    
    Snowflake column names:
    - Are uppercase by default
    - Cannot contain spaces (we replace with underscores)
    - Cannot start with numbers
    - Cannot contain special characters except underscore
    
    Args:
        df: pandas DataFrame with raw column names
        
    Returns:
        pandas DataFrame with cleaned column names
    """
    df.columns = (
        df.columns
        .str.strip()                    # Remove leading/trailing spaces
        .str.upper()                    # Make uppercase
        .str.replace(' ', '_')          # Replace spaces with underscores
        .str.replace('-', '_')          # Replace hyphens with underscores
        .str.replace('(', '')           # Remove parentheses
        .str.replace(')', '')
        .str.replace('.', '_')          # Replace dots with underscores
        .str.replace('/', '_PER_')      # Replace slashes
        .str.replace('%', '_PCT')       # Replace percent signs
        .str.replace('#', 'NUM')        # Replace hash with NUM
        .str.replace('__', '_')         # Clean up double underscores
    )
    return df


def load_csv_to_snowflake(filepath, table_name, conn, encoding='utf-8'):
    """
    Load a CSV file into a Snowflake table.
    
    Args:
        filepath (str): Path to the CSV file
        table_name (str): Name of the Snowflake table to load into
        conn: Active Snowflake connection
        encoding (str): File encoding - use 'latin-1' if utf-8 fails
        
    Returns:
        int: Number of rows loaded
    """
    print(f"\n--- Loading {os.path.basename(filepath)} ---")
    
    if not os.path.exists(filepath):
        print(f"  WARNING: File not found: {filepath}")
        print(f"  Skipping this dataset.")
        return 0
    
    # Get file size for progress indication
    file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"  File size: {file_size_mb:.1f} MB")
    print(f"  Reading CSV... (this may take a moment for large files)")
    
    # Read the CSV
    # dtype=str reads everything as strings — prevents type inference errors
    # We let dbt handle type casting later
    try:
        df = pd.read_csv(
            filepath,
            dtype=str,
            encoding=encoding,
            low_memory=False
        )
    except UnicodeDecodeError:
        print(f"  UTF-8 failed, trying latin-1 encoding...")
        df = pd.read_csv(
            filepath,
            dtype=str,
            encoding='latin-1',
            low_memory=False
        )
    
    print(f"  Rows read: {len(df):,}")
    print(f"  Columns: {len(df.columns)}")
    
    # Clean column names
    df = clean_column_names(df)
    print(f"  Column names cleaned")
    
    # Replace NaN with None so Snowflake inserts NULL
    df = df.where(pd.notna(df), None)
    
    print(f"  Loading to Snowflake table: {table_name}")
    
    # write_pandas is Snowflake's optimized bulk loader
    success, num_chunks, num_rows, output = write_pandas(
        conn=conn,
        df=df,
        table_name=table_name,
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema=os.getenv('SNOWFLAKE_SCHEMA'),
        auto_create_table=False,    # We already created the table
        overwrite=True,             # Replace existing data
        chunk_size=10000            # Load in batches of 10,000 rows
    )
    
    if success:
        print(f"  Successfully loaded {num_rows:,} rows")
    else:
        print(f"  ERROR: Load failed")
        print(f"  Output: {output}")
    
    return num_rows


def verify_loads(conn):
    """
    Verify the data loaded correctly by counting rows in each table.
    
    Args:
        conn: Active Snowflake connection
    """
    print("\n--- Verifying Data Loads ---")
    
    tables = [
        'RAW_HOSPITAL_READMISSIONS',
        'RAW_DRUG_PRESCRIBING',
        'RAW_PROVIDER_ENROLLMENT'
    ]
    
    cursor = conn.cursor()
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM CMS_HEALTH.RAW.{table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count:,} rows")
        except Exception as e:
            print(f"  {table}: ERROR - {e}")
    
    cursor.close()


def run_ingestion():
    """
    Main ingestion function.
    
    Loads all three CMS datasets into Snowflake.
    Run this to refresh all data.
    """
    print("=" * 50)
    print("CMS Healthcare Pipeline — Data Ingestion")
    print("=" * 50)
    
    # Connect to Snowflake
    conn = get_snowflake_connection()
    
    try:
        # Define which files map to which tables
        datasets = [
            {
                'filepath': 'ingestion/data/hospital_readmissions.csv',
                'table': 'RAW_HOSPITAL_READMISSIONS'
            },
            {
                'filepath': 'ingestion/data/drug_prescribing.csv',
                'table': 'RAW_DRUG_PRESCRIBING'
            },
            {
                'filepath': 'ingestion/data/provider_enrollment.csv',
                'table': 'RAW_PROVIDER_ENROLLMENT'
            }
        ]
        
        total_rows = 0
        
        for dataset in datasets:
            rows = load_csv_to_snowflake(
                filepath=dataset['filepath'],
                table_name=dataset['table'],
                conn=conn
            )
            total_rows += rows
        
        print(f"\n{'=' * 50}")
        print(f"Ingestion complete. Total rows loaded: {total_rows:,}")
        
        # Verify the loads
        verify_loads(conn)
        
    except Exception as e:
        print(f"\nERROR during ingestion: {e}")
        raise
        
    finally:
        conn.close()
        print("\nSnowflake connection closed.")


if __name__ == "__main__":
    run_ingestion()