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

### Lista de funções:
# notify(title, text)
# file_handling(ano_text, estado_text, instituicao_text_sigla)
# coletar_aprovados_instituicao(confirmar_dados=True, notificar=False, abrir_driver=True, driver=None, coletar_todos_aprovados=False)
# coletar_aprovados_estado(confirmar_dados=True, notificar=False, abrir_driver=True, enable_skipping=False, driver=None)
# coletar_aprovados_ano(confirmar_dados=True, notificar=False, enable_skipping=False, enable_skipping_instituicoes=False)
# concatenador(ano)
# main()
# help()


def notify(title, text):
    ''' >> I/O:
        str, str -> void
    '''
    if platform.system() == "Darwin":
        os.system("""
                  osascript -e 'display notification "{}" with title "{}"'
                  """.format(text, title))


def file_handling(ano_text, estado_text, instituicao_text_sigla):
    ''' >> I/O:
            str, str, str -> str

        >> Parâmetros:
        - ano_text: Ano em formato de texto da instituição cujo arquivo será criado.

        - estado_text: Estado em formato de texto da instituição cujo arquivo será criado.

        - instituicao_text_sigla: Sigla da Instituição em formato de texto da instituição cujo arquivo será criado.

        >> Retorno:
        - path: retorna o path absoluto do arquivo a ser criado

        >> Descrição:
            A partir do ano, estado e sigla da instituição, cria-se um path da seguinte forma:
                Arquivos_CSV/estado_text/instituicao_text_sigla
            Dentro de cada path é então criado um nome para o arquivo na forma:
                aprovados_medgrupo_{ano_text}_{estado_text}_{instituicao_text_sigla}.csv
            ou
                aprovados_medgrupo_{ano_text}_{estado_text}_{instituicao_text_sigla}_({i}).csv,
                    sendo i um valor autoincrimentante de forma com que nenhum arquivo seja sobrescrito.
            Com o nome do arquivo criado, é retornado o path absoluto do arquivo para que este seja criado de fato na
        função coletar_aprovados_instituicao(), onde é chamado.
    '''

    # Troca / e \n por - para evitar problemas na criação de paths absolutos que podem causar erros de execução
    instituicao_text_sigla = instituicao_text_sigla.replace("/", "-")
    instituicao_text_sigla = instituicao_text_sigla.replace("\n", "-")

    # Nome do path a ser criado
    file_path = os.path.join("Arquivos_CSV", estado_text, instituicao_text_sigla)

    # Cria o path com todos os diretórios intermediários, caso não existiam
    logging.debug("file_path = {}".format(file_path))
    os.makedirs(file_path, exist_ok=True)
    logging.info("Path {} criado, se não existia.".format(file_path))

    # Procura um nome válido para o arquivo CSV da instituição
    # Se já existe algum arquivo com este nome, percorre um loop até encontrar um que não exista
    if file_exists(os.path.join('.', file_path, 'aprovados_medgrupo_%s_%s_%s.csv' % (ano_text, estado_text, instituicao_text_sigla))):
        i = 1
        while file_exists(os.path.join('.', file_path, 'aprovados_medgrupo_%s_%s_%s_(%s).csv' % (ano_text, estado_text, instituicao_text_sigla, i))):
            i += 1
        print("| |-Criando novo arquivo aprovados_medgrupo_%s_%s_%s_(%s).csv..." % (ano_text, estado_text, instituicao_text_sigla, i))
        file_name = "aprovados_medgrupo_%s_%s_%s_(%s).csv" % (ano_text, estado_text, instituicao_text_sigla, i)
    else:
        print("| |-Criando novo arquivo aprovados_medgrupo_%s_%s_%s.csv..." % (ano_text, estado_text, instituicao_text_sigla))
        file_name = "aprovados_medgrupo_%s_%s_%s.csv" % (ano_text, estado_text, instituicao_text_sigla)

    # Com o nome criado, realiza o log dele
    logging.info("file_name = {}".format(file_name))
    logging.debug("return {}".format(os.path.join(os.getcwd(), file_path, file_name)))

    # Retorna o path absoluto do arquivo a ser criado
    return os.path.join(os.getcwd(), file_path, file_name)


def coletar_aprovados_instituicao(confirmar_dados=True, notificar=False, abrir_driver=True, driver=None, coletar_todos_aprovados=False):
    ''' >> I/O:
        opt(bool), opt(bool), opt(bool), opt(bool), opt(bool) -> driver, bool

        >> Parâmetros:
        - confirmar_dados (optional): Se ativado, a cada instituição a ser varrida, pergunta ao usuário se o ano, estado e instituição
            analisados estão corretos e, se não, deixa o usuário modificá-los. Ativado pela opção debug da função main.

        - notificar (optional): Se ativado, lança uma notificação ao final da varredura da instituição (apenas para MacOS).
            Ativado pela opção notificar da função main.

        - abrir_driver (optional): Se ativado, cria um novo driver para coleta de dados.
            Não ativo se função de coletar instituição for chamada pela função de coletar estado.

        - driver (optional): Se a função for chamada pela função de coletar estado, então ele recebe o driver criado naquela função.

        - coletar_todos_aprovados (optional): Se ativado, coleta todos os nomes da lista, mesmo que não marcados como aprovados.
            Ativado pela opção opcao_coleta da função main.

        >> Retorno:
        - driver: retorna driver do navegador rodando no momento.

        - erros_referencia: booleano dizendo se houve ou não algum erro de referência ao se coletar os dados da instituição.

        >> Descrição:
            Coleta todos os aprovados de uma determinada instituição, de todos os hospitais e cursos à ela pertencente.
            Retorna o driver, ou para ser encerrado na execução principal, ou para ser ignorado pela função de coleta de estado;
        além de retornar um booleano dizendo se houve erro de referência ocorrido na varredura da instituição.
    '''

    # Driver Setup. Só cria um novo driver se não houver outro ativo
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

        # Pausa a execução e aguarda a seleção do ano, do estado e do instituição no navegador, até que se dê enter
        logging.info("Aguardando seleção do ano, estado e instituição.")
        input("Selecione no navegador o ano, o estado e instituição desejados. Pressione enter para continuar...")
        logging.info("Ano, estado e instituição selecionados.")

    # Retira o ano e o estado da página do site
    ano_text = driver.find_element_by_xpath("//ul[@class='aprovacoes__selecao-ano']/li[@class='pointer active']").text
    estado_text = driver.find_element_by_xpath("//h2[@class='estado-instituicao__titulo disable-select']").text

    # Retira a instituição da página do site formata em sigla + nome
    instituicao_text = driver.find_element_by_xpath("//h2[@class='lista-aprovados__titulo']").text
    instituicao_text_sigla, *_ = instituicao_text.split(" - ")
    instituicao_text_nome = instituicao_text.split("\n")[1]
    instituicao_text = instituicao_text_sigla + " - " + instituicao_text_nome

    logging.info("ano_text = %s" % (ano_text))
    logging.info("estado_text = %s" % (estado_text))
    logging.info("instituicao_text = %s" % (instituicao_text))
    logging.debug("instituicao_text_sigla = %s" % (instituicao_text_sigla))

    # Confirmação dos dados de ano, estado e instituição retirados da página
    # Somente ocorre se a opção de confirmar dados estiver ativo
    logging.debug("confirmar_dados = {}".format(confirmar_dados))
    if confirmar_dados:
        logging.info("Confirmando dados.")

        print("\nEstes dados estão corretos?")
        print("Ano: %s" % (ano_text))
        print("Estado: %s" % (estado_text))
        print("Instituição: %s" % (instituicao_text))
        print("S/N? ", end="")
        modificar = input("")

        # Default é não modificar; modifica apenas se explicitamente digitar "N" ou "n" (dados não corretos)
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

    # A partir do ano, estado e sigla da instituição, cria-se um path da forma:
    # ./Arquivos_CSV/estado_text/instituicao_text_sigla
    file_fullname = file_handling(ano_text, estado_text, instituicao_text_sigla)
    logging.info("file_fullname = {}".format(file_fullname))

    # Cria arquivo CSV do ano e já escreve os cabeçalhos na primeira linha
    with open(file_fullname, "w+") as file:
        logging.debug("Arquivo aberto.")
        file.write("Estado;Instituição;Hospital;Curso;Colocação;Nome_Aprovado\n")

        # Pega todos os blocos de código que contém os aprovados, divididos em hospitais.
        # Geralmente contém toda a estrutura de hospital, curso e aprovados, mas alguns vem vazios
        # (má programação do site) e, como não se sabe qual deles virá quebrado, é necessário listar e testar todos.
        infos_por_instituicao = driver.find_elements_by_xpath("//div[@class='content-lista-aprovados__container']")
        logging.debug("len(infos_por_instituicao) = {}".format(len(infos_por_instituicao)))

        # Por default, não há erros de referência
        erro_referencia = False

        # Passa por todos os blocos de aprovados por hospital
        for infos_por_hospital in infos_por_instituicao:

            # Como pode ser que seja um bloco de informações vazio, o método find_element_by_xpath
            # pode falhar, então esse bloco try/except serve para tratar esse erros previsíveis.
            # É muito importante o bloco de try/except esteja dentro do for, para que não se perca
            # as informações de uma instituição caso o primeiro bloco esteja com defeito.
            try:
                # Retira o hospital de um dos blocos de aprovados por hospital
                hospital = infos_por_hospital.find_element_by_xpath(".//div[@class='content-lista-aprovados__hospital']")
                logging.info("---Hospital: {}".format(hospital.text))

                # Retira a lista contendo todos os cursos e aprovados de um dos blocos de aprovados por hospital
                all_cursos_aprovados = infos_por_hospital.find_elements_by_xpath(".//div[not(contains(@class, 'content-lista-aprovados__info'))]")
                logging.info("Cursos encontrados.")
                logging.debug("len(infos_por_instituicao) = {}".format(len(infos_por_instituicao)))

                # Imprime nome do hospital que foi encontrado no bloco (para conferência do usuário)
                print("| |---Hospital: %s" % (hospital.text))

                # Contagem do número de cursos por hospital para salvar no log
                num_cursos = 0

                # Passa por todos os cursos dentro do bloco de hospital
                for cursos_aprovados in all_cursos_aprovados[1:]:

                    # Retira o curso de um dos blocos de hospital da instituição
                    curso = cursos_aprovados.find_element_by_xpath(".//h4[@class='content-lista-aprovados__titulo']")
                    logging.debug("curso.text = {}".format(curso.text))

                    # Se opção coletar_todos_aprovados estiver ativa, ele não restringe a coleta dos aprovados
                    # apenas aos nomes marcados como tais, e sim coleta todos os nomes de alunos que aparecer.
                    # Isso serve caso todos os aprovados não estejam marcados como tais por falha do site.
                    if coletar_todos_aprovados:
                        all_aprovados_curso = cursos_aprovados.find_elements_by_xpath(".//li/span")
                        logging.debug("Coletando todos os nomes.")
                    else:
                        all_aprovados_curso = cursos_aprovados.find_elements_by_xpath(".//li/span[@class='destaque']")
                        logging.debug("Coletando apenas os marcados como aprovados")

                    # Soma 1 na contagem do número de cursos por hospital para salvar no log
                    num_cursos += 1

                    # Valor default é falso, pois os aprovados estão sempre antes dos suplentes (na lista e na vida real)
                    suplentes = False

                    # Contagem do número de aprovados por curso para salvar no log
                    num_aprovados = 0

                    # Passa por todos os cursos dentro do bloco de hospital
                    for aprovado in all_aprovados_curso:

                        # Se os próximos nomes forem de suplentes, ignora todos até o final da lista do curso
                        if not suplentes:

                            # Se a palavra "Suplente" aparecer significa que os nomes em seguida até o final do curso não são de aprovados.
                            # Ele não deixa setar essa condição se a opção de coletar_todos_aprovados estiver ativa.
                            if "suplente" in aprovado.text.lower() and not coletar_todos_aprovados:
                                suplentes = True
                                logging.debug("Suplente encontrado, pulando restante dos nomes no curso.")

                            # Na lista de aprovados existe também a palavra MEDGRUPO, que deve ser ignorada ao coletar os valores/
                            elif "medgrupo" in aprovado.text.lower():
                                pass

                            # Impede um erro de out of range no bloco if/elif/else no else a seguir
                            elif len(aprovado.text) == 0:
                                logging.warning("aprovado.text é uma string vazia.")

                            # Escreve no arquivo a combinação total de todas as informações.
                            else:
                                # Comando de log abaixo pode gerar um arquivo de log muito poluído.
                                # Edite por sua conta e risco de ter um log ilegível.
                                # logging.debug("aprovado.text = {}".format(aprovado.text))

                                # Se o nome do aprovado começar com um . então ele não possui uma classificação.
                                # Substitui-se então o ponto por ; para equiparar ao número de colunas correto.
                                if aprovado.text[0] == ".":
                                    file.write("%s;%s;%s;%s;%s\n" % (estado_text, instituicao_text, hospital.text, curso.text, aprovado.text.replace(". ", ";", 1)))

                                # Se o primeiro número for um dígito, significa que há classificação.
                                # Esta é então separada do nome por um ; (efetivamente colocando em colunas diferentes)
                                elif aprovado.text[0].isdigit():
                                    file.write("%s;%s;%s;%s;%s\n" % (estado_text, instituicao_text, hospital.text, curso.text, aprovado.text.replace(". ", ";", 1)))

                                # Se nenhuma correspondência comum bater, assume-se então que há apenas o nome.
                                # Adiciona-se então o ; para equiparar ao número de colunas correto.
                                else:
                                    file.write("%s;%s;%s;%s;;%s\n" % (estado_text, instituicao_text, hospital.text, curso.text, aprovado.text))

                                # Soma 1 na contagem do número de cursos por hospital para salvar no log
                                num_aprovados += 1

                    # loga o número total de aprovados ao final da leitura de cada curso
                    logging.info("-- {} aprovados registrados no curso {}".format(num_aprovados, curso.text))

                # loga o número total de cursos ao final da leitura de um dos hospitais
                logging.info("---- {} cursos registrados no hospital {}".format(num_cursos, hospital.text))

            # Tratamento do erro: StaleElementReferenceException
            # Geralmente causado por uma peração do DOM (Document Object Model) acontecendo
            # na página no momento, tornando o elemento inacessível.
            # https://stackoverflow.com/questions/12967541/how-to-avoid-staleelementreferenceexception-in-selenium
            except StaleElementReferenceException:
                erro_referencia = True
                print("\nStaleElementReferenceException occured; line not written on file. Aborting...\n")
                logging.error("StaleElementReferenceException")
                logging.warning("Pulando restante dos dados do hospital.")

            # Tratamento do erro: NoSuchElementException
            # Elemento da página (ou parte dela) não encontrado ao tentar ser acessado.
            # Causado pelo método find_elements_by_xpath
            except NoSuchElementException:
                erro_referencia = True
                print("\nNoSuchElementException; Indo para próximo hospital\n")
                logging.error("NoSuchElementException")
                logging.warning("Pulando restante dos dados do hospital.")

            # Tratamento de erro desconhecido.
            # Driver é finalizado e exceção levantada.
            except Exception as e:
                logging.exception("Erro inesperado ocorrido.")
                driver.quit()
                raise e

    # Se opção de notificar estiver ativa, notifica ao final da execução de varredura da instituição
    # que a varredura deste foi concluída e se possui erro.
    if notificar:
        if erro_referencia:
            notify("Instituição concluída (com erros)", "Retirada de dados da instituição {} concluída com erro de referência. Verifique arquivo gerado.".format(instituicao_text_sigla))
        else:
            notify("Instituição concluída", "Retirada de dados da instituição {} concluída sem erros".format(instituicao_text))

    logging.info("Fim da leitura da instituição.")

    # Por fim, retorna o driver para que possa ser finalizado na rotina principal de execução do programa
    # e o booleado informando se houve erro na varredura da instituição, sendo este último só utilizado se for chamado pelas funções coletar_aprovados_ano() ou coletar_aprovados_estado()
    return driver, erro_referencia


def coletar_aprovados_estado(confirmar_dados=True, notificar=False, abrir_driver=True, enable_skipping=False, driver=None):
    ''' >> I/O:
        opt(bool), opt(bool), opt(bool), opt(bool), opt(bool) -> driver, dict

        >> Parâmetros:
        - confirmar_dados (optional): Se ativado, a cada instituição a ser varrida, pergunta ao usuário se o ano, estado e instituição
            analisados estão corretos e, se não, deixa o usuário modificá-los. Ativado pela opção debug da função main.

        - notificar (optional): Se ativado, lança uma notificação ao final da varredura de cada estado (apenas para MacOS).
            Ativado pela opção notificar da função main.

        - abrir_driver (optional): Se ativado, cria um novo driver para coleta de dados.
            Não ativo se função de coletar estado for chamada pela função de coletar ano.

        - enable_skipping (optional): Se ativado, a cada estado a ser varrido, pergunta ao usuário se deseja pulá-lo.
            Ativado pela opção skip da função main.

        - driver (optional): Se a função for chamada pela função de coletar ano, então ele recebe o driver criado naquela função.

        >> Retorno:
        - driver: retorna driver do navegador rodando no momento.

        - estado_erros_referencia: dicionário contendo todos os erros de referência ocorridos na varredura do estado

        >> Descrição:
            Coleta todos os aprovados de um determinado estado, de todas as instituições presentes
        e salva cada instituição em uma pasta diferente, de forma a facilitar a conferência posterior da integridade dos dados.
            Não coleta aprovados diretamente, mas sim chamando a função de coletar_aprovados_instituicao().
            Retorna o driver, ou para ser encerrado na execução principal, ou para ser ignorado pela função de coleta de ano;
        além de retornar um dicionário contendo todos os erros de referência ocorridos na varredura do estado.
    '''

    # Driver Setup. Só cria um novo driver se não houver outro ativo
    if abrir_driver:
        my_url = "https://site.medgrupo.com.br/#/aprovacoes"

        # Define window size for certain class selectors appear, thanks to the page's JS
        options = Options()
        # options.add_argument("window-size=800,700")
        driver_path = os.path.join(os.getcwd(), 'chromedriver')

        driver = webdriver.Chrome(options=options, executable_path=driver_path)
        driver.get(my_url)
        logging.info("Navegador aberto e site carregado.")

        # Pausa a execução e aguarda a seleção do ano e do estado no navegador, até que se dê enter
        logging.info("Aguardando seleção do ano e estado.")
        input("Selecione no navegador o ano e o estado desejados. Pressione enter para continuar...")
        logging.info("Ano e estado selecionados.")

    # Retira o ano e o estado da página do site
    ano_text = driver.find_element_by_xpath("//ul[@class='aprovacoes__selecao-ano']/li[@class='pointer active']").text
    estado_text = driver.find_element_by_xpath("//h2[@class='estado-instituicao__titulo disable-select']").text

    logging.info("ano_text = %s" % (ano_text))
    logging.info("estado_text = %s" % (estado_text))

    # Confirmação dos dados retirados da página 5 linhas de código atrás
    # Somente ocorre se a opção de confirmar dados estiver ativo
    logging.debug("confirmar_dados = {}".format(confirmar_dados))
    if confirmar_dados:
        logging.info("Confirmando dados.")

        print("\nEstes dados estão corretos?")
        print("Ano: %s" % (ano_text))
        print("Estado: %s" % (estado_text))
        print("S/N? ", end="")
        modificar = input("")

        # Default é não modificar; modifica apenas se explicitamente digitar "N" ou "n" (dados não corretos)
        if modificar.lower() == "n":
            logging.info("Usuário pede para modificar ano e/ou estado.")

            print("")
            ano_text = input("Digite o ano: ")
            estado_text = input("Digite nome do estado: ")

            logging.info("Novo ano_text = %s" % (ano_text))
            logging.info("Novo estado_text = %s" % (estado_text))

        print("")

    # Retira a lista de todas as instituições de um respectivo estado da página do site
    all_instituicoes = driver.find_elements_by_xpath("//ul[@class='estado-instituicao__lista disable-select']/li")
    logging.debug("Lista de instituições adquirida")

    instituicoes_erros_referencia = []

    # Faz a varredura de todas as instituições da lista
    logging.debug("len(all_instituicoes) = {}".format(len(all_instituicoes)))
    for instituicao in all_instituicoes:
        # Clica na instituição da vez na lista
        instituicao.click()

        # Imprime nome da instituição que foi encontrada na página (para conferência do usuário)
        print("|")
        print("|---Instituição: %s" % (instituicao.text.replace("\n", " - ")))
        logging.info("Instituição selecionada: %s" % (instituicao.text.replace("\n", " - ")))

        # ATENÇÃO: PARTE MAIS IMPORTANTE DO CÓDIGO
        # Um simples comando de pausa da execução do código por 1 segundo não parece tão relevante assim,
        # mas este é um caso de que como uma linha de código faz toda a diferença.
        # Geralmente os próprios comandos do webdriver funcionam muito bem, pois esperam a página terminar
        # de carregar para executar os comandos. Isso não acontece nesse caso específico, pois esse site é
        # extremamente dependente de JavaScript.
        # Ao mudar de instituição, não é ativado o carregamento da página no navegador (por conta de todas
        # as informações estarem já carregadas no front). Isso não ativa o trigger da funcionalidade
        # biblioteca Selenium, fazendo com que o restante do código do Scrapper seja executando antes que
        # o JavaScript da página termine de carregar as informações. Isso causa todo tipo de erro nas linhas
        # de código seguintes e na função coletar_aprovados_intituicao(), como ausência de tags
        # (StaleElementReferenceException e/ou NoSuchElementException), index out of range nas listas (IndexError),
        # entre outros.
        # Para corrigir esse problema, então, deve-se dar um tempo para que o JavaScript termine de carregar
        # a página. Para isso que serve esta pequena, mas tão importante, linha de código.
        time.sleep(1)

        # Se enable_skipping estiver ativado, pergunta se deseja pular o estado
        skip = ""
        if enable_skipping:
            skip = input("Pular instituição? S/N? ")
            logging.debug("skip = {}".format(skip))

        # Default é não pular; pula apenas se explicitamente digitar "S" ou "s"
        if skip.lower() != "s":
            # Executa a varredura da instituição selecionada, passando os parâmetros da função de estado para a de instituição
            # e recebe a informação de erro de referência, que pode ter acontecido ao tentar coletar os dados da instituição
            _, erro_referencia = coletar_aprovados_instituicao(confirmar_dados=confirmar_dados, abrir_driver=False, driver=driver)

            # Se houve erro de referência, adiciona na lista de erros para posterior tratamento
            # Troca as múltiplas linhas por - para melhorar a legibilidade do log.
            if erro_referencia:
                instituicoes_erros_referencia.append(instituicao.text.replace("\n", " - "))

        # Se pulou, é colocado no log e passa para o próximo
        else:
            logging.info("Pulou estado {}".format(estado_text))

    # Se opção de notificar estiver ativa, notifica ao final da execução de varredura do estado
    # que a varredura deste foi concluída, se possui erros e, se possui, quantos são.
    if notificar:
        if len(instituicoes_erros_referencia) > 0:
            notify("Estado concluído (com erros)", "Retirada de dados do Estado {} concluído com {} erros de referência. Verifique arquivos gerados.".format(estado_text, len(instituicoes_erros_referencia)))
        else:
            notify("Estado concluído", "Retirada de dados do Estado {} concluído sem erros de referência.".format(estado_text))

    # Após a varredura de todas as instituições do estado, verifica se houveram erros na execução
    # Se houve algum erro, todos os estados com erro são referenciados no log, seguido por cada instituição que deu erro de cada estado
    if len(instituicoes_erros_referencia) > 0:
        logging.warning("------ {} erros de referência ao coletar as instituições. Instituições afetadas:".format(len(instituicoes_erros_referencia)))
        for erro_referencia in instituicoes_erros_referencia:
            logging.warning(">>> {}".format(erro_referencia))

    # Se não houve nenhum erro, é colocado no log essa informação
    else:
        logging.info("------ {} erros de referência ao coletar as instituições.".format(len(instituicoes_erros_referencia)))

    # Os erros das instituições do estado são colocadas em um dicionário para ser avaliado posteriormente,
    # caso a função de coletar_aprovados_estado() tenha sido executada a partir da coletar_aprovados_ano()
    estado_erros_referencia = {estado_text: instituicoes_erros_referencia}

    # Por fim, retorna o driver para que possa ser finalizado na rotina principal de execução do programa
    # e o dicionário com os erros de referência do estado, sendo este último só utilizado se for chamado pela função coletar_aprovados_ano()
    return driver, estado_erros_referencia


def coletar_aprovados_ano(confirmar_dados=True, notificar=False, enable_skipping=False, enable_skipping_instituicoes=False):
    ''' >> I/O:
            opt(bool), opt(bool), opt(bool), opt(bool) -> driver

        >> Parâmetros:
        - confirmar_dados (optional): Se ativado, a cada instituição a ser varrida, pergunta ao usuário se o ano, estado e instituição
            analisados estão corretos e, se não, deixa o usuário modificá-los. Ativado pela opção debug da função main.

        - notificar (optional): Se ativado, lança uma notificação ao final da varredura de cada estado (apenas para MacOS).
            Ativado pela opção notificar da função main.

        - enable_skipping (optional): Se ativado, a cada estado a ser varrido, pergunta ao usuário se deseja pulá-lo.
            Ativado pela opção skip da função main.

        - enable_skipping_instituicoes (optional): Se ativado, a cada instituição a ser varrida, pergunta ao usuário se deseja pulá-la.
            Ativado pela opção skip_all da função main.

        >> Retorno:
        - driver: retorna driver do navegador rodando no momento.

        >> Descrição:
            Coleta todos os aprovados de um determinado ano, de todos os estados e instituições presentes
        e salva cada instituição em uma pasta diferente, de forma a facilitar a conferência posterior da integridade dos dados.
            Não coleta aprovados diretamente, mas sim chamando a função de coletar_aprovados_estado().
            Retorna o driver para que possa ser encerrado na execução principal.
    '''

    all_erros_referencia = {}

    # Driver Setup
    my_url = "https://site.medgrupo.com.br/#/aprovacoes"

    # Define window size for certain class selectors appear, thanks to the page's JS
    options = Options()
    # options.add_argument("window-size=800,700")
    driver_path = os.path.join(os.getcwd(), 'chromedriver')

    driver = webdriver.Chrome(options=options, executable_path=driver_path)
    driver.get(my_url)
    logging.info("Navegador aberto e site carregado.")
    # /Driver Setup

    # Pausa a execução e aguarda a seleção do ano no navegador, até que se dê enter
    logging.info("Aguardando seleção do ano.")
    input("Selecione no navegador o ano desejado. Pressione enter para continuar...")
    logging.info("Ano selecionado.")

    # Retira o ano da página do site
    ano_text = driver.find_element_by_xpath("//ul[@class='aprovacoes__selecao-ano']/li[@class='pointer active']").text
    logging.info("ano_text = %s" % (ano_text))

    # Se confirmar_dados estiver ativo... bom... então se ativa a confirmação de dados...
    logging.debug("confirmar_dados = {}".format(confirmar_dados))
    if confirmar_dados:
        logging.info("Confirmando dados.")

        print("\nO ano selecionado está correto?")
        print("Ano: %s" % (ano_text))
        print("S/N? ", end="")
        modificar = input("")

        # Default é não modificar; modifica apenas se explicitamente digitar "N" ou "n" (dados não corretos)
        if modificar.lower() == "n":
            logging.info("Usuário pede para modificar ano e/ou estado.")

            print("")
            ano_text = input("Digite o ano: ")

            logging.info("Novo ano_text = %s" % (ano_text))

    print("")

    # Lista com todos os estados para serem percorridos no for a seguir
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

    # Faz a varredura de todos os estados da lista
    for estado_text in all_estados_text:
        # Pausa a execução e aguarda a seleção do ano no navegador, até que se dê enter
        logging.info("Próximo estado da lista: {}".format(estado_text))
        print("\n")
        input("Selecione no navegador o estado {}. Pressione enter para continuar...".format(estado_text))
        print("")

        # Retira o nome do estado da página do site e confere se é igual para fazer o log
        estado_selecionado_text = driver.find_element_by_xpath("//h2[@class='estado-instituicao__titulo disable-select']").text
        if estado_text == estado_selecionado_text:
            logging.info("Estado selecionado e estado da lista são iguais")
        else:
            logging.warning("Estado selecionado e estado da lista NÃO são iguais")

        # Imprime nome do estado que foi encontrado na página (para conferência do usuário)
        print(".Estado: %s" % (estado_selecionado_text))
        logging.info("Estado selecionado: %s" % (estado_selecionado_text))

        # Se enable_skipping estiver ativado, pergunta se deseja pular o estado
        skip = ""
        if enable_skipping:
            skip = input("Pular estado? S/N? ")
            logging.debug("skip = {}".format(skip))

        # Default é não pular; pula apenas se explicitamente digitar "S" ou "s"
        if skip.lower() != "s":
            # Executa a varredura do estado selecionado, passando os parâmetros da função de ano para a de estado
            # e recebe os erros de referência da função para ser tratado posteriormente.
            _, erros_referencia = coletar_aprovados_estado(confirmar_dados=confirmar_dados, abrir_driver=False, enable_skipping=enable_skipping_instituicoes, driver=driver)

            # Se opção de notificar estiver ativa, notifica ao final da execução de varredura de um estado
            # que a varredura foi concluída, se possui erros e, se possui, quantos são.
            if notificar:
                if len(erros_referencia[estado_text.upper()]) > 0:
                    notify("Estado concluído (com erros)", "Retirada de dados do Estado {} concluído com {} erros de referência. Verifique arquivos gerados.".format(estado_text, len(erros_referencia[estado_text.upper()])))
                else:
                    notify("Estado concluído", "Retirada de dados do Estado {} concluído sem erros de referência.".format(estado_text))

            # Se possui erros de referência, adiciona no dicionário de erros para posterior tratamento
            if len(erros_referencia) > 0:
                all_erros_referencia.update(erros_referencia)

        # Se pulou, é colocado no log e passa para o próximo
        else:
            logging.info("Pulou estado {}".format(estado_text))

    # Após a varredura de todos os estados, verifica se houveram erros na execução
    # Se houve algum erro, todos os estados com erro são referenciados no log, seguido por cada instituição que deu erro de cada estado
    if len(all_erros_referencia) > 0:
        logging.warning("------ {} erros de referência ao coletar os aprovados. Estados afetados:".format(len(all_erros_referencia)))
        for estado in all_erros_referencia:
            logging.warning("> {}".format(estado))

        logging.warning("----- Erros de referência discretos por instituição de cada estado:")
        for estado, lista_instituicoes_erro in all_erros_referencia.items():
            logging.warning("> {}: {} instituições afetas.".format(estado, len(lista_instituicoes_erro)))
            for instituicao in lista_instituicoes_erro:
                logging.warning(">>> {}".format(instituicao))

    # Se não houve nenhum erro, é colocado no log essa informação
    else:
        logging.info("------ {} erros de referência ao coletar as instituições.".format(len(instituicoes_erros_referencia)))

    # Se opção de notificar estiver ativa, notifica ao final da execução de varredura do ano
    # que a varredura foi concluída, se possui erros e, se possui, quantos são.
    if notificar:
        if len(all_erros_referencia) > 0:
            notify("Aprovados de {} concluído (com erros)", "Retirada de dados de {} Estados com erros de referência. Verifique arquivos gerados.".format(ano_text, len(all_erros_referencia)))
        else:
            notify("Aprovados de {} concluído", "Retirada de dados concluída sem erros de referência.".format(ano_text))

    # Por fim, retorna o driver para que possa ser finalizado na rotina principal de execução do programa
    return driver


def concatenador(ano):
    ''' >> I/O:
            int -> void

        >> Parâmetros:
        - ano: ano de referência para concatenação

        >> Descrição:
            Função para concatenar arquivos CSV de um determinado ano.
            Além de fazer a concatenação do ano inteiro, é feita a concatenação de cada estado.
    '''

    arquivos_csv = os.path.join(os.getcwd(), 'Arquivos_CSV')
    file_ano_name = "aprovados_medgrupo_{}.csv".format(ano)

    # Procura um nome válido para o arquivo CSV do ano
    # Se já existe algum arquivo com este nome, percorre um loop até encontrar um que não exista
    if file_exists(os.path.join(arquivos_csv, file_ano_name)):
        i = 1
        while file_exists(os.path.join(arquivos_csv, "aprovados_medgrupo_{}_({}).csv".format(ano, i))):
            i += 1
        file_ano_name = "aprovados_medgrupo_{}_({}).csv".format(ano, i)

    # Cria arquivo CSV do ano e já escreve os cabeçalhos na primeira linha
    with open(os.path.join(arquivos_csv, file_ano_name), "w+") as f_concat_ano:
        f_concat_ano.write("Estado;Instituição;Hospital;Curso;Colocação;Nome_Aprovado\n")

        # Lista todos os estados
        for estado in os.listdir(arquivos_csv):

            # Verifica se o estado listado realmente é uma pasta (se não for próximos passos iriam dar erros)
            if os.path.isdir(os.path.join(arquivos_csv, estado)):
                logging.info("Concatenando estado {}".format(estado))
                estado_path = os.path.join(arquivos_csv, estado)
                file_estado_name = "aprovados_medgrupo_{}_{}.csv".format(ano, estado)

                # Procura um nome válido para o arquivo CSV do estado
                # Se já existe algum arquivo com este nome, percorre um loop até encontrar um que não exista
                if file_exists(os.path.join(estado_path, file_estado_name)):
                    i = 1
                    while file_exists(os.path.join(estado_path, "aprovados_medgrupo_{}_{}_({}).csv".format(ano, estado, i))):
                        i += 1
                    file_estado_name = "aprovados_medgrupo_{}_{}_({}).csv".format(ano, estado, i)

                # Cria arquivo CSV do estado e já escreve os cabeçalhos na primeira linha
                with open(os.path.join(estado_path, file_estado_name), "w+") as f_concat_estado:
                    f_concat_estado.write("Estado;Instituição;Hospital;Curso;Colocação;Nome_Aprovado\n")

                    # Caminha por todos os diretórios e arquivos dentro da pasta do estado
                    for root, dirs, files in os.walk(estado_path):

                        # Ignora pasta inicial para evitar referências cíclicas (abrir o arquivo de estado que já está aberto, por exemplo)
                        if file_estado_name not in files:

                            # Coloca todos os arquivos da pasta que possui o ano no nome
                            # Exemplo:
                            # aprovados_medgrupo_2018_São Paulo_USP.csv
                            # aprovados_medgrupo_2018_São Paulo_USP_(1).csv
                            possible_files = []
                            for file in files:
                                if str(ano) in file:
                                    possible_files.append(file)
                                    logging.debug("Arquivo possível: {}".format(file))

                            # Se não possuir nenhum arquivo do ano correspondente, pula para o próximo
                            if len(possible_files) > 0:

                                # Dentre os arquivos possíveis, pega o que possui número maior
                                # Exemplo:
                                # aprovados_medgrupo_2018_São Paulo_USP.csv
                                # aprovados_medgrupo_2018_São Paulo_USP_(1).csv
                                # aprovados_medgrupo_2018_São Paulo_USP_(2).csv  <--- selecionado
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

                                    # Assert evita que haja um erro posteriormente ao tentar abrir arquivo vazio
                                    assert file != ""

                                # Tratamento de erros de 2 formas possíveis:
                                # 1. AssertionError: arquivo retornou como vazio
                                # 2. Outros (provavelmente se conversão do int falhou)
                                except AssertionError as ae:
                                    logging.critical("Arquivo do estado {} e ano {} retornou vazio".format(estado, ano))
                                    raise ae
                                except Exception as e:
                                    logging.exception("Erro ao concatenar arquivos.")
                                    raise e

                                # Se o file passou do assert (ou seja, não é vazio), abre o arquivo e copia tanto para o arquivo do respectivo estado quanto do ano
                                else:
                                    logging.info("Arquivo selecionado: {}".format(file))
                                    with open(os.path.join(root, file), "r") as f_instituicao:
                                        f_instituicao.readline()  # ignorar primeira linha
                                        for linha in f_instituicao:
                                            f_concat_estado.write(linha)
                                            f_concat_ano.write(linha)


def main():
    ''' >> I/O:
            void -> void

        >> Descrição:
            Função main une as funções em um único fluxo e seta as opções necessárias
        para cada tipo de execução.
    '''

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

    # Se houver algum argumento passado na execução do programa, é feita a verificação aqui
    if len(sys.argv) > 1:

        # Valores default
        selected = False
        locked = False

        # Verificação dos comandos ativados
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

                # Se algum dos comandos de coleta for selecionada, ativa essa variável que
                # travará a execução do programa se houver mais de uma opção ativada
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

    # Se não for passado nenhum argumento, se ativarão as opções no terminal
    else:
        # Modo de operação
        print("Selecione o modo de operação:\n")
        print("1. Coletar aprovados de um ano.")
        print("2. Coletar aprovados de um estado.")
        print("3. Coletar aprovados de uma instituição.")
        print("4. Apenas concatenar arquivos de um ano.")
        print("x. Abortar\n")
        opcao = input("Digite a opção: ")
        logging.debug("opcao = %s" % (opcao))
        # /Modo de operação

        # Ativa opção de somente concatenar e pula as outras perguntas
        if opcao == '4':
            somente_concatenar = True
            logging.info("Somente concatenar.")
            print("\nOpção de somente concatenar selecionada.")

        # Se for uma das outras opções, continua questionário
        elif opcao == '1' or opcao == '2' or opcao == '3':
            # Modo de debug/Confirmação de Dados
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
            # /Modo de debug/Confirmação de Dados

            # Notificação (apenas MacOS)
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
            # /Notificação (apenas MacOS)

            # Opção de pular estado/instituição
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
            # /Opção de pular estado/instituição

            # Opção de concatenar arquivos
            print("\nConcatenar arquivos?\n")
            print("1. Sim")
            print("2. Não\n")
            concat_option = input("Digite a opção: ")
            logging.debug("concat_option = %s" % (concat_option))

            if concat_option == '2':
                concatenar = False
                logging.info("Não concatenar ao final da varredura.")
            else:
                concatenar = True
                logging.info("Concatenar ao final da varredura.")
            # /Opção de concatenar arquivos

        # Se nenhuma das opções válidas for selecionada, aborta a execução do programa.
        else:
            logging.info("Nenhuma opção válida selecionada. Abortando operação...")
            logging.info("Fim da execução. <<<<<<<<<<<<<<<<<<<<<\n\n\n\n\n\n")
            print("\nNenhuma opção válida selecionada.")
            print("Abortando...")
            sys.exit()

    # Rotina principal do programa. Se a opção somente_concatenar for selecionada, pula essa parte.
    if not somente_concatenar:
        #Opção 1 leva à coleta de aprovados de um ano inteiro (ano, estados e instituições)
        if opcao == '1':
            logging.info("Selecionado: coletar_aprovados_ano()")
            driver = coletar_aprovados_ano(confirmar_dados=DEBUG, notificar=notificar, enable_skipping=skip, enable_skipping_instituicoes=skip_all)

        #Opção 2 leva à coleta de aprovados de um estado inteiro, de um determinado ano (estado e instituições)
        elif opcao == '2':
            logging.info("Selecionado: coletar_aprovados_estado()")
            driver, _ = coletar_aprovados_estado(confirmar_dados=DEBUG, notificar=notificar, enable_skipping=skip)

        #Opção 3 leva à coleta de aprovados de uma instituição
        elif opcao == '3':
            logging.info("Selecionado: coletar_aprovados_instituicao()")

            # Modo coleta da instituição
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
            # /Modo coleta da instituição

            driver, _ = coletar_aprovados_instituicao(confirmar_dados=DEBUG, notificar=notificar, coletar_todos_aprovados=opcao_coleta)

        # Nunca deveria chegar aqui por conta do teste anterior, mas... better safe than sorry
        else:
            logging.info("Nenhuma opção válida selecionada. Abortando operação...")
            logging.info("Fim da execução. <<<<<<<<<<<<<<<<<<<<<\n\n\n\n\n\n")
            print("Nenhuma opção válida selecionada.")
            print("Abortando...")
            sys.exit()

        driver.quit()

    # Se opção de concatenar (ou somente_concatenar) for ativada, ativa a função de concatenação
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
    # Checando se algum dos comandos for de help
    # https://stackoverflow.com/questions/740287/how-to-check-if-one-of-the-following-items-is-in-a-list
    if [x for x in sys.argv if x.lower() in ["-h", "--help"]]:
        help()
        logging.info("Função help() acionada.")
    else:
        main()
