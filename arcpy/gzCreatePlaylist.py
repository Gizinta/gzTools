## gzCreatePlaylist.py - Generate a Gizinta playlist from a folder of Xml files
## SG May, 2013
## Loop through the xml files in a folder and user wildcards and xml Gizinta node tests to only include the Gizinta xml files.
# ---------------------------------------------------------------------------
# Copyright 2012-2014 Vertex3 Inc
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License.

import os, sys, traceback, time, xml.dom.minidom, gzSupport, arcpy, re
from xml.dom.minidom import Document

# Local variables...
debug = False
# Parameters
folder = arcpy.GetParameterAsText(0) # folder with Gizinta Xml files
wildcard = arcpy.GetParameterAsText(1) # wildcard for file name search
outputFileName = arcpy.GetParameterAsText(2) # output file name argument, default is gzPlaylist.xml

if not outputFileName.lower().endswith(".xml"):
    outputFileName = outputFileName + ".xml"
gzSupport.successParameterNumber = 3
gzSupport.startLog()

def main(argv = None):
    global wildcard
    success = False
    if wildcard == "" or wildcard == "#":
        wildcard = ""
    files = getFiles(folder,wildcard)

    xmlStrSource = writeDocument(files,outputFileName)
    if xmlStrSource != "":
        success = True

    arcpy.SetParameter(gzSupport.successParameterNumber, success)
    arcpy.ResetProgressor()
    gzSupport.closeLog()
    return

def writeDocument(files,outputFileName):

    xmlDoc = Document()
    root = xmlDoc.createElement('GizintaPlaylist')
    xmlDoc.appendChild(root)
    root.setAttribute("logTableName",'gzLog')
    root.setAttribute("errorTableName",'gzError')
    root.setAttribute("fileExtension",'.dwg')
    root.setAttribute("xmlns:gizinta",'http://gizinta.com')
    for fname in files:

        fElem = xmlDoc.createElement("File")
        root.appendChild(fElem)
        nodeText = xmlDoc.createTextNode(fname)
        fElem.appendChild(nodeText)
    try:
        xmlStr = xmlDoc.toprettyxml()
        uglyXml = xmlDoc.toprettyxml(indent='	')
        text_re = re.compile('>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL)
        prettyXml = text_re.sub('>\g<1></', uglyXml)

        fHandle = open(outputFileName, 'w')
        fHandle.write(prettyXml)
        fHandle.close()
    except:
        gzSupport.showTraceback()
        xmlStr =""
    return xmlStr

def getFiles(topFolder,wildcard):
    if wildcard.find("*") > -1:
        searchStrings = wildcard.split("*")
    else:
        searchStrings = [wildcard,".xml"]
    fileList =[]
    for root, dirs, files in os.walk(topFolder, topdown=False):
        for fileName in files:
          currentFile=fileName #os.path.join(root, fl)
          if (searchStrings[0] in currentFile) and fileName.endswith(searchStrings[1]):
                fileList.append(currentFile)
    return fileList

if __name__ == "__main__":
    main()
