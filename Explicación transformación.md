# Transformaciones aplicadas a los datos bibliográficos
## Limpieza general
- Se eliminan registros que no tienen biblioteca asignada
- Se conservan solo los datos válidos y se guardan por separado los descartados
- Se eliminan espacios innecesarios y caracteres especiales

## Normalización de Lugares de publicación
- "Santafé de Bogotá" se convierte en "Bogotá"
- "México" se convierte en "Ciudad de México"
- "New York" se convierte en "Nueva York"
- "Köln" se convierte en "Colonia"


### Manejo de múltiples ciudades

Cuando un registro tiene múltiples ciudades separadas por comas, mantiene hasta 2 ciudades
Ejemplo: "Barcelona, Bogotá" → Devuelve ambas ciudades


### Limpieza del formato

- Elimina paréntesis y su contenido: "Madrid (España)" → "Madrid"
- Elimina espacios extra y caracteres especiales
- Elimina números y símbolos innecesarios

### Manejo de ubicaciones faltantes o poco claras

- Los valores vacíos se convierten en "Lugar no identificado"
- Los valores con "##" o marcadores poco claros similares se convierten en "Lugar no identificado"

### Preservación de nombres originales cuando corresponde

- Las ciudades que no necesitan estandarización mantienen sus nombres originales
- Los acentos y caracteres especiales se preservan cuando son correctos

## Normalización de Fechas de publicación
###  Extracción del año más reciente
- De un rango de años como "2019-2020", se toma el 2020
- Si hay varios años mencionados, se selecciona el más actual
### Limpieza de símbolos y marcadores especiales
- Se eliminan símbolos como ©, #, ;, []
- Se quitan palabras como "circa", "Aprox." o "c."
- Se remueven signos de interrogación y corchetes 
### Manejo de formatos diversos
- Identifica años escritos como secuencias de 4 dígitos
- Funciona con años sueltos como "2020"
- Procesa años con marcadores de copyright como "©2021"
### Casos especiales
- Cuando no se encuentra un año válido, se marca como no disponible
- Si la fecha está vacía, se indica que no hay información
- Elimina texto adicional manteniendo solo el año

## Nombres de autores
### Formato estándar "Apellido, Nombre"
- Mantiene el formato bibliográfico tradicional
- Asegura consistencia en todo el catálogo
- Ejemplo: "GARCÍA MÁRQUEZ, GABRIEL" → "García Márquez, Gabriel"
### Corrección de mayúsculas y minúsculas
- Primera letra en mayúscula para nombres y apellidos
- Respeta prefijos nobiliarios en minúscula
- Ejemplo: "browne, anthony" → "Browne, Anthony"
### Manejo de múltiples autores
- Separa autores usando punto y coma
- Normaliza cada autor individualmente
- Ejemplo: "Süskind, Patrick,; Gambolini, Gerardo" → "Süskind, Patrick; Gambolini, Gerardo"
### Limpieza de títulos y elementos adicionales
- Elimina títulos académicos (Dr., PhD., Mr., etc.)
- Quita puntuación extra y espacios innecesarios
- Ejemplo: "Dr. Cardona Marín, PhD., Guillermo" → "Cardona Marín, Guillermo"
### Casos especiales
- Autores desconocidos se marcan como "Desconocido"
- Preserva caracteres especiales y acentos correctos
- Mantiene prefijos como "von", "van", "de" en minúscula

## Títulos
### Limpieza básica del texto
- Elimina espacios innecesarios al inicio y final
- Quita números y punto y coma al principio del título
- Ejemplo: " El príncipe " → "El príncipe"
### Eliminación de elementos bibliográficos
- Remueve barras diagonales al final (/)
- Quita dos puntos y comas al final (:,)
- Ejemplo: "Prince of the elves /" → "Prince of the elves"
### Manejo de caracteres especiales
- Mantiene caracteres válidos como en "C++"
- Elimina símbolos innecesarios (#%&*{}[]^~)
- Preserva acrónimos y abreviaturas comunes
### Corrección de espacios y puntuación
- Ajusta espacios alrededor de signos de puntuación
- Elimina espacios múltiples
- Ejemplo: "Historia del arte :," → "Historia del arte"
### Casos especiales
- Títulos vacíos se marcan como "Sin título"
- Mantiene la integridad de títulos con caracteres especiales válidos
- Preserva mayúsculas y minúsculas según corresponda

# Modelado de Tópicos usando Embeddings

## Proceso General
1. Se utiliza el modelo de embeddings "jinaai/jina-embeddings-v3" para convertir texto a vectores
2. El modelo se carga en GPU si está disponible para mejor rendimiento
3. Se procesan tanto los términos del tesauro como los temas de los libros

## Tesauro y Jerarquía
- Se cargan términos del tesauro desde vocabulario.html
- Se extraen específicamente los términos de nivel 3 para mayor especificidad
- Se generan embeddings para cada término del tesauro

## Procesamiento de Temas
1. Normalización del texto:

- Eliminación de acentos
- Conversión a minúsculas
- Eliminación de texto entre paréntesis
- Remoción de frases comunes como "en la literatura"
2. Comparación vectorial:

- Se generan embeddings para los temas de los libros
- Se calcula similitud coseno entre temas y términos del tesauro
- Se selecciona el término más similar para cada tema


## Resultados
- Se añaden dos columnas al DataFrame:
    - tema_general: el término del tesauro más cercano
    - score_tema_general: el puntaje de similitud