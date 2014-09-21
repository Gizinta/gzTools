# ---------------------------------------------------------------------------
# sourceTargetQA.py
# Created on: 2013-02-03 SG
# Description: Run QA on source datasets using the SourceTargetMatrix.xml
# ---------------------------------------------------------------------------
# Copyright 2012-2014 Vertex3 Inc
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import os, sys, traceback, time, arcpy,  xml.dom.minidom, gzSupport

gzSupport.xmlFileName = arcpy.GetParameterAsText(0) # xml file name as a parameter
gzSupport.workspace = arcpy.GetParameterAsText(1) # Gizinta Geodatabase
sourceFieldQA = arcpy.GetParameterAsText(2) # True/False
targetFieldQA = arcpy.GetParameterAsText(3) # True/False
gzSupport.ignoreErrors = gzSupport.strToBool(arcpy.GetParameterAsText(4)) # boolean indicates whether to return False if errors encountered
SUCCESS = 5 # parameter number for output success value

gzSupport.startLog()
xmlDoc = xml.dom.minidom.parse(gzSupport.xmlFileName)
datasets = gzSupport.getXmlElements(gzSupport.xmlFileName,"Dataset")
rootElem = gzSupport.getRootElement(xmlDoc)
gzSupport.logTableName = rootElem.getAttributeNode("logTableName").nodeValue
gzSupport.errorTableName = rootElem.getAttributeNode("errorTableName").nodeValue
valueMaps = gzSupport.getXmlElements(gzSupport.xmlFileName,"ValueMap")

def main(argv = None):
    success = True
    gzSupport.compressGDB(gzSupport.workspace)
    tables = gzSupport.listDatasets(gzSupport.workspace)
    tNames = tables[0]
    tFullNames = tables[1]

    if len(datasets) > 0:
        progBar = len(datasets)
        arcpy.SetProgressor("step", "Running QA...", 0,progBar, 1)
    for dataset in datasets:
        arcpy.env.Workspace = gzSupport.workspace
        name = dataset.getAttributeNode("name").nodeValue
        gzSupport.sourceIDField = dataset.getAttributeNode("sourceIDField").nodeValue
        table = gzSupport.getFullName(name,tNames, tFullNames)
        #table = os.path.join(gzSupport.workspace,name)
        fields = dataset.getElementsByTagName("Field")
        name = ''
        try:
            # run qa for dataset
            qaRulesDataset = dataset.getAttributeNode("qa").nodeValue
            gzSupport.addMessage("\nRunning QA (" + qaRulesDataset + ") for " + name)
            retVal = runDatasetChecks(dataset,table,qaRulesDataset)
            if retVal == False:
                success = False

            for field in fields:
                sourceQA = False
                targetQA = False
                fieldName = gzSupport.getNodeValue(field,"TargetName")
                if sourceFieldQA.lower() == "true" and qaRulesDataset.find("CheckFields") > -1:
                    sourceQA = True
                    fieldName = gzSupport.getNodeValue(field,"SourceName")
                if targetFieldQA.lower() == "true" and qaRulesDataset.find("CheckFields") > -1:
                    targetQA = True
                    fieldName = gzSupport.getNodeValue(field,"TargetName")
                retVal = runFieldCheck(dataset,table,field,sourceQA,targetQA)
                if retVal == False:
                    success = False
                try:
                    gzSupport.logDatasetProcess(name,fieldName,retVal)
                except:
                    gzSupport.addMessage("Process not logged for field")
            arcpy.SetProgressorPosition()
        except:
            gzSupport.showTraceback()
            gzSupport.addError("Field Check Error")
            success = False
            gzSupport.logDatasetProcess("sourceTargetQA",name,False)
        finally:
            arcpy.ResetProgressor()
            arcpy.RefreshCatalog(table)
            arcpy.ClearWorkspaceCache_management(gzSupport.workspace)
    if success == False:
        gzSupport.addError("Errors occurred during process, look in log file tools\\log\\sourceTargetQA.log for more information")
    if gzSupport.ignoreErrors == True:
        success = True
    arcpy.SetParameter(SUCCESS, success)
    gzSupport.closeLog()
    return

def runDatasetChecks(dataset,table,qaRulesDataset):
    qaRules = qaRulesDataset.split(",")
    success = True
    for rule in qaRules:
        if rule == "RepairGeometry":
            i = 0
            count = 1
            gzSupport.addMessage("Running " + rule + " for " + table)
            while i < 3 and count > 0:
                arcpy.RepairGeometry_management(table)
                count = checkGeometry(table)
                i += 1
            if count > 0:
                err = str(count) + " Geometry Errors found after repairing " + str(i) + " times"
                gzSupport.addError(err)
                gzSupport.logProcessError(table,rule,rule,str(count),err)
                success = False
            else:
                gzSupport.addMessage("Geometry successfully repaired")

        elif rule == "CheckGeometry":
            gzSupport.addMessage("Running " + rule + " for " + table)
            count = checkGeometry(table)
            if count > 0:
                success = False
                gzSupport.logProcessError(table,rule,rule,str(count),"Geometry Errors Found")

    return success

def checkGeometry(table):

    try:
        errTable = table + "_Check"
        if arcpy.Exists(errTable):
            arcpy.Delete_management(errTable)
            gzSupport.addMessage("Deleted existing " + errTable)

        arcpy.CheckGeometry_management(table,errTable)
        count = int(arcpy.GetCount_management(errTable).getOutput(0))
        if count == 0:
            gzSupport.addMessage("No Geometry Errors found")
            arcpy.Delete_management(errTable)
        else:
            gzSupport.addMessage(str(count) + " Errors located in " + errTable)
    except:
        gzSupport.showTraceback()
        gzSupport.addMessage("Unable to perform geometry check, see error listed above")
        count = 0

    return count

def runFieldCheck(dataset,table,field,sourceQA,targetQA):
    success = True
    if sourceQA == True:
        sourceName = gzSupport.getNodeValue(field,"SourceName")
        retVal = runOneFieldCheck(dataset,table,field,"SourceName")
        if retVal == False:
            success = False
    if targetQA == True:
        targetName = gzSupport.getNodeValue(field,"TargetName")
        retVal = runOneFieldCheck(dataset,table,field,"TargetName")
        if retVal == False:
            success = False

    return success

def runOneFieldCheck(dataset,table,field,fieldTag):
    success = True
    fieldVal = field.getElementsByTagName(fieldTag)[0]
    qaRulesField = fieldVal.getAttributeNode("qa").nodeValue
    fieldName = gzSupport.getNodeValue(field,fieldTag)
    gzSupport.addMessage("Field QA (" + qaRulesField + ")for " + fieldName)
    if fieldTag == "SourceName":
        mapName = "SourceValues"
    else:
        mapName = "TargetValues"
    if qaRulesField.find("Unique") > -1:
        retVal = findDuplicates(dataset,table,fieldName)
        if retVal == False:
            success = False
            gzSupport.logProcessError(table,"FieldName",fieldName,"","Duplicate values found")
    if qaRulesField.find("Required") > -1 and qaRulesField.find("Unique") == -1:
        retVal = getCountNullBlank(table,fieldName,"")
        if retVal == False:
            success = False
            gzSupport.logProcessError(table,"FieldName",fieldName,"","Null or blank values found")
    if qaRulesField.find("ValueMaps") > -1:
        retVal = checkValueMaps(dataset,table,field,fieldName,mapName)
        if retVal == False:
            success = False
            gzSupport.logProcessError(table,"FieldName",fieldName,"","Values found that do not match ValueMaps")
    if qaRulesField.find("Check") > -1:
        retVal = getCountNullBlank(table,fieldName,"")
        #retVal = findDuplicates(dataset,table,fieldName)
        retVal = checkValueMaps(dataset,table,field,fieldName,mapName)
    return success

def findDuplicates(dataset,table,field):
    success = True
    uValues = gzSupport.getFieldValues("Unique",[field],[dataset])
    uniqueValues = uValues[0]
    diffValues = uValues[1]
    #fieldValues = gzSupport.getFieldValues("All",[field],[dataset])[0]
    delta = len(diffValues)
    if delta > 0:
        count = int(arcpy.GetCount_management(table).getOutput(0))
        gzSupport.addMessage(str(count) + " rows : " + str(len(uniqueValues)) + " Unique")
        gzSupport.addError(str(delta) + " Duplicates found, results located in " + gzSupport.errorTableName)
        for x in diffValues:
            gzSupport.logProcessError(table,field,str(x),field,"Duplicate Value:" + str(x))
        success = False
    elif delta == 0:
        gzSupport.addMessage("No Duplicates found")

    return success

def getCountNullBlank(table,field,extraExpr):

    whereClause = "\"" + field + "\" is Null " + extraExpr
    success = True
    desc = arcpy.Describe(os.path.join(gzSupport.workspace,table))
    viewName = gzSupport.makeView(desc.dataElementType,gzSupport.workspace,table,"temp_"+field,whereClause,[])
    count = int(arcpy.GetCount_management(viewName).getOutput(0))
    if count > 0:
        gzSupport.addError(str(count) + " Null field values found")
        success = False
    else:
        gzSupport.addMessage("No Null field values found")

    return success

def checkValueMaps(dataset,table,field,fieldName,mapName):
    global valueMaps
    method = gzSupport.getNodeValue(field,"Method")
    success = True
    if method == "ValueMap":
        fieldMapName = gzSupport.getNodeValue(field,"ValueMapName")
        otherwise = gzSupport.getNodeValue(field,"ValueMapOtherwise")
        found = False
        for map in valueMaps:
            mapNodeName = map.getAttributeNode("name").nodeValue
            if mapNodeName == fieldMapName and not found:
                found = True # it is possible for the same value map to be present in multiple gizinta project files, just use the first one.
                mapValues = gzSupport.getNodeValue(map,mapName).split(",")
                if otherwise != None and otherwise != '' and otherwise not in mapValues and not otherwise.count(" ") > 2:
                    mapValues.append(otherwise)
                values = gzSupport.getFieldValues("Unique",[fieldName],[dataset])
                uniqueValues = values[0]
                #delta = len(uniqueValues[0]) - len(mapValues)
                mismatch = []
                for uVal in uniqueValues:
                    if uVal not in mapValues:
                        mismatch.append(uVal)
                if len(mismatch) > 0 and not otherwise.count(" ") > 2:
                    gzSupport.addError(str(len(mismatch)) + " mismatches for " + fieldName + ", results located in " + gzSupport.errorTableName)
                    for uVal in mismatch:
                        gzSupport.addError("'" + str(uVal) + "' not found in value map " + str(fieldMapName))
                        gzSupport.logProcessError(table,gzSupport.sourceIDField,"",fieldName,"Mismatched Value Map:" + str(uVal))
                    success = False
                elif len(mismatch) == 0:
                    gzSupport.addMessage("No mismatches found for ValueMaps")
    return success

if __name__ == "__main__":
    main()
