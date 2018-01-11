from ormMethods import createSession, getParcelsWithinGeographicalBoundaries
from KMLMethods import createKMLString
from flask import Flask, render_template, Response, request
app = Flask(__name__)


@app.route("/")
def index():
    return render_template('app.html')

@app.route('/api/generateMappings', methods=["GET"])
def generateMappings():
    print(request)
    parcelsWithinBoundary = getParcelsWithinGeographicalBoundaries(request.args);
    xml = createKMLString(parcelsWithinBoundary);
    return Response(xml, mimetype='text/xml')

if __name__ == "__main__":
    session = createSession()
    app.run(host='0.0.0.0', port=8080)