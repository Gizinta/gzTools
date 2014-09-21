# ---------------------------------------------------------------------------
# ExtractLayerToGDB.py
# Created on: 2013-05-06 SG
# rewritten in June 2013
# Description: Import a set of .lyr files to Geodatabase.
# ---------------------------------------------------------------------------
# Copyright 2012-2014 Vertex3 Inc
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License.

import os, sys, traceback, time, arcpy, xml.dom.minidom, gzSupport

gzSupport.xmlFileName = arcpy.GetParameterAsText(0) # xml file name as a parameter
sourceLayer = arcpy.GetParameterAsText(1) # Source Layer File to load from
gzSupport.workspace = arcpy.GetParameterAsText(2) # Gizinta Geodatabase
gzSupport.ignoreErrors = gzSupport.strToBool(arcpy.GetParameterAsText(3)) # boolean indicates whether to return False if errors encountered
SUCCESS = 4 # parameter number for output success value

gzSupport.startLog()
xmlDoc = xml.dom.minidom.parse(gzSupport.xmlFileName)
datasets = gzSupport.getDatasets(gzSupport.xmlFileName)

rootElem = gzSupport.getRootElement(xmlDoc)
gzSupport.logTableName = rootElem.getAttributeNode("logTableName").nodeValue
gzSupport.errorTableName = rootElem.getAttributeNode("errorTableName").nodeValue

def main(argv = None):
    success = True
    name = ''
    try:
        if not arcpy.Exists(gzSupport.workspace):
            gzSupport.addMessage(gzSupport.workspace + " does not exist, attempting to create")
            gzSupport.createGizintaGeodatabase()
        else:
            gzSupport.compressGDB(gzSupport.workspace)
        if len(datasets) > 0:
            progBar = len(datasets) + 1
            arcpy.SetProgressor("step", "Importing Layers...", 0,progBar, 1)
            arcpy.SetProgressorPosition()
        for dataset in datasets:
            gzSupport.sourceIDField = dataset.getAttributeNode("sourceIDField").nodeValue
            sourceName = dataset.getAttributeNode("sourceName").nodeValue
            targetName = dataset.getAttributeNode("targetName").nodeValue
            arcpy.SetProgressorLabel("Loading " + sourceName + " to " + targetName +"...")
            if not arcpy.Exists(sourceLayer):
                gzSupport.addError("Layer " + sourceLayer + " does not exist, exiting")
                return
            target = os.path.join(gzSupport.workspace,targetName)
            arcpy.env.Workspace = gzSupport.workspace
            if not arcpy.Exists(target):
                gzSupport.addMessage("Feature Class " + target + " does not exist")
            else:
                arcpy.Delete_management(target)
            try:
                retVal = exportDataset(sourceLayer,targetName,dataset)
                if retVal == False:
                    success = False
            except:
                gzSupport.showTraceback()
                success = False
                retVal = False
            gzSupport.logDatasetProcess(sourceName,targetName,retVal)
        arcpy.SetProgressorPosition()
    except:
        gzSupport.addError("A Fatal Error occurred")
        gzSupport.showTraceback()
        success = False
        gzSupport.logDatasetProcess("extractLayerToGDB",name,False)
    finally:
        arcpy.ResetProgressor()
        arcpy.RefreshCatalog(gzSupport.workspace)
        arcpy.ClearWorkspaceCache_management(gzSupport.workspace)

    if success == False:
        gzSupport.addError("Errors occurred during process, look in log files for more information")
    if gzSupport.ignoreErrors == True:
        success = True
    gzSupport.closeLog()
    arcpy.SetParameter(SUCCESS, success)

def exportDataset(sourceLayer,targetName,dataset):
    result = True
    targetTable = os.path.join(gzSupport.workspace,targetName)
    gzSupport.addMessage("Exporting Layer from " + sourceLayer)
    whereClause = ""
    try:
        try:
            whereClause = gzSupport.getNodeValue(dataset,"WhereClause")
        except:
            whereClause = ''
        gzSupport.addMessage("Where '" + whereClause + "'")
        sourceName = sourceLayer[sourceLayer.rfind(os.sep)+1:sourceLayer.lower().rfind(".lyr")]
        viewName = sourceName + "_View"
        xmlFields = xmlDoc.getElementsByTagName("Field")
        view = gzSupport.makeFeatureViewForLayer(gzSupport.workspace,sourceLayer,viewName,whereClause,xmlFields)
        count = arcpy.GetCount_management(view).getOutput(0)
        gzSupport.addMessage(str(count) + " source rows")
        arcpy.FeatureClassToFeatureClass_conversion(view,gzSupport.workspace,targetName)
    except:
        err = "Failed to create new dataset " + targetName
        gzSupport.showTraceback()
        gzSupport.addError(err)
        gzSupport.logProcessError(sourceLayer,gzSupport.sourceIDField,sourceLayer,targetName,err)
        result = False
    return result

if __name__ == "__main__":
    main()
