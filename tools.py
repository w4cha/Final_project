

# clean the list of dictionaries returned by a sql query 
# of any duplicated results
def clean(r):
    seen = set()
    new_l = []
    for d in r:
        t = tuple(d.items())
        if t not in seen:
            seen.add(t)
            new_l.append(d)
    return new_l


# creates variable length sql queries that are
# returned as string to be executed
def format(elemento, commune, material_en, zone):
    try:
        if len(elemento) == 1:
            if commune[0] != "Comuna":
                query = (f'SELECT OBJECTID, the_geom, address_na, {material_en[elemento[0]]} FROM reciclaje WHERE '
                         f'status = "Open" AND region_id = "{zone[0]}" AND '
                         f'commune_id = "{commune[0]}" AND {material_en[elemento[0]]} = "Si"')
                return query
            else:
                query = (f'SELECT OBJECTID, the_geom, commune_id, address_na, {material_en[elemento[0]]} FROM reciclaje WHERE '
                         f'status = "Open" AND region_id = "{zone[0]}" AND {material_en[elemento[0]]} = "Si"')
                return query
        elif len(elemento) > 1:
            if commune[0] != "Comuna":
                orden = 'SELECT OBJECTID, the_geom, address_na, '
                reglas = f'WHERE status = "Open" AND region_id = "{zone[0]}" AND commune_id = "{commune[0]}" AND ('
            else:
                orden = 'SELECT OBJECTID, the_geom, commune_id, address_na, '
                reglas = f'WHERE status = "Open" AND region_id = "{zone[0]}" AND ('
            for i in elemento:
                if elemento.index(i) == len(elemento) - 1:
                    orden += f'{material_en[i]} FROM reciclaje '
                    reglas += f'{material_en[i]} = "Si")'
                else:
                    orden += f'{material_en[i]}, '
                    reglas += f'{material_en[i]} = "Si" OR '
            return orden+reglas
        else:
            return 'unexpected error'

    except IndexError:
        return 'unexpected error'


# get all the types of recyclable materials an entry supports
# and returns them as a list
def esta(msn, es_en):
    holder = []
    for itm in msn:
        if msn[itm] == "Si":
            if itm in es_en:
                holder.append(es_en[itm])
            else:
                return "db_error"
        else:
            pass
    return holder


# seeks items in a txt file to return the
# contents that are after that item but before
# the next item
def seek_info(texto_path, indice):
    seek = []
    mensaje = ""
    try:
        with open(texto_path, "r") as informaciones:
            for line in informaciones:
                if line.strip("\n") == indice:
                    seek.append(indice)
                elif line.strip("\n") == "$$" and len(seek) != 0:
                    break
                else:
                    if len(seek) != 0:
                        mensaje += line.strip("\n")
                    else:
                        pass
        return mensaje
    except FileNotFoundError:
        return mensaje

