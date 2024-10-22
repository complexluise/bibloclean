from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import unicodedata
import re


class ProcesadorMateriasEmbeddings:
    def __init__(self, tesauro_terminos: List[str], modelo_nombre: str = 'paraphrase-multilingual-mpnet-base-v2'):
        """
        Inicializa el procesador con un modelo de embeddings y un tesauro

        Args:
            tesauro_terminos: Lista de términos del tesauro
            modelo_nombre: Nombre del modelo de sentence-transformers a usar
        """
        self.modelo = SentenceTransformer(modelo_nombre)
        self.tesauro_terminos = tesauro_terminos
        # Precalculamos los embeddings del tesauro
        self.tesauro_embeddings = self.modelo.encode(tesauro_terminos)

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

    def encontrar_termino_similar(self, termino: str, umbral: float = 0.6) -> Tuple[str, float]:
        """
        Encuentra el término más similar en el tesauro usando similitud coseno

        Args:
            termino: Término a buscar
            umbral: Umbral mínimo de similitud para aceptar una coincidencia

        Returns:
            Tupla con el término más similar y su score de similitud
        """
        termino_normalizado = self.normalizar_texto(termino)
        # Calculamos el embedding del término de búsqueda
        termino_embedding = self.modelo.encode([termino_normalizado])[0]

        # Calculamos similitud con todos los términos del tesauro
        similitudes = cosine_similarity([termino_embedding], self.tesauro_embeddings)[0]

        # Encontramos el índice del término más similar
        indice_max = np.argmax(similitudes)
        max_similitud = similitudes[indice_max]

        if max_similitud >= umbral:
            return self.tesauro_terminos[indice_max], max_similitud
        else:
            return termino, max_similitud

    def procesar_linea(self, linea: str, umbral: float = 0.6) -> List[Dict]:
        """
        Procesa una línea completa de materias

        Returns:
            Lista de diccionarios con término original, término sugerido y score
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
    # Ejemplo de tesauro más amplio
    tesauro_ejemplo = [
        "PSICOLOGÍA - AUTOESTIMA",
        "PSICOLOGÍA - DESARROLLO PERSONAL",
        "PSICOLOGÍA - EMOCIONES",
        "PSICOLOGÍA - CONDUCTA",
        "DERECHO INTERNACIONAL HUMANITARIO",
        "DERECHO - DERECHOS HUMANOS",
        "DERECHO PENAL INTERNACIONAL",
        "EDUCACIÓN - CIVISMO",
        "EDUCACIÓN - VALORES",
        "PSICOLOGÍA INFANTIL",
        "EDUCACIÓN - DISCIPLINA",
        "DESARROLLO INFANTIL",
        # Agregar más términos según sea necesario
    ]

    # Inicializamos el procesador
    procesador = ProcesadorMateriasEmbeddings(tesauro_ejemplo)

    # Datos de ejemplo
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
            Sugerido: {resultado['termino_sugerido']}
            Score: {resultado['score']:.4f}
            """)