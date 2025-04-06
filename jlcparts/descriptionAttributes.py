import jlcparts.regexCache as re_cached

# returns a string representing the component package if one could be identified, otherwise None
def extractPassivePackageName(description):
    # standard passive size codes - sizes taken from JLC and https://topline.tv/SizeChart.html
    # skip regex here since it's just a token lookup (much faster)
    sizeCodes = [ "008004", "008005", "01005", "015015", "0201", "0202", "0204", "024024", "0303", "0306", "0402", "0508", "0603", "0805", "0815", "0830", "1008", "1020", "1111", "1206", "1210", "1218", "1225", "1411", "1805", "1806", "1808", "1812", "1825", "2010", "2030", "2220", "2225", "2312", "2512", "2725", "2917", "2920", "3035", "3333", "3530", "3640", "3940", "4045", "4252", "4540" ]
    tokens = description.split()
    for sizeCode in sizeCodes:
        if sizeCode in tokens:
            return sizeCode
    # tantalum style, e.g. CASE-X, CASE-X-1234, CASE-X-1234-56(mm)
    matches = re_cached.search(r"(?:^|\s)(CASE[_-][A-Z](?:[_-]\d{4}(?:-\d+\(mm\))?)?)(?:\s|$)", description)
    if matches is not None:
        return matches.group(1)
    # MELF packages
    matches = re_cached.search(r"(?:^|\s)(MELF[,_-]\d{4})(?:\s|$)", description)
    if matches is not None:
        return matches.group(1)
    return None

# returns a string representing the component package if one could be identified, otherwise None
def extractGeneralPackageName(description):
    packageRegexes = [
        r"(?:^|\s)(?P<pkg>[A-Z0-9]{,2}PAK[A-Za-z0-9.()_-]+?)(?:\s|$)", # PAK (e.g. D2PAK, LFPAK)
        r"(?:^|\s)(?P<pkg>[A-Z]{,1}DFN[A-Za-z0-9.()_-]+?)(?:\s|$)", # DFN
        r"(?:^|\s)(?P<pkg>[A-Z]{,2}BGA-\d+)(?:\s|$)", # BGA
        r"(?:^|\s)(?P<pkg>[A-Z]{,2}SO[A-Z]{1,2}-[A-Za-z0-9.()_-]+?)(?:\s|$)", # SO (SOP, SOIC, SOT, TSON, TSSOP, etc.)
        r"(?:^|\s)(?P<pkg>TO-?\d+[A-Za-z0-9.()_-]+?)(?:\s|$)", # TO-xyz
        r"(?:^|\s)(?P<pkg>Power-?[PFDSTVW][A-Za-z0-9.()_-]+?)(?:\s|$)", # Power* (PowerPAK, PowerDI, PowerTDFN, etc.)
        r"(?:^|\s)(?P<pkg>[A-Z]QF[NP][A-Za-z0-9.()_-]+?)(?:\s|$)" # QFN / QFP
    ]
    for packageRegex in packageRegexes:
        matches = re_cached.search(packageRegex, description)
        if matches is not None:
            return matches.group("pkg")
    return None


def chipResistor(description):
    attrs = {}
    
    package = extractPassivePackageName(description)
    if package is not None:
        attrs["Package"] = package

    matches = re_cached.search(r"\d+(\.\d+)?[fpnuμmkKMG]?(Ω|Ohms?)", description)
    if matches is not None:
        attrs["Resistance"] = matches.group(0)

    matches = re_cached.search(r"±\d+(\.\d+)?%", description)
    if matches is not None:
        attrs["Tolerance"] = matches.group(0)

    matches = re_cached.search(r"((\d+/\d+)|(\d+(.\d+)?[fpnuμmkKMG]?))W", description)
    if matches is not None:
        attrs["Power"] = matches.group(0)
    
    # look for asymmetric tempco (-a~+b) first, then fall back to looking for symmetric (±)
    matches = re_cached.search(r"(-?\d+(?:\.\d+)?)(ppm/(?:℃|°C|K))?~(\+?\d+(?:\.\d+)?)ppm/(?:℃|°C|K)", description)
    if matches is not None:
        attrs["Temperature coefficient"] = matches.group(0)
    else:
        matches = re_cached.search(r"±(\d+(?:\.\d+)?)ppm/(?:degC|℃|°C|K)", description)
        if matches is not None:
            attrs["Temperature coefficient"] = "±" + matches.group(1) + "ppm/°C"

    # operating temp
    matches = re_cached.search(r"(?:^|\s)((?:-?\d+(?:\.\d+)?)(?:℃|°C|K)?~(?:\+?\d+(?:\.\d+)?)(?:℃|°C|K))(?:\s|$)", description)
    if matches is not None:
        attrs["Operating temperature"] = matches.group(1)

    return attrs


def capacitor(description):
    attrs = {}

    matches = re_cached.search(r"\d+(\.\d+)?[fpnuμmkKMG]?F", description)
    if matches is not None:
        attrs["Capacitance"] = matches.group(0)

    matches = re_cached.search(r"\d+(\.\d+)?[fpnuμmkKMG]?V", description)
    if matches is not None:
        attrs["Voltage - Rated"] = matches.group(0)
    
    matches = re_cached.search(r"(?:^|\s)((?:-?\d+(?:\.\d+)?)(?:℃|°C|K)?~(?:\+?\d+(?:\.\d+)?)(?:℃|°C|K))(?:\s|$)", description)
    if matches is not None:
        attrs["Operating temperature"] = matches.group(1)
    
    # match on a cylindrical case string first, then fall back to looking for a standard passive code
    matches = re_cached.search(r"(SMD,)?D(\d+(?:\.\d+)?)xL(\d+(?:\.\d+)?)mm", description)
    if matches is not None:
        attrs["Package"] = matches.group(0)
        attrs["Diameter"] = matches.group(2) + "mm"
        attrs["Φd"] = matches.group(2) + "mm"
        attrs["L"] = matches.group(3) + "mm"
    else:
        package = extractPassivePackageName(description)
        if package is not None:
            attrs["Package"] = package
    
    matches = re_cached.search(r"(?:^|\s)(\d+(?:\.\d+)?[fpnuμmkKMG]?(?:Ω|Ohms?))(?:@(\d+(?:\.\d+)?[fpnuμmkKMG]?Hz))?(?:\s|$)", description)
    if matches is not None:
        esr = matches.group(1)
        freq = matches.group(2)
        if freq is None:
            attrs["Equivalent series resistance"] = esr
        else:
            attrs["Equivalent series resistance"] = f"{esr}@{freq}"

    return attrs


def mosfet(description):
    attrs = {}
    
    package = extractGeneralPackageName(description)
    if package is not None:
        attrs["Package"] = package

    # multiple FET types in one package (e.g. 1 N-chan + 1 P-chan)
    matches = re_cached.search(r"(?:^|\s)(\d)\s*(?:(?:Pieces?|PCS)\s*)?([PNpn])[ -]?[Cc]hannels?\s*[+&]?\s*(\d)\s*(?:(?:Pieces?|PCS)\s*)?([PNpn])[ -]?[Cc]hannels?(?:\s|$)", description)
    if matches is not None:
        fetCount1 = matches.group(1)
        fetType1 = matches.group(2).upper()
        fetCount2 = matches.group(3)
        fetType2 = matches.group(4).upper()
        attrs["Type"] = f"{fetCount1} {fetType1}-Channel + {fetCount2} {fetType2}-Channel"
    else:
        # single type but with numeric prefix and optional configuration, e.g. 2 N-channel, 2 N-Channel (common drain)
        matches = re_cached.search(r"(?:^|\s)(\d)\s*(?:(?:Pieces?|PCS)\s*)?([PNpn])[ -]?[Cc]hannels?(?:\s+\((.+?)\))?(?:\s|$)", description)
        if matches is not None:
            fetCount = matches.group(1)
            fetType = matches.group(2).upper()
            fetConfig = matches.group(3)
            fetSuffix = "" if fetConfig is None else f" ({fetConfig})"
            attrs["Type"] = f"{fetCount} {fetType}-Channel{fetSuffix}"
        else:
            # single type
            matches = re_cached.search(r"(?:^|\s)([PNpn])[ -]?[Cc]hannel(?:\s|$)", description)
            if matches is not None:
                fetType = matches.group(1).upper()
                attrs["Type"] = f"{fetType}-Channel"
    
    # Rds(on) @ Vgs(test), Ids(test)
    matches = re_cached.search(r"(?:^|\s)(\d+(?:\.\d+)?[fpnuμmkKMG]?(?:Ω|Ohms?))@(\d+(?:\.\d+)?[fpnuμmkKMG]?[vV])(?:,(\d+(?:\.\d+)?[fpnuμmkKMG]?A))?(?:\s|$)", description)
    if matches is not None:
        rdson = matches.group(1)
        vgstest = matches.group(2)
        idstest = matches.group(3)
        if idstest is None:
            attrs["Rds(on)"] = f"{rdson}@{vgstest}"
        else:
            attrs["Rds(on)"] = f"{rdson}@{vgstest},{idstest}"
    
    # Vgs(th) @ Ids
    matches = re_cached.search(r"(?:^|\s)(\d+(?:\.\d+)?[fpnuμmkKMG]?[vV])@(\d+(?:\.\d+)?[fpnuμmkKMG]?A)(?:\s|$)", description)
    if matches is not None:
        vgsth = matches.group(1)
        ids = matches.group(2)
        attrs["Gate threshold voltage (vgs(th)@id)"] = f"{vgsth}@{ids}"
    
    # note: cannot extract capacitances (Ciss, Crss, etc.) since there's no way to disambiguate them
    
    # Qg @ Vgs
    matches = re_cached.search(r"(?:^|\s)(\d+(?:\.\d+)?[fpnuμmkKMG]?C)@(\d+(?:\.\d+)?[fpnuμmkKMG]?V)(?:\s|$)", description)
    if matches is not None:
        qg = matches.group(1)
        vgs = matches.group(2)
        attrs["Gate charge(qg)"] = f"{qg}@{vgs}"
    
    # power
    matches = re_cached.search(r"(?:^|\s)(\d+(?:.\d+)?[fpnuμmkKMG]?W)(?:\s|$)", description)
    if matches is not None:
        attrs["Power dissipation (Pd)"] = matches.group(1)
    
    # current
    matches = re_cached.search(r"(?:^|\s)(\d+(?:.\d+)?[fpnuμmkKMG]?A)(?:\s|$)", description)
    if matches is not None:
        attrs["Continuous drain current (id)"] = matches.group(1)
    
    # operating temp
    matches = re_cached.search(r"(?:^|\s)((?:-?\d+(?:\.\d+)?)(?:℃|°C|K)?~(?:\+?\d+(?:\.\d+)?)(?:℃|°C|K))(?:\s|$)", description)
    if matches is not None:
        attrs["Operating temperature"] = matches.group(1)
    
    return attrs


def led(description):
    attrs = {}
    
    package = extractPassivePackageName(description)
    if package is not None:
        attrs["Package"] = package
    
    # current
    matches = re_cached.search(r"(?:^|\s)(\d+(?:.\d+)?[fpnuμmkKMG]?A)(?:\s|$)", description)
    if matches is not None:
        attrs["Forward current"] = matches.group(1)
    
    # luminous intensity (mcd)
    matches = re_cached.search(r"(?:^|\s)(\d+(?:.\d+)mcd)(?:\s|$)", description)
    if matches is not None:
        attrs["Luminous intensity"] = matches.group(1)
    
    # viewing angle (degrees)
    matches = re_cached.search(r"(?:^|\s)(\d+(?:.\d+)°)(?:\s|$)", description)
    if matches is not None:
        attrs["Viewing angle"] = matches.group(1)
    
    # CT
    matches = re_cached.search(r"(?:^|\s)(\d+(?:.\d+)K(?:~\d+(?:.\d+)K)?)(?:\s|$)", description)
    if matches is not None:
        attrs["Color temperature"] = matches.group(1)

    # operating temp
    matches = re_cached.search(r"(?:^|\s)((?:-?\d+(?:\.\d+)?)(?:℃|°C|K)?~(?:\+?\d+(?:\.\d+)?)(?:℃|°C|K))(?:\s|$)", description)
    if matches is not None:
        attrs["Operating temperature"] = matches.group(1)
    
    # power
    matches = re_cached.search(r"(?:^|\s)(\d+(?:.\d+)?[fpnuμmkKMG]?W)(?:\s|$)", description)
    if matches is not None:
        attrs["Power dissipation (Pd)"] = matches.group(1)
        attrs["Power"] = matches.group(1)

    return attrs

