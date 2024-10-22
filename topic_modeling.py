from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import unicodedata
import re
from extraer_vocabulario import Termino


class ProcesadorMateriasEmbeddings:
    def __init__(self, tesauro_terminos: List[Termino], modelo_nombre: str = 'paraphrase-multilingual-mpnet-base-v2'):
        """
        Inicializa el procesador con un modelo de embeddings y un tesauro

        Args:
            tesauro_terminos: Lista de términos del tesauro como objetos Termino
            modelo_nombre: Nombre del modelo de sentence-transformers a usar
        """
        self.modelo = SentenceTransformer(modelo_nombre)
        self.tesauro_terminos = tesauro_terminos
        # Precalculamos los embeddings del tesauro
        self.tesauro_embeddings = self.modelo.encode([term.label for term in tesauro_terminos])

    def normalizar_texto(self, texto: str) -> str:
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

    def separar_materias(self, texto: str) -> List[str]:
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

    def procesar_linea(self, linea: str, umbral: float = 0.6) -> List[Dict]:
        """
        Procesa una línea completa de materias

        Returns:
            Lista de diccionarios con término original, término sugerido (como objeto Termino) y score
        """
        materias = self.separar_materias(linea)
        resultados = []

        for materia in materias:
            termino_sugerido, score = self.encontrar_termino_similar(materia, umbral)
            resultados.append({
                'termino_original': materia,
                'termino_sugerido': termino_sugerido,
                'score': float(score)
            })

        return resultados


# Ejemplo de uso
if __name__ == "__main__":
    from extraer_vocabulario import extraer_vocabulario

    # Cargar el tesauro desde el archivo HTML
    with open('raw_data/vocabulary.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    tesauro = extraer_vocabulario(html_content)

    # Inicializamos el procesador con el tesauro extraído
    procesador = ProcesadorMateriasEmbeddings(tesauro)

    # TODO Datos de ejemplo
    datos = [
        "Autoestima;Autorrealización (Psicología);Tristeza",
        "Crímenes contra la humanidad en la literatura;Derechos humanos en la literatura",
        "Constituciones;Educación cívica",
        "Conducta infantil;Disciplina infantil"
    ]

    # Procesamos cada línea
    for linea in datos:
        print(f"\nProcesando: {linea}")
        resultados = procesador.procesar_linea(linea)
        for resultado in resultados:
            print(f"""
            Original: {resultado['termino_original']}
            Sugerido: {resultado['termino_sugerido'].label} (Notación: {resultado['termino_sugerido'].notation})
            Score: {resultado['score']:.4f}
            """)
