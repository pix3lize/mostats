from pymongo import MongoClient
from urllib.parse import urlparse
import pandas as pd
import csv
import argparse
import sys
import os

output = []
cluster_stats = []

def main():

    argparser = argparse.ArgumentParser(description='Get the MongoDB database statistic '
                                                    'to a local CSV file')
    argparser.add_argument('-u', '--url', nargs='+', default="mongodb://127.0.0.1",
                            help='MongoDB cluster URL, default is "mongodb://127.0.0.1". \nExample: "mongodb+srv://<<username>>:<<password>>@cluster.zqqqy.mongodb.net/?retryWrites=true&w=majority". For multiple server please use the space and "" to seperate example:"mongodb+srv://<<username>>:<<password>>@cluster1.zqqqy.mongodb.net/?retryWrites=true&w=majority" "mongodb+srv://<<username>>:<<password>>@cluster2.zqqqy.mongodb.net/?retryWrites=true&w=majority" ')
    argparser.add_argument('-c', '--csv', default="cluster-data.csv",
                            help='CSV filename, default "cluster-data.csv" \n')
    argparser.add_argument('-n', '--name', nargs='+', default="",
                            help='Cluster name, default value first subdomain example: mongodb+srv://clustername.cl0.mongodb.net will be clustername. For multiple server please use the space and "" to seperate example:"cluster1" "cluster2"  \n')
    argparser.add_argument('-m', '--moreinfo', default=False,
                            help='Getting the host information, uptime, total number of command, read, and insert \n')
    args = argparser.parse_args()
    
    print('\nMostats - Get the MongoDB database statistic to a local CSV file\nPlease follow the instruction by run mostats -h\n')
    if args.name == "":
        print(f'Get the database information from : "{args.url}" and save to "{args.csv}"')
    else:
        print(f'Get the database information from : "{args.url}" with cluster name "{args.name}" and save to "{args.csv}"')
    print('\n')
    print("Please wait as it might take a while...")
    conn_pool = args.url
    more_info = args.moreinfo
    counter = 0    
    try:
        for conn in conn_pool:
            parsed_uri = urlparse(conn)
            if args.name == "":
                cluster_name = parsed_uri.hostname.split('.')[0]
            else:
                cluster_name = args.name[counter]
            client = MongoClient(conn)
            if more_info:               
                data = client.admin.command("hostInfo")
                cstat = {
                    "cluster_name" : cluster_name,
                    "hostname" : data["system"]["hostname"],
                    "memSizeMB" : data["system"]["memSizeMB"],
                    "numCores" : data["system"]["numCores"], 
                    "numPhysicalCores" : data["system"]["numPhysicalCores"],
                    "cpuArch" : data["system"]["cpuArch"]            
                }
                server_status = client.admin.command("serverStatus")

                cstat.update({
                    "uptime" : server_status["uptime"],
                    "opc_insert" : server_status["opcounters"]["insert"], 
                    "opc_query" : server_status["opcounters"]["query"],
                    "opc_update" : server_status["opcounters"]["update"],
                    "opc_delete" : server_status["opcounters"]["delete"], 
                    "opc_getmore" : server_status["opcounters"]["getmore"],
                    "opc_command" : server_status["opcounters"]["command"],
                    "est_insert_per_sec" : round((server_status["opcounters"]["insert"])/ server_status["uptime"],2),
                    "est_query_per_sec" : round((server_status["opcounters"]["query"])/ server_status["uptime"],2),
                    "est_update_per_sec" : round((server_status["opcounters"]["update"])/ server_status["uptime"],2),
                    "est_delete_per_sec" : round((server_status["opcounters"]["delete"])/ server_status["uptime"],2),
                    "est_getmore_per_sec" : round((server_status["opcounters"]["getmore"])/ server_status["uptime"],2),
                    "est_command_per_sec" : round((server_status["opcounters"]["command"])/ server_status["uptime"],2),           
                })
                cluster_stats.append(cstat)

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
            counter = counter + 1
            client.close()

        df = pd.json_normalize(output)
        df.to_csv(args.csv, quoting=csv.QUOTE_NONNUMERIC, index=False)
        if more_info:
            df = pd.json_normalize(cluster_stats)
            df.to_csv("cluster-info.csv", quoting=csv.QUOTE_NONNUMERIC, index=False)
        print("Getting cluster information - completed successfully")
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