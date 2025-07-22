import json
import os
import re
import requests

### Funciones

## Funcion de buscar texto en variable issue_body
def search_text(name_input):
    descripcion = ""
    descripcion_match = re.search(fr"### {name_input}\s*(.*)", issue_body, re.DOTALL)
    if descripcion_match:
        descripcion = descripcion_match.group(1).strip()
        descripcion = descripcion.split("###")[0].strip()
    else: descripcion = None
    return descripcion
    
## Variables de entorno
issue_body = os.getenv("ISSUE_BODY", "Cuerpo no disponible")
new_label = os.getenv("NEW_LABEL", "Nuevo label no disponible")
azure_secret = os.getenv("AZURE_SECRET","Secreto no disponible")
description_label = os.getenv("DESCRIPTION_LABEL", "Descripcion no disponible")
url_azure_issue = os.getenv("URL_AZURE_ISSUE","URL no disponible")
azure_area_path_update = os.getenv("AZURE_AREA_PATH_UPDATE","Ruta no disponible")

## Variables locales
azure_id = search_text("Codigo Azure:")

### Cuerpos de Peticiones

##Cuerpo de Peticion de Issue en Azure
headers = {
    "Content-Type": "application/json-patch+json",
    "Authorization": f"Bearer {azure_secret}"
}

### Funciones de Peticiones
def updateTag(tag):
    body_add_tag = [
        {
            "op": "add",
            "path": "/fields/System.Tags",
            "value": f"{tag}"
        }
    ]
    resp = requests.patch(f"{url_azure_issue}{azure_id}?api-version=7.1-preview.3", json=body_add_tag, headers=headers)
    print(f"Actualizacion de Tag:{resp}")


def updateArea(route):
    body_update_area = [
        {
            "op": "replace",
            "path": "/fields/System.AreaPath",
            "value": f"{azure_area_path_update}{route}"
        }
    ]
    resp = requests.patch(f"{url_azure_issue}{azure_id}?api-version=7.1-preview.3", json=body_update_area, headers=headers)
    print(f"Actualizacion de Area:{resp}")

if new_label.find('team') != -1 :
    updateArea(description_label)
else:
    updateTag(new_label)
