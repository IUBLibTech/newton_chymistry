<?xml version="1.1"?>
<xsl:stylesheet version="2.0" 
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
	xmlns:c="http://www.w3.org/ns/xproc-step" 
	xmlns:xs="http://www.w3.org/2001/XMLSchema"
	xmlns:nma="tag:conaltuohy.com,2018:nma"
	xmlns:f="http://www.w3.org/2005/xpath-functions"
	exclude-result-prefixes="xs nma">

	<xsl:param name="solr-base-uri"/>
	<xsl:param name="default-results-limit" required="true"/>	
	
	<xsl:variable name="fields-definition" select="/*/fields"/>
	
	<!-- Transform the user's HTTP request into an outgoing HTTP request to Solr using Solr's JSON request API 
	https://lucene.apache.org/solr/guide/7_6/json-request-api.html -->
	
	<!-- The incoming request has been parsed into a set of parameters i.e. c:param-set, and aggregated with the field definitions -->
	<xsl:template match="/">
		<c:request method="post" href="{$solr-base-uri}query">
			<c:body content-type="application/xml">
				<xsl:apply-templates select="/*/c:param-set"/>
			</c:body>
		</c:request>
	</xsl:template>
	
	<xsl:template match="c:param-set">
		<f:map>
			<f:map key="params">
				<xsl:if test="c:param[@name='text']/@value">
					<!-- only if we have a "text" query parameter, can we can request hit-highlighting: -->
					<f:boolean key="hl">true</f:boolean>
					<f:boolean key="hl.mergeContiguous">true</f:boolean>
					<f:string key="hl.fl">normalized,diplomatic,introduction</f:string>
					<f:string key="hl.q">text:<xsl:value-of select="c:param[@name='text']/@value"/></f:string>
					<f:string key="hl.snippets">10</f:string>
					<f:number key="hl.maxAnalyzedChars">-1</f:number><!-- analyze the entire text -->
				</xsl:if>
			</f:map>
			<f:string key="query">*:*</f:string>
			<!-- request only the values of certain fields -->
			<!--<f:string key="fl">id title introduction</f:string>-->
			<!-- the Solr 'offset' and 'limit' query parameters control pagination -->
			<!-- if 'page' is blank, then it counts as 1. e.g. if $default-results-limit=2 and page=1 then offset=2*(1-1)=0 -->
			<xsl:variable name="page" select=" (c:param[@name='page']/@value, 1)[1] "/>
			<f:number key="offset"><xsl:value-of select="$default-results-limit * ($page - 1)"/></f:number>
			<f:number key="limit"><xsl:value-of select="$default-results-limit"/></f:number>
			<!-- Any parameter other than 'page' is assumed to a field in Solr -->
			<xsl:variable name="control-parameter-names" select="('page')"/>
			<xsl:variable name="search-fields" select="c:param[not(@name = $control-parameter-names)]"/>
			<!-- impose a sort order; sort by descending score, then by the value of the "sort" field, ascending -->
			<f:string key="sort">score desc, sort asc</f:string>
			<f:array key="filter">
				<xsl:for-each-group group-by="@name" select="$search-fields[normalize-space(@value)]">
					<!-- the param/@name specifies the field's name; look up the field by name and get field's definition -->
					<xsl:variable name="field-name" select="@name"/>
					<xsl:variable name="field-value" select="@value"/>
					<xsl:variable name="field-definition" select="$fields-definition/field[@name=$field-name]"/>
					<xsl:variable name="field-range" select="$field-definition/@range"/>
					<xsl:choose>
						<xsl:when test="$field-range">
							<f:string><xsl:value-of select="
								concat(
									'{!tag=', $field-name, '}', 
									string-join(
										for $field-value in current-group()/@value return concat(
											$field-name, 
											':[&quot;', 
											$field-value,
											'/', $field-range,
											'&quot; TO &quot;',
											$field-value,
											'/', $field-range, '+1', $field-range,
											'&quot;]'
										),
										' OR '
									)
								)
							"/></f:string>
						</xsl:when>
						<xsl:otherwise>
							<f:string><xsl:value-of select="
								concat(
									'{!tag=', $field-name, '}', 
									string-join(
										for $field-value in current-group()/@value return concat(
											$field-name, ':&quot;', $field-value, '&quot;'
										),
										' OR '
									)
								)
							"/></f:string>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:for-each-group>
			</f:array>
			<f:map key="facet">
				<xsl:for-each select="$fields-definition/field[@type='facet']">
					<f:map key="{@name}">
						<xsl:if test="@missing"><!-- include a count of records which are missing a value for this facet -->
							<f:boolean key="missing">true</f:boolean>
						</xsl:if>
						<xsl:choose>
							<xsl:when test="range">
								<!-- facet/range specifies a range unit; either MONTH, DAY, or YEAR -->
								<f:string key="type">range</f:string>
								<!-- e.g. "NOW/DAY-1MONTH", "NOW/MONTH-1YEAR" -->
								<f:string key="start"><xsl:value-of select="concat('NOW/', range, start)"/></f:string>
								<!-- e.g. "+1DAY", "+1MONTH" -->
								<f:string key="gap"><xsl:value-of select="concat('+1', range)"/></f:string>
								<!-- e.g. "NOW/+1DAY", "NOW/+1MONTH" -->
								<f:string key="end"><xsl:value-of select="concat('NOW/', range, '+1', range)"/></f:string>
							</xsl:when>
							<xsl:otherwise>
								<f:string key="type">terms</f:string>
							</xsl:otherwise>
						</xsl:choose>
						<f:string key="field"><xsl:value-of select="@name"/></f:string>
						<f:number key="mincount">0</f:number>
						<f:number key="limit">40</f:number>
						<f:boolean key="numBuckets">true</f:boolean>
						<f:map key="domain">
							<f:string key="excludeTags"><xsl:value-of select="@name"/></f:string>
						</f:map>
					</f:map>
				</xsl:for-each>
			</f:map>
		</f:map>
	</xsl:template>
		
</xsl:stylesheet>
