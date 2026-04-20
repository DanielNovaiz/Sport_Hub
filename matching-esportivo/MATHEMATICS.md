# 📐 Documentação Matemática - Matching Esportivo

## Algoritmo de Proximidade - Fase 2

### Definição do Problema

Dado:
- Um usuário na localização $P_u = (lat_u, lng_u)$
- Um conjunto de eventos $E = \{e_1, e_2, ..., e_n\}$ com localizações $P_i = (lat_i, lng_i)$
- Um raio de proximidade $R$ (em km)
- Preferências do usuário: esporte $s$ e nível de habilidade $h$

**Objetivo**: Encontrar eventos que satisfazem:

$$d(P_u, P_i) \leq R \quad \text{e} \quad sport_i = s$$

### Sistema de Coordenadas e Conversão

#### WGS84 (SRID 4326)

Usamos latitude/longitude em graus decimais:
- **Latitude**: $\phi \in [-90°, 90°]$
- **Longitude**: $\lambda \in [-180°, 180°]$

#### Conversão Graus para Quilômetros

Na superfície de uma esfera:
$$1° \approx 111.32 \text{ km}$$

Mais precisamente:
$$1° = \frac{\pi \cdot R_{terra}}{180}$$

onde $R_{terra} \approx 6371$ km

**Fórmula de conversão** (simples, suficiente para distâncias <100km):
$$\Delta_{graus} = \frac{R_{km}}{111.32}$$

### Cálculo de Distância - Haversine (Futura Otimização)

Para distâncias grandes, use a fórmula Haversine:

$$a = \sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1) \cdot \cos(\phi_2) \cdot \sin^2\left(\frac{\Delta\lambda}{2}\right)$$

$$c = 2 \cdot \arcsin(\sqrt{a})$$

$$d = R_{terra} \cdot c$$

### Implementação Atual - PostGIS

#### Query ST_DWithin

Busca todos os eventos $e_i$ onde:

$$ST\_DWithin(P_u, P_i, d) = \text{true}$$

Com $d = \frac{R}{111.32}$ (em graus)

**Características**:
- ✅ Usa índice GIST (Generalized Search Tree)
- ✅ Complexidade: $O(\log n)$ em média
- ✅ Retorna aproximadamente (não necessariamente exato em graus)

```sql
SELECT * FROM event
WHERE ST_DWithin(
    location,
    ST_GeomFromText('POINT(-46.6333 -23.5505)', 4326),
    0.1349  -- 15km / 111.32
)
ORDER BY ST_Distance(location, ...) * 111.32
```

### Matching com Habilidade - Modelo Simples

#### Score de Compatibilidade

$$Score = w_s \cdot \mathbb{1}_{sport\_match} + w_h \cdot harmony(h_u, h_i)$$

Onde:
- $w_s = 0.5$ (peso para esporte)
- $w_h = 0.5$ (peso para habilidade)
- $\mathbb{1}_{sport\_match}$ = 1 se usuário pratica o esporte, 0 caso contrário
- $harmony(h_u, h_i)$ = função de compatibilidade de habilidade

#### Função de Compatibilidade de Habilidade

$$harmony(h_u, h_i) = \begin{cases}
1.0 & \text{se } h_u = h_i \text{ (mesma habilidade)} \\
0.5 & \text{se } |h_u - h_i| = 1 \text{ (um nível diferente)} \\
0.0 & \text{se } |h_u - h_i| > 1 \text{ (muito diferente)}
\end{cases}$$

Com mapeamento: $beginner=1, intermediate=2, advanced=3$

**Exemplo**:

Usuario: $h_u = intermediate$ (2), pratica $\{futsal\}$
Evento: $sport_i = futsal$, $h_i = intermediate$ (2)

$$Score = 0.5 \cdot 1 + 0.5 \cdot 1.0 = 1.0 \quad (\text{match perfeito})$$

### Fase 2 - Algoritmo Avançado (Machine Learning)

Expandir com:

$$Score = \sum_{i=1}^{k} w_i \cdot f_i(u, e)$$

Onde:
- $f_1$ = Proximidade (distância)
- $f_2$ = Compatibilidade de habilidade
- $f_3$ = Histórico de eventos do usuário
- $f_4$ = Ratings de compatibilidade (modelo colaborativo)
- $f_5$ = Similaridade com usuários que gostaram do evento (CF)

### Complexidade Assintótica

| Operação | Complexidade | Notas |
|----------|-------------|-------|
| Busca por raio | $O(\log n)$ | Com índice GIST |
| Cálculo de score | $O(k)$ | k = eventos retornados |
| Ordenação | $O(k \log k)$ | k << n |
| **Total** | **$O(\log n + k \log k)$** | Eficiente |

### Exemplo de Cálculo Prático

**Usuário em São Paulo:**
- $P_u = (-23.5505, -46.6333)$
- $R = 15$ km
- Esporte: futsal
- Habilidade: intermediate

**Conversão raio para graus:**
$$\Delta = \frac{15}{111.32} \approx 0.1349°$$

**Query PostGIS:**
```sql
SELECT id, title, ST_Distance(location, POINT(-46.6333 -23.5505)) * 111.32 as distance_km
FROM event
WHERE ST_DWithin(location, POINT(-46.6333 -23.5505), 0.1349)
AND sport = 'futsal'
ORDER BY distance_km
LIMIT 20
```

Result:
| ID | Título | Distância |
|----|--------|-----------|
| 1 | Futsal Ibirapuera | 2.3 km |
| 2 | Futsal Vila Madalena | 5.1 km |
| 3 | Futsal Parque Ibirapuera | 8.7 km |
| 4 | Futsal Pinheiros | 12.4 km |

todos $\leq 15$ km ✅

---

**Próximos passos:**
1. Implementar Haversine para maior precisão
2. Adicionar Machine Learning (Phase 2)
3. Testar performance com 1M+ eventos
4. Otimizar índices geoespaciais
