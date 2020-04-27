<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="2.0"
  xmlns:cvs="http://nwalsh.com/rdf/cvs#" xmlns:dcterms="http://purl.org/dc/terms/"
  xmlns:tei="http://www.tei-c.org/ns/1.0"
  xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
  xpath-default-namespace="http://www.tei-c.org/ns/1.0">
  <xsl:output method="xml" indent="yes"/>

  <xsl:param name="xuser"/>
  <xsl:param name="xlog"/>
  <xsl:param name="xdate"/>
  <xsl:param name="xversion"/>
  <xsl:param name="xfile"/>

  <xsl:template match="/">
    <xsl:apply-templates select="TEI"/>
  </xsl:template>

  <xsl:template match="TEI">
    <rdf:RDF>
      <rdf:Description rdf:about="{$xfile}">
        <dc:identifier><xsl:value-of select="teiHeader/fileDesc/sourceDesc/msDesc/msIdentifier/altIdentifier/idno[@type='iunp']"/></dc:identifier>
        <dc:title><xsl:value-of select="teiHeader/fileDesc/sourceDesc/msDesc/msContents/msItem/title"/></dc:title>
        <dc:language><xsl:apply-templates select="teiHeader/profileDesc/langUsage/language"/></dc:language>
        <dc:relation><xsl:apply-templates select="teiHeader/fileDesc/sourceDesc/msDesc/msIdentifier"/></dc:relation>
        <dc:coverage>
          <xsl:variable name="status" select="teiHeader/fileDesc/publicationStmt/availability/@status"/>
          <xsl:choose>
            <xsl:when test="$status = 'restricted'">Development</xsl:when>
            <xsl:when test="$status='free'">Production</xsl:when>
            <xsl:when test="$status = 'unknown'">Unknown</xsl:when>
          </xsl:choose>
        </dc:coverage>
        <dc:date><xsl:value-of select="teiHeader/fileDesc/titleStmt/title[not(@type='gmd')]/date/@value"/></dc:date>
        <cvs:log><xsl:value-of select="$xlog"/></cvs:log>
        <cvs:date><xsl:value-of select="$xdate"/></cvs:date>
        <cvs:revision><xsl:value-of select="$xversion"/></cvs:revision>
        <cvs:author><xsl:value-of select="$xuser"/></cvs:author>
      </rdf:Description>
    </rdf:RDF>
  </xsl:template>

  <xsl:template match="msIdentifier">
    <xsl:value-of select="collection" /><xsl:text> </xsl:text><xsl:value-of select="idno"/>,<xsl:text> </xsl:text><xsl:value-of select="institution" />
  </xsl:template>

  <xsl:template match="language">
    <xsl:value-of select="."/><xsl:text>&#160;</xsl:text>
  </xsl:template>

  <xsl:template match="*"/>
</xsl:stylesheet>
