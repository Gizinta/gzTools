## gzCreateFiles.py - Generate Gizinta files given the source and target workspaces
## SG December, 2013
## Loop through the datasets in the target database and create a gizinta file for each target that has a matching source name
# ---------------------------------------------------------------------------
# Copyright 2012-2013 Vertex3 Inc
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import os, sys, traceback, time, xml.dom.minidom, gzSupport, arcpy, gzCreateProject
from xml.dom.minidom import Document

# Local variables...
debug = False
# Parameters
sourceGDB = arcpy.GetParameterAsText(0) # source workspace
targetGDB = arcpy.GetParameterAsText(1) # target workspace
outputFolder = arcpy.GetParameterAsText(2) # output folder argument, default is same as target workspace
prefixStr = arcpy.GetParameterAsText(3) # Prefix for file names created, default is Gizinta
gzSupport.successParameterNumber = 4

if outputFolder == None or outputFolder == "":
    outputFolder = targetGDB[:targetGDB.rfind(os.sep)+1]

if prefixStr == None:
    prefixStr = ""

def main(argv = None):
    # main function - list the source and target datasets, then delete rows/append where there is a match on non-prefixed name
    dir = os.path.dirname(os.path.dirname( os.path.realpath( __file__) ))
    logname = os.path.join(outputFolder,'gzCreateProjectFiles.log')
    gzSupport.startLog()

    success = True
    try:

        gzSupport.addMessage("Getting list of datasets for Target " + targetGDB)
        targets = gzSupport.listDatasets(targetGDB)
        tNames = targets[0]
        tFullNames = targets[1]

        gzSupport.addMessage("Getting list of datasets for Source " + sourceGDB)
        sources = gzSupport.listDatasets(sourceGDB)
        sNames = sources[0]
        sFullNames = sources[1]

        t = 0
        arcpy.SetProgressor("Step","Creating Files...",0,len(tNames),1)
        
        for name in tNames:
            arcpy.SetProgressorPosition(t)
            arcpy.SetProgressorLabel("Creating file for " + name + "...")
            # for each source name
            if debug:
                gzSupport.addMessage(name)
            try:
                # look for the matching name in target names
                s = sNames.index(name)
            except:
                # will get here if no match
                s = -1
            if s > -1:
                # create file if there is a match
                fileName = outputFolder + os.sep + prefixStr + name.title() + ".xml"
                if os.path.exists(fileName):
                    os.remove(fileName)
                try:
                    #arcpy.AddToolbox(os.path.join(dir,"Gizinta.tbx")) 
                    #arcpy.gzCreateProject_gizinta(sFullNames[s],tFullNames[t],fileName) # this doesn't always work...
                    gzCreateProject.createGzFile(sFullNames[s],tFullNames[t],fileName)
                    retVal = True
                    gzSupport.addMessage("Created "  + fileName)
                except:
                    retVal = False
                if retVal == False:                    
                    gzSupport.addMessage("Failed to create file for "  + name)
                    gzSupport.showTraceback()
                    success = False
            else:
                gzSupport.addMessage("Skipping "  + name)
            t = t + 1
    except:
        gzSupport.showTraceback()
        arcpy.AddError("Error creating project files")
        success = False
  
    finally:
        arcpy.ResetProgressor()
        arcpy.SetParameter(gzSupport.successParameterNumber, success)
        arcpy.env.workspace = targetGDB
        arcpy.RefreshCatalog(outputFolder)
        gzSupport.closeLog()
  
if __name__ == "__main__":
    main()
