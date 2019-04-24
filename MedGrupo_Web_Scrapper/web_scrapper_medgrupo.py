import os
import sys
from os.path import isfile as file_exists
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException


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


def main():
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


def coletar_aprovados_instituicao():
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

if __name__ == '__main__':
    # main()
    # test_function()
    coletar_aprovados_instituicao()
