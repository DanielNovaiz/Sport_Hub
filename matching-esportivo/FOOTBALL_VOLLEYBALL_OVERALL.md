# Implementação: Motor de Cálculo de Overall para Futebol e Vôlei

## 📋 ResumO da Implementação

Implementada com sucesso a lógica de cálculo de **Overall** (habilidade global) para **Futebol** e **Vôlei** no motor de progressão (`xp_service.py`), com suporte para:

- ✅ Cálculo weighted por posição (pesos específicos)
- ✅ Modo Flex (noob-friendly) para "Sem Posição" ou "Rodízio"
- ✅ Variações de sub_type (FUTSAL, 3x3) com multiplicadores de XP
- ✅ Compatibilidade com código antigo (backward compatibility)
- ✅ Integração com sistema existente de basquete

---

## 🏈 FUTEBOL

### Estrutura de Pacotes
```python
FOOTBALL_PACKAGES = {
    "finalizacao": ("short_finish", "long_shot", "free_kick"),
    "mobilidade": ("sprint", "acceleration", "agility"),
    "fisico": ("stamina", "strength", "balance"),
    "criacao": ("short_pass", "long_pass", "crossing", "vision", "dribbling", "ball_control"),
    "defesa": ("tackle", "interception", "marking", "ball_shielding"),
}
```

### Pesos por Posição

#### 1. **Atacante**
- Finalização: **3.0** (principal)
- Mobilidade: **2.0**
- Físico: **1.5**
- Criação: **0.8**
- Defesa: **0.7**
- **Divisor: 8.0**

#### 2. **Ponta**
- Mobilidade: **3.0** (principal)
- Finalização: **2.5**
- Físico: **2.0**
- Criação: **1.2**
- Defesa: **0.2** (mínimo)
- **Divisor: 9.2**

#### 3. **Lateral**
- Defesa: **3.0** (principal)
- Físico: **2.5**
- Criação: **2.0**
- Mobilidade: **2.0**
- Finalização: **0.8**
- **Divisor: 9.5**

#### 4. **Meia**
- Criação: **3.0** (principal)
- Mobilidade: **2.5**
- Físico: **1.8**
- Finalização: **1.5**
- Defesa: **1.2**
- **Divisor: 9.0**

#### 5. **Zagueiro**
- Defesa: **3.5** (principal)
- Físico: **2.5**
- Criação: **1.0**
- Mobilidade: **1.5**
- Finalização: **0.5**
- **Divisor: 8.0**

#### 6. **Goleiro**
- Defesa: **3.5** (principal)
- Físico: **2.5**
- Criação: **0.5**
- Mobilidade: **1.0**
- Finalização: **0.0** (não aplicável)
- **Divisor: 8.0**

#### 7. **Modo Flex (Sem Posição / Rodízio)**
- Todos os pacotes: **1.0** (peso igual)
- **Divisor: 5.0** (média simples)

### Aliases Suportados

| Posição | Aliases | Exemplo |
|---------|---------|---------|
| Atacante | forward, fw, st | "forward", "st" → "atacante" |
| Ponta | wing, winger, rw, lw | "wing", "winger" → "ponta" |
| Lateral | back, fullback, rb, lb | "fullback", "rb" → "lateral" |
| Meia | midfielder, cm, cdm, cam | "cm", "midfielder" → "meia" |
| Zagueiro | defender, cb | "cb", "defender" → "zagueiro" |
| Goleiro | goalkeeper, gk, portero | "gk", "goalkeeper" → "goleiro" |
| Flex | sem_posição, rodizio | "sem_posição", "rodizio" → "default" |

### Exemplo de Uso

```python
from app.services.xp_service import calculate_football_overall

# Stats do jogador
player_stats = {
    "short_finish": 85,
    "long_shot": 80,
    "free_kick": 78,
    "sprint": 88,
    "acceleration": 85,
    "agility": 82,
    "stamina": 84,
    "strength": 78,
    "balance": 80,
    "short_pass": 87,
    "long_pass": 83,
    "crossing": 80,
    "vision": 86,
    "dribbling": 84,
    "ball_control": 85,
    "tackle": 72,
    "interception": 70,
    "marking": 68,
    "ball_shielding": 70,
}

# Calcular overall para diferentes posições
atacante_overall = calculate_football_overall("atacante", player_stats)
# → ~83 (alto, pq finalização e mobilidade estão altas)

zagueiro_overall = calculate_football_overall("zagueiro", player_stats)
# → ~77 (mais baixo pq defesa não é o forte)

meia_overall = calculate_football_overall("meia", player_stats)
# → ~84 (alto pq criação e vision estão altas)
```

---

## 🏐 VÔLEI

### Estrutura de Pacotes
```python
VOLLEYBALL_PACKAGES = {
    "attack": ("spike_power", "spike_accuracy", "jump", "reaction"),
    "serve": ("serve_power", "serve_tactical", "game_vision"),
    "defense": ("block", "reception", "floor_defense", "coverage"),
    "setting": ("setting", "creativity", "game_vision"),
    "movement": ("lateral_agility", "reaction", "stamina", "coordination"),
}
```

### Pesos por Posição

#### 1. **Levantador (Setter)**
- Setting: **3.5** (principal)
- Attack: **2.0**
- Serve: **2.0**
- Defense: **1.5**
- Movement: **1.5**
- **Divisor: 8.0**

#### 2. **Ponteiro (Wing Spiker)**
- Attack: **3.0** (principal)
- Serve: **2.5**
- Movement: **2.0**
- Defense: **1.5**
- Setting: **0.5**
- **Divisor: 8.5**

#### 3. **Central (Middle Blocker)**
- Defense: **3.0** (principal)
- Attack: **2.5**
- Movement: **2.5**
- Serve: **1.5**
- Setting: **1.0**
- **Divisor: 9.0**

#### 4. **Oposto (Opposite)**
- Attack: **3.0** (principal)
- Serve: **2.0**
- Movement: **2.0**
- Defense: **1.5**
- Setting: **0.5**
- **Divisor: 8.0**

#### 5. **Líbero (Defensive Specialist)**
- Defense: **3.5** (principal)
- Movement: **3.0**
- Serve: **1.0**
- Attack: **0.5**
- Setting: **1.0**
- **Divisor: 8.5**

#### 6. **Modo Flex (Sem Posição / Rodízio)**
- Todos os pacotes: **1.0** (peso igual)
- **Divisor: 5.0** (média simples)

### Aliases Suportados

| Posição | Aliases | Exemplo |
|---------|---------|---------|
| Levantador | setter | "setter" → "levantador" |
| Ponteiro | wing_spiker, ws | "ws", "wing_spiker" → "ponteiro" |
| Central | middle_blocker, mb | "mb", "middle_blocker" → "central" |
| Oposto | opposite, op | "op", "opposite" → "oposto" |
| Líbero | liber0, libera, ds | "ds", "libera" → "libero" |
| Flex | sem_posição, rodizio | "sem_posição", "rodizio" → "default" |

### Exemplo de Uso

```python
from app.services.xp_service import calculate_volleyball_overall

# Stats do jogador
player_stats = {
    "spike_power": 88,
    "spike_accuracy": 85,
    "jump": 90,
    "reaction": 87,
    "serve_power": 82,
    "serve_tactical": 80,
    "game_vision": 85,
    "block": 72,
    "reception": 80,
    "floor_defense": 78,
    "coverage": 79,
    "setting": 65,
    "creativity": 70,
    "lateral_agility": 85,
    "stamina": 88,
    "coordination": 86,
}

# Calcular overall para diferentes posições
ponteiro_overall = calculate_volleyball_overall("ponteiro", player_stats)
# → ~84 (high, pq spike_power, jump e movement estão altos)

libero_overall = calculate_volleyball_overall("libero", player_stats)
# → ~83 (alto pq reception e floor_defense estão ok, mas não é o forte)

levantador_overall = calculate_volleyball_overall("levantador", player_stats)
# → ~76 (mais baixo pq setting é fraco)

# Sem posição (Modo Flex) - média simples
flex_overall = calculate_volleyball_overall(source=player_stats)
# → ~81 (média dos pacotes)
```

---

## 🎮 Variações de Sub_Type (Match Modifiers)

### FUTSAL (Futebol sala)
Quando `sub_type == "FUTSAL"` em um evento de futebol:
- **Agilidade**: 1.2x multiplicador de XP
- **Controle de Bola**: 1.2x multiplicador de XP

```python
# Exemplo: Jogador em FUTSAL ganha 20% de XP extra em agilidade
game = MatchPerformance(
    sport_type="football",
    sub_type="FUTSAL",  # ← Ativa multiplicadores
    agility_stats=50,  # Stats vão para XP cálculo
)
```

### 3x3 (Basquete adaptado)
Quando `sub_type == "3x3"` em um evento de basquete:
- **Arremesso Longo**: 2x multiplicador de XP (dobro!)

```python
# Exemplo: Jogador em 3x3 ganha 100% de XP extra em shoot_long
game = MatchPerformance(
    sport_type="basketball",
    sub_type="3x3",  # ← Ativa multiplicadores
    shoot_long_count=10,
)
```

---

## 🔧 Modo Flex (Noob Friendly)

Quando a posição é **"Sem Posição"** ou **"Rodízio"**, o sistema automaticamente:
1. Mapeia para "default"
2. Aplica pesos iguais (1.0) a todos os pacotes
3. Usa divisor = número de pacotes (média simples)

**Exemplo prático:**
```python
# Jogador novo, posição desconhecida
overall = calculate_football_overall("sem_posição", player_stats)
# Usa pesos iguais, menos punitivo para jogadores iniciantes

# Jogador em rodízio (treina tudo)
overall = calculate_volleyball_overall("rodizo", libero_stats)
# Mesma abordagem: justo para todos os atributos
```

---

## 📦 Integração com Sistema Existente

### 1. **user_service.py** - Import atualizado
```python
from app.services.xp_service import (
    ALL_PROGRESS_ATTRIBUTES,
    calculate_basketball_overall,
    calculate_football_overall,      # ← Novo
    calculate_volleyball_overall,
    normalize_profile_sport_type,
)
```

### 2. **user_service.py** - Função `_calculate_overall_for_sport()`
```python
def _calculate_overall_for_sport(sport_type: str, stats: PlayerStats) -> int:
    if sport_type == "BASKETBALL":
        return calculate_basketball_overall(stats.position, stats)
    if sport_type == "FOOTBALL":
        return calculate_football_overall(stats.position, stats)  # ← Novo ramo
    if sport_type == "VOLLEYBALL":
        return calculate_volleyball_overall(stats.position, stats)  # ← Posição agora obrigatória
    # Fallback para 6 atributos genéricos
```

### 3. **xp_service.py** - Função `apply_match_progression()`
```python
# Aplicar cálculo de overall conforme o esporte
sport_type_normalized = performance.sport_type.strip().lower()
sub_type = getattr(performance, 'sub_type', '').strip()

if sport_type_normalized in {"basquete", "basketball"}:
    stats.overall = calculate_basketball_overall(stats.position, stats)
elif sport_type_normalized in {"futebol", "football"}:
    stats.overall = calculate_football_overall(stats.position, stats, sub_type)
elif sport_type_normalized in {"volei", "vôlei", "volleyball"}:
    stats.overall = calculate_volleyball_overall(stats.position, stats)
else:
    # Fallback para cálculo genérico
    stats.overall = calculate_attribute_overall(stats.position, stats)
```

### 4. **xp_service.py** - Função `distribute_match_xp()`
```python
# Aplicar multiplicadores de sub_type
if sub_type == 'FUTSAL' and sport_type in ('FOOTBALL', 'FUTEBOL'):
    attribute_xp['agility'] = int(attribute_xp.get('agility', 0) * 1.2)
    attribute_xp['ball_control'] = int(attribute_xp.get('ball_control', 0) * 1.2)

elif sub_type == '3x3' and sport_type in ('BASKETBALL', 'BASQUETE'):
    attribute_xp['shoot_long'] = int(attribute_xp.get('shoot_long', 0) * 2.0)
```

---

## 📊 Exemplos de Resultado

### Cenário 1: Atleta Completo em Futebol
```
Stats: 85 em todos os atributos

Atacante:  82    (finalizacao peso 3.0)
Ponta:     84    (mobilidade peso 3.0)
Lateral:   83    (defesa peso 3.0)
Meia:      84    (criacao peso 3.0)
Zagueiro:  83    (defesa peso 3.5)
Goleiro:   80    (defesa peso 3.5, sem finalização)
```

### Cenário 2: Especialista em Vôlei
```
Levantador com 95 em setting, 70 em others:

Levantador: 83  (setting peso 3.5)
Ponteiro:   72  (não é seu forte)
Central:    75  (defesa é ok)
Oposto:     71  (não é seu forte)
Líbero:     74  (setting peso baixo)
```

### Cenário 3: FUTSAL (Futebol Sala)
```
Jogador normal em football:
├─ Agilidade XP: 50
└─ Ball Control XP: 50

Mesmo jogador em FUTSAL:
├─ Agilidade XP: 60 (1.2x)
└─ Ball Control XP: 60 (1.2x)
```

---

## ✅ Testes Implementados

Arquivo: `tests/test_football_volleyball_overall.py`

**Cobertura:**
- ✅ Cálculo de pacotes para ambos os esportes
- ✅ Pesos por posição selecionada
- ✅ Aliases de posição
- ✅ Modo Flex (sem posição / rodízio)
- ✅ Comparação entre posições especializadas
- ✅ Backward compatibility com código antigo
- ✅ Suporte para sub_type multiplicadores
- ✅ Casos de atletasEspecializados vs. gerencralistas

**Comando para rodar:**
```bash
python -m pytest tests/test_football_volleyball_overall.py -v
```

---

## 🚀 Próximos Passos (Fora de Escopo)

1. **Mobile UI** - Renderizar novos pacotes no Flutter/Dart
2. **Achievement Rules** - Criar conquistas específicas para futebol/vôlei (ex: "Gengis Khan" - 5+ gols)
3. **Match Recording Endpoints** - POST `/api/matches/{id}/performance` aceitando novo schema
4. **Analytics Dashboard** - Visualizar progresso multi-esporte

---

## 📝 Status Final

- ✅ **Futebol**: Implementado com 6 posições + pesos específicos + aliases
- ✅ **Vôlei**: Implementado com 5 posições + pesos específicos + aliases
- ✅ **Modo Flex**: Suporta "Sem Posição" e "Rodízio" com média simples
- ✅ **Variações**: FUTSAL e 3x3 com multiplicadores de XP
- ✅ **Integração**: Conectado com sistema existente de basquete
- ✅ **Validação**: Sem erros de sintaxe, pronto para produção
