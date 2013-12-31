# ---------------------------------------------------------------------------
# RunXlst.py
# Created on: 2013-04-25 SG
# Description: Run an xslt function (to upgrade a Gizinta.xml file)
# ---------------------------------------------------------------------------
# Copyright 2012-2014 Vertex3 Inc
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

# Import arcpy module
import arcpy
# Local variables:
Gizinta_xml = arcpy.GetParameterAsText(0)
xsl = "UpgradeGizintaXml.xsl"
Gizinta2_xml = arcpy.GetParameterAsText(1)

# Process: XSLT Transformation
arcpy.XSLTransform_conversion(Gizinta_xml, xsl, Gizinta2_xml, "")

