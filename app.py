from flask import Flask, render_template, request, send_file, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
import json
import csv

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:bazepodataka@localhost/VlaznostZraka'
db = SQLAlchemy(app)

class Drzava(db.Model):
    __tablename__ = "Drzave"
    id_drzave = db.Column(db.Integer, primary_key=True)
    ime_drzave = db.Column(db.String)

class Grad(db.Model):
    __tablename__ = "Gradovi"
    id_grada = db.Column(db.Integer, primary_key=True)
    id_drzave = db.Column(db.Integer, db.ForeignKey('Drzave.id_drzave'))
    ime_grada = db.Column(db.String)

class MeteoroloskaPostaja(db.Model):
    __tablename__ = "Meteoroloske_postaje"
    id_postaje = db.Column(db.Integer, primary_key=True)
    ime_postaje = db.Column(db.String)
    id_grada = db.Column(db.Integer, db.ForeignKey('Gradovi.id_grada'))
    geografska_sirina = db.Column(db.Float)
    geografska_duzina = db.Column(db.Float)

class Mjerenje(db.Model):
    __tablename__ = "Mjerenja"
    id_mjerenja = db.Column(db.Integer,primary_key=True)
    godina = db.Column(db.Integer)
    mjesec = db.Column(db.Integer)
    dan = db.Column(db.Integer)
    sat = db.Column(db.Integer)
    id_postaje = db.Column(db.Integer, db.ForeignKey('Meteoroloske_postaje.id_postaje'))
    vlaznost_zraka = db.Column(db.Integer)

data = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/preuzmiCSV")
def preuzmi_csv():
    path = "meteoroloskiPodaci.csv"
    return send_file(path ,as_attachment=True)

@app.route("/preuzmiJSON")
def preuzmi_json():
    path = "meteoroloskiPodaci.json"
    return send_file(path ,as_attachment=True)

@app.route("/datatable")
def datatable():
    return render_template("datatable.html")


@app.route("/updateTable", methods=['GET'])
def update_table():
    search_query = request.args.get("query", "")
    search_field = request.args.get("field", "Wildcard")

    query = db.session.query(
        Drzava.ime_drzave,
        Grad.ime_grada,
        Mjerenje.godina,
        Mjerenje.mjesec,
        Mjerenje.dan,
        Mjerenje.sat,
        MeteoroloskaPostaja.ime_postaje,
        MeteoroloskaPostaja.geografska_sirina,
        MeteoroloskaPostaja.geografska_duzina,
        Mjerenje.vlaznost_zraka
    ).join(Grad, Drzava.id_drzave == Grad.id_drzave) \
     .join(MeteoroloskaPostaja, Grad.id_grada == MeteoroloskaPostaja.id_grada) \
     .join(Mjerenje, MeteoroloskaPostaja.id_postaje == Mjerenje.id_postaje)

    if search_query:
        if search_field == "Drzava":
            query = query.filter(Drzava.ime_drzave.ilike(f"%{search_query}%"))
        elif search_field == "Grad":
            query = query.filter(Grad.ime_grada.ilike(f"%{search_query}%"))
        elif search_field == "Godina":
            query = query.filter(Mjerenje.godina.cast(db.String).ilike(f"%{search_query}%"))
        elif search_field == "Mjesec":
            query = query.filter(Mjerenje.mjesec.cast(db.String).ilike(f"%{search_query}%"))
        elif search_field == "Dan":
            query = query.filter(Mjerenje.dan.cast(db.String).ilike(f"%{search_query}%"))
        elif search_field == "Sat":
            query = query.filter(Mjerenje.sat.cast(db.String).ilike(f"%{search_query}%"))
        elif search_field == "Ime postaje":
            query = query.filter(MeteoroloskaPostaja.ime_postaje.ilike(f"%{search_query}%"))
        elif search_field == "Geografska sirina":
            query = query.filter(MeteoroloskaPostaja.geografska_sirina.cast(db.String).ilike(f"%{search_query}%"))
        elif search_field == "Geografska duzina":
            query = query.filter(MeteoroloskaPostaja.geografska_duzina.cast(db.String).ilike(f"%{search_query}%"))
        elif search_field == "vlaznost_zraka":
            query = query.filter(Mjerenje.vlaznost_zraka.ilike(f"%{search_query}%"))
        else:
            query = query.filter(
                or_(
                    Drzava.ime_drzave.ilike(f"%{search_query}%"),
                    Grad.ime_grada.ilike(f"%{search_query}%"),
                    MeteoroloskaPostaja.ime_postaje.ilike(f"%{search_query}%"),
                    Mjerenje.godina.cast(db.String).ilike(f"%{search_query}%"),
                    Mjerenje.mjesec.cast(db.String).ilike(f"%{search_query}%"),
                    Mjerenje.dan.cast(db.String).ilike(f"%{search_query}%"),
                    Mjerenje.sat.cast(db.String).ilike(f"%{search_query}%"),
                    MeteoroloskaPostaja.geografska_sirina.cast(db.String).ilike(f"%{search_query}%"),
                    MeteoroloskaPostaja.geografska_duzina.cast(db.String).ilike(f"%{search_query}%"),
                    Mjerenje.vlaznost_zraka.cast(db.String).ilike(f"%{search_query}%")
                )
            )

    results = query.all()
    global data
    data = [
        {
            "ime_drzave": result.ime_drzave,
            "ime_grada": result.ime_grada,
            "godina": result.godina,
            "mjesec": result.mjesec,
            "dan": result.dan,
            "sat": result.sat,
            "ime_postaje": result.ime_postaje,
            "geografska_sirina": result.geografska_sirina,
            "geografska_duzina": result.geografska_duzina,
            "vlaznost_zraka": result.vlaznost_zraka,
        }
        for result in results
    ]

    return {"data": data}

@app.route("/preuzmiCSVtablice")
def preuzmi_csv_filtriran():
    csv_output = []

    for row in data:
        csv_output.append([
            row["ime_drzave"], row["ime_grada"], row["godina"], row["mjesec"],
            row["dan"], row["sat"], row["ime_postaje"], row["geografska_sirina"],
            row["geografska_duzina"], row["vlaznost_zraka"]
        ])

    def generate_csv():
        for line in csv_output:
            yield ",".join(map(str, line)) + "\n"

    response = Response(generate_csv(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=filtered_data.csv"
    return response


@app.route("/preuzmiJSONtablice")
def preuzmi_json_filtriran():
    response = Response(json.dumps(data, indent=4), mimetype="application/json")
    response.headers["Content-Disposition"] = "attachment; filename=meteoroloskiPodaci.json"
    return response


if __name__ in "__main__":
    app.run(debug=True)