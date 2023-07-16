from pymongo import MongoClient
from urllib.parse import urlparse
import pandas as pd
import csv
import argparse
import sys
import os
from openpyxl import load_workbook

output = []
cluster_stats = []
db_sizing = []

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
    argparser.add_argument('-iops', '--iops', default="",
                            help='Expected IOPS\n')
    args = argparser.parse_args()
    
    print('\nMostats - Get the MongoDB database statistic to an excel file\nPlease follow the instruction by run mostats -h\n')
    
    if args.urlfile != "":
        conn_pool = read_file(args.urlfile)          
    else: 
        conn_pool = args.url

    if args.namefile != "":
        cname = read_file(args.namefile)
        if(len(conn_pool) != len(cname)) and (len(cname) >0 ):
            raise Exception(f'The number of MongoDB URL "{len(conn_pool)}" doesnt match with the number of cluster name "{len(cname)}"')
    elif args.name != "": 
        cname = args.name
        if(len(conn_pool) != len(cname)) and (len(cname) >0 ):
            raise Exception(f'The number of MongoDB URL "{len(conn_pool)}" doesnt match with the number of cluster name "{len(cname)}"')

    if args.name == "":
        print(f'Get the database information from : "{conn_pool}" and save to "{args.excelfile}"')
    else:
        print(f'Get the database information from : "{conn_pool}" with cluster name "{args.name}" and save to "{args.excelfile}"')
    #print('\n')
    print('\nPlease wait as it might take a while...')

    more_info = args.moreinfo
    counter = 0    
    
    try:
        for conn in conn_pool:
            print(f'Getting database information from {conn}. Progress: {counter+1}/{len(conn_pool)}')
            totalindex = 0
            totalindexsize =0
            totaluniqueindex =0
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
                    "Cluster name" : cluster_name,
                    "Hostname" : data["system"]["hostname"],
                    "Memory size(MB)" : data["system"]["memSizeMB"],
                    "CPU Cores" : data["system"]["numCores"], 
                    "CPU physicalCores" : data["system"]["numPhysicalCores"],
                    "CPU arch" : data["system"]["cpuArch"]            
                }
                server_status = client.admin.command("serverStatus")  
                cstat.update({
                    "Uptime" : server_status["uptime"],
                    "Opc insert" : server_status["opcounters"]["insert"], 
                    "Opc query" : server_status["opcounters"]["query"],
                    "Opc update" : server_status["opcounters"]["update"],
                    "Opc delete" : server_status["opcounters"]["delete"], 
                    "Opc getmore" : server_status["opcounters"]["getmore"],
                    "Opc command" : server_status["opcounters"]["command"],
                    "Est insert per sec" : 0 if server_status["uptime"] <=0 else round((server_status["opcounters"]["insert"])/ server_status["uptime"],2),
                    "Est query per sec" : 0 if server_status["uptime"] <=0 else round((server_status["opcounters"]["query"])/ server_status["uptime"],2),
                    "Est update per sec" : 0 if server_status["uptime"] <=0 else round((server_status["opcounters"]["update"])/ server_status["uptime"],2),
                    "Est delete per sec" : 0 if server_status["uptime"] <=0 else round((server_status["opcounters"]["delete"])/ server_status["uptime"],2),
                    "Est getmore per sec" : 0 if server_status["uptime"] <=0 else round((server_status["opcounters"]["getmore"])/ server_status["uptime"],2),
                    "Est command per sec" : 0 if server_status["uptime"] <=0 else round((server_status["opcounters"]["command"])/ server_status["uptime"],2),           
                })
                total_operation_sec = cstat["Est insert per sec"] + cstat["Est query per sec"] + (cstat["Est update per sec"] *2) + (cstat["Est delete per sec"] *2) + cstat["Est getmore per sec"] + cstat["Est command per sec"]
                cstat.update({
                    "Est total ops per sec" : total_operation_sec
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
                                avgObjSize = 0
                            try:
                                num_doc = client[db].command(
                                    "collStats", coll["name"])["count"]
                            except KeyError:
                                num_doc = 0
                            coll_stat = {
                                "Cluster name": cluster_name,
                                "Database name": db,
                                "Collection name": coll["name"],
                                "Collection size(MB)": client[db].command("collStats", coll["name"], scale=1024*1024)["size"],
                                "Average object size(Bytes)": avgObjSize,
                                "Total number of document": num_doc,
                                "Storage size(MB)": client[db].command("collStats", coll["name"], scale=1024*1024)["storageSize"],
                                "Total number of index": client[db].command("collStats", coll["name"])["nindexes"],
                                "Total index size(MB)": client[db].command("collStats", coll["name"], scale=1024*1024)["totalIndexSize"],
                                "Total size(MB)": client[db].command("collStats", coll["name"], scale=1024*1024)["totalSize"],
                            }
                            if more_info:
                                totalindex += coll_stat["Total number of index"]
                                if coll_stat["Total number of index"] != 0:
                                    totaluniqueindex += coll_stat["Total number of index"] -1
                                if args.fa != "":
                                    frequentlyaccess = ((int(args.fa) /100) * (coll_stat["Average object size(Bytes)"]* coll_stat["Total number of document"]))
                                totalindexsize += coll_stat["Total index size(MB)"]
                                totaldocuments += coll_stat["Total number of document"]
                                totalstoragesize += coll_stat["Storage size(MB)"]
                                totalsize += coll_stat["Total size(MB)"]                                
                            output.append(coll_stat)                                                                                 
            counter = counter + 1
            client.close()
            if more_info:
                    if args.fa != "":
                        cstat.update({  
                            "Frequently access file(MB)" :frequentlyaccess
                        })
                
                    cstat.update({
                        "Total number of index" : totalindex,
                        "Total unique index" : totaluniqueindex,
                        "Total index size(MB)" : totalindexsize,
                        "Total number of document" : totaldocuments,
                        "Storage size(MB)" : totalstoragesize,
                        "Total size(MB)" : totalsize,
                        "Estimate compression ratio(%)" : 0 if totalsize <= 0 else round(((totalsize-totalstoragesize)/totalsize) *100,2)
                    })
                         
                    if args.fa != "":                        
                        if args.iops != "":
                            recommendcpu = round((args.iops / (12500) * ((1-0.05) ** cstat["Total unique index"])),5)
                        else:
                            recommendcpu = round((cstat["Est total ops per sec"] / ((12500) * ((1-0.05) ** cstat["Total unique index"]))),5)                                                
                        dbs = {
                            "Cluster name" : str(cstat["Cluster name"]),
                            "Hostname" : cstat["Hostname"],
                            "Memory size(GB)" : round(cstat["Memory size(MB)"]/1024,2),
                            "CPU Cores" : cstat["CPU Cores"], 
                            "CPU physicalCores" : cstat["CPU physicalCores"],
                            "Required harddisk size(GB)" : round(cstat["Storage size(MB)"]/1024,2),
                            "Recommended memory(GB)" : round(((cstat["Frequently access file(MB)"] + cstat["Total index size(MB)"]) *2)/1024,2),
                            "Recommended CPU core" : recommendcpu
                        }
                        db_sizing.append(dbs)  

        write_json_to_excel(output, args.excelfile, "Cluster Data")

        if more_info:
            write_json_to_excel(cluster_stats, args.excelfile, "Cluster Info")

        if args.fa != "":                  
            write_json_to_excel(db_sizing, args.excelfile, "Cluster Sizing")

        print('\nGetting all databases information - completed successfully')
    except KeyboardInterrupt:
        shutdown()
    except Exception as e:
        print("Exception:", str(e))

def write_json_to_excel(json_data, output_file, worksheet):
    # Convert JSON data to a pandas DataFrame
    df = pd.DataFrame(json_data)

    if file_exists(output_file):   
        with pd.ExcelWriter(output_file, engine='openpyxl', mode='a', if_sheet_exists="replace") as writer:
            # Write the data to the specified sheet
            df.to_excel(writer, sheet_name=worksheet, index=False)
            
    else: 
        df.to_excel(output_file, sheet_name=worksheet, index=False)

    # Load the workbook
    workbook = load_workbook(output_file)

    # Access the active worksheet
    worksheet = workbook[worksheet]

    # Expand column widths based on the content of the first row
    for column_cells in worksheet.columns:
        max_length = 0
        column = column_cells[0].column_letter  # Get the column letter
        for cell in column_cells:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 2) * 1  # Adjust the width factor as needed
        worksheet.column_dimensions[column].width = adjusted_width

    # Save the modified workbook
    workbook.save(output_file)

def file_exists(file_path):
    return os.path.isfile(file_path)

def read_file(file_path):
    lines = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            lines.append(line)
    return lines

def shutdown():
    print()

    try:
        sys.exit(0)
    except SystemExit as e:
        os._exit(0)

if __name__ == "__main__":
    main()