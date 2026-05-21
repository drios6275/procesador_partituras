import json

from partituras.modelo.compositor import Compositor
from partituras.modelo.errores import (
    ArchivoNoEncontrado,
    ArchivoCorrupto,
    ErrorPartitura,
)


class LectorPartituras:
    def __init__(self, ruta_archivo: str):
        self.ruta_archivo = ruta_archivo

    def cargar(self) -> list[str]:
        try:
            with open(self.ruta_archivo, "r", encoding="utf-8") as f:
                datos = json.load(f)
            return datos["partituras"]
        except FileNotFoundError as e:
            raise ArchivoNoEncontrado(
                f"No se encontró el archivo: {self.ruta_archivo}"
            ) from e
        except json.JSONDecodeError as e:
            raise ArchivoCorrupto(
                f"El archivo no tiene formato JSON válido: {self.ruta_archivo}"
            ) from e

    def _procesar_una(self, partitura: str, compositor: Compositor) -> dict:
        errores = []
        transformada = None
        revertida = None
        exito = False

        try:
            transformada = compositor.transformar(partitura)
            revertida = compositor.revertir(transformada)
            exito = True
        except ExceptionGroup as eg:
            errores = [str(e) for e in eg.exceptions]
        except ErrorPartitura as e:
            errores = [str(e)]
        except Exception as e:
            errores = [str(e)]

        return {
            "original": partitura,
            "transformada": transformada,
            "revertida": revertida,
            "exito": exito,
            "errores": errores,
        }



