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
  
## Funcion que limpia el url para poder enviar la ruta del Issue
def limpiar_url(url):
    patron = r'^https://api\.github\.com/repos/'
    return re.sub(patron, '', url)
  
## Funcion que extrae el id del Issue de la ruta
def extraer_id_final(url):
    patron = r'.*/(\d+)$'
    match = re.search(patron, url)
    return match.group(1) if match else None
  
### Variables

## Variables de entorno
issue_title = os.getenv("ISSUE_TITLE", "Título no disponible")
issue_body = os.getenv("ISSUE_BODY", "Cuerpo no disponible")
issue_url = os.getenv("ISSUE_URL", "Direccion no disponible")
repo_name = os.getenv("REPO_NAME","Nombre no disponible")
github_secret = os.getenv("GITHUB_SECRET","Secreto no disponible")
azure_secret = os.getenv("AZURE_SECRET","Secreto no disponible")
url_azure_issue = os.getenv("URL_AZURE_ISSUE","URL no disponible")
url_teams_triage = os.getenv("URL_TEAMS_TRIAGE","URL no disponible")
azure_area_path_create = os.getenv("AZURE_AREA_PATH_CREATE","Ruta no disponible")
azure_route_message = os.getenv("AZURE_ROUTE_MESSAGE","Ruta no disponible")
azure_iteration_path = os.getenv("AZURE_ITERATION_PATH","Ruta no disponible")


## Variables locales
descripcion_issue = search_text("Describa el error")
replicar_issue= search_text("Como replicar el error")
validacion_canal= search_text("Si vas a contribuir la solucion al issue ingresa el nombre del programa")
nombre_del_componente = search_text("Nombre del componente") if search_text("Nombre del componente") != None else repo_name
version = search_text("Version del componente Galatea")
programa = search_text("Programa") if search_text("Programa") != None else search_text("EVC")
evidencias = search_text("Adjunte Evidencias")
clasificacion = "Web"
issue_route = limpiar_url(issue_url)

description_azure = f"""
    <strong>Descripcion:</strong>
    <br>{descripcion_issue} <br>
    <br>
    <strong>Como replicar el error:</strong>
    <br>{replicar_issue} <br>
    <br>
    <strong>Version:</strong>
    <br>{version} <br>
    <br>
    <strong>Evidencias:</strong>
    <br>{evidencias} <br>
    <br>
    <strong>Link:</strong>
    <br>https://github.com/{issue_route}
"""

criterios_azure = """
* Realizar un primer contacto con el usuario oportunamente</br>
* Solucionar el incidente mencionado en desarrollo.</br>
* Hacer las respectivas pruebas al componente.</br>
* Realizar PR en LTS y Trunk (Artifactory)</br>
* PR aceptado y versión disponibilizada.</br>
* Lanzar release para disponibilizar versión en S3.</br>
* Lanzar comunicado en grupo de Teams</br>
* Certificación del Issue: creación DoD creacion del test plan.</br>
* Documentar en Sharepoint, dejar registro en comentarios, cerrar el issue.</br>
* Documentar el issue de forma clara</br>
* Adjuntar evidencias de lo trabajado (si es posible pantallazos de parte del usuario)</br>
* Crear tareas descriptivas</br>
* Relacionar los:</br>
     - PRs</br>
     - Releases (si aplica)</br>
"""


### Cuerpos de Peticiones

def generacion_issue():
    ##Cuerpo de Peticion de Issue en Azure
    headers = {
        "Content-Type": "application/json-patch+json",
        "Authorization": f"Bearer {azure_secret}"
    }
    body_request= [
        {
            "op": "add",
            "path": "/fields/System.AreaPath",
            "value": f"{azure_area_path_create}"
        },
        {
            "op": "add",
            "path": "/fields/System.IterationPath",
            "value": f"{azure_iteration_path}"
        },
        {
            "op": "add",
            "path": "/fields/System.Title",
            "value": f"[{clasificacion}]({nombre_del_componente}): {issue_title}"
        },
        {
            "op": "add",
            "path": "/fields/System.Description",
            "value": f"{description_azure}"
        },
        {
            "op": "add",
            "path": "/fields/Microsoft.VSTS.Common.AcceptanceCriteria",
            "value": f"{criterios_azure}"
        },
        {
            "op": "add",
            "path": "/fields/System.Tags",
            "value": f"{clasificacion}; {programa}"
        },
        {
            "op": "add",
            "path": "/relations/-",
            "value": {
            "rel": "System.LinkTypes.Hierarchy-Reverse",
            "url": f"https://dev.azure.com/GrupoBancolombia/Vicepresidencia%20Servicios%20de%20Tecnología/_apis/wit/workitems/6450785",
            "attributes": {
                "comment": "Estableciendo el work item padre"
                }
            }
        },
    ]
    ### Peticiones
    ##Evento de generacion de issue en Azure
    resp = requests.post(f"{url_azure_issue}$issue?api-version=7.1-preview.3", json=body_request, headers=headers)
    resp_string = json.loads(resp.content)
    codigo_azure = resp_string['id']
    return codigo_azure

def actualizacion_issue_github(codigo_azure):
    ## Generacion de texto para que se añada en github
    codigo_azure_github = {
        "body": f"{issue_body}\n### Codigo Azure:\n{codigo_azure}"
    }

    headers_github = {
        "Authorization": f"Bearer {github_secret}",
        "Accept": "application/vnd.github+json"
    }
    ##Evento de actualizacion de datos en Github
    requests.patch(f"{issue_url}",headers= headers_github, json=codigo_azure_github)
    
def generacion_mensaje_teams_issue(codigo_azure):

    ##Cuerpo de Peticion de mensaje en teams
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
                        "text": "Hola compañeros de Soporte Mobile",
                        "style": "heading",
                            "wrap": "true"
                    },
                    {
                            "type": "FactSet",
                            "facts": [
                                {
                                    "title": "Titulo del caso: ",
                                    "value": f"{issue_title}"
                                },
                                {
                                    "title": "Nombre de componente: ",
                                    "value": f"{nombre_del_componente}"
                                },
                                {
                                    "title": "Programa/EVC: ",
                                    "value": f"{programa}"
                                },
                                {
                                    "title": "Version: ",
                                    "value": f"{version}"
                                },
                                {
                                    "title": "Vinculo de azure: ",
                                    "value": f"{azure_route_message}{codigo_azure}"
                                },
                                {
                                    "title": "Vinculo de Github: ",
                                    "value": f"https://github.com/{issue_route}"
                                }
                            ]
                        },
                ],
                }
            }
        ]
    }
    requests.post(f"{url_teams_triage}", json=body_request_teams)

def generacion_mensaje_teams_contribucion():

    ##Cuerpo de Peticion de mensaje en teams
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
                        "text": f"Hola compañeros de Soporte Web el issue {issue_route} sera contribuido por el canal {validacion_canal}",
                        "style": "heading",
                            "wrap": "true"
                    },
                ],
                }
            }
        ]
    }
    requests.post(f"{url_teams_triage}", json=body_request_teams)

### Ejecucion de funciones
if validacion_canal == "_No response_":
    codigo_azure = generacion_issue()
    actualizacion_issue_github(codigo_azure)
    generacion_mensaje_teams_issue(codigo_azure)
else:
    generacion_mensaje_teams_contribucion()
    
