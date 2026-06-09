"""
╔══════════════════════════════════════════════════════════════╗
║         SPACEGUARD — MISSION ENERGY MONITOR v1.0            ║
║   Sistema de Monitoramento de Missão Espacial Experimental  ║
║                                                              ║
║   FIAP — Ciências da Computação | 1CCPW | 1º Semestre 2026  ║
║   Disciplina: Soluções em Energias Renováveis e Sustentáveis║
║                                                              ║
║   Henrique Eduardo da Silveira  — RM 571803                 ║
║   Felipe Elze da Silva          — RM 572024                 ║
╚══════════════════════════════════════════════════════════════╝

DESCRIÇÃO:
    Sistema inteligente de monitoramento de sistemas energéticos
    para missão espacial experimental. Coleta, interpreta e exibe
    dados simulados de temperatura, energia solar, comunicação e
    status dos módulos operacionais. Gera alertas automáticos e
    toma decisões com base em lógica condicional avançada.

USO:
    python spaceguard.py           → inicia o monitor em loop
    python spaceguard.py --once    → gera um único relatório
    python spaceguard.py --html    → abre o dashboard web
"""

import random
import time
import datetime
import os
import sys
import json
import math
import webbrowser
import tempfile
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from enum import Enum


# ─────────────────────────────────────────────────────────────
#  ENUMS E CONSTANTES
# ─────────────────────────────────────────────────────────────

class AlertLevel(Enum):
    OK       = "OK"
    INFO     = "INFO"
    AVISO    = "AVISO"
    CRITICO  = "CRÍTICO"


class ModuleStatus(Enum):
    OPERACIONAL  = "OPERACIONAL"
    DEGRADADO    = "DEGRADADO"
    FALHA        = "FALHA"
    STANDBY      = "STANDBY"


# Limites operacionais de referência (baseados em missões reais NASA/ESA)
LIMITS = {
    "temp_paineis":      {"min": -160.0, "max": 120.0,  "warn_min": -100.0, "warn_max": 90.0},
    "temp_bateria":      {"min": -20.0,  "max": 45.0,   "warn_min": -10.0,  "warn_max": 38.0},
    "temp_computador":   {"min": 0.0,    "max": 70.0,   "warn_min": 10.0,   "warn_max": 60.0},
    "energia_solar_w":   {"min": 0.0,    "max": 8500.0, "warn_min": 500.0,  "warn_max": 8000.0},
    "bateria_pct":       {"min": 0.0,    "max": 100.0,  "warn_min": 20.0,   "warn_max": 95.0},
    "tensao_v":          {"min": 22.0,   "max": 34.0,   "warn_min": 24.0,   "warn_max": 32.0},
    "sinal_dbm":         {"min": -130.0, "max": -50.0,  "warn_min": -110.0, "warn_max": -55.0},
    "taxa_dados_kbps":   {"min": 0.0,    "max": 2000.0, "warn_min": 50.0,   "warn_max": 1800.0},
}


# ─────────────────────────────────────────────────────────────
#  DATACLASSES — ESTRUTURA DOS DADOS DA MISSÃO
# ─────────────────────────────────────────────────────────────

@dataclass
class ThermalData:
    """Dados de temperatura dos subsistemas"""
    paineis_solares_c: float = 0.0      # Temperatura dos painéis solares (°C)
    bateria_c: float = 0.0              # Temperatura das baterias (°C)
    computador_bordo_c: float = 0.0     # Temperatura do computador de bordo (°C)


@dataclass
class EnergyData:
    """Dados do sistema energético"""
    geracao_solar_w: float = 0.0        # Geração fotovoltaica (Watts)
    consumo_total_w: float = 0.0        # Consumo total da missão (Watts)
    bateria_pct: float = 0.0            # Nível de carga da bateria (%)
    tensao_barramento_v: float = 0.0    # Tensão do barramento (Volts)
    eficiencia_pct: float = 0.0         # Eficiência dos painéis (%)
    em_eclipse: bool = False             # Nave em zona de sombra orbital


@dataclass
class CommunicationData:
    """Dados do sistema de comunicação"""
    link_ativo: bool = True             # Link com estação terrestre ativo
    sinal_dbm: float = 0.0             # Potência do sinal recebido (dBm)
    taxa_dados_kbps: float = 0.0       # Taxa de transferência (Kbps)
    latencia_ms: float = 0.0           # Latência de comunicação (ms)
    pacotes_perdidos_pct: float = 0.0   # Percentual de pacotes perdidos


@dataclass
class ModuleData:
    """Status dos módulos operacionais"""
    propulsao: ModuleStatus = ModuleStatus.OPERACIONAL
    suporte_vida: ModuleStatus = ModuleStatus.OPERACIONAL
    cientifico: ModuleStatus = ModuleStatus.OPERACIONAL
    navegacao: ModuleStatus = ModuleStatus.OPERACIONAL
    comunicacao: ModuleStatus = ModuleStatus.OPERACIONAL
    energia: ModuleStatus = ModuleStatus.OPERACIONAL


@dataclass
class Alert:
    """Alerta gerado pelo sistema de IA"""
    nivel: AlertLevel
    modulo: str
    mensagem: str
    acao_recomendada: str
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().strftime("%H:%M:%S"))


@dataclass
class MissionSnapshot:
    """Snapshot completo da missão em um momento"""
    missao_id: str = "GS-2026-ALPHA"
    timestamp: str = ""
    ciclo: int = 0
    altitude_km: float = 408.0
    velocidade_kms: float = 7.66
    orbita_numero: int = 1
    fase_orbital: str = "ILUMINAÇÃO"
    thermal: ThermalData = field(default_factory=ThermalData)
    energy: EnergyData = field(default_factory=EnergyData)
    communication: CommunicationData = field(default_factory=CommunicationData)
    modules: ModuleData = field(default_factory=ModuleData)
    alerts: List[Alert] = field(default_factory=list)
    score_saude: int = 100


# ─────────────────────────────────────────────────────────────
#  SIMULADOR DE DADOS — FÍSICA ORBITAL SIMPLIFICADA
# ─────────────────────────────────────────────────────────────

class OrbitalSimulator:
    """
    Simula dados físicos realistas de uma missão em órbita baixa (LEO).
    Modela ciclos de iluminação/eclipse, degradação de baterias,
    variações térmicas e anomalias aleatórias.
    """

    def __init__(self):
        self.ciclo = 0
        self.orbita = 1
        self.fase = 0.0          # 0 a 360 graus de fase orbital
        self.anomalia_ativa = False
        self.anomalia_modulo = None
        self.historico_bateria = [85.0]  # Nível inicial

    def _fase_orbital(self) -> tuple:
        """Calcula iluminação/eclipse com base na fase orbital (período ~92 min)"""
        self.fase = (self.fase + 4.0) % 360.0  # 4° por ciclo de atualização
        if self.fase > 360.0:
            self.orbita += 1

        # Eclipsa ~35% de cada órbita
        em_eclipse = 128.0 < self.fase < 256.0
        fator_solar = 0.0 if em_eclipse else abs(math.sin(math.radians(self.fase)))
        return em_eclipse, fator_solar

    def _gerar_anomalia(self):
        """Injeta anomalia aleatória com probabilidade baixa"""
        if not self.anomalia_ativa and random.random() < 0.08:
            modulos = ["propulsao", "cientifico", "comunicacao", "energia"]
            self.anomalia_modulo = random.choice(modulos)
            self.anomalia_ativa = True
        elif self.anomalia_ativa and random.random() < 0.3:
            self.anomalia_ativa = False
            self.anomalia_modulo = None

    def generate(self, ciclo: int) -> MissionSnapshot:
        self.ciclo = ciclo
        self._gerar_anomalia()
        em_eclipse, fator_solar = self._fase_orbital()

        snap = MissionSnapshot()
        snap.ciclo = ciclo
        snap.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        snap.altitude_km = 408.0 + random.uniform(-2.0, 2.0)
        snap.velocidade_kms = 7.66 + random.uniform(-0.01, 0.01)
        snap.orbita_numero = self.orbita
        snap.fase_orbital = "ECLIPSE" if em_eclipse else "ILUMINAÇÃO"

        # ── ENERGIA ──────────────────────────────────────────
        geracao_base = 8200.0 * fator_solar
        anomalia_energia = 0.4 if (self.anomalia_ativa and self.anomalia_modulo == "energia") else 1.0
        geracao = geracao_base * anomalia_energia + random.gauss(0, 80)
        geracao = max(0.0, geracao)

        consumo_base = random.gauss(3800, 150)
        consumo = max(2000.0, consumo_base)

        # Modelo de bateria: carga/descarga com eficiência coulombiana
        bat_anterior = self.historico_bateria[-1]
        if em_eclipse:
            delta_bat = -(consumo / 100000.0) * random.uniform(0.8, 1.2)
        else:
            delta_bat = ((geracao - consumo) / 150000.0) * random.uniform(0.85, 1.0)
        bat_nova = max(5.0, min(100.0, bat_anterior + delta_bat))
        self.historico_bateria.append(bat_nova)
        if len(self.historico_bateria) > 50:
            self.historico_bateria.pop(0)

        eficiencia = random.gauss(28.5, 1.2) * anomalia_energia
        tensao = 28.0 + (bat_nova - 50.0) * 0.1 + random.gauss(0, 0.3)

        snap.energy = EnergyData(
            geracao_solar_w=round(geracao, 1),
            consumo_total_w=round(consumo, 1),
            bateria_pct=round(bat_nova, 1),
            tensao_barramento_v=round(tensao, 2),
            eficiencia_pct=round(max(0, eficiencia), 1),
            em_eclipse=em_eclipse,
        )

        # ── TEMPERATURA ───────────────────────────────────────
        temp_painel = (-100.0 if em_eclipse else 60.0) + random.gauss(0, 8)
        temp_bat = 15.0 + (bat_nova - 50.0) * 0.2 + random.gauss(0, 1.5)
        temp_comp = 42.0 + random.gauss(0, 3.0)
        if self.anomalia_ativa and self.anomalia_modulo == "energia":
            temp_bat += 18.0

        snap.thermal = ThermalData(
            paineis_solares_c=round(temp_painel, 1),
            bateria_c=round(temp_bat, 1),
            computador_bordo_c=round(temp_comp, 1),
        )

        # ── COMUNICAÇÃO ───────────────────────────────────────
        link_ok = not (self.anomalia_ativa and self.anomalia_modulo == "comunicacao")
        sinal = random.gauss(-85.0, 8.0) if link_ok else random.gauss(-125.0, 5.0)
        taxa = random.gauss(1200.0, 120.0) if link_ok else random.gauss(80.0, 40.0)
        latencia = 350.0 + random.gauss(0, 20.0)
        pacotes_perdidos = random.uniform(0, 2.0) if link_ok else random.uniform(15, 45.0)

        snap.communication = CommunicationData(
            link_ativo=link_ok,
            sinal_dbm=round(sinal, 1),
            taxa_dados_kbps=round(max(0, taxa), 0),
            latencia_ms=round(latencia, 0),
            pacotes_perdidos_pct=round(pacotes_perdidos, 1),
        )

        # ── MÓDULOS ───────────────────────────────────────────
        def status_modulo(nome):
            if self.anomalia_ativa and self.anomalia_modulo == nome:
                return random.choice([ModuleStatus.DEGRADADO, ModuleStatus.FALHA])
            return ModuleStatus.OPERACIONAL

        snap.modules = ModuleData(
            propulsao=status_modulo("propulsao"),
            suporte_vida=ModuleStatus.OPERACIONAL,
            cientifico=status_modulo("cientifico"),
            navegacao=ModuleStatus.OPERACIONAL,
            comunicacao=status_modulo("comunicacao") if not link_ok else ModuleStatus.OPERACIONAL,
            energia=status_modulo("energia"),
        )

        return snap


# ─────────────────────────────────────────────────────────────
#  MOTOR DE IA — ANÁLISE E TOMADA DE DECISÃO
# ─────────────────────────────────────────────────────────────

class AIDecisionEngine:
    """
    Motor de IA baseado em lógica condicional multi-camada.
    Analisa todos os subsistemas, calcula score de saúde da missão
    e gera alertas com ações corretivas recomendadas.
    """

    def analyze(self, snap: MissionSnapshot) -> MissionSnapshot:
        alerts = []
        score = 100

        # ── ANÁLISE DE ENERGIA ────────────────────────────────
        bat = snap.energy.bateria_pct
        if bat < 10.0:
            alerts.append(Alert(
                nivel=AlertLevel.CRITICO,
                modulo="BATERIA",
                mensagem=f"Nível crítico: {bat}% — risco de perda de energia primária",
                acao_recomendada="EMERGÊNCIA: Desligar sistemas não-essenciais. Ativar modo sobrevivência.",
            ))
            score -= 35
        elif bat < 20.0:
            alerts.append(Alert(
                nivel=AlertLevel.AVISO,
                modulo="BATERIA",
                mensagem=f"Carga baixa: {bat}% — monitorar consumo",
                acao_recomendada="Reduzir carga de módulo científico. Aguardar saída de eclipse.",
            ))
            score -= 15
        elif bat > 97.0:
            alerts.append(Alert(
                nivel=AlertLevel.INFO,
                modulo="BATERIA",
                mensagem=f"Bateria no limite superior: {bat}%",
                acao_recomendada="Considerar desvio de carga para evitar sobretensão.",
            ))
            score -= 3

        tensao = snap.energy.tensao_barramento_v
        if tensao < 24.0 or tensao > 32.0:
            alerts.append(Alert(
                nivel=AlertLevel.CRITICO,
                modulo="ENERGIA",
                mensagem=f"Tensão do barramento fora de especificação: {tensao}V",
                acao_recomendada="Acionar regulador de tensão backup. Verificar células fotovoltaicas.",
            ))
            score -= 25

        if not snap.energy.em_eclipse and snap.energy.geracao_solar_w < 500.0:
            alerts.append(Alert(
                nivel=AlertLevel.AVISO,
                modulo="PAINÉIS SOLARES",
                mensagem=f"Geração anormalmente baixa em iluminação: {snap.energy.geracao_solar_w}W",
                acao_recomendada="Verificar orientação dos painéis. Possível degradação ou obstrução.",
            ))
            score -= 20

        # ── ANÁLISE TÉRMICA ───────────────────────────────────
        tb = snap.thermal.bateria_c
        if tb > 38.0:
            alerts.append(Alert(
                nivel=AlertLevel.AVISO if tb < 44.0 else AlertLevel.CRITICO,
                modulo="TEMPERATURA",
                mensagem=f"Temperatura da bateria elevada: {tb}°C",
                acao_recomendada="Ativar sistema de resfriamento. Reduzir carga de corrente.",
            ))
            score -= 20 if tb >= 44.0 else 10
        elif tb < -10.0:
            alerts.append(Alert(
                nivel=AlertLevel.AVISO,
                modulo="TEMPERATURA",
                mensagem=f"Bateria abaixo da temperatura mínima: {tb}°C",
                acao_recomendada="Ativar aquecedores da bateria. Aguardar normalização térmica.",
            ))
            score -= 10

        tc = snap.thermal.computador_bordo_c
        if tc > 60.0:
            alerts.append(Alert(
                nivel=AlertLevel.CRITICO,
                modulo="COMPUTADOR DE BORDO",
                mensagem=f"Processador superaquecido: {tc}°C",
                acao_recomendada="Reduzir carga computacional. Ativar dissipador térmico passivo.",
            ))
            score -= 20

        # ── ANÁLISE DE COMUNICAÇÃO ────────────────────────────
        if not snap.communication.link_ativo:
            alerts.append(Alert(
                nivel=AlertLevel.CRITICO,
                modulo="COMUNICAÇÃO",
                mensagem="Link com estação terrestre perdido",
                acao_recomendada="Executar protocolo de reconexão. Ativar antena de contingência.",
            ))
            score -= 30
        else:
            if snap.communication.sinal_dbm < -110.0:
                alerts.append(Alert(
                    nivel=AlertLevel.AVISO,
                    modulo="COMUNICAÇÃO",
                    mensagem=f"Sinal fraco: {snap.communication.sinal_dbm} dBm",
                    acao_recomendada="Reorientar antena. Aumentar potência de transmissão.",
                ))
                score -= 10
            if snap.communication.pacotes_perdidos_pct > 10.0:
                alerts.append(Alert(
                    nivel=AlertLevel.AVISO,
                    modulo="COMUNICAÇÃO",
                    mensagem=f"Alta taxa de perda de pacotes: {snap.communication.pacotes_perdidos_pct}%",
                    acao_recomendada="Ativar protocolo de retransmissão ARQ.",
                ))
                score -= 8

        # ── ANÁLISE DE MÓDULOS ────────────────────────────────
        modulos_dict = asdict(snap.modules)
        for nome_mod, status_val in modulos_dict.items():
            status = ModuleStatus(status_val)
            nome_display = nome_mod.upper().replace("_", " ")
            if status == ModuleStatus.FALHA:
                alerts.append(Alert(
                    nivel=AlertLevel.CRITICO,
                    modulo=nome_display,
                    mensagem=f"Módulo {nome_display} em FALHA",
                    acao_recomendada=f"Isolar módulo {nome_display}. Acionar backup redundante.",
                ))
                score -= 25
            elif status == ModuleStatus.DEGRADADO:
                alerts.append(Alert(
                    nivel=AlertLevel.AVISO,
                    modulo=nome_display,
                    mensagem=f"Módulo {nome_display} DEGRADADO",
                    acao_recomendada=f"Monitorar {nome_display} continuamente. Preparar protocolo de contingência.",
                ))
                score -= 12

        # Sem alertas = bônus de estabilidade
        if not alerts:
            alerts.append(Alert(
                nivel=AlertLevel.OK,
                modulo="SISTEMA",
                mensagem="Todos os sistemas operando dentro dos parâmetros nominais",
                acao_recomendada="Continuar monitoramento de rotina.",
            ))

        snap.alerts = alerts
        snap.score_saude = max(0, min(100, score))
        return snap


# ─────────────────────────────────────────────────────────────
#  DISPLAY — TERMINAL (RICH TEXT)
# ─────────────────────────────────────────────────────────────

CORES = {
    "reset":   "\033[0m",
    "bold":    "\033[1m",
    "verde":   "\033[92m",
    "amarelo": "\033[93m",
    "vermelho":"\033[91m",
    "azul":    "\033[94m",
    "ciano":   "\033[96m",
    "branco":  "\033[97m",
    "cinza":   "\033[90m",
    "magenta": "\033[95m",
    "bg_verm": "\033[41m",
    "bg_amar": "\033[43m\033[30m",
    "bg_verd": "\033[42m\033[30m",
    "bg_azul": "\033[44m",
}

def c(texto, cor): return f"{CORES.get(cor,'')}{texto}{CORES['reset']}"


def barra_progresso(valor, maximo, largura=20, cor="verde"):
    preenchido = int((valor / maximo) * largura)
    barra = "█" * preenchido + "░" * (largura - preenchido)
    return c(f"[{barra}]", cor)


def nivel_cor(nivel: AlertLevel):
    return {"OK": "verde", "INFO": "azul", "AVISO": "amarelo", "CRÍTICO": "vermelho"}.get(nivel.value, "branco")


def status_cor(s: ModuleStatus):
    return {"OPERACIONAL": "verde", "DEGRADADO": "amarelo", "FALHA": "vermelho", "STANDBY": "ciano"}.get(s.value, "branco")


def exibir_snapshot(snap: MissionSnapshot):
    os.system("cls" if os.name == "nt" else "clear")
    W = 70
    linha = "─" * W

    print(c("╔" + "═" * W + "╗", "ciano"))
    print(c("║", "ciano") + c(" ⚡ SPACEGUARD — MISSION ENERGY MONITOR v1.0".center(W), "bold") + c("║", "ciano"))
    print(c("║", "ciano") + c(f"  Missão: {snap.missao_id} │ Ciclo #{snap.ciclo:04d} │ {snap.timestamp}".center(W), "cinza") + c("║", "ciano"))
    print(c("╚" + "═" * W + "╝", "ciano"))

    # ── ORBITAL ──────────────────────────────────────────────
    print(f"\n{c('▸ POSIÇÃO ORBITAL', 'azul')}")
    print(f"  Altitude   : {c(f'{snap.altitude_km:.1f} km', 'branco')}   Velocidade: {c(f'{snap.velocidade_kms:.2f} km/s', 'branco')}")
    fase_cor = "amarelo" if snap.fase_orbital == "ECLIPSE" else "amarelo"
    fase_icone = "🌑" if snap.fase_orbital == "ECLIPSE" else "☀️"
    print(f"  Órbita Nº  : {c(str(snap.orbita_numero), 'branco')}          Fase: {c(f'{fase_icone} {snap.fase_orbital}', 'amarelo')}")

    # ── ENERGIA ──────────────────────────────────────────────
    print(f"\n{c('▸ SISTEMA ENERGÉTICO', 'azul')}")
    e = snap.energy
    bat_cor = "verde" if e.bateria_pct > 40 else ("amarelo" if e.bateria_pct > 20 else "vermelho")
    print(f"  Geração Solar  : {c(f'{e.geracao_solar_w:7.1f} W', 'verde')}   Consumo   : {c(f'{e.consumo_total_w:6.1f} W', 'amarelo')}")
    print(f"  Tensão Barrm.  : {c(f'{e.tensao_barramento_v:5.2f} V', 'branco')}        Eficiência: {c(f'{e.eficiencia_pct:.1f}%', 'ciano')}")
    print(f"  Bateria        : {barra_progresso(e.bateria_pct, 100, cor=bat_cor)} {c(f'{e.bateria_pct:.1f}%', bat_cor)}")

    # ── TEMPERATURA ───────────────────────────────────────────
    print(f"\n{c('▸ SISTEMA TÉRMICO', 'azul')}")
    t = snap.thermal
    def tc_display(val, warn_max):
        cor = "vermelho" if val > warn_max else ("amarelo" if val > warn_max * 0.85 else "verde")
        return c(f"{val:+6.1f}°C", cor)
    print(f"  Painéis Solares: {tc_display(t.paineis_solares_c, 90)}   Bateria  : {tc_display(t.bateria_c, 38)}")
    print(f"  Computador Bordo: {tc_display(t.computador_bordo_c, 60)}")

    # ── COMUNICAÇÃO ───────────────────────────────────────────
    print(f"\n{c('▸ SISTEMA DE COMUNICAÇÃO', 'azul')}")
    cm = snap.communication
    link_txt = c("● ATIVO", "verde") if cm.link_ativo else c("● PERDIDO", "vermelho")
    print(f"  Link Estação   : {link_txt}          Latência : {c(f'{cm.latencia_ms:.0f} ms', 'branco')}")
    print(f"  Sinal          : {c(f'{cm.sinal_dbm:.1f} dBm', 'ciano')}        Taxa dados: {c(f'{cm.taxa_dados_kbps:.0f} kbps', 'ciano')}")
    print(f"  Pacotes perdidos: {c(f'{cm.pacotes_perdidos_pct:.1f}%', 'vermelho' if cm.pacotes_perdidos_pct > 10 else 'verde')}")

    # ── MÓDULOS ───────────────────────────────────────────────
    print(f"\n{c('▸ STATUS DOS MÓDULOS', 'azul')}")
    mods = snap.modules
    linha_mods = [
        ("PROPULSÃO",     mods.propulsao),
        ("SUPORTE VIDA",  mods.suporte_vida),
        ("CIENTÍFICO",    mods.cientifico),
        ("NAVEGAÇÃO",     mods.navegacao),
        ("COMUNICAÇÃO",   mods.comunicacao),
        ("ENERGIA",       mods.energia),
    ]
    for i, (nome, status) in enumerate(linha_mods):
        icone = {"OPERACIONAL": "✓", "DEGRADADO": "⚠", "FALHA": "✗", "STANDBY": "○"}[status.value]
        print(f"  {c(icone, status_cor(status))} {nome:<14}: {c(status.value, status_cor(status))}", end="   " if i % 2 == 0 else "\n")
    if len(linha_mods) % 2 != 0:
        print()

    # ── SCORE DE SAÚDE ────────────────────────────────────────
    print(f"\n{c('▸ ÍNDICE DE SAÚDE DA MISSÃO', 'azul')}")
    score = snap.score_saude
    score_cor = "verde" if score >= 70 else ("amarelo" if score >= 40 else "vermelho")
    print(f"  {barra_progresso(score, 100, largura=30, cor=score_cor)} {c(f'{score}/100', score_cor)}")

    # ── ALERTAS ───────────────────────────────────────────────
    print(f"\n{c('▸ ALERTAS DO SISTEMA DE IA', 'azul')}")
    for alerta in snap.alerts[:6]:
        nivel_txt = f"[{alerta.nivel.value:8s}]"
        print(f"  {c(nivel_txt, nivel_cor(alerta.nivel))} {c(alerta.modulo, 'branco')}: {alerta.mensagem}")
        print(f"  {c('→', 'cinza')} {c(alerta.acao_recomendada, 'cinza')}")

    print(f"\n{c(linha, 'cinza')}")
    print(c("  FIAP 1CCPW 2026 │ Henrique RM:571803 │ Felipe RM:572024", "cinza"))
    print(c(f"  Próxima leitura em 5s… (Ctrl+C para encerrar)", "cinza"))


# ─────────────────────────────────────────────────────────────
#  DASHBOARD HTML — GERAÇÃO E ABERTURA NO BROWSER
# ─────────────────────────────────────────────────────────────

def gerar_dashboard_html(historico: list) -> str:
    """Gera HTML do dashboard com dados do histórico"""
    if not historico:
        return "<html><body>Sem dados</body></html>"

    snap = historico[-1]
    e = snap.energy
    t = snap.thermal
    cm = snap.communication

    # Preparar séries temporais
    timestamps = [h.timestamp.split(" ")[1] for h in historico[-20:]]
    bat_series = [h.energy.bateria_pct for h in historico[-20:]]
    solar_series = [h.energy.geracao_solar_w for h in historico[-20:]]
    consumo_series = [h.energy.consumo_total_w for h in historico[-20:]]
    temp_bat_series = [h.thermal.bateria_c for h in historico[-20:]]

    score = snap.score_saude
    score_cor = "#00ff88" if score >= 70 else ("#ffcc00" if score >= 40 else "#ff4444")

    alertas_html = ""
    for a in snap.alerts[:5]:
        cor_map = {"OK": "#00ff88", "INFO": "#4488ff", "AVISO": "#ffcc00", "CRÍTICO": "#ff4444"}
        cor = cor_map.get(a.nivel.value, "#ffffff")
        alertas_html += f"""
        <div class="alert-item" style="border-left: 3px solid {cor};">
            <span class="alert-badge" style="background:{cor};">{a.nivel.value}</span>
            <div>
                <div class="alert-title">{a.modulo}: {a.mensagem}</div>
                <div class="alert-action">▶ {a.acao_recomendada}</div>
            </div>
        </div>"""

    modulos_html = ""
    for nome, status in [
        ("PROPULSÃO", snap.modules.propulsao),
        ("SUPORTE VIDA", snap.modules.suporte_vida),
        ("CIENTÍFICO", snap.modules.cientifico),
        ("NAVEGAÇÃO", snap.modules.navegacao),
        ("COMUNICAÇÃO", snap.modules.comunicacao),
        ("ENERGIA", snap.modules.energia),
    ]:
        cor_mod = {"OPERACIONAL": "#00ff88", "DEGRADADO": "#ffcc00", "FALHA": "#ff4444", "STANDBY": "#4488ff"}[status.value]
        icone_mod = {"OPERACIONAL": "✓", "DEGRADADO": "⚠", "FALHA": "✗", "STANDBY": "○"}[status.value]
        modulos_html += f"""
        <div class="module-card" style="border-color:{cor_mod}22">
            <div class="module-icon" style="color:{cor_mod}">{icone_mod}</div>
            <div class="module-name">{nome}</div>
            <div class="module-status" style="color:{cor_mod}">{status.value}</div>
        </div>"""

    ts_js = str(timestamps)
    bat_js = str(bat_series)
    solar_js = str(solar_series)
    consumo_js = str(consumo_series)
    temp_bat_js = str(temp_bat_series)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SpaceGuard — Mission Energy Monitor</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@300;400;600;700&display=swap');

:root {{
  --bg: #030a14;
  --panel: #0a1628;
  --border: #0d2440;
  --accent: #00d4ff;
  --accent2: #00ff88;
  --warn: #ffcc00;
  --crit: #ff4444;
  --text: #c8deff;
  --muted: #4a6080;
  --glow: 0 0 20px rgba(0,212,255,0.15);
}}

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
  background: var(--bg);
  color: var(--text);
  font-family: 'Rajdhani', sans-serif;
  font-size: 15px;
  min-height: 100vh;
  background-image:
    radial-gradient(ellipse at 20% 50%, rgba(0,50,100,0.15) 0%, transparent 60%),
    radial-gradient(ellipse at 80% 20%, rgba(0,80,60,0.1) 0%, transparent 50%);
}}

/* Grid de estrelas */
body::before {{
  content: '';
  position: fixed;
  inset: 0;
  background-image:
    radial-gradient(1px 1px at 10% 15%, rgba(255,255,255,0.4) 0%, transparent 100%),
    radial-gradient(1px 1px at 30% 70%, rgba(255,255,255,0.3) 0%, transparent 100%),
    radial-gradient(1px 1px at 55% 25%, rgba(255,255,255,0.35) 0%, transparent 100%),
    radial-gradient(1px 1px at 75% 60%, rgba(255,255,255,0.25) 0%, transparent 100%),
    radial-gradient(1px 1px at 90% 10%, rgba(255,255,255,0.4) 0%, transparent 100%),
    radial-gradient(1px 1px at 45% 85%, rgba(255,255,255,0.3) 0%, transparent 100%),
    radial-gradient(1px 1px at 20% 90%, rgba(255,255,255,0.2) 0%, transparent 100%),
    radial-gradient(1px 1px at 65% 45%, rgba(255,255,255,0.35) 0%, transparent 100%);
  pointer-events: none;
  z-index: 0;
}}

.container {{ max-width: 1400px; margin: 0 auto; padding: 20px; position: relative; z-index: 1; }}

header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-bottom: 2px solid var(--accent);
  border-radius: 4px;
  margin-bottom: 20px;
  box-shadow: var(--glow);
}}

.header-left {{ display: flex; align-items: center; gap: 16px; }}
.logo {{ font-family: 'Share Tech Mono', monospace; font-size: 22px; color: var(--accent); letter-spacing: 3px; }}
.logo span {{ color: var(--accent2); }}
.subtitle {{ color: var(--muted); font-size: 12px; letter-spacing: 1px; }}

.mission-id {{
  font-family: 'Share Tech Mono', monospace;
  background: rgba(0,212,255,0.08);
  border: 1px solid var(--accent);
  padding: 6px 14px;
  border-radius: 2px;
  font-size: 13px;
  color: var(--accent);
}}

.timestamp {{ font-family: 'Share Tech Mono', monospace; font-size: 12px; color: var(--muted); margin-top: 4px; }}

/* Score de saúde */
.health-bar-wrap {{
  display: flex;
  align-items: center;
  gap: 12px;
}}
.health-score {{
  font-family: 'Share Tech Mono', monospace;
  font-size: 28px;
  font-weight: bold;
  color: {score_cor};
}}
.health-label {{ font-size: 11px; color: var(--muted); letter-spacing: 1px; }}

/* Grid principal */
.main-grid {{
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  grid-template-rows: auto auto auto;
  gap: 16px;
  margin-bottom: 16px;
}}

.panel {{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 20px;
  box-shadow: var(--glow);
  transition: border-color 0.3s;
}}
.panel:hover {{ border-color: rgba(0,212,255,0.3); }}

.panel-title {{
  font-family: 'Share Tech Mono', monospace;
  font-size: 11px;
  letter-spacing: 2px;
  color: var(--accent);
  text-transform: uppercase;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 8px;
}}
.panel-title::before {{
  content: '';
  display: inline-block;
  width: 6px; height: 6px;
  background: var(--accent);
  border-radius: 50%;
  animation: pulse 2s infinite;
}}
@keyframes pulse {{
  0%, 100% {{ opacity: 1; }}
  50% {{ opacity: 0.3; }}
}}

/* Métricas */
.metric {{ margin-bottom: 14px; }}
.metric-label {{ font-size: 11px; color: var(--muted); letter-spacing: 1px; text-transform: uppercase; margin-bottom: 4px; }}
.metric-value {{
  font-family: 'Share Tech Mono', monospace;
  font-size: 22px;
  font-weight: bold;
  color: var(--text);
}}
.metric-unit {{ font-size: 12px; color: var(--muted); margin-left: 4px; }}

.metric-row {{ display: flex; gap: 20px; flex-wrap: wrap; }}

/* Barra de progresso */
.prog-wrap {{ margin-top: 6px; }}
.prog-track {{ background: rgba(255,255,255,0.06); border-radius: 2px; height: 6px; overflow: hidden; }}
.prog-bar {{ height: 100%; border-radius: 2px; transition: width 0.5s ease; }}

/* Status badge */
.badge {{
  display: inline-block;
  padding: 3px 10px;
  border-radius: 2px;
  font-size: 11px;
  font-family: 'Share Tech Mono', monospace;
  letter-spacing: 1px;
}}
.badge-ok    {{ background: rgba(0,255,136,0.12); color: #00ff88; border: 1px solid rgba(0,255,136,0.3); }}
.badge-warn  {{ background: rgba(255,204,0,0.12);  color: #ffcc00; border: 1px solid rgba(255,204,0,0.3); }}
.badge-crit  {{ background: rgba(255,68,68,0.12);   color: #ff4444; border: 1px solid rgba(255,68,68,0.3); }}
.badge-info  {{ background: rgba(68,136,255,0.12);  color: #4488ff; border: 1px solid rgba(68,136,255,0.3); }}

/* Orbital status */
.orbital-info {{ display: flex; gap: 24px; flex-wrap: wrap; margin-bottom: 12px; }}
.orb-item {{ }}
.orb-value {{ font-family: 'Share Tech Mono', monospace; font-size: 18px; color: var(--text); }}
.orb-unit  {{ font-size: 11px; color: var(--muted); }}

/* Módulos grid */
.modules-grid {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}}

.module-card {{
  background: rgba(255,255,255,0.03);
  border: 1px solid;
  border-radius: 4px;
  padding: 12px;
  text-align: center;
  transition: all 0.3s;
}}
.module-icon {{ font-size: 20px; margin-bottom: 4px; }}
.module-name {{ font-size: 10px; color: var(--muted); letter-spacing: 1px; margin-bottom: 4px; }}
.module-status {{ font-size: 11px; font-family: 'Share Tech Mono', monospace; }}

/* Alertas */
.alert-item {{
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 12px;
  margin-bottom: 8px;
  background: rgba(255,255,255,0.02);
  border-radius: 2px;
}}
.alert-badge {{
  padding: 2px 8px;
  border-radius: 2px;
  font-size: 10px;
  font-family: 'Share Tech Mono', monospace;
  white-space: nowrap;
  color: #000;
  font-weight: bold;
  min-width: 60px;
  text-align: center;
}}
.alert-title {{ font-size: 13px; margin-bottom: 2px; }}
.alert-action {{ font-size: 11px; color: var(--muted); font-style: italic; }}

/* Charts */
.chart-wrap {{ position: relative; height: 160px; }}
.full-width {{ grid-column: 1 / -1; }}
.two-thirds {{ grid-column: 1 / 3; }}

/* Rodapé */
footer {{
  text-align: center;
  padding: 16px;
  font-family: 'Share Tech Mono', monospace;
  font-size: 11px;
  color: var(--muted);
  border-top: 1px solid var(--border);
  margin-top: 8px;
  letter-spacing: 1px;
}}
</style>
</head>
<body>
<div class="container">

  <header>
    <div class="header-left">
      <div>
        <div class="logo">SPACE<span>GUARD</span></div>
        <div class="subtitle">MISSION ENERGY MONITOR v1.0 │ FIAP 1CCPW 2026</div>
      </div>
      <div class="mission-id">{snap.missao_id} │ CICLO #{snap.ciclo:04d}</div>
    </div>
    <div>
      <div class="health-bar-wrap">
        <div>
          <div class="health-label">ÍNDICE DE SAÚDE</div>
          <div class="health-score">{score}<span style="font-size:14px;color:var(--muted)">/100</span></div>
        </div>
      </div>
      <div class="timestamp">{snap.timestamp}</div>
    </div>
  </header>

  <div class="main-grid">

    <!-- ORBITAL -->
    <div class="panel">
      <div class="panel-title">Posição Orbital</div>
      <div class="orbital-info">
        <div class="orb-item">
          <div class="orb-value">{snap.altitude_km:.1f}</div>
          <div class="orb-unit">km ALTITUDE</div>
        </div>
        <div class="orb-item">
          <div class="orb-value">{snap.velocidade_kms:.2f}</div>
          <div class="orb-unit">km/s VELOCIDADE</div>
        </div>
        <div class="orb-item">
          <div class="orb-value">#{snap.orbita_numero}</div>
          <div class="orb-unit">ÓRBITA</div>
        </div>
      </div>
      <div style="margin-top:8px">
        <span class="badge {'badge-warn' if snap.fase_orbital == 'ECLIPSE' else 'badge-ok'}">
          {'🌑 ECLIPSE' if snap.fase_orbital == 'ECLIPSE' else '☀ ILUMINAÇÃO'}
        </span>
      </div>
    </div>

    <!-- ENERGIA -->
    <div class="panel">
      <div class="panel-title">Sistema Energético</div>
      <div class="metric-row">
        <div class="metric">
          <div class="metric-label">Geração Solar</div>
          <div class="metric-value">{e.geracao_solar_w:.0f}<span class="metric-unit">W</span></div>
        </div>
        <div class="metric">
          <div class="metric-label">Consumo</div>
          <div class="metric-value">{e.consumo_total_w:.0f}<span class="metric-unit">W</span></div>
        </div>
      </div>
      <div class="metric">
        <div class="metric-label">Bateria</div>
        <div class="metric-value">{e.bateria_pct:.1f}<span class="metric-unit">%</span></div>
        <div class="prog-wrap">
          <div class="prog-track">
            <div class="prog-bar" style="width:{e.bateria_pct}%;background:{'#00ff88' if e.bateria_pct > 40 else ('#ffcc00' if e.bateria_pct > 20 else '#ff4444')}"></div>
          </div>
        </div>
      </div>
      <div class="metric">
        <div class="metric-label">Tensão Barramento</div>
        <div class="metric-value">{e.tensao_barramento_v:.2f}<span class="metric-unit">V</span></div>
      </div>
    </div>

    <!-- TEMPERATURA -->
    <div class="panel">
      <div class="panel-title">Sistema Térmico</div>
      <div class="metric">
        <div class="metric-label">Painéis Solares</div>
        <div class="metric-value" style="color:{'#ff4444' if t.paineis_solares_c > 90 else '#c8deff'}">{t.paineis_solares_c:+.1f}<span class="metric-unit">°C</span></div>
      </div>
      <div class="metric">
        <div class="metric-label">Bateria</div>
        <div class="metric-value" style="color:{'#ff4444' if t.bateria_c > 38 else ('#ffcc00' if t.bateria_c > 30 else '#00ff88')}">{t.bateria_c:+.1f}<span class="metric-unit">°C</span></div>
      </div>
      <div class="metric">
        <div class="metric-label">Computador de Bordo</div>
        <div class="metric-value" style="color:{'#ff4444' if t.computador_bordo_c > 60 else '#c8deff'}">{t.computador_bordo_c:+.1f}<span class="metric-unit">°C</span></div>
      </div>
    </div>

    <!-- GRÁFICO: Bateria e Energia -->
    <div class="panel two-thirds">
      <div class="panel-title">Histórico — Bateria & Geração Solar</div>
      <div class="chart-wrap">
        <canvas id="chartEnergy"></canvas>
      </div>
    </div>

    <!-- COMUNICAÇÃO -->
    <div class="panel">
      <div class="panel-title">Comunicação</div>
      <div style="margin-bottom:12px">
        <span class="badge {'badge-ok' if cm.link_ativo else 'badge-crit'}">
          {'● LINK ATIVO' if cm.link_ativo else '● LINK PERDIDO'}
        </span>
      </div>
      <div class="metric">
        <div class="metric-label">Sinal</div>
        <div class="metric-value">{cm.sinal_dbm:.1f}<span class="metric-unit">dBm</span></div>
      </div>
      <div class="metric">
        <div class="metric-label">Taxa de Dados</div>
        <div class="metric-value">{cm.taxa_dados_kbps:.0f}<span class="metric-unit">kbps</span></div>
      </div>
      <div class="metric">
        <div class="metric-label">Latência</div>
        <div class="metric-value">{cm.latencia_ms:.0f}<span class="metric-unit">ms</span></div>
      </div>
      <div class="metric">
        <div class="metric-label">Pacotes Perdidos</div>
        <div class="metric-value" style="color:{'#ff4444' if cm.pacotes_perdidos_pct > 10 else '#00ff88'}">{cm.pacotes_perdidos_pct:.1f}<span class="metric-unit">%</span></div>
      </div>
    </div>

    <!-- MÓDULOS -->
    <div class="panel full-width">
      <div class="panel-title">Status dos Módulos Operacionais</div>
      <div class="modules-grid">
        {modulos_html}
      </div>
    </div>

    <!-- ALERTAS -->
    <div class="panel full-width">
      <div class="panel-title">Alertas do Sistema de IA</div>
      {alertas_html}
    </div>

  </div>

  <footer>
    SPACEGUARD v1.0 │ FIAP — SOLUÇÕES EM ENERGIAS RENOVÁVEIS E SUSTENTÁVEIS │ 1CCPW 2026<br>
    Henrique Eduardo da Silveira RM:571803 │ Felipe Elze da Silva RM:572024
  </footer>

</div>

<script>
const ctx = document.getElementById('chartEnergy').getContext('2d');
const labels = {ts_js};
const batData = {bat_js};
const solarData = {solar_js};
const consumoData = {consumo_js};

new Chart(ctx, {{
  type: 'line',
  data: {{
    labels: labels,
    datasets: [
      {{
        label: 'Bateria (%)',
        data: batData,
        borderColor: '#00ff88',
        backgroundColor: 'rgba(0,255,136,0.05)',
        tension: 0.4,
        yAxisID: 'yBat',
        pointRadius: 2,
        borderWidth: 2,
      }},
      {{
        label: 'Geração Solar (W)',
        data: solarData,
        borderColor: '#00d4ff',
        backgroundColor: 'rgba(0,212,255,0.05)',
        tension: 0.4,
        yAxisID: 'ySolar',
        pointRadius: 2,
        borderWidth: 2,
      }},
      {{
        label: 'Consumo (W)',
        data: consumoData,
        borderColor: '#ffcc00',
        backgroundColor: 'rgba(255,204,0,0.05)',
        tension: 0.4,
        yAxisID: 'ySolar',
        pointRadius: 2,
        borderWidth: 2,
        borderDash: [4,4],
      }},
    ]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{ labels: {{ color: '#4a6080', font: {{ size: 10, family: 'Share Tech Mono' }} }} }},
    }},
    scales: {{
      x: {{
        ticks: {{ color: '#4a6080', font: {{ size: 9, family: 'Share Tech Mono' }}, maxTicksLimit: 8 }},
        grid: {{ color: 'rgba(255,255,255,0.04)' }},
      }},
      yBat: {{
        type: 'linear', position: 'left',
        min: 0, max: 100,
        ticks: {{ color: '#00ff88', font: {{ size: 9 }}, callback: v => v + '%' }},
        grid: {{ color: 'rgba(255,255,255,0.04)' }},
      }},
      ySolar: {{
        type: 'linear', position: 'right',
        min: 0,
        ticks: {{ color: '#00d4ff', font: {{ size: 9 }}, callback: v => v + 'W' }},
        grid: {{ drawOnChartArea: false }},
      }},
    }}
  }}
}});
</script>
</body>
</html>"""
    return html


def abrir_dashboard(historico: list):
    html = gerar_dashboard_html(historico)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html)
        caminho = f.name
    print(f"\n  Dashboard salvo em: {caminho}")
    webbrowser.open(f"file://{caminho}")
    return caminho


# ─────────────────────────────────────────────────────────────
#  LOOP PRINCIPAL
# ─────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    modo_once = "--once" in args
    modo_html = "--html" in args

    simulador = OrbitalSimulator()
    motor_ia  = AIDecisionEngine()
    historico: List[MissionSnapshot] = []

    print(c("\n  ⚡ SpaceGuard inicializando...\n", "ciano"))
    time.sleep(0.5)

    ciclo = 1
    try:
        while True:
            raw = simulador.generate(ciclo)
            snap = motor_ia.analyze(raw)
            historico.append(snap)
            if len(historico) > 100:
                historico.pop(0)

            exibir_snapshot(snap)

            if modo_once:
                break

            if modo_html or (ciclo % 10 == 0):
                abrir_dashboard(historico)

            time.sleep(5)
            ciclo += 1

    except KeyboardInterrupt:
        print(c("\n\n  Monitoramento encerrado pelo operador.\n", "amarelo"))
        if historico:
            print(c("  Gerando relatório final HTML...", "ciano"))
            caminho = abrir_dashboard(historico)
            print(c(f"  Dashboard final: {caminho}\n", "verde"))


if __name__ == "__main__":
    main()
