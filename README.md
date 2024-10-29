# BibloClean: Pipeline ETL para Análisis Bibliográfico de MARC21

## Descripción General

**BibloClean** es un paquete Python diseñado para el procesamiento integral de datos bibliográficos, utilizando un pipeline ETL (Extracción, Transformación, Carga) para procesar registros MARC21 y normalizar la información extraída. Este paquete facilita la limpieza, normalización y análisis de datos bibliográficos, y es especialmente útil para bibliotecarios y gestores de información que manejan grandes volúmenes de registros MARC21.

### Características Principales

- **Extracción de datos**: Carga registros desde archivos CSV/Excel.
- **Preprocesamiento de texto**: Limpia y normaliza campos bibliográficos.
- **Generación de embeddings**: Crea representaciones vectoriales para análisis temático.
- **Normalización de entidades**: Detecta y normaliza autores, títulos y lugares.
- **Red de correlaciones temáticas**: Genera redes de conexiones entre temas basados en umbrales de similitud.
- **Exportación de resultados**: Guarda los datos procesados en un formato estructurado y exporta redes temáticas a formato GraphML.

### Limitaciones

- Los datos de entrada deben estar en formato CSV o Excel.
- Los pipelines están diseñados específicamente para datos bibliográficos MARC21.
- El rendimiento depende de la calidad de los modelos de embedding y el tamaño de los datos.
- La estructura de columnas en los datos de entrada debe cumplir con un formato específico.

## Prerrequisitos

### 1. Instalación

Para instalar el paquete y sus dependencias:

```bash
git clone https://github.com/complexluise/limpieza_marc21
cd limpieza_marc21
# Si tienes una GPU, instala PyTorch para mejor rendimiento en embeddings
pip3 install torch --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt
```

### 2. Estructura de Datos

Los datos de entrada deben seguir la estructura de campos MARC21 especificada en la documentación, como:

- **Campos de autor**: 100$a
- **Campos de título**: 245$a, 245$b
- **Campos temáticos**: 650$a
- **Campos de clasificación**: 082$a
- **Campos de biblioteca**: 943$a-g

El archivo CSV o Excel debe tener las siguientes columnas:

| 100$a             | 245$a                                   | 245$b                                         | 245$c             | 082$a | 082$b | 082$2 | 090$a | 090$b | 650$a                                       | 650$y | 650$v | 650$x              | 520$a                                                | 943$a     | 943$b | 943$c | 943$d | 943$e | 943$f | 943$g |
|-------------------|-----------------------------------------|-----------------------------------------------|-------------------|-------|-------|-------|-------|-------|---------------------------------------------|--------|--------|--------------------|-------------------------------------------------------|-----------|--------|--------|--------|--------|--------|--------|
| Nombre principal (autor) | Título principal                             | Subtítulo                                         | Mención de responsabilidad | Número de clasificación Dewey | Número adicional de clasificación | Edición de la clasificación Dewey | Clasificación local | Número de clasificación local adicional | Tema principal                                  | Periodo cronológico | Forma del término | Subdivisión temática   | Resumen | Biblioteca_1 | Biblioteca_2 | Biblioteca_3 | Biblioteca_6 | Biblioteca_5 | Biblioteca_4 | Biblioteca_7 |
| Goldberg, Beatriz | ¿Cómo voy a hacer esto a la edad que tengo?: | aprenda a enfrentar las crisis y los cambios a cualquier edad/ | Beatriz Goldberg | 155.25 |       | 20    |       |       | Autoestima;Autorrealización (Psicología);Tristeza |        |        | Aspectos psicologicos | FAJM                                                  |           |        |        |        |        |        |        |

### 3. Directorios del Proyecto

```plaintext
├── raw_data/           # Datos de entrada sin procesar
├── clean_data/         # Datos procesados y limpios
├── modelos/            # Modelos de embeddings guardados
└── bibloclean/         # Código fuente
└── analysis/           # Artefactos de salida de las redes temáticas
```

## Uso

### 1. Preparación de Datos

1. Colocar los archivos CSV/Excel en la carpeta `raw_data/`.
2. Verificar que las columnas coincidan con la estructura requerida.
3. Asegurar que los datos estén codificados en UTF-8.

### 2. Ejecución del Pipeline

Las funcionalidades principales están disponibles a través de una interfaz de línea de comandos (CLI) que permite realizar la limpieza y generación de redes temáticas.

#### Comandos Disponibles

1. **Limpieza de datos bibliográficos de KOHA**

   ```bash
   python bibloclean limpiar-koha archivo.csv --salida <directorio> --verbose
   ```

   - **archivo**: Ruta al archivo CSV/Excel a procesar.
   - **--salida, -s**: Directorio para guardar los resultados (por defecto: `clean_data`).
   - **--verbose, -v**: Muestra información detallada del proceso.

   Este comando procesa los datos, aplicando limpieza y normalización a los registros bibliográficos, y los guarda en el directorio de salida especificado.

2. **Generación de red de correlaciones temáticas**

   ```bash
   python bibloclean analizar-red archivo.csv --umbral <valor> --modelo <nombre_modelo> --salida <ruta_salida>
   ```

   - **archivo**: Archivo CSV con los temas asignados.
   - **--umbral, -u**: Umbral de similaridad para conexiones entre temas (rango de 0 a 1; por defecto: 0.7).
   - **--modelo, -m**: Nombre del modelo de embeddings disponible en [SentenceTransformers](https://www.sbert.net/docs/sentence_transformer/pretrained_models.html) a utilizar (por defecto: `jinaai/jina-embeddings-v3`).
   - **--salida, -s**: Ruta para guardar el archivo de la red en formato GraphML.

   Este comando genera una red temática que representa las relaciones entre temas en el archivo CSV, basada en un umbral de similitud y un modelo de embeddings.

### 3. Resultados

- Los datos procesados se guardan en `clean_data/` con los siguientes atributos mejorados:
  - Campos normalizados.
  - Análisis temático.
  - Estadísticas de procesamiento.
- La red de temas generada se guarda en el formato GraphML en la ubicación especificada por el usuario, ideal para visualización en herramientas de análisis de redes.

## Contribuciones

Agradecemos las contribuciones a **BibloClean**:

### Reportar Problemas

1. Revisar los issues existentes.
2. Crear un nuevo issue con una descripción detallada.
3. Incluir pasos para reproducir el problema.

### Realizar Mejoras

1. Hacer fork del repositorio.
2. Crear una rama para la nueva funcionalidad.
3. Seguir los estándares de código del proyecto.
4. Enviar un pull request.

### Proponer Cambios Mayores

1. Abrir un issue para discutir la propuesta.
2. Detallar la justificación e implementación.
3. Esperar retroalimentación antes de comenzar.

## Licencia

**BibloClean** está licenciado bajo Apache License Version 2.0.