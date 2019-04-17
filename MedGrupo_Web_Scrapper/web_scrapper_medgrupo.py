import sys
from os.path import isfile as file_exists
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException


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
        file.write("Estado;Instituição;Hospital;Colocação;Nome_Aprovado\n")

    return file, test

# <------------------ /File Handler ------------------>


# <----------------- Webdriver start ----------------->
def web_scrapper(file, test):
    print("\nIniciando importação...\n")

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
    estado_text = all_estados_text[0]

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

        print("-Instituição: %s" % (instituicao_text))

        instituicao.click()

        infos_por_instituicao = driver.find_elements_by_xpath("//div[@class='content-lista-aprovados__container']")

        for infos_por_hospital in infos_por_instituicao:
            print(len(infos_por_instituicao))
            hospital = infos_por_hospital.find_element_by_xpath(".//div[@class='content-lista-aprovados__hospital']")
            all_cursos = infos_por_hospital.find_elements_by_xpath(".//h4[@class='content-lista-aprovados__titulo']")
            all_aprovados = infos_por_hospital.find_elements_by_xpath(".//ul[@class='content-lista-aprovados__nomes' or @class='content-lista-aprovados__nomes stamp']")

            i = 0
            print("--Hospital: %s" % (hospital.text))

            for curso in all_cursos:
                try:
                    if i < len(all_aprovados):
                        aprovados_curso = all_aprovados[i].find_elements_by_xpath(".//span[@class='destaque']")
                        i += 1
                        for aprovado in aprovados_curso:
                            file.write("%s;%s;%s;%s;%s\n" % (estado_text, instituicao_text, hospital.text, curso.text, aprovado.text.replace(". ", ";")))
                except StaleElementReferenceException:
                    print("StaleElementReferenceException occured; line not written on file. Continuing...")

        # driver.refresh()
        num_instituicao += 1

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


if __name__ == '__main__':
    main()
