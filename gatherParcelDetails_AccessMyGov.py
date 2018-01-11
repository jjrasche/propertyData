from ormMethods import tryFindElement, setValue, createSession, safeCommitDBObject, IntegrityError, safeAddObject, getIncompleteParcel
from dataStructures import Parcel, Coordinate, Certificate, Sale, Municipality, Tax, TaxDetail
from browsingFunctionaliy import browseUrlByClass, browseOnAction, findElementsInListByText, driver
import urllib2
from urllib2 import HTTPError
import json
from fuzzywuzzy import fuzz
import re
import traceback
from datetime import datetime
from sqlalchemy import inspect as sqlInspect
import inspect
import constants

ADDRESS_SUFFIX = ', Lansing, MI'


def sameAddress(propAddr, ownerAddr):
    if propAddr == None or ownerAddr == None:
        return None
    streetNum1 = re.search("\d{4}", propAddr).group()
    streetNum2 = re.search("\d{4}", ownerAddr).group()
    streetNumCompare = fuzz.ratio(streetNum1, streetNum2)

    wholeCompare = fuzz.token_set_ratio(propAddr, ownerAddr)
    trustMatchAttempt = re.search('trust', ownerAddr, re.IGNORECASE)
    matchPercent = 70 if trustMatchAttempt == None else 60
    return streetNumCompare == 100 and wholeCompare > matchPercent


def convertAddressToCoordinates(address, trys = 3):
    if address == None:
        print "address is null."
        return
    try:
        quotedAddress = urllib2.quote(address)
        geocode_url = "https://maps.googleapis.com/maps/api/geocode/json?address=%s&key=AIzaSyDXxZxWaE1X6aWcphTsHDWEPGSkzXDMpNI" % quotedAddress
        req = urllib2.urlopen(geocode_url)
        jsonResponse = json.loads(req.read())
        if (jsonResponse.get('status') == 'ZERO_RESULTS'):
            return constants.badAddress
        coordinateObj = jsonResponse.get('results')[0].get('geometry').get('location')
        return coordinateObj
    except HTTPError:
        if trys < 3:
            convertAddressToCoordinates(address, trys + 1)
        print "tried {0} times to get coordinates on {1}".format(trys, address)
        return constants.badAddress
    except Exception:
        print traceback.format_exc()
        return constants.badAddress


def runAndTimeMethod(expression):
    startTime = datetime.now()
    val = expression()
    completeTime = datetime.now()
    duration = completeTime - startTime
    print "{0}\t{1}".format(duration, inspect.getsourcelines(expression)[0][0])
    return val


def saveDataFromAccessMyGov(session, parcel):

    print "working on {0}".format(parcel.parcelNumber)
    url = 'https://accessmygov.com/SiteSearch/SiteSearchDetails?ReferenceKey={0}&RecordKeyDisplayString={1}&uid={2}' \
        .format(parcel.parcelNumber, parcel.parcelNumber, parcel.municipality_id)

    ownerTab = "Owner and Taxpayer Information"
    genTaxInfoTab = "General Information for Tax Year"
    landInfoTab = "Land Information"
    descriptionTab = "Legal Description"
    saleHistoryTab = "Sale History"
    buildingInfoTab = "Building Information"
    certificateTab = "Certificates"
    taxHistoryTab = "Tax History"

    try:
        soup = browseUrlByClass(url, "record-details-collapsible-box")
        if soup == constants.noRecord:
            print "'{0}' no record found".format(parcel.parcelNumber)
            return constants.noRecord

        parcel.createDate = datetime.now()
        parcel.tabs = soup.find("ul", "t-tabstrip-items").text

        header = soup.find('div', 'detail-header')
        propertyAddressElement = tryFindElement(lambda: header.next.contents[1])
        setValue(parcel, "propertyAddress",
                 lambda: propertyAddressElement.contents[0].text + ' ' +
                         propertyAddressElement.contents[1].text.replace(u'\xa0', u' ').replace('(Property Address)',
                                                                                                '').strip() +
                         ADDRESS_SUFFIX)

        coords = convertAddressToCoordinates(parcel.propertyAddress, 1)
        if (coords == constants.badAddress):
            return constants.badAddress
        parcel.lat = coords["lat"]
        parcel.long = coords["lng"]

        expanders = soup.find_all("div", "record-details-collapsible-box")

        tabElement = findElementsInListByText(expanders, ownerTab)
        if (tabElement):
            ownerInfo = tabElement.findChild(text="Owner").next
            setValue(parcel, "owner", lambda: ownerInfo.contents[0])
            # TODO: handle outliers
            setValue(parcel, "ownerAddress", lambda: ownerInfo.contents[1].contents[0] + " " +
                                                     ownerInfo.contents[1].contents[1].contents[0] + " " +
                                                     ownerInfo.contents[1].contents[1].contents[1].text)
        # tax tab
        tabElement = findElementsInListByText(expanders, genTaxInfoTab)
        if (tabElement):
            setValue(parcel, "mapNumber", lambda: tabElement.findChild(text="MAP #").next.text)
            setValue(parcel, "propertyClass", lambda: tabElement.findChild(text="Property Class").next.text)
            setValue(parcel, "schoolDistrict", lambda: tabElement.findChild(text="School District").next.text)
            setValue(parcel, "assessedValue", lambda: tabElement.findChild(text="Assessed Value").next.text)
            setValue(parcel, "taxableValue", lambda: tabElement.findChild(text="Taxable Value").next.text)

        # land info tab
        tabElement = findElementsInListByText(expanders, landInfoTab)
        if (tabElement):
            setValue(parcel, "zoningCode", lambda: tabElement.findChild(text="Zoning Code").next.text)
            setValue(parcel, "landValue", lambda: tabElement.findChild(text="Land Value").next.text)
            setValue(parcel, "dimensions", lambda: tabElement.findChild(text="Lot Dimensions/Comments").next.text)
            setValue(parcel, "landImprovements", lambda: tabElement.findChild(text="Land Improvements").next.text)
            setValue(parcel, "renZone", lambda: tabElement.findChild(text="Renaissance Zone").next.text)
            setValue(parcel, "acreage", lambda: tabElement.findChild(text="Total Acres").next.text)

        # legal description tab
        tabElement = findElementsInListByText(expanders, descriptionTab)
        if (tabElement):
            setValue(parcel, "legalDescription",
                     lambda: tabElement.findChild('div', 'collapse-container1-content').text)

        # building information tab
        tabElement = findElementsInListByText(expanders, buildingInfoTab)
        if (tabElement):
            setValue(parcel, "garageSize", lambda: tabElement.findChild(text="Garage Area").next.text)
            setValue(parcel, "floorSize", lambda: tabElement.findChild(text="Floor Area").next.text)
            setValue(parcel, "foundationSize", lambda: tabElement.findChild(text="Foundation Size").next.text)
            setValue(parcel, "basementSize", lambda: tabElement.findChild(text="Basement Area").next.text)
            setValue(parcel, "numHalfBaths", lambda: tabElement.findChild(text="2 Fixture Bath").next.text)
            setValue(parcel, "numFullBaths", lambda: tabElement.findChild(text="3 Fixture Bath").next.text)
            setValue(parcel, "bedrooms", lambda: tabElement.findChild(text="Bedrooms").next.text)
            setValue(parcel, "yearBuilt", lambda: tabElement.findChild(text="Year Built").next.text)
            setValue(parcel, "style", lambda: tabElement.findChild(text="Style").next.text)
            setValue(parcel, "heat", lambda: tabElement.findChild(text="Heat").next.text)
            setValue(parcel, "occupancy", lambda: tabElement.findChild(text="Occupancy").next.text)
            setValue(parcel, "buildingClass", lambda: tabElement.findChild(text="Class").next.text)
            setValue(parcel, "water", lambda: tabElement.findChild(text="Water").next.text)
            setValue(parcel, "sewer", lambda: tabElement.findChild(text="Sewer").next.text)
            setValue(parcel, "builtInInformation", lambda: tabElement.findChild(text="Built-In Information").next.text)

        setValue(parcel, "rental", lambda: not sameAddress(parcel.propertyAddress, parcel.ownerAddress))
        # session.add(parcel)

        # sale history
        tabElement = findElementsInListByText(expanders, saleHistoryTab)
        if tabElement:
            salesTable = tabElement.findChild('tbody')
            hasData = tryFindElement(
                lambda: salesTable.find('tr', {'class': 't-no-data'})) == None or salesTable == None
            if hasData:
                for i in range(0, len(salesTable)):
                    row = salesTable.contents[i]
                    sale = Sale(parcel=parcel)
                    setValue(sale, "date", lambda: row.contents[0].text)
                    setValue(sale, "price", lambda: row.contents[1].text)
                    setValue(sale, "instrument", lambda: row.contents[2].text)
                    setValue(sale, "grantor", lambda: row.contents[3].text)
                    setValue(sale, "grantee", lambda: row.contents[4].text)
                    setValue(sale, "terms", lambda: row.contents[5].text)
                    setValue(sale, "createDate", lambda: datetime.now())
                    safeAddObject(sale)
                    # print "sale: {0}".format(object_as_dict(sale))
                    # session.flush()

        # certificate status
        tabElement = findElementsInListByText(expanders, certificateTab)
        if (tabElement):
            certTable = tabElement.findChild('tbody')
            hasData = tryFindElement(lambda: certTable.find('tr', {'class': 't-no-data'})) == None or certTable == None
            if hasData:
                for i in range(0, len(certTable)):
                    row = certTable.contents[i]
                    cert = Certificate(parcel=parcel)
                    setValue(cert, "type", lambda: row.contents[0].text)
                    setValue(cert, "number", lambda: row.contents[1].text)
                    setValue(cert, "status", lambda: row.contents[2].text)
                    setValue(cert, "issued", lambda: row.contents[3].text)
                    setValue(cert, "inspected", lambda: row.contents[4].text)
                    setValue(cert, "createDate", lambda: datetime.now())
                    safeAddObject(cert)

        # tax history
        soup = browseOnAction(lambda: driver.find_element_by_link_text("Tax Information").click(), {"text":"Tax History"})
        expanders = soup.find_all("div", "record-details-collapsible-box")
        tabElement = findElementsInListByText(expanders, taxHistoryTab)
        taxTable = tryFindElement(lambda: tabElement.findChildren('tr', {'class': 'g-detail-row'}))
        if tabElement != None and taxTable != None:
            for i in range(0, len(taxTable)):
                row = taxTable[i]
                tax = Tax(parcel=parcel)
                setValue(tax, "year",
                         lambda: row.find('h3').text.replace('General Information for ', '').replace(' Taxes', '')[:4])
                setValue(tax, "season",
                         lambda: row.find('h3').text.replace('General Information for ', '').replace(' Taxes', '')[-6:])
                setValue(tax, "taxableValue", lambda: row(text="Taxable Value")[0].next.text)
                setValue(tax, "propertyClass", lambda: row(text="Property Class")[0].next.text)
                setValue(tax, "assessedValue", lambda: row(text="Assessed Value")[0].next.text)
                setValue(tax, "datePaid", lambda: row(text="Last Payment Date")[0].next.text)
                setValue(tax, "due", lambda: row(text="Total Tax & Fees")[0].next.text)
                setValue(tax, "paid", lambda: row(text="Total Paid")[0].next.text)
                setValue(tax, "createDate", lambda: datetime.now())

                safeAddObject(tax)
                details = row.find_all('tbody')[1].contents
                for j in range(0, len(details)):
                    taxDetailRow = details[j]
                    detail = TaxDetail(tax=tax)
                    setValue(detail, "authority", lambda: taxDetailRow.contents[0].text)
                    setValue(detail, "milage", lambda: taxDetailRow.contents[1].text)
                    setValue(detail, "due", lambda: taxDetailRow.contents[2].text)
                    setValue(detail, "paid", lambda: taxDetailRow.contents[3].text)
                    setValue(detail, "createDate", lambda: datetime.now())
                    safeAddObject(detail)

        safeCommitDBObject()
    except Exception, e:
        driver.save_screenshot('screenshot.png')
        print 'failed to collect data on parcel: {0}\nerror:{1}' \
            .format(parcel.parcelNumber, traceback.format_exc() if not e.message else e.message)
        return None
    return parcel

count = 0
def identifyAndSaveSingleParcel(session):
    global count
    parcel = getIncompleteParcel()
    data = saveDataFromAccessMyGov(session, parcel)
    # session.refresh(parcel)
    # if parcel.lat == -1 or parcel.lat == -2:
    #     parcel.lat = -1
    #     print "didn't commit parcel {0}".format(data)
    #     session.commit();
    # if data == None:
    #     if parcel.lat == -2:
    #         parcel.lat = -1
    #         print "exception happened reverting parcel {0}".format(parcel)
    #         session.commit();
    count += 1
    print "{0} finished: {1}".format(count, parcel.parcelNumber)

def gatherDataOnParcels(session, parcels):
    if (parcels == None):
        while(1):
            runAndTimeMethod(lambda: identifyAndSaveSingleParcel(session))

    else:
        for parcel in parcels:
            try:
                time = datetime.now()
                data = None
                trys = 1
                while (data == None and trys <= 3):
                    trys += 1
                    data = runAndTimeMethod(lambda: saveDataFromAccessMyGov(session, parcel))

            except Exception as e:
                print 'failed to create data:{0}\nerror:{1}\n' \
                    .format(str(parcel), traceback.format_exc())
                raise
