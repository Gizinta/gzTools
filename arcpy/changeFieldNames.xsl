<?xml version="1.0"?>
<!--
# Change the case of field names in a Gizinta xml document
# Copyright 2012-2014 Vertex3 Inc
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.
-->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:str="http://exslt.org/common" xmlns:gizinta="http://gizinta.com" xmlns:exsl="http://exslt.org/common" extension-element-prefixes="exsl">
	<xsl:output omit-xml-declaration="yes"/>
	<xsl:output indent="yes"/>

	<xsl:param name="case" select="'lower'"/>
	<xsl:variable name="lowerCaseLetters">abcdefghijklmnopqrstuvwxyz</xsl:variable>
	<xsl:variable name="upperCaseLetters">ABCDEFGHIJKLMNOPQRSTUVWXYZ</xsl:variable>

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

	<xsl:template match="Field">
		<xsl:copy>
			<xsl:for-each select="./*">
				<xsl:copy>
					<xsl:choose>
						<xsl:when test="name(.)='SourceName' or name(.)='TargetName'">
							<xsl:call-template name="caseChanger">
								<xsl:with-param name="str" select="."/>
							</xsl:call-template>
						</xsl:when>
						<xsl:otherwise>
							<xsl:value-of select="."/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:copy>
			</xsl:for-each>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="SourceFieldNames">
		<xsl:copy>
			<xsl:call-template name="caseChanger">
				<xsl:with-param name="str" select="."/>
			</xsl:call-template>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="@idField">

		<xsl:attribute name="idField">
			<xsl:call-template name="caseChanger">
				<xsl:with-param name="str" select="."/>
			</xsl:call-template>
		</xsl:attribute>
	</xsl:template>

	<xsl:template match="@viewFields">

		<xsl:attribute name="viewFields">
			<xsl:call-template name="caseChanger">
				<xsl:with-param name="str" select="."/>
			</xsl:call-template>
		</xsl:attribute>
	</xsl:template>

	<xsl:template name="caseChanger">
		<xsl:param name="str"/>
		<xsl:choose>
			<xsl:when test="$case='lower'">
				<xsl:value-of select="translate($str,$upperCaseLetters,$lowerCaseLetters)"/>
			</xsl:when>
			<xsl:when test="$case='upper'">
				<xsl:value-of select="translate($str,$lowerCaseLetters,$upperCaseLetters)"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:comment>Incorrect value for case parameter: <xsl:value-of select="$case"/></xsl:comment>
				<xsl:value-of select="$str"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
</xsl:stylesheet>


	<!--	<xsl:template match="ChangeDetection">
		<xsl:copy>
			<xsl:choose>
				<xsl:when test="@idField!=''">
					<xsl:attribute name="idField">
							<xsl:call-template name="caseChanger">
								<xsl:with-param name="str" select="@idField"/>
							</xsl:call-template>
					</xsl:attribute>
				</xsl:when>
				<xsl:when test="@viewFields!=''">
					<xsl:attribute name="viewFields">
							<xsl:call-template name="caseChanger">
								<xsl:with-param name="str" select="@viewFields"/>
							</xsl:call-template>
					</xsl:attribute>
				</xsl:when>
				<xsl:otherwise>
					<xsl:apply-templates select="@*|node()"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:copy>
	</xsl:template>--><!-- Stylus Studio meta-information - (c) 2004-2009. Progress Software Corporation. All rights reserved.

<metaInformation>
	<scenarios>
		<scenario default="no" name="Scenario1" userelativepaths="yes" externalpreview="no" url="..\..\test\Gizinta.xml" htmlbaseurl="" outputurl="..\..\test\out.xml" processortype="saxon8" useresolver="no" profilemode="0" profiledepth="" profilelength=""
		          urlprofilexml="" commandline="" additionalpath="" additionalclasspath="" postprocessortype="none" postprocesscommandline="" postprocessadditionalpath="" postprocessgeneratedext="" validateoutput="no" validator="internal"
		          customvalidator="">
			<advancedProp name="sInitialMode" value=""/>
			<advancedProp name="bXsltOneIsOkay" value="true"/>
			<advancedProp name="bSchemaAware" value="false"/>
			<advancedProp name="bGenerateByteCode" value="false"/>
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
		<scenario default="no" name="Scenario2" userelativepaths="yes" externalpreview="no" url="..\..\CampusFM\ETL\config\fpInteriorSpaceAll.xml" htmlbaseurl="" outputurl="..\..\test\out.xml" processortype="saxon8" useresolver="no" profilemode="0"
		          profiledepth="" profilelength="" urlprofilexml="" commandline="" additionalpath="" additionalclasspath="" postprocessortype="none" postprocesscommandline="" postprocessadditionalpath="" postprocessgeneratedext="" validateoutput="no"
		          validator="internal" customvalidator="">
			<advancedProp name="sInitialMode" value=""/>
			<advancedProp name="bXsltOneIsOkay" value="true"/>
			<advancedProp name="bSchemaAware" value="false"/>
			<advancedProp name="bGenerateByteCode" value="true"/>
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
		<scenario default="yes" name="Scenario3" userelativepaths="yes" externalpreview="no" url="" htmlbaseurl="" outputurl="" processortype="saxon8" useresolver="no" profilemode="0" profiledepth="" profilelength="" urlprofilexml="" commandline=""
		          additionalpath="" additionalclasspath="" postprocessortype="none" postprocesscommandline="" postprocessadditionalpath="" postprocessgeneratedext="" validateoutput="no" validator="internal" customvalidator="">
			<advancedProp name="sInitialMode" value=""/>
			<advancedProp name="bXsltOneIsOkay" value="true"/>
			<advancedProp name="bSchemaAware" value="false"/>
			<advancedProp name="bGenerateByteCode" value="true"/>
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