from flask import Flask, render_template, request, redirect, url_for, session
import logging
import os
import re
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "chave_secreta_para_sessao")

logging.basicConfig(
    filename='Logs do Sistema.log',
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

log = logging.getLogger("etiquetaAT")
log.setLevel(logging.DEBUG)

BASE_URL = os.environ.get("HOSPITAL_BASE_URL")
if not BASE_URL:
    raise RuntimeError(
        "Variável de ambiente HOSPITAL_BASE_URL não definida. "
        "Configure-a com a URL base do sistema do hospital "
        "(ex.: http://10.2.2.8:8080/pacientehrn)."
    )
_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"

http_session = None


def _get_http_session():
    global http_session
    if http_session is None:
        http_session = requests.Session()
        http_session.headers["User-Agent"] = _UA
    return http_session


def _ajax_post(path, data):
    sess = _get_http_session()
    return sess.post(
        f"{BASE_URL}/{path}",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
    )


def _extract_ajax_html(response_text):
    """Extrai o HTML dos blocos CDATA da resposta AJAX do RichFaces."""
    parts = re.findall(r'<!\[CDATA\[(.*?)\]\]>', response_text, re.DOTALL)
    return "\n".join(parts) if parts else response_text


def login_if_needed(username, password):
    sess = _get_http_session()
    try:
        sess.get(f"{BASE_URL}/login.jsf")
        resp = sess.post(
            f"{BASE_URL}/login.jsf",
            data={
                "formulario": "formulario",
                "login": username,
                "xyb-ac": password,
                "formulario:botaoLogin": "confirmar",
                "formulario:host": "10.2.2.8:8080",
                "javax.faces.ViewState": "j_id1",
            },
            allow_redirects=True,
        )
        if "paginaPrincipal.jsf" in resp.url:
            log.info("Login bem-sucedido.")
            return True
        raise Exception("Redirecionamento de URL falhou")
    except Exception as e:
        log.error(f"Erro no login: {str(e)}")
        return False


def _find_select_button(ajax_text):
    """Encontra o ID do botão de seleção na primeira linha dos resultados."""
    # Extrai todos os IDs com padrão formMedicos:oTableNovo:0:<id>
    matches = re.findall(r'"(formMedicos:oTableNovo:0:[^"]+)"', ajax_text)
    if matches:
        seen, unique = set(), []
        for m in matches:
            if m not in seen:
                seen.add(m)
                unique.append(m)
        # O botão de seleção é o último (equivale ao a[2] do XPath original)
        return unique[-1]
    return None


def _parse_patient_data(ajax_text):
    """Extrai os dados do paciente do bloco viewBloco na resposta AJAX."""
    html = _extract_ajax_html(ajax_text)
    soup = BeautifulSoup(html, "html.parser")

    view_bloco = soup.find(id="viewBloco")
    if not view_bloco:
        log.error("viewBloco não encontrado na resposta AJAX")
        log.debug(f"Resposta recebida: {ajax_text[:500]}")
        return None

    try:
        # html.parser não insere <tbody> implícito — buscar <tr> diretamente
        td = view_bloco.find("table").find("tr").find_all("td")[1]
        divs = td.find("div").find_all("div", recursive=False)

        return {
            "prontuario":      divs[0].find("strong").find("span").get_text(strip=True),
            "data_nascimento": divs[1].find_all("strong")[0].find("span").get_text(strip=True),
            "sexo":            divs[1].find_all("strong")[2].find("span").get_text(strip=True),
            "setor":           divs[2].find("strong").find("span").get_text(strip=True),
        }
    except Exception as e:
        log.error(f"Erro ao parsear viewBloco: {e}")
        log.debug(f"HTML do viewBloco: {str(view_bloco)[:500]}")
        return None


def _navegar_e_buscar(sess, prontuario):
    """Navega ao menu, carrega a busca e retorna a resposta AJAX da pesquisa."""
    _ajax_post("paginaPrincipal.jsf", {
        "AJAXREQUEST": "_viewRoot",
        "formCabecalho": "formCabecalho",
        "javax.faces.ViewState": "j_id5",
        "formCabecalho:j_id54": "formCabecalho:j_id54",
    })
    sess.get(f"{BASE_URL}/cs_pep_sem_status.jsf")
    return _ajax_post("cs_pep_sem_status.jsf", {
        "AJAXREQUEST": "_viewRoot",
        "formMedicos": "formMedicos",
        "formMedicos:selClinica": "0",
        "formMedicos:selEnfermaria": "0",
        "formMedicos:iptProntuario": prontuario,
        "javax.faces.ViewState": "j_id6",
        "formMedicos:btnPesquisa": "formMedicos:btnPesquisa",
    })


def get_patient_info(prontuario, username, password):
    sess = _get_http_session()

    for tentativa in range(2):
        try:
            # Verifica se a sessão ainda é válida
            check = sess.get(f"{BASE_URL}/paginaPrincipal.jsf", allow_redirects=True)
            if "login.jsf" in check.url:
                if not login_if_needed(username, password):
                    return None

            resp = _navegar_e_buscar(sess, prontuario)

            btn_id = _find_select_button(resp.text)
            if not btn_id:
                if tentativa == 0:
                    log.info("Sem resultado na 1ª tentativa — renavegando.")
                    continue
                log.info("Paciente não encontrado nos resultados.")
                return None

            # Seleciona o primeiro resultado
            resp = _ajax_post("cs_pep_sem_status.jsf", {
                "AJAXREQUEST": "_viewRoot",
                "formMedicos": "formMedicos",
                "formMedicos:selClinica": "0",
                "formMedicos:selEnfermaria": "0",
                "formMedicos:iptProntuario": prontuario,
                "javax.faces.ViewState": "j_id6",
                btn_id: btn_id,
                "ajaxSingle": btn_id,
            })

            # Trata modal de obstetrícia, se presente
            if "formObstetricia:btnProntMae" in resp.text:
                log.info("Paciente Mãe Encontrado")
                resp = _ajax_post("cs_pep_sem_status.jsf", {
                    "AJAXREQUEST": "_viewRoot",
                    "formObstetricia": "formObstetricia",
                    "javax.faces.ViewState": "j_id6",
                    "formObstetricia:btnProntMae": "formObstetricia:btnProntMae",
                })
            else:
                log.info("Paciente Comum")

            return _parse_patient_data(resp.text)

        except Exception as e:
            log.error(f"Erro ao buscar informações: {str(e)}")
            return None

    return None


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()

        if username and password:
            if login_if_needed(username, password):
                session["username"] = username
                session["password"] = password
                return redirect(url_for("prontuario"))
            else:
                log.info("Usuário ou senha incorretos.")
                return render_template("index.html", error="Usuário ou senha incorretos.")
        else:
            log.info("Usuário e senha são obrigatórios.")
            return render_template("index.html", error="Usuário e senha são obrigatórios.")
    return render_template("index.html")


@app.route("/prontuario", methods=["GET", "POST"])
def prontuario():
    if "username" not in session or "password" not in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        pront = request.form.get("prontuario").strip()
        username = session["username"]
        password = session["password"]

        if pront:
            info = get_patient_info(pront, username, password)
            if info:
                log.info("Etiqueta Gerada")
                return render_template("etiqueta.html", info=info)
            else:
                log.info("Paciente não encontrado.")
                return render_template("prontuario.html", error="Paciente não encontrado.")

    return render_template("prontuario.html")


@app.route("/logout")
def logout():
    global http_session
    session.clear()
    if http_session:
        http_session.close()
        http_session = None
    log.info("Logout Realizado pelo Usuario")
    return redirect(url_for("index"))
