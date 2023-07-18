# Mostats 📊

---

![PyPI](https://img.shields.io/pypi/v/mostats) [![Downloads](https://static.pepy.tech/personalized-badge/mostats?period=month&units=international_system&left_color=brightgreen&right_color=grey&left_text=Downloads)](https://pepy.tech/project/mostats) ![GitHub repo size](https://img.shields.io/github/repo-size/pix3lize/mostats) ![GitHub last commit (by committer)](https://img.shields.io/github/last-commit/pix3lize/mostats)

Get the MongoDB database statistic e.g : database name, collection, index size, and collection size to a an excel file.

New version support multiple server instance and getting additional host information, uptime, total number of command, read, getmore, command, insert, summarise the cluster report, and recommended sizing. Host information will be save as "Cluster-info.xlsx" on the same folder

To get host information :

```python
mostats -u "mongodb+srv://username:password@cluster1.cluster.mongodb.net/" -m True
```

To get sizing information (specify frequenly access data in percentage -fa) below is the sample of 5% :

```python
mostats -u "mongodb+srv://username:password@cluster1.cluster.mongodb.net/" -fa 5 -m True
```

#### Install

Run this command, please choose pip or pip3

```terminal
pip3 install mostats
pip install mostats
```

or manually download the source code :

```
https://raw.githubusercontent.com/pix3lize/mostats/main/mostats/getCluster.py
```

Required packages: `pymongo`, `pandas`, `argparse`, `openpyxl`,`xlsxwriter`, and `numpy`

#### Minimum permission to run

A database user with the `readAnyDatabase` and `clusterMonitor` roles. To create a username please follow this code. For more information about built-in roles https://www.mongodb.com/docs/manual/reference/built-in-roles/

```javascript
db.getSiblingDB("admin").createUser({
  user: "readonly_user",
  pwd: "readonly_password",
  roles: ["readAnyDatabase", "clusterMonitor"],
});
```

#### How to use

Please check on the guide below:

```terminal
usage: getCluster.py [-h] [-u URL [URL ...]] [-uf URLFILE] [-e EXCELFILE] [-n NAME [NAME ...]] [-nf NAMEFILE] [-m MOREINFO] [-fa FA]
                     [-p PERCENTILE] [-iops IOPS]

Get the MongoDB database statistic to an excel file

options:
  -h, --help            show this help message and exit
  -u URL [URL ...], --url URL [URL ...]
                        MongoDB cluster URL, default is "mongodb://127.0.0.1". Example:
                        "mongodb+srv://<<username>>:<<password>>@cluster.zqqqy.mongodb.net/?retryWrites=true&w=majority". For multiple
                        server please use the space and "" to seperate
                        example:"mongodb+srv://<<username>>:<<password>>@cluster1.zqqqy.mongodb.net/?retryWrites=true&w=majority"
                        "mongodb+srv://<<username>>:<<password>>@cluster2.zqqqy.mongodb.net/?retryWrites=true&w=majority"
  -uf URLFILE, --urlfile URLFILE
                        Get the MongoDB cluster URL from a file. It will read each line as one MongoDB cluster URL
  -e EXCELFILE, --excelfile EXCELFILE
                        Excel filename, default "Cluster-info.xlsx"
  -n NAME [NAME ...], --name NAME [NAME ...]
                        Cluster name, default value first subdomain example: mongodb+srv://clustername.cl0.mongodb.net will be clustername.
                        For multiple server please use the space and "" to seperate example:"cluster1" "cluster2"
  -nf NAMEFILE, --namefile NAMEFILE
                        Get the cluster name from a file. It will read each line as one cluster name
  -m MOREINFO, --moreinfo MOREINFO
                        Getting the host information, uptime, total number of command, read, and insert
  -fa FA, --fa FA       Frequently access ratio in percent (input number only)
  -p PERCENTILE, --percentile PERCENTILE
                        Specify the percentile based on how much the index is used to calculate total number of index for CPU requirement
                        calculation. Default is 70
  -iops IOPS, --iops IOPS
                        Expected IOPS
```

#### Example

For MongoDB Atlas please leave the cluster name empty

```python
mostats -u "mongodb+srv://username:password@cluster0.cluster.mongodb.net/"
```

Specify custom cluster name for MongoDB Community or Enterprise Edition installation only when MongogDB installed without FQDN

```python
mostats -u "mongodb+srv://username:password@cluster0.cluster.mongodb.net/?retryWrites=true&w=majority" -n "Cluster1" -c "Custom-file.xlsx"
```

Getting host information on multiple cluster with custom cluster name. Please leave it empty when getting the data from MongoDB atlas

```python
mostats -u "mongodb+srv://username:password@cluster1.cluster.mongodb.net/" "mongodb+srv://username:password@cluster2.cluster.mongodb.net/" -n "Cluster 1" "Cluster 2" -m True
```

Getting host information and sizing on multiple cluster with custom cluster name. Specify frequently access file by adding parameter -fa. Please leave it empty when getting the data from MongoDB atlas. Below are the sample code for adding frequently access data equal to 5%

```python
mostats -u "mongodb+srv://username:password@cluster1.cluster.mongodb.net/" "mongodb+srv://username:password@cluster2.cluster.mongodb.net/" -n "Cluster 1" "Cluster 2" -fa 5 -m True
```

#### Getting more than one MongoDB cluster with external file

Mostats can read external files to specify both MongoDB URL and custom name. It will read each line as one MongoDB URL and one cluster name.

Sample mongourl.txt

```txt
mongodb+srv://username:password@cluster1.cluster.mongodb.net/
mongodb+srv://username:password@cluster2.cluster.mongodb.net/
```

Sample name.txt

```txt
Cluster 1
Cluster 2
```

Below are the sample script:

```python
mostats -uf "mongourl.txt" -nf "name.txt" -fa 0 -m True
```

#### DISCLAIMER

Please note: all tools/ scripts in this repo are released for use "AS IS" without any warranties of any kind, including, but not limited to their installation, use, or performance. We disclaim any and all warranties, either express or implied, including but not limited to any warranty of noninfringement, merchantability, and/ or fitness for a particular purpose. We do not warrant that the technology will meet your requirements, that the operation thereof will be uninterrupted or error-free, or that any errors will be corrected.

Any use of these scripts and tools is at your own risk. There is no guarantee that they have been through thorough testing in a comparable environment and we are not responsible for any damage or data loss incurred with their use.

You are responsible for reviewing and testing any scripts you run thoroughly before use in any non-testing environment.
