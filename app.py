from flask import Flask, render_template, request, send_file, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
import json
import csv
from flask_restful import Resource, Api, reqparse, fields, marshal_with, abort
from sqlalchemy.engine.row import Row

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:bazepodataka@localhost/VlaznostZraka'
db = SQLAlchemy(app)
api = Api(app)

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

class Database(Resource):
    #@marshal_with(databaseFields)
    def get(self):
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
        results = query.all()
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

        return {'status': "200 OK", 'message': "fetched successfully", 'response': data}
 
    
    
class Datapoint(Resource):
    def get(self, id):
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
        results = query.all()

        if(len(results) <= id):
            return {'status': "404 Not found", 'message': "Object with the provided ID doesn't exist", 'response': None}

        data = {
                "ime_drzave": results[id].ime_drzave,
                "ime_grada": results[id].ime_grada,
                "godina": results[id].godina,
                "mjesec": results[id].mjesec,
                "dan": results[id].dan,
                "sat": results[id].sat,
                "ime_postaje": results[id].ime_postaje,
                "geografska_sirina": results[id].geografska_sirina,
                "geografska_duzina": results[id].geografska_duzina,
                "vlaznost_zraka": results[id].vlaznost_zraka,
            }

        return {'status': "200 OK", 'message': "fetched successfully", 'response': data}


class DatapointMjerenje(Resource):
    def get(self, id):
        query = db.session.query(
        Mjerenje.godina,
        Mjerenje.mjesec,
        Mjerenje.dan,
        Mjerenje.sat,
        Mjerenje.vlaznost_zraka)
        results = query.all()

        if(len(results) <= id):
            return {'status': "404 Not found", 'message': "Object with the provided ID doesn't exist", 'response': None}

        data = {
                "godina": results[id].godina,
                "mjesec": results[id].mjesec,
                "dan": results[id].dan,
                "sat": results[id].sat,
                "vlaznost_zraka": results[id].vlaznost_zraka,
            }

        return {'status': "200 OK", 'message': "fetched successfully", 'response': data}
    

class DatapointPostaja(Resource):
    def get(self, id):
        query = db.session.query(
        MeteoroloskaPostaja.ime_postaje,
        MeteoroloskaPostaja.geografska_sirina,
        MeteoroloskaPostaja.geografska_duzina)
        results = query.all()

        if(len(results) <= id):
            return {'status': "404 Not found", 'message': "Object with the provided ID doesn't exist", 'response': None}

        data = {
                "ime_postaje": results[id].ime_postaje,
                "geografska_sirina": results[id].geografska_sirina,
                "geografska_duzina": results[id].geografska_duzina,
            }

        return {'status': "200 OK", 'message': "fetched successfully", 'response': data}
    

class DatapointDrzavaGrad(Resource):
    def get(self, id):
        query = db.session.query(
        Drzava.ime_drzave,
        Grad.ime_grada,
        ).join(Grad, Drzava.id_drzave == Grad.id_drzave)
        results = query.all()

        if(len(results) <= id):
            return {'status': "404 Not found", 'message': "Object with the provided ID doesn't exist", 'response': None}

        data = {
                "ime_drzave": results[id].ime_drzave,
                "ime_grada": results[id].ime_grada,
            }

        return {'status': "200 OK", 'message': "fetched successfully", 'response': data}


class DodajDrzavu(Resource):
    def post(self, ime):
        postojeca_drzava = Drzava.query.filter_by(ime_drzave=ime).first()
        if postojeca_drzava:
            return {'status': "400 Bad request", 'message': "Drzava vec postoji", 'response': None}
        
        nova_drzava = Drzava(ime_drzave=ime)
        try:
            db.session.add(nova_drzava)
            db.session.commit()
            return {'status': "200 OK", 'message': "Drzava uspjesno dodana", 'response': None}
        except Exception as e:
            db.session.rollback()
            return {'status': "500 Internal server error", 'message': "Doslo je do pogreske prilikom dodavanja drzave", 'response':  str(e)}


class IzmijeniDrzavu(Resource):
    def put(self, id, ime):
        try:
            drzava = Drzava.query.get(id)
            if not drzava:
                return {'status': "400 Bad request", 'message': "Drzava ne postoji", 'response': None}

            drzava.ime_drzave = ime
            db.session.commit()
            return {'status': "200 OK", 'message': "Ime drzave uspjesno izmjenjeno", 'response': None}
        except Exception as e:
            db.session.rollback()
            return {"message": "Došlo je do greške prilikom ažuriranja države.", "response": str(e)}  


class MakniDrzavu(Resource):
    def delete(self, id):
        try:
            drzava = Drzava.query.get(id)
            if not drzava: 
                return {'status': "400 Bad request", 'message': "Drzava ne postoji", 'response': None}
            db.session.delete(drzava)
            db.session.commit()
            return {'status': "200 OK", 'message': "Drzava uspjesno obrisana", 'response': None}
        except Exception as e:
            db.session.rollback()
            return {'status': "500 Internal server error", 'message': "Doslo je do pogreske prilikom brisanja drzave", 'response':  str(e)}


api.add_resource(Database, "/api/database") #a
api.add_resource(Datapoint, "/api/datapoint/<int:id>") #b
api.add_resource(DatapointMjerenje, "/api/datapointMjerenje/<int:id>") #c1
api.add_resource(DatapointPostaja, "/api/datapointPostaja/<int:id>") #c2
api.add_resource(DatapointDrzavaGrad, "/api/datapointDrzavaGrad/<int:id>") #c3
api.add_resource(DodajDrzavu, "/api/dodajDrzavu/<string:ime>") #d
api.add_resource(IzmijeniDrzavu, "/api/izmijeniDrzavu/<int:id>/<string:ime>") #e
api.add_resource(MakniDrzavu, "/api/makniDrzavu/<int:id>") #f

if __name__ in "__main__":
    app.run(debug=True)