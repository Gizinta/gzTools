# ---------------------------------------------------------------------------
# replaceByFieldValuesGDB.py
# Created on: 2013-02-15 SG
# Description: For unique values in a field, such as AutoCAD DocName or City names in a County:
# 1. Create a version
# 2. Delete rows from the Target database for one of the field values
# 3. Append rows from the Source database for that field value
# 4. If no errors then Reconcile and Post the version
# 5. If any errors then delete the version
# if the target workspace is a file gdb then do the same logic without a version
# ---------------------------------------------------------------------------
# Copyright 2012-2014 Vertex3 Inc
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import os, sys, traceback, time, arcpy,  xml.dom.minidom, gzSupport

gzSupport.xmlFileName = arcpy.GetParameterAsText(0) # xml file name as a parameter
gzSupport.workspace = arcpy.GetParameterAsText(1) # Gizinta Geodatabase
defaultWorkspace =   arcpy.GetParameterAsText(2) # Connection to the default version
targetWorkspace =   arcpy.GetParameterAsText(3) # Connection to the version to be used/updated
gzSupport.ignoreErrors = gzSupport.strToBool(arcpy.GetParameterAsText(4)) # boolean indicates whether to return False if errors encountered
SUCCESS = 5 # parameter number for output success value

if targetWorkspace == "" or targetWorkspace == "#":
    targetWorkspace = defaultWorkspace

gzSupport.startLog()
xmlDoc = xml.dom.minidom.parse(gzSupport.xmlFileName)
datasets = gzSupport.getXmlElements(gzSupport.xmlFileName,"Dataset")
rootElem = gzSupport.getRootElement(xmlDoc)
gzSupport.logTableName = rootElem.getAttributeNode("logTableName").nodeValue
gzSupport.errorTableName = rootElem.getAttributeNode("errorTableName").nodeValue

settings = gzSupport.getXmlElements(gzSupport.xmlFileName,"AppendSettings")[0]
fieldNames = gzSupport.getNodeValue(settings,"FieldNames")
fieldNames = fieldNames.split(",")

try:
    versionName = gzSupport.getNodeValue(settings,"VersionName")
    defaultVersionName = gzSupport.getNodeValue(settings,"DefaultVersionName")
except:
    versionName = None
    defaultVersionName = None

def main(argv = None):
    global targetWorkspace
    hasVersion = False
    desc = arcpy.Describe(gzSupport.workspace)
    if desc.workspaceType != "RemoteDatabase" and versionName == None:
        targetWorkspace = defaultWorkspace
    success = True
    arcpy.ResetProgressor()
    arcpy.env.Workspace = gzSupport.workspace
    uniqueValues = gzSupport.getFieldValues("Unique",fieldNames,datasets)[0]
    sources = gzSupport.listDatasets(gzSupport.workspace)
    sNames = sources[0]
    sFullNames = sources[1]
    arcpy.SetProgressor("Step","Load by " + str(fieldNames) + "...",0,len(uniqueValues)*len(datasets),1)
    for value in uniqueValues:
        try:
            hasVersion = False
            gzSupport.addMessage(value)
            if desc.workspaceType == "RemoteDatabase" and versionName != None:
                arcpy.SetProgressorLabel("Creating Version " + versionName)
                hasVersion = gzSupport.createVersion(defaultWorkspace,defaultVersionName,versionName)
            if hasVersion == True  or versionName == None or desc.workspaceType == "LocalDatabase":
                arcpy.env.Workspace = targetWorkspace
                targets = gzSupport.listDatasets(targetWorkspace)
                tNames = targets[0]
                tFullNames = targets[1]
                for dataset in datasets:
                    name = dataset.getAttributeNode("name").nodeValue
                    arcpy.SetProgressorLabel("Loading Dataset " + name)
                    targetTable = gzSupport.getFullName(name,tNames,tFullNames)
                    sourceTable = gzSupport.getFullName(name,sNames,sFullNames)
                    attrs = [f.name for f in arcpy.ListFields(targetTable)]
                    expr = getExpression(attrs,fieldNames,value)
                    arcpy.SetProgressorLabel("Loading Dataset " + name + " Where " + expr)
                    tName = targetTable[targetTable.rfind("\\")+1:]
                    tLocation = targetTable[0:targetTable.rfind("\\")]
                    if gzSupport.deleteRows(tLocation,tName,expr) == True:
                        retVal = gzSupport.appendRows(sourceTable,targetTable,expr)
                        if retVal == False:
                            success == False
                    else:
                        success == False
                    arcpy.SetProgressorPosition()
                if success == True:
                    if desc.workspaceType == "RemoteDatabase":
                        arcpy.SetProgressorLabel("Reconcile and Post")
                        retVal = gzSupport.reconcilePost(defaultWorkspace,versionName,defaultVersionName)
                        if retVal == False:
                            success = False
                            gzSupport.deleteVersion(defaultWorkspace,versionName)
                    elif desc.workspaceType == "LocalDatabase":
                        arcpy.SetProgressorLabel("Completed Update for " + str(value))
                    gzSupport.logDatasetProcess(sys.argv[0],targetTable,retVal)
                else:
                    gzSupport.logDatasetProcess(sys.argv[0],targetTable,retVal)
                gzSupport.cleanupGarbage()


        except:
            gzSupport.showTraceback()
            success = False
            gzSupport.logDatasetProcess("Serious error",sys.argv[0],False)
        finally:
            arcpy.SetProgressorPosition()
            arcpy.ClearWorkspaceCache_management(defaultWorkspace)
    if success == False:
        gzSupport.addError("Errors occurred during process, look in log files for more information")
    if gzSupport.ignoreErrors == True:
        success = True
    if desc.workspaceType == "RemoteDatabase" and success == True:
        analyze(defaultWorkspace,datasets,tNames,tFullNames)
    arcpy.SetParameter(SUCCESS, success)

    arcpy.ClearWorkspaceCache_management(defaultWorkspace)
    gzSupport.compressGDB(gzSupport.workspace)
    gzSupport.compressGDB(defaultWorkspace)
    gzSupport.closeLog()
    return

def analyze(workspace,datasets,tNames,tFullNames):
    retVal = True
    for dataset in datasets:
        name = dataset.getAttributeNode("name").nodeValue
        targetTable = gzSupport.getFullName(name,tNames,tFullNames)
        arcpy.SetProgressorLabel("Analyzing " + name)
        try:
            arcpy.Analyze_management(targetTable,"BUSINESS")
            arcpy.Analyze_management(targetTable,"ADDS")
            arcpy.Analyze_management(targetTable,"DELETES")
            arcpy.Analyze_management(targetTable,"FEATURE")
        except:
            retVal = False

    return retVal

def getExpression(attrs,fieldNames,value):
    expr = ""
    i = 0
    for name in fieldNames:
        if name in attrs:
            if i >= 1:
                expr = expr + " OR "
            expr = expr + "\"" + name + "\"='" + str(value) + "'"
            i += 1

    return expr


if __name__ == "__main__":
    main()
