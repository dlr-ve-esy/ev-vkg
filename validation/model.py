from __future__ import annotations
from pydantic import ValidationError
from datetime import date
from typing import List, Optional

from pydantic import AnyUrl, AwareDatetime, BaseModel, ConfigDict, EmailStr, Field


class SubjectItem(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    name: Optional[str] = Field(
        None,
        description="The class label of the OEO term.",
        examples=["energy"],
        title="Name",
    )
    path: Optional[AnyUrl] = Field(
        None,
        description="The URI of the class.",
        examples=["https://openenergyplatform.org/ontology/oeo/OEO_00000150"],
        title="Path",
    )


class Context(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    homepage: Optional[AnyUrl] = Field(
        None,
        description="URL of project.",
        examples=["https://openenergyplatform.org/"],
        title="Homepage",
    )
    documentation: Optional[str] = Field(
        None,
        description="A URL of the project's documentation.",
        examples=["https://openenergyplatform.org/about/"],
        title="Documentation",
    )
    sourceCode: Optional[str] = Field(
        None,
        description="A URL of the projects source code.",
        examples=["https://github.com/OpenEnergyPlatform"],
        title="Source Code",
    )
    contact: Optional[EmailStr] = Field(
        None,
        description="A reference to the creator or maintainer of the data set. This can be an email address or a GitHub handle.",
        examples=["contact@example.com"],
        title="E-Mail Contact",
    )
    grantNo: Optional[str] = Field(
        None,
        description="An identifying grant number. In case of a publicly funded project, this number is assigned by the funding agency.",
        examples=["01AB2345"],
        title="Grant no",
    )
    fundingAgency: Optional[str] = Field(
        None,
        description="In a funded project this is the funding agency, which can be a governmental or a company.",
        examples=["Bundesministerium für Wirtschaft und Klimaschutz"],
        title="Funding agency",
    )
    fundingAgencyLogo: Optional[AnyUrl] = Field(
        None,
        description="A URL to the logo or image of the funding agency.",
        examples=[
            "https://commons.wikimedia.org/wiki/File:BMWi_Logo_2021.svg#/media/File:BMWi_Logo_2021.svg"
        ],
        title="Funding agency logo",
    )
    publisherLogo: Optional[AnyUrl] = Field(
        None,
        description="A URL to the logo of the agency publishing the data.",
        examples=[
            "https://reiner-lemoine-institut.de//wp-content/uploads/2015/09/rlilogo.png"
        ],
        title="Publisher logo",
    )


class Spatial(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    location: Optional[str] = Field(
        None,
        description="A location of the data. In case of data where the location can be described as a point. May be specified as coordinates, URI or addresses with street, house number and zip code.",
        examples=["52.433509, 13.535855"],
        title="Location",
    )
    extent: Optional[str] = Field(
        None,
        description="A covered area. May be the name of a region, or the geometry of a bounding box.",
        examples=["Europe"],
        title="Extent",
    )
    resolution: Optional[str] = Field(
        None,
        description="Pixel size in case of a regular raster image. Reference to administrative level or other spatial division that is present as the smallest spatially distinguished unit size.",
        examples=["3 m"],
        title="Resolution",
    )


class Timesery(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    start: Optional[AwareDatetime] = Field(
        None,
        description="The beginning point in time of a time series.",
        examples=["2019-02-06T10:12:04+00:00"],
        title="Start",
    )
    end: Optional[AwareDatetime] = Field(
        None,
        description="The end point in time of a time series.",
        examples=["2019-02-07T10:12:04+00:00"],
        title="End",
    )
    resolution: Optional[str] = Field(
        None,
        description="The time span between individual points of information in a time series.",
        examples=[" 30 s"],
        title="Resolution",
    )
    alignment: Optional[str] = Field(
        None,
        description="An indicator whether stamps in a time series are left, right or middle.",
        examples=["left"],
        title="Alignment",
    )
    aggregationType: Optional[str] = Field(
        None,
        description="Indicates whether the values are a sum, average or current.",
        examples=["sum"],
        title="Aggregation type",
    )


class Temporal(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    referenceDate: Optional[date] = Field(
        None,
        description="The base year, month or day. Point in time for which the data is meant to be accurate. The census data or a satellite image will have a reference date. Date Format is ISO 8601.",
        examples=["2016-01-01"],
        title="Reference date",
    )
    timeseries: Optional[List[Timesery]] = Field(
        None,
        description="A list of objects that describe the timeseries. It contains start, end, resolution, alignment and aggregation type properties.",
        title="Timeseries",
    )


class License(BaseModel):
    name: Optional[str] = Field(
        None, description="THe SPDX identifier.", examples=["ODbL-1.0"], title="Name"
    )
    title: Optional[str] = Field(
        None,
        description="The official (human readable) title of the license.",
        examples=["Open Data Commons Open Database License 1.0"],
        title="Title",
    )
    path: Optional[str] = Field(
        None,
        description="A link to the license text.",
        examples=["https://opendatacommons.org/licenses/odbl/1-0/index.html"],
        title="Path",
    )
    instruction: Optional[str] = Field(
        None,
        description="A short description of rights and restrictions. The use of tl;drLegal is recommended.",
        examples=[
            "You are free to share and change, but you must attribute, and share derivations under the same license. See https://tldrlegal.com/license/odc-open-database-license-(odbl) for further information."
        ],
        title="Instruction",
    )
    attribution: Optional[str] = Field(
        None,
        description="The copyright owner of the source. Copyright owner name must be acknowledged if attribution licenses are used.",
        examples=["© Intergovernmental Panel on Climate Change 2014"],
        title="Attribution",
    )


class Source(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    title: Optional[str] = Field(
        None,
        description="A human readable title of the source, a document title or organisation name.",
        examples=["IPCC Fifth Assessment Report"],
        title="Title",
    )
    description: Optional[str] = Field(
        None,
        description="A free text description of the data set.",
        examples=["Scientific climate change report by the UN"],
        title="Description",
    )
    path: Optional[AnyUrl] = Field(
        None,
        description="A URL to the original source.",
        examples=[
            "https://www.ipcc.ch/site/assets/uploads/2018/02/ipcc_wg3_ar5_full.pdf"
        ],
        title="Path",
    )
    licenses: Optional[List[License]] = Field(
        None,
        description="The license(s) under which the source(s) is/are provided. List of objects.",
        title="Licenses",
    )


class License1(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    name: Optional[str] = Field(
        None, description="The SPDX identifier.", examples=["ODbL-1.0"], title="Name"
    )
    title: Optional[str] = Field(
        None,
        description="The official (human readable) title of the license.",
        examples=["Open Data Commons Open Database License 1.0"],
        title="Title",
    )
    path: Optional[str] = Field(
        None,
        description="A url-or-path string, that is a fully qualified HTTP address, or a relative POSIX path (see the url-or-path definition in Data Resource for details).",
        examples=["https://opendatacommons.org/licenses/odbl/1-0/index.html"],
        title="Path",
    )
    instruction: Optional[str] = Field(
        None,
        description="A short description of rights and restrictions. The use of tl;drLegal is recommended.",
        examples=[
            "You are free to share and change, but you must attribute, and share derivations under the same license. See https://tldrlegal.com/license/odc-open-database-license-(odbl) for further information."
        ],
        title="Instruction",
    )
    attribution: Optional[str] = Field(
        None,
        description="The copyright holder of the data set. If attribution licenses are used, that name must be acknowledged.",
        examples=["© Reiner Lemoine Institut"],
        title="Attribution",
    )


class Contributor(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    title: Optional[str] = Field(
        None,
        description="Name/title of the contributor (name for a person, name or title for an organization).",
        examples=["John Doe"],
        title="Title",
    )
    email: Optional[EmailStr] = Field(
        None,
        description="E-mail address of the contributor.",
        examples=["contact@example.com"],
        title="Email",
    )
    contributionDate: Optional[date] = Field(
        None,
        description="Date of the contribution. If the contribution took more than a day, use the date of the final contribution. Date Format is ISO 8601.",
        examples=["2016-06-16"],
        title="Date",
    )
    object: Optional[str] = Field(
        None,
        description="Target of contribution. Which part of the package was supplied/changed.",
        examples=["data and metadata"],
        title="Object",
    )
    comment: Optional[str] = Field(
        None,
        description="Free text comment on what has been done.",
        examples=["Fix typo in the title."],
        title="Comment",
    )


class IsAboutItem(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    name: Optional[str] = Field(
        None,
        description="A class label of the OEO terms.",
        examples=["wind energy converting unit"],
        title="Name",
    )
    path: Optional[AnyUrl] = Field(
        None,
        description="Path to the OEO class (URI)",
        examples=["https://openenergyplatform.org/ontology/oeo/OEO_00000044"],
        title="Path",
    )


class ValueReferenceItem(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    value: Optional[str] = Field(
        None,
        description="The name of the value in the column.",
        examples=["onshore"],
        title="Value",
    )
    name: Optional[str] = Field(
        None,
        description="The class label of the OEO terms.",
        examples=["onshore wind farm"],
        title="Name",
    )
    path: Optional[AnyUrl] = Field(
        None,
        description=" The URI of the OEO class",
        examples=["https://openenergyplatform.org/ontology/oeo/OEO_00000311"],
        title="Path",
    )


class FieldModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    name: Optional[str] = Field(
        None,
        description="The name of the field. The string must be unique within it's scope",
        examples=["year"],
        title="Name",
    )
    description: Optional[str] = Field(
        None,
        description="A text describing the field.",
        examples=["Reference year for which the data were collected."],
        title="Description",
    )
    type: Optional[str] = Field(
        None,
        description="The data type of the field. In case of a geom column in a database, also indicate the shape and CRS.",
        examples=["geometry(Point, 4326)"],
        title="Type",
    )
    isAbout: Optional[List[IsAboutItem]] = Field(
        None, description="Ontology URI to describe the column header", title="isAbout"
    )
    valueReference: Optional[List[ValueReferenceItem]] = Field(
        None,
        description="Ontology URI for an extended description of the values in the column",
        title="valueReference",
    )
    unit: Optional[str] = Field(
        None,
        description="The unit, preferably SI-unit, that values in this field are mapped to. If 'unit' doesn't apply to a field, use 'null'. If the unit is given in a separate field, reference this field.",
        examples=["MW"],
        title="Unit",
    )


class Reference(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    resource: Optional[str] = Field(
        None,
        description="The foreign resource (table).",
        examples=["schema.table"],
        title="Resource",
    )
    fields: Optional[List[Optional[str]]] = Field(
        None,
        description="The foreign resource column.",
        examples=["version"],
        title="Field",
    )


class ForeignKey(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    fields: Optional[List[Optional[str]]] = Field(
        None,
        description="The column (as list of items) in the table that is constrained by the foreign key.",
        examples=["version"],
        title="Fields",
    )
    reference: Optional[Reference] = Field(
        None, description="The reference to the foreign table.", title="Reference"
    )


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    fields: Optional[List[FieldModel]] = Field(
        None, description="List of field objects.", title="Field"
    )
    primaryKey: Optional[List[Optional[str]]] = Field(
        None,
        description="A primary key is a field or set of fields that uniquely identifies each row in the table. It's recorded as a list of strings, since it is possible to define the primary key as made up of several columns.",
        examples=["id"],
        title="Primary key",
    )
    foreignKeys: Optional[List[ForeignKey]] = Field(
        None, description="List of foreign keys.", title="Foreign Keys"
    )


class Dialect(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    delimiter: Optional[str] = Field(
        None,
        description='The delimiter specifies the character sequence which should separate fields (columns). Common characters are "," (comma), "." (point) and "\\t" (tab).',
        examples=[","],
        title="Delimiter",
    )
    decimalSeparator: Optional[str] = Field(
        None,
        description='A symbol used to separate the integer part from the fractional part of a number written in decimal form. Depending on language and region this symbol can be "." or ",".',
        examples=["."],
        title="Decimal separator",
    )


class Resource(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    profile: Optional[str] = Field(
        None,
        description='A string identifying the profile of this descriptor as per the profiles specification. This information is retained in order to comply with the "Tabular Data Package" standard. If at all in doubt the value should read "tabular-data-resource".',
        examples=["tabular-data-resource"],
        title="Profile",
    )
    name: Optional[str] = Field(
        None,
        description='A resource MUST contain a name unique to amongst all resources in this data package. To comply with the data package standard it must consist of only lowercase alphanumeric character plus ".", "-" and "_". It may not start with a number. In a database this will be the name of the table within its containing schema. It would be usual for the name to correspond to the file name (minus the file-extension) of the data file the resource describes. Example:',
        examples=["sandbox.example_table"],
        title="Name",
    )
    path: Optional[str] = Field(
        None,
        description="A URL that should be a permanent http(s) address or other path directly linking to the resource.",
        examples=[
            "https://openenergyplatform.org/dataedit/view/openstreetmap/osm_deu_line"
        ],
        title="Path",
    )
    format: Optional[str] = Field(
        None,
        description="The file extension. 'csv', 'xls', 'json' etc. are expected to be the standard file extension for this type of resource. When you upload your data to the OEP, in the shown metadata string, the format will be changed accordingly to 'PostgreSQL', since the data there are stored in a database.",
        examples=["csv"],
        title="Format",
    )
    encoding: Optional[str] = Field(
        None,
        description='Specifies the character encoding of the resource\'s data file. The values should be one of the "Preferred MIME Names" for a character encoding registered with IANA. If no value for this key is specified then the default is UTF-8.',
        examples=["UTF-8"],
        title="Encoding",
    )
    schema_: Optional[Schema] = Field(
        None,
        alias="schema",
        description="Object containing fields, primary key and for foreign keys. Describes the structure of the present data.",
        title="Schema",
    )
    dialect: Optional[Dialect] = Field(
        None,
        description='Object. A CSV Dialect defines a simple format to describe the various dialects of CSV files in a language agnostic manner. In case of a database, the values in the containing fields are "null".',
        title="Dialect",
    )


class Review(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    path: Optional[str] = Field(
        None,
        description="A URL or path string, that should be a permanent http(s) address directly linking to the documented review.",
        examples=["https://www.example.com"],
        title="Path",
    )
    badge: Optional[str] = Field(
        None,
        description="A badge of either Bronze, Silver, Gold or Platinum is used to label the given metadata based on its quality.",
        examples=["Platinum"],
        title="Badge",
    )


class MetadataLicense(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    name: Optional[str] = Field(
        None, description="SPDX identifier", examples=["CC0-1.0"], title="Name"
    )
    title: Optional[str] = Field(
        None,
        description="Official (human readable) license title.",
        examples=["Creative Commons Zero v1.0 Universal"],
        title="Title",
    )
    path: Optional[str] = Field(
        None,
        description="Url or path string, that is a fully qualified HTTP address.",
        examples=["https://creativecommons.org/publicdomain/zero/1.0"],
        title="Path",
    )


class MetaMetadata(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    metadataVersion: Optional[str] = Field(
        None,
        description="Type and version number of the metadata.",
        examples=["OEM-1.6.0"],
        title="Metadata version",
    )
    metadataLicense: Optional[MetadataLicense] = Field(
        None,
        description="Object describing the license of the provided metadata.",
        title="Metadata license",
    )


class FieldComment(BaseModel):
    metadata: Optional[str] = Field(
        None,
        description="Reference to the metadata documentation in use. Example: Metadata documentation and explanation (https://github.com/OpenEnergyPlatform/organisation/wiki/metadata)",
        title="Metadata",
    )
    dates: Optional[str] = Field(
        None,
        description="Comment on data/time format. Example: Dates and time must follow the ISO8601 including time zone (YYYY-MM-DD or YYYY-MM-DDThh:mm:ss±hh)",
        title="Dates",
    )
    units: Optional[str] = Field(
        None,
        description="Comment on units. Example: If you must use units in cells (which is discouraged), leave a space between numbers and units (100 m)",
        title="Units",
    )
    languages: Optional[str] = Field(
        None,
        description="Comment on language format. Example: Languages must follow the IETF (BCP47) format (en-GB, en-US, de-DE)",
        title="Languages",
    )
    licenses: Optional[str] = Field(
        None,
        description="Reference to license format. Example: License name must follow the SPDX License List (https://spdx.org/licenses/)",
        title="Licenses",
    )
    review: Optional[str] = Field(
        None,
        description="Reference to review documentation. Example: Following the OEP Data Review (https://github.com/OpenEnergyPlatform/data-preprocessing/wiki)",
        title="Review",
    )
    null: Optional[str] = Field(
        None,
        description='Feel free to add more descriptive comments. Like "null". Example: If a field is not applicable just enter "null"',
        title="Null",
    )
    todo: Optional[str] = Field(
        None,
        description="If an applicable value is not yet available and will be inserted later on use: 'todo' ",
        title="Todo",
    )


class Model(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    field_context: Optional[str] = Field(
        None,
        alias="@context",
        description="Explanation of metadata keys in ontology terms.",
        examples=[
            "https://raw.githubusercontent.com/LOD-GEOSS/databus-snippets/production/oep_metadata/context.jsonld"
        ],
        title="@context",
    )
    name: Optional[str] = Field(
        None,
        description="File name or database table name",
        examples=["oep_metadata_table_example_v160"],
        title="Name",
    )
    title: Optional[str] = Field(
        None,
        description="A Human readable, full title , including author.",
        examples=["RLI - OEMetadata - Metadata example table"],
        title="Title",
    )
    id: Optional[str] = Field(
        None,
        description="Uniform Resource Identifier (URI) that unambiguously identifies the resource. This can be a URL on the data set. It can also be a Digital Object Identifier (DOI).",
        examples=["https://example.com"],
        title="ID",
    )
    field_id: Optional[str] = Field(
        None,
        alias="@id",
        description="A Uniform Resource Identifier (URI) that links the resource via the DBpedia Databus",
        examples=["https://databus.dbpedia.org/kurzum/mastr/bnetza-mastr/01.04.00"],
        title="@Id",
    )
    description: Optional[str] = Field(
        None,
        description="A description of the package. It should be usable as summary information for the entire package that is described by the metadata.",
        examples=[
            "Example table used to illustrate the metadata structure and meaning."
        ],
        title="Description",
    )
    subject: Optional[List[SubjectItem]] = Field(
        None,
        description="Reference the topic of the resource in ontology terms",
        title="Subject",
    )
    language: Optional[List[Optional[str]]] = Field(
        None,
        description="List of languages used within the described data structures (e.g. titles, descriptions). Standard: IETF (BCP47).",
        examples=["[en-GB, de-DE, fr-FR]"],
        title="Language",
    )
    keywords: Optional[List[Optional[str]]] = Field(
        None,
        description="A list of string keywords to assist users searching for the package in catalogs.",
        examples=["[example, template, test]"],
        title="Keywords",
    )
    publicationDate: Optional[date] = Field(
        None,
        description="Date of publishing. Date Format is ISO 8601 (YYYY-MM-DD)",
        examples=["2019-02-06"],
        title="Publication date",
    )
    context: Optional[Context] = Field(
        None,
        description="An Object that describes the general setting, environment or project leading to the creation or maintenance of this dataset. In science this can be the research project.",
        title="Context",
    )
    spatial: Optional[Spatial] = Field(
        None,
        description="An object that describes the spatial context of the data it contains.",
        title="Spatial",
    )
    temporal: Optional[Temporal] = Field(
        None,
        description='An object with the time period covered in the data. Temporal information should either contain a "referenceDate" or the keys describing a time series; in rare cases both.',
        title="Temporal",
    )
    sources: Optional[List[Source]] = Field(
        None,
        description="List of source objects. Each object has all name-value-pairs.",
        title="Sources",
    )
    licenses: Optional[List[License1]] = Field(
        None,
        description="The license(s) under which the described package is provided. List of objects.",
        title="Licenses",
    )
    contributors: Optional[List[Contributor]] = Field(
        None,
        description="The people or organizations who contributed to this data package. List of objects.",
        title="Contributors",
    )
    resources: Optional[List[Resource]] = Field(
        None,
        description="Resources, described as a list of data resource format objects.",
        title="Resource",
    )
    review: Optional[Review] = Field(
        None,
        description="Data uploaded through the OEP needs to go through review. The review will cover the areas described here: https://github.com/OpenEnergyPlatform/data-preprocessing/wiki and carried out by a team of the platform. The review itself is documented at the specified path and a badge is rewarded with regards to completeness.",
        title="Review",
    )
    metaMetadata: Optional[MetaMetadata] = Field(
        None,
        description="Object. Description about the metadata themselves, their format, version and license. These fields should already be provided when you’re filling out your metadata.",
        title="Meta Metadata",
    )
    field_comment: Optional[FieldComment] = Field(
        None,
        alias="_comment",
        description="Object. The “_comment”-section is used as a self-description of the final metadata-file. It is text, intended for humans and can include a link to the metadata documentation(s), required value formats and similar remarks. The comment section has no fix structure or mandatory values, but a useful self-description, similar to the one depicted here, is encouraged.",
        title="_comment",
    )
