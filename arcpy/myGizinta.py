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

import sys,os,time

def defaultUserName():
	return "Jacob Marley"

def timer(input):
    return time.time() - input

def getDBTime():
    return getStrTime(time.localtime())

def getStrTime(timeVal):
    return time.strftime("%Y-%m-%d %H:%M:%S", timeVal)

def getTimeFromStr(timeStr):
    return time.strptime(timeStr,"%d/%m/%Y %I:%M:%S %p")	
	