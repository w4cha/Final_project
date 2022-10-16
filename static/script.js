// makes a request to the server to display the communes 
// inside a region when the name variable is region
// makes a request to the server to display the recycling
// materials accepted by a commune when the name variable is comuna

async function consulta(name) {
    const invalid_values = ["Región"];
    var input = document.getElementById(name).value;
    if (!input) {
        return;
    }
    if (invalid_values.includes(input)) {
        document.getElementById("contenido").style.display = "none";
        return;
    }
    document.getElementById("contenido").style.display = "inline";
    let x = await fetch("/request?" + name + "=" + input, { method: "POST" });
    let y = await x.text();
    if (x.ok) {
        document.getElementById(name + "_contenido").innerHTML = y;
        document.getElementById("materiales").innerHTML = "";
    } else {
        return;
    }
}

// check if any recycling materials where selected inside a commune
// and if at least 1 was selected then it makes a request to the server
// asking for the locations inside the commune that can receive at least one
// of the selected materials

async function material() {
    const checked_values = document.getElementsByClassName("form-check-input");
    var materials = "";
    if (!checked_values.length) {
        return;
    } else { 
        for (var j = 0; checked_values[j]; ++j) {
            if (checked_values[j].checked) {
                materials += checked_values[j].value + ".";
            }
        }
        if (materials.length > 1) {
            let x = await fetch("/request?material=" + materials, { method: "POST" });
            let y = await x.text();
            if (x.ok) {
                document.getElementById("materiales").innerHTML = y;
                if (y != "No hay resultados para la búsqueda") {
                    const disponible = ["Si"];
                    const ausente = ["No"];
                    for (const a of document.querySelectorAll("td")) {
                        if (disponible.includes(a.textContent)) {
                            a.style.backgroundColor = "#32cd32";
                        }
                        if (ausente.includes(a.textContent)) {
                            a.style.backgroundColor = "#dc143c";
                        }
                    }
                }
                return;
            } else {
                document.getElementById("materiales").innerHTML = "Ha habido un error en el sistema al procesar su consulta";
                return;
            }
        } else {
            document.getElementById("materiales").innerHTML = "Debe seleccionar primero al menos un tipo de residuo.";
            return;
        }
    
    } 
}

// gives a preview of which communes accept the current 
// recyclable material being selected in the switch checkbox

async function llamar(valor) {
    var comprovar = document.getElementById("comuna").value;
    if (comprovar != "Comuna") {
        var texto = "Elige una o más opciones que tu lugar de reciclaje debe poder procesar";
        document.getElementById("flavour-text").innerHTML = texto;
        return;
    }
    var material = document.querySelector("input[value='" + valor + "']");
    if (!material.checked) {
        return;
    }
    let x = await fetch("/request?consulta=" + material.value, { method: "POST" });
    let y = await x.text();
    if (x.ok) {
        document.getElementById("flavour-text").innerHTML = y;
        return;
    } else {
        return;
    }
}

// takes the location (value attribute) of the Ver en el mapa
// button and extract from it a latitude and a longitude value
// that is then check to make sure is a number and then use those
// numbers to change the url of the google maps iframe so it can then display
// the map of the current recycling point entry

function get_value(location, identity, numero) {
    give(numero);
    if (!location) {
        document.getElementById("gmap_canvas").src = 
            "https://maps.google.com/maps?q=-33.44867469085204%20-70.64996860614981&t=&z=11&ie=UTF8&iwloc=&output=embed";
        document.querySelector("div.modal").style.display = "grid";
        info("no");
        return;
    }
    const clean = location.trim().slice(7, -1);
    const limpio = clean.trim().split(" ").reverse();
    const len = limpio.length;
    if (len == 2) {
        if (isNaN(limpio[0]) || isNaN(limpio[1])) {
            document.getElementById("gmap_canvas").src = 
                "https://maps.google.com/maps?q=-33.44867469085204%20-70.64996860614981&t=&z=11&ie=UTF8&iwloc=&output=embed";
            document.querySelector("div.modal").style.display = "grid";
            info("no");
            return;
        } else {
            const nuevo = "https://maps.google.com/maps?q=" + limpio[0] + "%20" + limpio[1] + 
                "&t=&z=15&ie=UTF8&iwloc=&output=embed";
            document.getElementById("gmap_canvas").src = nuevo;
            info(identity);
            document.querySelector("div.modal").style.display = "grid";
            return;
        }
        
    } 
}

// makes possible to go up and down inside the map view of the table of results
// containing the locations of recycling points of a region or commune

function give(ver) {
    var top = document.getElementById("number-of-rows").getAttribute("name");
    if (top != 1) {
        document.getElementById("right").style.visibility = "visible";
        document.getElementById("left").style.visibility = "visible";
    }
    var down = parseInt(ver) - 1;
    var up = parseInt(ver) + 1;
    var safe = [];
    try {
        var above = document.getElementById(up).getAttribute("id");
        safe.push(above);
    } catch (error) {
        safe.push("no-up");
    }
    try {
        var below = document.getElementById(down).getAttribute("id");
        safe.push(below);
    } catch (error) {
        safe.push("no-down");
    }
    if (safe.includes("no-up") && safe.includes("no-down")) {
        document.getElementById("right").style.visibility = "hidden";
        document.getElementById("left").style.visibility = "hidden";
    } else if (safe.includes("no-up")) {
        document.getElementById("left").setAttribute("name", down);
        document.getElementById("right").setAttribute("name", 1);
    } else if (safe.includes("no-down")) {
        document.getElementById("left").setAttribute("name", top);
        document.getElementById("right").setAttribute("name", up);
    } else {
        document.getElementById("left").setAttribute("name", down);
        document.getElementById("right").setAttribute("name", up);
    }  
}

// sends a request to the server to get extra information
// about the recycling point to be displayed aside the map
// of the location

async function info(place) {
    if (place == "no") {
        document.getElementById("msg_content").innerText = "Mapa no disponible";
        return;
    } else {
        let x = await fetch("/request?info=" + place, { method: "POST" });
        let y = await x.text();
        if (x.ok) {
            document.getElementById("msg_content").innerHTML = y;
            return;
        } else {
            document.getElementById("msg_content").innerText = "Error al mostrar información";
            return;
        }
    }

}

// automatically select and deselect all the switch
// checkbox options

function limpia(que) {
    const lista = document.getElementsByClassName("form-check-input");
    if (que == "nada") {
        for (var w = 0; lista[w]; w++) {
            lista[w].checked = false;
        }
    } else {
        for (var w = 0; lista[w]; w++) {
            lista[w].checked = true;
        }
    }
    document.getElementById("flavour-text").innerHTML = "Elige una o más opciones que tu lugar de reciclaje debe poder procesar";
    return;
}

// opens up a pop up window containing images
// and information about the current selected
// recycling material while making it possible
// to navigate between them inside the window
// using a left and right button

function reveal(element) {
    var material = ["Vidrio", "Papel", "Cartoncillo", "Cartón", "Plástico", "Metal", 
        "Baterías", "Celulares", "Electrodomésticos", "Aceite", "Pilas", "Neumáticos"];
    if (material.includes(element)) {
        document.getElementById("texto-content").setAttribute("name", element);
        var position = document.getElementById("texto-content").getAttribute("name");
        const from_here = material.indexOf(position);
        const to_where = [from_here - 1, from_here + 1];
        if (to_where[0] == -1) {
            document.getElementById("left").setAttribute("title", material[11]);
            document.getElementById("right").setAttribute("title", material[to_where[1]]);
        } else if (to_where[1] == 12) {
            document.getElementById("right").setAttribute("title", material[0]);
            document.getElementById("left").setAttribute("title", material[to_where[0]]);
        } else {
            document.getElementById("left").setAttribute("title", material[to_where[0]]);
            document.getElementById("right").setAttribute("title", material[to_where[1]]);
        }
        get_text(element);
        var where = document.querySelector(".modal2");
        where.style.display = "grid";
        return;
    } else {
        return;
    }
}

// request the information and images about
// the current selected recycling material to the server

async function get_text(solid) {
    let x = await fetch("/request?SolidInfo=" + solid, { method: "POST" });
    let y = await x.text();
    let w = await fetch("/request?SolidImage=" + solid, { method: "POST" });
    let z = await w.text();
    document.getElementById("titulos").innerHTML = solid + ":";
    if (x.ok) {
        document.getElementById("parrafo").innerHTML = y;
    } else {
        document.getElementById("parrafo").innerHTML = "Error al mostrar la información";
    }
    if (w.ok) {
        document.getElementById("ejemplo_residuo").innerHTML = z;
    } else {
        document.getElementById("ejemplo_residuo").innerHTML = "<h5 style='color: white;'>Error al mostrar la imagen</h5>";
    }
    return;
}

// allows to copy the value of a button to the clipboard
// when the button is clicked

function clipboard_copy(element) {
    if (navigator && navigator.clipboard && navigator.clipboard.writeText) {
        window.location.href = "/?status=copia";
        return navigator.clipboard.writeText(element);
    } else {
        window.location.href = "/?error=" + element;
        return Promise.reject('The Clipboard API is not available.');
    }              
}

// allows to display the sub menu options available for
// a signed in admin or editor user

async function get_resource(what, trampa) {
    if (what == "default") {
        document.getElementById(trampa).innerHTML = "";
        return;
    }
    let x = await fetch("/member?request=" + what, { method: "POST" });
    let y = await x.text();
    if (x.ok) {
        document.getElementById(trampa).innerHTML = y;
    } else {
        document.getElementById(trampa).innerHTML = "Error al mostrar el elemento";
    }
    return;
}

// show the map and info of the next or previous entry in the table when
// the button left or right is clicked

function change(arg1) {
    var redirect = document.getElementById(arg1).getAttribute("name");
    var drive = document.getElementById(arg1).getAttribute("value");
    get_value(drive, redirect, arg1);
    return;
}

// request the entry information to the server
// when its identification number is enter

async function consultan(figure) {
    if (!figure) {
        document.getElementById("resultado").innerHTML = "Debe ingresar un número";
        return;
    }
    let x = await fetch("/request?entry-info=" + figure, { method: "POST" });
    let y = await x.text();
    if (x.ok) {
        document.getElementById("resultado").innerHTML = y;
        document.getElementById("punto-id").setAttribute("name", figure);
    } else {
        document.getElementById("resultado").innerHTML = "Identificador no válido";
    }
    return;
}

// show sub menu options when an user wants to
// change an entry specific value

async function optionview(color) {
    let no_valid = ["owner", "manager"];
    if (no_valid.includes(color)) {
        let x = await fetch("/morph?type=no-mater", { method: "POST" });
        let y = await x.text();
        if (x.ok) {
            document.getElementById("mater-or-person").innerHTML = y;
        } else {
            document.getElementById("mater-or-person").innerHTML = "Error al mostrar elemento";
        }
        return;
    } else if (color == "default") {
        document.getElementById("mater-or-person").innerHTML = "Debe seleccionar un campo válido para cambiar";
        return;
        
    } else {
        let x = await fetch("/morph?type=mater", { method: "POST" });
        let y = await x.text();
        if (x.ok) {
            document.getElementById("mater-or-person").innerHTML = y;
        } else {
            document.getElementById("mater-or-person").innerHTML = "Error al mostrar elemento";
        }
        return;
    } 

}