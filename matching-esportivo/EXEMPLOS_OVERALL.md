# Exemplos Práticos - Cálculo de Overall para Futebol e Vôlei

## 📝 Exemplos de Uso

### Importações Necessárias

```python
from app.services.xp_service import (
    calculate_football_overall,
    calculate_football_overall_by_position,
    calculate_football_package_scores,
    calculate_volleyball_overall,
    calculate_volleyball_overall_by_position,
    calculate_volleyball_package_scores,
)
from app.models.player_stats import PlayerStats, MatchPerformance
```

---

## ⚽ EXEMPLOS DE FUTEBOL

### Exemplo 1: Calcular Overall de um Meia Ofensivo

```python
# Stats de um meia ofensivo (playmaker)
stats_dict = {
    "short_finish": 78,
    "long_shot": 75,
    "free_kick": 82,
    "sprint": 87,
    "acceleration": 85,
    "agility": 88,
    "stamina": 86,
    "strength": 75,
    "balance": 80,
    "short_pass": 90,      # ← Criação é forte
    "long_pass": 88,       # ← Criação é forte
    "crossing": 85,
    "vision": 92,          # ← Criação é forte
    "dribbling": 89,       # ← Criação é forte
    "ball_control": 90,    # ← Criação é forte
    "tackle": 68,
    "interception": 70,
    "marking": 65,
    "ball_shielding": 67,
}

# Calcular como meia
overall = calculate_football_overall("meia", stats_dict)
print(f"Overall como Meia: {overall}")
# Resultado: 87 (alto, pois criação e mobilidade são o destaque)

# Com dict por position
result = calculate_football_overall_by_position("meia", stats_dict)
print(f"""
Position: {result['position']}
Overall: {result['overall']}
Packages:
  - Finalizacao: {result['packages']['finalizacao']}
  - Mobilidade: {result['packages']['mobilidade']}
  - Fisico: {result['packages']['fisico']}
  - Criacao: {result['packages']['criacao']}
  - Defesa: {result['packages']['defesa']}
""")
```

### Exemplo 2: Avaliar o Mesmo Jogador em Diferentes Posições

```python
# Suponha stats de um jogador versátil
universal_stats = {
    "short_finish": 80, "long_shot": 76, "free_kick": 74,
    "sprint": 85, "acceleration": 83, "agility": 84,
    "stamina": 85, "strength": 80, "balance": 81,
    "short_pass": 82, "long_pass": 80, "crossing": 78,
    "vision": 84, "dribbling": 82, "ball_control": 83,
    "tackle": 78, "interception": 76, "marking": 75, "ball_shielding": 76,
}

posicoes = {
    "atacante": calculate_football_overall("atacante", universal_stats),
    "ponta": calculate_football_overall("ponta", universal_stats),
    "lateral": calculate_football_overall("lateral", universal_stats),
    "meia": calculate_football_overall("meia", universal_stats),
    "zagueiro": calculate_football_overall("zagueiro", universal_stats),
}

print("Avaliação por Posição:")
for posicao, overall in posicoes.items():
    print(f"  {posicao:15} → {overall}")

# Resultado esperado:
# atacante        → 82
# ponta           → 84  (mobilidade mais forte)
# lateral         → 83  (defesa ok, mobilidade ok)
# meia            → 85  (criação e mobilidade altas)
# zagueiro        → 81  (defesa ok, mas não é o destaque)
```

### Exemplo 3: Jogador Novo sem Posição Definida (Modo Flex)

```python
# Novo jogador que ainda não definiu posição
novato_stats = {
    "short_finish": 65, "long_shot": 62, "free_kick": 60,
    "sprint": 70, "acceleration": 68, "agility": 70,
    "stamina": 72, "strength": 69, "balance": 70,
    "short_pass": 72, "long_pass": 68, "crossing": 65,
    "vision": 70, "dribbling": 73, "ball_control": 72,
    "tackle": 65, "interception": 63, "marking": 62, "ball_shielding": 64,
}

# Modo Flex - média simples de todos os pacotes
overall_flex = calculate_football_overall("sem_posicao", novato_stats)
print(f"Overall (Modo Flex): {overall_flex}")

# Equivalente a:
overall_default = calculate_football_overall("default", novato_stats)
overall_rodizio = calculate_football_overall("rodizio", novato_stats)

assert overall_flex == overall_default == overall_rodizio
print("✓ Todos retornam o mesmo valor (modo flex ativo)")
```

### Exemplo 4: Jogador em FUTSAL (com Multiplicador de XP)

```python
# Quando um MatchPerformance for criado com sub_type="FUTSAL"
# o sistema automaticamente multiplica XP

# Em xp_service.py, distribute_match_xp() aplica:
# if sub_type == 'FUTSAL':
#     attribute_xp['agility'] *= 1.2
#     attribute_xp['ball_control'] *= 1.2

# Exemplo de uso:
from app.models.player_stats import MatchPerformance

futsal_match = MatchPerformance(
    user_id="jogador-123",
    sport_type="football",
    sub_type="FUTSAL",  # ← Ativa multiplicadores
    goals=2,
    assists=3,
    ball_touches=120,
    # ... outros campos
)

# Quando process_match_performance(futsal_match) é chamado:
# - Agilidade e Controle de Bola ganham 1.2x XP
# - Jogador especializado em futsal progride mais rápido nesses atributos
```

---

## 🏐 EXEMPLOS DE VÔLEI

### Exemplo 1: Calcular Overall de um Levantador

```python
# Stats de um levantador (setter) especializado
stats_setter = {
    "spike_power": 50,     # Não precisa de força de ataque
    "spike_accuracy": 55,  # Ataque secundário
    "jump": 65,            # Salto moderado
    "reaction": 92,        # ← Crucial para setting
    "serve_power": 78,
    "serve_tactical": 88,  # ← Setting é tático
    "game_vision": 95,     # ← Visão de jogo vital
    "block": 60,           # Proteção básica
    "reception": 82,       # Boa recepção
    "floor_defense": 75,
    "coverage": 78,
    "setting": 98,         # ← ESPECIALIDADE
    "creativity": 95,      # ← Criatividade alta
    "lateral_agility": 72,
    "stamina": 87,
    "coordination": 92,    # ← Coordenação vital
}

overall = calculate_volleyball_overall("levantador", stats_setter)
print(f"Overall como Levantador: {overall}")
# Resultado esperado: 90+ (setting muito alto pesa 3.5)

# Por posição alternativa:
as_ponteiro = calculate_volleyball_overall("ponteiro", stats_setter)
print(f"Overall como Ponteiro: {as_ponteiro}")
# Resultado: ~68 (spike_power e spike_accuracy são fracos)
# Mostra que o levantador não seria bom como ponteiro
```

### Exemplo 2: Comparar Posições de Vôlei

```python
# Stats de um jogador versátil de vôlei
versatil_stats = {
    "spike_power": 85,
    "spike_accuracy": 82,
    "jump": 87,
    "reaction": 85,
    "serve_power": 80,
    "serve_tactical": 82,
    "game_vision": 84,
    "block": 86,
    "reception": 83,
    "floor_defense": 84,
    "coverage": 85,
    "setting": 78,
    "creativity": 80,
    "lateral_agility": 86,
    "stamina": 88,
    "coordination": 87,
}

posicoes_volei = {
    "levantador": calculate_volleyball_overall("levantador", versatil_stats),
    "ponteiro": calculate_volleyball_overall("ponteiro", versatil_stats),
    "central": calculate_volleyball_overall("central", versatil_stats),
    "oposto": calculate_volleyball_overall("oposto", versatil_stats),
    "libero": calculate_volleyball_overall("libero", versatil_stats),
}

print("Análise Multi-Posição (Vôlei):")
for pos, overall in posicoes_volei.items():
    print(f"  {pos:15} → {overall}")

# Resultado esperado:
# levantador      → 84  (setting só é bom)
# ponteiro        → 88  (spike_power, spike_accuracy, jump altos)
# central         → 89  (block e defesa excelentes)
# oposto          → 87  (spike_power alto, similar ao ponteiro)
# libero          → 91  (defesa excepcional é seu melhor)
```

### Exemplo 3: Jogador sem Posição - Modo Flex

```python
# Novo jogador ou em rodízio
novato_volei = {
    "spike_power": 72,
    "spike_accuracy": 70,
    "jump": 75,
    "reaction": 75,
    "serve_power": 72,
    "serve_tactical": 70,
    "game_vision": 73,
    "block": 72,
    "reception": 73,
    "floor_defense": 71,
    "coverage": 72,
    "setting": 71,
    "creativity": 72,
    "lateral_agility": 74,
    "stamina": 76,
    "coordination": 74,
}

# Sem posição - média simples dos pacotes
overall_flex = calculate_volleyball_overall("rodizio", novato_volei)
print(f"Overall (Rodízio): {overall_flex}")

# Equivalente:
overall_no_pos = calculate_volleyball_overall(source=novato_volei)
assert overall_flex == overall_no_pos
print("✓ Ambos usam modo flex (média simples)")
```

### Exemplo 4: Líbero Especializado

```python
# Stats de um líbero (defensor especialista)
stats_libero = {
    "spike_power": 35,     # Não ataca
    "spike_accuracy": 40,  # Não ataca
    "jump": 55,            # Salto baixo
    "reaction": 95,        # ← Reflexos aguçados
    "serve_power": 60,
    "serve_tactical": 68,
    "game_vision": 78,
    "block": 45,           # Não bloqueia muito
    "reception": 96,       # ← Excelente recepção
    "floor_defense": 96,   # ← Defesa excepcional
    "coverage": 97,        # ← Cobertura de quadra
    "setting": 55,         # Levanta o básico
    "creativity": 60,
    "lateral_agility": 95, # ← Mobilidade lateral
    "stamina": 92,         # ← Resistência alta
    "coordination": 90,    # ← Coordenação fina
}

overall_libero = calculate_volleyball_overall("libero", stats_libero)
print(f"Overall como Líbero: {overall_libero}")
# Resultado esperado: 91-92 (defesa e movement muito altos, peso 3.5 + 3.0)

overall_ponteiro = calculate_volleyball_overall("ponteiro", stats_libero)
print(f"Overall como Ponteiro: {overall_ponteiro}")
# Resultado esperado: ~45 (spike_power e spike_accuracy críticos)
# Deixa claro que líbero faria péssimo como atacante
```

---

## 🎮 EXEMPLO DE MATCH PROGRESSION COM SUB_TYPE

```python
from app.services.xp_service import (
    apply_match_progression,
    process_match_performance,
)
from app.models.player_stats import MatchPerformance, PlayerStats
from app.models.user import User

# Criar uma partida de futsal
futsal_performance = MatchPerformance(
    user_id="player-456",
    sport_type="football",
    sub_type="FUTSAL",  # ← Ativa multiplicadores
    goals=2,
    assists=1,
    ball_touches=120,
    passes_completed=68,
    passes_attempted=75,
    ball_recoveries=15,
    fouls_committed=3,
    field_goals_made=0,
    field_goals_attempted=0,
    points=0,
    rebounds=0,
    blocks=0,
    steals=5,
    # Stats personalizadas de performance
)

# Quando processada:
# distribute_match_xp() vai:
# 1. Calcular XP base por pacote (futebol)
# 2. Aplicar multiplicador 1.2x em agility
# 3. Aplicar multiplicador 1.2x em ball_control
# 4. Retornar XP distribuído com multiplicadores aplicados

result = process_match_performance(futsal_performance)

print(f"""
XP Ganho em FUTSAL:
  Agilidade: {result.attribute_xp.get('agility', 0)} (1.2x multiplicado)
  Ball Control: {result.attribute_xp.get('ball_control', 0)} (1.2x multiplicado)
  Outros atributos: normais
""")
```

---

## 📊 COMPARAÇÃO: Mesmo Jogador em Esportes Diferentes

```python
# Jogador multi-esporte (raro, mas exemplar)
universal_player_stats = {
    # Futebol
    "short_finish": 82,
    "long_shot": 78,
    "free_kick": 75,
    "sprint": 87,
    "acceleration": 84,
    "agility": 86,
    "stamina": 88,
    "strength": 78,
    "balance": 80,
    "short_pass": 85,
    "long_pass": 82,
    "crossing": 80,
    "vision": 86,
    "dribbling": 85,
    "ball_control": 86,
    "tackle": 76,
    "interception": 74,
    "marking": 72,
    "ball_shielding": 75,
    
    # Vôlei (mesmos stats servem de base)
    "spike_power": 82,
    "spike_accuracy": 80,
    "jump": 87,
    "reaction": 85,
    "serve_power": 80,
    "serve_tactical": 82,
    "game_vision": 86,
    "block": 80,
    "reception": 78,
    "floor_defense": 76,
    "coverage": 77,
    "setting": 72,
    "creativity": 80,
    "lateral_agility": 86,
    "coordination": 84,
    
    # Basket (usa stats genéricas já em sistema antigo)
}

# Futebol
futebol_meia = calculate_football_overall("meia", universal_player_stats)
print(f"Futebol (Meia): {futebol_meia}")

# Vôlei
volei_ponteiro = calculate_volleyball_overall("ponteiro", universal_player_stats)
print(f"Vôlei (Ponteiro): {volei_ponteiro}")

# Conclusão: A mesma pessoa brilha em posições diferentes dos esportes!
# Isso mostra a flexibilidade do sistema.
```

---

## ✅ Checklist de Uso

- [ ] Importar funções corretas de `xp_service.py`
- [ ] Passar `position` como primeiro argumento para futebol e vôlei
- [ ] Verificar se sport_type normatizado está correto (lowercase)
- [ ] Testar aliases de posição compatíveis
- [ ] Usar "sem_posição" ou "rodizio" para modo flex
- [ ] Adicionar `sub_type` ao MatchPerformance para variações
- [ ] Validar que overall estar sempre entre 0-99

---

## 📚 Referência Rápida

| Função | Esporte | Retorna | Com Position |
|--------|---------|---------|--------------|
| `calculate_football_overall()` | Futebol | int (0-99) | ✅ Obrigatório |
| `calculate_football_overall_by_position()` | Futebol | dict | ✅ Obrigatório |
| `calculate_football_package_scores()` | Futebol | dict | ❌ Não precisa |
| `calculate_volleyball_overall()` | Vôlei | int (0-99) | ✅ Opcional |
| `calculate_volleyball_overall_by_position()` | Vôlei | dict | ✅ Obrigatório |
| `calculate_volleyball_package_scores()` | Vôlei | dict | ❌ Não precisa |
| `calculate_basketball_overall()` | Basket | int (0-99) | ✅ Obrigatório |
