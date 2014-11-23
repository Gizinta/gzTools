## gzFieldMapper.py - set up xml document for field mapping on the gizinta website
## SG April, 2013
##
# ---------------------------------------------------------------------------
# Copyright 2012-2014 Vertex3 Inc
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import os, sys, traceback, time, xml.dom.minidom, arcpy, gzSupport, urllib, urllib2, webbrowser, myGizinta
from xml.dom.minidom import Document
from threading import Thread
# Local variables...
debug = True
# Parameters

gzSupport.xmlFileName = arcpy.GetParameterAsText(0) # file name argument
automap = arcpy.GetParameterAsText(1) # option to use auto field mapping
gzSupport.successParameterNumber = 2

xmlDoc = xml.dom.minidom.parse(gzSupport.xmlFileName)
gzSupport.startLog()
xmlStr = ""
url="http://www.gizinta.com/fields/scripts/GizintaMapper.php"

def main(argv = None):
    success = True
    OpenBrowserURL(gzSupport.xmlFileName)
    gzSupport.closeLog()
    return

def OpenBrowserURL(xmlFileName):
    global url
    xmlDoc = xml.dom.minidom.parse(xmlFileName)
    xmlStrGizinta = xmlDoc.toxml()
    dsNode = xmlDoc.getElementsByTagName("Dataset")[0]
    target = dsNode.getAttributeNode("name").nodeValue
    theData = [('gizinta', xmlStrGizinta),('target', target),('automap',automap)]
    params = urllib.urlencode(theData)
    setupProxy()
        
    f = urllib2.urlopen(url, params)
    fileName = f.read()
    gzSupport.addMessage(fileName )
    if fileName.find(">Warning<") == -1 and fileName.find(">Error<") == -1:
        url = 'http://www.gizinta.com/fields/gizinta.html?target='+fileName
        webbrowser.open(url, new=2)
    else:
        gzSupport.addMessage("An error occurred interacting with gizinta.com. Please check your network connection and error messages printed above")

def setupProxy():
    proxies = {}
    if myGizinta.proxyhttp != None:
        proxies['http'] = 'http://' + myGizinta.proxyhttp
        os.environ['http'] = myGizinta.proxyhttp
    if myGizinta.proxyhttps != None:
        proxies['https'] = myGizinta.proxyhttps
        os.environ['https'] = 'http://' + myGizinta.proxyhttps
    if proxies != {}:
        proxy = urllib2.ProxyHandler(proxies)
        opener = urllib2.build_opener(proxy)
        urllib2.install_opener(opener)    


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
