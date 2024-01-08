from pymongo import MongoClient
from urllib.parse import urlparse
import pandas as pd
import argparse
import sys
import os
from openpyxl import load_workbook
import datetime
import traceback
from openpyxl.styles import numbers
import numpy as np


output = []
cluster_stats = []
db_sizing = []
cluster_index_info = []


def main():

    argparser = argparse.ArgumentParser(description='Get the MongoDB database statistic '
                                                    'to an excel file')
    argparser.add_argument('-u', '--url', nargs='+', default="mongodb://127.0.0.1",
                           help='MongoDB cluster URL, default is "mongodb://127.0.0.1". \nExample: "mongodb+srv://<<username>>:<<password>>@cluster.zqqqy.mongodb.net/?retryWrites=true&w=majority". For multiple server please use the space and "" to seperate example:"mongodb+srv://<<username>>:<<password>>@cluster1.zqqqy.mongodb.net/?retryWrites=true&w=majority" "mongodb+srv://<<username>>:<<password>>@cluster2.zqqqy.mongodb.net/?retryWrites=true&w=majority" ')
    argparser.add_argument('-uf', '--urlfile', default="",
                           help='Get the MongoDB cluster URL from a file. It will read each line as one MongoDB cluster URL')
    argparser.add_argument('-e', '--excelfile', default="Cluster-info.xlsx",
                           help='Excel filename, default "Cluster-info.xlsx" \n')
    argparser.add_argument('-n', '--name', nargs='+', default="",
                           help='Cluster name, default value first subdomain example: mongodb+srv://clustername.cl0.mongodb.net will be clustername. For multiple server please use the space and "" to seperate example:"cluster1" "cluster2"  \n')
    argparser.add_argument('-nf', '--namefile', default="",
                           help='Get the cluster name from a file. It will read each line as one cluster name \n')
    argparser.add_argument('-m', '--moreinfo', default=False,
                           help='Getting the host information, uptime, total number of command, read, and insert \n')
    argparser.add_argument('-fa', '--fa', default="",
                           help='Frequently access ratio in percent (input number only)\n')
    argparser.add_argument('-p', '--percentile', default=70,
                           help='Specify the percentile based on how much the index is used to calculate total number of index for CPU requirement calculation. Default is 70\n')
    argparser.add_argument('-iops', '--iops', default="",
                           help='Expected IOPS\n')
    argparser.add_argument('-debug', '--debug', default=False,
                           help='Throw raw JSON information\n')
    args = argparser.parse_args()

    print('\nMostats - Get the MongoDB database statistic to an excel file\nPlease follow the instruction by run mostats -h\n')

    if args.urlfile != "":
        conn_pool = read_file(args.urlfile)
    else:
        conn_pool = args.url

    if args.namefile != "":
        cname = read_file(args.namefile)
        if (len(conn_pool) != len(cname)) and (len(cname) > 0):
            raise Exception(
                f'The number of MongoDB URL "{len(conn_pool)}" doesnt match with the number of cluster name "{len(cname)}"')
    elif args.name != "":
        cname = args.name
        if (len(conn_pool) != len(cname)) and (len(cname) > 0):
            raise Exception(
                f'The number of MongoDB URL "{len(conn_pool)}" doesnt match with the number of cluster name "{len(cname)}"')

    if args.name == "":
        print(
            f'Get the database information from : "{conn_pool}" and save to "{args.excelfile}"')
    else:
        print(
            f'Get the database information from : "{conn_pool}" with cluster name "{args.name}" and save to "{args.excelfile}"')
    # print('\n')
    print('\nPlease wait as it might take a while...')

    more_info = args.moreinfo
    counter = 0

    try:
        for conn in conn_pool:
            print(
                f'Getting database information from {conn}. Progress: {counter+1}/{len(conn_pool)}')
            totalindex = 0
            totalindexsize = 0
            totaluniqueindex = 0
            frequentlyaccess = 0
            totaldocuments = 0
            totalstoragesize = 0
            totalsize = 0
            parsed_uri = urlparse(conn)
            if args.name == "":
                cluster_name = parsed_uri.hostname.split('.')[0]
            else:
                cluster_name = cname[counter]
            client = MongoClient(conn)
            if more_info:
                data = client.admin.command("hostInfo")

                cstat = {
                    "Cluster name": cluster_name,
                    "Hostname": data["system"]["hostname"],
                    "Memory size(MB)": data["system"]["memSizeMB"],
                    "CPU Cores": data["system"]["numCores"],
                    "CPU arch": data["system"]["cpuArch"]
                }
                data = client.server_info()['version']
                cstat.update({
                    "MongoDB version": data
                })

                try:
                    data = client.admin.command("getShardMap")["map"]
                    nodes = 0
                    config = 0
                    for x in data:
                        # print(x)
                        if (x != "config"):
                            nodes += len(data[x].split(","))
                        else:
                            config += len(data[x].split(","))
                    shardinfo = f'{len(data) -1} Shard(s) {nodes} nodes with {config} nodes Config'
                    cstat.update({
                        "Config": shardinfo
                    })
                except Exception as e:
                    pass
                try:
                    data = client.admin.command("replSetGetStatus")
                    nodes = len(data["members"])
                    primary = 0
                    secondary = 0
                    arbiter = 0

                    for x in data["members"]:
                        if (x["stateStr"] == "SECONDARY"):
                            secondary += 1
                        elif (x["stateStr"] == "PRIMARY"):
                            primary += 1
                        elif (x["stateStr"] == "ARBITER"):
                            arbiter += 1

                    replinfo = f'{nodes} member(s) : {primary} primary, {secondary} secondary, {arbiter} arbiter'
                    cstat.update({
                        "Config": replinfo
                    })
                except Exception as e:
                    pass

                server_status = client.admin.command("serverStatus")
                cstat.update({
                    "Uptime": server_status["uptime"],
                    "Opc insert": server_status["opcounters"]["insert"],
                    "Opc query": server_status["opcounters"]["query"],
                    "Opc update": server_status["opcounters"]["update"],
                    "Opc delete": server_status["opcounters"]["delete"],
                    "Opc getmore": server_status["opcounters"]["getmore"],
                    "Opc command": server_status["opcounters"]["command"],
                    "Est insert per sec": 0 if server_status["uptime"] <= 0 else round((server_status["opcounters"]["insert"]) / server_status["uptime"], 2),
                    "Est query per sec": 0 if server_status["uptime"] <= 0 else round((server_status["opcounters"]["query"]) / server_status["uptime"], 2),
                    "Est update per sec": 0 if server_status["uptime"] <= 0 else round((server_status["opcounters"]["update"]) / server_status["uptime"], 2),
                    "Est delete per sec": 0 if server_status["uptime"] <= 0 else round((server_status["opcounters"]["delete"]) / server_status["uptime"], 2),
                    "Est getmore per sec": 0 if server_status["uptime"] <= 0 else round((server_status["opcounters"]["getmore"]) / server_status["uptime"], 2),
                    "Est command per sec": 0 if server_status["uptime"] <= 0 else round((server_status["opcounters"]["command"]) / server_status["uptime"], 2),
                })
                total_operation_sec = cstat["Est insert per sec"] + cstat["Est query per sec"] + (cstat["Est update per sec"] * 2) + (
                    cstat["Est delete per sec"] * 2) + cstat["Est getmore per sec"] + cstat["Est command per sec"]
                cstat.update({
                    "Est total ops per sec": total_operation_sec
                })

                cluster_stats.append(cstat)
                index_info = []
            for db in client.list_database_names():
                if db not in ["admin", "config", "local"]:
                    for coll in client[db].list_collections():
                        if (coll["name"] not in ["system.views"]) and (coll["type"] != "view"):
                            try:
                                avgObjSize = client[db].command(
                                    "collStats", coll["name"], scale=1024 * 1024)["avgObjSize"]
                            except KeyError:
                                avgObjSize = 0
                            try:
                                num_doc = client[db].command(
                                    "collStats", coll["name"])["count"]
                            except KeyError:
                                num_doc = 0
                            try:
                                total_size = client[db].command(
                                    "collStats", coll["name"], scale=1024 * 1024)["totalSize"]
                            except Exception as e:
                                total_size = 0

                            collStat = client[db].command(
                                "collStats", coll["name"], scale=1024 * 1024)
                            try:
                                cache_ratio = 0
                                if (collStat['wiredTiger']['cache']['pages requested from the cache'] != 0 and collStat['wiredTiger']['cache']['pages read into cache'] != 0):
                                    cache_ratio = round(100 - (collStat['wiredTiger']['cache']['pages read into cache']
                                                        * 100 / collStat['wiredTiger']['cache']['pages requested from the cache']), 2)
                            except Exception as e:
                                pass

                            coll_stat = {
                                "Cluster name": cluster_name,
                                "Database name": db,
                                "Collection name": coll["name"],
                                "Collection size(MB)": collStat["size"],
                                "Collection size(GB)": round(collStat["size"] / 1024, 2),
                                "Average object size(Bytes)": avgObjSize,
                                "Total number of document": num_doc,
                                "Storage size(MB)": collStat["storageSize"],
                                "Storage size(GB)": round(collStat["storageSize"] / 1024, 2),
                                "Total number of index": client[db].command("collStats", coll["name"])["nindexes"],
                                "Total index size(MB)": round(client[db].command("collStats", coll["name"], scale=1024)["totalIndexSize"] / 1024, 5),
                                "Total index size(GB)": round(collStat["totalIndexSize"] / 1024, 5),
                                "Total size(MB)": total_size,
                                "Total size(GB)": round(total_size / 1024, 2),
                                "Cache hit ratio": cache_ratio
                            }
                            if more_info:
                                pipeline = [{'$indexStats': {}}]

                                collection_name = coll["name"]
                                try:
                                    result = list(
                                        client[db][collection_name].aggregate(pipeline))

                                    indexsizes = client[db].command(
                                        "collStats", coll["name"], scale=1024)["indexSizes"]
                                    index_array = []
                                    for y in result:
                                        index_array.append(str(y["key"])[1:-1])

                                    for i in result:
                                        number_of_days = (
                                            datetime.datetime.utcnow() - i["accesses"]["since"])
                                        total_seconds = number_of_days.total_seconds()

                                        # Calculate the number of days (86400 seconds in a day)
                                        days = int(total_seconds // 86400)
                                        # Calculate the remaining hours
                                        hours = int(
                                            (total_seconds % 86400) // 3600)

                                        formatted_time = f"{days} day(s) and {hours} hour(s)"

                                        if number_of_days.days > 0:
                                            ops_perday = i["accesses"]["ops"] / (
                                                datetime.datetime.utcnow() - i["accesses"]["since"]).days
                                        else:
                                            ops_perday = 0
                                        index_stats = {
                                            "Cluster name": cluster_name,
                                            "Database name": db,
                                            "Collection name": coll["name"],
                                            "Index name": i["name"],
                                            "Index key": i["key"],
                                            "Index size (MB)": round(indexsizes[i["name"]] / 1024, 5),
                                            "Ops counter": i["accesses"]["ops"],
                                            "No of day since start/created": formatted_time,
                                            "Ops per day": ops_perday,
                                            "Duplicate": is_subset_of_any(str(i["key"])[1:-1], index_array)
                                        }
                                        index_info.append(index_stats)
                                except Exception as e:
                                    pass
                                    # traceback.print_tb(e.__traceback__)
                                    # print("Exception:", str(e))
                                totalindex += coll_stat["Total number of index"]
                                if coll_stat["Total number of index"] != 0:
                                    totaluniqueindex += coll_stat["Total number of index"] - 1
                                if args.fa != "":
                                    frequentlyaccess += ((int(args.fa) / 100) * (
                                        coll_stat["Average object size(Bytes)"] * coll_stat["Total number of document"]))
                                totalindexsize += coll_stat["Total index size(GB)"]
                                totaldocuments += coll_stat["Total number of document"]
                                totalstoragesize += coll_stat["Storage size(MB)"]
                                totalsize += coll_stat["Collection size(MB)"]
                            output.append(coll_stat)

            counter = counter + 1
            client.close()

            if more_info:
                index_info = sorted(index_info, key=lambda x: (
                    x['Ops counter']), reverse=True)
                total_index_run = 0
                percentile_indexcounter = 0
                temp_count = 0

                for i in index_info:
                    total_index_run += i["Ops counter"]

                for i in index_info:
                    percentile_indexcounter += 1
                    temp_count += i["Ops counter"]
                    if (temp_count >= (total_index_run * (int(args.percentile) / 100))):
                        break

                cluster_index_info.extend(index_info)
                if args.fa != "":
                    cstat.update({
                        # converting from bytes to kb to mb to gb
                        "Frequently access file(GB)": round((frequentlyaccess / 1024) / 1024 / 1024, 2)
                    })

                cstat.update({
                    "Total number of index": totalindex,
                    "Total unique index": totaluniqueindex,
                    "Total index size(GB)": totalindexsize,
                    "Total number of document": totaldocuments,
                    "Storage size(MB)": totalstoragesize,
                    "Total size(MB)": totalsize,
                    "Estimate compression ratio(%)": 0 if totalsize <= 0 else round(((totalsize - totalstoragesize) / totalsize) * 100, 2)
                })

                if args.fa != "":
                    if args.iops != "":
                        recommendcpu = round(
                            (args.iops / (12500) * ((1 - 0.05) ** cstat["Total unique index"])), 5)
                    else:
                        recommendcpu = round(
                            (cstat["Est total ops per sec"] / ((12500) * ((1 - 0.05) ** cstat["Total unique index"]))), 5)
                    if args.iops != "":
                        recommendcpu_precentile = round(
                            (args.iops / (12500) * ((1 - 0.05) ** percentile_indexcounter)), 5)
                    else:
                        recommendcpu_precentile = round(
                            (cstat["Est total ops per sec"] / ((12500) * ((1 - 0.05) ** percentile_indexcounter))), 5)

                    totalindex_percent_string = f"Total index({args.percentile}%)"
                    recommend_cpu_string = f"Recommended CPU core ({args.percentile}%)"
                    dbs = {
                        "Cluster name": str(cstat["Cluster name"]),
                        "Hostname": cstat["Hostname"],
                        "Memory size(GB)": round(cstat["Memory size(MB)"] / 1024, 2),
                        "CPU Cores": cstat["CPU Cores"],
                        "Required harddisk size(GB)": round(cstat["Storage size(MB)"] / 1024, 2),
                        "Recommended memory(GB)": round(((cstat["Frequently access file(GB)"] + cstat["Total index size(GB)"]) * 2), 2),
                        "Recommended CPU core ": recommendcpu,
                        totalindex_percent_string: percentile_indexcounter,
                        recommend_cpu_string: recommendcpu_precentile
                    }
                    db_sizing.append(dbs)

        if (len(output) > 0):
            write_json_to_excel(output, "temp.xlsx", "Cluster Data")
        else:
            print('Datbase collection is empty!\r\n')

        if more_info:
            if (len(cluster_index_info) > 0):
                write_json_to_excel(cluster_index_info,
                                    "temp.xlsx", "Index Data")
            else:
                print('Cluster index info is empty!\r\n')

            if (len(cluster_stats) > 0):
                write_json_to_excel(cluster_stats, "temp.xlsx", "Cluster Info")
            else:
                print('Cluster stats is empty!\r\n')

        if args.fa != "":
            if (len(db_sizing) > 0):
                write_json_to_excel(db_sizing, "temp.xlsx", "Cluster Sizing")
            else:
                print('Cluster sizing is empty!\r\n')

        if (args.debug):
            debug()

        if file_exists("temp.xlsx"):
            create_autofilter(args.excelfile)

        if file_exists("temp.xlsx"):
            # Delete the file
            os.remove("temp.xlsx")

        print('\nGetting all databases information - completed successfully')
    except KeyboardInterrupt:
        shutdown()
    except Exception as e:
        traceback.print_tb(e.__traceback__)
        print("Exception:", str(e))


def print_obj_json(object, filename):
    df = pd.DataFrame(object)

# Convert DataFrame to JSON
    json_data = df.to_json(orient='records')

    print(json_data)
    print('\r\n')
    with open(filename, 'w') as file:
        file.write(json_data)


def write_json_to_excel(json_data, output_file, worksheet):
    # Convert JSON data to a pandas DataFrame
    df = pd.DataFrame(json_data)

    if file_exists(output_file):
        with pd.ExcelWriter(output_file, engine='openpyxl', mode='a', if_sheet_exists="replace") as writer:
            # Write the data to the specified sheet
            df.to_excel(writer, sheet_name=worksheet, index=False)

    else:
        df.to_excel(output_file, sheet_name=worksheet, index=False)

    # Load the Excel file
    workbook = load_workbook(output_file)

    # Get the active sheet (change the sheet name if needed)
    sheet = workbook[worksheet]

    # Save the modified workbook
    workbook.save(output_file)
    workbook.close()


def create_autofilter(file_path):
    try:
        xl = pd.ExcelFile("temp.xlsx")

        # Create a new Excel writer with XlsxWriter engine
        writer = pd.ExcelWriter(file_path, engine="xlsxwriter")

        # Iterate over each sheet in the file
        for sheet_name in xl.sheet_names:
            # Read the sheet into a DataFrame
            df = xl.parse(sheet_name)

            # Write the DataFrame to the Excel writer
            df.to_excel(writer, sheet_name=sheet_name, index=False)

            # Get the worksheet object
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]

            # Add autofilter to the worksheet
            num_rows, num_cols = df.shape
            worksheet.autofilter(0, 0, num_rows, num_cols - 1)

            # Auto adjust column widths
            for i, column in enumerate(df.columns):
                column_width = max(df[column].astype(
                    str).map(len).max(), len(column))
                worksheet.set_column(i, i, column_width + 2)

            # Apply number format to whole numbers
            number_format = workbook.add_format({'num_format': '#,##0'})
            number_format2 = workbook.add_format({'num_format': '#,##0.00'})
            for row in range(1, num_rows + 1):
                for col in range(num_cols):
                    cell_value = df.iat[row - 1, col]
                    if isinstance(cell_value, np.int64):
                        worksheet.write_number(
                            row, col, cell_value, number_format)
                    elif isinstance(cell_value, np.float64):
                        worksheet.write_number(
                            row, col, cell_value, number_format2)

        xl.close()
        # Save the modified Excel file
        writer.close()

    except Exception as e:
        pass


def debug():
    print('Database colelctions : \r\n --------------')
    print_obj_json(output, "database_collections.json")

    print('Cluster index info : \r\n --------------')
    print_obj_json(cluster_index_info, "cluster_index_info.json")

    print('Cluster Statistic : \r\n --------------')
    print_obj_json(cluster_stats, "cluster_stats.json")

    print('DB Sizing : \r\n --------------')
    print_obj_json(db_sizing, "db_sizing.json")


def file_exists(file_path):
    return os.path.isfile(file_path)


def read_file(file_path):
    lines = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            lines.append(line)
    return lines


def is_subset(str1, str2):
    """Check if str1 is a subset of str2."""
    values1 = set(str1.split(','))
    values2 = set(str2.split(','))

    return values1 != values2 and values1.issubset(values2)


def is_subset_of_any(str1, strings):
    """Check if str1 is a subset of any string in the array."""
    for s in strings:
        if is_subset(str1, s):
            return "True"
    return "False"


def shutdown():
    print()

    try:
        sys.exit(0)
    except SystemExit as e:
        os._exit(0)


if __name__ == "__main__":
    main()
