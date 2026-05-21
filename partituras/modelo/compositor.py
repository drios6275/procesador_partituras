from abc import ABC, abstractmethod

from partituras.modelo.errores import (
    ContieneNumero,
    ContieneCaracterInvalido,
    SinNotas,
    EspacioMultiple,
    EspacioBordes,
)

NOTAS = ["do", "re", "mi", "fa", "sol", "la", "si"]
FRECUENCIAS = {
    "do": 261, "re": 293, "mi": 329, "fa": 349,
    "sol": 392, "la": 440, "si": 493,
}
FRECUENCIAS_INVERTIDAS = {v: k for k, v in FRECUENCIAS.items()}


class ReglaTransformacion(ABC):
    def __init__(self, token: int):
        self.token = token

    @abstractmethod
    def transformar(self, partitura: str) -> str:
        pass

    @abstractmethod
    def revertir(self, partitura: str) -> str:
        pass

    @abstractmethod
    def partitura_valida(self, partitura: str) -> bool:
        pass

    def encontrar_numeros_partitura(self, partitura: str) -> list:
        return [(i, c) for i, c in enumerate(partitura) if c.isdigit()]

    def encontrar_caracteres_invalidos(self, partitura: str) -> list:
        return [(i, c) for i, c in enumerate(partitura) if ord(c) > 127]


class ReglaTransposicion(ReglaTransformacion):
    def partitura_valida(self, partitura: str) -> bool:
        errores = []

        numeros = self.encontrar_numeros_partitura(partitura)
        if numeros:
            detalle = ", ".join(f"pos {i}: '{c}'" for i, c in numeros)
            errores.append(ContieneNumero(f"La partitura contiene números: {detalle}"))

        invalidos = self.encontrar_caracteres_invalidos(partitura)
        if invalidos:
            detalle = ", ".join(f"pos {i}: '{c}'" for i, c in invalidos)
            errores.append(ContieneCaracterInvalido(f"La partitura contiene caracteres no ASCII: {detalle}"))

        if not errores:
            tokens = partitura.lower().split()
            validos = set(NOTAS) | {"|", "-"}
            tokens_invalidos = [(i, t) for i, t in enumerate(tokens) if t not in validos]
            if tokens_invalidos:
                detalle = ", ".join(f"pos {i}: '{t}'" for i, t in tokens_invalidos)
                errores.append(ContieneCaracterInvalido(f"La partitura contiene tokens inválidos: {detalle}"))

            notas_presentes = [t for t in tokens if t in NOTAS]
            if not notas_presentes:
                errores.append(SinNotas("La partitura no contiene ninguna nota válida."))

        if len(errores) > 1:
            raise ExceptionGroup("Errores en la partitura", errores)
        elif len(errores) == 1:
            raise errores[0]

        return True

    def transformar(self, partitura: str) -> str:
        self.partitura_valida(partitura)
        partitura = partitura.lower()
        tokens = partitura.split()
        resultado = [
            NOTAS[(NOTAS.index(t) + self.token) % len(NOTAS)] if t in NOTAS else t
            for t in tokens
        ]
        return " ".join(resultado)

    def revertir(self, partitura: str) -> str:
        self.partitura_valida(partitura)
        partitura = partitura.lower()
        tokens = partitura.split()
        resultado = [
            NOTAS[(NOTAS.index(t) - self.token) % len(NOTAS)] if t in NOTAS else t
            for t in tokens
        ]
        return " ".join(resultado)
class ReglaFrecuencia(ReglaTransformacion):
    def partitura_valida(self, partitura: str) -> bool:
        errores = []

        numeros = self.encontrar_numeros_partitura(partitura)
        if numeros:
            detalle = ", ".join(f"pos {i}: '{c}'" for i, c in numeros)
            errores.append(ContieneNumero(f"La partitura contiene números: {detalle}"))

        invalidos = self.encontrar_caracteres_invalidos(partitura)
        if invalidos:
            detalle = ", ".join(f"pos {i}: '{c}'" for i, c in invalidos)
            errores.append(ContieneCaracterInvalido(f"La partitura contiene caracteres no ASCII: {detalle}"))

        if not errores:
            if partitura != partitura.strip():
                errores.append(EspacioBordes("La partitura tiene espacios al inicio o al final."))

            if "  " in partitura:
                errores.append(EspacioMultiple("La partitura tiene más de un espacio consecutivo."))

            if not errores:
                tokens = partitura.lower().split()
                tokens_invalidos = [(i, t) for i, t in enumerate(tokens) if t not in NOTAS]
                if tokens_invalidos:
                    detalle = ", ".join(f"pos {i}: '{t}'" for i, t in tokens_invalidos)
                    errores.append(ContieneCaracterInvalido(f"La partitura contiene tokens inválidos: {detalle}"))

        if len(errores) > 1:
            raise ExceptionGroup("Errores en la partitura", errores)
        elif len(errores) == 1:
            raise errores[0]

        return True

    def transformar(self, partitura: str) -> str:
        self.partitura_valida(partitura)
        partitura = partitura.lower()
        tokens = partitura.split()
        resultado = [str(FRECUENCIAS[t] * self.token) for t in tokens]
        return " ".join(resultado)

    def revertir(self, partitura: str) -> str:
        valores = partitura.split()
        resultado = [FRECUENCIAS_INVERTIDAS[int(v) // self.token] for v in valores]
        return " ".join(resultado)