"""
Testes unitários para app/services/calculations.py
Validação de multiplicadores de sub-tipo de esporte
"""

import sys
from pathlib import Path

# Resolver importação do pacote
workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root))

# Importação direta do arquivo para evitar cadeias de dependências do pacote
import importlib.util
calc_spec = importlib.util.spec_from_file_location(
    "calculations",
    workspace_root / "app" / "services" / "calculations.py"
)
calculations = importlib.util.module_from_spec(calc_spec)
calc_spec.loader.exec_module(calculations)

apply_sub_type_multipliers = calculations.apply_sub_type_multipliers
FUTSAL_MULTIPLIERS = calculations.FUTSAL_MULTIPLIERS
SOCIETY_MULTIPLIERS = calculations.SOCIETY_MULTIPLIERS
FOOTBALL_ATTRIBUTE_TO_PACKAGE = calculations.FOOTBALL_ATTRIBUTE_TO_PACKAGE


def test_futsal_multipliers_exist():
    """FUTSAL: Multiplicadores devem estar definidos."""
    assert "agility" in FUTSAL_MULTIPLIERS
    assert FUTSAL_MULTIPLIERS["agility"] == 1.2
    assert FUTSAL_MULTIPLIERS["ball_control"] == 1.2
    assert FUTSAL_MULTIPLIERS["stamina"] == 0.8
    print("✓ FUTSAL multiplicadores definidos corretamente")


def test_society_multipliers_exist():
    """SOCIETY: Multiplicadores devem estar definidos."""
    assert "long_shot" in SOCIETY_MULTIPLIERS
    assert SOCIETY_MULTIPLIERS["long_shot"] == 1.1
    assert SOCIETY_MULTIPLIERS["strength"] == 1.1
    print("✓ SOCIETY multiplicadores definidos corretamente")


def test_attribute_to_package_mapping():
    """Verificar se atributos estão mapeados para pacotes."""
    assert FOOTBALL_ATTRIBUTE_TO_PACKAGE["agility"] == "mobilidade"
    assert FOOTBALL_ATTRIBUTE_TO_PACKAGE["ball_control"] == "criacao"
    assert FOOTBALL_ATTRIBUTE_TO_PACKAGE["stamina"] == "fisico"
    assert FOOTBALL_ATTRIBUTE_TO_PACKAGE["long_shot"] == "finalizacao"
    assert FOOTBALL_ATTRIBUTE_TO_PACKAGE["strength"] == "fisico"
    print("✓ Mapeamento atributo->pacote correto")


def test_apply_futsal_multipliers_increases_agility():
    """FUTSAL: Agilidade deve aumentar em 20%."""
    package_scores = {
        "finalizacao": 66.0,
        "mobilidade": 70.0,  # Começa com 70
        "fisico": 70.0,
        "criacao": 70.0,
        "defesa": 70.0,
    }
    available_attributes = {
        "agility": 70,
        "ball_control": 70,
        "stamina": 70,
        "long_shot": 50,
        "strength": 50,
    }
    
    adjusted = apply_sub_type_multipliers(
        package_scores,
        available_attributes,
        sub_type="futsal",
        sport_type="football",
    )
    
    # Mobilidade contém agility → deve aumentar
    assert adjusted["mobilidade"] > package_scores["mobilidade"]
    print(f"✓ FUTSAL: Mobilidade aumentou de {package_scores['mobilidade']} para {adjusted['mobilidade']:.2f}")


def test_apply_futsal_multipliers_decreases_stamina():
    """FUTSAL: Fisico (stamina) deve diminuir em 20%."""
    package_scores = {
        "finalizacao": 70.0,
        "mobilidade": 70.0,
        "fisico": 75.0,  # Começa com 75
        "criacao": 70.0,
        "defesa": 70.0,
    }
    available_attributes = {
        "agility": 70,
        "ball_control": 70,
        "stamina": 75,
        "long_shot": 50,
        "strength": 50,
    }
    
    adjusted = apply_sub_type_multipliers(
        package_scores,
        available_attributes,
        sub_type="futsal",
        sport_type="football",
    )
    
    # Fisico contém stamina → deve diminuir
    assert adjusted["fisico"] < package_scores["fisico"]
    print(f"✓ FUTSAL: Físico diminuiu de {package_scores['fisico']} para {adjusted['fisico']:.2f}")


def test_apply_society_multipliers_increases_finishing():
    """SOCIETY: Finalização (long_shot) deve aumentar em 10%."""
    package_scores = {
        "finalizacao": 70.0,
        "mobilidade": 70.0,
        "fisico": 70.0,
        "criacao": 70.0,
        "defesa": 70.0,
    }
    available_attributes = {
        "agility": 70,
        "ball_control": 70,
        "stamina": 70,
        "long_shot": 70,  # Começa com 70
        "strength": 50,
    }
    
    adjusted = apply_sub_type_multipliers(
        package_scores,
        available_attributes,
        sub_type="society",
        sport_type="football",
    )
    
    # Finalização contém long_shot → deve aumentar
    assert adjusted["finalizacao"] > package_scores["finalizacao"]
    print(f"✓ SOCIETY: Finalização aumentou de {package_scores['finalizacao']} para {adjusted['finalizacao']:.2f}")


def test_apply_society_multipliers_increases_physical():
    """SOCIETY: Físico (strength) deve aumentar em 10%."""
    package_scores = {
        "finalizacao": 70.0,
        "mobilidade": 70.0,
        "fisico": 70.0,  # Começa com 70
        "criacao": 70.0,
        "defesa": 70.0,
    }
    available_attributes = {
        "agility": 70,
        "ball_control": 70,
        "stamina": 70,
        "long_shot": 50,
        "strength": 70,  # Começa com 70
    }
    
    adjusted = apply_sub_type_multipliers(
        package_scores,
        available_attributes,
        sub_type="society",
        sport_type="football",
    )
    
    # Físico contém strength → deve aumentar
    assert adjusted["fisico"] > package_scores["fisico"]
    print(f"✓ SOCIETY: Físico aumentou de {package_scores['fisico']} para {adjusted['fisico']:.2f}")


def test_field_no_multipliers():
    """FIELD: Sem multiplicadores, scores devem permanecer iguais."""
    package_scores = {
        "finalizacao": 70.0,
        "mobilidade": 70.0,
        "fisico": 70.0,
        "criacao": 70.0,
        "defesa": 70.0,
    }
    available_attributes = {
        "agility": 70,
        "ball_control": 70,
        "stamina": 70,
        "long_shot": 70,
        "strength": 70,
    }
    
    adjusted = apply_sub_type_multipliers(
        package_scores,
        available_attributes,
        sub_type="field",
        sport_type="football",
    )
    
    # Nenhum multiplicador → devem ser iguais
    for pkg_name in package_scores:
        assert abs(adjusted[pkg_name] - package_scores[pkg_name]) < 0.01
    print("✓ FIELD: Nenhum multiplicador aplicado (scores iguais)")


def test_no_sub_type_no_multipliers():
    """Sem sub_type: Nenhum multiplicador deve ser aplicado."""
    package_scores = {
        "finalizacao": 70.0,
        "mobilidade": 70.0,
        "fisico": 70.0,
        "criacao": 70.0,
        "defesa": 70.0,
    }
    available_attributes = {
        "agility": 70,
        "ball_control": 70,
        "stamina": 70,
        "long_shot": 70,
        "strength": 70,
    }
    
    adjusted = apply_sub_type_multipliers(
        package_scores,
        available_attributes,
        sub_type=None,
        sport_type="football",
    )
    
    # Sem sub_type → devem ser iguais
    for pkg_name in package_scores:
        assert abs(adjusted[pkg_name] - package_scores[pkg_name]) < 0.01
    print("✓ Sem sub_type: Nenhum multiplicador aplicado")


def test_scores_bounded_0_99():
    """Scores não devem sair do intervalo [0, 99]."""
    package_scores = {
        "finalizacao": 90.0,  # Alto
        "mobilidade": 95.0,   # Muito alto
        "fisico": 5.0,        # Muito baixo
        "criacao": 0.0,       # Mínimo
        "defesa": 99.0,       # Máximo
    }
    available_attributes = {
        "agility": 90,       # Vai ser multiplicado por 1.2 em FUTSAL
        "ball_control": 95,
        "stamina": 5,
        "long_shot": 0,
        "strength": 99,
    }
    
    adjusted = apply_sub_type_multipliers(
        package_scores,
        available_attributes,
        sub_type="futsal",
        sport_type="football",
    )
    
    # Verificar limites
    for pkg_name, score in adjusted.items():
        assert 0 <= score <= 99, f"{pkg_name} fora de limites: {score}"
    print("✓ Todos os scores estão no intervalo [0, 99]")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("TESTES: Domain - Soccer Variations (Multiplicadores de Sub-Tipo)")
    print("="*70 + "\n")
    
    test_futsal_multipliers_exist()
    test_society_multipliers_exist()
    test_attribute_to_package_mapping()
    test_apply_futsal_multipliers_increases_agility()
    test_apply_futsal_multipliers_decreases_stamina()
    test_apply_society_multipliers_increases_finishing()
    test_apply_society_multipliers_increases_physical()
    test_field_no_multipliers()
    test_no_sub_type_no_multipliers()
    test_scores_bounded_0_99()
    
    print("\n" + "="*70)
    print("✅ TODOS OS TESTES PASSARAM!")
    print("="*70 + "\n")
