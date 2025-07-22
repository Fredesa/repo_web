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
    else: descripcion = "No se genero"
    return descripcion

def extraer_id_final(url):
    patron = r'.*/(\d+)$'
    match = re.search(patron, url)
    return match.group(1) if match else None

## Variables de entorno
issue_body = os.getenv("ISSUE_BODY", "Cuerpo no disponible")
azure_secret = os.getenv("AZURE_SECRET","Secreto no disponible")
url_azure_issue = os.getenv("URL_AZURE_ISSUE","URL no disponible")
azure_area_path_update = os.getenv("AZURE_AREA_PATH_UPDATE","Ruta no disponible")
url_teams_triage = os.getenv("URL_TEAMS_TRIAGE","URL no disponible")
github_issue_url = os.getenv("GITHUB_ISSUE_URL","URL no disponible")
repo_name = os.getenv("REPO_NAME","Nombre no disponible")

## Variables locales
azure_id = search_text("Codigo Azure:")
github_id = extraer_id_final(github_issue_url)

### Cuerpos de Peticiones

##Cuerpo de Peticion de Issue en Azure
headers = {
    "Content-Type": "application/json-patch+json",
    "Authorization": f"Bearer {azure_secret}"
}

### Funciones de Peticiones
body_add_tag = [
    {
        "op": "replace",
        "path": "/fields/System.State",
        "value": f"Closed"
    }
]

resp = requests.patch(f"{url_azure_issue}{azure_id}?api-version=7.1-preview.3", json=body_add_tag, headers=headers)
print(f"Actualizacion de Estado:{resp}")

body_request_teams= {
    "type": "message",
    "attachments": [
        {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.2",
                "body": [
                  {
                      "type": "TextBlock",
                      "size": "medium",
                      "weight": "bolder",
                      "text": f"Hola compañeros de Soporte Mobile se ha cerrado el issue en azure: {azure_id} y github: {github_id} en el repositorio: {repo_name}",
                      "style": "heading",
                        "wrap": "true"
                  },
              ],
            }
        }
    ]
}

##Evento de generacion de issue en Teams
respTeams = requests.post(f"{url_teams_triage}", json=body_request_teams)
print(f"Notificacion a Teams:{respTeams}")
