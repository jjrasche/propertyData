from dataStructures import Parcel, Municipality
from ormMethods import safeCommitDBObject
from browsingFunctionaliy import  browseUrlByClass, browseOnAction, driver, browseUrl, timeOutException
from largeData import parcels, prefixes
import re
from decimal import Decimal
from sets import Set
from datetime import datetime
import traceback
import constants


####        Get list of parcels
def createMunicipalities():
    soup = browseUrlByClass("https://accessmygov.com/MunicipalDirectory", "unit-directory-grid-toolbar")
    mu = soup.find_all("tr", "unit-directory-row")

    for m in mu:
        municipality = Municipality()
        municipalityId = m.contents[0].get("id")
        municipalityName = m.contents[0].text.strip()
        setattr(municipality, "id", municipalityId)
        setattr(municipality, "name", municipalityName)
        commitDBObject(municipality)

def getParcelSearchUrl(parcelPrefix, municipality, sort):
    return 'https://accessmygov.com/SiteSearch/SiteSearchResults?SearchFocus=All+Records&SearchCategory=Parcel+Number&SearchText={0}&uid={1}&SearchOrigin=0&SortBy={2}'\
        .format(parcelPrefix, municipality, sort)

def getParcelSearchUrlByName(name, municipality):
    return 'https://accessmygov.com/SiteSearch/SiteSearchResults?SearchFocus=All+Records&SearchCategory=Name&SearchText={0}&uid={1}&SearchOrigin=0&SortBy=Name'\
        .format(name, municipality)

def markParcelIncomplete(parcel):
    parcel.lat = -1
    return parcel

def getParcelNumbersFromSearch(soup):
    ret = Set()
    records = soup.findAll('tr', 'site-search-row')
    for j in range(0, len(records)):
        record = records[j]
        try:
            ret.add(record.contents[2].contents[0])
        except:
            print 'failure: ' + str(record) +  "       " + traceback.format_exc()
            continue
    return ret

def getAllPagedParcelNumbers(url):
    ret = Set()
    soup = browseUrlByClass(url, "t-grid")
    error = soup.find(text=re.compile("An error has occurred:"))
    if error != None:
        print "no parcel search found for {0}".format(soup.find("div", "header-text-unit").text)
        return ret

    totalRecords = int(soup.find("div", "t-status-text").text.split("of")[1].strip())
    # get first page
    records = getParcelNumbersFromSearch(soup)
    ret = ret.union(records)
    attempts = 1

    def morePages():
        ele = soup.find("span", "t-arrow-next")
        if ele == None:
            print "arrow element not found\t\turl:{0}".format(driver.current_url)
            return False
        return ele.parent.has_attr('class') and len(ele.parent.attrs['class']) != 2

    while(morePages()):
        attempts = 1

        requestStartTime = datetime.now()
        browseResult = browseOnAction(lambda: driver.find_element_by_class_name("t-arrow-next").click(), {"class":"t-grid"})
        requestCompleteTime = datetime.now()

        while (attempts <= constants.maxTimeoutAttempts and browseResult == timeOutException):
            attempts += 1
            browseResult = browseOnAction(lambda: driver.find_element_by_class_name("t-arrow-next").click(), {"class": "t-grid"})
        if (attempts >= constants.maxTimeoutAttempts):
            return ret

        soup = browseResult
        records = getParcelNumbersFromSearch(soup)
        print "{0}% done\t\trequestTime:{1}\t\tsearchSize:{2}".format(
            int(Decimal(len(ret)) / Decimal(totalRecords) * 100),
            requestCompleteTime - requestStartTime,
            totalRecords)
        ret = ret.union(records)

    return ret






def getParcelNumbersFromRandomPrefixSearches(prefix, municipalityID):
    url = 'https://accessmygov.com/SiteSearch/SiteSearchResults?SearchFocus=All+Records&SearchCategory=Parcel+Number&SearchText={0}&uid={1}&SearchOrigin=0&SortBy=Name'.format(prefix, municipalityID)
    return getAllPagedParcelNumbers(url)

def getParcelNumbersFromRandomNameSearches(municipalityID):
    ret = Set()
    baseUrl = 'https://accessmygov.com/SiteSearch/SiteSearchResults?SearchFocus=All+Records&SearchCategory=Name&SearchText={0}&uid={1}&SearchOrigin=0&SortBy=Name&LimitResults=false'
    letters = ["v", "q", "k"]
    for letter in letters:
        print "searching on letter '{0}'".format(letter)
        url = baseUrl.format(letter, municipalityID)
        records = getAllPagedParcelNumbers(url)
        print str(records)
        ret = ret.union(records)
    return ret



def getUniquePrefixes(numbers, numSections):
    prefixNums = Set()
    for num in numbers:
        prefix = getPrefix(num, numSections)
        if prefix != None:
            prefixNums.add(prefix)
    return prefixNums

def getUniquePrefixesAndCount(numbers, numSections):
    prefixNums = {}
    for num in numbers:
        prefix = getPrefix(num, numSections)
        if prefix != None:
            if (prefix in prefixNums):
                prefixNums[prefix] += 1
            else:
                prefixNums[prefix] = 1
    return sorted(prefixNums.items(), key=lambda x:x[1], reverse=True)


def getPrefix(num, n):
    try:
        split = num.split('-')
        return '-'.join(split[:n])
    except Exception, e:
        return None


def getUniqueSetOfParcelNumberParts(numbers, numSections):
    n3Numbers = Set()
    for num in numbers:
        identifiers = num.split("-")
        n3Num = ""
        for idx, val in enumerate(identifiers):
            n3Num += val
            if idx == numSections:
                break
            else:
                n3Num += "-"
        n3Numbers.add(n3Num)
    return n3Numbers

def getParcelNumberFormat(num):
    ret = []
    split = num.split("-")
    for s in split:
        ret.append(len(s))
    return list(reversed(ret))

# check all parent forms of section
def isComplete(completedSections, section):
    split = section.split("-")
    for s in split:
        if (completedSections.get(s) != None):
            return True
    return False


def getAllParcelsFromMunicipality(session, municipalityID):
    for pre in prefixes:
        print "search on prefix {0}".format(str(pre));
        url = "https://accessmygov.com/SiteSearch/SiteSearchResults?SearchFocus=All+Records&SearchCategory=Parcel+Number&SearchText={0}&AddrSearchStreetName=&AddrSearchStreetNumFrom=&AddrSearchStreetNumTo=&UseAdvancedAddrSearch=false&uid={1}&LimitResults=false".format(pre, municipalityID)
        records = getAllPagedParcelNumbers(url)
        print "prefix '{0}' \nparcels:{1}".format(pre, str(records))

        for parcel in records:
            dbParcel = Parcel()
            dbParcel.parcelNumber = parcel
            dbParcel.municipality_id = municipalityID
            dbParcel = markParcelIncomplete(dbParcel)
            session.add(dbParcel)
        safeCommitDBObject()

