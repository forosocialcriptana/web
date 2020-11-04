import pandas as pd
import os
import re
import shutil

def normaliza(cadena):
  nexos = [' a ', ' al ', ' ante ', ' antes ', ' asi ', ' aunque ', ' bajo ', ' bien ', ' cabe ', ' como ', ' con ', ' con ', ' contra ', ' cuando ', ' de ', ' del ', ' desde ', ' despues ', ' durante ', ' e ', ' el ', ' empero ', ' en ', ' entre ', ' esta ', ' hacia ', ' hasta ', ' la ', ' las ', ' los ', ' luego ', ' mas ', ' mediante ', ' muy ', ' ni ', ' o ', ' ora ', ' para ', ' pero ', ' por ', ' porque ', ' pues ', ' que ', ' se ', ' sea ', ' según ', ' si ', ' sin ', ' sino ', ' siquiera ', ' sobre ', ' tal ', ' toda ', ' tras ', ' u ', ' un ', ' una ', ' uno ', ' unos ', ' y ', ' ya ']
  signos = ['\\\'', '"', '“', '”', '(', ')', '/', ':', '.', ',', '¿', '?', '¡', '!', 'º', 'ª']
  cadena = cadena.lower()
  for i in signos: 
    cadena = cadena.replace(i,'')
  for i in nexos:
    cadena = cadena.replace(i,' ')
  return cadena.replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('ñ','n').replace(' ','-')

# Carga de secciones
dfsecciones = pd.read_csv("datos/secciones.csv", sep=";") 
dfsecciones = dfsecciones.fillna('')
secciones = dfsecciones[dfsecciones.statut=='publie'].reindex(columns=['id_rubrique', 'id_parent', 'titre', 'date_tmp', 'texte']).to_dict('records')
# Creación diccionario de secciones
secciones = {x['id_rubrique']:x for x in secciones}

# Carga de artículos
dfarticulos = pd.read_excel("datos/articulos.xlsx") 
dfarticulos = dfarticulos.fillna('')
articulos = dfarticulos[dfarticulos.statut=='publie'].reindex(columns=['id_article', 'id_rubrique', 'titre', 'soustitre', 'descriptif', 'texte', 'date']).to_dict('records')
# Creación diccionario de secciones
articulos = {x['id_article']:x for x in articulos}

# Carga de documentos
dfdocs = pd.read_excel("datos/documentos.xlsx") 
dfdocs = dfdocs.fillna('')
docs = dfdocs.reindex(columns=['id_document', 'titre', 'fichier', 'largeur', 'media']).to_dict('records')
# Creación diccionario de secciones
docs = {x['id_document']:x for x in docs}

# Cabecera de secciones
cabecera_sec = '''---
title: {titre}
summary: "{texte}"
# View (1 = List, 2 = Compact, 3 = Card, 4 = Citation)
view: 2
# Optional header image (relative to `static/media/` folder).
header:
  caption: ""
  image: ""
---

'''

# Recorrido de secciones y creación de estructura de directorios
# Diccionario con las rutas de las secciones indexado por el número de sección (id_rubrique)
rutas_secciones = {}
for clave in secciones.keys():
  dirs = []
  x = clave
  while x != 0:
    dirs.append(normaliza(secciones[x]['titre']))
    x = secciones[x]['id_parent']
  dirs.reverse()
  for i in range(len(dirs)):
    ruta = 'content/post'
    for j in range(i+1):
      ruta += '/' + dirs[j]
    if not os.path.isdir(ruta):
      # Creamos el directorio y el fichero índice.
      os.mkdir(ruta)
      print(ruta)
      f = open(ruta + '/_index.md', 'w')
      f.write(cabecera_sec.format(**secciones[clave]))
      f.write(secciones[clave]['texte'])
      f.close()
  rutas_secciones[clave] = 'content/post/' + '/'.join(dirs)


# Cabecera artículos
cabecera_art = """---
title: '{titre}'
subtitle: '{soustitre}'
summary: '{descriptif}'
tags: []
categories: []
asociacion: []
date: {date}
lastmod:
---

"""

for num, articulo in articulos.items():
  ruta = rutas_secciones[articulo['id_rubrique']] + '/' + normaliza(articulo['titre'])
  print(num, ruta)
  if not os.path.isdir(ruta):
    # Creamos el directorio del artículo
    os.mkdir(ruta)
    # Preparamos el texto
    texto = articulo['texte']
    # Reemplazamos guiones de listas numeradas y no numeradas
    texto = texto.replace('\n-#', '\n1. ').replace('\n--', '\n\n    -').replace('\n-', '\n\n- ')
    # Reemplazamos negrita y cursiva
    texto = texto.replace('{{', '**').replace('}}', '**').replace('{', '*').replace('}', '*')
    # Lista de imágenes
    images = re.findall(r'<img\d+.*>', texto)
    if images:
      # Creamos el directorio de las imágenes del artículo
      os.mkdir(ruta + '/img')
    for i in range(len(images)):
      image = images[i].replace('<', '').replace('>', '')
      num = int(image.split('|')[0][3:])
      if docs[num]['media'] == "image":
        if '|' in image:
          alineamiento = image.split('|')[1][:-1]
        else:
          alineamiento = ''
        typeimg = docs[num]['fichier'].split('/')[0]
        rutaimg = 'img/' + docs[num]['fichier'].split('/')[1]
        # Copiamos la imagen a la carpeta de imágenes del artículo
        if os.path.exists('IMG/' + docs[num]['fichier']):
          shutil.copy2('IMG/' + docs[num]['fichier'], ruta + '/' + rutaimg)
          # Creamos imagen principal
          if i == len(images)-1:
            if typeimg == 'png':
              shutil.copy2('IMG/' + docs[num]['fichier'], ruta + '/featured.png')
            elif typeimg == 'jpg':
              shutil.copy2('IMG/' + docs[num]['fichier'], ruta + '/featured.jpg')
            texto = texto.replace('<' + image + '>', '')
          else:
            if alineamiento and alineamiento != 'center':
              rutaimg += '#' + alineamiento
            # Reemplazamos cada ocurrencia de imagen por su ruta
            texto = texto.replace(image, 'img src="' + rutaimg + '" alt="' + docs[num]['titre'] + '" width="' + str(int(docs[num]['largeur'])) + '"')
    # Lista de enlaces
    enlaces = re.findall(r'\[.*->.*\]', texto)
    for enlace in enlaces:
      cadena = enlace.split('->')[0][1:]
      url = enlace.split('->')[1][:-1]
      if cadena:
        texto = texto.replace(enlace, '[' + cadena + '](' + url + ')')
      else: 
        texto = texto.replace(enlace, url)
    # Creamos el directorio y el fichero índice.
    f = open(ruta + '/index.md', 'w')
    f.write(cabecera_art.format(**articulo))
    f.write(texto)
    f.close()











