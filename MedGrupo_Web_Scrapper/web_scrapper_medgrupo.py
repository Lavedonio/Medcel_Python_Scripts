import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


my_url = "https://site.medgrupo.com.br/#/aprovacoes"

# Define window size for certain class selectors appear, thanks to the page's JS
options = Options()
# options.add_argument("window-size=800,700")

driver = webdriver.Chrome(options=options, executable_path=r'/Library/FilesToPath/chromedriver')
driver.get(my_url)
# driver.set_window_size(800, 800)
# time.sleep(2)
driver.set_window_size(1200, 800)
time.sleep(2)

infos_por_instituicao = driver.find_elements_by_xpath("//div[@class='content-lista-aprovados__container']")


for infos_por_hospital in infos_por_instituicao:
    hospital = infos_por_hospital.find_element_by_xpath(".//div[@class='content-lista-aprovados__hospital']")
    all_cursos = infos_por_hospital.find_elements_by_xpath(".//h4[@class='content-lista-aprovados__titulo']")
    all_aprovados = infos_por_hospital.find_elements_by_xpath(".//ul[@class='content-lista-aprovados__nomes' or @class='content-lista-aprovados__nomes stamp']")

    i = 0

    for curso in all_cursos:
        aprovados_curso = all_aprovados[i].find_elements_by_xpath(".//span[@class='destaque']")
        i += 1
        for aprovado in aprovados_curso:
            print("%s; %s; %s" % (hospital.text, curso.text, aprovado.text))
    #     num_aprovado = 1
    #     primeira_execucao = True
    #     while (primeira_execucao or num_aprovado != 1) and i < len(all_aprovados):
    #         aprovado = all_aprovados[i].find_element_by_xpath(".//span[@class='destaque']")
    #         print("%s; %s; %s" % (hospital.text, curso.text, aprovado.text))
    #         i += 1
    #         num_aprovado = int(aprovado.text.split()[0][0:-1])   # Texto da forma: "1. Nome Completo"
    #         primeira_execucao = False
    # while i < len(all_aprovados):
    #     aprovado = all_aprovados[i].find_element_by_xpath(".//span[@class='destaque']")
    #     print(aprovado.text)
    #     i += 1

# all_hospital = driver.find_elements_by_xpath("//div[@class='content-lista-aprovados__hospital']")

# for hospital in all_hospital:
#     print(hospital.text)

# all_cursos = driver.find_elements_by_xpath("//h4[@class='content-lista-aprovados__titulo']")
# for curso in all_cursos:
#     nome_curso = curso.find_element_by_xpath("//span[@class='no-events']")
#     print(curso.text)

# all_aprovados = driver.find_elements_by_xpath("//ul[@class='content-lista-aprovados__nomes' or @class='content-lista-aprovados__nomes stamp']")
# print(all_uls.text)
# for aprovado_curso in all_aprovados:
#     for aprovado in aprovado_curso.find_elements_by_xpath(".//span[@class='destaque']"):
#         print(aprovado.text)

driver.quit()
