# MyGizinta.py - user-defined functions that can be used in the field calculator
# SG May 2013
# ---------------------------------------------------------------------------
# Copyright 2012-2013 Vertex3 Inc
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

# you can write any function here you like and use it in a Python expression for the field calculator
# for example:
# <Field>
	# <SourceName qa="Required"></SourceName>
	# <TargetName qa="Required">LASTEDITOR</TargetName>
	# <Method>PythonCalculate</Method>
	# <PythonExpression>myGizinta.defaultUserName()</PythonExpression>
	# <FieldType>TEXT</FieldType>
	# <FieldLength>50</FieldLength>
# </Field>

import sys,os,time, arcpy

proxyhttp = None # "127.0.0.1:80" # ip address and port for proxy, you can also add user/pswd like: username:password@proxy_url:port
proxyhttps = None # same as above for any https sites - not needed for gizinta tools but your proxy setup may require it.

def defaultUserName():
    return os.getenv("USERNAME")
    #return "V3DataLoad"

def dateFromYear(yearVal):
    dateSuffix = "-06-01 12:00:00"
    if yearVal != None:
        if int(yearVal) < 100:
            yearVal = "19" + str(yearVal) + dateSuffix # assume 2 char year is from 1900s...
        else:
            yearVal = str(yearVal) + dateSuffix
    return yearVal

def timer(input):
    return time.time() - input

def getDBTime():
    return getStrTime(time.localtime())

def getStrTime(timeVal):
    return time.strftime("%Y-%m-%d %H:%M:%S", timeVal)

def getTimeFromStr(timeStr):
    return time.strptime(timeStr,"%d/%m/%Y %I:%M:%S %p")

def getWGS1984X(row):
    sr = arcpy.SpatialReference(4326)
    feat = row.getValue("Shape")
    pnt = feat.getPart(0)  
    feat2 = feat.projectAs(sr) #arcpy.PointGeometry(pnt,sr)
    pnt = feat2.getPart(0)
    return pnt.X


