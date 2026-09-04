# CLAUDE.md

Este arquivo fornece orientações ao Claude Code (claude.ai/code) ao trabalhar com o código deste repositório.

## O Que Este Projeto Faz

**Etiqueta AT** (Agência Transfusional) é um aplicativo desktop para Windows que gera etiquetas de pacientes do banco de sangue para os hospitais ISGH/HRN. Ele automatiza o login e a raspagem de dados do sistema interno do hospital (`http://10.2.2.8:8080/pacientehrn/login.jsf`) e renderiza uma etiqueta imprimível de 47×30mm.

## Executando o App

```bash
# Modo desenvolvimento (servidor Flask, sem ícone na bandeja)
python app.py

# Modo produção (Waitress + ícone na bandeja do sistema)
python run.py
```

O app roda em `http://localhost:5000`. Os logs são gravados em `Logs do Sistema.log` no diretório de trabalho.

## Gerando o Executável

```bash
# Build com PyInstaller usando o spec existente
pyinstaller run.spec
```

O resultado vai para `dist/run.exe`. O script do Inno Setup em `text\script instalado inno setup.iss` empacota o `dist\run.exe` em um instalador e o registra como serviço Windows via NSSM (`tools\nssm.exe`).

## Instalando Dependências

```bash
pip install -r text/requirements.txt
```

Pacotes principais: `flask`, `seleniumbase`, `waitress`, `pystray`, `Pillow`.

## Arquitetura

### Fluxo

```
run.py  →  pystray (ícone na bandeja, thread daemon)
        →  waitress.serve(app)  →  app.py (rotas Flask)
```

### `app.py` — Lógica Principal

- **`driver` global**: Um único `seleniumbase.Driver` (Chrome headless) é reutilizado em todas as requisições. É criado na primeira chamada e destruído apenas no logout.
- **`login_if_needed()`**: Abre a página de login JSF do hospital, envia as credenciais e verifica o redirecionamento para `paginaPrincipal.jsf`.
- **`get_patient_info()`**: Navega pela interface do hospital usando seletores XPath para localizar o prontuário, trata um modal de obstetrícia e extrai nome, setor, data de nascimento e sexo.
- **Rotas**: `GET/POST /` (login), `GET/POST /prontuario` (busca de paciente), `GET /logout` (encerra o Chrome, limpa a sessão).

### `run.py` — Wrapper Windows

Inicia duas threads daemon — uma para o servidor HTTP Waitress e outra para o ícone pystray. O caminho do ícone está fixo em `C:\Projeto Etiqueta Ag Transfusional\static\icone_etiquetaAT.jpg`; atualize se o caminho de instalação mudar.

### Templates

- `templates/index.html` — Formulário de login (Jinja2, envia para `/`)
- `templates/prontuario.html` — Formulário de entrada do número do prontuário (envia para `/prontuario`)
- `templates/etiqueta.html` — Etiqueta imprimível renderizada a partir do dict `info`; o `@media print` oculta os botões e remove borda/sombra

### Sistema Alvo

O scraper aponta para um endereço de rede interna. A URL pública (`https://sistemasnti.isgh.org.br/pacientehrn/login.jsf`) está comentada em `app.py:31`. Para trocar de ambiente, basta alternar esse comentário.

## Restrições Importantes

- O driver Selenium usa **seletores XPath posicionais** (`tr[1]/td[7]/a[2]/img`) vinculados à estrutura da página JSF do hospital — se o hospital atualizar o sistema, esses seletores irão quebrar.
- O caminho do ícone na bandeja em `run.py:17` está **hardcoded** para o caminho antigo de instalação `C:\Projeto Etiqueta Ag Transfusional\...` — deve ser atualizado se o projeto for movido.
- A `app.secret_key` em `app.py:7` é uma string estática em texto simples; as credenciais do usuário ficam armazenadas na sessão Flask.
