# Procesamiento de Datos Bibliográficos

Este proyecto contiene un conjunto de herramientas para procesar, limpiar y enriquecer datos bibliográficos provenientes de sistemas de gestión de bibliotecas como Koha en formato MARC21.

## Estructura del Proyecto

- `extraer_vocabulario.py`: Extrae y procesa la jerarquía de términos del tesauro desde un archivo HTML.
- `modelamiento_topicos.py`: Implementa el modelado de tópicos usando embeddings y similitud coseno.
- `limpiar_tablas.py`: Realiza la limpieza y normalización de los datos bibliográficos.

## Funcionalidades Principales

- Extracción de vocabulario controlado desde tesauro
- Normalización de:
  - Nombres de autores
  - Títulos
  - Lugares de publicación 
  - Fechas
- Modelado de tópicos usando embeddings
- Análisis de registros descartados
- Exportación de resultados procesados

## Requisitos

- Python 3.8+
- Pandas
- NumPy
- BeautifulSoup4
- Sentence Transformers
- PyTorch
- Scikit-learn

## Uso

1. Colocar los archivos de entrada en la carpeta `raw_data/`
2. Ejecutar el script principal:

```bash
python limpiar_tablas.py
```
3. Los resultados procesados se guardarán en clean_data/

## Estructura de Directorios
```
├── raw_data/           # Datos de entrada sin procesar
├── clean_data/         # Datos procesados y limpios
├── modelos/            # Modelos de embeddings guardados
└── src/                # Código fuente
```
## Flujo de Procesamiento
1. Carga de datos desde archivos CSV/Excel
2. Filtrado de registros válidos
3. Normalización de campos
4. Modelado de tópicos
5. Exportación de resultados

## Contribuciones
Para contribuir al proyecto:

1. Fork del repositorio
2. Crear rama para nuevas características
3. Enviar pull request