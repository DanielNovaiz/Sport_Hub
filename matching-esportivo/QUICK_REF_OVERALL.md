# Quick Reference - Overall Calculation Functions

## 🚀 Uso Rápido

### Futebol

```python
from app.services.xp_service import calculate_football_overall

# Calcular overall de um jogador
stats = {"short_finish": 85, "long_shot": 80, ...}
overall = calculate_football_overall("meia", stats)  # → 84

# Posições disponíveis
"atacante" | "ponta" | "lateral" | "meia" | "zagueiro" | "goleiro" | "sem_posicao"
```

### Vôlei

```python
from app.services.xp_service import calculate_volleyball_overall

# Calcular overall de um jogador
stats = {"spike_power": 88, "reaction": 87, ...}
overall = calculate_volleyball_overall("ponteiro", stats)  # → 88

# Posições disponíveis
"levantador" | "ponteiro" | "central" | "oposto" | "libero" | "sem_posicao"
```

---

## 📋 Mapeamento de Posições

### ⚽ Futebol → Aliases
```
"atacante"   ← forward, fw, st
"ponta"      ← wing, winger, rw, lw
"lateral"    ← back, fullback, rb, lb
"meia"       ← midfielder, cm, cdm, cam
"zagueiro"   ← defender, cb
"goleiro"    ← goalkeeper, gk, portero
```

### 🏐 Vôlei → Aliases
```
"levantador" ← setter
"ponteiro"   ← wing_spiker, ws
"central"    ← middle_blocker, mb
"oposto"     ← opposite, op
"libero"     ← liber0, libera, ds
```

---

## 🎮 SubType Multiplicadores

### FUTSAL (Futebol Sala)
```python
match = MatchPerformance(
    sport_type="football",
    sub_type="FUTSAL",  # ← 1.2x em agility + ball_control
)
```

### 3x3 (Basquete adaptado)
```python
match = MatchPerformance(
    sport_type="basketball",
    sub_type="3x3",  # ← 2.0x em shoot_long
)
```

---

## 🔧 Função Completa vs. Simplificada

### Com Dict (Simples)
```python
stats = {"short_finish": 80, "long_shot": 75, ...}
overall = calculate_football_overall("meia", stats)  # int (0-99)
```

### Com PlayerStats Object
```python
player = PlayerStats(position="meia", short_finish=80, ...)
overall = calculate_football_overall(player.position, player)  # int (0-99)
```

### Com Pacotes por Position
```python
result = calculate_football_overall_by_position("meia", stats)
# {
#   "position": "meia",
#   "overall": 84,
#   "packages": {
#     "finalizacao": 78,
#     "mobilidade": 85,
#     "fisico": 81,
#     "criacao": 87,
#     "defesa": 70
#   }
# }
```

---

## ✅ Checklist de Integração

- [ ] Importar função: `from app.services.xp_service import calculate_football_overall`
- [ ] Passar position como string (lowercase, será normalizado)
- [ ] Passar stats como dict ou PlayerStats object
- [ ] Sub_type opcional, só aplicado se fornecido
- [ ] Overall sempre 0-99
- [ ] Testes em `tests/test_football_volleyball_overall.py`

---

## 🐛 Troubleshooting

| Problema | Solução |
|----------|---------|
| `position not found` | Use alias (ex: "midfielder" → "meia") |
| `overall = 0` | Verifique se stats tem valores (default 0-99) |
| `sub_type não aplicado` | Confirme que está em sport_type correto |
| `KeyError em packages` | Verifique se todos os atributos estão em stats |

---

## 📊 Peso Total por Esporte

### Futebol - 5 Posições
```
Atacante:  (3+2+1.5+0.8+0.7) / 8.0 = 1.0 (peso total normalizado)
Ponta:     (2.5+3+2+1.2+0.2) / 9.2 = 1.0
Lateral:   (0.8+2+2.5+2+3) / 9.5 = 1.0
Meia:      (1.5+2.5+1.8+3+1.2) / 9.0 = 1.0
Zagueiro:  (0.5+1.5+2.5+1+3.5) / 8.0 = 1.0
Goleiro:   (0+1+2.5+0.5+3.5) / 8.0 = 1.0
```

### Vôlei - 5 Posições
```
Levantador: (2+2+1.5+3.5+1.5) / 8.0 = 1.0
Ponteiro:   (3+2.5+1.5+0.5+2) / 8.5 = 1.0
Central:    (2.5+1.5+3+1+2.5) / 9.0 = 1.0
Oposto:     (3+2+1.5+0.5+2) / 8.0 = 1.0
Líbero:     (0.5+1+3.5+1+3) / 8.5 = 1.0
```

---

## 🎯 Casos de Uso Comuns

### Case 1: Carregar Perfil de Jogador
```python
# Em get_user_profile_card() do user_service
overall = _calculate_overall_for_sport(sport_type, stats)
# Roteia automaticamente para funcao correta baseada em sport_type
```

### Case 2: Registrar Performance de Match
```python
# Em apply_match_progression() do xp_service
stats.overall = calculate_football_overall(stats.position, stats, sub_type)
```

### Case 3: Analisar Multi-Esporte
```python
# Mesmo jogador, diferentes esportes
player_stats = PlayerStats(...)

futebol = calculate_football_overall("ponta", player_stats)
volei = calculate_volleyball_overall("ponteiro", player_stats)
basket = calculate_basketball_overall("ala", player_stats)

best_sport = max([
    ("futebol", futebol),
    ("volei", volei),
    ("basket", basket)
], key=lambda x: x[1])

print(f"Melhor esporte: {best_sport[0]} (overall {best_sport[1]})")
```

---

## 📌 Pontos Críticos

1. **Position é Case-Insensitive**: "MEIA", "meia", "Meia" → todas normalizam para "meia"
2. **Spaces são Tratados**: "sem posição" → "sem_posicao"
3. **Modo Flex Automático**: "sem_posicao" OU "rodizio" → divisor = 5 (média simples)
4. **Overall Sempre Clamped**: max(0, min(99, overall))
5. **Sub_type Case-Insensitive**: "futsal", "FUTSAL", "Futsal" → todos funcionam
6. **Atributos Faltando**: Defaults to 0, não gera erro

---

## 🔌 API Contract

### `calculate_football_overall(position: str, source: dict | PlayerStats, sub_type: str | None = None) -> int`

**Retorna:** Overall entre 0 e 99

**Lança:** Nenhuma exceção (valores defaults aplicados)

### `calculate_volleyball_overall(position: str | None = None, source: dict | PlayerStats | None = None, **kwargs) -> int`

**Retorna:** Overall entre 0 e 99

**Modo 1:** `calculate_volleyball_overall("levantador", stats)`  
**Modo 2:** `calculate_volleyball_overall(source=stats)`  
**Modo 3:** `calculate_volleyball_overall(stats)` ← Compatibilidade antiga

---

## 📚 Arquivos Relacionados

- `app/services/xp_service.py` - Implementa funções
- `app/services/user_service.py` - Usa em `_calculate_overall_for_sport()`
- `tests/test_football_volleyball_overall.py` - 20+ testes
- `FOOTBALL_VOLLEYBALL_OVERALL.md` - Documentação técnica
- `EXEMPLOS_OVERALL.md` - Exemplos práticos de código

---

**Criado em:** Abril 14, 2026  
**Versão:** 1.0  
**Status:** Production Ready
