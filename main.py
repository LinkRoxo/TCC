import sys
import subprocess
import pkg_resources
import pytesseract
import regex as re
import cv2
import os
import pandas as pd

#init
path = ''

def list_files_in_directory(folder_path):
  old_parts = ["primeiroValor","primeiroValor","primeiroValor","primeiroValor"]
  files_array = []
  document_array = []
  for root, dirs, files in os.walk(folder_path):
    for file in files:
        
      file_path = os.path.join(root, file)
      
      parts = file.split('-')
      print(parts)
    
      if parts[0] == old_parts[0] and parts[1] == old_parts[1] and parts[2] == old_parts[2] and parts[3] == old_parts[3]:
        document_array.append(file_path)
      else:
        if old_parts[0] != "primeiroValor":
          files_array.append(document_array)
          document_array = []
        document_array.append(file_path)

      old_parts = parts

  # print(files_array)
  return files_array

def descobre_prestadora(documento):
  if re.findall('^[Cc][Ll][Aa][Rr][Oo]', documento,  re.MULTILINE):
        prestadora = 'Claro'
  elif re.findall('^[Tt][Ii][Mm]', documento,  re.MULTILINE):
        prestadora = 'Tim'
  elif re.findall('^[Vv][Ii][Vv][Oo]', documento, re.MULTILINE):
        prestadora = 'Vivo'
  else:
        prestadora = None

  return prestadora

def extrair_info(documento, prestadora):
  tipo_conta = None
  n_conta = None
  mes_referencia = None
  vencimento = None
  emisao = None
  cpf = None
  periodo = None
  valor_vencimento = None
  valor_vencimento1 = None
  valor_vencimento2 = None
  valor_vencimento3 = None
  

  
  if prestadora == 'Vivo':
    #PIPELINE VIVO
    tipo_conta = 'Telefonia'

    n_conta = re.findall(r'Conta: (\d{14})', documento, re.MULTILINE)
    if len(n_conta) == 0:
      n_conta = re.findall(r'Número da fatura: (\d{10}-\d)', documento, re.MULTILINE)
      if len(n_conta) == 0:
        n_conta = re.findall(r'Conta: (\d{10})', documento, re.MULTILINE)
    if len(n_conta) > 0:
      n_conta = n_conta[0]
    
    mes_referencia = re.findall(r'[Rr][Ee][Ff][Ee][Rr][Êê|Ee][Nn][Cc][Ii][Aa][\:\s|\s].*?(0[1-9]|1[0-2])\/(19|20)\d{2}', documento, re.MULTILINE)
    if len(mes_referencia) > 0:
      mes_referencia = mes_referencia[0][0]

    vencimento = re.findall(r'Vencimento.*\n.*[\:\s|\s].*?((0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0,1,2])\/(19|20)\d{2})', documento, re.MULTILINE)
    if len(vencimento) > 0:
      vencimento = str(vencimento[0][1] + "/" + vencimento[0][2] + "/" + vencimento[0][3])

    emisao = re.findall(r'[Dd][Aa][Tt][Aa] [Dd][Ee] [Ee][Mm][Ii][Ss][Ss][Ãã][oO]: ((0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/(19|20)\d{2})', documento, re.MULTILINE)
    if len(emisao) > 0:
      emisao = emisao[0][0]

    cpf = encontra_cpf_cnpj(documento)

    periodo = re.findall(r'Período:((0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0,1,2])\/(19|20)\d{2}) a ((0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0,1,2])\/(19|20)\d{2})', documento, re.MULTILINE)
    if len(periodo) == 0:
      periodo = re.findall(r'Data \/ Período .*\n.*[\:\s|\s].*?((0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0,1,2])\/(19|20)\d{2}) a ((0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0,1,2])\/(19|20)\d{2})', documento, re.MULTILINE)
    if len(periodo) > 0: 
      periodo = str("de " + periodo[0][0] + " a " + periodo[0][4])

    valor_vencimento = re.findall(r'VALOR A PAGAR \(R\$\)\n*.*(\d{2,5}\,\d{2})', documento, re.MULTILINE)

  elif prestadora == 'Claro':


    regex_n_conta = r'(\b\d{9}\b)'

    # Regex para encontrar a data de vencimento
    regex_data_vencimento = r'\b(\d{2}/\d{2}/\d{4})\b'

    # Regex para encontrar a data de início
    regex_data_inicio = r'\b(\d{2}/\d{2}/\d{4})\b'

    # Regex para encontrar o valor total
    regex_valor_total1 = r'\b(\d+,\d{2})\b'
    regex_valor_total2 = r'TOTAL A PAGAR R\$ (\d{1,3}(?:,\d{3})*(?:\,\d{2})?)'
    regex_valor_total3 = r'Plano Contratado R\$ (\d{1,3}(?:,\d{3})*(?:\,\d{2})?)'

    #PIPELINE CLARO

    tipo_conta = 'Telefonia'



    pre_n_conta = re.findall(regex_n_conta, documento, re.MULTILINE)

    pre_mes_referencia = re.findall(regex_data_vencimento, documento, re.MULTILINE)

    vencimento =  re.findall(r'[Vv][Ee][Nn][Cc][Ii][Mm][Ee][Nn][Tt][Oo]\s(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0,1,2])/(19|20)\d{2}', documento, re.MULTILINE)

    emisao = re.findall(regex_data_inicio, documento, re.MULTILINE)

    cpf =  re.findall(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b', documento, re.MULTILINE)

    periodo = None
    
    # Numero conta
    for numero_conta in pre_n_conta:
       n_conta = numero_conta
    
    # Mes Referencia
    mes_referencia1 = re.findall(r'[Mm][EeÊê][Ss]/[Aa][Nn][Oo]\n\d*? ((0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0,1,2])/(19|20)\d{2}) ((0[1-9]|1[0-2])/(19|20)\d{2})', documento, re.MULTILINE)
    mes_referencia2 = re.findall(r'[Mm][EeÊê][Ss] [Rr][Ee][Ff][Ee][Rr][EeÊê][Nn][Cc][Ii][Aa]\n\n(\w+/\d{4})', documento, re.MULTILINE)
    print(mes_referencia1)
    print(mes_referencia2)

    if mes_referencia2:
       mes_referencia = mes_referencia2
    if mes_referencia1:
      mes_referencia = mes_referencia1[0][4]
    
    # Valor vencimento
    valor_vencimento1 = re.findall(regex_valor_total1, documento, re.MULTILINE)
    valor_vencimento2 = re.findall(regex_valor_total2, documento, re.MULTILINE)
    valor_vencimento3 = re.findall(regex_valor_total3, documento, re.MULTILINE)

    vencimento_numerico1 = [float(elemento.replace(',', '.')) for elemento in valor_vencimento1]
    if vencimento_numerico1:
      valor_vencimento1 = max(vencimento_numerico1)

    vencimento_numerico2 = [float(elemento.replace(',', '.')) for elemento in valor_vencimento2]
    if vencimento_numerico2:
      valor_vencimento2 = max(vencimento_numerico2)

    vencimento_numerico3 = [float(elemento.replace(',', '.')) for elemento in valor_vencimento3]
    if vencimento_numerico3:
      valor_vencimento3 = max(vencimento_numerico3)
    

  elif prestadora == 'Tim':
    n_conta = re.findall(r'FATURA: (\d{10})', documento, re.MULTILINE)

    mes_referencia = re.findall(r'(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)/(19|20)\d{2}', documento, re.MULTILINE)

    vencimento =  re.findall(r'VENCIMENTO\n((0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/(19|20)\d{2})', documento, re.MULTILINE)

    emisao = re.findall(r'EMISSÃO: ((0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/(19|20)\d{2})', documento, re.MULTILINE)

    cpf = encontra_cpf_cnpj(documento)

    periodo = re.findall(r'PERÍODO: ((0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/(19|20)\d{2}) A ((0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/(19|20)\d{2})', documento, re.MULTILINE)


  nome_conta = re.findall(r'\w+-\d{2}-\d{4}-\w+\.pdf', documento, re.MULTILINE)
  print(str(nome_conta[0]))
  print(prestadora)
  print(tipo_conta)
  print(n_conta)
  print(mes_referencia)
  print(vencimento)
  print(emisao)

  print(periodo)
  print(valor_vencimento)


  retorno = {
    "nome_conta": nome_conta[0],
    "prestadora": prestadora,
    "tipo_conta": tipo_conta,
    "n_conta": n_conta,
    "mes_referencia": mes_referencia,
    "vencimento": vencimento,
    "emisao": emisao,
    "cpf": cpf,
    "periodo": periodo,
    "valor_vencimento": valor_vencimento
  }
  return retorno

def encontra_cpf_cnpj(documento):
  tipo = 'CNPJ'
  dado = re.findall(r"[Cc][Pp][Ff]\/[Cc][Nn][Pp][Jj].*?:.*?(?=\d)(.*?(?=\d)([0-9]{3}\.?[0-9]{3}\.?[0-9]{3}\-?[0-9]{2}))", documento, re.MULTILINE)
  return dado #dado[0][0]

def main(arg):
  pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

  path = arg
  paths = list_files_in_directory(path)
  documento = ''
  array_documento = []
  all_data = []
  infos = []

  for x in paths:
    teste = x[0].split('-')
    nome_arquivo = teste[0] + '-' + teste[1] + '-' + teste[2] + '-' + teste[3] + '.pdf' + ' '
    documento = str(nome_arquivo)
    for i, pdfs in enumerate(x):
      img = cv2.imread(x[i])
      convertido = pytesseract.image_to_string(img, lang = 'por', config='--psm 3')
      documento += convertido
      print(documento)
    array_documento.append(documento)

  for documento in array_documento:
    prestadora = descobre_prestadora(documento)
    print('+++++++++++++++++++++++++++++++++++++++')
    print('+++++++++++++++++++++++++++++++++++++++')
    info = extrair_info(documento, prestadora)
    infos.append(info)

  print(infos)
  
  input("Digite qualquer coisa para continuar.............")
  
  all_data.append(infos)
  df = pd.DataFrame(columns=["prestadora", "tipo_conta", "n_conta", "mes_referencia", "vencimento", "emisao", "cpf", "periodo", "valor_vencimento"])
  for i in range(0, len(all_data)):
    dado = all_data[i]
    df.loc[i] = [all_data[i]["prestadora"],all_data[i]["tipo_conta"],all_data[i]["n_conta"],all_data[i]["mes_referencia"],all_data[i]["vencimento"],all_data[i]["emisao"],all_data[i]["cpf"],[all_data[i]["periodo"],[all_data[i]["valor_vencimento"]]]]

  excel_file = "dados_contas.xlsx"


  df.to_excel(excel_file, index=False, engine='openpyxl')

  print(f'Dados foram salvos em {excel_file}')

  all_data



required = {'pytesseract', 'regex', 'opencv-python', 'pandas'}
installed = {pkg.key for pkg in pkg_resources.working_set}
missing = required - installed

if missing:
    python = sys.executable
    subprocess.check_call([python, '-m', 'pip', 'install', *missing], stdout=subprocess.DEVNULL)

if __name__ == "__main__":
  path = str(input('Insira o caminho da pasta com os as contas convertidas: '))
  array_documento = main(path)
  


  









