"""Tests de traduccion VA->PA y de los 4 algoritmos de reemplazo."""
from so_sim.core import World
from so_sim.scenarios import presets
from tests.helpers import correr, mundo


def test_traduccion_va_pa_y_hit():
    # va = 0x2008 -> VPN=2, offset=0x8. Primer acceso FALLA, el segundo ACIERTA.
    w = correr(mundo({
        "num_marcos": 4, "offset_bits": 12,
        "procesos": [{"pid": 1, "rafaga": 2, "llegada": 0, "accesos": [
            {"en_cpu": 0, "va": 0x2008}, {"en_cpu": 1, "va": 0x2008}]}],
    }))
    ev = w.mmu.ultimo_evento
    assert ev["vpn"] == 2
    assert ev["offset"] == 0x8
    assert ev["resultado"] == "HIT"
    # marco 0 (primer libre) -> PA = (0 << 12) | 8 = 8
    assert ev["pa"] == 0x8
    assert w.mmu.fallos == 1
    assert w.mmu.aciertos == 1


def _fallos_de(alg: str):
    cfg = presets.cargar("page_faults")
    cfg.replacer = alg
    w = correr(World(cfg))
    total = w.mmu.aciertos + w.mmu.fallos
    return w.mmu.fallos, total


def test_reemplazos_sobre_cadena_clasica():
    n_refs = 13                      # longitud de la cadena del preset
    distintas = 6                    # paginas distintas {7,0,1,2,3,4} -> fallos forzosos
    resultados = {}
    for alg in ("fifo", "lru", "optimo", "reloj"):
        fallos, total = _fallos_de(alg)
        assert total == n_refs, f"{alg}: deben procesarse {n_refs} accesos"
        assert distintas <= fallos <= n_refs, f"{alg}: fallos fuera de rango"
        resultados[alg] = fallos
    # OPTIMO es la cota minima teorica de Belady.
    assert resultados["optimo"] <= resultados["fifo"]
    assert resultados["optimo"] <= resultados["lru"]
    assert resultados["optimo"] <= resultados["reloj"]


def test_optimo_no_peor_que_marcos_infinitos():
    # Con tantos marcos como paginas distintas no debe haber reemplazos:
    # los fallos son exactamente las paginas distintas (fallos forzosos).
    cfg = presets.cargar("page_faults")
    cfg.num_marcos = 10
    w = correr(World(cfg))
    assert w.mmu.fallos == 6
