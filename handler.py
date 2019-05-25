import os
import json
import boto3

DB_CLST_ARN = os.environ.get("DB_CLST_ARN")
SECRET_ARN = os.environ.get("SECRET_ARN")
DB_NAME = "test_db"
TABLE_NAME = "test_table"


create_db_sql = f"""
CREATE DATABASE IF NOT EXISTS `{DB_NAME}`;
"""

create_table_sql = f"""
CREATE TABLE IF NOT EXISTS `{TABLE_NAME}` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `content` TEXT DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT null DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
"""

select_sql = f"""
SELECT
    *
FROM
    `{TABLE_NAME}`
;
"""

insert_sql = """
INSERT INTO `{table_name}` (`content`)
VALUES ( "{content}" );
"""


def execute_sql(sql, db_exists=True):
    client = boto3.client('rds-data', region_name='us-east-1')
    args = {
        "awsSecretStoreArn": SECRET_ARN,
        "dbClusterOrInstanceArn": DB_CLST_ARN,
        "sqlStatements": sql
    }
    if db_exists:
        args['database'] = DB_NAME

    response = client.execute_sql(**args)
    return response


def setup(event, content):
    execute_sql(create_db_sql, db_exists=False)
    execute_sql(create_table_sql)
    for i in range(20):
        sql = insert_sql.format(table_name=TABLE_NAME, content=i)
        execute_sql(sql)

    return {
        "statusCode": 200,
        "body": "success"
    }

def index(event, context):
    response = execute_sql(select_sql)

    return {
        "statusCode": 200,
        "body": json.dumps(parse_aurora(response))
    }

def parse_aurora(response):
    metadata = response['sqlStatementResults'][0]['resultFrame']['resultSetMetadata']['columnMetadata']
    columns = [
        meta['name']
        for meta
        in metadata
    ]
    records = response['sqlStatementResults'][0]['resultFrame']['records']
    results = []
    
    for values in records:
        result = {}
        for c, v in zip(columns, values['values']):
            if v.get("isNull"):
                result[c] = None
            else:
                result[c] = list(v.values())[0]
        results.append(result)
    
    return results

def hello(event, content):
    return {
        "account_id": os.environ.get("TEST")
    }