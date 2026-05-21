import json
import pytest
from partituras.modelo.compositor import *
from partituras.modelo.errores import *
from partituras.modelo.lector import LectorPartituras


@pytest.fixture(scope='function')
def regla_transposicion():
    return ReglaTransposicion(5)


@pytest.fixture(scope='function')
def regla_frecuencia():
    return ReglaFrecuencia(5)


@pytest.fixture(scope='function')
def compositor_transposicion(regla_transposicion):
    return Compositor(regla_transposicion)


@pytest.fixture(scope='function')
def compositor_frecuencia(regla_frecuencia):
    return Compositor(regla_frecuencia)


# ---------------- ReglaTransposicion ----------------

def test_transformar_transposicion(compositor_transposicion):
    resultado = compositor_transposicion.transformar('do')
    assert resultado == "la"


def test_revertir_transposicion(compositor_transposicion):
    resultado = compositor_transposicion.revertir('la')
    assert resultado == "do"


def test_transformar_transposicion_circular(compositor_transposicion):
    # 'si' (indice 6) + 5 = 11 % 7 = 4 -> 'sol'
    resultado = compositor_transposicion.transformar('si')
    assert resultado == "sol"


def test_transformar_transposicion_secuencia(compositor_transposicion):
    resultado = compositor_transposicion.transformar('do re mi')
    # do->la, re->si, mi->do
    assert resultado == "la si do"


def test_transformar_transposicion_con_separadores(compositor_transposicion):
    resultado = compositor_transposicion.transformar('do - mi | sol')
    # los separadores '-' y '|' se conservan
    assert resultado == "la - do | re"


def test_revertir_transposicion_secuencia(compositor_transposicion):
    resultado = compositor_transposicion.revertir('la si do')
    assert resultado == "do re mi"


def test_transformar_transposicion_error_caracter_invalido(compositor_transposicion):
    with pytest.raises(Exception) as exinfo:
        compositor_transposicion.transformar("xyz")
    exinfo.match("ContieneCaracterInvalido")


def test_transformar_transposicion_error_contiene_numero(compositor_transposicion):
    with pytest.raises(Exception) as exinfo:
        compositor_transposicion.transformar("do re 1 mi")
    exinfo.match("ContieneNumero")


def test_transformar_transposicion_error_sin_notas(compositor_transposicion):
    with pytest.raises(Exception) as exinfo:
        compositor_transposicion.transformar("- - | -")
    exinfo.match("SinNotas")


def test_transformar_transposicion_error_sin_notas_y_numero(compositor_transposicion):
    with pytest.raises(Exception) as exinfo:
        compositor_transposicion.transformar("- 1 - | -")
    exinfo.match("SinNotas") and exinfo.match("ContieneNumero")


# ---------------- ReglaFrecuencia ----------------

def test_transformar_frecuencia(compositor_frecuencia):
    # do=261, re=293, mi=329, fa=349
    # con token=5 -> 1305 1465 1645 1745
    resultado = compositor_frecuencia.transformar('do re mi fa')
    assert resultado == "1305 1465 1645 1745"


def test_revertir_frecuencia(compositor_frecuencia):
    resultado = compositor_frecuencia.revertir("1305 1465 1645 1745")
    assert resultado == 'do re mi fa'


def test_transformar_frecuencia_error_caracter_invalido(compositor_frecuencia):
    with pytest.raises(Exception) as exinfo:
        compositor_frecuencia.transformar("dó re mi")
    exinfo.match("ContieneCaracterInvalido")


def test_transformar_frecuencia_error_contiene_numero(compositor_frecuencia):
    with pytest.raises(Exception) as exinfo:
        compositor_frecuencia.transformar("do re 1 mi")
    exinfo.match("ContieneNumero")


def test_transformar_frecuencia_error_espacio_bordes(compositor_frecuencia):
    with pytest.raises(Exception) as exinfo:
        compositor_frecuencia.transformar(" do re mi ")
    exinfo.match("EspacioBordes")


def test_transformar_frecuencia_error_espacio_multiple(compositor_frecuencia):
    with pytest.raises(Exception) as exinfo:
        compositor_frecuencia.transformar("do  re mi")
    exinfo.match("EspacioMultiple")


def test_transformar_frecuencia_error_espacio_multiple_y_numero(compositor_frecuencia):
    with pytest.raises(Exception) as exinfo:
        compositor_frecuencia.transformar("do  re 1 mi")
    exinfo.match("EspacioMultiple") and exinfo.match("ContieneNumero")


# ---------------- LectorPartituras ----------------

@pytest.fixture
def archivo_valido(tmp_path):
    archivo = tmp_path / "partituras.json"
    archivo.write_text(json.dumps({"partituras": ["do re mi", "fa sol la"]}))
    return str(archivo)


@pytest.fixture
def archivo_corrupto(tmp_path):
    archivo = tmp_path / "corrupto.json"
    archivo.write_text("{esto no es json valido")
    return str(archivo)


def test_lector_cargar_archivo_valido(archivo_valido):
    lector = LectorPartituras(archivo_valido)
    assert lector.cargar() == ["do re mi", "fa sol la"]


def test_lector_cargar_archivo_no_existe():
    lector = LectorPartituras("/ruta/que/no/existe.json")
    with pytest.raises(Exception) as exinfo:
        lector.cargar()
    exinfo.match("ArchivoNoEncontrado")


def test_lector_cargar_archivo_corrupto(archivo_corrupto):
    lector = LectorPartituras(archivo_corrupto)
    with pytest.raises(Exception) as exinfo:
        lector.cargar()
    exinfo.match("ArchivoCorrupto")


def test_lector_procesar_con_compositor_exitoso(tmp_path, compositor_transposicion):
    archivo = tmp_path / "p.json"
    archivo.write_text(json.dumps({"partituras": ["do re mi"]}))
    lector = LectorPartituras(str(archivo))

    resultados = lector.procesar_con(compositor_transposicion)

    assert len(resultados) == 1
    assert resultados[0]["original"] == "do re mi"
    assert resultados[0]["exito"] is True
    assert resultados[0]["transformada"] == "la si do"
    assert resultados[0]["revertida"] == "do re mi"


def test_lector_procesar_con_compositor_captura_errores(tmp_path, compositor_transposicion):
    archivo = tmp_path / "p.json"
    archivo.write_text(json.dumps({"partituras": ["do re mi", "do re 1 mi"]}))
    lector = LectorPartituras(str(archivo))

    resultados = lector.procesar_con(compositor_transposicion)

    assert len(resultados) == 2
    assert resultados[0]["exito"] is True
    assert resultados[1]["original"] == "do re 1 mi"
    assert resultados[1]["exito"] is False
    assert len(resultados[1]["errores"]) >= 1
