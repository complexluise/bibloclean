import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from limpiar_tablas import BibliotecaDataProcessor, DatasetPartition


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "0": ['Biblioteca_1', 'Lib1', 'Lib2', None, 'Lib4'],
        "1": ['Biblioteca_2', None, 'Lib2', None, None],
        "2": ['Lugar de publicación', 'Bogotá', 'México', 'New York', 'Madrid'],
        "3": ['Fecha de publicación', '2020', '2019-2020', 'c.2018', '©2021'],
        #"4": ['Tema principal', 'Historia del Arte, ', 'Arte', 'Ciencia', 'Literatura'],
        "5": ['Nombre principal (autor)',
              'GARCÍA MÁRQUEZ, GABRIEL,',
              'von Goethe,   Johann Wolfgang.',
              'browne,anthony',
              'Süskind, Patrick,; Gambolini, Gerardo']
    })


@pytest.fixture
def processor(tmp_path, sample_df):
    test_file = tmp_path / "test_data.csv"
    sample_df.to_csv(test_file, index=False)
    return BibliotecaDataProcessor(str(test_file))


def test_cargar_datos(processor):
    df = processor.cargar_datos()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 4
    assert 'Biblioteca_1' in df.columns


def test_filtrar_registros_con_biblioteca(processor):
    processor.cargar_datos()
    result = processor.filtrar_registros_con_biblioteca()
    assert isinstance(result, DatasetPartition)
    assert len(result.registros_validos) == 3  # Records with at least one library
    assert len(result.registros_descartados) == 1  # Records with no library


def test_normalizar_lugar_publicacion():
    processor = BibliotecaDataProcessor("")
    assert processor._normalizar_lugar_publicacion("Bogotá") == ("Bogotá", "")
    assert processor._normalizar_lugar_publicacion("México") == ("Ciudad de México", "")
    assert processor._normalizar_lugar_publicacion("New York") == ("Nueva York", "")
    assert processor._normalizar_lugar_publicacion("##") == ("Lugar no identificado", "")
    assert processor._normalizar_lugar_publicacion("Barcelona,Bogotá") == ("Barcelona", "Bogotá")
    assert not pd.isna(processor._normalizar_lugar_publicacion(np.nan)[0])


def test_normalizar_fecha_publicacion():
    processor = BibliotecaDataProcessor("")
    assert processor._normalizar_fecha_publicacion("2020") == "2020"
    assert processor._normalizar_fecha_publicacion("2019-2020") == "2020"
    assert processor._normalizar_fecha_publicacion("c.2018") == "2018"
    assert processor._normalizar_fecha_publicacion("©2021") == "2021"
    assert pd.isna(processor._normalizar_fecha_publicacion("sin fecha"))


def test_normalizar_nombre_autor():
    processor = BibliotecaDataProcessor("")

    # Test removing trailing commas
    assert processor._normalizar_nombre_autor("Kibuishi, Kazu,") == "Kibuishi, Kazu"

    # Test standardizing format and removing extra spaces
    assert processor._normalizar_nombre_autor("Otálvaro S., Rubén Darío  ") == "Otálvaro S., Rubén Darío"

    # Test fixing capitalization
    assert processor._normalizar_nombre_autor("BROWNE, ANTHONY") == "Browne, Anthony"
    assert processor._normalizar_nombre_autor("browne, anthony") == "Browne, Anthony"

    # Test handling missing authors
    assert processor._normalizar_nombre_autor("") == "Desconocido"
    assert processor._normalizar_nombre_autor(None) == "Desconocido"
    assert not pd.isna(processor._normalizar_nombre_autor(np.nan))

    # Test handling compound surnames
    assert processor._normalizar_nombre_autor("Villamil Portilla, Edgardo.") == "Villamil Portilla, Edgardo"

    # Test removing titles and fixing misplaced initials
    assert processor._normalizar_nombre_autor("Dr. Cardona Marín, Guillermo") == "Cardona Marín, Guillermo"
    assert processor._normalizar_nombre_autor("Cardona Marín, PhD., Guillermo") == "Cardona Marín, Guillermo"

    # Test handling multiple authors
    assert processor._normalizar_nombre_autor(
        "Süskind, Patrick,; Gambolini, Gerardo") == "Süskind, Patrick; Gambolini, Gerardo"

    # Test handling special characters and diacritics
    assert processor._normalizar_nombre_autor("García Márquez, Gabriel") == "García Márquez, Gabriel"

    # Test handling various edge cases
    assert processor._normalizar_nombre_autor("   Smith,   John   ") == "Smith, John"
    assert processor._normalizar_nombre_autor("von Goethe, Johann Wolfgang") == "von Goethe, Johann Wolfgang"
    assert processor._normalizar_nombre_autor("O'Connor, Flannery") == "O'Connor, Flannery"


def test_normalizar_titulo():
    processor = BibliotecaDataProcessor("")

    # Test removing leading and trailing spaces
    assert processor._normalizar_titulo(" El príncipe ") == "El príncipe"

    # Test correct punctuation spacing
    assert processor._normalizar_titulo("Prince of the elves /") == "Prince of the elves"

    # Test removing trailing slashes
    assert processor._normalizar_titulo("Batallas de Champiñón /") == "Batallas de Champiñón"

    # Test replacing incorrect comma separators
    assert processor._normalizar_titulo("Los cantos de Maldoror /,") == "Los cantos de Maldoror"

    # Test removing redundant punctuation
    assert processor._normalizar_titulo("The adventures of Ook and Gluk :,") == "The adventures of Ook and Gluk"

    # Test handling subtitle indicators
    assert processor._normalizar_titulo("Protección familiar :") == "Protección familiar"

    # Test title case conversion for proper nouns
    assert processor._normalizar_titulo("En el país de los zenúes /") == "En el país de los zenúes"

    # Test removing invalid characters
    assert processor._normalizar_titulo("Fácil dibujar expresión artística %") == "Fácil dibujar expresión artística"

    # Test handling multiple issues simultaneously
    assert processor._normalizar_titulo(" Historia del arte moderno /: , ") == "Historia del arte moderno"

    # Test preserving valid special characters
    assert processor._normalizar_titulo("C++ Programming Language") == "C++ Programming Language"

    # Test handling leading numbers and semicolons
    assert processor._normalizar_titulo("00;Fichero de juegos al aire libre") == "Fichero de juegos al aire libre"

    # Test handling empty or None values
    assert processor._normalizar_titulo("") == "Sin título"
    assert processor._normalizar_titulo(None) == "Sin título"
    assert not pd.isna(processor._normalizar_titulo(np.nan))


def test_transformar_datos(processor):
    processor.cargar_datos()
    result = processor.filtrar_registros_con_biblioteca()
    df_transformed = processor.transformar_datos()
    assert isinstance(df_transformed, pd.DataFrame)
    assert 'Lugar de publicación' in df_transformed.columns
    assert 'Fecha de publicación' in df_transformed.columns
