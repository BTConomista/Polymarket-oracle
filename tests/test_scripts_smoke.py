"""Controlli statici su TUTTI gli script di `scripts/` (audit Fase 101).

Perche' esiste: la suite e' passata verde mentre 32 script migrati dal cantiere
non partivano — `ROOT` puntava a `parents[2]` (una cartella sopra il repo) e i
percorsi contenevano ancora il segmento `cantiere/`. Nessun test toccava
`scripts/`, quindi il buco non poteva essere visto.

Sono controlli STATICI: niente esecuzione, niente rete, niente dati. Costano
millisecondi e catturano proprio la classe di difetto che era sfuggita.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SCRIPTS = sorted(p for p in (ROOT / "scripts").glob("*.py"))


def test_ci_sono_script_da_controllare():
    """Guardia contro un test che passa perche' non guarda nulla."""
    assert len(SCRIPTS) > 100, f"solo {len(SCRIPTS)} script trovati in scripts/"


@pytest.mark.parametrize("path", SCRIPTS, ids=lambda p: p.name)
def test_sintassi_valida(path: Path):
    ast.parse(path.read_text(), filename=str(path))


@pytest.mark.parametrize("path", SCRIPTS, ids=lambda p: p.name)
def test_root_risolve_alla_radice_del_repo(path: Path):
    """Ogni `Path(__file__).resolve().parents[N]` in scripts/ deve avere N == 1.

    Uno script in `scripts/` dista UN livello dalla radice. `parents[2]` era
    corretto quando gli stessi file vivevano in `cantiere/scripts/`, e li' e'
    rimasto dopo lo spostamento: il risultato era una ROOT fuori dal repo.
    """
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Subscript)
                and isinstance(node.value, ast.Attribute)
                and node.value.attr == "parents"):
            continue
        if not isinstance(node.slice, ast.Constant):
            continue          # indice calcolato: non giudicabile staticamente
        assert node.slice.value == 1, (
            f"{path.name}: parents[{node.slice.value}] — uno script in "
            f"scripts/ dista un livello dalla radice, atteso parents[1]")


@pytest.mark.parametrize("path", SCRIPTS, ids=lambda p: p.name)
def test_root_non_e_un_percorso_assoluto_cablato(path: Path):
    """Nessun `ROOT = Path("/home/...")`: i numeri devono essere rifacibili da
    terzi (CLAUDE.md §1.5), e una copia del repo altrove non deve scrivere
    dentro il repo originale."""
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        nomi = {t.id for t in node.targets if isinstance(t, ast.Name)}
        if "ROOT" not in nomi:
            continue
        for arg in ast.walk(node.value):
            if (isinstance(arg, ast.Constant) and isinstance(arg.value, str)
                    and arg.value.startswith("/")):
                pytest.fail(f"{path.name}: ROOT cablato su {arg.value!r}")


@pytest.mark.parametrize("path", SCRIPTS, ids=lambda p: p.name)
def test_nessun_percorso_cantiere(path: Path):
    """Nessun join di percorso contiene ancora il segmento `cantiere`.

    Si guardano solo le stringhe che SONO un pezzo di percorso — il segmento
    esatto `"cantiere"` (come in `ROOT / "cantiere" / "scripts"`) o un prefisso
    `cantiere/` — non la parola in mezzo alla prosa: la storia del cantiere si
    racconta, non si percorre.
    """
    tree = ast.parse(path.read_text(), filename=str(path))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            d = ast.get_docstring(node, clean=False)
            if d is not None:
                docstrings.add(d)
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            continue
        if node.value in docstrings:
            continue
        v = node.value.strip().lower()
        assert v != "cantiere" and "cantiere/" not in v, (
            f"{path.name}: percorso residuo del cantiere in {node.value!r}")
