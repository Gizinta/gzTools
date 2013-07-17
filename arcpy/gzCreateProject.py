## gzCreateProject.py - take a list of 2 datasets and export a Gizinta setup file
## SG April, 2013
## Loop through the source and target datasets and write an xml document that can be used in the Gizinta online mapping tool
## or edited by hand
# ---------------------------------------------------------------------------
# Copyright 2012-2013 Vertex3 Inc
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import os, sys, traceback, time, xml.dom.minidom, arcpy, gzSupport, urllib, webbrowser
from xml.dom.minidom import Document
import re

# Local variables...
debug = True
# Parameters
sourceDataset = arcpy.GetParameterAsText(0) # source dataset to analyze
targetDataset = arcpy.GetParameterAsText(1) # target dataset to analyze
xmlFileName = arcpy.GetParameterAsText(2) # file name argument
gzSupport.successParameterNumber = 3
gzSupport.startLog()
xmlStr = ""

def main(argv = None):
    success = False
    xmlStrSource = writeDocument(sourceDataset,targetDataset,xmlFileName)
    if xmlStrSource != "":
        success = True
        
    arcpy.SetParameter(gzSupport.successParameterNumber, success)
    arcpy.ResetProgressor()
    gzSupport.closeLog()
    return

def writeDocument(sourceDataset,targetDataset,xmlFileName):
    desc = arcpy.Describe(sourceDataset)
    descT = arcpy.Describe(targetDataset)

    gzSupport.addMessage(sourceDataset)
    xmlDoc = Document()
    root = xmlDoc.createElement('Gizinta')
    xmlDoc.appendChild(root)
    root.setAttribute("logTableName",'gzLog')
    root.setAttribute("errorTableName",'gzError')
    root.setAttribute("version",'2013.1')
    root.setAttribute("xmlns:gizinta",'http://gizinta.com')

    extract = xmlDoc.createElement("Extract")
    root.appendChild(extract)

    dataElementName = getExtractElementName(desc,sourceDataset)
    
    source = xmlDoc.createElement(dataElementName)
    sourceName = getName(desc,sourceDataset)
    targetName = getName(descT,targetDataset)
    setDefaultProperties(source,dataElementName,sourceDataset,sourceName,targetName)
    where = xmlDoc.createElement("WhereClause")
    source.appendChild(where)
    extract.appendChild(source)
    
    transform = xmlDoc.createElement("Transform")
    root.appendChild(transform)

    dataset = xmlDoc.createElement("Dataset")
    transform.appendChild(dataset)
    dataset.setAttribute("name",targetName)
    dataset.setAttribute("qa","CheckFields,CheckGeometry")
    dataset.setAttribute("sourceIDField","")
    dataset.setAttribute("sourceNameField","")
    
    fields = getFields(descT,targetDataset)
    sourceFields = getFields(desc,sourceDataset)
    sourceNames = [field.name[field.name.rfind(".")+1:] for field in sourceFields]
    i=0
    try:
        for field in fields:
            fNode = xmlDoc.createElement("Field")
            dataset.appendChild(fNode)
            fieldName = field.name[field.name.rfind(".")+1:]
            if fieldName in sourceNames:
                addFieldElement(xmlDoc,fNode,"SourceName",fieldName)
            else:
                addFieldElement(xmlDoc,fNode,"SourceName","*"+fieldName+"*")
               
            addFieldElement(xmlDoc,fNode,"TargetName",fieldName)
            addFieldElement(xmlDoc,fNode,"Method","Copy")
            addFieldElement(xmlDoc,fNode,"FieldType",field.type)
            addFieldElement(xmlDoc,fNode,"FieldLength",str(field.length))
            i += 1
        setSourceFields(xmlDoc,dataset,sourceNames)
        # Should add a template section for value maps, maybe write domains...
            
        xmlStr = xmlDoc.toprettyxml()
        uglyXml = xmlDoc.toprettyxml(indent='	')
        text_re = re.compile('>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL)    
        prettyXml = text_re.sub('>\g<1></', uglyXml)
        
        fHandle = open(xmlFileName, 'w')
        fHandle.write(prettyXml)
        fHandle.close()

    except:
        gzSupport.showTraceback()
        xmlStr =""
    return xmlStr
    
def getName(desc,dataset):
    if desc.baseName.find('.') > -1:
        baseName = desc.baseName[desc.baseName.rfind('.')+1:]
    else:
        baseName = desc.baseName
    if desc.dataElementType == "DEShapefile":
        baseName = baseName + ".shp"
    return baseName    

def setSourceFields(xmlDoc,dataset,sourceNames):
    sourceFieldsNode = xmlDoc.createElement("SourceFieldNames")
    dataset.appendChild(sourceFieldsNode)
    sourceFields = ",".join(sorted(sourceNames))
    nodeText = xmlDoc.createTextNode(sourceFields)
    sourceFieldsNode.appendChild(nodeText)

def addFieldElement(xmlDoc,node,name,value):
    xmlName = xmlDoc.createElement(name)
    if name == "SourceName":
        xmlName.setAttribute("qa","Optional")
    if name == "TargetName":
        xmlName.setAttribute("qa","Optional")
    node.appendChild(xmlName)
    nodeText = xmlDoc.createTextNode(value)
    xmlName.appendChild(nodeText)

def getFields(desc,dataset):
    fields = []
    ignore = []
    for name in ["OIDFieldName","ShapeFieldName","LengthFieldName","AreaFieldName"]:
        val = getFieldExcept(desc,name)
        if val != None:
            val = val[val.rfind(".")+1:]
            ignore.append(val)
    for field in arcpy.ListFields(dataset):
        if field.name[field.name.rfind(".")+1:] not in ignore:
            fields.append(field)
          
    return fields

def getFieldExcept(desc,name):
    val = None
    try:
        val = eval("desc." + name)
    except:
        val = None
    return val

def setDefaultProperties(source,dataElementName,sourceDataset,sourceName,targetName):
    # set source properties according to the type of dataset

    source.setAttribute("sourceName",sourceName)
    source.setAttribute("targetName",targetName)

    if dataElementName == "MapLayer":
        #source.setAttribute("fieldPrefixes","")
        source.setAttribute("sourceIDField","OBJECTID")

    elif dataElementName == "CADDataset":
        source.setAttribute("sourceIDField","Handle")
        #source.setAttribute("fieldPrefixes","")
        #source.setAttribute("layerName",sourceDataset[sourceDataset.rfind(os.sep)+1:])
        #source.setAttribute("cadKey","Handle")
        #source.setAttribute("csvKey","HANDLE")

    elif dataElementName == "GDBDataset":
        source.setAttribute("sourceIDField","OBJECTID")

    

def getExtractElementName(desc,sourceDataset):
    deType = ""
    if desc.dataElementType == "DELayer":
        deType = "MapLayer"
    elif desc.dataElementType == "DEFeatureClass" and sourceDataset.lower().find(".dwg"+os.sep) > -1:
        deType = "CADDataset"
    elif desc.dataElementType == "DEFeatureClass":
        deType = "GDBDataset"
    elif desc.dataElementType == "DETable":
        deType = "GDBDataset"
    elif desc.dataElementType == "DEShapefile":
        deType = "GDBDataset"
    return deType

if __name__ == "__main__":
    main()
