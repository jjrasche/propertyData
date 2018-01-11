from bs4 import BeautifulSoup
import mechanize
import time
import re
from gatherParcelDetails_AccessMyGov import convertAddressToCoordinates, sameAddress
from ormMethods import safeCommitDBObject, setValue
from dataStructures import Parcel


browser = mechanize.Browser()
browser.set_handle_robots(False)
browser.set_handle_equiv(False)
headers = [
    ('Accept','text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'),
    ('Accept-Encoding','gzip, deflate, sdch, br'),
    ('Accept-Language','en-US,en;q=0.8'),
    ('Cache-Control','no-cache'),
    ('Connection','keep-alive'),
    ('Cookie','timezoneoffset=240; showMobileView=; user_collapseVerticalNav=; IsWeb=92F42FA1CE18118CC4A9437CE9F10970930448964CD837E974B142F472CFC16E2AF9F71B0DAC1188D74B9551DA58C8AE4138844C0A5156CB40EF6C89D6F84D426591ACD6D22B9D7C3C80EA1A05DE226430B855EFCCA211A1EDA11A25624DAFB004E0EC695A8FBFF5ABC771D990CB9052202095555A25048BA56DC66BDDB41B3EAE57160D5C7A68C2E8CC4788D10C23D409C9457B3AC41C6E1D04783913A0F07E93DC38DC2E7A9ADC48CA7B058AE664B9635BFC9F; ASP.NET_SessionId=ou01gl1nslrs4qeqlvrztcam; sFocus=All Records; sCategory=Parcel Number; __utma=177973685.1603943979.1490146295.1492802911.1492804837.18; __utmc=177973685; __utmz=177973685.1492192986.10.5.utmcsr=zillow.com|utmccn=(referral)|utmcmd=referral|utmcct=/homes/for_sale/Charlotte-MI/house_type/74721272_zpid/21554_rid/globalrelevanceex_sort/42.55895,-84.8302,42.556489,-84.833854_rect/17_zm/; user_showAdvAddrSearchCheckbox=false; user_useAdvAddrSearch=false'),
    ('Host','accessmygov.com'),
    ('Pragma','no-cache'),
    ('Referer','https,//accessmygov.com/SiteSearch/SiteSearchResults?SearchFocus=All%20Records&SearchCategory=Parcel%20Number&SearchText=41-20-02-___-___&uid=1363&DetailResultsGrid-size=15&ubUsingAccountNumber=true&ubHideName=false&ubHideAddress=false&ubHideParcelNumber=false&mrHideName=true&mrHideAddress=true&mrHideCustomerID=true&UseAdvancedAddrSearch=false&DetailResultsGrid-page=11'),
    ('Upgrade-Insecure-Requests','1'),
    ('User-Agent','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36')
]
browser.addheaders = headers

def gotoPage(link, delay):
    browser.open(link)
    time.sleep(delay)
    resp = browser.response()
    return BeautifulSoup(resp.read(), "html.parser")

def getHTMLText(soup, name):
    element = soup(text=re.compile(name))[0].next
    if 'bs4.element.Tag' in str(type(element)):
        return element.text.strip()
    else:
        return element.strip()

def resetBrowser():
    browser = mechanize.Browser()
    browser.set_handle_robots(False)
    browser.set_handle_equiv(False)
    headers = [
        ('User-Agent','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36')
    ]
    browser.addheaders = headers

def getMostRecentTaxableValue(soup):
    firstRowData = soup.find('table', 'grid').contents[3].contents[3].text.strip().split('\n')
    year = firstRowData[0]
    value = firstRowData[2]
    ret = []
    ret.append(year)
    ret.append(value)
    return ret

def saveDataFromKentAccess(parcelNumber, save = False):
    http = 'https://www.accesskent.com/Property/FromGIS.jsp?parcelNumber=%s' % parcelNumber
    soup = gotoPage(http, 2)
    parcel = Parcel()

    setValue(parcel, "propertyAddress", lambda: getHTMLText(soup, 'Property Address'))
    setValue(parcel, "ownerAddress", lambda: getHTMLText(soup, 'Mailing Address:') + ' ' +
                                             getHTMLText(soup, 'Mailing City, State, Zip Code:'))
    setValue(parcel, "owner", lambda: getHTMLText(soup, 'Owner Name One:'))
    setValue(parcel, "acreage", lambda: getHTMLText(soup, 'Acreage & Lot Dimensions:'))
    setValue(parcel, "propertyClass", lambda: getHTMLText(soup, 'Property Classification:'))
    setValue(parcel, "propertyClass", lambda: getHTMLText(soup, 'Property Status:'))
    setValue(parcel, "buildingClass", lambda: getHTMLText(soup, 'Property Classification:'))
    setValue(parcel, "taxableValue", lambda: sameAddress(parcel.propertyAddress, parcel.ownerAddress))
    setValue(parcel, "rental", lambda: getHTMLText(soup, 'Property Classification:'))
    setValue(parcel, "buildingClass", lambda: getHTMLText(soup, 'Property Classification:'))

    coordinates = convertAddressToCoordinates(parcel.propertyAddress)
    setValue(parcel, "lat", lambda: getHTMLText(soup, 'Property Classification:'))
    setValue(parcel, "long", lambda: getHTMLText(soup, 'Property Classification:'))
    parcel.lat = coordinates["lat"]
    parcel.long = coordinates["lng"]

    if save:
        safeCommitDBObject()
    return parcel

