# ---------------------------------------------------------------------------
# addMissingFields.py
# Created on: 2014-08-14 SG
# Description: Add missing fields to a target Geodatabase using the provided field name, type, etc. using the Gizinta.xml
# ---------------------------------------------------------------------------
# Copyright 2012-2014 Vertex3 Inc
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License.

import os, sys, traceback, time, arcpy,  xml.dom.minidom, gzSupport, myGizinta

gzSupport.xmlFileName = arcpy.GetParameterAsText(0) # xml file name as a parameter
gzSupport.workspace = arcpy.GetParameterAsText(1) # Gizinta Geodatabase
gzSupport.ignoreErrors = gzSupport.strToBool(arcpy.GetParameterAsText(2)) # boolean indicates whether to return False if errors encountered
SUCCESS = 3 # parameter number for output success value

gzSupport.startLog()
xmlDoc = xml.dom.minidom.parse(gzSupport.xmlFileName)
datasets = gzSupport.getXmlElements(gzSupport.xmlFileName,"Dataset")
rootElem = gzSupport.getRootElement(xmlDoc)
gzSupport.logTableName = rootElem.getAttributeNode("logTableName").nodeValue
gzSupport.errorTableName = rootElem.getAttributeNode("errorTableName").nodeValue
valueMappings = gzSupport.getXmlElements(gzSupport.xmlFileName,"ValueMaps")

def main(argv = None):
    success = True
    gzSupport.compressGDB(gzSupport.workspace)
    arcpy.ClearWorkspaceCache_management(gzSupport.workspace)
    tables = gzSupport.listDatasets(gzSupport.workspace)
    tNames = tables[0]
    tFullNames = tables[1]

    for dataset in datasets:
        arcpy.env.Workspace = gzSupport.workspace
        name = dataset.getAttributeNode("name").nodeValue
        table = gzSupport.getFullName(name,tNames,tFullNames)
        gzSupport.sourceIDField = dataset.getAttributeNode("sourceIDField").nodeValue
        gzSupport.sourceNameField = dataset.getAttributeNode("sourceNameField").nodeValue
        if not arcpy.Exists(table):
            gzSupport.addError("Feature Class " + table + " does not exist, exiting")
            arcpy.SetParameter(SUCCESS, False)
            return
        if not arcpy.TestSchemaLock(table):
            gzSupport.addError("Unable to obtain a schema lock for " + table + ", exiting")
            arcpy.SetParameter(SUCCESS, False)
            return -1
        desc = arcpy.Describe(table)
        fields = dataset.getElementsByTagName("Field")
        try:
            attrs = [f.name for f in arcpy.ListFields(table)]
            for field in fields:
                arcpy.env.Workspace = gzSupport.workspace
                targetName = gzSupport.getNodeValue(field,"TargetName")
                retVal = gzSupport.addGizintaField(table,targetName,field,attrs)
                if retVal == False:
                    success = False
            gzSupport.logDatasetProcess("addMissingFields",name,retVal)
            arcpy.ClearWorkspaceCache_management(gzSupport.workspace)
            gzSupport.cleanupGarbage()

        except:
            gzSupport.showTraceback()
            success = False
            gzSupport.logDatasetProcess("addMissingFields",name,False)
        finally:
            arcpy.RefreshCatalog(table)
            arcpy.ClearWorkspaceCache_management(gzSupport.workspace)
    if success == False:
        gzSupport.addError("Errors occurred during process, look in log file tools\\log\\addMissingFields.log for more information")
    if gzSupport.ignoreErrors == True:
        success = True
    arcpy.SetParameter(SUCCESS, success)
    arcpy.ResetProgressor()
    gzSupport.closeLog()
    return

if __name__ == "__main__":
    main()
