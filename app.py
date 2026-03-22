from flask import Flask, render_template, request, redirect, url_for, session
import logging
from seleniumbase import Driver
from selenium.webdriver.common.by import By

app = Flask(__name__)
app.secret_key = "chave_secreta_para_sessao"


# Configuração básica de logging para salvar logs em arquivo 'app.log'
logging.basicConfig(
    filename='Logs do Sistema.log',  # Nome do arquivo onde os logs serão salvos
    level=logging.DEBUG,  # Nível de detalhe do log (INFO, DEBUG, ERROR etc.)
    format='%(asctime)s - %(levelname)s - %(message)s'  # Formato do log
)


driver = None

def get_driver():
    global driver
    if driver is None:
        driver = Driver(browser="chrome", headless=True)
    return driver

# Função para login e navegação até a página de prontuário
def login_if_needed(username, password):
    driver = get_driver()
    try:
        #driver.open("https://sistemasnti.isgh.org.br/pacientehrn/login.jsf")
        driver.open("http://10.2.2.8:8080/pacientehrn/login.jsf")
        driver.type("#login", username)
        driver.type("#xyb-ac", password)
        login_button = driver.find_element(By.ID, "formulario:botaoLogin")
        driver.execute_script("arguments[0].click();", login_button)
        # Confirma se a URL contém o trecho desejado
        if "paginaPrincipal.jsf" in driver.get_current_url():
            logging.info("Login bem-sucedido.")
            return True
        else:
            raise Exception("Redirecionamento de URL falhou")
    except Exception as e:
        logging.error(f"Erro no login: {str(e)}")
        return False

# Função para buscar informações do paciente
def get_patient_info(prontuario, username, password):
    driver = get_driver()
    try:
        # Verifica se estamos na página principal e faz login se necessário
        if "paginaPrincipal.jsf" not in driver.get_current_url():
            if not login_if_needed(username, password):
                return None

        try:
            driver.wait_for_element('//*[@id="formModalNotificacao:btnFechar"]', timeout=1)
            driver.click('//*[@id="formModalNotificacao:btnFechar"]')  # Clica no botão se estiver presente
            logging.info("Fechou")
        except Exception as e:
            logging.info("Não Fechou")
            
        # Navega para a página do prontuário e realiza a busca
        driver.click("//a[@class='img' and text()='Assistência']")
        driver.click("/html/body/div[2]/form/div[3]/div/ul/li[3]/ul/li[9]/a")
        driver.type("/html/body/div[4]/div/form/div/div[2]/div[3]/input", prontuario)
        driver.click("/html/body/div[4]/div/form/div/div[2]/div[4]/input")
        driver.click("/html/body/div[4]/div/form/div/div[4]/table/tbody/tr[1]/td[7]/a[2]/img")

        # Tenta clicar no botão de obstetrícia com um tempo máximo de espera
        try:
            driver.wait_for_element('//*[@id="formObstetricia:btnProntMae"]', timeout=1)
            driver.click('//*[@id="formObstetricia:btnProntMae"]')  # Clica no botão se estiver presente
            logging.info("Paciente Mãe Encontrado")
        except Exception as e:
            logging.info("Paciente Comum")

        # Extrai informações do paciente
        patient_info = {
            'prontuario': driver.get_text("//*[@id='viewBloco']/div/table/tbody/tr[1]/td[2]/div/div[1]/strong/span"),
            'setor': driver.get_text("//*[@id='viewBloco']/div/table/tbody/tr[1]/td[2]/div/div[3]/strong[1]/span"),
            'data_nascimento': driver.get_text("//*[@id='viewBloco']/div/table/tbody/tr[1]/td[2]/div/div[2]/strong[1]/span"),
            'sexo': driver.get_text("//*[@id='viewBloco']/div/table/tbody/tr[1]/td[2]/div/div[2]/strong[3]/span")
        }
        driver.back()  # Volta para a página anterior
        return patient_info

    except Exception as e:
        logging.error(f"Erro ao buscar informações: {str(e)}")
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
                logging.info("Usuário ou senha incorretos.")
                return render_template("index.html", error="Usuário ou senha incorretos.")
        else:
            logging.info("Usuário e senha são obrigatórios.")
            return render_template("index.html", error="Usuário e senha são obrigatórios.")
    return render_template("index.html")

@app.route("/prontuario", methods=["GET", "POST"])
def prontuario():
    if "username" not in session or "password" not in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        prontuario = request.form.get("prontuario").strip()
        username = session["username"]
        password = session["password"]

        if prontuario:
            info = get_patient_info(prontuario, username, password)
            if info:
                logging.info("Etiqueta Gerada")
                return render_template("etiqueta.html", info=info)
                
            else:
                logging.info("Paciente não encontrado.")
                return render_template("prontuario.html", error="Paciente não encontrado.")

    return render_template("prontuario.html")

@app.route("/logout")
def logout():
    global driver
    session.clear()
    if driver:
        driver.quit()
        driver = None
    logging.info("Logout Realizado pelo Usuario")
    return redirect(url_for("index"))

#if __name__ == "__main__":
    #app.run(debug=True)
