# ---------------------------------------------------------------------------
# fieldCalculator.py
# Created on: 2013-01-22 SG
# Description: Create new fields using the provided field name, type, etc. using the Gizinta.xml
# Calculate values into that field based on source-target mappings.
# ---------------------------------------------------------------------------
# Copyright 2012-2013 Vertex3 Inc
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
    name = ''
    
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
                gzSupport.addGizintaField(table,targetName,field,attrs)

            retVal = setFieldValues(table,fields)
            if retVal == False:
                success = False
            gzSupport.logDatasetProcess(name,"Fields",retVal)
            arcpy.ClearWorkspaceCache_management(gzSupport.workspace)
            gzSupport.cleanupGarbage()

        except:
            gzSupport.showTraceback()
            success = False
            gzSupport.logDatasetProcess("fieldCalculator",name,False)
        finally:
            arcpy.RefreshCatalog(table)
            arcpy.ClearWorkspaceCache_management(gzSupport.workspace)
    if success == False:
        gzSupport.addError("Errors occurred during process, look in log file tools\\log\\fieldCalculator.log for more information")
    if gzSupport.ignoreErrors == True:
        success = True
    arcpy.SetParameter(SUCCESS, success)
    arcpy.ResetProgressor()
    gzSupport.closeLog()
    return

def calcValue(row,attrs,calcString):
    # calculate a value based on fields and or other expressions
    if calcString.find("|") > -1:
        calcList = calcString.split("|")
    else:
        calcList = calcString.split("!")
    outVal = ""
    for strVal in calcList:
        if strVal in attrs:
            outVal += str(row.getValue(strVal))
        else:
            outVal += strVal
    try:
        outVal = eval(outVal)
    except:
        gzSupport.addMessage("Error evaluating:" + outVal)
        gzSupport.showTraceback()
        gzSupport.addError("Error calculating field values:" + outVal)
    return outVal

def setFieldValues(table,fields):
    # from source xml file match old values to new values to prepare for append to target geodatabase
    success = False
    try:
        updateCursor = arcpy.UpdateCursor(table)
        row = updateCursor.next()
    except Exception, ErrorDesc:
        gzSupport.addMessage( "Unable to update the Dataset, Python error is: ")
        msg = str(getTraceback(Exception, ErrorDesc)) # this is the old style, could update
        gzSupport.addMessage(msg[msg.find("Error Info:"):])
        row = None

    valueMaps = gzSupport.getXmlElements(gzSupport.xmlFileName,"ValueMap")
    result = arcpy.GetCount_management(table)
    numFeat = int(result.getOutput(0))
    gzSupport.addMessage(table + ", " + str(numFeat) + " features")
    progressUpdate = 1
    i=0
    if numFeat > 100:
        progressUpdate = int(numFeat/100)
    arcpy.SetProgressor("Step","Calculating " + table + "...",0,numFeat,progressUpdate)
    attrs = [f.name for f in arcpy.ListFields(table)]

    if row is not None:
        success = True
        errCount = 0
        while row:
            if errCount > gzSupport.maxErrorCount:
                return False
            i += 1
            if i % 1000 == 0:
                gzSupport.addMessage("Feature " + str(i) + " processed")
            if i % progressUpdate == 0:
                arcpy.SetProgressorPosition(i)
                gzSupport.addMessage("Processing feature " + str(i))

            for field in fields:
                method = "None"
                currentValue = "None"
                targetName = gzSupport.getNodeValue(field,"TargetName")
                try:
                    sourceName = gzSupport.getNodeValue(field,"SourceName")# handle the case where the source field does not exist or is blank
                except:
                    sourceName = ""

                if sourceName != "" and not sourceName.startswith("*"):
                    try:
                        if sourceName != targetName and sourceName.upper() == targetName.upper():
                            # special case for same name but different case - should already have the target name from extract functions
                            currentValue = row.getValue(targetName)
                        else:
                            currentValue = row.getValue(sourceName)
                    except:
                        #gzSupport.addMessage("No value for "  + sourceName)
                        currentValue = "None" # handle the case where the source field does not exist or is blank

                method = gzSupport.getNodeValue(field,"Method")
                if (method == "None" or method == "Copy") and currentValue == "None":
                    method = "None"
                elif method == "ValueMap":
                    valueMappingName = gzSupport.getNodeValue(field,"ValueMapName")
                    try:
                        otherwise = gzSupport.getNodeValue(field,"ValueMapOtherwise")
                    except:
                        otherwise = None
                    try:
                        mapExpr = gzSupport.getNodeValue(field,"ValueMapExpression")
                    except:
                        mapExpr = None
                    found = False
                    for valueMap in valueMaps:
                        try:
                            valID = valueMap.getAttributeNode("name").nodeValue
                        except:
                            valID = None
                        if not found and valID:
                            if valID == valueMappingName:
                                sourceValues = []
                                sourceValues = gzSupport.getNodeValue(valueMap,"SourceValues")
                                if sourceValues.find("|") > -1:
                                    sourceValues = sourceValues.split("|")
                                elif sourceValues.find(",") > -1:
                                    sourceValues = sourceValues.split(",")
                                targetValues = []
                                targetValues = gzSupport.getNodeValue(valueMap,"TargetValues")
                                if targetValues.find("|") > -1:
                                    targetValues = targetValues.split("|")
                                elif targetValues.find(",") > -1:
                                    targetValues = targetValues.split(",")

                                for sourceValue in sourceValues:
                                    try:
                                        sourceTest = float(sourceValue)
                                    except ValueError:
                                        sourceTest = str(sourceValue)
                                        if sourceTest == '':
                                            sourceTest = None
                                    if mapExpr and mapExpr != "":
                                        currentValue = calcValue(row,attrs,mapExpr)
                                    if currentValue == sourceTest or currentValue == sourceValue: # this will check numeric and non-numeric equivalency for current values in value maps
                                        found = True
                                        try:
                                            idx = sourceValues.index(sourceValue)
                                            newValue = targetValues[idx]
                                            row.setValue(targetName,newValue)
                                        except:
                                            errCount += 1
                                            row.setValue(targetName,currentValue)
                                            success = False
                                            err = "Unable to map values for " + targetName + ", value = " + str(newValue)
                                            gzSupport.showTraceback()
                                            gzSupport.addError(err)
                                            gzSupport.logProcessError(row.getValue(gzSupport.sourceNameField),gzSupport.sourceIDField,row.getValue(gzSupport.sourceIDField),targetName,err)

                    if not found:
                        if otherwise and str(otherwise) != "None":
                            otherwise = str(otherwise)
                            if otherwise.count(" ") > 2 or otherwise.count("!") > 1:
                                otherwise = calcValue(row,attrs,otherwise)
                                #gzSupport.addMessage(otherwise)
                            row.setValue(targetName,otherwise)
                        else:
                            errCount += 1
                            success = False
                            err = "Unable to find map value (otherwise) for " + str(targetName) + ", value = " + str(currentValue)
                            gzSupport.addError(err)
                            gzSupport.logProcessError(row.getValue(gzSupport.sourceNameField),gzSupport.sourceIDField,row.getValue(gzSupport.sourceIDField),targetName,err)

                elif method == "Copy":
                    if currentValue and currentValue != "":
                        row.setValue(targetName,currentValue)
                elif method == "DefaultValue":
                    defaultValue = gzSupport.getNodeValue(field,"DefaultValue")
                    row.setValue(targetName,defaultValue)
                elif method == "PythonCalculate":
                    calcString = gzSupport.getNodeValue(field,"PythonExpression")
                    calcNew = calcValue(row,attrs,calcString)
                    if calcNew != None and calcNew != "": # don't bother setting null/blank values
                        try:
                            row.setValue(targetName,calcNew)
                        except:
                            gzSupport.addMessage("calculated value=" + str(calcNew))
                            success = False
                            err = "Exception caught: unable to set calculated value for " + targetName + ' calcString=' + calcString
                            gzSupport.showTraceback()
                            gzSupport.addError(err)
                            gzSupport.logProcessError(row.getValue(gzSupport.sourceNameField),gzSupport.sourceIDField,row.getValue(gzSupport.sourceIDField),targetName,err)
                            errCount += 1
                    #else:
                    #    errCount += 1
                    #    success = False
                    #    err = "Blank or null value calculated: unable to set value for " + targetName + " " + str(calcString)
                    #    gzSupport.addError(err)
                    #    gzSupport.logProcessError(row.getValue(gzSupport.sourceNameField),gzSupport.sourceIDField,row.getValue(gzSupport.sourceIDField),targetName,err)

            try:
                updateCursor.updateRow(row)
            except:
                errCount += 1
                success = False
                err = "Exception caught: unable to update row"
                gzSupport.showTraceback()
                gzSupport.addError(err)
                gzSupport.logProcessError(row.getValue(gzSupport.sourceNameField),gzSupport.sourceIDField,row.getValue(gzSupport.sourceIDField),"One of the values",err)
            row = updateCursor.next()

    del updateCursor
    gzSupport.cleanupGarbage()
    arcpy.ResetProgressor()

    return success

if __name__ == "__main__":
    main()
