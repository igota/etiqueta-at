# Etiqueta AT

Aplicativo desktop para Windows que gera etiquetas de pacientes do banco de sangue (Agência Transfusional) para os hospitais **ISGH/HRN**. Ele automatiza o login e a busca de dados no sistema interno do hospital e renderiza uma etiqueta imprimível de 47×30mm com nome, prontuário, data de nascimento, sexo e setor do paciente.

## Como funciona

O app se autentica no sistema hospitalar (ARS VITAE, baseado em JSF/RichFaces) reproduzindo as mesmas requisições HTTP/AJAX que o navegador faria — sem precisar abrir um navegador de verdade. A partir do número do prontuário informado, ele navega pelo fluxo de busca de pacientes, trata o caso de vínculo com prontuário de mãe (obstetrícia) e extrai os dados para montar a etiqueta.

Fluxo resumido:

```
run.py  →  pystray (ícone na bandeja)  +  waitress.serve(app)
                                              │
                                              ▼
                                        app.py (rotas Flask)
                                              │
                                              ▼
                              requests + BeautifulSoup → sistema JSF do hospital
```

## Executando em modo desenvolvimento

```bash
pip install -r text/requirements.txt
python app.py
```

O app sobe em `http://localhost:5000`.

## Executando em modo produção

```bash
python run.py
```

Sobe o servidor com Waitress e um ícone na bandeja do sistema.

## Gerando o executável

```bash
pyinstaller run.spec
```

O executável vai para `dist/run.exe`. Não há instalador nem registro como serviço Windows — basta copiar `run.exe` (junto com o `.env`, veja abaixo) para onde for rodar e executá-lo diretamente. Para iniciar junto com o Windows, crie um atalho na pasta Inicializar (`shell:startup`).

## Estrutura

- **`app.py`** — lógica principal: autenticação, navegação e extração de dados do sistema hospitalar, e as rotas Flask (`/`, `/prontuario`, `/logout`).
- **`run.py`** — wrapper para Windows: inicia o servidor Waitress e o ícone da bandeja em threads separadas.
- **`templates/`** — telas de login, busca de prontuário e a etiqueta imprimível.
- **`static/`** — logos e ícones usados na interface e no executável.
- **`text/`** — dependências (`requirements.txt`).

## Configuração

O app é configurado por variáveis de ambiente, carregadas de um arquivo `.env` colocado na mesma pasta do `run.exe` (build) ou do `app.py` (desenvolvimento). Copie `.env.example` para `.env` e preencha com os valores reais do seu ambiente — o `.env` já está no `.gitignore` e nunca deve ser commitado.

- `HOSPITAL_BASE_URL` (**obrigatória**): URL base do sistema do hospital (ex.: `http://10.2.2.8:8080/pacientehrn`). O app não sobe sem ela — falha logo na inicialização com um erro claro.
- `FLASK_SECRET_KEY` (opcional): chave de sessão do Flask. Se não definida, usa um valor padrão embutido no código — recomendado configurar em produção.

## Avisos importantes

- Este projeto depende de **seletores e estrutura de página específicos** do sistema JSF do hospital — qualquer atualização desse sistema pode quebrar a extração de dados.
- O caminho do ícone na bandeja em `run.py` está fixo para `C:\Projeto Etiqueta Ag Transfusional\...`; ajuste se o local de instalação mudar.
- As credenciais informadas no login ficam guardadas na sessão Flask durante o uso do app — não são persistidas em disco.
- Repositório privado: lida com dados de pacientes e credenciais de acesso a um sistema hospitalar interno. Não versione arquivos de log, capturas de tráfego (`trafego_capturado.json`) ou páginas HTML de depuração — já cobertos pelo `.gitignore`.
