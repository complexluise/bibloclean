import pandas as pd
import numpy as np
import re
from pathlib import Path
from typing import List, Dict, Union, Tuple
from dataclasses import dataclass


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
            'bibliotecas': [
                'Biblioteca_1', 'Biblioteca_2', 'Biblioteca_3',
                'Biblioteca_4', 'Biblioteca_5', 'Biblioteca_6',
                'Biblioteca_7'
            ],
            'lugar': 'Lugar de publicación',
            'fecha': 'Fecha de publicación'
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
            'bibliotecas': [col for col in self.columnas_esperadas['bibliotecas']
                            if col in self.datos.columns],
            'lugar': self.columnas_esperadas['lugar']
            if self.columnas_esperadas['lugar'] in self.datos.columns else None,
            'fecha': self.columnas_esperadas['fecha']
            if self.columnas_esperadas['fecha'] in self.datos.columns else None
        }
        return columnas_disponibles

    def cargar_datos(self, fila_encabezado: int = 1) -> pd.DataFrame:
        """
        Carga los datos del archivo Excel.

        Args:
            fila_encabezado (int): Número de fila que contiene los encabezados

        Returns:
            pd.DataFrame: DataFrame con los datos cargados
        """
        self.datos = pd.read_csv(self.ruta_archivo, header=fila_encabezado)
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

        columnas_biblioteca = self.obtener_columnas_disponibles()['bibliotecas']

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

        return DatasetPartition(registros_validos, registros_descartados)

    def _normalizar_lugar_publicacion(self, valor: Union[str, float]) -> str:
        """
        Normaliza el lugar de publicación aplicando reglas específicas.

        Args:
            valor: Valor a normalizar

        Returns:
            str: Lugar de publicación normalizado
        """
        if pd.isnull(valor):
            return np.nan

        valor = str(valor).strip()
        # Limpieza básica
        valor = valor.replace(';', ',').replace(':', '') \
            .replace('[', '').replace(']', '') \
            .replace('©', '')

        # Eliminar espacios múltiples
        valor = ' '.join(valor.split())

        # Diccionario de normalizaciones de ciudades
        normalizaciones_ciudades = {
            'Bogotá': 'Bogotá',
            'México': 'Ciudad de México',
            'Mexico': 'Ciudad de México',
            'Madrid': 'Madrid',
            'Salamanca': 'Salamanca',
            'Köln': 'Colonia',
            'Koln': 'Colonia',
            'Singapur': 'Singapur',
            'New York': 'Nueva York',
            'Londres': 'Londres',
            'París': 'París'
        }

        for ciudad_original, ciudad_normalizada in normalizaciones_ciudades.items():
            if ciudad_original in valor:
                valor = valor.replace(ciudad_original, ciudad_normalizada)

        # Limpiar números y caracteres especiales
        valor = ''.join([c for c in valor if not c.isdigit()]).rstrip(',')

        # Manejo de lugares no identificados
        if any(phrase in valor.lower() for phrase in ["no identificado", "##"]) or \
                valor.startswith("#"):
            return "Lugar no identificado"

        return valor

    def _normalizar_fecha_publicacion(self, fecha: Union[str, float]) -> Union[str, float]:
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
        fecha = re.sub(r'[;#©\\]', '', fecha)
        fecha = re.sub(r'[\[\]\?]', '', fecha)
        fecha = re.sub(r'c|circa|Ariel|Aprox\.?', '', fecha, flags=re.IGNORECASE)
        fecha = fecha.rstrip('.')

        # Extraer años (secuencias de 4 dígitos)
        anos_encontrados = re.findall(r'\b\d{4}\b', fecha)

        return max(anos_encontrados) if anos_encontrados else np.nan

    def normalizar_datos(self) -> pd.DataFrame:
        """
        Aplica todas las normalizaciones necesarias al DataFrame según las columnas disponibles.

        Returns:
            pd.DataFrame: DataFrame con datos normalizados
        """
        if self.datos is None:
            raise ValueError("Primero debe cargar los datos usando cargar_datos()")

        columnas_disponibles = self.obtener_columnas_disponibles()

        # Normalizar lugar de publicación si existe la columna
        if columnas_disponibles['lugar']:
            print(f"Normalizando columna: {columnas_disponibles['lugar']}")
            self.datos[columnas_disponibles['lugar']] = self.datos[columnas_disponibles['lugar']] \
                .apply(self._normalizar_lugar_publicacion)

        # Normalizar fecha de publicación si existe la columna
        if columnas_disponibles['fecha']:
            print(f"Normalizando columna: {columnas_disponibles['fecha']}")
            self.datos[columnas_disponibles['fecha']] = self.datos[columnas_disponibles['fecha']] \
                .apply(self._normalizar_fecha_publicacion)

        return self.datos

    def guardar_resultados(self, directorio_salida: str) -> None:
        """
        Guarda tanto los resultados procesados como los registros descartados.

        Args:
            directorio_salida (str): Directorio donde se guardarán los archivos
        """
        if self.datos is None:
            raise ValueError("No hay datos para guardar")

        directorio = Path(directorio_salida)
        directorio.mkdir(parents=True, exist_ok=True)

        # Obtener el nombre del archivo original sin extensión
        nombre_archivo_original = self.ruta_archivo.stem

        # Crear el nuevo nombre de archivo con el sufijo "_procesado"
        nombre_archivo_procesado = f"{nombre_archivo_original}_procesado.csv"

        # Guardar registros procesados
        ruta_procesados = directorio / nombre_archivo_procesado
        self.datos.to_csv(ruta_procesados, index=False)
        print(f"Registros procesados guardados en: {ruta_procesados}")

        # Guardar registros descartados si existen
        if self.datos_descartados is not None and not self.datos_descartados.empty:
            nombre_archivo_descartados = f"{nombre_archivo_original}_descartados.csv"
            ruta_descartados = directorio / nombre_archivo_descartados
            self.datos_descartados.to_csv(ruta_descartados, index=False)
            print(f"Registros descartados guardados en: {ruta_descartados}")

    def analizar_registros_descartados(self) -> Dict:
        """
        Analiza los registros descartados para identificar patrones y posibles reglas
        de transformación adicionales.

        Returns:
            Dict: Estadísticas y patrones encontrados en los registros descartados
        """
        if self.datos_descartados is None or self.datos_descartados.empty:
            return {"mensaje": "No hay registros descartados para analizar"}

        analisis = {
            "total_registros": len(self.datos_descartados),
            "columnas_vacias": {},
            "valores_unicos": {},
            "patrones_fecha": set(),
            "patrones_lugar": set()
        }

        # Analizar columnas vacías
        for col in self.datos_descartados.columns:
            pct_nulos = (self.datos_descartados[col].isna().sum() / len(self.datos_descartados)) * 100
            analisis["columnas_vacias"][col] = f"{pct_nulos:.2f}%"

        # Analizar valores únicos en columnas relevantes
        columnas_disponibles = self.obtener_columnas_disponibles()

        if columnas_disponibles['lugar']:
            lugares_unicos = self.datos_descartados[columnas_disponibles['lugar']].dropna().unique()
            analisis["valores_unicos"]["lugares"] = list(lugares_unicos)

        if columnas_disponibles['fecha']:
            fechas_unicas = self.datos_descartados[columnas_disponibles['fecha']].dropna().unique()
            analisis["valores_unicos"]["fechas"] = list(fechas_unicas)

        return analisis


def main():
    # Configuración de rutas
    ruta_entrada = "raw_data/tablero_7_oplb.xlsx - 02102024KOHA.csv"
    directorio_salida = "clean_data"

    # Inicializar procesador
    procesador = BibliotecaDataProcessor(ruta_entrada)

    # Ejecutar pipeline de procesamiento
    procesador.cargar_datos()
    particion = procesador.filtrar_registros_con_biblioteca()
    procesador.normalizar_datos()

    # Analizar registros descartados
    analisis_descartados = procesador.analizar_registros_descartados()
    print("\nAnálisis de registros descartados:")
    print(analisis_descartados)

    # Guardar resultados
    procesador.guardar_resultados(directorio_salida)


if __name__ == "__main__":
    main()
