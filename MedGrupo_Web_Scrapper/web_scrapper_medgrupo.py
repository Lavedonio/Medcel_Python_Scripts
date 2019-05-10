import os
import sys
import platform
import time
import logging
import logging.config
from os.path import isfile as file_exists
from os.path import isdir as dir_exists
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException

logging.basicConfig(filename='web_scrapper.log', level=logging.DEBUG,
    format='%(asctime)s:%(levelname)s:%(funcName)s:%(message)s')

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
})


def notify(title, text):
    if platform.system() == "Darwin":
        os.system("""
                  osascript -e 'display notification "{}" with title "{}"'
                  """.format(text, title))


# <------------------- File Handler ------------------>
def csv_Handler():
    test = False

    if file_exists('./aprovados_medgrupo.csv'):
        if len(sys.argv) > 1:
            opcao = str(sys.argv[1])
        else:
            print("Já existe CSV criado. Deseja sobrescrever ou criar um novo arquivo?\n")
            print("1. Sobrescrever")
            print("2. Criar novo arquivo")
            print("3. Realizar teste")
            print("x. Abortar\n")
            opcao = input("Digite opção: ")

        if opcao == "1":
            print("Sobrescrevendo...")
            file = open("aprovados_medgrupo.csv", "w")
        elif opcao == "2":
            i = 1
            while file_exists('./aprovados_medgrupo_(%s).csv' % (i)):
                i += 1
            print("Criando novo arquivo aprovados_medgrupo_(%s).csv..." % (i))
            file = open("aprovados_medgrupo_(%s).csv" % (i), "w+")
        elif opcao == "3":
            print("Opção de teste selecionada; nenhum arquivo criado.")
            test = True
        else:
            print("Execução abortada")
            sys.exit()
    else:
        file = open("aprovados_medgrupo.csv", "w+")

    if not test:
        file.write("Estado;Instituição;Hospital;Curso;Colocação;Nome_Aprovado\n")

    return file, test

# <------------------ /File Handler ------------------>


# <----------------- Webdriver start ----------------->
def web_scrapper(file, test):
    print("\nIniciando importação...\n")

    error_counter = 0

    my_url = "https://site.medgrupo.com.br/#/aprovacoes"

    # Define window size for certain class selectors appear, thanks to the page's JS
    options = Options()
    # options.add_argument("window-size=800,700")

    driver = webdriver.Chrome(options=options, executable_path=r'/Library/FilesToPath/chromedriver')
    driver.get(my_url)

    driver.set_window_size(800, 800)

    all_estados_text = []
    all_estados = driver.find_elements_by_xpath("//select[@class='estado-instituicao-mobile__estado tagmanager-select']/option")
    for estado in all_estados:
        all_estados_text.append(estado.get_attribute("value"))

    for estado_text in all_estados_text:
        notify("Aviso do Web Scrapper!", "Estado concluído! Abra o terminal para continuar.")
        input("\nPróximo estado é %s. Selecione o estado indicado no browser e digite enter para continuar..." % (estado_text))
        print(".")
        print("|---Estado: %s" % (estado_text))
        driver.set_window_size(800, 800)

        # Pega todos os nomes das instituições de determinado estado
        all_instituicoes_text = []
        all_instituicoes = driver.find_elements_by_xpath("//select[@class='estado-instituicao-mobile__instituicao tagmanager-select']/option")
        for instituicao in all_instituicoes:
            all_instituicoes_text.append(instituicao.get_attribute("value"))

        driver.set_window_size(1200, 800)

        all_instituicoes = driver.find_elements_by_xpath("//ul[@class='estado-instituicao__lista disable-select']/li")

        num_instituicao = 0
        for instituicao in all_instituicoes:
            instituicao_text = all_instituicoes_text[num_instituicao]

            print("| |---Instituição: %s" % (instituicao_text))

            instituicao.click()

            infos_por_instituicao = driver.find_elements_by_xpath("//div[@class='content-lista-aprovados__container']")

            try:
                for infos_por_hospital in infos_por_instituicao:
                    # print(len(infos_por_instituicao))
                    hospital = infos_por_hospital.find_element_by_xpath(".//div[@class='content-lista-aprovados__hospital']")
                    all_cursos = infos_por_hospital.find_elements_by_xpath(".//h4[@class='content-lista-aprovados__titulo']")
                    all_aprovados = infos_por_hospital.find_elements_by_xpath(".//ul[@class='content-lista-aprovados__nomes' or @class='content-lista-aprovados__nomes stamp']")

                    i = 0
                    print("| | |---Hospital: %s" % (hospital.text))

                    for curso in all_cursos:
                        if i < len(all_aprovados):
                            aprovados_curso = all_aprovados[i].find_elements_by_xpath(".//span[@class='destaque']")
                            i += 1
                            suplentes = False
                            for aprovado in aprovados_curso:
                                if not suplentes:
                                    if "suplente" in aprovado.text.lower():
                                        suplentes = True
                                    elif len(aprovado.text) == 0:
                                        pass
                                    else:
                                        if aprovado.text[0] == ".":
                                            file.write("%s;%s;%s;%s;%s\n" % (estado_text, instituicao_text, hospital.text, curso.text, aprovado.text.replace(".", ";", 1)))
                                        elif aprovado.text[0].isdigit():
                                            file.write("%s;%s;%s;%s;%s\n" % (estado_text, instituicao_text, hospital.text, curso.text, aprovado.text.replace(". ", ";", 1)))
                                        else:
                                            file.write("%s;%s;%s;%s;;%s\n" % (estado_text, instituicao_text, hospital.text, curso.text, aprovado.text))
            except StaleElementReferenceException:
                print("\nStaleElementReferenceException occured; line not written on file. Continuing...\n")
                error_counter += 1
                file.write(" ")

            num_instituicao += 1
        driver.refresh()

    print("\nHouveram um total de %d erros na execução do programa. Verifique se os dados retirados do site conferem com o CSV." % (error_counter))
    return driver
# <---------------- /Webdriver start ----------------->


def closing(driver, file, test):
    if not test:
        file.close()
    driver.quit()


def main_DEPRICATED():
    file, test = csv_Handler()
    driver = web_scrapper(file, test)
    closing(driver, file, test)


def test_function():
    '''
    ' Função criada para testar funcionalidades do código sem atrapalhar o fluxo principal
    '
    '''
    file, test = csv_Handler()
    if test:
        raise ValueError

    error_counter = 0
    estado_error_counter = 0
    erros_por_estado_dict = {}

    my_url = "https://site.medgrupo.com.br/#/aprovacoes"

    # Define window size for certain class selectors appear, thanks to the page's JS
    options = Options()
    # options.add_argument("window-size=800,700")

    driver = webdriver.Chrome(options=options, executable_path=r'/Library/FilesToPath/chromedriver')
    driver.get(my_url)

    driver.set_window_size(800, 800)

    all_estados_text = []
    all_estados = driver.find_elements_by_xpath("//select[@class='estado-instituicao-mobile__estado tagmanager-select']/option")
    for estado in all_estados:
        all_estados_text.append(estado.get_attribute("value"))

    for estado_text in all_estados_text:
        notify("Aviso do Web Scrapper!", "Estado concluído! Abra o terminal para continuar.")
        input("\nPróximo estado é %s. Selecione o estado indicado no browser e digite enter para continuar..." % (estado_text))
        print(".")
        print("|---Estado: %s" % (estado_text))

        driver.set_window_size(800, 800)

        # Pega todos os nomes das instituições de determinado estado
        all_instituicoes_text = []
        all_instituicoes = driver.find_elements_by_xpath("//select[@class='estado-instituicao-mobile__instituicao tagmanager-select']/option")
        for instituicao in all_instituicoes:
            all_instituicoes_text.append(instituicao.get_attribute("value"))

        driver.set_window_size(1200, 800)

        all_instituicoes = driver.find_elements_by_xpath("//ul[@class='estado-instituicao__lista disable-select']/li")

        num_instituicao = 0
        for instituicao in all_instituicoes:
            instituicao_text = all_instituicoes_text[num_instituicao]

            print("| |---Instituição: %s" % (instituicao_text))

            instituicao.click()

            infos_por_instituicao = driver.find_elements_by_xpath("//div[@class='content-lista-aprovados__container']")

            try:
                for infos_por_hospital in infos_por_instituicao:
                    # print(len(infos_por_instituicao))
                    hospital = infos_por_hospital.find_element_by_xpath(".//div[@class='content-lista-aprovados__hospital']")
                    all_cursos_aprovados = infos_por_hospital.find_elements_by_xpath(".//div[not(contains(@class, 'content-lista-aprovados__info'))]")
                    # all_cursos_aprovados = infos_por_hospital.find_elements_by_xpath(".//div")

                    print("| | |---Hospital: %s" % (hospital.text))

                    for cursos_aprovados in all_cursos_aprovados[1:]:
                        # print("index =", index)
                        # print(cursos_aprovados.text)
                        # if index == 2:
                        #     driver.quit()
                        #     raise ValueError
                        curso = cursos_aprovados.find_element_by_xpath(".//h4[@class='content-lista-aprovados__titulo']")
                        all_aprovados_curso = cursos_aprovados.find_elements_by_xpath(".//li/span[@class='destaque']")
                        suplentes = False
                        for aprovado in all_aprovados_curso:
                            if not suplentes:
                                if "suplente" in aprovado.text.lower():
                                    suplentes = True
                                elif len(aprovado.text) == 0:
                                    pass
                                else:
                                    if aprovado.text[0] == ".":
                                        file.write("%s;%s;%s;%s;%s\n" % (estado_text, instituicao_text, hospital.text, curso.text, aprovado.text.replace(".", ";", 1)))
                                    elif aprovado.text[0].isdigit():
                                        file.write("%s;%s;%s;%s;%s\n" % (estado_text, instituicao_text, hospital.text, curso.text, aprovado.text.replace(". ", ";", 1)))
                                    else:
                                        file.write("%s;%s;%s;%s;;%s\n" % (estado_text, instituicao_text, hospital.text, curso.text, aprovado.text))
            except StaleElementReferenceException:
                print("\nStaleElementReferenceException occured; line not written on file. Continuing...\n")
                estado_error_counter += 1
                error_counter += 1

            num_instituicao += 1
        driver.refresh()

        erros_por_estado_dict[estado_text] = estado_error_counter
        print("\nNa apuração do estado de %s houveram %d erros de execução.\n" % (estado_text, estado_error_counter))
        estado_error_counter = 0

    print("\nHouveram um total de %d erros na execução do programa. Verifique se os dados retirados do site conferem com o CSV." % (error_counter))
    print("\nErros por estado:")
    for key, value in erros_por_estado_dict.items():
        print("  %s: %d" % (key, value))

    file.close()
    driver.quit()


def coletar_aprovados_instituicao_DEPRICATED():
    my_url = "https://site.medgrupo.com.br/#/aprovacoes"

    # Define window size for certain class selectors appear, thanks to the page's JS
    options = Options()
    # options.add_argument("window-size=800,700")

    driver = webdriver.Chrome(options=options, executable_path=r'/Library/FilesToPath/chromedriver')
    driver.get(my_url)

    estado_text = input("Digite nome do estado: ")
    instituicao_text = input("Digite o nome da instituição: ")

    print("")

    if file_exists('./aprovados_medgrupo_%s_%s.csv' % (estado_text, instituicao_text)):
        i = 1
        while file_exists('./aprovados_medgrupo_%s_%s_(%s).csv' % (estado_text, instituicao_text, i)):
            i += 1
        print("Criando novo arquivo aprovados_medgrupo_%s_%s_(%s).csv...\n" % (estado_text, instituicao_text, i))
        file = open("aprovados_medgrupo_%s_%s_(%s).csv" % (estado_text, instituicao_text, i), "w+")
    else:
        print("Criando novo arquivo aprovados_medgrupo_%s_%s.csv...\n" % (estado_text, instituicao_text))
        file = open("aprovados_medgrupo_%s_%s.csv" % (estado_text, instituicao_text), "w+")

    file.write("Estado;Instituição;Hospital;Curso;Colocação;Nome_Aprovado\n")

    infos_por_instituicao = driver.find_elements_by_xpath("//div[@class='content-lista-aprovados__container']")

    try:
        for infos_por_hospital in infos_por_instituicao:
            # print(len(infos_por_instituicao))
            hospital = infos_por_hospital.find_element_by_xpath(".//div[@class='content-lista-aprovados__hospital']")
            all_cursos_aprovados = infos_por_hospital.find_elements_by_xpath(".//div[not(contains(@class, 'content-lista-aprovados__info'))]")
            # all_cursos_aprovados = infos_por_hospital.find_elements_by_xpath(".//div")

            print("---Hospital: %s" % (hospital.text))

            for cursos_aprovados in all_cursos_aprovados[1:]:
                # print("index =", index)
                # print(cursos_aprovados.text)
                # if index == 2:
                #     driver.quit()
                #     raise ValueError
                curso = cursos_aprovados.find_element_by_xpath(".//h4[@class='content-lista-aprovados__titulo']")
                all_aprovados_curso = cursos_aprovados.find_elements_by_xpath(".//li/span[@class='destaque']")
                suplentes = False
                for aprovado in all_aprovados_curso:
                    if not suplentes:
                        if "suplente" in aprovado.text.lower():
                            suplentes = True
                        elif len(aprovado.text) == 0:
                            pass
                        else:
                            if aprovado.text[0] == ".":
                                file.write("%s;%s;%s;%s;%s\n" % (estado_text, instituicao_text, hospital.text, curso.text, aprovado.text.replace(".", ";", 1)))
                            elif aprovado.text[0].isdigit():
                                file.write("%s;%s;%s;%s;%s\n" % (estado_text, instituicao_text, hospital.text, curso.text, aprovado.text.replace(". ", ";", 1)))
                            else:
                                file.write("%s;%s;%s;%s;;%s\n" % (estado_text, instituicao_text, hospital.text, curso.text, aprovado.text))
    except StaleElementReferenceException:
        print("\nStaleElementReferenceException occured; line not written on file. Aborting...\n")

    file.close()
    driver.quit()


def coletar_aprovados_instituicao(confirmar_dados=True, notificar=False, abrir_driver=True, driver=None, coletar_todos_aprovados=False):
    logging.debug("abrir_driver = {}".format(abrir_driver))
    if abrir_driver:
        logging.info("Inicializando driver.")
        my_url = "https://site.medgrupo.com.br/#/aprovacoes"

        # Define window size for certain class selectors appear, thanks to the page's JS
        options = Options()
        # options.add_argument("window-size=800,700")
        driver_path = os.path.join(os.getcwd(), 'chromedriver')

        driver = webdriver.Chrome(options=options, executable_path=driver_path)
        driver.get(my_url)

        logging.info("Navegador aberto e site carregado.")

        logging.info("Aguardando seleção do ano, estado e instituição.")
        input("Selecione no navegador o ano, o estado e instituição desejados. Pressione enter para continuar...")
        logging.info("Ano, estado e instituição selecionados.")

    ano_text = driver.find_element_by_xpath("//ul[@class='aprovacoes__selecao-ano']/li[@class='pointer active']").text
    estado_text = driver.find_element_by_xpath("//h2[@class='estado-instituicao__titulo disable-select']").text
    instituicao_text = driver.find_element_by_xpath("//h2[@class='lista-aprovados__titulo']").text
    instituicao_text_sigla, *_ = instituicao_text.split(" - ")
    instituicao_text_nome = instituicao_text.split("\n")[1]
    instituicao_text = instituicao_text_sigla + " - " + instituicao_text_nome

    logging.info("ano_text = %s" % (ano_text))
    logging.info("estado_text = %s" % (estado_text))
    logging.info("instituicao_text = %s" % (instituicao_text))
    logging.debug("instituicao_text_sigla = %s" % (instituicao_text_sigla))

    logging.debug("confirmar_dados = {}".format(confirmar_dados))
    if confirmar_dados:
        logging.info("Confirmando dados.")

        print("\nEstes dados estão corretos?")
        print("Ano: %s" % (ano_text))
        print("Estado: %s" % (estado_text))
        print("Instituição: %s" % (instituicao_text))
        print("S/N? ", end="")
        modificar = input("")

        if modificar.lower() == "n":
            logging.info("Usuário pede para modificar ano e/ou estado.")

            print("")
            ano_text = input("Digite o ano: ")
            estado_text = input("Digite nome do estado: ")
            instituicao_text = input("Digite o nome da instituição: ")
            instituicao_text_sigla, *_ = instituicao_text.split(" - ")

            logging.info("Novo ano_text = %s" % (ano_text))
            logging.info("Novo estado_text = %s" % (estado_text))
            logging.info("Novo instituicao_text = %s" % (instituicao_text))
            logging.debug("Novo instituicao_text_sigla = %s" % (instituicao_text_sigla))

        print("")

    file_fullname = file_handling(ano_text, estado_text, instituicao_text_sigla)

    logging.info("file_fullname = {}".format(file_fullname))

    with open(file_fullname, "w+") as file:
        logging.debug("Arquivo aberto.")

        file.write("Estado;Instituição;Hospital;Curso;Colocação;Nome_Aprovado\n")

        infos_por_instituicao = driver.find_elements_by_xpath("//div[@class='content-lista-aprovados__container']")
        logging.debug("len(infos_por_instituicao) = {}".format(len(infos_por_instituicao)))

        erro_referencia = False
        for infos_por_hospital in infos_por_instituicao:
            try:
                hospital = infos_por_hospital.find_element_by_xpath(".//div[@class='content-lista-aprovados__hospital']")
                logging.info("---Hospital: {}".format(hospital.text))

                all_cursos_aprovados = infos_por_hospital.find_elements_by_xpath(".//div[not(contains(@class, 'content-lista-aprovados__info'))]")
                logging.info("Cursos encontrados.")
                logging.debug("len(infos_por_instituicao) = {}".format(len(infos_por_instituicao)))

                print("| |---Hospital: %s" % (hospital.text))

                num_cursos = 0
                for cursos_aprovados in all_cursos_aprovados[1:]:
                    curso = cursos_aprovados.find_element_by_xpath(".//h4[@class='content-lista-aprovados__titulo']")
                    logging.debug("curso.text = {}".format(curso.text))

                    if coletar_todos_aprovados:
                        all_aprovados_curso = cursos_aprovados.find_elements_by_xpath(".//li/span")
                        logging.debug("Coletando todos os nomes.")
                    else:
                        all_aprovados_curso = cursos_aprovados.find_elements_by_xpath(".//li/span[@class='destaque']")
                        logging.debug("Coletando apenas os marcados como aprovados")

                    num_cursos += 1

                    suplentes = False
                    num_aprovados = 0
                    for aprovado in all_aprovados_curso:
                        if not suplentes:
                            if "suplente" in aprovado.text.lower() and not coletar_todos_aprovados:
                                suplentes = True
                                logging.debug("Suplente encontrado, pulando restante dos nomes no curso.")
                            elif "medgrupo" in aprovado.text.lower():
                                pass
                            elif len(aprovado.text) == 0:
                                logging.warning("aprovado.text é uma string vazia.")
                            else:
                                # logging.debug("aprovado.text = {}".format(aprovado.text))
                                if aprovado.text[0] == ".":
                                    file.write("%s;%s;%s;%s;%s\n" % (estado_text, instituicao_text, hospital.text, curso.text, aprovado.text.replace(". ", ";", 1)))
                                elif aprovado.text[0].isdigit():
                                    file.write("%s;%s;%s;%s;%s\n" % (estado_text, instituicao_text, hospital.text, curso.text, aprovado.text.replace(". ", ";", 1)))
                                else:
                                    file.write("%s;%s;%s;%s;;%s\n" % (estado_text, instituicao_text, hospital.text, curso.text, aprovado.text))

                                num_aprovados += 1

                    logging.info("-- {} aprovados registrados no curso {}".format(num_aprovados, curso.text))
                logging.info("---- {} cursos registrados no hospital {}".format(num_cursos, hospital.text))

            except StaleElementReferenceException:
                erro_referencia = True
                print("\nStaleElementReferenceException occured; line not written on file. Aborting...\n")
                logging.error("StaleElementReferenceException")
                logging.warning("Pulando restante dos dados da instituição.")

            except NoSuchElementException:
                erro_referencia = True
                print("\nNoSuchElementException; Indo para próximo hospital\n")
                logging.error("NoSuchElementException")
                logging.warning("Pulando restante dos dados do hospital.")

            except Exception as e:
                logging.exception("Erro inesperado ocorrido.")
                driver.quit()
                raise e

    if notificar:
        if erro_referencia:
            notify("Instituição concluída (com erros)", "Retirada de dados da instituição {} concluída com erro de referência. Verifique arquivo gerado.".format(instituicao_text_sigla))
        else:
            notify("Instituição concluída", "Retirada de dados da instituição {} concluída sem erros".format(instituicao_text))
    logging.info("Fim da leitura da instituição.")
    return driver, erro_referencia


def file_handling(ano_text, estado_text, instituicao_text_sigla):
    instituicao_text_sigla = instituicao_text_sigla.replace("/", "-")

    file_path = os.path.join("Arquivos_CSV", estado_text, instituicao_text_sigla)

    logging.debug("file_path = {}".format(file_path))
    os.makedirs(file_path, exist_ok=True)
    logging.info("Path {} criado, se não existia.".format(file_path))

    if file_exists(os.path.join('.', file_path, 'aprovados_medgrupo_%s_%s_%s.csv' % (ano_text, estado_text, instituicao_text_sigla))):
        i = 1
        while file_exists(os.path.join('.', file_path, 'aprovados_medgrupo_%s_%s_%s_(%s).csv' % (ano_text, estado_text, instituicao_text_sigla, i))):
            i += 1
        print("| |-Criando novo arquivo aprovados_medgrupo_%s_%s_%s_(%s).csv..." % (ano_text, estado_text, instituicao_text_sigla, i))
        file_name = "aprovados_medgrupo_%s_%s_%s_(%s).csv" % (ano_text, estado_text, instituicao_text_sigla, i)
    else:
        print("| |-Criando novo arquivo aprovados_medgrupo_%s_%s_%s.csv..." % (ano_text, estado_text, instituicao_text_sigla))
        file_name = "aprovados_medgrupo_%s_%s_%s.csv" % (ano_text, estado_text, instituicao_text_sigla)

    logging.info("file_name = {}".format(file_name))
    logging.debug("return {}".format(os.path.join(os.getcwd(), file_path, file_name)))

    return os.path.join(os.getcwd(), file_path, file_name)


def coletar_aprovados_estado(confirmar_dados=True, notificar=False, abrir_driver=True, enable_skipping=False, driver=None):
    if abrir_driver:
        my_url = "https://site.medgrupo.com.br/#/aprovacoes"

        # Define window size for certain class selectors appear, thanks to the page's JS
        options = Options()
        # options.add_argument("window-size=800,700")
        driver_path = os.path.join(os.getcwd(), 'chromedriver')

        driver = webdriver.Chrome(options=options, executable_path=driver_path)
        driver.get(my_url)
        logging.info("Navegador aberto e site carregado.")

        logging.info("Aguardando seleção do ano e estado.")
        input("Selecione no navegador o ano e o estado desejados. Pressione enter para continuar...")
        logging.info("Ano e estado selecionados.")

    ano_text = driver.find_element_by_xpath("//ul[@class='aprovacoes__selecao-ano']/li[@class='pointer active']").text
    estado_text = driver.find_element_by_xpath("//h2[@class='estado-instituicao__titulo disable-select']").text

    logging.info("ano_text = %s" % (ano_text))
    logging.info("estado_text = %s" % (estado_text))

    logging.debug("confirmar_dados = {}".format(confirmar_dados))
    if confirmar_dados:
        logging.info("Confirmando dados.")

        print("\nEstes dados estão corretos?")
        print("Ano: %s" % (ano_text))
        print("Estado: %s" % (estado_text))
        print("S/N? ", end="")
        modificar = input("")

        if modificar.lower() == "n":
            logging.info("Usuário pede para modificar ano e/ou estado.")

            print("")
            ano_text = input("Digite o ano: ")
            estado_text = input("Digite nome do estado: ")

            logging.info("Novo ano_text = %s" % (ano_text))
            logging.info("Novo estado_text = %s" % (estado_text))

        print("")

    all_instituicoes = driver.find_elements_by_xpath("//ul[@class='estado-instituicao__lista disable-select']/li")
    logging.debug("Lista de instituições adquirida")

    instituicoes_erros_referencia = []

    logging.debug("len(all_instituicoes) = {}".format(len(all_instituicoes)))
    for instituicao in all_instituicoes:
        instituicao.click()

        print("|")
        print("|---Instituição: %s" % (instituicao.text.replace("\n", " - ")))
        logging.info("Instituição selecionada: %s" % (instituicao.text.replace("\n", " - ")))

        time.sleep(1)

        skip = ""
        if enable_skipping:
            skip = input("Pular instituição? S/N? ")
            logging.debug("skip = {}".format(skip))

        if skip.lower() != "s":
            _, erro_referencia = coletar_aprovados_instituicao(confirmar_dados=confirmar_dados, abrir_driver=False, driver=driver)

            if erro_referencia:
                instituicoes_erros_referencia.append(instituicao.text.replace("\n", " - "))
        else:
            logging.info("Pulou estado {}".format(estado_text))

    if notificar:
        if len(instituicoes_erros_referencia) > 0:
            notify("Estado concluído (com erros)", "Retirada de dados do Estado {} concluído com {} erros de referência. Verifique arquivos gerados.".format(estado_text, len(instituicoes_erros_referencia)))
        else:
            notify("Estado concluído", "Retirada de dados do Estado {} concluído sem erros de referência.".format(estado_text))

    if len(instituicoes_erros_referencia) > 0:
        logging.warning("------ {} erros de referência ao coletar as instituições. Instituições afetadas:".format(len(instituicoes_erros_referencia)))
        for erro_referencia in instituicoes_erros_referencia:
            logging.warning(">>> {}".format(erro_referencia))
    else:
        logging.info("------ {} erros de referência ao coletar as instituições.".format(len(instituicoes_erros_referencia)))

    estado_erros_referencia = {estado_text: instituicoes_erros_referencia}

    return driver, estado_erros_referencia


def coletar_aprovados_ano(confirmar_dados=True, notificar=False, enable_skipping=False, enable_skipping_instituicoes=False):
    my_url = "https://site.medgrupo.com.br/#/aprovacoes"

    all_erros_referencia = {}

    # Define window size for certain class selectors appear, thanks to the page's JS
    options = Options()
    # options.add_argument("window-size=800,700")
    driver_path = os.path.join(os.getcwd(), 'chromedriver')

    driver = webdriver.Chrome(options=options, executable_path=driver_path)
    driver.get(my_url)
    logging.info("Navegador aberto e site carregado.")

    logging.info("Aguardando seleção do ano.")
    input("Selecione no navegador o ano desejado. Pressione enter para continuar...")
    logging.info("Ano selecionado.")

    ano_text = driver.find_element_by_xpath("//ul[@class='aprovacoes__selecao-ano']/li[@class='pointer active']").text

    logging.info("ano_text = %s" % (ano_text))

    logging.debug("confirmar_dados = {}".format(confirmar_dados))
    if confirmar_dados:
        logging.info("Confirmando dados.")

        print("\nO ano selecionado está correto?")
        print("Ano: %s" % (ano_text))
        print("S/N? ", end="")
        modificar = input("")

        if modificar.lower() == "n":
            logging.info("Usuário pede para modificar ano e/ou estado.")

            print("")
            ano_text = input("Digite o ano: ")

            logging.info("Novo ano_text = %s" % (ano_text))

    print("")

    all_estados_text = [
        "Rio de Janeiro",
        "São Paulo",
        "Minas Gerais",
        "Espírito Santo",
        "Paraná",
        "Santa Catarina",
        "Rio Grande do Sul",
        "Bahia",
        "Pernambuco",
        "Ceará",
        "Paraíba",
        "Alagoas",
        "Maranhão",
        "Rio Grande do Norte",
        "Sergipe",
        "Piauí",
        "Distrito Federal",
        "Goiás",
        "Mato Grosso",
        "Mato Grosso do Sul",
        "Amazonas",
        "Pará",
        "Acre",
        "Roraima",
        "Amapá",
        "Tocantins",
        "Rondônia"
    ]

    for estado_text in all_estados_text:
        logging.info("Próximo estado da lista: {}".format(estado_text))
        print("\n")
        input("Selecione no navegador o estado {}. Pressione enter para continuar...".format(estado_text))
        print("")

        estado_selecionado_text = driver.find_element_by_xpath("//h2[@class='estado-instituicao__titulo disable-select']").text
        if estado_text == estado_selecionado_text:
            logging.info("Estado selecionado e estado da lista são iguais")
        else:
            logging.warning("Estado selecionado e estado da lista NÃO são iguais")

        print(".Estado: %s" % (estado_selecionado_text))
        logging.info("Estado selecionado: %s" % (estado_selecionado_text))

        time.sleep(1)

        skip = ""
        if enable_skipping:
            skip = input("Pular estado? S/N? ")
            logging.debug("skip = {}".format(skip))

        if skip.lower() != "s":
            _, erros_referencia = coletar_aprovados_estado(confirmar_dados=confirmar_dados, abrir_driver=False, enable_skipping=enable_skipping_instituicoes, driver=driver)

            if notificar:
                if len(erros_referencia[estado_text.upper()]) > 0:
                    notify("Estado concluído (com erros)", "Retirada de dados do Estado {} concluído com {} erros de referência. Verifique arquivos gerados.".format(estado_text, len(erros_referencia[estado_text.upper()])))
                else:
                    notify("Estado concluído", "Retirada de dados do Estado {} concluído sem erros de referência.".format(estado_text))

            if len(erros_referencia) > 0:
                all_erros_referencia.update(erros_referencia)
        else:
            logging.info("Pulou estado {}".format(estado_text))

    if len(all_erros_referencia) > 0:
        logging.warning("------ {} erros de referência ao coletar os aprovados. Estados afetados:".format(len(all_erros_referencia)))
        for estado in all_erros_referencia:
            logging.warning("> {}".format(estado))

        logging.warning("----- Erros de referência discretos por instituição de cada estado:")
        for estado, lista_instituicoes_erro in all_erros_referencia.items():
            logging.warning("> {}: {} instituições afetas.".format(estado, len(lista_instituicoes_erro)))
            for instituicao in lista_instituicoes_erro:
                logging.warning(">>> {}".format(instituicao))
    else:
        logging.info("------ {} erros de referência ao coletar as instituições.".format(len(instituicoes_erros_referencia)))

    if notificar:
        if len(all_erros_referencia) > 0:
            notify("Aprovados de {} concluído (com erros)", "Retirada de dados de {} Estados com erros de referência. Verifique arquivos gerados.".format(ano_text, len(all_erros_referencia)))
        else:
            notify("Aprovados de {} concluído", "Retirada de dados concluída sem erros de referência.".format(ano_text))

    return driver


def concatenador(ano):
    arquivos_csv = os.path.join(os.getcwd(), 'Arquivos_CSV')
    file_ano_name = "aprovados_medgrupo_{}.csv".format(ano)

    if file_exists(os.path.join(arquivos_csv, file_ano_name)):
        i = 1
        while file_exists(os.path.join(arquivos_csv, "aprovados_medgrupo_{}_({}).csv".format(ano, i))):
            i += 1
        file_ano_name = "aprovados_medgrupo_{}_({}).csv".format(ano, i)

    with open(os.path.join(arquivos_csv, file_ano_name), "w+") as f_concat_ano:
        f_concat_ano.write("Estado;Instituição;Hospital;Curso;Colocação;Nome_Aprovado\n")

        for estado in os.listdir(arquivos_csv):
            if os.path.isdir(os.path.join(arquivos_csv, estado)):
                logging.info("Concatenando estado {}".format(estado))
                estado_path = os.path.join(arquivos_csv, estado)
                file_estado_name = "aprovados_medgrupo_{}_{}.csv".format(ano, estado)

                if file_exists(os.path.join(estado_path, file_estado_name)):
                    i = 1
                    while file_exists(os.path.join(estado_path, "aprovados_medgrupo_{}_{}_({}).csv".format(ano, estado, i))):
                        i += 1
                    file_estado_name = "aprovados_medgrupo_{}_{}_({}).csv".format(ano, estado, i)

                with open(os.path.join(estado_path, file_estado_name), "w+") as f_concat_estado:
                    f_concat_estado.write("Estado;Instituição;Hospital;Curso;Colocação;Nome_Aprovado\n")

                    for root, dirs, files in os.walk(estado_path):
                        if file_estado_name not in files:
                            # print(estado)
                            # print(root)
                            # print(dirs)
                            # print(files)
                            possible_files = []
                            for file in files:
                                if str(ano) in file:
                                    possible_files.append(file)
                                    logging.debug("Arquivo possível: {}".format(file))

                            if len(possible_files) > 0:
                                try:
                                    if len(possible_files) == 1:
                                        file = possible_files[0]
                                    else:
                                        numero = 0
                                        for teste in possible_files:
                                            if "(" in teste and ")" in teste:
                                                num_test = teste.split("(")[1]
                                                num_test = int(num_test.split(")")[0])
                                                if num_test > numero:
                                                    numero = num_test
                                                    file = teste

                                    assert file != ""
                                except Exception as e:
                                    raise e
                                else:
                                    logging.info("Arquivo selecionado: {}".format(file))
                                    with open(os.path.join(root, file), "r") as f_instituicao:
                                        f_instituicao.readline()  # ignorar primeira linha
                                        for linha in f_instituicao:
                                            f_concat_estado.write(linha)
                                            f_concat_ano.write(linha)


def main():
    logging.info(">>>>>>>>>>>>>>>>>>>>> Início da execução.")

    # Valores default
    DEBUG = False
    notificar = False
    skip = False
    skip_all = False
    concatenar = False
    somente_concatenar = False
    opcao = ""
    opcao_coleta = ""

    if len(sys.argv) > 1:

        # Valores default
        selected = False
        locked = False

        try:
            for arg in sys.argv[1:]:
                if arg.lower() == "-d" or arg.lower() == "--debug":
                    DEBUG = True
                    logging.info("Modo debug ativado.")

                if platform.system() == "Darwin" and (arg.lower() == "-n" or arg.lower() == "--notify"):
                    notificar = True
                    logging.info("Ativando notificações do MacOS.")

                if arg.lower() == "-s" or arg.lower() == "--skip":
                    skip = True
                    logging.info("Modo pular estados/instituições ativado.")

                if arg.lower() == "-sa" or arg.lower() == "--skip_all":
                    skip_all = True
                    skip = True
                    logging.info("Modo pular estados e instituições ativado.")

                if arg.lower() == "-c" or arg.lower() == "--concatenar":
                    concatenar = True
                    logging.info("Concatenar ao final da varredura.")

                if arg.lower() == "-sc" or arg.lower() == "--somente_concatenar":
                    somente_concatenar = True
                    logging.info("Somente concatenar.")

                if arg.lower() == "-a" or arg.lower() == "--ano":
                    opcao = '1'
                    selected = True
                    assert not locked

                if arg.lower() == "-e" or arg.lower() == "--estado":
                    opcao = '2'
                    selected = True
                    assert not locked

                if arg.lower() == "-ia" or arg.lower() == "--instituicao_aprovados":
                    opcao = '3'
                    opcao_coleta = False
                    selected = True
                    assert not locked

                if arg.lower() == "-it" or arg.lower() == "--instituicao_todos":
                    opcao = '3'
                    opcao_coleta = True
                    selected = True
                    assert not locked

                if selected:
                    locked = True
        except AssertionError:
            print("Erro: Mais de uma opção de coleta selecionada.\nConsulte -h ou --Help para ajuda sobre os comandos.\n")
            logging.error("Erro: Mais de uma opção de coleta selecionada.\n\n")
            sys.exit()
        finally:
            logging.debug("DEBUG = {}".format(DEBUG))
            logging.debug("skip = {}".format(skip))
            logging.debug("skip_all = {}".format(skip_all))
            logging.debug("concatenar = {}".format(concatenar))
            logging.debug("somente_concatenar = {}".format(somente_concatenar))
            logging.debug("opcao = {}".format(opcao))
            logging.debug("opcao_coleta = {}".format(opcao_coleta))
    else:
        print("Selecione o modo de operação:\n")
        print("1. Coletar aprovados de um ano.")
        print("2. Coletar aprovados de um estado.")
        print("3. Coletar aprovados de uma instituição.")
        print("x. Abortar\n")
        opcao = input("Digite a opção: ")
        logging.debug("opcao = %s" % (opcao))

        print("\nAtivar modo de debug?\n")
        print("1. Sim")
        print("2. Não\n")
        debug_mode = input("Digite a opção: ")
        logging.debug("debug_mode = %s" % (debug_mode))

        if debug_mode == '2':
            DEBUG = False
            logging.info("Modo debug desativado.")
        else:
            DEBUG = True
            logging.info("Modo debug ativado.")

        if platform.system() == "Darwin":
            print("\nAtivar notificações de input e fim de execução?\n")
            print("1. Sim")
            print("2. Não\n")
            notificar_opcao = input("Digite a opção: ")
            logging.debug("notificar = %s" % (notificar_opcao))

            if notificar_opcao == '1':
                notificar = True
                logging.info("Notificações ativadas.")
            else:
                notificar = False
                logging.info("Notificações desativadas.")

        print("\nAtivar opção de pular estado/instituição?\n")
        print("1. Sim, apenas estado.")
        print("2. Sim, estado e instituição.")
        print("3. Não\n")
        skip_option = input("Digite a opção: ")
        logging.debug("skip_option = %s" % (skip_option))

        if skip_option == '1':
            skip = True
            skip_all = False
            logging.info("Modo pular estados/instituições ativado.")
        elif skip_option == '2':
            skip = True
            skip_all = True
            logging.info("Modo pular estados e instituições ativado.")
        else:
            skip = False
            skip_all = False
            logging.info("Modo pular estados/instituições desativado.")

        print("\nConcatenar arquivos?\n")
        print("1. Sim")
        print("2. Não\n")
        concat_option = input("Digite a opção: ")
        logging.debug("concat_option = %s" % (concat_option))

        if concat_option == '2':
            concatenar = False
            logging.info("Notificações desativadas.")
        else:
            concatenar = True
            logging.info("Ativando notificações do MacOS.")

    # if len(sys.argv) > 1:
    #     opcao = str(sys.argv[1])
    # else:
    #     print("Selecione o modo de operação:\n")
    #     print("1. Coletar aprovados de um ano.")
    #     print("2. Coletar aprovados de um estado.")
    #     print("3. Coletar aprovados de uma instituição.")
    #     print("x. Abortar\n")
    #     opcao = input("Digite a opção: ")

    # logging.debug("opcao = %s" % (opcao))

    # if len(sys.argv) > 2:
    #     debug_mode = str(sys.argv[2])
    # else:
    #     print("\nAtivar modo de debug?\n")
    #     print("1. Sim")
    #     print("2. Não\n")
    #     debug_mode = input("Digite a opção: ")

    # logging.debug("debug_mode = %s" % (debug_mode))

    # if debug_mode == '2':
    #     DEBUG = False
    #     logging.info("Modo debug desativado.")
    # else:
    #     DEBUG = True
    #     logging.info("Modo debug ativado.")

    # if len(sys.argv) > 3:
    #     skip_option = str(sys.argv[3])
    # else:
    #     print("\nAtivar opção de pular estado/instituição?\n")
    #     print("1. Sim")
    #     print("2. Não\n")
    #     skip_option = input("Digite a opção: ")

    # logging.debug("skip_option = %s" % (skip_option))

    # if skip_option == '2':
    #     skip = False
    #     logging.info("Modo pular estados/instituições desativado.")
    # else:
    #     skip = True
    #     logging.info("Modo pular estados/instituições ativado.")

    if not somente_concatenar:
        if opcao == '1':
            logging.info("Selecionado: coletar_aprovados_ano()")
            driver = coletar_aprovados_ano(confirmar_dados=DEBUG, notificar=notificar, enable_skipping=skip, enable_skipping_instituicoes=skip_all)
        elif opcao == '2':
            logging.info("Selecionado: coletar_aprovados_estado()")
            driver, _ = coletar_aprovados_estado(confirmar_dados=DEBUG, notificar=notificar, enable_skipping=skip)
        elif opcao == '3':
            logging.info("Selecionado: coletar_aprovados_instituicao()")

            if opcao_coleta == "":
                print("\nModo coletar aprovados de Instituição selecionado.")
                print("Coletar na instituição:\n")
                print("1. Somente marcados como aprovados.")
                print("2. Todos os nomes. (Use quando houver problema de formatação na página)\n")
                opcao_coleta = input("Digite a opção: ")

                logging.debug("opcao_coleta = %s" % (opcao_coleta))

                if opcao_coleta == '2':
                    opcao_coleta = True
                    print("Coletando todos os nomes de uma instituição\n")
                    logging.info("[Sub-Menu] Selecionado: Coletar todos os nomes.")
                else:
                    # Opção default é coletar apenas nomes em destaque.
                    opcao_coleta = False
                    print("Coletando apenas os nomes destacados de uma instituição\n")
                    logging.info("[Sub-Menu] Selecionado: Coletar somente nomes marcados como aprovados.")

            driver, _ = coletar_aprovados_instituicao(confirmar_dados=DEBUG, notificar=notificar, coletar_todos_aprovados=opcao_coleta)
        else:
            logging.info("Nenhuma opção válida selecionada. Abortando operação...")
            logging.info("Fim da execução. <<<<<<<<<<<<<<<<<<<<<\n\n\n\n\n\n")
            print("Nenhuma opção válida selecionada.")
            print("Abortando...")
            sys.exit()

        driver.quit()

    if concatenar or somente_concatenar:
        print("\n")
        ano = int(input("Digite ano para concatenar: "))
        logging.info("Concatenando arquivos do ano {}".format(ano))
        concatenador(ano)
        print("Arquivos do ano de {} concatenados com sucesso.".format(ano))
        if notificar:
            notify("Concatenação concluída", "Confira os arquivos gerados.")

    logging.info("Fim da execução. <<<<<<<<<<<<<<<<<<<<<\n\n\n\n\n\n")


def help():
    print("\n>>>>>> HELP: Ajuda do Web Scrapper.")
    print("")
    print(">>Uso: python {} [-h | --Help] [-d | --Debug]".format(sys.argv[0]))
    print("         [-n | --Notify] [-s | --Skip] [-sa | --Skip_All]")
    print("         [-c | --Concatenar] [-sc | --Somente_Concatenar]")
    print("       * [-a | --Ano] * [-e | --Estado]")
    print("       * [-ia | --Instituicao_Aprovados]")
    print("       * [-it | --Instituicao_Todos]")
    print("")
    print("    Atenção: usar apenas um dos que tem *")
    print("")
    print(">>Lista de comandos:")
    print("")
    print("Comandos gerais:")
    print("-h  ou --Help:                   abrir menu de ajuda;")
    print("-d  ou --Debug:                  ativar modo de confirmação de dados;")
    print("-n  ou --Notify:                 ativar notificação de final de execução ou espera de input")
    print("                                 (Disponível somente para MacOS);")
    print("-s  ou --Skip:                   ativar possibilidade de pular um estado na varredura de ano")
    print("                                 ou instituição na varredura de estado;")
    print("-sa ou --Skip_All:               ativar possibilidade de pular um estado e uma instituição")
    print("                                 na varredura de ano ou instituição na varredura de estado;")
    print("")
    print("Função Concatenar:")
    print("-c  ou --Concatenar:             concatenar arquivos CSV ao final da varredura;")
    print("-sc ou --Somente_Concatenar:     pular varredura e somente concatenar arquivos CSV;")
    print("")
    print("Tipo de coleta de dados:")
    print("-a  ou --Ano:                    coletar todos os estados e instituições de determinado ano;")
    print("-e  ou --Estado:                 coletar todas as instituições de determinado estado;")
    print("-ia ou --Instituicao_Aprovados:  coletar de uma instituição os nomes que estejam com a tag")
    print("                                 de aprovado;")
    print("-it ou --Instituicao_Todos:      coletar de uma instituição todos os nomes, independente da tag")
    print("")
    print("Obs: não utilizar opções de coletar ano, estado e instituição na mesma série de comandos.")
    print("Obs2: na varredura de estado, os comandos Skip e Skip_All tem o mesmo efeito.\n")


if __name__ == '__main__':
    # https://stackoverflow.com/questions/740287/how-to-check-if-one-of-the-following-items-is-in-a-list
    if [x for x in sys.argv if x.lower() in ["-h", "--help"]]:
        help()
        logging.info("Função help() acionada.")
    else:
        main()
