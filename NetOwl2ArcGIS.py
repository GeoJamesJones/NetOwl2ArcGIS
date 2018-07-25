
import arcgis
import os
import csv
import json
import glob
import requests
import zipfile
import time
import string

import pandas as pd

from arcgis import geometry
from arcgis.gis import GIS
from copy import deepcopy

filePath = r'C:\xampp\htdocs\camera\Docs'
json_out = r'C:\outFiles\JSON'
csv_out = r'C:\outFiles\CSV'

# Base web end point for the hosted images
baseWeb = 'http://40.76.87.212/camera/'

# Hosted location for the marked up images
web_markUp = baseWeb + 'Docs/'

gis = GIS('https://wdcdefense.esri.com/portal/', 'james_jones', 'QWerty654321@!')

class RDFitem:
    """Model to hold non-geo or ready to geocode items."""

    def __init__(self, rdfid, rdfvalue, timest, orgdoc, ontology, rdflinks=None):  # noqa: E501
        """Docstring."""
        self.id = rdfid
        self.links = [] if rdflinks is None else rdflinks  # list - optional
        self.value = rdfvalue
        self.timest = timest
        self.orgdoc = orgdoc
        self.type = ontology


class RDFitemGeo(RDFitem):
    """Model to hold objs with lat/long already assigned."""

    def __init__(self, rdfid, rdfvalue, longt, latt, timest,
                 orgdoc, rdflinks=None):
        """Docstring."""
        self.id = rdfid
        self.links = [] if rdflinks is None else rdflinks  # list - optional
        self.value = rdfvalue
        self.lat = latt
        self.long = longt
        self.timest = timest
        self.orgdoc = orgdoc

    def set_type(self, typeofgeo):
        """Docstring."""
        self.type = typeofgeo

    def set_subtype(self, subtypegeo):
        """Docstring."""
        self.subtype = subtypegeo

    def set_link_details(self, details):
        """Docstring."""
        self.linkdetails = details


class RDFlinkItem():
    """Model to hold link objs."""

    def __init__(self, linkid, fromid, toid, fromvalue, tovalue,
                 fromrole, torole, fromroletype, toroletype, timest):
        """Docstring."""
        self.linkid = linkid
        self.fromid = fromid
        self.toid = toid
        self.fromvalue = fromvalue
        self.tovalue = tovalue
        self.fromrole = fromrole
        self.torole = torole
        self.fromroletype = fromroletype
        self.toroletype = toroletype
        self.timest = timest

def cleanup_text(intext):
    """Function to remove funky chars."""
    printable = set(string.printable)
    p = ''.join(filter(lambda x: x in printable, intext))
    g = p.replace('"', "")
    return g


def geocode_address(address):
    """Use World Geocoder to get XY for one address at a time."""
    querystring = {
        "f": "json",
        "singleLine": address}
    url = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"  # noqa: E501
    response = requests.request("GET", url, params=querystring)
    p = response.text
    j = json.loads(p)
    location = j['candidates'][0]['location']  # returns first location as X, Y
    return location

#Defines a function that will pass documents derived from the list
# above to the NetOwl API.  
#Function checks the type of document and makes necessary adjustment 
# to the POST command.
#Function has three inputs:
#    1.  inFile:  This is the file that will be passed to the NetOwl API
#    2.  outPath: Path where the output file will be saved
#    3.  outExtension:  the file type that will be saved (RDF, etc..)

def netowlCurl(infile, outpath, outextension):
    headers = {
        'accept': 'application/json',  # 'application/rdf+xml',
        'Authorization': 'netowl ff5e6185-5d63-459b-9765-4ebb905affc8',
    }

    if infile.endswith(".txt"):
        headers['Content-Type'] = 'text/plain'
    elif infile.endswith(".pdf"):
        headers['Content-Type'] = 'application/pdf'
    elif infile.endswith(".docx"):
        headers['Content-Type'] = 'application/msword'

    params = (
        ('language', 'english'),
    )

    data = open(infile, 'rb').read()
    response = requests.post('https://api.netowl.com/api/v2/_process',
                             headers=headers, params=params, data=data,
                             verify=False)
    r = response.text
    outpath = outpath
    filename = os.path.split(infile)[1]
    if os.path.exists(outpath) is False:
        os.mkdir(outpath, mode=0o777, )
    outfile = os.path.join(outpath, filename + outextension)
    open(outfile, "w", encoding="utf-8").write(r)
    return outfile

def make_link_list(linklist):
    """Turn linklist into string."""
    l = ""
    for u in linklist:
        l = l + " " + u
    return l[1:len(l)]

entity_points = gis.content.get("8d779fbd4ca94c9b98c6c9ead9e88d6a")
geo_entities_lyr = entity_points.layers[0]
geo_fset = geo_entities_lyr.query(where='OBJECTID= 1', return_geometry=True)
geo_all_features = geo_fset.features
geo_original_features = geo_all_features[0]
geo_template_feature = deepcopy(geo_original_features)

non_geo_entities_lyr = entity_points.tables[0]
non_geo_fset = non_geo_entities_lyr.query(where='OBJECTID= 1', return_geometry=False)
non_geo_all_features = non_geo_fset.features
non_geo_original_features = non_geo_all_features[0]
non_geo_template_feature = deepcopy(non_geo_original_features)

links_entities_lyr = entity_points.tables[1]
links_fset = links_entities_lyr.query(where='OBJECTID= 1', return_geometry=False)
links_all_features = links_fset.features
links_original_features = links_all_features[0]
links_template_feature = deepcopy(links_original_features)

docs = []
ext = ".json"
for root, dirs, files in os.walk(filePath):
    for file in files:
        pathFile = os.path.join(root, file)
        docs.append(filePath)
        outFile = netowlCurl(pathFile, json_out, ext)
        
        rdfobjs = []
        rdfobjsGeo = []
        linkobjs = []

        fn = file[:-5]
        with open(os.path.join(root, outFile), encoding='UTF-8') as j_file:
            data = json.load(j_file)
            uniquets = str(time.time())
            doc = data['document'][0]
            ents = (doc['entity'])
            for e in ents:

                # gather data from each entity
                rdfvalue = cleanup_text(e['value'])  # value (ie name)
                # rdfvalue = e['value']
                rdfid = e['id']  # rdfid (unique to each entity - with timestamp)  # noqa: E501

                # test for geo (decide which type of obj to make)
                if 'geodetic' in e:
                    if 'entity-ref' in e:
                        # print("already plotted elsewhere...")
                        isGeo = False  # already plotted, relegate to rdfobj list  # noqa: E501
                        skiplinks = True
                    else:
                        lat = float(e['geodetic']['latitude'])
                        longg = float(e['geodetic']['longitude'])
                        isGeo = True
                        skiplinks = False
                else:
                    isGeo = False
                    skiplinks = True

                # relationships
                # HACK - put into attribute table inside of fc rather than as link
                if 'link-ref' in e:
                    refrels = []
                    linkdescs = []  # add funct to describe link in attribute field
                    if skiplinks is not True:  # is false, plotting the point in Feature Class
                        for k in e['link-ref']:  # every link-ref per entity
                            refrels.append(k['idref'])  # keep these - all references  # noqa: E501
                            if 'role-type' in k:  # test the role type is source
                                if k['role-type'] == "source":
                                    linkdesc = rdfvalue + " is a " + k['role'] + " in " + k['entity-arg'][0]['value']  # noqa: E501
                                    linkdescs.append(linkdesc)
                                else:
                                    linkdescs.append("This item has parent links but no children")  # noqa: E501
                    haslinks = True

                else:
                    haslinks = False

                # check for addresses
                if e['ontology'] == "entity:address:mail":
                    address = e['value']
                    location = geocode_address(address)  # returns x,y
                    isGeo = True
                    # set lat long
                    lat = location['y']
                    longg = location['x']

                # build the objects
                if isGeo:
                    if haslinks:
                        # add refrels to new obj
                        rdfobj = RDFitemGeo(rdfid, rdfvalue, longg, lat, uniquets, refrels)
                        ld = str(linkdescs)
                        if len(ld) > 255:
                            ld = ld[:254]  # shorten long ones

                        rdfobj.set_link_details(ld)
                    else:
                        rdfobj = RDFitemGeo(rdfid, rdfvalue, longg, lat, uniquets, fn)  # noqa: E501
                        rdfobj.set_link_details("No links for this point")

                    # set type for symbology
                    rdfobj.set_type("placename")  # default
                    rdfobj.set_subtype("unknown")  # default
                    if e['ontology'] == "entity:place:city":
                        rdfobj.set_type("placename")
                        rdfobj.set_subtype("city")
                    if e['ontology'] == "entity:place:country":
                        rdfobj.set_type("placename")
                        rdfobj.set_subtype("country")
                    if e['ontology'] == "entity:place:province":
                        rdfobj.set_type("placename")
                        rdfobj.set_subtype("province")
                    if e['ontology'] == "entity:place:continent":
                        rdfobj.set_type("placename")
                        rdfobj.set_subtype("continent")
                    if e['ontology'] == "entity:numeric:coordinate:mgrs":
                        rdfobj.set_type("coordinate")
                        rdfobj.set_subtype("MGRS")
                    if e['ontology'] == "entity:numeric:coordinate:latlong":  # noqa: E501
                        rdfobj.set_type("coordinate")
                        rdfobj.set_subtype("latlong")
                    if e['ontology'] == "entity:address:mail":
                        rdfobj.set_type("address")
                        rdfobj.set_subtype("mail")
                    if e['ontology'] == "entity:place:other":
                        rdfobj.set_type("placename")
                        rdfobj.set_subtype("descriptor")
                    if e['ontology'] == "entity:place:landform":
                        rdfobj.set_type("placename")
                        rdfobj.set_subtype("landform")
                    if e['ontology'] == "entity:organization:facility":
                        rdfobj.set_type("placename")
                        rdfobj.set_subtype("facility")
                    if e['ontology'] == "entity:place:water":
                        rdfobj.set_type("placename")
                        rdfobj.set_subtype("water")
                    if e['ontology'] == "entity:place:county":
                        rdfobj.set_type("placename")
                        rdfobj.set_subtype("county")

                    rdfobjsGeo.append(rdfobj)

                else:  # not geo
                    ontology = e['ontology']
                    if haslinks:
                        rdfobj = RDFitem(rdfid, rdfvalue, uniquets, fn, ontology, refrels)  # noqa: E501
                    else:  # has neither links nor address
                        rdfobj = RDFitem(rdfid, rdfvalue, uniquets, fn, ontology)

                    rdfobjs.append(rdfobj)

            if 'link' in doc:
                linksys = (doc['link'])
                for l in linksys:
                    linkid = l['id']  # HOOCH
                    if 'entity-arg' in l:
                        fromid = l['entity-arg'][0]['idref']
                        toid = l['entity-arg'][1]['idref']
                        fromvalue = l['entity-arg'][0]['value']
                        tovalue = l['entity-arg'][1]['value']
                        fromrole = l['entity-arg'][0]['role']
                        torole = l['entity-arg'][1]['role']
                        fromroletype = l['entity-arg'][0]['role-type']
                        toroletype = l['entity-arg'][1]['role-type']
                    # build link objects -  ,uniquets
                    linkobj = RDFlinkItem(linkid, fromid, toid, fromvalue, tovalue,
                                      fromrole, torole, fromroletype,
                                      toroletype, uniquets)
                    linkobjs.append(linkobj)

        header = ["RDFID", "ENTITY", "TIMEST", "RDFLINKS", "TYPE", "SUBTYPE", "ORGDOC", "UNIQUEID", "LINKDETAILS", 'Long', 'Lat']
        rows = []
        filePath = web_markUp + file
        for r in rdfobjsGeo:


            features_to_be_added = []
            new_feature = deepcopy(geo_template_feature)
            
            input_geometry = {'y':r.lat,
                              'x':r.long}
            output_geometry = geometry.project(geometries = [input_geometry], 
                                               in_sr=geo_fset.spatial_reference['latestWkid'], 
                                               out_sr=geo_fset.spatial_reference['latestWkid'], 
                                               gis=gis)
            
            new_feature.geometry = output_geometry[0]
            new_feature.attributes['rdfid'] = r.id
            new_feature.attributes['rdfvalue'] = r.value
            new_feature.attributes['timest'] = r.timest
            # need less than 23 links or fc won't accept list (255 char max)
            if len(r.links) > 23:
                new_feature.attributes['rdflinks'] = r.links[0:22]
            else:
                new_feature.attributes['rdflinks'] = r.links

            new_feature.attributes['type'] = r.type
            new_feature.attributes['subtype'] = r.subtype
            new_feature.attributes['orgdoc'] = r.orgdoc
            new_feature.attributes['uniqueid'] = file + "_" + r.id
            new_feature.attributes['doclink'] = filePath

            features_to_be_added.append(new_feature)

        try: geo_entities_lyr.edit_features(adds=features_to_be_added)
        except: print("Error on adding geo features...")
            
        for d in rdfobjs:
            non_geo_features_to_be_added = []
            new_features = deepcopy(non_geo_template_feature)
			
            new_features.attributes['rdfid'] = d.id
            new_features.attributes['rdfvalue'] = d.value
            new_features.attributes['timest'] = d.timest
            new_features.attributes['orgdoc'] = d.orgdoc
            new_features.attributes['uniqueid'] = file + "_" + d.id 
            new_features.attributes['type'] = d.type
            new_features.attributes['doclink'] = filePath
            non_geo_features_to_be_added.append(new_features)

        try: 
            non_geo_entities_lyr.edit_features(adds=non_geo_features_to_be_added)
        except: 
            print("Error on adding non-geo feature")
		
        if len(linkobjs) > 0:
            for lo in linkobjs:
                link_features_to_be_added = []
                new_link_features = deepcopy(links_template_feature)
            
                new_link_features.attributes['linkid'] = file + "_" + lo.linkid
                new_link_features.attributes['fromid'] = file + "_" + lo.fromid
                new_link_features.attributes['toid'] = file + "_" + lo.toid
                new_link_features.attributes['fromvalue'] = lo.fromvalue
                new_link_features.attributes['tovalue'] = lo.tovalue
                new_link_features.attributes['fromrole'] = lo.fromrole
                new_link_features.attributes['torole'] = lo.torole
                new_link_features.attributes['fromroletype'] = lo.fromroletype
                new_link_features.attributes['toroletype'] = lo.toroletype
                new_link_features.attributes['uniquets'] = lo.timest
                new_link_features.attributes['doclink'] = filePath
            
                link_features_to_be_added.append(new_link_features)
        
            try: links_entities_lyr.edit_features(adds=link_features_to_be_added)
            except: print("Error on adding link feature")


