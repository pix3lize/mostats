# Mostats 📊

---

![PyPI](https://img.shields.io/pypi/v/mostats) [![Downloads](https://static.pepy.tech/personalized-badge/mostats?period=month&units=international_system&left_color=brightgreen&right_color=grey&left_text=Downloads)](https://pepy.tech/project/mostats) ![GitHub repo size](https://img.shields.io/github/repo-size/pix3lize/mostats) ![GitHub last commit (by committer)](https://img.shields.io/github/last-commit/pix3lize/mostats)

Get the MongoDB database statistic e.g : database name, collection, index size, and collection size to a local CSV file.

New version support multiple server instance and getting additional host information, uptime, total number of command, read, getmore, command, insert, and summarise the cluster report. Host information will be save as cluster-info.csv on the same folder

```python
mostats -u "mongodb+srv://username:password@cluster1.cluster.mongodb.net/" -m True
```

#### Install

Run this command, please choose pip or pip3

```terminal
pip3 install mostats
pip install mostats
```

#### How to use

Please check on the guide below:

```terminal
usage: getCluster.py [-h] [-u URL [URL ...]] [-c CSV] [-n NAME [NAME ...]] [-m MOREINFO]

Get the MongoDB database statistic to a local CSV file

options:
  -h, --help            show this help message and exit
  -u URL [URL ...], --url URL [URL ...]
                        MongoDB cluster URL, default is "mongodb://127.0.0.1". Example:
                        "mongodb+srv://<<username>>:<<password>>@cluster.zqqqy.mongodb.net/?retryWrites=true&w=majority". For multiple server
                        please use the space and "" to seperate
                        example:"mongodb+srv://<<username>>:<<password>>@cluster1.zqqqy.mongodb.net/?retryWrites=true&w=majority"
                        "mongodb+srv://<<username>>:<<password>>@cluster2.zqqqy.mongodb.net/?retryWrites=true&w=majority"
  -c CSV, --csv CSV     CSV filename, default "cluster-data.csv"
  -n NAME [NAME ...], --name NAME [NAME ...]
                        Cluster name, default value first subdomain example: mongodb+srv://clustername.cl0.mongodb.net will be clustername. For
                        multiple server please use the space and "" to seperate example:"cluster1" "cluster2"
  -m MOREINFO, --moreinfo MOREINFO
                        Getting the host information, uptime, total number of command, read, and insert
```

#### Example

For MongoDB Atlas please leave the cluster name empty

```python
mostats -u "mongodb+srv://username:password@cluster0.cluster.mongodb.net/?retryWrites=true&w=majority" -c "cluster-info.csv"
```

Specify custom cluster name for MongoDB Community or Enterprise Edition installation only when MongogDB installed without FQDN

```python
mostats -u "mongodb+srv://username:password@cluster0.cluster.mongodb.net/?retryWrites=true&w=majority" -c "cluster-info.csv"
```

Getting more host information on multiple cluster with custom cluster name. Please leave it empty when getting the data from MongoDB atlas

```python
mostats -u "mongodb+srv://username:password@cluster1.cluster.mongodb.net/" "mongodb+srv://username:password@cluster2.cluster.mongodb.net/" -n "Cluster 1" "Cluster 2" -m True
```
