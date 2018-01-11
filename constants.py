constants = {
    "resultsLimit": 1000,
    "kmlBeginString": '<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2">\n\t<Document>\n\t\t<name>Rental map</name>\n\t\t<description>Map of properties by rental status</description>\n\n\t\t<Style id="rental">\n\t\t\t<IconStyle>\n\t\t\t\t<Icon>\n\t\t\t\t\t<href>http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png</href>\n\t\t\t\t</Icon>\n\t\t\t</IconStyle>\n\t\t</Style>\n\t    <Style id="homeOwner">\n\t\t\t<IconStyle>\n\t\t\t\t<Icon>\n\t\t\t\t\t<href>http://maps.google.com/mapfiles/kml/pushpin/green-pushpin.png</href>\n\t\t\t\t</Icon>\n\t\t\t</IconStyle>\n\t\t</Style>',
    "placemarkKml": '\t\t<Placemark>\n\t\t\t<styleUrl>{0}</styleUrl>\n\t\t\t<name>{1}</name>\n\t\t\t<Point>\n\t\t\t\t<coordinates>{2},0</coordinates>\n\t\t\t</Point>\n\t\t</Placemark>\n',
    "kmlEndString": '\n\t</Document>\n</kml>',
    "noRecord": "noRecord",
    "badAddress": "badAddress",
    "timeOutException": "timeout",
    "parcelNotFoundText": "sresult-detail-norecord-found",
    "maxTimeoutAttempts": 3
}