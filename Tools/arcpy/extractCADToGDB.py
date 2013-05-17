# ---------------------------------------------------------------------------
# ExtractCADToGDB.py
# Created on: 2013-02-03 SG
# Description: Import a set of CAD Drawings in a folder structure to Geodatabase. Join to .csv files that contain Identifiers and potentially other values.
# ---------------------------------------------------------------------------
# Copyright 2012-2013 Vertex3 Inc and Caltech Pasadena
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import os, sys, traceback, time, datetime as dt, arcpy,  xml.dom.minidom, gzSupport

gzSupport.xmlFileName = arcpy.GetParameterAsText(0) # xml file name as a parameter
cadFolder = arcpy.GetParameterAsText(1) # Folder to scan for drawing files
since = arcpy.GetParameterAsText(2) # date since file name as a parameter
gzSupport.workspace = arcpy.GetParameterAsText(3) # Gizinta Geodatabase
gzSupport.ignoreErrors = gzSupport.strToBool(arcpy.GetParameterAsText(4)) # boolean indicates whether to return False if errors encountered
SUCCESS = 5 # parameter number for output success value

gzSupport.startLog()
xmlDoc = xml.dom.minidom.parse(gzSupport.xmlFileName)
datasets = gzSupport.getXmlElements(xmlDoc,"CADDataset")
rootElem = gzSupport.getRootElement(xmlDoc)
gzSupport.logTableName = rootElem.getAttributeNode("logTableName").nodeValue
gzSupport.errorTableName = rootElem.getAttributeNode("errorTableName").nodeValue
cadExt = rootElem.getAttributeNode("fileExtension").nodeValue
  
def main(argv = None):
    success = True
    if not arcpy.Exists(gzSupport.workspace):
        gzSupport.addMessage(gzSupport.workspace + " does not exist, attempting to create")
        gzSupport.createGizintaGeodatabase()
    else:
        arcpy.Compact_management(gzSupport.workspace)

    gzSupport.setupLogTables()

    arcpy.ClearWorkspaceCache_management(gzSupport.workspace)
    try:
        gzSupport.addMessage("Looking for drawings modified since " + since)
        minTime = dt.datetime.strptime(since,"%d/%m/%Y %I:%M:%S %p")
        cadFiles = getFileList(cadFolder,cadExt,minTime)
        if len(cadFiles) > 0:
            progBar = len(cadFiles) + 1
            arcpy.SetProgressor("step", "Importing Drawings...", 0,progBar, 1) 
            deleteExistingRows(datasets)
            arcpy.SetProgressorPosition()
        for item in cadFiles:
            cadPath = item[0]
            cadName = item[1]
            gzSupport.addMessage("Importing Drawing " + cadName)
            
            for dataset in datasets:
                try:
                    name = dataset.getAttributeNode("sourceName").nodeValue
                except:
                    name = dataset.getAttributeNode("name").nodeValue

                gzSupport.sourceIDField = dataset.getAttributeNode("sourceIDField").nodeValue
                arcpy.SetProgressorLabel("Loading " + name + " for " + cadName + "...") 
                arcpy.env.Workspace = gzSupport.workspace
                targetName = dataset.getAttributeNode("targetName").nodeValue
                sourceWorkspace = os.path.join(cadPath,cadName)
                if not arcpy.Exists(os.path.join(gzSupport.workspace,targetName)):
                    gzSupport.addMessage(os.path.join(gzSupport.workspace,targetName) + " does not exist")
                    mode = "export"
                else:
                    mode = "import"

                try:
                    if mode == "import":
                        retVal = gzSupport.importDataset(sourceWorkspace,name,targetName,dataset)
                    elif mode == "export":
                        retVal = gzSupport.exportDataset(sourceWorkspace,name,targetName,dataset)
                    #retVal = importLayer(cadPath,cadName,dataset)
                    if retVal == False:
                        success = False
                except:
                    gzSupport.showTraceback()
                    success = False
                    retVal = False

                arcpy.env.Workspace = gzSupport.workspace
                gzSupport.logDatasetProcess(cadName,name,retVal)
                gzSupport.cleanupGarbage()
            arcpy.SetProgressorPosition()
    except:
        gzSupport.addError("A Fatal Error occurred")
        gzSupport.showTraceback()
        success = False
        gzSupport.logDatasetProcess("","",False)
    finally:
        arcpy.ResetProgressor()
        arcpy.RefreshCatalog(gzSupport.workspace)
        arcpy.ClearWorkspaceCache_management(gzSupport.workspace)
        gzSupport.cleanupGarbage()

    if success == False:
        gzSupport.addError("Errors occurred during process, look in log files for more information")        
    if gzSupport.ignoreErrors == True:
        success = True
    gzSupport.closeLog()
    arcpy.SetParameter(SUCCESS, success)

def importLayer(cadPath,cadName,dataset):
    result = False
    try:
        name = dataset.getAttributeNode("targetName").nodeValue
    except:
        name = dataset.getAttributeNode("name").nodeValue
        
    table = os.path.join(gzSupport.workspace,name)
    layerName = dataset.getAttributeNode("sourceName").nodeValue
    layer = os.path.join(cadPath,cadName,layerName)
    gzSupport.addMessage("Importing Layer " + layer)

    try:
        whereClause = gzSupport.getNodeValue(dataset,"WhereClause")
        gzSupport.addMessage("Where " + whereClause)
        if not arcpy.Exists(table):
            err = "Feature Class " + name + " does not exist"
            gzSupport.addError(err)
            gzSupport.logProcessError(cadName,gzSupport.sourceIDField,name,name,err)
            return False
        if whereClause != '':
            view = gzSupport.makeFeatureView(gzSupport.workspace,layer,layerName + "_View", whereClause)
        else:
            view = layer
        count = arcpy.GetCount_management(view).getOutput(0)
        gzSupport.addMessage(str(count) + " source Features for " + name)
                
        if hasJoinTo(dataset) == True:            
            res = joinToCsv(view,dataset,cadPath,cadName)
            result = res[0]
            view = res[1]
        else:
            view = view
            result = True

        if result == True and count > 0:
            arcpy.Append_management([view],table, "NO_TEST","","")
            arcpy.ClearWorkspaceCache_management(gzSupport.workspace)
       
    except:
        err = "Failed to import layer " + name
        gzSupport.addError(err)
        gzSupport.showTraceback()
        gzSupport.logProcessError(cadName,gzSupport.sourceIDField,name,layerName,err)
    gzSupport.cleanupGarbage()
    try:
        del view
    except:
        gzSupport.addMessage("")
    return result


def hasJoinTo(dataset):
    joinTo = True    
    try:
        test = dataset.getAttributeNode("joinTo").nodeValue
    except:
        joinTo = False
        #gzSupport.addMessage("No join requested for layer")

    return joinTo

def joinToCsv(view, dataset,cadPath,cadName):
    retVal = False
    joinTo = ""
    if hasJoinTo(dataset) == True:
        try:
            joinTo = dataset.getAttributeNode("joinTo").nodeValue
            cadPart0 = cadName.split(".dwg")[0]
            csvFile = os.path.join(cadPath,cadPart0,cadPart0 + joinTo)
            if joinTo and joinTo != "":
                cadKey = dataset.getAttributeNode("cadKey").nodeValue
                csvKey = dataset.getAttributeNode("csvKey").nodeValue
                prefix = dataset.getAttributeNode("fieldPrefix").nodeValue
                tempTable = os.path.join(gzSupport.workspace, prefix)
                # Create temporary table
                if arcpy.Exists(tempTable):
                    arcpy.Delete_management(tempTable)
                if os.path.isfile(csvFile) == True:
                    arcpy.CopyRows_management(csvFile, tempTable)
                    arcpy.AddJoin_management(view, cadKey, tempTable, csvKey)
                    retVal = True
                else:
                    err = "Missing csv file - " + csvFile
                    gzSupport.addError(err)
                    gzSupport.logProcessError(cadName,gzSupport.sourceIDField,name,csvFile,err)

                    retVal = False
        except:
            err = "Unable to create join for " + name + ", " + csvFile
            gzSupport.logProcessError(cadName,gzSupport.sourceIDField,name,csvFile,err)
            gzSupport.addError(err)
            gzSupport.showTraceback()
            retVal = False
        #finally:
        #    if arcpy.Exists(tempTable):
        #        arcpy.Delete_management(tempTable)

    return [retVal,view]

def deleteExistingRows(datasets):
    for dataset in datasets:
        try:
            name = dataset.getAttributeNode("targetName").nodeValue
        except:
            name = dataset.getAttributeNode("name").nodeValue
        table = os.path.join(gzSupport.workspace,name)
        if arcpy.Exists(table):
            arcpy.DeleteRows_management(table)
            gzSupport.addMessage("Rows deleted from: " + name)
    #gzSupport.deleteLogTableRows("Delete") # don't delete
    #gzSupport.deleteErrorTableRows("Delete")

def getFileList(inputFolder,fileExt,minTime): # get a list of files - recursively
    inputFiles = []
    docList = os.listdir(inputFolder) #Get directory list for inputDirectory
    for doc in docList:
        docLow = doc.lower()
        ffile = os.path.join(inputFolder,doc)
        if docLow.endswith(fileExt.lower()):
            t = os.path.getmtime(ffile)
            modTime = dt.datetime.fromtimestamp(t)
            if modTime > minTime:
                inputFiles.append([inputFolder,doc])
        elif os.path.isdir(ffile):
            newFiles = getFileList(ffile,fileExt,minTime)
            inputFiles = newFiles + inputFiles
    return(inputFiles)

if __name__ == "__main__":
    main()
