import os
import sys
import logging
import logging.config
from os.path import isfile as file_exists
from os.path import isdir as dir_exists
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException

logging.basicConfig(filename='web_scrapper.log', level=logging.DEBUG,
    format='%(asctime)s:%(levelname)s:%(funcName)s:%(message)s')

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
})


def notify(title, text):
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


def coletar_aprovados_instituicao(confirmar_dados=True, abrir_driver=True, driver=None, coletar_todos_aprovados=False):
    logging.debug("abrir_driver = {}".format(abrir_driver))
    if abrir_driver:
        logging.info("Inicializando driver.")
        my_url = "https://site.medgrupo.com.br/#/aprovacoes"

        # Define window size for certain class selectors appear, thanks to the page's JS
        options = Options()
        # options.add_argument("window-size=800,700")

        driver = webdriver.Chrome(options=options, executable_path=r'/Library/FilesToPath/chromedriver')
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
        try:
            for infos_por_hospital in infos_por_instituicao:
                hospital = infos_por_hospital.find_element_by_xpath(".//div[@class='content-lista-aprovados__hospital']")
                logging.info("---Hospital: {}".format(hospital.text))

                all_cursos_aprovados = infos_por_hospital.find_elements_by_xpath(".//div[not(contains(@class, 'content-lista-aprovados__info'))]")
                logging.info("Cursos encontrados.")
                logging.debug("len(infos_por_instituicao) = {}".format(len(infos_por_instituicao)))

                print("---Hospital: %s" % (hospital.text))

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

        except Exception as e:
            logging.exception("Erro inesperado ocorrido.")
            driver.quit()
            raise e

    logging.info("Fim da leitura da instituição.")
    return driver, erro_referencia


def file_handling(ano_text, estado_text, instituicao_text_sigla):
    file_path = os.path.join("Arquivos_CSV", estado_text, instituicao_text_sigla)

    logging.debug("file_path = {}".format(file_path))
    os.makedirs(file_path, exist_ok=True)
    logging.info("Path {} criado, se não existia.".format(file_path))

    if file_exists(os.path.join('.', file_path, 'aprovados_medgrupo_%s_%s_%s.csv' % (ano_text, estado_text, instituicao_text_sigla))):
        i = 1
        while file_exists(os.path.join('.', file_path, 'aprovados_medgrupo_%s_%s_%s_(%s).csv' % (ano_text, estado_text, instituicao_text_sigla, i))):
            i += 1
        print("Criando novo arquivo aprovados_medgrupo_%s_%s_%s_(%s).csv...\n" % (ano_text, estado_text, instituicao_text_sigla, i))
        file_name = "aprovados_medgrupo_%s_%s_%s_(%s).csv" % (ano_text, estado_text, instituicao_text_sigla, i)
    else:
        print("Criando novo arquivo aprovados_medgrupo_%s_%s_%s.csv...\n" % (ano_text, estado_text, instituicao_text_sigla))
        file_name = "aprovados_medgrupo_%s_%s_%s.csv" % (ano_text, estado_text, instituicao_text_sigla)

    logging.info("file_name = {}".format(file_name))
    logging.debug("return {}".format(os.path.join(os.getcwd(), file_path, file_name)))

    return os.path.join(os.getcwd(), file_path, file_name)


def coletar_aprovados_estado(confirmar_dados=True):
    my_url = "https://site.medgrupo.com.br/#/aprovacoes"

    # Define window size for certain class selectors appear, thanks to the page's JS
    options = Options()
    # options.add_argument("window-size=800,700")

    driver = webdriver.Chrome(options=options, executable_path=r'/Library/FilesToPath/chromedriver')
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

        print("|--Instituição: %s" % (instituicao.text.replace("\n", " - ")))
        logging.info("Instituição selecionada: %s" % (instituicao.text.replace("\n", " - ")))

        _, erro_referencia = coletar_aprovados_instituicao(confirmar_dados=True, abrir_driver=False, driver=driver)

        if erro_referencia:
            instituicoes_erros_referencia.append(instituicao.text.replace("\n", " - "))

    if len(instituicoes_erros_referencia) > 0:
        logging.warning("------ {} erros de referência ao coletar as instituições. Instituições afetadas:".format(len(instituicoes_erros_referencia)))
        for erro_referencia in instituicoes_erros_referencia:
            logging.warning(">>> {}".format(erro_referencia))
    else:
        logging.info("------ {} erros de referência ao coletar as instituições.".format(len(instituicoes_erros_referencia)))

    return driver


def main():
    logging.info(">>>>>>>>>>>>>>>>>>>>> Início da execução.")
    if len(sys.argv) > 1:
        opcao = str(sys.argv[1])
    else:
        print("Selecione o modo de operação:\n")
        print("1. Coletar aprovados de um estado.")
        print("2. Coletar aprovados de uma instituição.")
        print("x. Abortar\n")
        opcao = input("Digite a opção: ")

    logging.debug("opcao = %s" % (opcao))

    if opcao == '1':
        logging.info("Selecionado: coletar_aprovados_estado()")
        driver = coletar_aprovados_estado()
    elif opcao == '2':
        logging.info("Selecionado: coletar_aprovados_instituicao()")

        if len(sys.argv) > 2:
            opcao_coleta = str(sys.argv[2])
        else:
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

        driver, _ = coletar_aprovados_instituicao(coletar_todos_aprovados=opcao_coleta)
    else:
        logging.info("Nenhuma opção válida selecionada. Abortando operação...")
        logging.info("Fim da execução. <<<<<<<<<<<<<<<<<<<<<\n\n\n\n\n\n")
        quit()
    driver.quit()
    logging.info("Fim da execução. <<<<<<<<<<<<<<<<<<<<<\n\n\n\n\n\n")


if __name__ == '__main__':
    main()
