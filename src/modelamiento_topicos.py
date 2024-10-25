import logging
import os
import pandas as pd
import re
import time
import unicodedata
import torch

from functools import wraps
from typing import List

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from extraer_vocabulario import Termino

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logging.info(
            f"{func.__name__} took {end_time - start_time:.2f} seconds to execute."
        )
        return result

    return wrapper


class ProcesadorMateriasEmbeddings:
    def __init__(
        self,
        tesauro_terminos: List[Termino],
        modelo_nombre: str = "jinaai/jina-embeddings-v3",
    ):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.modelo = self.cargar_o_descargar_modelo(modelo_nombre)
        self.tesauro_terminos = self.extraer_terminos_nivel_3(tesauro_terminos)
        self.tesauro_embeddings = self.modelo.encode(
            [term.etiqueta for term in self.tesauro_terminos], device=self.device
        )

    @staticmethod
    def cargar_o_descargar_modelo(modelo_nombre: str) -> SentenceTransformer:
        modelo_path = os.path.join("../modelos", modelo_nombre)
        if os.path.exists(modelo_path):
            logging.info(f"Cargando modelo existente desde {modelo_path}")
            modelo = SentenceTransformer(modelo_path, trust_remote_code=True)
        else:
            logging.info(f"Descargando modelo {modelo_nombre}")
            modelo = SentenceTransformer(modelo_nombre, trust_remote_code=True)
            os.makedirs("../modelos", exist_ok=True)
            modelo.save(modelo_path)
            logging.info(f"Modelo guardado en {modelo_path}")
        return modelo.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))

    @staticmethod
    def normalizar_texto(texto: str) -> str:
        """Normaliza el texto eliminando acentos y caracteres especiales"""
        # Eliminar acentos
        texto = "".join(
            c
            for c in unicodedata.normalize("NFD", texto)
            if unicodedata.category(c) != "Mn"
        )
        # Limpieza básica
        texto = texto.lower().strip()
        # Eliminar texto entre paréntesis
        texto = re.sub(r"\([^)]*\)", "", texto)
        # Eliminar "en la literatura" y frases similares
        texto = re.sub(r"en la literatura", "", texto)
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
    def extraer_terminos_nivel_3(tesauro: List[Termino]) -> List[Termino]:
        """
        Extrae todos los términos de nivel 3 del tesauro.

        Args:
            tesauro: Lista de términos raíz del tesauro.

        Returns:
            Lista de todos los términos de nivel 3.
        """
        terminos_nivel_3 = []
        for termino_raiz in tesauro:
            for termino_nivel_2 in termino_raiz.hijos:
                terminos_nivel_3.extend(termino_nivel_2.hijos)
        return terminos_nivel_3

    @timer
    def procesar_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        logging.info(f"Procesando DataFrame con {len(df)} filas")
        df = df.copy()

        temas_validos = df["Tema principal"].dropna()
        temas_normalizados = [self.normalizar_texto(tema) for tema in temas_validos]

        embeddings_temas = self.modelo.encode(temas_normalizados, device=self.device)

        similitudes = cosine_similarity(embeddings_temas, self.tesauro_embeddings)

        indices_mejores_coincidencias = similitudes.argmax(axis=1)
        puntuaciones_mejores_coincidencias = similitudes.max(axis=1)

        mejores_coincidencias = pd.Series(
            [self.tesauro_terminos[i].etiqueta for i in indices_mejores_coincidencias],
            index=temas_validos.index,
        )

        df.loc[temas_validos.index, "tema_general"] = mejores_coincidencias
        df.loc[temas_validos.index, "score_tema_general"] = (
            puntuaciones_mejores_coincidencias
        )

        return df


if __name__ == "__main__":
    from extraer_vocabulario import extraer_vocabulario

    start_time = time.time()

    logging.info("Loading tesauro from HTML file")
    with open("../raw_data/vocabulario.html", "r", encoding="utf-8") as f:
        html_content = f.read()

    tesauro = extraer_vocabulario(html_content)

    logging.info("Initializing ProcesadorMateriasEmbeddings")
    procesador = ProcesadorMateriasEmbeddings(tesauro)

    logging.info("Loading DataFrame")
    df = pd.read_csv("../raw_data/tablero_8_oplb.xlsx - 02102024KOHA.csv", header=1)

    logging.info("Processing DataFrame")
    df_procesado = procesador.procesar_dataframe(df)

    logging.info("Saving processed DataFrame")
    df_procesado.to_csv(
        "clean_data/tablero_8_oplb.xlsx - 02102024KOHA_enriquecido.csv", index=False
    )

    end_time = time.time()
    logging.info(f"Total execution time: {end_time - start_time:.2f} seconds")
