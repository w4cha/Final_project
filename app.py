# Libraries
import sqlite3
from cs50 import SQL
import pandas as pd
import openpyxl
from flask import Flask, redirect, render_template, request, send_file, session, flash
from flask_session import Session
from markupsafe import Markup
from tools import clean, format, esta, seek_info
from werkzeug.security import check_password_hash, generate_password_hash

# Global variables

# translate column names from the database to text to be displayed in the html document

TIPO_MATERIAL = {"glass": "Vidrio", "paper": "Papel", "paperboard": "Cartoncillo", 
                 "cardboard": "Cartón", "plastic": "Plásticos", "metal": "Metal", 
                 "power_bank": "Baterías", "phone": "Celulares", 
                 "electronic": "Electrodomésticos", "oil": "Aceite", "battery": "Pilas", 
                 "tire": "Neumáticos"}

MATERIAL_TIPO = dict(map(reversed, TIPO_MATERIAL.items()))

INFO = {"commune_id": "Comuna", "address_na": "Dirección", 
        "region_id": "Región", "owner": "Dueño", "manager": "Administrador", 
        "status": "Estado", "type": "Tipo", "address_nu": "Número", "OBJECTID": "Identificador", 
        "Open": "Abierto", "Close": "Cerrado"}

LABELS = {**TIPO_MATERIAL, **INFO}

# save path to files use to store information to be displayed inside a html

MATERIAL_DESCRIPTION = "/files/informacion_materiales.txt"

MATERIAL_IMAGE = "/files/imagenes_materiales.txt"

DELETED_ENTRIES_BACKUP = "/files/borradas.txt"

# save variables that are used to know what kind of information to display in the webpages

REGION_ACTUAL = []

COMUNA_ACTUAL = ["Comuna"]

CURRENT_ENTRY = []

# list to append error messages that are later flashed when redirected if the
# user makes an invalid action

ERROR = []

# list to append success messages that are later flashed when redirected if
# the user action was completed without raising any errors

SUCCESS = []

# app configuration

app = Flask(__name__)

# adding jinja support to use the keyword continue inside loops

app.jinja_env.add_extension("jinja2.ext.loopcontrols")

# session configuration

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# autoreload templetes when changes are detected

app.config["TEMPLATES_AUTO_RELOAD"] = True

# saving the app path in a variable 

path = app.root_path

# linking the app to the database to execute queries when needed

db = SQL(f"sqlite:///{path}/files/puntos_de_reciclaje.db")

# saving the path to text files where information that is displayed
# in the html documents is stored

material_path = f"{path}{MATERIAL_DESCRIPTION}"

image_path = f"{path}{MATERIAL_IMAGE}"

back_up_path = f"{path}{DELETED_ENTRIES_BACKUP}"


# check if any registered user is signed in and return a value that is
# use to show different content to users signed in and not signed in
def dentro():
    if session.get("user_id") is None:
        return 0
    else:
        return 1


# makes sure the password the user choose has at least 1 not alphanumeric character
# 5 letters and 2 numbers
def secure(contra):
    numbers = sum(c.isdigit() for c in contra)
    letters = sum(c.isalpha() for c in contra)
    sola = len(contra) - numbers - letters
    if numbers < 2:
        return 0
    elif letters < 5:
        return 0
    elif sola < 1:
        return 0
    else:
        return 1


# any change done to the database is registered in the hitorial table inside
# the puntos_de_reciclaje.db database
def history(change, entry):
    person = db.execute("SELECT user_id, user_email, user_power FROM usuarios_registrados WHERE user_id = ?", session["user_id"])
    db.execute("INSERT INTO historial (email, power, change_type, entry_or_user_value) "
               "VALUES(?, ?, ?, ?)", person[0]["user_email"], person[0]["user_power"], change, entry)


# what to do after a server request is processed
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# home page route
@app.route("/", methods=["GET"])
def inicio():

    # get the data to display in the page

    regiones = clean(db.execute("SELECT region_id FROM reciclaje"))

    # check if user is signed in or not

    some = dentro()

    # if status is a key in the get request positive feedback
    # is returned to the user about the action he just did
    # where the message content varies depending on the value of the status key

    if "status" in request.args:
        promesa = request.args.get("status")
        if promesa == "Exito":
            flash("Sesión iniciada exitosamente")
            return render_template("inicio.html", status=1, region=regiones, index=1, editor=1) 
        elif promesa == "No":
            flash("Debe ingresar coreo y contraseña")
            return render_template("inicio.html", status=0, region=regiones, index=1, editor=0)
        elif promesa == "copia":
            if some == 1:
                flash("Identificador de entrada copiado al portapapeles")
                return render_template("inicio.html", status=1, region=regiones, index=1, editor=some)
            else:
                flash(Markup("Identificador de entrada copiado al portapapeles, "
                             "al no estar registrado como editor puede seguir el <br>"
                             "siguiente <a class='link' href='/contacto'> link <a>" 
                             "para pedir que una entrada sea modificada"))
                return render_template("inicio.html", status=3, region=regiones, index=1, editor=some)
        elif promesa == "Borrado":
            flash("Su sesión fue eliminada exitosamente")
            return render_template("inicio.html", status=1, region=regiones, index=1, editor=0)
        elif promesa == "Cerrado":
            flash("Sesión cerrada exitosamente")
            return render_template("inicio.html", status=1, region=regiones, index=1, editor=0)
        else:
            flash(f"Campo incorrecto: {promesa}")
            return render_template("inicio.html", status=0, region=regiones, index=1, editor=some)

    # if error is a key in the get request negative feedback
    # is returned to the user about the action he just did
    # where the message content varies depending on the value of the error key
           
    elif "error" in request.args:
        copy_value = request.args.get("error")
        if some == 1:
            flash(f"Error al copiar a portapapeles, valor para editar: {copy_value}")
            return render_template("inicio.html", status=2, region=regiones, index=1, editor=some)
        else:
            flash(Markup(f"Error al copiar a portapapeles, valor para editar: {copy_value}<br>"
                         "al no estar registrado como editor puede seguir el <br>"
                         "siguiente <a class='link' href='/contacto'> link <a><br>" 
                         "para pedir que una entrada sea modificada"))
            return render_template("inicio.html", status=2, region=regiones, index=1, editor=some)
    
    # if there is no feedback to give to the user the home page
    # is displayed normally

    else:
        return render_template("inicio.html", status=1, region=regiones, index=1, editor=some)


# route to page with information about recycling
@app.route("/reciclaje", methods=["GET"])
def about():

    # check if user is signed in

    editor = dentro()

    # check if the key puntos or residuos is in the get request
    # to know what contents to display

    if "puntos" in request.args:
        return render_template("about_reciclaje.html", index=0, show=1, editor=editor)
    elif "residuos" in request.args:
        return render_template("about_reciclaje.html", index=0, residuo=1, editor=editor)
    else:
        return render_template("about_reciclaje.html", index=0, show=0, editor=editor)


# route to page with contact information
@app.route("/contacto", methods=["GET"])
def contact():
    im_in = dentro()
    return render_template("contacto.html", index=0, editor=im_in)


# route to download the site upgraded database when the anchor
# element with this route as href is clicked
@app.route("/descarga")
def link():

    # here the database is converted to an excel file
    # using pandas before being send to the user

    sheet_path = f"{path}/files/Puntos_verdes_y_limpios_Chile.xlsx"
    conn = sqlite3.connect(f"{path}/files/puntos_de_reciclaje.db")
    db_df = pd.read_sql_query("SELECT * FROM reciclaje", conn)
    with pd.ExcelWriter(sheet_path) as pen:
        db_df.to_excel(pen, sheet_name="datos_reciclaje", engine="openpyxl")   
    return send_file(sheet_path, as_attachment=True)


# route to download the site deleted entries when the anchor
# element with this route as href is clicked
@app.route("/eliminados")
def ruta():
    return send_file(back_up_path, as_attachment=True)


# here the majority of asynchronous request that the page does are handled
@app.route("/request", methods=["POST"])
def pedidos():

    # here the comunas and type of materials that are recycled
    # inside a region are displayed when a region is selected

    if "region" in request.args:
        REGION_ACTUAL.clear()
        region = request.args.get("region")
        REGION_ACTUAL.append(region)
        COMUNA_ACTUAL.clear()
        COMUNA_ACTUAL.append("Comuna")
        comunas = clean(db.execute(f'SELECT commune_id FROM reciclaje WHERE region_id = "{region}"'))
        lista = []
        for i in TIPO_MATERIAL:
            disponible = db.execute(
                f'SELECT region_id FROM reciclaje WHERE status = "Open" AND region_id = "{region}" AND {i} = "Si"')
            if len(disponible) >= 1:
                lista.append(TIPO_MATERIAL[i])
        return render_template("material.html", material=lista, comuna=comunas), 200

    # display the kind of recycled materials that 
    # a comuna accepts when a specific comuna is chosen

    elif "comuna" in request.args:
        if request.args.get("comuna") == "Comuna":
            COMUNA_ACTUAL.clear()
            COMUNA_ACTUAL.append("Comuna")
            lista = []
            for i in TIPO_MATERIAL:
                disponible = db.execute(
                    f'SELECT region_id FROM reciclaje WHERE status = "Open" AND region_id = "{REGION_ACTUAL[0]}" AND {i} = "Si"')
                if len(disponible) >= 1:
                    lista.append(TIPO_MATERIAL[i])
            return render_template("comuna.html", material=lista, area="región"), 200
        else:
            lista = []
            municipio = request.args.get("comuna")
            COMUNA_ACTUAL.clear()
            COMUNA_ACTUAL.append(municipio)
            for i in TIPO_MATERIAL:
                disponible = db.execute(
                    f'SELECT region_id FROM reciclaje WHERE status = "Open" AND commune_id = "{municipio}" AND {i} = "Si"')
                if len(disponible) >= 1:
                    lista.append(TIPO_MATERIAL[i])
            return render_template("comuna.html", material=lista), 200
    
    # display the information of all the recycling points
    # inside a region or comuna in a table that is send to the webpage

    elif "material" in request.args:
        mater = request.args.get("material")
        lista_ingredientes = mater.split(".")
        lista_ingredientes.remove("")
        permiso = format(lista_ingredientes, COMUNA_ACTUAL, MATERIAL_TIPO, REGION_ACTUAL)
        if permiso != 'unexpected error':
            tabla = clean(db.execute(permiso))
            if len(tabla) != 0:
                if COMUNA_ACTUAL[0] != "Comuna":
                    table_head = ["Dirección"]
                    keys = ["OBJECTID", "the_geom", "address_na"]
                    for write in lista_ingredientes:
                        table_head.append(write)
                        keys.append(MATERIAL_TIPO[write])
                    table_head.append("Acción")
                else:
                    table_head = ["Comuna"]
                    table_head.append("Dirección")
                    keys = ["OBJECTID", "the_geom", "commune_id", "address_na"]
                    for write in lista_ingredientes:
                        table_head.append(write)
                        keys.append(MATERIAL_TIPO[write])
                    table_head.append("Acción")
                return render_template("tabla.html", head=table_head, content=tabla, llave=keys, label=LABELS), 200
            else:
                return "No hay resultados para la búsqueda", 200
        else:
            return "", 404 

    # display a list of comunas inside a selected region
    # that currently accept the type of material selected
    # in the switch checkbox to be recycled

    elif "consulta" in request.args:
        objeto = request.args.get("consulta")
        cosas = clean(db.execute(
            f'SELECT commune_id FROM reciclaje WHERE {MATERIAL_TIPO[objeto]} = "Si" AND region_id = "{REGION_ACTUAL[0]}"'))
        frase = f"En las siguientes comunas se pueden reciclar {objeto}: "
        for v in range(0, len(cosas)):
            if len(cosas) == 1:
                frase += f"{cosas[v]['commune_id']}."
            elif len(cosas) == 2:
                if v == 0:
                    frase += f"{cosas[v]['commune_id']} y "
                else:
                    frase += f"{cosas[v]['commune_id']}."
            else:
                if v >= 0 and v < len(cosas) - 2:
                    frase += f"{cosas[v]['commune_id']}, "
                elif v == len(cosas) - 2:
                    frase += f"{cosas[v]['commune_id']} y "
                else:
                    frase += f"{cosas[v]['commune_id']}."
        return frase, 200

    # display additional information about an entry (recycling point)
    # when the user press the button to see the map of the location

    elif "info" in request.args:
        devolver = request.args.get("info")
        escrito = db.execute("SELECT * FROM reciclaje WHERE OBJECTID = ?", devolver)
        if len(escrito) == 0:
            return "", 404
        else:
            ind = escrito[0]
            solid = esta(ind, TIPO_MATERIAL)
            if solid != "db_error" or len(solid) != 0:
                try:
                    contenido = (f"Este lugar es uno de los "
                                 f"<a href='/reciclaje?puntos=info' class='link'>{ind['type']}</a> "
                                 f"que pertenece a {ind['owner']} y es manejado actualmente " 
                                 f"por {ind['manager']}")
                    solido = " y en el se pueden reciclar: "
                    for m in solid:
                        if len(solid) == 1:
                            solido += f"{m}."
                        elif len(solid) == 2:
                            if m == solid[len(solid) - 1]:
                                solido += f"{m}."
                            else:
                                solido += f"{m} y "
                        else:
                            if m == solid[len(solid) - 1]:
                                solido += f"{m}."
                            elif m == solid[len(solid) - 2]:
                                solido += f"{m} y "
                            else:
                                solido += f"{m}, "
                    solido += (f"<br>Número de entrada: {ind['OBJECTID']}"
                               "<br><button title='Cambiar datos' class='map_button'"
                               f"name='{ind['OBJECTID']}' onclick='clipboard_copy(this.name);'>Editar</button>")
                    return contenido+solido, 200
                except KeyError:
                    return "", 404
            else:
                return "", 404

    # seeks information stored in the informacion_materiales.txt
    # and returns it to be display in a html document

    elif "SolidInfo" in request.args:
        titulo = request.args.get("SolidInfo")
        decision = seek_info(material_path, titulo)
        if decision == "":
            return "", 404
        else:
            return decision, 200 

    # seeks information stored in the imagenes_materiales.txt
    # and returns it to be display in a html document

    elif "SolidImage" in request.args:
        encabezado = request.args.get("SolidImage")
        resolve = seek_info(image_path, encabezado)
        if resolve == "":
            return "", 404
        else:
            return resolve, 200

    # returns information of an entry when a page editor or admin
    # (signed users that can change entries info) ask for it on input

    elif "entry-info" in request.args:
        pase = request.args.get("entry-info")
        entry = db.execute("SELECT * FROM reciclaje WHERE OBJECTID = ?", pase)
        filter = ["the_geom", "lat", "lng", "address_ty"]
        hold = []
        if len(entry) == 1:
            CURRENT_ENTRY.clear()
            CURRENT_ENTRY.append(pase)
            see = entry[0]
            for t in see:
                if t in filter:
                    continue
                elif see[t] == "No":
                    continue
                elif t in TIPO_MATERIAL:
                    hold.append(f"{TIPO_MATERIAL[t]}: Si")
                elif t == "status":
                    hold.append(f"{INFO[t]}: {INFO[see[t]]}")
                else:
                    hold.append(f"{INFO[t]}: {see[t]}")
            return render_template("sub-menu.html", modo="entrada", extra=hold), 200
        else:
            return "", 404
    else:
        return "", 404


# this is the route for the entry and users editing page that can
# only be entered if the user is signed in this page replace the 
# contact section of the site when a editor or admin user stars a session 
@app.route("/sesion_editor", methods=["GET"])
def welcome():

    # here we check if there is a signed in user and 
    # check if the signed in user is an admin or editor
    # an admin can delete users but an editor can't the contents
    # shown in the page change if the user is an admin or an editor

    try:
        power = db.execute("SELECT user_power FROM usuarios_registrados WHERE user_id = ?", session["user_id"])
    except KeyError:
        return redirect("/", 302)
    
    if len(power) == 1:

        # if the status key is present in the get request
        # we check if is value is either error or success

        if "status" in request.args:

            # here if an action that is made by an editor or admin to change entries
            # or users is invalid an error message stored inside the ERROR variable is flashed 

            if request.args.get("status") == "error":
                flash(ERROR[0])
                if power[0]["user_power"] == "admin":
                    return render_template("sesion_editor.html", power="admin", status=2)
                else:
                    return render_template("sesion_editor.html", power="editor", status=2)
            
            # here if an action that is made by an editor or admin to change entries
            # or users is valid a success message stored inside the SUCCESS variable is flashed

            else:
                flash(SUCCESS[0])
                if power[0]["user_power"] == "admin":
                    return render_template("sesion_editor.html", power="admin", status=3)
                else:
                    return render_template("sesion_editor.html", power="editor", status=3)

        # if there is no key in the get request the editing page
        # is normally displayed without flashing messages
               
        else:
            if power[0]["user_power"] == "admin":
                return render_template("sesion_editor.html", power="admin")
            else:
                return render_template("sesion_editor.html", power="editor")
    else:
        return redirect("/", 302)


# route to process the form with the login information of an user
@app.route("/login", methods=["POST"])
def sesion():

    # here we check that a user email is submitted

    if not request.form.get("email") or not request.form.get("password"):
        return redirect("/?status=No", 302)

    # then we see if the user email is in the database
    # to see if he has an account

    correo = request.form.get("email")
    clave = request.form.get("password")
    enter = db.execute("SELECT * FROM usuarios_registrados WHERE user_email = ?", correo)
    if len(enter) == 0:
        return redirect("/?status=Correo", 302)

    # then we check that its password match
    # the one saved in the database

    if len(enter) != 0 and not check_password_hash(enter[0]["user_pass"], clave):
        return redirect("/?status=Clave", 302)

    # if both email and password are correct
    # then we finally save the user id of 
    # the current signed in user so the server
    # knows that from now on it has to show
    # page contents that are accessible to
    # a logged in user

    session["user_id"] = enter[0]["user_id"]
    return redirect("/?status=Exito", 302)


# this route is used for user to exit their current session
@app.route("/out", methods=["GET"])
def out():
    session.clear()
    return redirect("/?status=Cerrado"), 302


# route to handle async function that returns
# different types of menu options to 
# edit an entry
@app.route("/morph", methods=["POST"])
def type():
    if "type" in request.args:
        part = request.args.get("type")
        if part == "no-mater":
            return render_template("sub-menu.html", modo=part, what=CURRENT_ENTRY[0]), 200 
        elif part == "mater":
            return render_template("sub-menu.html", modo=part, what=CURRENT_ENTRY[0]), 200
        else:
            return "", 404
    else:
        return "", 404


# route to handle an async function request
# depending on what the key is in the post
# request different sections of html documents are returned
# here we return either different menu options, tables or other html content
@app.route("/member", methods=["POST"])
def to_do():
    if "request" in request.args:
        roma = request.args.get("request")
        if roma == "editar":
            return render_template("editar.html", modo=roma), 200
        elif roma == "usuarios":
            return render_template("editar.html", modo=roma), 200
        elif roma == "añadir":
            return render_template("editar.html", modo=roma), 200
        elif roma == "contraseña":
            return render_template("editar.html", modo=roma), 200
        elif roma == "cambio":
            return render_template("sub-sub-menu.html", opcion=roma, what=CURRENT_ENTRY[0]), 200
        elif roma == "elimina":
            return render_template("sub-sub-menu.html", opcion=roma, what=CURRENT_ENTRY[0]), 200
        elif roma == "visibilidad":
            return render_template("sub-sub-menu.html", opcion=roma, what=CURRENT_ENTRY[0]), 200
        elif roma == "historial":
            return render_template("editar.html", modo=roma), 200
        elif roma in ["entrada eliminada", "nueva entrada"]:
            regist = db.execute("SELECT * FROM historial WHERE change_type = ?", roma)
            if roma == "entrada eliminada":
                poder = db.execute("SELECT user_power FROM usuarios_registrados WHERE user_id = ?", session["user_id"])
                if poder[0]["user_power"] == "admin":
                    return render_template("sub-menu.html", modo="registro", entries=regist, might="admin"), 200
                else:
                    return render_template("sub-menu.html", modo="registro", entries=regist, might="editor"), 200
            else:
                return render_template("sub-menu.html", modo="registro", entries=regist)
        elif roma == "usuario añadido":
            regist = db.execute("SELECT * FROM historial WHERE change_type LIKE 'usuario añadido%'")
            return render_template("sub-menu.html", modo="registro", entries=regist), 200
        elif roma == "usuario eliminado":
            regist = db.execute("SELECT * FROM historial WHERE change_type LIKE 'usuario eliminado%'")
            return render_template("sub-menu.html", modo="registro", entries=regist), 200
        elif roma == "entrada editada":
            regist = db.execute("SELECT * FROM historial WHERE change_type LIKE 'valor%' OR change_type = 'entrada visible' "
                                "OR change_type = 'entrada ocultada'")
            return render_template("sub-menu.html", modo="registro", entries=regist), 200
        elif roma == "delet_user":
            return render_template("sub-menu.html", modo=roma)
        elif roma == "add_user":
            return render_template("sub-menu.html", modo=roma)
        else:       
            return "", 404
    else:
        return "", 404


# here the form containing the info for
# a new entry is check to see if is 
# compatible and logical to the other entries info
# this form is submitted when an editor or admin user
# want to add a new entry
@app.route("/add", methods=["POST"])
def add():

    # first we clean any error or success messages
    # that may have been stored in other routes
    # if any error is raise this route redirects to other
    # route and a error message is flashed in the new route

    ERROR.clear()
    SUCCESS.clear()

    # here we check that all 6 required inputs to add
    # a new entry are not empty strings

    residuos = []
    info_add = ["región", "comuna", "latitud", "longitud", "tipo punto"]
    opcionales = {"dirección": "address_na", "número-dirección": "address_nu", 
                  "dueño": "owner", "administrador": "manager"}
    campos = ""
    for h in info_add:
        if not request.form.get(h):
            campos += f" {h}"
    if len(campos) != 0:
        ERROR.append(f"Operación no se llevo a cabo, ya que faltaron los siguientes campos por llenar:{campos}")
    if len(ERROR) != 0:
        return redirect("/sesion_editor?status=error"), 302
    for y in TIPO_MATERIAL:
        if y in request.form:
            residuos.append(y)
    if len(residuos) == 0:
        ERROR.append("Debe seleccionar al menos un tipo de residuo")
        return redirect("/sesion_editor?status=error"), 302

    # here we check that the latitud and longitud
    # of the new entry is inside the boundaries for
    # values of latitud and longitud found inside Chile

    lat = request.form.get("latitud")
    ln = request.form.get("longitud")
    try:
        if float(lat) <= 0 or float(ln) <= 0:
            pass
        else:
            ERROR.append("Los valores de latitud y longitud tienen que ser números negativos")
            return redirect("/sesion_editor?status=error"), 302
        if -90 <= float(lat) <= -60 or -57 <= float(lat) <= -17:
            pass
        else:
            ERROR.append("El valor de latitud no se encuentra entre los rangos aceptados")
            return redirect("/sesion_editor?status=error"), 302
        if -110 < float(ln) < -109 or -81 <= float(ln) <= -77 or -75 <= float(ln) <= -65:
            pass
        else:
            ERROR.append("El valor de longitud no se encuentra entre los rangos aceptados")
            return redirect("/sesion_editor?status=error"), 302
    except ValueError:
        ERROR.append("Los valores de latitud y longitud tienen que ser números")
        return redirect("/sesion_editor?status=error"), 302
    the_geom = f"POINT ({ln} {lat})"

    # here we check that the user selected a valid recycling point type

    if request.form.get("tipo punto") in ["Puntos Verdes", "Puntos Limpios"]:
        pass
    else:
        ERROR.append("El lugar de reciclaje debe ser un Punto verde o Punto Limpio")
        return redirect("/sesion_editor?status=error"), 302

    # once we check the values are correct we insert them
    # as a new row in our database

    zona1 = request.form.get("región")
    zona2 = request.form.get("comuna")
    typoint = request.form.get("tipo punto")
    last_entry = db.execute("INSERT INTO reciclaje (the_geom, lat, lng, status, type, region_id, commune_id) "
                            "VALUES (?, ?, ?, 'Open', ?, ?, ?)", the_geom, lat, ln, typoint, zona1, zona2)
    
    # then we update the new entry with the values
    # selected in the switch checkbox section of the form
    # the user can select up to 12 values at a time

    for rsd in residuos:
        db.execute("UPDATE reciclaje SET ? = 'Si' WHERE OBJECTID = ?", rsd, last_entry)

    # finally we update that new entry with the other optional values
    # the user may have entered in the form

    for opt in opcionales:
        elemnt = request.form.get(opt)
        if elemnt != "":
            db.execute("UPDATE reciclaje SET ? = ? WHERE OBJECTID = ?", opcionales[opt], elemnt, last_entry)

    # with the new entry created now we insert a row into the historial table
    # to show that an user has altered the database
    # then a success message is send to be flash 
    # in the new route this route redirects to

    history('nueva entrada', last_entry)
    SUCCESS.append(f"Entrada añadida exitosamente, número de la nueva entrada: {last_entry}")
    return redirect("/sesion_editor?status=exito"), 302


# this route deletes an entry when an admin
# or editor request it
@app.route("/delet", methods=["POST"])
def subtraction():

    # first we clean any error or success messages
    # that may have been stored in other routes
    # if any error is raise this route redirects to other
    # route and a error message is flashed in the new route

    ERROR.clear()
    SUCCESS.clear()

    # here we make sure that the entry the user wants to delete
    # has not been deleted already

    if request.form.get("borrar"):
        to_delete = request.form.get("borrar")
        esta = db.execute("SELECT * FROM reciclaje WHERE OBJECTID = ?", to_delete)
        if len(esta) == 0:
            ERROR.append("La entrada que intenta borrar no existe")
            return redirect("/sesion_editor?status=error"), 302

        # once we now the entry has not been deleted already here we first 
        # create a backup to the entry in the borradas.txt file that can be
        # downloaded in the /eliminados route then we delete the entry from
        # the database and finally return a success message to be flashed in
        # the route this route redirect to

        else:
            db.execute("DELETE FROM reciclaje WHERE OBJECTID = ?", to_delete)
            with open(back_up_path, "a") as backup:
                backup.write(f"Número de entrada: {to_delete}")
                backup.write("\n")
                backup.write(str(esta))
                backup.write("\n")
            history('entrada eliminada', to_delete)
            SUCCESS.append(f"Entrada número {to_delete} borrada exitosamente")
            return redirect("/sesion_editor?status=exito"), 302
    else:
        ERROR.append("Error inesperado al procesar su pedido")
        return redirect("/sesion_editor?status=error"), 302


# make an entry visible or invisible in the search results when
# requested by an user
@app.route("/show", methods=["POST"])
def show():

    # first we clean any error or success messages
    # that may have been stored in other routes
    # if any error is raise this route redirects to other
    # route and an error message is flashed in the new route

    ERROR.clear()
    SUCCESS.clear()

    # here we check that the user gave a valid change option and
    # valid entry identification number to apply the changes to

    if request.form.get("ocultar"):
        if request.form.get("entry"):
            to_cover = request.form.get("ocultar")
            to_change = request.form.get("entry")
            entry = db.execute("SELECT status FROM reciclaje WHERE OBJECTID = ?", to_change)
            if len(entry) != 0:

                # here we check that the user selected either
                # that he wants to make the entry visible or not

                if to_cover == "Close":

                    # here we check if the current entry has its status set
                    # to visible (Open) or invisible (Close)
                    # if the entry is going to be set to invisible then we check if it is already
                    # invisible or not if it is not already invisible then we make it invisible
                    # in the database and then regist that change by the user in the historial
                    # table and a success message is raise
                    # if the table was already invisible then an error message is raise

                    if entry[0]["status"] == "Close":
                        ERROR.append("La entrada que intenta ocultar ya estaba ocultada")
                        return redirect("/sesion_editor?status=error"), 302
                    else:
                        db.execute("UPDATE reciclaje SET status = 'Close' WHERE OBJECTID = ?", to_change)
                        history('entrada ocultada', to_change)
                        SUCCESS.append(f"Entrada número {to_change} ocultada exitosamente")
                        return redirect("/sesion_editor?status=exito"), 302
               
                elif to_cover == "Open":

                    # here we check if the current entry has its status set
                    # to visible (Open) or invisible (Close)
                    # if the entry is going to be set to visible then we check if it is already
                    # visible or not if it is not already visible then we make it visible
                    # in the database and then regist that change by the user in the historial
                    # table and a success message is raise
                    # if the table was already visible then an error message is raise
                    
                    if entry[0]["status"] == "Open":
                        ERROR.append("La entrada que intenta hacer visible ya era visible")
                        return redirect("/sesion_editor?status=error"), 302
                    else:
                        db.execute("UPDATE reciclaje SET status = 'Open' WHERE OBJECTID = ?", to_change)
                        history('entrada visible', to_change)
                        SUCCESS.append(f"Entrada número {to_change} hecha visible exitosamente")
                        return redirect("/sesion_editor?status=exito"), 302

                # an error is raise if the user try to pass any
                # value other than Close or Open

                else:
                    ERROR.append("Debe seleccionar mostrar u ocultar")
                    return redirect("/sesion_editor?status=error"), 302

            # an error is raise if the identification number
            # is not found in the database

            else:
                ERROR.append(f"Hubo un error al procesar su pedido: entrada {to_change} no encontrada")
                return redirect("/sesion_editor?status=error"), 302

        # an error is raise if the identification number
        # is an empty string

        else:
            ERROR.append("Error inesperado al procesar su pedido")
            return redirect("/sesion_editor?status=error"), 302

    # an error is raise if the change type
    # is an empty string

    else:        
        ERROR.append("Error inesperado al procesar su pedido")
        return redirect("/sesion_editor?status=error"), 302


# Here we check the form submitted by an user
# to change one of the 14 changeable values of an entry
@app.route("/change", methods=["POST"])
def changing():

    # first we clean any error or success messages
    # that may have been stored in other routes
    # if any error is raise this route redirects to other
    # route and a error message is flashed in the new route

    ERROR.clear()
    SUCCESS.clear()

    # here we see if the identification number
    # of the entry was submitted

    if request.form.get("valor-ref"):
        see_value = request.form.get("valor-ref")
        see_if_in = db.execute("SELECT * FROM reciclaje WHERE OBJECTID = ?", see_value)
        if len(see_if_in) != 0:

            # here we see what type value of the entry wants to be modify
            # nuevo-valor accepts any string that can be a name as a new value

            if "nuevo-valor" in request.form:
                if request.form.get("nuevo-valor"):
                    if request.form.get("attribute") in ["owner", "manager"]:
                        attr = request.form.get("attribute")
                        new_vl = request.form.get("nuevo-valor")

                        # here we check that the new value is different to the old one
                        # then we update the table with the new value insert a new row
                        # to regist that change and flash a success message in the
                        # redirected route 

                        if see_if_in[0][attr] != new_vl:
                            db.execute("UPDATE reciclaje SET ? = ? WHERE OBJECTID = ?", attr, new_vl, see_value)
                            history(f'valor {INFO[attr]} cambiado desde {see_if_in[0][attr]} a {new_vl}', see_value)
                            SUCCESS.append(
                                f"Valor {INFO[attr]} de entrada {see_value} cambiado exitosamente desde {see_if_in[0][attr]} a {new_vl}")
                            return redirect("/sesion_editor?status=exito"), 302
                        else:
                            ERROR.append("Debe ingresar un valor distinto al original para cambiarlo")
                            return redirect("/sesion_editor?status=error"), 302
                    else:
                        ERROR.append("Error inesperado al procesar su pedido")
                        return redirect("/sesion_editor?status=error"), 302
                else:
                    ERROR.append("Debe ingresar un valor por el cual cambiar")
                    return redirect("/sesion_editor?status=error"), 302

            # add-sub only accepts Si or No as new values
            
            elif "add-sub" in request.form:
                if request.form.get("add-sub") in ["Si", "No"]:
                    if request.form.get("attribute") in TIPO_MATERIAL:
                        attr = request.form.get("attribute")
                        new_vl = request.form.get("add-sub")

                        # here we check that the new value is different to the old one
                        # then we update the table with the new value insert a new row
                        # to regist that change and flash a success message in the
                        # redirected route 

                        if see_if_in[0][attr] != new_vl:
                            db.execute("UPDATE reciclaje SET ? = ? WHERE OBJECTID = ?", attr, new_vl, see_value)
                            history(f'valor {TIPO_MATERIAL[attr]} cambiado desde {see_if_in[0][attr]} a {new_vl}', see_value)
                            SUCCESS.append(
                                f"Valor {TIPO_MATERIAL[attr]} de entrada {see_value} cambiado exitosamente desde {see_if_in[0][attr]} a {new_vl}")
                            return redirect("/sesion_editor?status=exito"), 302
                        else:
                            ERROR.append("Debe ingresar un valor distinto al original para cambiarlo")
                            return redirect("/sesion_editor?status=error"), 302
                    else:
                        ERROR.append("Error inesperado al procesar su pedido")
                        return redirect("/sesion_editor?status=error"), 302
                else:
                    ERROR.append("El valor para cambiar debe ser Si o No")
                    return redirect("/sesion_editor?status=error"), 302

            # if any other value is tried to be change an error is raise
            # and flashed in the redirected route

            else:
                ERROR.append("Error inesperado al procesar su pedido")
                return redirect("/sesion_editor?status=error"), 302
        else:
            ERROR.append(f"Hubo un error al procesar su pedido: entrada {see_value} no encontrada")
            return redirect("/sesion_editor?status=error"), 302
    else:
        ERROR.append("Error inesperado al procesar su pedido")
        return redirect("/sesion_editor?status=error"), 302


# this route is used for users to change their password
@app.route("/pass", methods=["POST"])
def password():

    # first we clean any error or success messages
    # that may have been stored in other routes
    # if any error is raise this route redirects to other
    # route and a error message is flashed in the new route

    ERROR.clear()
    SUCCESS.clear()

    # here we check that the user current password
    # new password and new password confirmation
    # are not empty strings

    if not request.form.get("contraseña actual"):
        ERROR.append("Debe ingresar su contraseña actual para poder cambiarla por una nueva")
        return redirect("/sesion_editor?status=error"), 302
    if not request.form.get("contraseña nueva"):
        ERROR.append("Debe ingresar una nueva contraseña")
        return redirect("/sesion_editor?status=error"), 302
    if not request.form.get("confirmar contraseña"):
        ERROR.append("Debe confirmar su contraseña nueva")
        return redirect("/sesion_editor?status=error"), 302

    # here we check that the user current password is the
    # same as the one in the database and that the new password
    # is the same as the confirmation and different that the
    # example password shown in the webpage and the user current password

    old_p = request.form.get("contraseña actual")
    new_p = request.form.get("contraseña nueva")
    con_p = request.form.get("confirmar contraseña")
    if old_p == new_p:
        ERROR.append("Nueva contraseña no puede ser igual a la anterior")
        return redirect("/sesion_editor?status=error"), 302
    if new_p != con_p:
        ERROR.append("Nueva contraseña no es igual a la confirmación de la nueva contraseña")
        return redirect("/sesion_editor?status=error"), 302
    if "Ejem78%" in new_p:
        ERROR.append("No puede usar esa contraseña")
        return redirect("/sesion_editor?status=error"), 302
    enter = db.execute("SELECT user_pass FROM usuarios_registrados WHERE user_id = ?", session["user_id"])
    if not check_password_hash(enter[0]["user_pass"], old_p):
        ERROR.append("Su contraseña actual es incorrecta")
        return redirect("/sesion_editor?status=error"), 302

    # here we check that the new password is 8 characters long
    # and consist of 1 symbol 5 letters and 2 numbers minimum

    if len(new_p) < 8:
        ERROR.append(f"Nueva contraseña debe tener 8 caracteres, la que eligió tiene {len(new_p)}")
        return redirect("/sesion_editor?status=error"), 302
    if secure(new_p) == 0:
        ERROR.append(f"Nueva contraseña debe contener como mínimo 5 letras, 2 números y 1 símbolo no alfanumérico")
        return redirect("/sesion_editor?status=error"), 302

    # finally the new password is updated to the database
    # in the usuarios_registrados table and a success
    # message is flashed to the redirected route

    new_hashed = generate_password_hash(new_p)
    db.execute("UPDATE usuarios_registrados SET user_pass = ? WHERE user_id = ?", new_hashed, session["user_id"])
    SUCCESS.append("Contraseña cambiada exitosamente")
    return redirect("/sesion_editor?status=exito"), 302


# this route allows signed in users that are admins
# to add other users
@app.route("/user_add", methods=["POST"])
def user_add():

    # first we clean any error or success messages
    # that may have been stored in other routes
    # if any error is raise this route redirects to other
    # route and a error message is flashed in the new route

    ERROR.clear()
    SUCCESS.clear()

    # here we make sure that the required data to add an user
    # was submitted in the form

    requires = ["correo usuario", "contraseña provisional", "poder"]
    falta = ""
    for d in requires:
        if not request.form.get(d):
            falta += f" {d}"
    if len(falta) != 0:
        ERROR.append(f"Operación no se llevo a cabo, ya que faltaron los siguientes campos por llenar:{falta}")
        return redirect("/sesion_editor?status=error"), 302
    if request.form.get("poder") in ["admin", "editor"]:
        pass
    else:
        ERROR.append(f"Debe seleccionar ya sea administrador o editor como poder para el nuevo usuario")
        return redirect("/sesion_editor?status=error"), 302

    # once it was check that data was submitted here
    # we make sure that the user is not trying to add
    # an already added user

    new_email = request.form.get("correo usuario")
    user_power = request.form.get("poder")
    temp_pass = request.form.get("contraseña provisional")
    new_hashed = generate_password_hash(temp_pass)
    is_user = db.execute("SELECT user_email FROM usuarios_registrados WHERE user_email = ?", new_email)
    if len(is_user) != 0:
        ERROR.append("El correo que intenta añadir ya se encuentra registrado en la base de datos por lo que no esta disponible")
        return redirect("/sesion_editor?status=error"), 302

    # finally we add the user to the database and insert a new row in the
    # historial table to regist that someone added an user
    # then a success message is flashed in the redirected route

    db.execute("INSERT INTO usuarios_registrados (user_email, user_pass, user_power)"
               " VALUES (?, ?, ?)", new_email, new_hashed, user_power)
    history(f'usuario añadido: {user_power}', new_email)
    SUCCESS.append(
        f"Usuario añadido correctamente, recuerde enviar la contraseña temporal del nuevo usuario ({temp_pass}) a su correo ({new_email})")
    return redirect("/sesion_editor?status=exito"), 302


# this route allows signed in users that are admins
# to delete other users
@app.route("/user_del", methods=["POST"])
def user_del():

    # first we clean any error or success messages
    # that may have been stored in other routes
    # if any error is raise this route redirects to other
    # route and a error message is flashed in the new route

    ERROR.clear()
    SUCCESS.clear()

    # here we make sure a user email is submitted

    if not request.form.get("correo usuario"):
        ERROR.append("Debe ingresar el correo de algún usuario primero antes de eliminarlo")
        return redirect("/sesion_editor?status=error"), 302

    # checking that the user has not been already eliminated

    del_email = request.form.get("correo usuario")
    is_user = db.execute("SELECT user_email, user_power FROM usuarios_registrados WHERE user_email = ?", del_email)
    if len(is_user) == 0:
        ERROR.append("El correo que intenta eliminar ya se encuentra eliminado")
        return redirect("/sesion_editor?status=error"), 302

    # checking that there is always at least one admin left
    # before deleting an user

    num_adm = db.execute("SELECT user_email, user_power FROM usuarios_registrados WHERE user_power = 'admin'")
    val_adm = len(num_adm)
    for u in num_adm:
        if del_email in list(u.values()):
            if u["user_power"] == "admin":
                val_adm -= 1
            break
    if val_adm == 0:
        ERROR.append("No pueden quedar 0 administradores en el sistema si quiere dejar de ser administrador"
                     " primero debe asignar a otro editor como administrador, para hacerlo debe borrarlo del sistema"
                     " y luego volverlo a registrar como administrador")
        return redirect("/sesion_editor?status=error"), 302

    # an insert is made to the historial table to regist that 
    # someone deleted an user if an user deleted himself
    # the route redirects to the homepage and a success message is 
    # flashed otherwise the route redirects to the editing page
    # and a success message is flashed

    self_email = db.execute("SELECT user_email FROM usuarios_registrados WHERE user_id = ?", session["user_id"])
    history(f'usuario eliminado: {is_user[0]["user_power"]}', del_email)
    db.execute("DELETE FROM usuarios_registrados WHERE user_email = ?", del_email)
    if self_email[0]["user_email"] == del_email:
        session.clear()
        return redirect("/?status=Borrado"), 302
    else:
        SUCCESS.append("Usuario eliminado exitosamente")
        return redirect("/sesion_editor?status=exito"), 302
    