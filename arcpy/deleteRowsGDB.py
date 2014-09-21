## deleteRowsGDB.py - Delete all of the rows from the datasets in a workspace
## SG September, 2012
## loop through the list of datasets in a workspace and delete everything
# ---------------------------------------------------------------------------
# Copyright 2012-2014 Vertex3 Inc
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License.

import os, sys, traceback, xml.dom.minidom, arcpy, gzSupport

# Local variables...
debug = False
# Parameters
sourceGDB = arcpy.GetParameterAsText(0) # workspace / connection file
if sourceGDB == "#" or sourceGDB == "":
    sourceGDB = "Sample.gdb"

gzSupport.xmlFileName = arcpy.GetParameterAsText(1) # optional - xml File for list of datasets
datasetNames = []
if gzSupport.xmlFileName == "#" or gzSupport.xmlFileName == "":
    gzSupport.xmlFileName = None
else:
    xmlDoc = xml.dom.minidom.parse(gzSupport.xmlFileName)
    datasets = gzSupport.getXmlElements(gzSupport.xmlFileName,"Dataset")
    rootElem = gzSupport.getRootElement(xmlDoc)
    gzSupport.logTableName = rootElem.getAttributeNode("logTableName").nodeValue
    gzSupport.errorTableName = rootElem.getAttributeNode("errorTableName").nodeValue
    for dataset in datasets:
        name = dataset.getAttributeNode("name").nodeValue
        datasetNames.append(name.upper())

SUCCESS = 2 # parameter number for output success value
gzSupport.startLog()

def main(argv = None):
    # main function - list the datasets and delete rows
    success = True
    name = ''
    gzSupport.workspace = sourceGDB
    try:
        if len(datasetNames) == 0:
            names = gzSupport.listDatasets(sourceGDB)
            tNames = names[0]
        else:
            tNames = datasetNames
        arcpy.SetProgressor("Step","Deleting rows...",0,len(tNames),1)
        i = 0
        for name in tNames:
            arcpy.SetProgressorPosition(i)
            arcpy.SetProgressorLabel(" Deleting rows in " + name + "...")
            # for each full name
            if len(datasetNames) == 0 or gzSupport.nameTrimmer(name.upper()) in datasetNames:
                retVal = doTruncate(os.path.join(sourceGDB,name))
                gzSupport.logDatasetProcess("deleteRowsGDB",name,retVal)
                if retVal == False:
                    success = False
            else:
                gzSupport.addMessage("Skipping "  + gzSupport.nameTrimmer(name))
            i = i + i
    except:
        gzSupport.showTraceback()
        gzSupport.addError("Failed to delete rows")
        success = False
        gzSupport.logDatasetProcess("deleteRowsGDB",name,success)
    finally:
        arcpy.SetParameter(SUCCESS, success)
        arcpy.ResetProgressor()
        gzSupport.closeLog()
        arcpy.ClearWorkspaceCache_management(sourceGDB)

def doTruncate(target):
    # perform the append from a source table to a target table
    success = False
    try:
        if arcpy.Exists(target):
            gzSupport.addMessage("Deleting rows in " + target)
            arcpy.DeleteRows_management(target)
            success = True
            if debug:
                gzSupport.addMessage("Deleted")
        else:
            gzSupport.addMessage("Target: " + target + " does not exist")
        gzSupport.cleanupGarbage()
    except:
        gzSupport.addMessage("Unable to delete rows for: " + target )
        # assume this is a view or something that can't be deleted if only some things are not deleted.
        
    return success


if __name__ == "__main__":
    main()
