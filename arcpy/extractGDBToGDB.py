# ---------------------------------------------------------------------------
# ExtractGDBToGDB.py
# Created on: 2013-02-03 SG
# Description: Import a set of GDB Datasets to Geodatabase. 
# ---------------------------------------------------------------------------
# Copyright 2012-2013 Vertex3 Inc and the Regional Municipality of Waterloo
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import os, sys, traceback, time, datetime as dt, arcpy,  xml.dom.minidom, gzSupport

gzSupport.xmlFileName = arcpy.GetParameterAsText(0) # xml file name as a parameter
sourceWorkspace = arcpy.GetParameterAsText(1) # Source Geodatabase or Feature dataset to load from
gzSupport.workspace = arcpy.GetParameterAsText(2) # Gizinta Geodatabase
gzSupport.ignoreErrors = gzSupport.strToBool(arcpy.GetParameterAsText(3)) # boolean indicates whether to return False if errors encountered
SUCCESS = 4 # parameter number for output success value

gzSupport.startLog()
xmlDoc = xml.dom.minidom.parse(gzSupport.xmlFileName)
datasets = gzSupport.getXmlElements(xmlDoc,"GDBDataset")
rootElem = gzSupport.getRootElement(xmlDoc)
gzSupport.logTableName = rootElem.getAttributeNode("logTableName").nodeValue
gzSupport.errorTableName = rootElem.getAttributeNode("errorTableName").nodeValue
            
def main(argv = None):
    success = True
    try:
        if not arcpy.Exists(gzSupport.workspace):
            gzSupport.addMessage(gzSupport.workspace + " does not exist, attempting to create")
            gzSupport.createGizintaGeodatabase()
        else:
            gzSupport.compressGDB(gzSupport.workspace)
        if len(datasets) > 0:
            progBar = len(datasets) + 1
            arcpy.SetProgressor("step", "Importing Datasets...", 0,progBar, 1) 
            deleteExistingRows(datasets)
            arcpy.SetProgressorPosition()
        for dataset in datasets:
            gzSupport.sourceIDField = dataset.getAttributeNode("sourceIDField").nodeValue
            sourceName = dataset.getAttributeNode("sourceName").nodeValue
            targetName = dataset.getAttributeNode("targetName").nodeValue
            arcpy.SetProgressorLabel("Loading " + sourceName + " to " + targetName +"...")
            if not arcpy.Exists(os.path.join(sourceWorkspace,sourceName)):
                gzSupport.addError(os.path.join(sourceWorkspace,sourceName + " does not exist, exiting"))
                return
            if not arcpy.Exists(os.path.join(gzSupport.workspace,targetName)):
                gzSupport.addMessage(os.path.join(gzSupport.workspace,targetName) + " does not exist")
                mode = "export"
            else:
                mode = "import"

            arcpy.env.Workspace = gzSupport.workspace
            try:
                if mode == "import":
                    retVal = gzSupport.importDataset(sourceWorkspace,sourceName,targetName,dataset)
                elif mode == "export":
                    retVal = gzSupport.exportDataset(sourceWorkspace,sourceName,targetName,dataset)
                if retVal == False:
                    success = False
            except:
                gzSupport.showTraceback()
                success = False
                retVal = False
            gzSupport.logDatasetProcess(sourceName,targetName,retVal)
        arcpy.SetProgressorPosition()
    except:
        gzSupport.showTraceback()
        gzSupport.addError("A Fatal Error occurred")
        success = False
        gzSupport.logDatasetProcess("","",False)
    finally:
        arcpy.ResetProgressor()
        arcpy.RefreshCatalog(gzSupport.workspace)
        arcpy.ClearWorkspaceCache_management(sourceWorkspace)
        arcpy.ClearWorkspaceCache_management(gzSupport.workspace)

    if success == False:
        gzSupport.addError("Errors occurred during process, look in log files for more information")        
    if gzSupport.ignoreErrors == True:
        success = True
        
    gzSupport.closeLog()
    arcpy.SetParameter(SUCCESS, success)

def deleteExistingRows(datasets):
    for dataset in datasets:
        name = dataset.getAttributeNode("targetName").nodeValue
        table = os.path.join(gzSupport.workspace,name)
        if arcpy.Exists(table):
            arcpy.DeleteRows_management(table)
            gzSupport.addMessage("Rows deleted from: " + name)
        else:
            gzSupport.addMessage(table + " does not exist")
            
    #gzSupport.deleteLogTableRows("Delete") # don't delete
    #gzSupport.deleteErrorTableRows("Delete")


if __name__ == "__main__":
    main()
