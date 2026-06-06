# 🤖 GitHub Copilot Instructions — Matching Esportivo

**Versão:** 3.0  
**Data:** Abril de 2026  
**Filosofia:** GSD + Simbiose IA-Código

---

## Missão

Este projeto existe para atingir **produção** no menor tempo possível com um sistema:

- funcional agora
- escalável quando necessário
- legível para IAs antes de ser “bonito” para humanos
- simples de corrigir quando algo quebrar

Prioridade máxima: **velocidade de execução com previsibilidade técnica**.

---

## Princípios de operação

### GSD radical

- Entregue a feature completa sem fragmentar demais o trabalho.
- Se um pacote externo consolidado resolve o problema, use-o.
- Menos código significa menos superfície de falha para a IA corrigir.
- Não invente abstração só para parecer elegante.

### Simbiose IA-Código

- Escreva para leitura por máquina antes de leitura humana.
- O código deve ser fácil de mapear, alterar e reexecutar por outro agente.
- Cada arquivo deve ter responsabilidade isolada.
- Se a lógica de matching mudar, idealmente apenas **um arquivo** deve mudar.

### Regra operacional

- Se o pedido é claro, execute.
- Se houver risco real, pare e sinalize.
- Se não houver risco, não atrase a entrega com confirmação desnecessária.

---

## Filosofia anti-complexidade

- Evite over-engineering.
- Não crie classes base, heranças, frameworks internos ou padrões complexos sem necessidade.
- Prefira uma função pequena, tipada e direta em vez de uma hierarquia sofisticada.
- Menos camadas = menos bugs.
- Se a solução simples resolve, a solução simples vence.

### Preferências práticas

- funções pequenas e com responsabilidade única
- módulos curtos e com nomes explícitos
- fluxos lineares e previsíveis
- poucas dependências internas
- zero “abstração por esporte”

---

## Legibilidade por estrutura

O código deve parecer **prosa lógica**.

### Nomes

- Use nomes extremamente descritivos e explícitos.
- Evite siglas obscuras, atalhos mentais e nomes genéricos.
- Prefira `nearby_event_search_query` a `query1`.
- Prefira `user_preferred_sports` a `prefs`.

### Comentários e docstrings

- Elimine comentários óbvios para humanos.
- Não comente o que o código já diz.
- Use docstrings técnicas curtas com:
  - Input
  - Output
  - efeitos colaterais

### Exemplo de docstring ideal

```python
async def get_nearby_events(...):
    """Input: geolocalização + raio. Output: lista ordenada. Side effects: consulta PostGIS."""
```

---

## Machine-Friendly: regras obrigatórias

- Python **3.12+**.
- Type hints em **100%** do código.
- Pydantic **V2** para entrada e saída previsíveis.
- Funções pequenas, puro foco em um objetivo.
- Preferir `from_attributes=True` em schemas de saída ORM.
- Manter serialização e validação explícitas.

### Regras de tipagem

- Nunca deixe função pública sem annotation.
- Nunca misture retorno implícito com fluxo complexo.
- Se o tipo for fechado, use `Literal`.
- Se o dado vier do banco, represente isso nos schemas com clareza.

---

## Stack obrigatória

- **FastAPI** para API
- **SQLModel / SQLAlchemy async** para persistência
- **PostgreSQL + PostGIS** para geolocalização
- **Redis** para pub/sub, cache e sinais assíncronos
- **Docker / Docker Compose** para ambiente reproduzível

### Regras de stack

- FastAPI sempre `async`.
- Banco sempre via `AsyncSession`.
- Geoprocessamento sempre no PostGIS quando possível.
- Redis nunca deve bloquear o request path.

---

## Fontes canônicas do repositório

### Backend

- Routers canônicos ficam em `app/api/`.
- Serviços canônicos ficam em `app/services/`.
- Schemas canônicos ficam em `app/schemas/`.
- Modelos canônicos ficam em `app/models/`.
- Arquivos na raiz como `backend_*_endpoints.py` são exemplos, rascunhos ou superfícies auxiliares; não devem virar a fonte principal sem migração explícita.

### Mobile

- A árvore canônica de UI é `mobile_app/lib/presentation/`.
- A árvore canônica de dados/contratos é `mobile_app/lib/data/`.
- Caminhos legados em `mobile_app/lib/screens/`, `mobile_app/lib/models/` e `mobile_app/lib/services/` só devem existir se estiverem documentados como compatibilidade temporária.

### Regra anti-drift

- Se houver duas implementações para a mesma responsabilidade, escolha uma canônica e marque a outra como legado ou remova-a.
- Nunca introduza um segundo contrato com o mesmo nome para responsabilidades diferentes.
- Sempre atualize `PROJECT-MEMORY.md` quando um caminho canônico mudar.
- Se um arquivo for somente exemplo, diga isso no nome, na docstring ou na memória do projeto.

---

## Database-First

Toda lógica que puder ser processada no **PostGIS** deve ser feita via SQL/SQLAlchemy.

### O que isso significa

- busca por raio com `ST_DWithin`
- ordenação por proximidade com `ST_Distance` / `ST_DistanceSphere`
- índices `GIST` em campos geométricos
- evitar loops Python para filtrar resultados espaciais

### Regra prática

Se existe uma query espacial, ela nasce no banco.

---

## Funcionalidade > arquitetura ornamental

- Se uma biblioteca externa consolidada resolve o problema, use-a.
- Não reimplemente o que já existe de forma robusta.
- Entregue primeiro o que funciona.
- Otimize depois, com dados.

---

## Diretrizes de workflow

### Modo A — Supervisão

Use quando houver risco técnico, segurança ou necessidade de máxima confiança.

**Foco:**

- segurança
- rigor
- cobertura de testes
- validação detalhada

**Comportamento esperado:**

- revisa efeitos colaterais
- corrige tipos e inconsistências imediatamente
- prioriza estabilidade sobre velocidade

### Modo B — Desenfreado

Use quando o objetivo for entregar uma feature completa o mais rápido possível.

**Foco:**

- entrega ponta a ponta
- modularidade suficiente para correção fácil
- Service Layer Pattern quando fizer sentido
- mínimo de fricção entre model, schema, service e API

**Comportamento esperado:**

- cria Model, Migration se houver, Schema e Endpoint de uma vez
- corrige falhas de tipagem ou lógica sem pedir confirmação
- mantém o código enxuto e substituível

---

## Regra de Ouro

- Não peça confirmação para criar estrutura de pastas ou arquivos.
- Se o objetivo for “Criar Feature X”, entregue tudo de uma vez:
  - Model
  - Schema
  - Service
  - API
  - Migration, se aplicável
- Só pare se houver bloqueio real, risco de perda de dados ou ambiguidade crítica.

---

## Personas Técnicas de Referência

### O Arquiteto Geográfico

Especialista em GeoAlchemy2 e performance de banco.

**Regra:** Toda query espacial deve usar índices GIST e evitar conversões custosas em tempo de execução.  
**Prioridade:** ST_DWithin sobre Haversine manual.

### O Maestro do Real-Time

Especialista em Redis e concorrência.

**Regra:** Notificações de convites devem ser assíncronas e não-bloqueantes.  
**Diretriz:** Use Pub/Sub do Redis para disparar alertas de proximidade.

### O Analista de Matching

Especialista em lógica de exatas.

**Regra:** O ranqueamento deve equilibrar distância vs. nível de habilidade.  
**Condição:** código puramente matemático, fácil de testar isoladamente.

---

## Implementação padrão de feature

### 1. Model

- SQLModel com tipos explícitos.
- IDs UUID.
- índices onde o filtro for frequente.
- localização com `Geometry(POINT, 4326)`.

### 2. Schema

- Pydantic V2.
- separação clara entre input e output.
- validação de coordenadas, limites e strings.

### 3. Service

- lógica de negócio isolada.
- consultas espaciais no banco.
- funções curtas e testáveis.

### 4. API

- routers finos.
- sem regra de negócio pesada no endpoint.
- entradas e saídas previsíveis.

### 5. Tests

- validar comportamento principal.
- testar services puros quando possível.

### 6. Manutenção guiada por IA

- Antes de editar, localize a fonte canônica da responsabilidade.
- Se existir duplicação, documente a escolha e remova a superfície sobrante quando possível.
- Prefira mudanças pequenas que reduzam ambiguidades de navegação para outro agente.
- cobertura forte em Modo A, cobertura suficiente em Modo B.

---

## Redis e concorrência

- Pub/Sub para alertas, convites e fan-out.
- Operações assíncronas, não-bloqueantes.
- Evite travar request HTTP por tarefa secundária.
- Se precisar de desacoplamento, use eventos pequenos e claros.

---

## Qualidade de código

- Prefira nomes longos e explícitos a nomes curtos e ambíguos.
- Prefira retorno claro e previsível.
- Evite comentário que só repete o código.
- Use docstrings técnicas curtas quando adicionarem contexto útil.

---

## Anti-padrões

- over-engineering
- classes base desnecessárias
- múltiplas abstrações para uma lógica simples
- loops Python para geoprocessamento que o banco resolve melhor
- sync dentro de async
- SQL interpolado manualmente
- funções grandes e multi-responsabilidade

---

## Memória do projeto

Existe um arquivo de memória legível para humanos e IA:

- `/.github/PROJECT-MEMORY.md`

**Esse arquivo deve registrar:**

- próximos passos
- implementações planejadas
- funcionalidades em aberto
- erros encontrados
- aprendizados importantes

Use-o como memória operacional para reduzir repetição de erros e aumentar autonomia.

---

## Checklist mental antes de entregar

- [ ] O código funciona agora
- [ ] Está simples o bastante para ser corrigido rápido
- [ ] Está tipado em 100%
- [ ] Usa Pydantic V2 onde há entrada/saída
- [ ] Usa PostGIS quando há geoprocessamento
- [ ] Evita abstrações desnecessárias
- [ ] É modular o suficiente para mudanças isoladas
- [ ] Está pronto para produção o mais cedo possível

---

## Lembrete final

O sistema ideal é aquele que funciona, escala e permanece fácil de substituir.

Se houver dúvida entre “bonito” e “executável”, escolha **executável**.
