# ---------------------------------------------------------------------------
# ExtractCADToGDB.py
# Created on: 2013-02-03 SG
# rewritten: June 2013
# Description: Import a set of CAD Drawings in a folder structure to Geodatabase. Join to .csv files that contain Identifiers and potentially other values.
# ---------------------------------------------------------------------------
# Copyright 2012-2014 Vertex3 Inc
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License.

import os, sys, traceback, time, datetime, arcpy,  xml.dom.minidom, gzSupport

gzSupport.xmlFileName = arcpy.GetParameterAsText(0) # xml file name as a parameter
cadFolder = arcpy.GetParameterAsText(1) # Folder to scan for drawing files
since = arcpy.GetParameterAsText(2) # date since file name as a parameter
gzSupport.workspace = arcpy.GetParameterAsText(3) # Gizinta Geodatabase
gzSupport.ignoreErrors = gzSupport.strToBool(arcpy.GetParameterAsText(4)) # boolean indicates whether to return False if errors encountered
SUCCESS = 5 # parameter number for output success value

gzSupport.startLog()
xmlDoc = xml.dom.minidom.parse(gzSupport.xmlFileName)
datasets = gzSupport.getXmlElements(gzSupport.xmlFileName,"CADDataset")
rootElem = gzSupport.getRootElement(xmlDoc)
gzSupport.logTableName = rootElem.getAttributeNode("logTableName").nodeValue
gzSupport.errorTableName = rootElem.getAttributeNode("errorTableName").nodeValue
cadExt = rootElem.getAttributeNode("fileExtension").nodeValue

def main(argv = None):
    success = True
    name = ''
    if not arcpy.Exists(gzSupport.workspace):
        gzSupport.addMessage(gzSupport.workspace + " does not exist, attempting to create")
        gzSupport.createGizintaGeodatabase()
    else:
        gzSupport.compressGDB(gzSupport.workspace)
    arcpy.ClearWorkspaceCache_management(gzSupport.workspace)
    try:
        gzSupport.addMessage("Looking for drawings modified since " + since)
        minTime = datetime.datetime.strptime(since,"%d/%m/%Y %I:%M:%S %p")
        cadFiles = gzSupport.getFileList(cadFolder,cadExt,minTime)
        if len(cadFiles) > 0:
            progBar = len(cadFiles) + 1
            arcpy.SetProgressor("step", "Importing Drawings...", 0,progBar, 1)
            arcpy.SetProgressorPosition()
            gzSupport.deleteExistingRows(datasets)
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
                xmlFields = gzSupport.getXmlElements(gzSupport.xmlFileName,"Field")
                arcpy.SetProgressorLabel("Loading " + name + " for " + cadName + "...")
                arcpy.env.Workspace = gzSupport.workspace
                targetName = dataset.getAttributeNode("targetName").nodeValue
                sourceWorkspace = os.path.join(cadPath,cadName)
                exists= False
                if not arcpy.Exists(os.path.join(gzSupport.workspace,targetName)):
                    gzSupport.addMessage(os.path.join(gzSupport.workspace,targetName) + " does not exist")
                else:
                    exists = True
                    #arcpy.Delete_management(os.path.join(gzSupport.workspace,targetName))

                try:
                    if not exists==True:
                        retVal = gzSupport.exportDataset(sourceWorkspace,name,targetName,dataset,xmlFields)
                        addDrawingField(os.path.join(gzSupport.workspace,targetName),cadName)
                    else:
                        retVal = importLayer(cadPath,cadName,dataset)
                        addDrawingField(os.path.join(gzSupport.workspace,targetName),cadName)
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
        gzSupport.logDatasetProcess("extractCADToGDB",name,False)
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
        xmlFields = dataset.getElementsByTagName("Field")
        gzSupport.addMessage("Where " + whereClause)
        if not arcpy.Exists(table):
            err = "Feature Class " + name + " does not exist"
            gzSupport.addError(err)
            gzSupport.logProcessError(cadName,gzSupport.sourceIDField,name,name,err)
            return False
        if whereClause != '':
            view = gzSupport.makeFeatureView(gzSupport.workspace,layer,layerName + "_View", whereClause,xmlFields)
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

def addDrawingField(table,dwgName):
    fieldName = "DRAWING"
    gzSupport.addField(table,"DRAWING","TEXT",50)
    if dwgName.rfind(".dwg") > -1:
        dwgName = dwgName[:dwgName.rfind(".dwg")]
    arcpy.CalculateField_management(table,fieldName,"\"" + dwgName + "\"","PYTHON_9.3")

if __name__ == "__main__":
    main()
