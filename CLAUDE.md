# CLAUDE.md

Este arquivo fornece orientações ao Claude Code (claude.ai/code) ao trabalhar com o código deste repositório.

## O Que Este Projeto Faz

**Etiqueta AT** (Agência Transfusional) é um aplicativo desktop para Windows que gera etiquetas de pacientes do banco de sangue para os hospitais ISGH/HRN. Ele automatiza o login e a raspagem de dados do sistema interno do hospital (endereço configurado via `HOSPITAL_BASE_URL`, ex.: `http://<host>:<porta>/pacientehrn`) reproduzindo as requisições HTTP/AJAX do sistema JSF, e renderiza uma etiqueta imprimível de 47×30mm.

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

O resultado vai para `dist/run.exe`. Não há instalador nem registro como serviço Windows — o `.exe` é executado diretamente (com um `.env` na mesma pasta), do mesmo jeito que o projeto irmão Mapa CCG.

## Instalando Dependências

```bash
pip install -r text/requirements.txt
```

Pacotes principais: `flask`, `requests`, `beautifulsoup4`, `python-dotenv`, `waitress`, `pystray`, `Pillow`.

## Arquitetura

### Fluxo

```
run.py  →  pystray (ícone na bandeja, thread daemon)
        →  waitress.serve(app)  →  app.py (rotas Flask)
                                       │
                                       ▼
                         requests + BeautifulSoup → sistema JSF do hospital
```

### `app.py` — Lógica Principal

- **`http_session` global**: uma única `requests.Session` reutilizada em todas as requisições, reproduzindo as chamadas HTTP/AJAX que o navegador faria contra o RichFaces/JSF do hospital. Criada na primeira chamada e fechada apenas no logout.
- **`login_if_needed()`**: faz `POST` no `login.jsf` do hospital com as credenciais e verifica o redirecionamento para `paginaPrincipal.jsf`.
- **`get_patient_info()` / `_navegar_e_buscar()`**: reproduz a navegação AJAX até a busca por prontuário, trata o caso de vínculo com prontuário de mãe (obstetrícia) e delega a `_parse_patient_data()` a extração de nome, setor, data de nascimento e sexo do bloco `viewBloco` (via BeautifulSoup).
- **Rotas**: `GET/POST /` (login), `GET/POST /prontuario` (busca de paciente), `GET /logout` (encerra a sessão HTTP, limpa a sessão Flask).
- `.env` é carregado no início do módulo (via `python-dotenv`) a partir da pasta do `.exe` (build) ou do `app.py` (dev) — ver `.env.example`.

### `run.py` — Wrapper Windows

Inicia duas threads daemon — uma para o servidor HTTP Waitress e outra para o ícone pystray. `HOST`, `PORT`, `THREADS` e `ICON_PATH` vêm do `.env` (ver `.env.example`); o ícone padrão é resolvido em `static/icone_etiquetaAT.jpg` relativo à pasta do `.exe`/script, não mais um caminho fixo.

### Templates

- `templates/index.html` — Formulário de login (Jinja2, envia para `/`)
- `templates/prontuario.html` — Formulário de entrada do número do prontuário (envia para `/prontuario`)
- `templates/etiqueta.html` — Etiqueta imprimível renderizada a partir do dict `info`; o `@media print` oculta os botões e remove borda/sombra

### Sistema Alvo

O endereço do sistema hospitalar vem da variável de ambiente `HOSPITAL_BASE_URL` (obrigatória — o app falha na inicialização se não estiver definida). Veja `.env.example` na raiz do projeto.

## Restrições Importantes

- A extração usa **regex e parsing posicional** (ex.: IDs `formMedicos:oTableNovo:0:...`, estrutura de `<div>`s dentro de `viewBloco`) vinculados à estrutura da página JSF do hospital — se o hospital atualizar o sistema, essa extração irá quebrar.
- A `app.secret_key` vem de `FLASK_SECRET_KEY` (com um valor padrão embutido como fallback se a variável não estiver definida); as credenciais do usuário ficam armazenadas na sessão Flask.
