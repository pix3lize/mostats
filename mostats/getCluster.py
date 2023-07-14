from pymongo import MongoClient
from urllib.parse import urlparse
import pandas as pd
import csv
import argparse
import sys
import os

output = []

def main():

    argparser = argparse.ArgumentParser(description='Get the MongoDB database statistic '
                                                    'to a local CSV file')
    argparser.add_argument('-u', '--url', default="mongodb://127.0.0.1",
                            help='MongoDB cluster URL, default is "mongodb://127.0.0.1". \nExample: mongodb+srv://<<username>>:<<password>>@cluster.zqqqy.mongodb.net/?retryWrites=true&w=majority')
    argparser.add_argument('-c', '--csv', default="cluster-data.csv",
                            help='CSV filename, default "cluster-data.csv" \n')
    argparser.add_argument('-n', '--name', default="",
                            help='Cluster name, default value first subdomain example: mongodb+srv://clustername.cl0.mongodb.net will be clustername \n')
    args = argparser.parse_args()
    
    print('\nMostats - Get the MongoDB database statistic to a local CSV file\nPlease follow the instruction by run mostats -h\n')

    print(f'Get the database information from : "{args.url}" and save to "{args.csv}"')
    print('\n')
    conn_pool = []
    conn_pool.append(args.url)
    try:
        for conn in conn_pool:
            parsed_uri = urlparse(conn)
            if args.name == "":
                cluster_name = parsed_uri.hostname.split('.')[0]
            else:
                cluster_name = args.name
            client = MongoClient(conn)
            for db in client.list_database_names():
                if db not in ["admin", "config", "local"]:
                    for coll in client[db].list_collections():
                        if (coll["name"] not in ["system.views"]) and (coll["type"] != "view"):
                            try:
                                avgObjSize = client[db].command(
                                    "collStats", coll["name"], scale=1024*1024)["avgObjSize"]
                            except KeyError:
                                avgObjSize = "N/A"
                            try:
                                num_doc = client[db].command(
                                    "collStats", coll["name"])["count"]
                            except KeyError:
                                num_doc = "N/A"
                            coll_stat = {
                                "cluster_name": cluster_name,
                                "db_name": db,
                                "coll_name": coll["name"],
                                "coll_size_MB": client[db].command("collStats", coll["name"], scale=1024*1024)["size"],
                                "avg_obj_size_Bytes": avgObjSize,
                                "num_doc": num_doc,
                                "storage_size_MB": client[db].command("collStats", coll["name"], scale=1024*1024)["storageSize"],
                                "num_idx": client[db].command("collStats", coll["name"])["nindexes"],
                                "idx_size_MB": client[db].command("collStats", coll["name"], scale=1024*1024)["totalIndexSize"],
                                "total_size_MB": client[db].command("collStats", coll["name"], scale=1024*1024)["totalSize"],
                            }
                            output.append(coll_stat)
            client.close()

        df = pd.json_normalize(output)
        df.to_csv(args.csv, quoting=csv.QUOTE_NONNUMERIC, index=False)
    except KeyboardInterrupt:
        shutdown()
    except Exception as e:
        print("Exception:", str(e))

def shutdown():
    print()

    try:
        sys.exit(0)
    except SystemExit as e:
        os._exit(0)

if __name__ == "__main__":
    main()