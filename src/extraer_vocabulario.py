import json
import re

from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Termino:
    """Representa un término en la jerarquía del vocabulario"""

    notacion: str
    etiqueta: str
    uri: str
    nivel: int
    hijos: list["Termino"]
    notacion_padre: Optional[str] = None
    etiqueta_padre: Optional[str] = None


def extraer_vocabulario(contenido_html: str) -> list[Termino]:
    """
    Extrae la jerarquía del vocabulario del contenido HTML

    Args:
        contenido_html: Cadena HTML que contiene la estructura del vocabulario

    Returns:
        Termino: Término raíz con la jerarquía completa
    """
    sopa = BeautifulSoup(contenido_html, "html.parser")

    def extraer_termino(
        elemento_li, notacion_padre=None, etiqueta_padre=None
    ) -> Termino:
        # Extraer el elemento ancla que contiene la información del término
        ancla = elemento_li.find("a", class_="jstree-anchor")
        texto_completo = ancla.get_text(strip=True)

        # Extraer detalles del término
        if ancla.get("aria-level") == "3":
            notacion = notacion_padre + "extended"
            etiqueta = texto_completo
        else:
            notacion = ancla.find("span", class_="tree-notation").text.strip()
            etiqueta = texto_completo[texto_completo.find(notacion) + len(notacion):]

        etiqueta = re.sub(
            r"\s+", " ", etiqueta
        ).strip()

        # Obtener URI y nivel
        uri = ancla.get("data-uri", "")
        nivel = int(ancla.get("aria-level", 1))

        # Crear objeto término
        termino = Termino(
            notacion=notacion,
            etiqueta=etiqueta,
            uri=uri,
            nivel=nivel,
            hijos=[],
            notacion_padre=notacion_padre,
            etiqueta_padre=etiqueta_padre,
        )

        # Procesar hijos si existen
        hijos_ul = elemento_li.find("ul", class_="jstree-children")
        if hijos_ul:
            for hijo_li in hijos_ul.find_all("li", recursive=False):
                hijo_termino = extraer_termino(
                    hijo_li,
                    notacion_padre=termino.notacion,
                    etiqueta_padre=termino.etiqueta,
                )
                termino.hijos.append(hijo_termino)

        return termino

    # Encontrar el elemento raíz y procesar la jerarquía
    raiz_li = sopa.find_all("li", role="presentation", attrs={"aria-level": "1"})
    if not raiz_li:
        raise ValueError("Elemento raíz no encontrado en el HTML")

    return [extraer_termino(raiz_li) for raiz_li in raiz_li]


def imprimir_jerarquia(termino: Termino, sangria: int = 0):
    """
    Imprime la jerarquía del vocabulario en un formato legible

    Args:
        termino: Objeto Termino a imprimir
        sangria: Nivel de sangría actual
    """
    print("  " * sangria + f"{termino.notacion} - {termino.etiqueta}")
    for hijo in termino.hijos:
        imprimir_jerarquia(hijo, sangria + 1)


def guardar_vocabulario_como_json(vocabulario: list[Termino], nombre_archivo: str):
    """
    Guarda la jerarquía del vocabulario en un archivo JSON

    Args:
        vocabulario: Lista de objetos Termino raíz
        nombre_archivo: Nombre del archivo JSON a guardar
    """

    def termino_a_diccionario(termino: Termino):
        diccionario_termino = asdict(termino)
        diccionario_termino["hijos"] = [
            termino_a_diccionario(hijo) for hijo in termino.hijos
        ]
        return diccionario_termino

    diccionario_vocabulario = [
        termino_a_diccionario(termino) for termino in vocabulario
    ]

    with open(nombre_archivo, "w", encoding="utf-8") as f:
        json.dump(diccionario_vocabulario, f, ensure_ascii=False, indent=2)


# Ejemplo de uso
if __name__ == "__main__":
    with open("../raw_data/vocabulario.html", "r", encoding="utf-8") as f:
        contenido_html = f.read()

    vocabulario = extraer_vocabulario(contenido_html)

    # Guardar vocabulario en archivo JSON
    guardar_vocabulario_como_json(vocabulario, "vocabulario.json")

    print("El vocabulario ha sido guardado en vocabulario.json")

    # Opcionalmente, aún puedes imprimir la jerarquía
    for termino in vocabulario:
        imprimir_jerarquia(termino)
