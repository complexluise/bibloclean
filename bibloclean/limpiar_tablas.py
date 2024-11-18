import logging
import pandas as pd
import numpy as np
import re
from pathlib import Path
from typing import List, Dict, Union, Tuple
from dataclasses import dataclass

from bibloclean.modelamiento_topicos import ProcesadorMateriasEmbeddings
from bibloclean.extraer_vocabulario import extraer_vocabulario


@dataclass
class DatasetPartition:
    """
    Clase para almacenar las diferentes particiones de los datos
    """

    registros_validos: pd.DataFrame
    registros_descartados: pd.DataFrame


class BibliotecaDataProcessor:
    """
    Clase para procesar y limpiar datos de bibliotecas desde archivos Excel.
    """

    def __init__(self, ruta_archivo: str):
        """
        Inicializa el procesador con la ruta del archivo Excel.

        Args:
            ruta_archivo (str): Ruta al archivo Excel que contiene los datos
        """
        self.ruta_archivo = Path(ruta_archivo)
        self.datos = None
        self.datos_descartados = None
        self.columnas_esperadas = {
            "bibliotecas": [
                "Biblioteca_1",
                "Biblioteca_2",
                "Biblioteca_3",
                "Biblioteca_4",
                "Biblioteca_5",
                "Biblioteca_6",
                "Biblioteca_7",
            ],
            "lugar": "Lugar de publicación",
            "fecha": "Fecha de publicación",
            "temas": "Tema principal",
            "autor": "Nombre principal (autor)",
            "titulo": "Título principal",
            "dewey": "Número de clasificación Dewey",
            "periodo": "Periodo cronológico",
            "editorial": "Editorial",
        }

    def obtener_columnas_disponibles(self) -> Dict[str, List[str]]:
        """
        Identifica qué columnas del esquema esperado están disponibles en el dataset.

        Returns:
            Dict[str, List[str]]: Diccionario con las columnas disponibles por categoría
        """
        if self.datos is None:
            raise ValueError("Primero debe cargar los datos usando cargar_datos()")

        columnas_disponibles = {
            "bibliotecas": [
                col
                for col in self.columnas_esperadas["bibliotecas"]
                if col in self.datos.columns
            ],
            "lugar": (
                self.columnas_esperadas["lugar"]
                if self.columnas_esperadas["lugar"] in self.datos.columns
                else None
            ),
            "fecha": (
                self.columnas_esperadas["fecha"]
                if self.columnas_esperadas["fecha"] in self.datos.columns
                else None
            ),
            "temas": (
                self.columnas_esperadas["temas"]
                if self.columnas_esperadas["temas"] in self.datos.columns
                else None
            ),
            "autor": (
                self.columnas_esperadas["autor"]
                if self.columnas_esperadas["autor"] in self.datos.columns
                else None
            ),
            "titulo": (
                self.columnas_esperadas["titulo"]
                if self.columnas_esperadas["titulo"] in self.datos.columns
                else None
            ),
            "dewey": (
                self.columnas_esperadas["dewey"]
                if self.columnas_esperadas["dewey"] in self.datos.columns
                else None
            ),
            "periodo": (
                self.columnas_esperadas["periodo"]
                if self.columnas_esperadas["periodo"] in self.datos.columns
                else None
            ),
            "editorial": (
                self.columnas_esperadas["editorial"]
                if self.columnas_esperadas["editorial"] in self.datos.columns
                else None
            ),
        }
        return columnas_disponibles

    def cargar_datos(self, fila_encabezado: int = 1) -> pd.DataFrame:
        """
        Carga los datos del archivo Excel o CSV.

        Args:
            fila_encabezado (int): Número de fila que contiene los encabezados

        Returns:
            pd.DataFrame: DataFrame con los datos cargados
        """
        logging.info("Cargando datos del archivo")

        extension = self.ruta_archivo.parts[-1]

        if extension.endswith(".csv"):
            self.datos = pd.read_csv(self.ruta_archivo, header=fila_encabezado)
            file_type = "CSV"
        elif extension.endswith((".xlsx", ".xls")):
            self.datos = pd.read_excel(self.ruta_archivo, header=fila_encabezado)
            file_type = "Excel"
        else:
            raise ValueError("El archivo debe ser CSV o Excel (.xlsx, .xls)")

        logging.info(
            f"Archivo {file_type} cargado exitosamente. Filas: {len(self.datos)}, Columnas: {len(self.datos.columns)}"
        )
        return self.datos

    def filtrar_registros_con_biblioteca(self) -> DatasetPartition:
        """
        Filtra los registros que tienen al menos una biblioteca asociada y
        guarda los registros descartados.

        Returns:
            DatasetPartition: Objeto conteniendo ambos conjuntos de datos
        """
        if self.datos is None:
            raise ValueError("Primero debe cargar los datos usando cargar_datos()")

        logging.info("Filtrando registros con al menos una biblioteca")
        columnas_biblioteca = self.obtener_columnas_disponibles()["bibliotecas"]

        if not columnas_biblioteca:
            print("Advertencia: No se encontraron columnas de biblioteca en el dataset")
            return DatasetPartition(self.datos.copy(), pd.DataFrame())

        # Crear máscara para registros con al menos una biblioteca
        mascara_biblioteca = self.datos[columnas_biblioteca].notnull().any(axis=1)

        # Separar registros válidos y descartados
        registros_validos = self.datos[mascara_biblioteca].copy()
        registros_descartados = self.datos[~mascara_biblioteca].copy()

        # Actualizar el DataFrame principal y guardar los descartados
        self.datos = registros_validos
        self.datos_descartados = registros_descartados

        logging.info(
            f"Registros válidos: {len(registros_validos)}, "
            f"Registros descartados: {len(registros_descartados)}"
        )
        return DatasetPartition(registros_validos, registros_descartados)

    @staticmethod
    def _normalizar_lugar_publicacion(valor: Union[str, float]) -> Tuple[str, str]:
        """
        Normaliza el lugar de publicación aplicando reglas específicas.
        Retorna una tupla con hasta dos ciudades.

        Args:
            valor: Valor a normalizar

        Returns:
            Tuple[str, str]: Tupla con dos ciudades (segunda ciudad vacía si solo hay una)
        """
        if pd.isnull(valor):
            return "Lugar no identificado", ""

        valor = str(valor).strip()
        # Limpieza básica
        valor = (
            valor.replace(";", ",")
            .replace(":", "")
            .replace("[", "")
            .replace("]", "")
            .replace("©", "")
        )

        # Eliminar espacios múltiples y contenido entre paréntesis
        valor = re.sub(r"\s*\([^)]*\)", "", valor)
        valor = " ".join(valor.split())

        # Diccionario de normalizaciones de ciudades
        normalizaciones_ciudades = {
            "Santafé de Bogotá": "Bogotá",
            "Bogota": "Bogotá",
            "Cartagena de Indias": "Cartagena",
            "México": "Ciudad de México",
            "Mexico": "Ciudad de México",
            "Ciudad de Ciudad de México": "Ciudad de México",
            "Köln": "Colonia",
            "Koln": "Colonia",
            "Salmanca": "Salamanca",
            "New York": "Nueva York",
        }

        # Separar ciudades por coma
        ciudades = [ciudad.strip() for ciudad in valor.split(",")]

        # Normalizar cada ciudad
        ciudades_normalizadas = []
        for ciudad in ciudades[:2]:  # Tomar solo las dos primeras ciudades
            ciudad_norm = ciudad
            for ciudad_original, ciudad_normalizada in normalizaciones_ciudades.items():
                if ciudad_original in ciudad:
                    ciudad_norm = ciudad.replace(ciudad_original, ciudad_normalizada)

            # Limpiar números y caracteres especiales
            ciudad_norm = "".join([c for c in ciudad_norm if not c.isdigit()]).strip()

            # Verificar si es lugar no identificado
            if any(
                phrase in ciudad_norm.lower() for phrase in ["no identificado", "##"]
            ) or ciudad_norm.startswith("#"):
                ciudad_norm = "Lugar no identificado"

            ciudades_normalizadas.append(ciudad_norm)

        # Asegurar que siempre retornemos una tupla de dos elementos
        if len(ciudades_normalizadas) == 0 or ciudades_normalizadas[0] == "":
            return "Lugar no identificado", ""
        elif len(ciudades_normalizadas) == 1:
            return ciudades_normalizadas[0], ""
        else:
            return ciudades_normalizadas[0], ciudades_normalizadas[1]

    @staticmethod
    def _normalizar_fecha_publicacion(fecha: Union[str, float]) -> Union[str, float]:
        """
        Normaliza la fecha de publicación extrayendo el año más reciente.

        Args:
            fecha: Valor de fecha a normalizar

        Returns:
            Union[str, float]: Año normalizado o np.nan si no se encuentra
        """
        if pd.isna(fecha):
            return np.nan

        fecha = str(fecha)
        # Limpieza de caracteres especiales
        fecha = re.sub(r"[;#©\\]", "", fecha)
        fecha = re.sub(r"[\[\]\?]", "", fecha)
        fecha = re.sub(r"c|circa|Ariel|Aprox\.?", "", fecha, flags=re.IGNORECASE)
        fecha = fecha.rstrip(".")

        # Extraer años (secuencias de 4 dígitos)
        años_encontrados = re.findall(r"\b\d{4}\b", fecha)

        return max(años_encontrados) if años_encontrados else np.nan

    def _normalizar_nombre_autor(self, autor: str) -> str:
        """
        Normaliza nombres de autores siguiendo estándares bibliográficos.

        Esta función aplica las siguientes transformaciones:
            1. Estandariza el formato "Apellido, Nombre"
            2. Corrige mayúsculas y minúsculas
            3. Maneja prefijos nobiliarios (von, van, de)
            4. Procesa múltiples autores
            5. Elimina títulos académicos y puntuación extra

        Args:
            autor (str): Nombre del autor a normalizar

        Returns:
            str: Nombre del autor normalizado

        Examples:
            >>> _normalizar_nombre_autor("GARCÍA MÁRQUEZ, GABRIEL")
            "García Márquez, Gabriel"
            >>> _normalizar_nombre_autor("von Goethe, Johann")
            "von Goethe, Johann"
        """
        if pd.isna(autor) or not autor or autor.strip() == "":
            return "Desconocido"

        autor = autor.strip().rstrip(".,")

        if ";" in autor:
            autores = [
                self._normalizar_nombre_autor(a.strip()) for a in autor.split(";")
            ]
            return "; ".join(autores)

        for titulo in ["Dr.", "PhD.", "Ph.D.", "Mr.", "Mrs.", "Ms."]:
            autor = autor.replace(titulo, "")

        partes = [p.strip() for p in autor.split(",") if p.strip()]
        autor = (
            f"{partes[0].title()}, {partes[1].title()}"
            if len(partes) >= 2
            else partes[0].title()
        )

        for prefijo in ["Von", "Van", "De", "Del", "La", "Las", "Los"]:
            autor = autor.replace(f" {prefijo} ", f" {prefijo.lower()} ")
            if autor.startswith(f"{prefijo} "):
                autor = f"{prefijo.lower()}{autor[len(prefijo):]}"

        return " ".join(autor.split())

    @staticmethod
    def _normalizar_titulo(titulo: str) -> str:
        """
        Normaliza títulos siguiendo estándares bibliográficos.

        Esta función aplica las siguientes transformaciones:
            1. Elimina espacios al inicio y final
            2. Corrige espacios alrededor de signos de puntuación
            3. Elimina barras diagonales al final
            4. Reemplaza comas incorrectas
            5. Elimina puntuación redundante
            6. Maneja indicadores de subtítulos
            7. Corrige mayúsculas y minúsculas
            8. Elimina caracteres inválidos

        Args:
            titulo (str): Título a normalizar

        Returns:
            str: Título normalizado

        Examples:
            >>> _normalizar_titulo(" El príncipe /")
            "El Príncipe"
            >>> _normalizar_titulo("Historia del arte :,")
            "Historia del Arte"
        """
        if pd.isna(titulo) or not titulo or titulo.strip() == "":
            return "Sin título"

        # Eliminar espacios extras y caracteres especiales
        titulo = titulo.strip()

        # Eliminar números y punto y coma al inicio
        titulo = re.sub(r"^[\d;]+", "", titulo)

        # Eliminar puntuación redundante al final
        titulo = re.sub(r"[/,:\s]+$", "", titulo)

        # Eliminar caracteres inválidos manteniendo algunos especiales
        titulo = re.sub(r"[#%&\*\{\}\[\]\^\~]", "", titulo)

        # Corregir espacios alrededor de puntuación
        titulo = re.sub(r"\s+([/,:;.])", r"\1", titulo)
        titulo = re.sub(r"([/,:;.])\s+", r"\1 ", titulo)

        # Eliminar espacios múltiples
        titulo = " ".join(titulo.split())

        # Preservar acrónimos y abreviaturas comunes
        titulo_limpio = re.sub(r"\b([A-Z])(\+\+)\b", r"\1\2", titulo)

        return titulo_limpio

    @staticmethod
    def _normalizar_periodo(periodo):
        """
        Normaliza un texto de periodo cronológico a número romano del siglo.

        Args:
            periodo (str): Texto del periodo cronológico

        Returns:
            str: Siglo en números romanos o None si no se puede normalizar
        """
        if not isinstance(periodo, str) or not periodo:
            return None

        def año_a_siglo_romano(año):
            """Convierte un año a su siglo en números romanos"""
            siglo = (año - 1) // 100 + 1
            # Convertir a romano usando biblioteca estándar
            valores = [
                (1000, "M"),
                (900, "CM"),
                (500, "D"),
                (400, "CD"),
                (100, "C"),
                (90, "XC"),
                (50, "L"),
                (40, "XL"),
                (10, "X"),
                (9, "IX"),
                (5, "V"),
                (4, "IV"),
                (1, "I"),
            ]
            resultado = ""
            for valor, numeral in valores:
                while siglo >= valor:
                    resultado += numeral
                    siglo -= valor
            return resultado

        def valor_siglo_romano(siglo_romano):
            """Convierte un siglo romano a su valor numérico"""
            valores = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
            valor = 0
            prev_valor = 0

            for char in reversed(siglo_romano.upper()):
                curr_valor = valores[char]
                if curr_valor >= prev_valor:
                    valor += curr_valor
                else:
                    valor -= curr_valor
                prev_valor = curr_valor
            return valor

        # Limpiar el texto
        periodo = periodo.lower().strip()
        periodo = re.sub(r"\s+", " ", periodo)

        # Buscar todos los años en el texto
        años = re.findall(r"\d{4}", periodo)
        if años:
            año_mas_reciente = max(map(int, años))
            return año_a_siglo_romano(año_mas_reciente)

        # Buscar todos los siglos romanos
        patron_siglos = r"(?:siglos?\s*|-)(xxi|xx|xix|xviii|xvii|xvi|xv|xiv|xiii|xii|xi|x|ix|viii|vii|vi|v|iv|iii|ii|i)"
        siglos_encontrados = re.findall(patron_siglos, periodo)

        if siglos_encontrados:
            return max(siglos_encontrados, key=valor_siglo_romano).upper()

        return None

    @staticmethod
    def _normalizar_numero_clasificacion_dewey(raw_dewey_number: str) -> str:
        """
        Normaliza el número de clasificación Dewey extrayendo los primeros tres dígitos y
        mapeándolo a la clase centena correspondiente.

        Parámetros:
        - raw_dewey_number (str): El número Dewey a normalizar.

        Retorna:
        - str: La clase centena Dewey correspondiente (ej: "100", "200", etc.),
               "R" para números de referencia, o cadena vacía para entradas inválidas.
        """
        if not raw_dewey_number:
            return ""

        match = re.search(r'(?:^R\s*)?(\d+)', re.sub(r'[^\dR]', '', raw_dewey_number))  # Extrae números y preserva R inicial
        if not match:
            return ""

        # Si comienza con R, retorna R independiente de los números que sigan
        if raw_dewey_number.strip().startswith('R'):
            return "R"

        number = match.group(1)

        if len(number) < 3 or number[0] == '0':
            return "0"

        return f"{number[0]}00"

    @staticmethod
    def _normalizar_editorial(editorial: str) -> Tuple[str, str]:
        """
        Normaliza el nombre de la editorial.

        Args:
            editorial (str): Nombre de la editorial a normalizar

        Returns:
            tuple: (editorial_principal, editorial_secundaria)
        """
        if pd.isna(editorial) or editorial == "" or editorial == "##":
            return "Editorial no identificada", ""

        # Limpieza inicial del texto
        editorial = str(editorial).strip()

        # Remover paréntesis y su contenido
        editorial = re.sub(r"\s*\([^)]*\)", "", editorial)

        # Normalizar separadores
        editorial = editorial.replace(",;", ";").replace(",", ";")

        # Dividir por punto y coma o coma
        editoriales = [e.strip() for e in editorial.split(";") if e.strip()]

        # Capitalizar primera letra de cada palabra
        normalize = lambda x: " ".join(
            w if w.isupper() else w.capitalize() for w in x.split()
        )
        editoriales = [normalize(e.strip(".")) for e in editoriales]

        # Si no hay editoriales después de la limpieza
        if not editoriales:
            return "Editorial no identificada", ""

        # Si solo hay una editorial
        if len(editoriales) == 1:
            return editoriales[0], ""

        # Si hay dos o más editoriales, tomar las dos primeras
        return editoriales[0], editoriales[1]

    def transformar_datos(self) -> pd.DataFrame:
        """
        Aplica todas las transformaciones necesarias al DataFrame según las columnas disponibles.
        """
        if self.datos is None:
            raise ValueError("Primero debe cargar los datos usando cargar_datos()")

        logging.info("Iniciando transformación de datos")

        columnas_disponibles = self.obtener_columnas_disponibles()

        # Add author normalization
        if columnas_disponibles["autor"]:
            logging.info(
                f"Normalizando nombres de autores: {columnas_disponibles['autor']}"
            )
            self.datos[columnas_disponibles["autor"] + " normalizado"] = self.datos[
                columnas_disponibles["autor"]
            ].apply(self._normalizar_nombre_autor)

        # Add title normalization
        if columnas_disponibles["titulo"]:
            logging.info(f"Normalizando títulos: {columnas_disponibles['titulo']}")
            self.datos[columnas_disponibles["titulo"] + " normalizado"] = self.datos[
                columnas_disponibles["titulo"]
            ].apply(self._normalizar_titulo)

        # Add lugar normalization
        if columnas_disponibles["lugar"]:
            logging.info(
                f"Normalizando columna de lugar: {columnas_disponibles['lugar']}"
            )
            editorial_normalizados = self.datos[columnas_disponibles["lugar"]].apply(
                self._normalizar_lugar_publicacion
            )
            self.datos[columnas_disponibles["lugar"] + " ciudad 1 normalizado"] = (
                editorial_normalizados.str[0]
            )
            self.datos[columnas_disponibles["lugar"] + " ciudad 2 normalizado"] = (
                editorial_normalizados.str[1]
            )

        if columnas_disponibles["fecha"]:
            logging.info(
                f"Normalizando columna de fecha: {columnas_disponibles['fecha']}"
            )
            self.datos[columnas_disponibles["fecha"] + " normalizado"] = self.datos[
                columnas_disponibles["fecha"]
            ].apply(self._normalizar_fecha_publicacion)

        if columnas_disponibles["dewey"]:
            logging.info(
                f"Normalizando columna de número de clasificación Dewey: {columnas_disponibles['dewey']}"
            )
            self.datos[columnas_disponibles["dewey"] + " normalizado"] = self.datos[
                columnas_disponibles["dewey"]
            ].apply(self._normalizar_numero_clasificacion_dewey)

        if columnas_disponibles["periodo"]:
            logging.info(
                f"Normalizando columna de periodo cronologico: {columnas_disponibles['periodo']}"
            )
            self.datos[columnas_disponibles["periodo"] + " normalizado"] = self.datos[
                columnas_disponibles["periodo"]
            ].apply(self._normalizar_periodo)

        if columnas_disponibles["editorial"]:
            logging.info(
                f"Normalizando columna de editorial: {columnas_disponibles['editorial']}"
            )
            editorial_normalizados = self.datos[
                columnas_disponibles["editorial"]
            ].apply(self._normalizar_editorial)
            self.datos[columnas_disponibles["editorial"] + " 1 normalizado"] = (
                editorial_normalizados.str[0]
            )
            self.datos[columnas_disponibles["editorial"] + " 2 normalizado"] = (
                editorial_normalizados.str[1]
            )

        if columnas_disponibles["temas"]:
            logging.info(f"Modelando temas en columna: {columnas_disponibles['temas']}")
            self.datos = self._modelar_topicos(columnas_disponibles["temas"])

        return self.datos

    def _modelar_topicos(self, columna_tema: str = "Tema principal") -> pd.DataFrame:
        """
        Realiza el modelado de tópicos en la columna especificada.

        Args:
            columna_tema (str): Nombre de la columna que contiene los temas principales.

        Returns:
            pd.DataFrame: DataFrame con los temas modelados y enriquecidos.
        """
        if columna_tema not in self.datos.columns:
            raise ValueError(f"La columna '{columna_tema}' no existe en el DataFrame.")

        # Cargar el tesauro
        with open("./raw_data/vocabulario.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        tesauro = extraer_vocabulario(html_content)

        # Inicializar el procesador de materias
        procesador = ProcesadorMateriasEmbeddings(tesauro)

        # Procesar el DataFrame
        df_procesado = procesador.procesar_dataframe(self.datos)

        # Actualizar el DataFrame principal
        self.datos = df_procesado

        return self.datos

    def guardar_resultados(self, directorio_salida: str) -> None:
        """
        Guarda tanto los resultados procesados como los registros descartados.

        Args:
            directorio_salida (str): Directorio donde se guardarán los archivos
        """
        if self.datos is None:
            raise ValueError("No hay datos para guardar")

        logging.info(f"Guardando resultados en: {directorio_salida}")

        directorio = Path(directorio_salida)
        directorio.mkdir(parents=True, exist_ok=True)

        # Obtener el nombre del archivo original sin extensión
        nombre_archivo_original = self.ruta_archivo.stem

        # Crear el nuevo nombre de archivo con el sufijo "_procesado"
        nombre_archivo_procesado = f"{nombre_archivo_original}_procesado.csv"

        # Guardar registros procesados
        ruta_procesados = directorio / nombre_archivo_procesado
        self.datos.to_csv(ruta_procesados, index=False)
        logging.info(f"Registros procesados guardados en: {ruta_procesados}")

        # Guardar registros descartados si existen
        if self.datos_descartados is not None and not self.datos_descartados.empty:
            nombre_archivo_descartados = f"{nombre_archivo_original}_descartados.csv"
            ruta_descartados = directorio / nombre_archivo_descartados
            self.datos_descartados.to_csv(ruta_descartados, index=False)
            logging.info(f"Registros descartados guardados en: {ruta_descartados}")

    def analizar_registros_descartados(self) -> Dict:
        """
        Analiza los registros descartados para identificar patrones y posibles reglas
        de transformación adicionales.

        Returns:
            Dict: Estadísticas y patrones encontrados en los registros descartados
        """
        logging.info("Analizando registros descartados")

        if self.datos_descartados is None or self.datos_descartados.empty:
            return {"mensaje": "No hay registros descartados para analizar"}

        analisis = {
            "total_registros": len(self.datos_descartados),
            "columnas_vacias": {},
            "valores_unicos": {},
            "patrones_fecha": set(),
            "patrones_lugar": set(),
        }

        # Analizar columnas vacías
        for col in self.datos_descartados.columns:
            pct_nulos = (
                self.datos_descartados[col].isna().sum() / len(self.datos_descartados)
            ) * 100
            analisis["columnas_vacias"][col] = f"{pct_nulos:.2f}%"

        # Analizar valores únicos en columnas relevantes
        columnas_disponibles = self.obtener_columnas_disponibles()

        if columnas_disponibles["lugar"]:
            lugares_unicos = (
                self.datos_descartados[columnas_disponibles["lugar"]].dropna().unique()
            )
            analisis["valores_unicos"]["lugares"] = list(lugares_unicos)

        if columnas_disponibles["fecha"]:
            fechas_unicas = (
                self.datos_descartados[columnas_disponibles["fecha"]].dropna().unique()
            )
            analisis["valores_unicos"]["fechas"] = list(fechas_unicas)

        logging.info(
            f"Análisis de registros descartados completado. "
            f"Total de registros descartados: {analisis['total_registros']}"
        )
        return analisis


def main(ruta_entrada):
    # Set up logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Configuración de rutas
    directorio_salida = "clean_data"

    logging.info(f"Iniciando procesamiento del archivo: {ruta_entrada}")

    # Inicializar procesador
    procesador = BibliotecaDataProcessor(ruta_entrada)

    # Ejecutar pipeline de procesamiento
    procesador.cargar_datos()
    procesador.filtrar_registros_con_biblioteca()
    procesador.transformar_datos()

    # Analizar registros descartados
    procesador.analizar_registros_descartados()
    logging.info("Análisis de registros descartados completado")

    # Guardar resultados
    procesador.guardar_resultados(directorio_salida)
    logging.info("Proceso de limpieza y transformación completado exitosamente")


if __name__ == "__main__":

    rutas = [
        # "raw_data/tablero_8_oplb.xlsx - 02102024KOHA.csv",
        "raw_data/tablero_7_oplb.xlsx - 02102024KOHA.csv",
    ]
    for i in rutas:
        main(i)
