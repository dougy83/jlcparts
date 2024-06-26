import dataclasses
import re
import os
import shutil
import json
import datetime
import gzip
import multiprocessing
from pathlib import Path

import click
from jlcparts.partLib import PartLibraryDb
from jlcparts.common import sha256file
from jlcparts import attributes, descriptionAttributes

from jlcparts.attrnames import freqattr,capattr,resattr,powerattr,currentattr,voltsattr,timeattr


import tarfile

from time import time

def saveDatabaseFile(database, outpath, outfilename):
    with tarfile.open(os.path.join(outpath, outfilename), 'w') as tar:
        for key, value in database.items():
            filename = os.path.join(outpath, key + ".jsonlines.gz")
            with gzip.open(filename, "wt", encoding="utf-8") as f:
                for entry in value:
                    json.dump(entry, f, separators=(',', ':'), sort_keys=False)
                    f.write("\n")        
            tar.add(filename, arcname=os.path.relpath(filename, start=outpath))
            os.unlink(filename)

def weakUpdateParameters(attrs, newParameters):
    for attr, value in newParameters.items():
        if attr in attrs and attrs[attr] not in ["", "-"]:
            continue
        attrs[attr] = value

def extractAttributesFromDescription(description):
    if description.startswith("Chip Resistor - Surface Mount"):
        return descriptionAttributes.chipResistor(description)
    if (description.startswith("Multilayer Ceramic Capacitors MLCC") or
       description.startswith("Aluminum Electrolytic Capacitors")):
        return descriptionAttributes.capacitor(description)
    return {}

def normalizeUnicode(value):
    """
    Replace unexpected unicode sequence with a resonable ones
    """
    value = value.replace("（", " (").replace("）", ")")
    value = value.replace("，", ",")
    return value

def normalizeAttribute(key, value):
    """
    Takes a name of attribute and its value (usually a string) and returns a
    normalized attribute name and its value as a tuple. Normalized value is a
    dictionary in the format:
        {
            "format": <format string, e.g., "${Resistance} ${Power}",
            "primary": <name of primary value>,
            "values": <dictionary of values with units, e.g, { "resistance": [10, "resistance"] }>
        }
    The fallback is unit "string"
    """
    larr = lambda arr : map(lambda str : str.lower(), arr)
    normkey = normalizeAttributeKey(key)
    key = normkey.lower()
    if isinstance(value, str):
        value = normalizeUnicode(value)

    try:
        if key in larr(["Resistance", "Resistance in Ohms @ 25°C", "DC Resistance"] + resattr):
            value = attributes.resistanceAttribute(value)
        elif key in larr(["Balance Port Impedence", "Unbalance Port Impedence"]):
            value = attributes.impedanceAttribute(value)
        elif key in larr(["Voltage - Rated", "Voltage Rating - DC", "Allowable Voltage",
                "Clamping Voltage", "Varistor Voltage(Max)", "Varistor Voltage(Typ)",
                "Varistor Voltage(Min)", "Voltage - DC Reverse (Vr) (Max)",
                "Voltage - DC Spark Over (Nom)", "Voltage - Peak Reverse (Max)",
                "Voltage - Reverse Standoff (Typ)", "Voltage - Gate Trigger (Vgt) (Max)",
                "Voltage - Off State (Max)", "Voltage - Input (Max)", "Voltage - Output (Max)",
                "Voltage - Output (Fixed)", "Voltage - Output (Min/Fixed)",
                "Supply Voltage (Max)", "Supply Voltage (Min)", "Output Voltage",
                "Voltage - Input (Min)", "Drain Source Voltage (Vdss)", "Overload voltage (max)", "Rated output voltage"] + voltsattr):
            value = attributes.voltageAttribute(value)
        elif key in larr(["Rated current", "surge current", "Current - Average Rectified (Io)",
                    "Current - Breakover", "Current - Peak Output", "Current - Peak Pulse (10/1000μs)",
                    "Impulse Discharge Current (8/20us)", "Current - Gate Trigger (Igt) (Max)",
                    "Current - On State (It (AV)) (Max)", "Current - On State (It (RMS)) (Max)",
                    "Current - Supply (Max)", "Output Current", "Output Current (Max)",
                    "Output / Channel Current", "Current - Output",
                    "Saturation Current (Isat)", "Current rating"] + currentattr):
            value = attributes.currentAttribute(value)
        elif key in larr(["Power", "Power Per Element", "Power Dissipation (Pd)"] + powerattr):
            value = attributes.powerAttribute(value)
        elif key in larr(["Number of Pins", "Number of Resistors", "Number of Loop",
                    "Number of Regulators", "Number of Outputs", "Number of Capacitors"]):
            value = attributes.countAttribute(value)
        elif key in larr(["Capacitance"] + capattr):
            value = attributes.capacitanceAttribute(value)
        elif key in larr(["Inductance"]):
            value = attributes.inductanceAttribute(value)
        elif key == "Rds On (Max) @ Id, Vgs".lower():
            value = attributes.rdsOnMaxAtIdsAtVgs(value)
        elif key in larr(["Operating Temperature (Max)", "Operating Temperature (Min)"]):
            value = attributes.temperatureAttribute(value)
        elif key.startswith("Continuous Drain Current".lower()):
            value = attributes.continuousTransistorCurrent(value, "Id")
        elif key == "Current - Collector (Ic) (Max)".lower():
            value = attributes.continuousTransistorCurrent(value, "Ic")
        elif key in larr(["Vgs(th) (Max) @ Id", "Gate Threshold Voltage (Vgs(th)@Id)"]):
            value = attributes.vgsThreshold(value)
        elif key.startswith("Drain to Source Voltage".lower()):
            value = attributes.drainToSourceVoltage(value)
        elif key == "Drain Source On Resistance (RDS(on)@Vgs,Id)".lower():
            value = attributes.rdsOnMaxAtVgsAtIds(value)
        elif key == "Power Dissipation-Max (Ta=25°C)".lower():
            value = attributes.powerDissipation(value)
        elif key in larr(["Equivalent Series Resistance", "Impedance @ Frequency"]):
            value = attributes.esr(value)
        elif key == "Ripple Current".lower():
            value = attributes.rippleCurrent(value)
        elif key == "Size(mm)".lower():
            value = attributes.sizeMm(value)
        elif key == "Voltage - Forward (Vf) (Max) @ If".lower():
            value = attributes.forwardVoltage(value)
        elif key in larr(["Voltage - Breakdown (Min)", "Voltage - Zener (Nom) (Vz)",
            "Vf - Forward Voltage"]):
            value = attributes.voltageRange(value)
        elif key == "Voltage - Clamping (Max) @ Ipp".lower():
            value = attributes.clampingVoltage(value)
        elif key == "Voltage - Collector Emitter Breakdown (Max)".lower():
            value = attributes.vceBreakdown(value)
        elif key == "Vce(on) (Max) @ Vge, Ic".lower():
            value = attributes.vceOnMax(value)
        elif key in larr(["Input Capacitance (Ciss@Vds)",
                    "Reverse Transfer Capacitance (Crss@Vds)"]):
            value = attributes.capacityAtVoltage(value)
        elif key in larr(["Total Gate Charge (Qg@Vgs)"]):
            value = attributes.chargeAtVoltage(value)
        elif key in larr(["Frequency - self resonant", "Output frequency (max)"] + freqattr):
            value = attributes.frequencyAttribute(value)
        elif key in larr(timeattr):
            value = attributes.timeAttribute(value)
        else:
            value = attributes.stringAttribute(value)
    except: 
        print(f"Could not process key {normkey}; obj {value}")
        value = attributes.stringAttribute(value)   # fall back to string -- these values should have their patterns updated

    assert isinstance(value, dict)
    return normkey, value

def normalizeCapitalization(key):
    """
    Given a category name, normalize capitalization. We turn everything
    lowercase, but some known substring (such as MOQ or MHz) replace back to the
    correct capitalization
    """
    key = key.lower()
    CAPITALIZATIONS = [
        "Basic/Extended", "MHz", "GHz", "Hz", "MOQ"
    ]
    for capt in CAPITALIZATIONS:
        key = key.replace(capt.lower(), capt)
    key = key[0].upper() + key[1:]
    return key

def normalizeAttributeKey(key):
    """
    Takes a name of attribute and its value and returns a normalized key
    (e.g., strip unit name).
    """
    if "(Watts)" in key:
        key = key.replace("(Watts)", "").strip()
    if "(Ohms)" in key:
        key = key.replace("(Ohms)", "").strip()
    if key == "aristor Voltage(Min)":
        key = "Varistor Voltage(Min)"
    if key in ["ESR (Equivalent Series Resistance)", "Equivalent Series   Resistance(ESR)"] or key.startswith("Equivalent Series Resistance"):
        key = "Equivalent Series Resistance"
    if key in ["Allowable Voltage(Vdc)", "Voltage - Max", "Rated Voltage"] or key.startswith("Voltage Rated"):
        key = "Allowable Voltage"
    if key in ["DC Resistance (DCR)", "DC Resistance (DCR) (Max)", "DCR( Ω Max )"]:
        key = "DC Resistance"
    if key in ["Insertion Loss ( dB Max )", "Insertion Loss (Max)"]:
        key = "Insertion Loss (dB Max)"
    if key in ["Current Rating (Max)", "Rated Current"]:
        key = "Rated current"
    if key == "Power - Max":
        key = "Power"
    if key == "Voltage - Breakover":
        key = "Voltage - Breakdown (Min)"
    if key == "Gate Threshold Voltage-VGE(th)":
        key = "Vgs(th) (Max) @ Id"
    if key == "Pins Structure":
        key = "Pin Structure"
    if key.startswith("Lifetime @ Temp"):
        key = "Lifetime @ Temperature"
    if key.startswith("Q @ Freq"):
        key = "Q @ Frequency"
    return normalizeCapitalization(key)

def pullExtraAttributes(component):
    """
    Turn common properties (e.g., base/extended) into attributes. Return them as
    a dictionary
    """
    status = "Discontinued" if component["extra"] == {} else "Active"
    type = "Extended"
    if component["basic"]:
        type = "Basic"
    if component["preferred"]:
        type = "Preferred"
    return {
        "Basic/Extended": type,
        "Package": component["package"],
        "Status": status
    }

def crushImages(images):
    if not images:
        return None
    firstImg = images[0]
    img = firstImg.popitem()[1].rsplit("/", 1)[1]
    # make sure every url ends the same
    assert all(i.rsplit("/", 1)[1] == img for i in firstImg.values())
    return img

def trimLcscUrl(url, lcsc):
    if url is None:
        return None
    slug = url[url.rindex("/") + 1 : url.rindex("_")]
    assert f"https://lcsc.com/product-detail/{slug}_{lcsc}.html" == url
    return slug

def extractComponent(component, schema):
    try:
        propertyList = []
        for schItem in schema:
            if schItem == "attributes":
                # The cache might be in the old format
                if "attributes" in component.get("extra", {}):
                    attr = component.get("extra", {}).get("attributes", {})
                else:
                    attr = component.get("extra", {})
                if isinstance(attr, list):
                    # LCSC return empty attributes as a list, not dictionary
                    attr = {}
                attr.update(pullExtraAttributes(component))
                weakUpdateParameters(attr, extractAttributesFromDescription(component["description"]))

                # Remove extra attributes that are either not useful, misleading
                # or overridden by data from JLC
                attr.pop("url", None)
                attr.pop("images", None)
                attr.pop("prices", None)
                attr.pop("datasheet", None)
                attr.pop("id", None)
                attr.pop("manufacturer", None)
                attr.pop("number", None)
                attr.pop("title", None)
                attr.pop("quantity", None)
                for i in range(10):
                    attr.pop(f"quantity{i}", None)

                attr["Manufacturer"] = component.get("manufacturer", None)

                attr = dict([normalizeAttribute(key, val) for key, val in attr.items()])
                propertyList.append(attr)
            elif schItem == "img":
                images = component.get("extra", {}).get("images", None)
                propertyList.append(crushImages(images))
            elif schItem == "url":
                url = component.get("extra", {}).get("url", None)
                propertyList.append(trimLcscUrl(url, component["lcsc"]))
            elif schItem == "stock":
                propertyList.append(component["stock"])                
            elif schItem in component:
                item = component[schItem]
                if isinstance(item, str):
                    item = item.strip()
                propertyList.append(item)
            else:
                propertyList.append(None)
        return propertyList
    except Exception as e:
        raise RuntimeError(f"Cannot extract {component['lcsc']}").with_traceback(e.__traceback__)

def buildDatatable(components):
    schema = ["lcsc", "mfr", "joints", "description",
              "datasheet", "price", "img", "url", "attributes", "stock"]
    return {
        "schema": schema,
        "components": [extractComponent(x, schema) for x in components]
    }

def clearDir(directory):
    """
    Delete everything inside a directory
    """
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)

def schemaToLookup(schema):
    lut = {}
    for idx, key in enumerate(schema):
        lut[key] = idx
    return lut

def updateLut(lut, item):
    key = json.dumps(item, separators=(',', ':'), sort_keys=True)
    if not key in lut:
        index = len(lut)
        lut[key] = index
        return index
    return lut[key]

# Inverts the lut so that the Map becomes an array, with the key being the value.
# Values must be 0-based, numeric, and contiguous, or everything will be wrong.
def lutToArray(lutMap):
    arr = [None] * len(lutMap)
    for key, value in lutMap.items():
        arr[value] = key
    return arr

@dataclasses.dataclass
class MapCategoryParams:
    libraryPath: str
    outdir: str
    ignoreoldstock: int

    catName: str
    subcatName: str


def _map_category(val: MapCategoryParams):
    # Sometimes, JLC PCB doesn't fill in the category names. Ignore such
    # components.
    if val.catName.strip() == "":
        return None
    if val.subcatName.strip() == "":
        return None
    
    lib = PartLibraryDb(val.libraryPath)
    components = lib.getCategoryComponents(val.catName, val.subcatName, stockNewerThan=val.ignoreoldstock)
    if not components:
        return None
    
    dataTable = buildDatatable(components)
    dataTable.update({"category": val.catName, "subcategory": val.subcatName})
    return dataTable

@click.command()
@click.argument("library", type=click.Path(dir_okay=False))
@click.argument("outdir", type=click.Path(file_okay=False))
@click.option("--ignoreoldstock", type=int, default=None,
    help="Ignore components that weren't on stock for more than n days")
@click.option("--jobs", type=int, default=1,
    help="Number of parallel processes. Defaults to 1, set to 0 to use all cores")
def buildtables(library, outdir, ignoreoldstock, jobs):
    """
    Build datatables out of the LIBRARY and save them in OUTDIR
    """

    t0 = time()
    
    lib = PartLibraryDb(library)
    Path(outdir).mkdir(parents=True, exist_ok=True)
    clearDir(outdir)


    total = lib.countCategories()
    categoryIndex = {}

    params = []
    for (catName, subcategories) in lib.categories().items():
        for subcatName in subcategories:
            params.append(MapCategoryParams(
                libraryPath=library, outdir=outdir, ignoreoldstock=ignoreoldstock,
                catName=catName, subcatName=subcatName))

    with multiprocessing.Pool(jobs or multiprocessing.cpu_count()) as pool:
        for i, result in enumerate(pool.imap_unordered(_map_category, params)):
            if result is None:
                continue
            catName = result["category"] #.lower()
            subcatName = result["subcategory"] #.lower()
            sourceName = f"{catName}__x__{subcatName}"
            print(f"{((i) / total * 100):.2f} % {catName}: {subcatName}")
            if sourceName not in categoryIndex:
                categoryIndex[sourceName] = result
            else:
                categoryIndex[sourceName]["components"] += result["components"]    # combine for categories that are only different because of case

    t1 = time()
    # db holds the data we're putting into our database file
    db = {
        "subcategories": [schemaToLookup(['subcategory', 'category', 'subcategoryIdx'])],
        "components": [schemaToLookup(['lcsc', 'mfr', 'description', 'attrsIdx', 'stock', 'subcategoryIdx', 'joints', 'datasheet', 'price', 'img', 'url'])],
        "attributes-lut": {}
    }
    
    # fill database
    s = None    # schema lookup
    subcatIndex = 0
    for sourceName, subcatEntry in categoryIndex.items():        
        if s is None:
            s = schemaToLookup(subcatEntry["schema"])  # all schema will be the same

        subcatIndex += 1
        db["subcategories"] += [[subcatEntry["subcategory"], subcatEntry["category"], subcatIndex]]

        for comp in subcatEntry["components"]:
            db["components"] += [[
                comp[s["lcsc"]],
                comp[s["mfr"]],
                comp[s["description"]],
                [updateLut(db["attributes-lut"], [attrName, value]) for attrName,value in comp[s["attributes"]].items()],
                comp[s["stock"]],
                subcatIndex,
                comp[s["joints"]],
                comp[s["datasheet"]],
                comp[s["price"]],
                comp[s["img"]],
                comp[s["url"]]
            ]]

    # invert the lut
    db["attributes-lut"] = [json.loads(str) for str in lutToArray(db["attributes-lut"])]
    saveDatabaseFile(db, outdir, "all.jsonlines.tar")

    print(f"Table extraction took {(t1 - t0)}, reformat into one file took {time() - t1}")
