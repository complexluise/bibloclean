import click
import logging
from pathlib import Path
from bibloclean.limpiar_tablas import BibliotecaDataProcessor
import pandas as pd

@click.group()
def cli():
    """Herramientas para procesamiento de datos bibliográficos"""
    pass

@cli.command()
@click.argument("archivo", type=click.Path(exists=True))
@click.option(
    "--salida",
    "-s",
    default="clean_data",
    help="Directorio de salida para los archivos procesados",
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Mostrar información detallada del proceso"
)
def limpiar_koha(archivo, salida, verbose):
    """Limpia y procesa archivos de datos bibliográficos de KOHA."""
    # Configurar logging
    nivel_log = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=nivel_log, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    click.echo(f"Procesando archivo: {archivo}")

    try:
        # Inicializar procesador
        procesador = BibliotecaDataProcessor(archivo)

        # Ejecutar pipeline de procesamiento
        procesador.cargar_datos()
        click.echo("✔ Datos cargados correctamente")

        procesador.filtrar_registros_con_biblioteca()
        click.echo("✔ Registros filtrados por biblioteca")

        procesador.transformar_datos()
        click.echo("✔ Datos transformados")

        # Crear directorio de salida si no existe
        Path(salida).mkdir(parents=True, exist_ok=True)

        # Guardar resultados
        procesador.guardar_resultados(salida)
        click.echo(f"✔ Resultados guardados en: {salida}")

        # Mostrar estadísticas
        if verbose:
            analisis = procesador.analizar_registros_descartados()
            click.echo("\nEstadísticas de registros descartados:")
            click.echo(f"Total de registros descartados: {analisis['total_registros']}")

        click.echo("\n¡Proceso completado exitosamente! 🎉")

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        raise click.Abort()

@cli.command()
@click.argument("archivo", type=click.Path(exists=True))
@click.option(
    "--umbral",
    "-u",
    default=0.7,
    help="Umbral de similaridad para conexiones entre temas (0-1)"
)
@click.option(
    "--modelo",
    "-m",
    default="jinaai/jina-embeddings-v3",
    help="Modelo de embeddings a utilizar"
)
@click.option(
    "--salida",
    "-s",
    default="clean_data/red_temas.graphml",
    help="Ruta de salida para el archivo GraphML"
)
def analizar_red(archivo, umbral, modelo, salida):
    """
    Genera red de correlaciones entre temas bibliográficos.

    ARCHIVO: CSV procesado con temas asignados
    """
    from bibloclean.modelamiento_topicos import ProcesadorMateriasEmbeddings, construir_red, exportar_graphml
    from bibloclean.extraer_vocabulario import extraer_vocabulario

    click.echo("🔄 Iniciando análisis de red temática")

    # Cargar tesauro
    with open("raw_data/vocabulario.html", "r", encoding="utf-8") as f:
        tesauro = extraer_vocabulario(f.read())

    # Inicializar procesador y red
    procesador = ProcesadorMateriasEmbeddings(tesauro, modelo_nombre=modelo)

    # Cargar datos
    df = pd.read_csv(archivo)

    # Construir y exportar red
    grafo = construir_red(umbral, df, procesador)

    # Crear directorio si no existe
    Path(salida).parent.mkdir(parents=True, exist_ok=True)
    exportar_graphml(grafo, salida)

    # Mostrar estadísticas
    click.echo(f"✨ Red generada con éxito:")
    click.echo(f"  - Nodos: {grafo.number_of_nodes()}")
    click.echo(f"  - Conexiones: {grafo.number_of_edges()}")
    click.echo(f"  - Archivo guardado en: {salida}")


if __name__ == "__main__":
    cli()
