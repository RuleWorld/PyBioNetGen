import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import functools
import marshal
from .util import logMess
import json


def memoize(obj):
    cache = obj.cache = {}

    @functools.wraps(obj)
    def memoizer(*args, **kwargs):
        # key = str(args) + str(kwargs)
        key = marshal.dumps([str(obj), args, kwargs])
        if key not in cache:
            cache[key] = obj(*args, **kwargs)
        return cache[key]

    return memoizer


'''
from bioservices import UniProt
u = UniProt(verbose=False)
@memoize
def name2uniprot(nameStr):
    """
    get the uniprot id for a given biological name. gives preference to human data
    """
    data = u.search('{0}+AND+organism:9606'.format(nameStr), limit=5, columns="entry name,id")

    if len(data) == 0:
        data = u.search('{0}'.format(nameStr), limit=10,columns="entry name,id")
    parsedData = [x.split('\t') for x in data.split('\n')][1:]
    if len([x for x in parsedData if nameStr in x[0]]) > 0:
        return [x[1] for x in parsedData if nameStr in x[0]]
    return [x[1] for x in parsedData if len(x) == 2]
'''


@memoize
def queryBioGridByName(name1, name2, organism, truename1, truename2):
    url = "http://webservice.thebiogrid.org/interactions/?"
    response = None
    if organism:
        organismExtract = list(organism)[0].split("/")[-1]
        d = {
            "geneList": "|".join([name1, name2]),
            "taxId": "|".join(organism),
            "format": "json",
            "accesskey": "f74b8d6f4c394fcc9d97b11c8c83d7f3",
            "includeInteractors": "false",
        }
        # FIXME: check if all "organism"s are the wrong thing,
        # for model 48 this returns a process identifier https://www.ebi.ac.uk/QuickGO/term/GO:0007173
        # and not an organism taxonomy identifier
        data = urllib.parse.urlencode(d).encode("utf-8")
        try:
            response = urllib.request.urlopen(url, data=data).read()
        except urllib.error.HTTPError:
            logMess(
                "ERROR:MSC02",
                "A connection could not be established to biogrid while testing with taxon {1} and genes {0}, trying without organism taxonomy limitation".format(
                    "|".join([name1, name2]), "|".join(organism)
                ),
            )
            # return False

    if response is None:
        d = {
            "geneList": "|".join([name1, name2]),
            "format": "json",
            "accesskey": "f74b8d6f4c394fcc9d97b11c8c83d7f3",
            "includeInteractors": "false",
        }
        data = urllib.parse.urlencode(d).encode("utf-8")
        try:
            response = urllib.request.urlopen(url, data=data).read()
        except urllib.error.HTTPError:
            logMess("ERROR:MSC02", "A connection could not be established to biogrid")
            return False
    results = json.loads(response)
    referenceName1 = truename1.lower() if truename1 else name1.lower()
    referenceName2 = truename2.lower() if truename2 else name2.lower()
    for result in results:
        resultName1 = results[result]["OFFICIAL_SYMBOL_A"].lower()
        resultName2 = results[result]["OFFICIAL_SYMBOL_B"].lower()
        synonymName1 = results[result]["SYNONYMS_A"].split("|")
        synonymName1 = [x.lower() for x in synonymName1]
        synonymName2 = results[result]["SYNONYMS_B"].split("|")
        synonymName2 = [x.lower() for x in synonymName2]
        if truename1 != None and truename2 != None and resultName1 != resultName2:
            return True
        elif (
            truename1 != None
            and truename2 != None
            and truename1 == truename2
            and resultName1 == resultName2
        ):
            return True
        if (referenceName1 == resultName1 or referenceName1 in synonymName1) and (
            referenceName2 == resultName2 or referenceName2 in synonymName2
        ):
            return True
        if (referenceName2 == resultName1 or referenceName2 in synonymName1) and (
            referenceName1 == resultName2 or referenceName1 in synonymName2
        ):
            return True

    return False


@memoize
def queryActiveSite(nameStr, organism):
    url = "http://www.uniprot.org/uniprot/?"

    response = None
    retry = 0
    while retry < 3:
        retry += 1
        if organism:
            organismExtract = list(organism)[0].split("/")[-1]
            # ASS - Updating the query to conform with a regular RESTful API request and work in Python3
            xparams = {
                "query": "{}+AND+organism:{}".format(nameStr, organismExtract),
                "columns": "name,id,feature(ACTIVE SITE)",
                "format": "tab",
                "limit": "5",
                "sort": "score",
            }
            xparams = urllib.parse.urlencode(xparams).encode("utf-8")
            try:
                xparams = urllib.parse.urlencode(xparams).encode("utf-8")
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, data=xparams) as f:
                    response = f.read().decode("utf-8")
            except urllib.error.HTTPError:
                logMess(
                    "ERROR:MSC03", "A connection could not be established to uniprot"
                )
        response = str(response)
        if response in ["", None]:
            url = "http://www.uniprot.org/uniprot/?"
            # ASS - Updating the query to conform with a regular RESTful API request and work in Python3
            xparams = {
                "query": nameStr,
                "columns": "name,id,feature(ACTIVE SITE)",
                "format": "tab",
                "limit": "5",
                "sort": "score",
            }
            xparams = urllib.parse.urlencode(xparams).encode("utf-8")
            try:
                req = urllib.request.Request(url, data=xparams)
                with urllib.request.urlopen(req) as f:
                    response = f.read().decode("utf-8")
            except urllib.error.HTTPError:
                logMess(
                    "ERROR:MSC03", "A connection could not be established to uniprot"
                )
    response = str(response)
    if not response:
        return response
    parsedData = [x.split("\t") for x in response.split("\n")][1:]
    # return parsedData
    return [
        x[0]
        for x in parsedData
        if len(x) == 3
        and any(nameStr.lower() in z for z in [y.lower() for y in x[0].split("_")])
        and len(x[2]) > 0
    ]


@memoize
def name2uniprot(nameStr, organism):
    url = "http://www.uniprot.org/uniprot/?"

    response = None
    if organism:
        organismExtract = list(organism)[0].split("/")[-1]
        d = {
            "query": f"{nameStr}+AND+organism:{organismExtract}",
            "format": "tab&limit=5",
            "columns": "entry name,id",
            "sort": "score",
        }
        data = urllib.parse.urlencode(d).encode("utf-8")
        try:
            response = urllib.request.urlopen(url, data=data).read()
        except urllib.error.HTTPError:
            logMess("ERROR:MSC03", "A connection could not be established to uniprot")
            return None

    if response in ["", None]:
        url = "http://www.uniprot.org/uniprot/?"
        d = {
            "query": f"{nameStr}",
            "format": "tab&limit=5",
            "columns": "entry name,id",
            "sort": "score",
        }
        data = urllib.parse.urlencode(d).encode("utf-8")
        try:
            response = urllib.request.urlopen(url, data=data).read()
        except urllib.error.HTTPError:
            return None
    parsedData = [x.split("\t") for x in str(response).split("\n")][1:]
    return [
        x[1]
        for x in parsedData
        if len(x) == 2
        and any(nameStr.lower() in z for z in [y.lower() for y in x[0].split("_")])
    ]


@memoize
def getReactomeBondByUniprot(uniprot1, uniprot2):
    """
    Queries reactome to see if two proteins references by their uniprot id
    are bound in the same complex
    """
    url = "http://www.pathwaycommons.org/pc2/graph"
    d = {
        "kind": "PATHSFROMTO",
        "format": "EXTENDED_BINARY_SIF",
        "source": "|".join(uniprot1),
        "target": "|".join(uniprot2),
    }
    data = urllib.parse.urlencode(d).encode("utf-8")
    # query reactome
    try:
        response = urllib.request.urlopen(url, data=data).read()
    except urllib.error.HTTPError:
        # logMess('ERROR:pathwaycommons','A connection could not be established to pathwaycommons')
        return None
    # divide by line
    parsedResponse = [x.split("\t") for x in str(response).split("\n")]

    # response is divided in two  sections. actual protein-protein relationships and protein descriptors
    separation = [i for i, x in enumerate(parsedResponse) if len(x) < 2]

    # separate the first half and focus on actual ppi entries
    ppi = [x for x in parsedResponse[: separation[0]] if x[1] == "in-complex-with"]
    # ppi = [x for x in parsedResponse[:separation[0]]]
    # get protein descriptors and filter by the initial uniprot id given in the method parameters
    includedElements = [[x[0], x[-1]] for x in parsedResponse[separation[0] :]]
    includedElements1 = [
        x for x in includedElements if any(y in x[1] for y in uniprot1)
    ]
    includedElements2 = [
        x for x in includedElements if any(y in x[1] for y in uniprot2)
    ]
    includedElements1 = [x[0] for x in includedElements1]
    includedElements2 = [x[0] for x in includedElements2]
    # filter protein interaction by those uniprot ids and names we truly care about
    ppi = [
        x[0:3]
        for x in ppi
        if (
            len([y for y in includedElements1 if y == x[0]]) == 1
            and len([y for y in includedElements2 if y == x[2]]) == 1
        )
        or (
            len([y for y in includedElements1 if y == x[2]]) == 1
            and len([y for y in includedElements2 if y == x[0]]) == 1
        )
    ]
    # ppi = [x[0:3] for x in ppi if len([y for y in includedElements1 if y in x]) == 1 and len([y for y in includedElements2 if y in x]) == 1]
    return ppi


@memoize
def getReactomeBondByName(name1, name2, sbmlURI, sbmlURI2, organism=None):
    """
    resolves the uniprot id of parameters *name1* and *name2* and obtains whether they
    can be bound in the same complex or not based on reactome information
    """
    if len(sbmlURI) > 0:
        uniprot1 = [x.split("/")[-1] for x in sbmlURI]
    else:
        uniprot1 = name2uniprot(name1, organism)
    if len(sbmlURI2) > 0:
        uniprot2 = [x.split("/")[-1] for x in sbmlURI2]
    else:
        uniprot2 = name2uniprot(name2, organism)
    uniprot1 = uniprot1 if uniprot1 else [name1]
    uniprot2 = uniprot2 if uniprot2 else [name2]
    result = getReactomeBondByUniprot(uniprot1, uniprot2)
    return result


def isInComplexWith(name1, name2, sbmlURI=[], sbmlURI2=[], organism=None):
    nameset = sorted([name1, name2], key=lambda x: x[0])
    result = None
    retry = 0
    while retry < 3:
        result = getReactomeBondByName(
            nameset[0][0], nameset[1][0], nameset[0][1], nameset[1][1], organism
        )
        retry += 1
        if result:
            return any([x[1] == "in-complex-with" for x in result])
    return False


if __name__ == "__main__":
    # pass
    # results =  isInComplexWith('Crk','Ras')
    # print(getReactomeBondByName('EGF', 'Grb2', [], []))
    print((queryActiveSite("EGF", "")))
    # print(getReactomeBondByName('EGF', 'EGF', ['P07522'], ['P07522']))
    # print(name2uniprot('MEKK1'))
    # print(results)
    # print(getReactomeBondByUniprot('Q9QX70','Q9QX70'))
    # print(getReactomeBondByUniprot('P07522','P07522'))
