"""
# PROMPT 1: DOMAIN - SOCCER VARIATIONS (FUTSAL & SOCIETY)

## Contexto Técnico
Implementação de sub-modelos de futebol com multiplicadores de atributos específicos 
para variações do jogo (FUTSAL, SOCIETY) no motor de cálculo de Overall.

## Requisitos Funcionais (Conforme Especificação)

### SUB_TYPE == "FUTSAL"
- **Multiplicadores:** 
  - agility (mobilidade): +20% (multiplicador 1.2x)
  - ball_control (criação): +20% (multiplicador 1.2x)
  - stamina (físico): -20% (multiplicador 0.8x)
- **Justificativa:** Futsal exige maior agilidade e controle em espaços reduzidos, mas gasta mais energia.

### SUB_TYPE == "SOCIETY"
- **Multiplicadores:**
  - long_shot (finalização): +10% (multiplicador 1.1x)
  - strength (físico): +10% (multiplicador 1.1x)
- **Justificativa:** Futebol de society (7x7) favorece finalizações de distância e força.

### Campo padrão (FIELD)
- **Multiplicadores:** Nenhum (1.0x em todos os atributos)

## Arquitetura Implementada

### 1. Enumerações (app/core/enums.py)
```python
class FootballSubType(str, Enum):
    FUTSAL = "futsal"
    SOCIETY = "society"
    FIELD = "field"

# Tipo dinâmico para validação
SportSubType = Literal["futsal", "society", "field", ...]
```

### 2. Motor de Cálculos (app/services/calculations.py)
**Responsabilidades:**
- Manter dicionários de multiplicadores por esporte/sub_type
- Mapear atributos para seus pacotes pai (FOOTBALL_ATTRIBUTE_TO_PACKAGE)
- Aplicar multiplicadores via `apply_sub_type_multipliers()`

**Função Principal:**
```python
def apply_sub_type_multipliers(
    package_scores: dict[str, float],
    available_attributes: dict[str, int],
    sub_type: str | None = None,
    sport_type: str | None = None,
) -> dict[str, float]:
    """
    Fluxo:
    1. Busca multiplicadores para (sport_type, sub_type)
    2. Para cada atributo afetado, calcula impacto (delta)
    3. Injeta impacto no pacote pai do atributo
    4. Retorna package_scores ajustados
    """
```

### 3. Integração em XP Service (app/services/xp_service.py)
**Função Modificada:**
```python
def calculate_football_overall(
    position: str,
    source: PlayerStats,
    sub_type: str | None = None
) -> int:
    # 1. Calcular scores de pacotes
    package_scores = calculate_football_package_scores(source)
    
    # 2. Extrair atributos relevantes para multiplicadores
    relevant_attrs = {
        "agility": _get_stat_value(source, "agility"),
        "ball_control": _get_stat_value(source, "ball_control"),
        ...
    }
    
    # 3. INJETAR multiplicadores de sub_type (PASSO CRÍTICO)
    adjusted_packages = apply_sub_type_multipliers(
        package_scores,
        relevant_attrs,
        sub_type=sub_type,
        sport_type="football",
    )
    
    # 4. Usar scores AJUSTADOS para weighted_sum
    weighted_sum = sum(
        adjusted_packages.get(name, original) * weight
        for name, weight in weights.items()
    )
    
    # 5. Retornar overall final
    return calculate_precise_overall(weighted_sum, divisor)
```

## Casos de Teste (Validação)

### Teste 1: FUTSAL com atacante (agility-heavy)
- Position: "atacante" (weight agility 2.0x na decisão final)
- Base agility: 70
- After FUTSAL multiplier: 70 × 1.2 = 84
- Expected: overall deve aumentar

### Teste 2: FUTSAL com goleiro (stamina-heavy)
- Position: "goleiro"
- Base stamina: 75
- After FUTSAL multiplier: 75 × 0.8 = 60
- Expected: overall deve DIMINUIR (goleiro sofre com stamina reduzida)

### Teste 3: SOCIETY com atacante
- Position: "atacante"
- Base long_shot: 65, strength: 60
- After SOCIETY: 65 × 1.1 = 71.5, 60 × 1.1 = 66
- Expected: overall aumento moderado

## Invariante de Segurança
- Todos os scores permanecem entre 0-99
- Clamping automático: `max(0, min(99, adjusted_score))`
- Multiplicadores são compostos additivamente por pacote

## Próximos Passos (Sugestões)
1. Expandir com basketball sub_types (3x3 vs 5x5)
2. Expandir com volleyball sub_types (beach vs indoor)
3. Implementar UI no mobile para exibir multiplicadores aplicados
4. Adicionar histórico de cálculos para debug/telemetria
"""
