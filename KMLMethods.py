import constants


def xstr(s):
    if s is None:
        return ''
    return str(s)

def escapeForXML(str):
    str = str.replace("&", "&amp;")
    str = str.replace("<", "&lt;")
    str = str.replace(">", "&gt;")
    str = str.replace("\"", "&quot;")
    str = str.replace("\'", "&apos;")
    return str

def writeKMLFile(fileName, parcels):
    kmlFile = open(fileName, 'w+')
    kmlText = createKMLString(parcels)
    kmlFile.write(kmlText)
    kmlFile.close()

def createKMLString(parcels, runValidations = True):
    kmlString = constants.kmlBeginString

    # validations
    for p in parcels:
        if runValidations:
            # need valid coordinates to set place mark on map.
            if p.lat == None or p.long == None:
                print "parcel {0} could not find coordinates on address {1}".format(p.parcelNumber, xstr(p.propertyAddress))

        style = '#rental' if p.rental == True else '#homeOwner'
        displatText = escapeForXML(xstr(p.propertyAddress) + ' : ' + xstr(p.occupancy) + ' : ' + xstr(p.propertyClass) + ' : ' + xstr(p.acreage) + ' : ' + xstr(p.owner))
        coordinateString = str(p.long) + "," + str(p.lat)
        line =  constants.placemarkKml.format(style, displatText, coordinateString)
        kmlString += line
    kmlString += constants.kmlEndString
    return kmlString