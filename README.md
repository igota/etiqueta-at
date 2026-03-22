# 🩸 Sistema de Etiquetas - Agência Transfusional

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://semver.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-em%20produção-brightgreen)]()
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-000000.svg)](https://flask.palletsprojects.com/)
[![Waitress](https://img.shields.io/badge/Waitress-2.0+-4B8BBE.svg)](https://docs.pylonsproject.org/projects/waitress/en/stable/)
[![SeleniumBase](https://img.shields.io/badge/SeleniumBase-4.0+-43B02A.svg)](https://seleniumbase.io/)

## 📋 Sobre o Projeto

O **Sistema de Etiquetas da Agência Transfusional** é uma solução desenvolvida para otimizar o fluxo de trabalho da agência transfusional, permitindo a rápida captura e impressão de etiquetas de identificação de pacientes. O sistema se integra ao sistema hospitalar Vitae para buscar informações dos pacientes e gerar etiquetas padronizadas, reduzindo o tempo de atendimento e minimizando erros manuais.

### 🏥 Status Atual de Implantação

Sistema em produção na **Agência Transfusional do Hospital Regional Norte**, facilitando o processo de identificação de pacientes para coleta e transfusão de hemocomponentes.

## 🎯 Objetivos de Negócio

- **Agilidade no Atendimento:** Reduzir o tempo de busca e impressão de etiquetas de identificação
- **Precisão dos Dados:** Eliminar erros de digitação através da captura automática do sistema Vitae
- **Rastreabilidade:** Registrar todas as operações em logs para auditoria
- **Facilidade de Uso:** Interface simples e intuitiva para operadores da agência transfusional
- **Operação Discreta:** Aplicativo executado em background com ícone na bandeja do sistema

## 👥 Público-Alvo

- **Técnicos de Enfermagem:** Responsáveis pela coleta e identificação de pacientes
- **Farmacêuticos/Bioquímicos:** Responsáveis pela liberação de hemocomponentes
- **Coordenador da Agência Transfusional:** Gestão e auditoria do processo

## 🚀 Funcionalidades Principais

### 1. Interface de Bandeja do Sistema (System Tray)

O aplicativo roda em background com um ícone na bandeja do sistema Windows:

| Funcionalidade | Descrição |
|----------------|-----------|
| **Ícone na Bandeja** | Ícone personalizado (icone_etiquetaAT.jpg) na área de notificações |
| **Menu Contextual** | Opções disponíveis ao clicar com botão direito no ícone |
| **Sobre / Logs** | Abre uma janela de console para visualização dos logs do sistema |
| **Sair** | Encerra completamente o servidor e o aplicativo |

### 2. Sistema de Autenticação

O sistema possui autenticação para acesso seguro:

| Funcionalidade | Descrição |
|----------------|-----------|
| **Login Seguro** | Credenciais do usuário são validadas no sistema Vitae |
| **Sessão Persistente** | Mantém o usuário logado durante a utilização |
| **Logout Automático** | Encerramento seguro da sessão e do driver do navegador |

### 3. Busca de Pacientes por Prontuário

| Funcionalidade | Descrição |
|----------------|-----------|
| **Campo de Busca** | Entrada rápida do número de prontuário |
| **Validação** | Verificação se o prontuário existe no sistema Vitae |
| **Feedback Visual** | Mensagens de erro ou sucesso na busca |

### 4. Captura de Dados do Sistema Vitae

```mermaid
graph LR
    A[Sistema Vitae] -->|SeleniumBase| B[Captura Automática]
    B -->|Extração de Dados| C[Sistema de Etiquetas]
    C -->|Exibição| D[Etiqueta para Impressão]
    C -->|Registro| E[(Logs do Sistema)]
```
### 5. Arquitetura do Sistema
```mermaid
graph TB
    subgraph "Aplicação Principal"
        A[run.py - Ponto de Entrada]
        A1[Thread: Tray Icon]
        A2[Thread: Servidor Waitress]
    end
    
    subgraph "Camada de Apresentação"
        B[Flask Application - app.py]
        C[Tela de Login]
        D[Tela de Busca de Prontuário]
        E[Tela de Etiqueta]
    end
    
    subgraph "Camada de Servidor"
        F[Waitress WSGI Server]
        F1[Porta 5010]
    end
    
    subgraph "Automação"
        G[SeleniumBase Driver]
        G1[Chrome Headless]
    end
    
    subgraph "Armazenamento"
        H[(Logs do Sistema.log)]
    end
    
    subgraph "Integrações"
        I[Sistema Vitae]
    end
    
    A --> A1
    A --> A2
    A2 --> F
    F --> B
    B --> C
    B --> D
    B --> E
    B --> G
    G --> G1
    G1 --> I
    B --> H
```
### 6. Fluxo de Inicialização do Aplicativo
```mermaid

graph TD
    A[Execução do run.py] --> B[Inicia Thread do Tray Icon]
    A --> C[Inicia Thread do Servidor Waitress]
    B --> D[Ícone na Bandeja do Sistema]
    C --> E[Waitress serve app Flask]
    E --> F[Servidor ouvindo em 0.0.0.0:5010]
    D --> G[Menu: Sobre - Abre Logs]
    D --> H[Menu: Sair - Encerra Aplicação]
```
### 7. Fluxo de Autenticação e Busca
```mermaid
graph TD
    A[Usuário acessa página inicial] --> B[Preenche credenciais]
    B --> C{Login válido?}
    C -->|Sim| D[Redireciona para tela de busca]
    C -->|Não| E[Exibe mensagem de erro]
    D --> F[Usuário digita prontuário]
    F --> G[Captura dados no Vitae]
    G --> H{Paciente encontrado?}
    H -->|Sim| I[Gera etiqueta para impressão]
    H -->|Não| J[Exibe mensagem de erro]
    I --> K[Impressão da etiqueta]
    K --> F

```
### 8. Fluxo de Captura de Dados (SeleniumBase)
```mermaid
graph TD
    A[Recebe prontuário] --> B[Verifica sessão ativa]
    B --> C{Sessão ativa?}
    C -->|Não| D[Realiza login no Vitae]
    C -->|Sim| E[Fechar modais de notificação]
    D --> E
    E --> F[Navega para Assistência]
    F --> G[Seleciona opção de busca]
    G --> H[Digita prontuário]
    H --> I[Confirma busca]
    I --> J{É paciente obstétrico?}
    J -->|Sim| K[Captura dados da mãe]
    J -->|Não| L[Captura dados do paciente]
    K --> M[Extrai informações]
    L --> M
    M --> N[Retorna dados para exibição]
