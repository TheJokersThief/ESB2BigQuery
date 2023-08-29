import os
from google.cloud import bigquery

from esbdata.util import divide_chunks

BIGQUERY_DB = os.getenv("ESB_BIGQUERY_DB")

class BigQuery():
    def __init__(self):
        self.table_id = BIGQUERY_DB
        self.client = bigquery.Client()

    def insert_rows(self, rows):
        if len(rows) > 1000:
            for chunk in divide_chunks(rows, 1000):
                self.insert_rows(chunk)
        else:
            errors = self.client.insert_rows_json(
                self.table_id, rows
            )
            if errors == []:
                print(f"{len(rows)} rows have been added.")
            else:
                print("Encountered errors while inserting rows: {}".format(errors))
                raise Exception(errors)
