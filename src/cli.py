import click
import logging
from pathlib import Path
from src.limpiar_tablas import BibliotecaDataProcessor


@click.command()
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
    """
    Limpia y procesa archivos de datos bibliográficos de KOHA.

    ARCHIVO: Ruta al archivo CSV/Excel que contiene los datos a procesar
    """
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


if __name__ == "__main__":
    limpiar_koha()
