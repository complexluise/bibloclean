import numpy as np
import pandas as pd
import re
import unicodedata
import logging
import time

from functools import wraps
from typing import List, Dict, Tuple

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from extraer_vocabulario import Termino


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logging.info(f"{func.__name__} took {end_time - start_time:.2f} seconds to execute.")
        return result
    return wrapper

import os
from sentence_transformers import SentenceTransformer

class ProcesadorMateriasEmbeddings:
    def __init__(self, tesauro_terminos: List[Termino], modelo_nombre: str = 'paraphrase-multilingual-mpnet-base-v2'):
        """
        Inicializa el procesador con un modelo de embeddings y un tesauro

        Args:
            tesauro_terminos: Lista de términos del tesauro como objetos Termino
            modelo_nombre: Nombre del modelo de sentence-transformers a usar
        """
        self.modelo = self.cargar_o_descargar_modelo(modelo_nombre)
        self.tesauro_terminos = self.extraer_terminos_nivel_2(tesauro_terminos)
        # Precalculamos los embeddings del tesauro
        self.tesauro_embeddings = self.modelo.encode([term.etiqueta for term in self.tesauro_terminos])

    def cargar_o_descargar_modelo(self, modelo_nombre: str) -> SentenceTransformer:
        """
        Carga el modelo si existe localmente, o lo descarga y guarda si no existe.

        Args:
            modelo_nombre: Nombre del modelo de sentence-transformers a usar

        Returns:
            SentenceTransformer: Modelo cargado o descargado
        """
        modelo_path = os.path.join('modelos', modelo_nombre)

        if os.path.exists(modelo_path):
            logging.info(f"Loading existing model from {modelo_path}")
            return SentenceTransformer(modelo_path)
        else:
            logging.info(f"Downloading model {modelo_nombre}")
            modelo = SentenceTransformer(modelo_nombre)
            os.makedirs('modelos', exist_ok=True)
            modelo.save(modelo_path)
            logging.info(f"Model saved to {modelo_path}")
            return modelo
    @staticmethod
    def normalizar_texto(texto: str) -> str:
        """Normaliza el texto eliminando acentos y caracteres especiales"""
        # Eliminar acentos
        texto = ''.join(c for c in unicodedata.normalize('NFD', texto)
                        if unicodedata.category(c) != 'Mn')
        # Limpieza básica
        texto = texto.lower().strip()
        # Eliminar texto entre paréntesis
        texto = re.sub(r'\([^)]*\)', '', texto)
        # Eliminar "en la literatura" y frases similares
        texto = re.sub(r'en la literatura', '', texto)
        return texto.strip()

    @staticmethod
    def extraer_terminos_nivel_2(tesauro: List[Termino]) -> List[Termino]:
        """
        Extrae todos los términos de nivel 2 del tesauro.

        Args:
            tesauro: Lista de términos raíz del tesauro.

        Returns:
            Lista de todos los términos de nivel 2.
        """
        terminos_nivel_2 = []
        for termino_raiz in tesauro:
            terminos_nivel_2.extend(termino_raiz.hijos)
        return terminos_nivel_2

    @staticmethod
    def separar_materias(texto: str) -> List[str]:
        """Separa las materias por punto y coma"""
        return [materia.strip() for materia in texto.split(';')]

    def encontrar_termino_similar(self, termino: str, umbral: float = 0.6) -> Tuple[Termino, float]:
        """
        Encuentra el término más similar en el tesauro usando similitud coseno

        Args:
            termino: Término a buscar
            umbral: Umbral mínimo de similitud para aceptar una coincidencia

        Returns:
            Tupla con el término más similar (como objeto Termino) y su score de similitud
        """
        termino_normalizado = self.normalizar_texto(termino)
        termino_embedding = self.modelo.encode([termino_normalizado])[0]

        similitudes = cosine_similarity([termino_embedding], self.tesauro_embeddings)[0]

        indice_max = np.argmax(similitudes)
        max_similitud = similitudes[indice_max]

        if max_similitud >= umbral:
            # TODO Seguro este es el comportamienteo deseado?
            return self.tesauro_terminos[indice_max], max_similitud
        else:
            return Termino(notacion="", etiqueta=termino, uri="", nivel=0, hijos=[]), max_similitud

    @timer
    def procesar_linea(self, linea: str, umbral: float = 0.3) -> List[Dict]:
        logging.info(f"Processing line: {linea}")
        materias = self.separar_materias(linea)
        resultados = []

        for materia in materias:
            logging.info(f"Processing subject: {materia}")
            termino_sugerido, score = self.encontrar_termino_similar(materia, umbral)
            resultados.append({
                'termino_original': materia,
                'termino_sugerido': termino_sugerido,
                'score': float(score)
            })
            logging.info(f"Suggested term: {termino_sugerido.etiqueta}, Score: {score:.2f}")

        best_result = max(resultados, key=lambda x: x['score'])
        logging.info(f"Best match: {best_result['termino_sugerido'].etiqueta}, Score: {best_result['score']:.2f}")
        return best_result

    @timer
    def procesar_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        logging.info(f"Processing DataFrame with {len(df)} rows")
        df = df.copy()
        df['tema_general'] = df['Tema principal'].apply(
            lambda x: self.procesar_linea(x)['termino_sugerido'].etiqueta if pd.notna(x) else None
        )
        return df


# Ejemplo de uso
if __name__ == "__main__":
    from extraer_vocabulario import extraer_vocabulario
    import time
    import logging

    start_time = time.time()

    logging.info("Loading tesauro from HTML file")
    with open('raw_data/vocabulario.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    tesauro = extraer_vocabulario(html_content)

    logging.info("Initializing ProcesadorMateriasEmbeddings")
    procesador = ProcesadorMateriasEmbeddings(tesauro)

    logging.info("Loading DataFrame")
    df = pd.read_csv("raw_data/tablero_8_oplb.xlsx - 02102024KOHA.csv", header=1)

    logging.info("Processing DataFrame")
    df_procesado = procesador.procesar_dataframe(df)

    logging.info("Saving processed DataFrame")
    df_procesado.to_csv("clean_data/tablero_8_oplb.xlsx - 02102024KOHA_procesado.csv", index=False)

    end_time = time.time()
    logging.info(f"Total execution time: {end_time - start_time:.2f} seconds")
