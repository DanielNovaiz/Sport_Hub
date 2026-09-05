"""
Guard de arquitetura de imports — Fase 0 do plano de refatoração.

Objetivos (conforme PLANO_REFATORACAO_BACKEND.md, F0/F3 e achados V4):
  1. Detectar ciclos de import ENTRE módulos de ``app/services/``, cobrindo imports no
     topo do arquivo E dentro de funções/métodos (lazy). A análise é estática (AST):
     o teste NÃO importa os módulos sob teste (evita disparar o próprio SCC e não exige
     as dependências de runtime do app).
  2. Detectar inversão de camada: QUALQUER arquivo em ``app/repositories/`` que importe
     algo de ``app/services/`` (dados não podem depender de negócio).

Só usa a biblioteca padrão (ast, pathlib). No estado atual do código este teste DEVE
FALHAR até as Fases 3 e 4 serem executadas, acusando exatamente:
  - SCC {xp_service, overall_engine, user_service} (ciclo em app/services/);
  - ``xp_repository → achievement_service`` (repo importando service).
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICES_DIR = ROOT / "app" / "services"
REPOSITORIES_DIR = ROOT / "app" / "repositories"
DOMAIN_DIR = ROOT / "app" / "domain"

SERVICE_PREFIX = "app.services"
REPOSITORY_PREFIX = "app.repositories"
DOMAIN_PREFIX = "app.domain"

def _iter_py_files(directory: Path) -> list[Path]:
    """Arquivos .py (exceto __init__) de um diretório, ordenados p/ reprodutibilidade."""
    if not directory.is_dir():
        return []
    return sorted(fp for fp in directory.glob("*.py") if fp.is_file() and fp.name != "__init__.py")


def _module_slug(path: Path) -> str:
    """De 'app/services/xp_service.py' gera o rótulo de nó 'app.services.xp_service'."""
    relative = path.relative_to(ROOT / "app")
    parts = relative.parts[:-1] + (relative.stem,)
    return ".".join(("app",) + parts)


def _internal_import_targets(source: str) -> set[str]:
    """Alvos internos (app.services.X / app.repositories.X) presentes no source.

    Percorre o AST INTEIRO (ast.walk) para capturar imports dentro de funções. Cobre
    ``from app.services.x import Y`` e ``import app.services.x``. ``from app import ...``
    sem submódulo concreto é ignorado.
    """
    tree = ast.parse(source)
    targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for prefix in (SERVICE_PREFIX, REPOSITORY_PREFIX, DOMAIN_PREFIX):
                if module == prefix or module.startswith(prefix + "."):
                    targets.add(module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                for prefix in (SERVICE_PREFIX, REPOSITORY_PREFIX, DOMAIN_PREFIX):
                    if name == prefix or name.startswith(prefix + "."):
                        targets.add(name)
    # Exige target concreto: `app.services.<x>` / `app.repositories.<x>` / `app.domain.<x>`.
    return {t for t in targets if t.count(".") >= 2}


def _service_files() -> dict[str, Path]:
    return {_module_slug(p): p for p in _iter_py_files(SERVICES_DIR)}


def _repo_files() -> dict[str, Path]:
    return {_module_slug(p): p for p in _iter_py_files(REPOSITORIES_DIR)}


def _domain_files() -> dict[str, Path]:
    return {_module_slug(p): p for p in _iter_py_files(DOMAIN_DIR)}


def _find_cycle(adjacency: dict[str, set[str]]) -> tuple[bool, list[str]]:
    """Primeiro ciclo no dígrafo -> (encontrado, caminho). DFS com caminho-atual (gray)."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {}

    def dfs(node: str) -> tuple[bool, list[str]]:
        color[node] = GRAY
        for neighbor in sorted(adjacency.get(node, ())):
            if neighbor not in color:
                color[neighbor] = WHITE
            if color[neighbor] == GRAY:
                return True, [node, neighbor]
            if color[neighbor] == WHITE:
                found, path = dfs(neighbor)
                if found:
                    return True, [node] + path
        color[node] = BLACK
        return False, []

    for start in sorted(adjacency):
        if color.get(start, WHITE) == WHITE:
            found, path = dfs(start)
            if found:
                return True, path
    return False, []


def test_services_have_no_import_cycles() -> None:
    """Não deve existir ciclo de imports em app/services/ (top-level OU lazy)."""
    service_files = _service_files()
    assert service_files, "nenhum arquivo de service encontrado para análise"
    service_slugs = set(service_files)

    adjacency: dict[str, set[str]] = {slug: set() for slug in service_slugs}
    for slug, path in service_files.items():
        source = path.read_text(encoding="utf-8")
        for target in _internal_import_targets(source):
            if not target.startswith(SERVICE_PREFIX + "."):
                continue
            # target tem a forma `app.services.<modulo>`; nós de services são esses mesmos rótulos.
            if target in service_slugs and target != slug:
                adjacency[slug].add(target)

    has_cycle, cycle_path = _find_cycle(adjacency)
    assert not has_cycle, (
        "CICLO de imports detectado em app/services/ (o grafo precisa virar um DAG):\n"
        "  caminho: "
        + " -> ".join(cycle_path)
        + "\n  Esperado até a Fase 4: SCC {xp_service, overall_engine, user_service}."
    )


def test_repositories_never_import_services() -> None:
    """app/repositories/ não pode depender de app/services/ (inversão de camada, Fase 3)."""
    repo_files = _repo_files()
    assert repo_files, "nenhum arquivo de repositório encontrado para análise"

    violations: list[str] = []
    for slug, path in repo_files.items():
        source = path.read_text(encoding="utf-8")
        for target in _internal_import_targets(source):
            if target.startswith(SERVICE_PREFIX + "."):
                violations.append(f"{slug} -> {target}")

    assert not violations, (
        "INVERSÃO de camada detectada em app/repositories/ (não pode importar services):\n"
        + "\n".join("  " + v for v in sorted(violations))
        + "\n  Esperado até a Fase 3: xp_repository -> achievement_service."
    )


def test_domain_never_imports_services_or_repositories() -> None:
    """app/domain/ é código puro: não pode depender de app/services/ nem app/repositories/."""
    domain_files = _domain_files()
    assert domain_files, "nenhum arquivo de domínio encontrado para análise"

    violations: list[str] = []
    for slug, path in domain_files.items():
        source = path.read_text(encoding="utf-8")
        for target in _internal_import_targets(source):
            if target.startswith(SERVICE_PREFIX + ".") or target.startswith(REPOSITORY_PREFIX + "."):
                violations.append(f"{slug} -> {target}")

    assert not violations, (
        "app/domain/ não pode importar de services/ ou repositories/ (deve ser código puro):\n"
        + "\n".join("  " + v for v in sorted(violations))
    )
