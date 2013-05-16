<?xml version="1.0"?>
<!--
# Upgrade Gizinta Xml document from an earlier version (April 2013)
# Copyright 2012-2013 Vertex3 Inc
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.
-->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:str="http://exslt.org/common" xmlns:gizinta="http://gizinta.com" xmlns:exsl="http://exslt.org/common" extension-element-prefixes="exsl">
	<xsl:output omit-xml-declaration="yes"/>
	<xsl:output indent="yes"/>

	<xsl:template match="/">
		<xsl:apply-templates select="*"/>
	</xsl:template>
	<xsl:template match="@*">
		<xsl:copy/>
	</xsl:template>

	<xsl:template match="*">
		<xsl:copy>
			<xsl:apply-templates select="@*|node()"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="FieldProperties">
		<xsl:element name="FieldType">
			<xsl:choose>
				<xsl:when test="substring-before(.,',,,') != ''">
					<xsl:value-of select="substring-before(.,',,,')"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="."/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:element>
		<xsl:element name="FieldLength">
			<xsl:value-of select="substring-after(.,',,,')"/>
		</xsl:element>
	</xsl:template>

	<xsl:template match="Dataset">
		<xsl:element name="Dataset">
			<xsl:apply-templates select="@*|node()"/>
			<xsl:element name="SourceFieldNames">
				<xsl:variable name="theCount" select="count(Field/SourceName)"/>
				<xsl:variable name="theList">
					<xsl:for-each select="Field/SourceName">
						<xsl:value-of select="."/>
						<xsl:if test="position() &lt; $theCount">
							<xsl:text>,</xsl:text>
						</xsl:if>
					</xsl:for-each>
				</xsl:variable>
				<xsl:value-of select="$theList"/>
			</xsl:element>
		</xsl:element>
	</xsl:template>
</xsl:stylesheet><!-- Stylus Studio meta-information - (c) 2004-2009. Progress Software Corporation. All rights reserved.

<metaInformation>
	<scenarios>
		<scenario default="yes" name="Scenario1" userelativepaths="yes" externalpreview="no" url="..\..\Region of Waterloo\Cambridge\Gizinta.xml" htmlbaseurl="" outputurl="..\..\Region of Waterloo\Cambridge\Gizinta2.xml" processortype="saxon8"
		          useresolver="no" profilemode="0" profiledepth="" profilelength="" urlprofilexml="" commandline="" additionalpath="" additionalclasspath="" postprocessortype="none" postprocesscommandline="" postprocessadditionalpath=""
		          postprocessgeneratedext="" validateoutput="no" validator="internal" customvalidator="">
			<advancedProp name="sInitialMode" value=""/>
			<advancedProp name="bXsltOneIsOkay" value="true"/>
			<advancedProp name="bSchemaAware" value="false"/>
			<advancedProp name="bXml11" value="false"/>
			<advancedProp name="iValidation" value="0"/>
			<advancedProp name="bExtensions" value="true"/>
			<advancedProp name="iWhitespace" value="0"/>
			<advancedProp name="sInitialTemplate" value=""/>
			<advancedProp name="bTinyTree" value="true"/>
			<advancedProp name="xsltVersion" value="2.0"/>
			<advancedProp name="bWarnings" value="true"/>
			<advancedProp name="bUseDTD" value="false"/>
			<advancedProp name="iErrorHandling" value="fatal"/>
		</scenario>
	</scenarios>
	<MapperMetaTag>
		<MapperInfo srcSchemaPathIsRelative="yes" srcSchemaInterpretAsXML="no" destSchemaPath="" destSchemaRoot="" destSchemaPathIsRelative="yes" destSchemaInterpretAsXML="no"/>
		<MapperBlockPosition></MapperBlockPosition>
		<TemplateContext></TemplateContext>
		<MapperFilter side="source"></MapperFilter>
	</MapperMetaTag>
</metaInformation>
-->