import pytest
import pandas as pd
import numpy as np
from bibloclean.limpiar_tablas import BibliotecaDataProcessor, DatasetPartition


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "0": ["Biblioteca_1", "Lib1", "Lib2", None, "Lib4"],
            "1": ["Biblioteca_2", None, "Lib2", None, None],
            "2": ["Lugar de publicación", "Bogotá", "México", "New York", "Madrid"],
            "3": ["Fecha de publicación", "2020", "2019-2020", "c.2018", "©2021"],
            # "4": ['Tema principal', 'Historia del Arte, ', 'Arte', 'Ciencia', 'Literatura'],
            "5": [
                "Nombre principal (autor)",
                "GARCÍA MÁRQUEZ, GABRIEL,",
                "von Goethe,   Johann Wolfgang.",
                "browne,anthony",
                "Süskind, Patrick,; Gambolini, Gerardo",
            ],
        }
    )


@pytest.fixture
def processor(tmp_path, sample_df):
    test_file = tmp_path / "test_data.csv"
    sample_df.to_csv(test_file, index=False)
    return BibliotecaDataProcessor(str(test_file))


def test_cargar_datos(processor):
    df = processor.cargar_datos()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 4
    assert "Biblioteca_1" in df.columns


def test_filtrar_registros_con_biblioteca(processor):
    processor.cargar_datos()
    result = processor.filtrar_registros_con_biblioteca()
    assert isinstance(result, DatasetPartition)
    assert len(result.registros_validos) == 3  # Records with at least one library
    assert len(result.registros_descartados) == 1  # Records with no library


@pytest.mark.parametrize(
    "lugar, expected",
    [
        # Casos básicos
        ("Bogotá", ("Bogotá", "")),
        ("México", ("Ciudad de México", "")),
        ("New York", ("Nueva York", "")),
        # Casos con múltiples lugares
        ("Barcelona,Bogotá", ("Barcelona", "Bogotá")),
        # Casos con paréntesis y espacios
        ("Badalona (España)", ("Badalona", "")),
        ("León ( España)", ("León", "")),
        ("Rubi (Barcelona)", ("Rubi", "")),
        # Casos especiales
        ("##", ("Lugar no identificado", "")),
        (np.nan, ("Lugar no identificado", "")),
        ("", ("Lugar no identificado", "")),
    ],
)
def test_normalizar_lugar_publicacion(lugar, expected):
    processor = BibliotecaDataProcessor("")
    assert processor._normalizar_lugar_publicacion(lugar) == expected


@pytest.mark.parametrize(
    "fecha, expected",
    [
        # Años simples
        ("2020", "2020"),
        # Rangos de años (tomar el mayor)
        ("2019-2020", "2020"),
        # Prefijos especiales
        ("c.2018", "2018"),
        ("©2021", "2021"),
        # Casos inválidos
        ("sin fecha", None),
        ("", None),
        (np.nan, None),
    ],
)
def test_normalizar_fecha_publicacion(fecha, expected):
    processor = BibliotecaDataProcessor("")
    if expected is None:
        assert pd.isna(processor._normalizar_fecha_publicacion(fecha))
    else:
        assert processor._normalizar_fecha_publicacion(fecha) == expected


@pytest.mark.parametrize(
    "autor, expected",
    [
        # Casos básicos de formato
        ("Kibuishi, Kazu,", "Kibuishi, Kazu"),
        ("BROWNE, ANTHONY", "Browne, Anthony"),
        ("browne, anthony", "Browne, Anthony"),
        # Casos con múltiples autores
        (
            "Süskind, Patrick,; Gambolini, Gerardo",
            "Süskind, Patrick; Gambolini, Gerardo",
        ),
        # Casos con títulos académicos
        ("Dr. Cardona Marín, Guillermo", "Cardona Marín, Guillermo"),
        ("Cardona Marín, PhD., Guillermo", "Cardona Marín, Guillermo"),
        # Casos con partículas nobiliarias
        ("von Goethe, Johann Wolfgang", "von Goethe, Johann Wolfgang"),
        # Casos con espacios extra
        ("   Smith,   John   ", "Smith, John"),
        # Casos especiales
        ("", "Desconocido"),
        (None, "Desconocido"),
        (np.nan, "Desconocido"),
    ],
)
def test_normalizar_nombre_autor(autor, expected):
    processor = BibliotecaDataProcessor("")
    assert processor._normalizar_nombre_autor(autor) == expected


@pytest.mark.parametrize(
    "periodo, expected",
    [
        # Casos básicos de siglos
        ("Siglo XX", "XX"),
        ("Siglo xx", "XX"),
        ("Siglo xix", "XIX"),
        ("siglo XXI", "XXI"),
        # Variaciones de formato y espacios
        ("Siglo  XX", "XX"),
        ("Siglo xx.", "XX"),
        ("Sigloxx", "XX"),
        # Rangos de siglos (toma el mayor)
        ("Siglos XX-XXI", "XXI"),
        ("Siglo xix-xx", "XX"),
        # Casos con texto adicional
        ("Siglo XX;Siglo XX", "XX"),
        ("Historia;Siglo xx;Siglo xx", "XX"),
        # Casos con Siglo repetido
        ("Siglo XX;Siglo XX", "XX"),
        ("Siglo XX;Siglo XX;Siglo XX", "XX"),
        ("Siglos xix-xx;Siglos xix-xx", "XX"),
        # Casos con números (toma el mayor)
        ("2013", "XXI"),
        ("1400-1600;1400-1600;1400-1600", "XVI"),
        ("1830-1990;1830-1990;1830-1990", "XX"),
        # Casos inválidos
        ("", None),
        (None, None),
        ("No es un siglo", None),
        # Siglos romanos específicos
        ("Siglo XVIII", "XVIII"),
        ("Siglo XVII", "XVII"),
        ("Siglo XVI", "XVI"),
    ],
)
def test_normalizar_periodo(periodo, expected):
    processor = BibliotecaDataProcessor("")
    assert processor._normalizar_periodo(periodo) == expected


@pytest.mark.parametrize(
    "dewey_number, expected",
    [
        # Standard cases
        ("123.456", "123"),
        ("70904062", "709"),
        ("70.904.062", "709"),
        # Edge cases with prefixes and additional characters
        ("3.386.425", "338"),  # should handle prefixes
        ("Co 867.6", "867"),  # non-numeric prefix
        ("14;155.633", "155"),  # semicolon separator
        ("338.9/86106", "338"),  # slash separator
        ("'070.44", "704"),  # single quote prefix and start with 0
        # Cases with only three digits
        ("523", "523"),  # exactly three digits
        ("920", "920"),  # another three-digit case
        # Cases with fewer than three digits
        ("5", ""),  # fewer than three digits
        ("88", ""),  # fewer than three digits
        # Complex non-numeric patterns
        ("AB123CD456", "123"),  # mixed letters
        ("90-123-456", "901"),  # hyphens in sequence
        (" 650.213 ", "650"),  # spaces around the number
        ("", ""),  # empty input
    ],
)
def test_normalizar_numero_clasificacion_dewey(dewey_number, expected):
    processor = BibliotecaDataProcessor("")
    assert processor._normalizar_numero_clasificacion_dewey(dewey_number) == expected
