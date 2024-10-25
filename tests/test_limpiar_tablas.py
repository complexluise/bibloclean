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
        "4": ['Tema principal', 'Historia del Arte, ', 'Arte', 'Ciencia', 'Literatura']
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
    assert processor._normalizar_lugar_publicacion("Bogotá") == "Bogotá"
    assert processor._normalizar_lugar_publicacion("México") == "Ciudad de México"
    assert processor._normalizar_lugar_publicacion("New York") == "Nueva York"
    assert processor._normalizar_lugar_publicacion("##") == "Lugar no identificado"
    assert pd.isna(processor._normalizar_lugar_publicacion(np.nan))


def test_normalizar_fecha_publicacion():
    processor = BibliotecaDataProcessor("")
    assert processor._normalizar_fecha_publicacion("2020") == "2020"
    assert processor._normalizar_fecha_publicacion("2019-2020") == "2020"
    assert processor._normalizar_fecha_publicacion("c.2018") == "2018"
    assert processor._normalizar_fecha_publicacion("©2021") == "2021"
    assert pd.isna(processor._normalizar_fecha_publicacion("sin fecha"))


def test_transformar_datos(processor):
    processor.cargar_datos()
    result = processor.filtrar_registros_con_biblioteca()
    df_transformed = processor.transformar_datos()
    assert isinstance(df_transformed, pd.DataFrame)
    assert 'Lugar de publicación' in df_transformed.columns
    assert 'Fecha de publicación' in df_transformed.columns
