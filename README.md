# ⚡ SpaceGuard — Mission Energy Monitor

> Sistema inteligente de monitoramento de sistemas energéticos para missão espacial experimental.

---

## 📋 Sobre o Projeto

O **SpaceGuard** é uma solução computacional desenvolvida para a **Global Solution 2026** da FIAP, na disciplina de **Soluções em Energias Renováveis e Sustentáveis**.

O sistema monitora, interpreta e exibe dados simulados das condições operacionais de uma missão espacial experimental em órbita baixa (LEO — *Low Earth Orbit* ~408 km), com foco em:

- 🔋 **Energia renovável fotovoltaica** — painéis solares como fonte primária
- 🌱 **Sustentabilidade** — gestão de consumo e eficiência energética
- 🤖 **IA introdutória** — motor de decisão com lógica condicional multi-camada
- 📊 **Visualização** — dashboard interativo HTML + gráficos matplotlib

---

## 👥 Integrantes

| Nome | RM | Turma |
|---|---|---|
| Henrique Eduardo da Silveira | 571803 | 1CCPW |
| Felipe Elze da Silva | 572024 | 1CCPW |

**FIAP — Ciências da Computação | 1º Semestre 2026**  
**Disciplina:** Soluções em Energias Renováveis e Sustentáveis

---

## 🛰️ Funcionalidades

### Monitoramento de Dados Simulados
- Temperatura dos painéis solares, baterias e computador de bordo
- Geração fotovoltaica, consumo total, nível de bateria e tensão do barramento
- Qualidade do link de comunicação com a estação terrestre
- Status individual de 6 módulos operacionais (propulsão, suporte vida, científico, navegação, comunicação, energia)

### Geração de Alertas Automáticos
Quatro níveis de alerta:
- ✅ **OK** — todos os sistemas nominais
- ℹ️ **INFO** — informação, sem ação urgente
- ⚠️ **AVISO** — atenção requerida
- 🔴 **CRÍTICO** — intervenção imediata

### Tomada de Decisão Básica (IA)
O motor de IA analisa cada subsistema e gera **ações corretivas recomendadas** automaticamente. Exemplos:
- Bateria crítica → ativa modo de sobrevivência
- Temperatura elevada → aciona resfriamento
- Link perdido → protocolo de reconexão
- Módulo em falha → isolamento e redundância

### Visualização dos Dados
- **Dashboard HTML** interativo com gráficos Chart.js (abre no navegador)
- **Dashboard matplotlib** com 6 painéis (roda no Colab)
- **Relatório em texto** no terminal com cores ANSI
- **Histórico** das últimas 30 leituras com identificação de períodos de eclipse

---

## 🚀 Como executar
### VSCode / PyCharm

```bash
# Clonar o repositório
git clone [https://github.com/SEU_USUARIO/spaceguard-fiap-2026.git](https://github.com/FelipeElze1010/Solucoes-em-Energias-Renovaveis-e-Sustentaveis)
cd spaceguard-fiap-2026

# Rodar em loop contínuo (terminal com cores)
python spaceguard.py

# Gerar apenas um relatório
python spaceguard.py --once

# Abrir dashboard HTML no navegador
python spaceguard.py --html
```

### Requisitos

```
Python 3.8+
matplotlib (pip install matplotlib)
numpy      (pip install numpy)
```

> Nenhuma API externa necessária — o sistema funciona completamente offline.

---

## 🧠 Arquitetura do Sistema

```
spaceguard/
├── spaceguard.py              # Sistema completo para VSCode/PyCharm
├── spaceguard_colab.ipynb     # Notebook para Google Colab
└── README.md                  # Este arquivo
```

### Componentes principais

```
OrbitalSimulator               → Geração de dados simulados com física orbital
     │
     ▼
MissionSnapshot                → Estrutura de dados da missão
     │
     ▼
AIDecisionEngine               → Motor de IA: análise e alertas
     │
     ├──▶ Terminal display      → Relatório colorido no terminal
     ├──▶ Matplotlib dashboard  → 6 painéis (Colab)
     └──▶ HTML dashboard        → Dashboard interativo (browser)
```

### Modelo de simulação

O simulador implementa física orbital simplificada baseada em missões reais (ISS/ESA):

- **Ciclo orbital:** ~92 minutos reais → modelado com fase angular de 0° a 360°
- **Eclipse:** 35% de cada órbita (fase 128°–256°) → geração solar = 0W
- **Painéis fotovoltaicos:** até 8.200W em iluminação plena, rendimento ~28.5%
- **Bateria:** modelo de carga/descarga com eficiência coulombiana
- **Anomalias:** injetadas aleatoriamente (8% de probabilidade por ciclo) em módulos aleatórios

---

## 📐 Conceitos de Energia Aplicados

| Conceito | Aplicação no SpaceGuard |
|---|---|
| Energia Fotovoltaica | Simulação de painéis solares como fonte primária da missão |
| Eficiência energética | Monitoramento do balanço geração vs consumo |
| Armazenamento de energia | Modelo de bateria Li-Ion com carga/descarga |
| Sustentabilidade | Sistema de alertas para gestão otimizada do consumo |
| Tomada de decisão | IA recomenda ações para maximizar a vida útil dos sistemas |

---

## 📊 Capturas de tela

<img width="754" height="570" alt="image" src="https://github.com/user-attachments/assets/15b3fce6-c8e1-45c3-926f-3236fbabc5cd" />

<img width="1223" height="816" alt="image" src="https://github.com/user-attachments/assets/35523ede-2699-41de-ba49-3491f28a8f09" />

<img width="1901" height="966" alt="image" src="https://github.com/user-attachments/assets/b4ed24a4-7842-49f3-9d98-e5367300ac37" />



---

*FIAP — Ciências da Computação | Turma 1CCPW | 1º Semestre 2026*
