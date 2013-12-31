## gzSetup.py - take a list of datasets and export a Gizinta setup file
## SG March, 2013
## Loop through the list datasets and write an xml document that can be used in the Gizinta online mapping tool
# ---------------------------------------------------------------------------
# Copyright 2012-2014 Vertex3 Inc
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import os, sys, traceback, time, xml.dom.minidom, arcpy, gzSupport, urllib, webbrowser
from xml.dom.minidom import Document
from threading import Thread
# Local variables...
debug = True
# Parameters

sourceDataset = arcpy.GetParameterAsText(0) # dataset to analyze
targetDataset = arcpy.GetParameterAsText(1) # dataset to analyze
xmlFileName = arcpy.GetParameterAsText(2) # file name argument
#sourceXml = arcpy.GetParameterAsText(3) # source output file name
#targetXml = arcpy.GetParameterAsText(4) # target output file name
gzSupport.successParameterNumber = 3
gzSupport.startLog()
xmlStr = ""

def main(argv = None):
    startTime = gzSupport.getDBTime()
    gzSupport.addMessage(startTime)
    success = True

    xmlStrSource = getDocument(sourceDataset)
    xmlStrTarget = getDocument(targetDataset)
    OpenBrowserURL(xmlStrSource,xmlStrTarget)

    arcpy.SetParameter(gzSupport.successParameterNumber, success)
    arcpy.ResetProgressor()
    #t = Thread(target=OpenBrowserURL(xmlStr))
    #t.start()
    #t.join()

    gzSupport.closeLog()
    return

def OpenBrowserURL(xmlStrSource,xmlStrTarget):
    xmlDoc = xml.dom.minidom.parse(xmlFileName)
    xmlStrGizinta = xmlDoc.toxml()
    params = urllib.urlencode( {'source': xmlStrSource, 'target': xmlStrTarget, 'gizinta': xmlStrGizinta})
    url="http://www.gizinta.com/giztest/scripts/GizintaMapper.php"
    f = urllib.urlopen(url, params)
    fileName = f.read()
    gzSupport.addMessage(fileName )
    url = 'http://www.gizinta.com/giztest/gizinta.html?target='+fileName
    webbrowser.open(url,new=2)

    #folder = xmlFileName[0:xmlFileName.rfind(os.sep)]
    #url = 'http://www.gizinta.com/giztest/index.html?' + "GizintaFolder="+folder
    #webbrowser.open(url,new=2)

def getDocument(dataset):
    gzSupport.addMessage(dataset)
    desc = arcpy.Describe(dataset)
    xmlDoc = Document()
    root = xmlDoc.createElement('table')
    xmlDoc.appendChild(root)
    root.setAttribute("xmlns",'http://gizinta.com')
    if desc.baseName.find('.') > -1:
        baseName = desc.baseName[desc.baseName.rfind('.')+1:]
    else:
        baseName = desc.baseName

    source = xmlDoc.createElement("data")
    source.setAttribute("name",baseName)
    root.appendChild(source)
    fields = getFields(dataset)
    i=0
    try:
        for field in fields:
            fNode = xmlDoc.createElement("row")
            fNode.setAttribute("id",str(i))
            source.appendChild(fNode)
            addFieldElement(xmlDoc,fNode,"FieldName",field.name)
            addFieldElement(xmlDoc,fNode,"SourceField","")
            addFieldElement(xmlDoc,fNode,"SourceQA","Required") # need to get these values from template project.
            addFieldElement(xmlDoc,fNode,"TargetQA","Required")
            addFieldElement(xmlDoc,fNode,"SourceMethod","Copy")
            addFieldElement(xmlDoc,fNode,"FieldType",field.type)
            addFieldElement(xmlDoc,fNode,"FieldLength",str(field.length))
            i += 1
        xmlStr = xmlDoc.toxml()
    except:
        gzSupport.showTraceback()
        xmlStr =""

                #xmlDoc.writexml( open(xmlFiles[ds], 'w'),indent="",addindent="",newl="")
                #xmlDoc.unlink()
    return xmlStr


def addFieldElement(xmlDoc,node,name,value):
    xmlName = xmlDoc.createElement("column")
    xmlName.setAttribute("name",name)
    node.appendChild(xmlName)
    nodeText = xmlDoc.createTextNode(value)
    xmlName.appendChild(nodeText)

def getFields(dataset):
    fields = []
    ignore = []
    desc = arcpy.Describe(dataset)
    for name in ["OIDFieldName","ShapeFieldName","LengthFieldName","AreaFieldName"]:
        val = getFieldExcept(desc,name)
        if val != None:
          ignore.append(val)
    for field in arcpy.ListFields(dataset):
        if field.name not in ignore:
          fields.append(field)

    return fields

def getFieldExcept(desc,name):
    val = None
    try:
        val = eval("desc." + name)
    except:
        val = None
    return val

if __name__ == "__main__":
    main()
