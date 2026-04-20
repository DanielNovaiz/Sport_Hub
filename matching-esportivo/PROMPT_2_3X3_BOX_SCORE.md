"""
# PROMPT 2: DOMAIN - BASKETBALL 3X3 BOX SCORE CONVERSION

## Contexto Técnico
Implementação de conversão de Box Score para Basquete 3x3 com multiplicadores específicos:
- Cestas de fora do arco (2pts): 2.5x mais XP em long_range_shot vs cestas de 1pt
- Clutch rebounds (último minuto): +50% XP adicional

## Requisitos Funcionais (Conforme Especificação)

### Parâmetro 1: Cestas de 2-Pontos (Fora do Arco)
- **Multiplicador:** 2.5x
- **Aplicação:** Comparar XP gerado por cestas de 2pts vs 1pt
  - 1pt: X XP → long_range_shot
  - 2pt: 2.5 * X XP → long_range_shot
- **Cálculo Base:**
  - 1 cesta de 1pt = 1 ponto * 3 XP/ponto = 3 XP
  - 1 cesta de 2pts = 2 pontos * 2 XP/ponto = 4 XP
  - Bonus 2pt: 4 * (2.5 - 1.0) = 4 * 1.5 = 6 XP adicional

### Parâmetro 2: Clutch Rebounds (Último Minuto)
- **Multiplicador:** +50% de XP
- **Aplicação:** Rebotes capturados nos últimos minutos da partida
- **Cálculo:**
  - Se total_xp = 100 e clutch_rebound_count/total_rebounds = 0.5
  - Clutch bonus = 100 * 0.5 * 0.5 = 25 XP

## Arquitetura Implementada

### 1. Modelo Expandido (app/models/player_stats.py)
Adicionado 3 campos ao MatchPerformance:
```python
# Box score basquete 3x3 (específico)
two_point_makes: int = Field(default=0, ge=0, description="Cestas de 2pts (fora do arco)")
clutch_rebounds: int = Field(default=0, ge=0, description="Rebotes no último minuto")
last_minute_timestamp_sec: int | None = Field(default=None, description="Timestamp em segundos")
```

### 2. Método Principal (app/services/xp_service.py)
```python
def process_3x3_performance(performance: MatchPerformance) -> dict[str, Any]:
    """Processa performance de Basquete 3x3 com multiplicadores específicos."""
    
    # Fluxo:
    # 1. Validar sport_type="basketball" e sub_type="3x3"
    # 2. Calcula XP base (pontos, assists, rebounds, steals, blocks)
    # 3. Aplica multiplicador 2.5x para two_point_makes
    # 4. Aplica bônus +50% para clutch_rebounds
    # 5. Retorna breakdown completo de XP
```

**Saídas:**
```python
{
    "base_xp": int,                    # XP sem multiplicadores
    "two_point_multiplier": float,     # 2.5
    "two_point_bonus_xp": int,         # Bonus apenas de 2-pontos
    "clutch_bonus_xp": int,            # Bonus apenas de clutch
    "total_xp": int,                   # base + two_point_bonus + clutch_bonus
    "details": str                     # Log estruturado
}
```

## Cálculos Detalhados

### Base XP por ação:
```python
base_xp = (
    (points - two_point_makes*2) * 3 +  # Pontos de 1pt
    two_point_makes * 2 * 2 +            # Pontos de 2pt
    assists * 10 +
    rebounds * 4 +
    steals * 8 +
    blocks * 6
)
```

### 2-Ponto Bonus:
```python
two_point_bonus = two_point_makes * 2 * (2.5 - 1.0)
                = two_point_makes * 2 * 1.5
```

### Clutch Bonus (Condicional):
```python
if total_rebounds > 0:
    clutch_bonus = (base_xp + two_point_bonus) * 0.5 * (clutch_rebounds / total_rebounds)
else:
    clutch_bonus = 0
```

## Casos de Teste (Validação)

| Caso | Points | 2-Pts | Rebounds | Clutch | Base XP | 2-Pt Bonus | Clutch Bonus | Total |
|------|--------|-------|----------|--------|---------|----------|--------------|-------|
| Base only | 10 | 0 | 3 | 0 | 80 | 0 | 0 | 80 |
| 2-point only | 6 | 1 | 1 | 0 | 20 | 3 | 0 | 23 |
| Clutch only | 10 | 0 | 3 | 3 | 62 | 0 | 31 | 93 |
| Mixed | 12 | 2 | 5 | 3 | 104 | 6 | 33 | 143 |
| Partial clutch | 10 | 0 | 10 | 2 | 80 | 0 | 8 | 88 |
| No rebounds | 15 | 0 | 0 | 3 | 85 | 0 | 0 | 85 |
| Non-3x3 | - | - | - | - | 0 | 0 | 0 | 0 |

## Integração no Fluxo de XP

1. Endpoint POST `/api/ranked/box-score` recebe MatchPerformance com 3x3 fields
2. `submit_box_score()` → `apply_match_progression()` → `distribute_match_xp()`
3. `distribute_match_xp()` pode chamar `process_3x3_performance()` se sub_type=="3x3"
4. XP retornado é aplicado aos atributos conforme pacotes (fisico, armacao, etc)

## Invariantes de Segurança
- Sem rebounds → clutch_bonus = 0 (edge case protection)
- Clamping automático em [0-99] para todos os scores
- Validação sport_type e sub_type obrigatória
- Total_xp nunca será negativo

## Próximos Passos (Sugestões)
1. Integrar com `distribute_match_xp()` para aplicar automaticamente
2. Adicionar UI no Flutter para visualizar breakdown de XP
3. Implementar historical tracking de 2-pontos vs 1-ponto
4. Expandir para outras variaçõesc (FIBA, street ball, etc)

## Arquivos Alterados/Criados
- `app/models/player_stats.py` ✓ (3 campos adicionados)
- `app/services/xp_service.py` ✓ (processo_3x3_performance implementado)
- `tests/test_3x3_performance.py` ✓ (testes unitários)
- `tests/test_3x3_standalone.py` ✓ (testes sem dependências SQLModel)
"""
