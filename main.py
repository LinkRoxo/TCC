import sys
import subprocess
import pytesseract
import regex as re
import cv2
import os
import pandas as pd
from pandas import json_normalize
from alive_progress import alive_it

#init
path = ''

#VIVO REGEX
vivo_n_conta1 = re.compile(r'Conta: (\d{14})', re.MULTILINE)
vivo_n_conta2 = re.compile(r'Número da fatura: (\d{10}-\d)', re.MULTILINE)
vivo_n_conta3 = re.compile(r'Conta: (\d{10})', re.MULTILINE)
vivo_mes_referencia = re.compile(r'[Rr][Ee][Ff][Ee][Rr][Êê|Ee][Nn][Cc][Ii][Aa][\:\s|\s].*?(0[1-9]|1[0-2])\/(19|20)\d{2}', re.MULTILINE)
vivo_vencimento = re.compile(r'Vencimento.*\n.*[\:\s|\s].*?((0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0,1,2])\/(19|20)\d{2})', re.MULTILINE)
vivo_emisao = re.compile(r'[Dd][Aa][Tt][Aa] [Dd][Ee] [Ee][Mm][Ii][Ss][Ss][Ãã][oO]: ((0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/(19|20)\d{2})', re.MULTILINE)
vivo_periodo1 = re.compile(r'Período:((0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0,1,2])\/(19|20)\d{2}) a ((0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0,1,2])\/(19|20)\d{2})', re.MULTILINE)
vivo_periodo2 =  re.compile(r'Data \/ Período .*\n.*[\:\s|\s].*?((0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0,1,2])\/(19|20)\d{2}) a ((0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0,1,2])\/(19|20)\d{2})', re.MULTILINE)
vivo_valor_vencimento = re.compile(r'VALOR A PAGAR \(R\$\)\n*.*(\d{2,5}\,\d{2})', re.MULTILINE)

#CLARO REGEX
claro_n_conta = re.compile(r'(\b\d{9}\b)', re.MULTILINE)
claro_mes_referencia1 = re.compile(r'[Mm][EeÊê][Ss]/[Aa][Nn][Oo]\n\d*? ((0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0,1,2])/(19|20)\d{2}) ((0[1-9]|1[0-2])/(19|20)\d{2})', re.MULTILINE)
claro_mes_referencia2 = re.compile(r'[Mm][EeÊê][Ss] [Rr][Ee][Ff][Ee][Rr][EeÊê][Nn][Cc][Ii][Aa]\n\n(\w+/\d{4})', re.MULTILINE)
claro_vencimento = re.compile(r'Vencimento\n.*((0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0,1,2])\/(19|20)\d{2})', re.MULTILINE)
claro_emisao = re.compile(r'Data de emissão: ((0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0,1,2])\/(19|20)\d{2})', re.MULTILINE)
claro_periodo1 = re.compile(r'Período.*\n.*((0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0,1,2])\/(19|20)\d{2}) a ((0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0,1,2])\/(19|20)\d{2})', re.MULTILINE)
claro_periodo2 = re.compile(r'Período.*\nde.*((0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0,1,2])\/(19|20)\d{2})a ((0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0,1,2])\/(19|20)\d{2})', re.MULTILINE)
claro_periodo3 = re.compile(r'Período.*\n.*((0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0,1,2])\/(19|20)\d{2})a ((0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0,1,2])\/(19|20)\d{2})', re.MULTILINE)
claro_valor_vencimento1 = re.compile(r'\b(\d+,\d{2})\b', re.MULTILINE)
claro_valor_vencimento2 = re.compile(r'TOTAL A PAGAR R\$ (\d{1,3}(?:,\d{3})*(?:\,\d{2})?)', re.MULTILINE)
claro_valor_vencimento3 = re.compile(r'Plano Contratado R\$ (\d{1,3}(?:,\d{3})*(?:\,\d{2})?)')


def list_files_in_directory(folder_path):
  old_parts = ["primeiroValor","primeiroValor","primeiroValor","primeiroValor"]
  files_array = []
  document_array = []
  for root, dirs, files in os.walk(folder_path):
    for file in files:
        
      file_path = os.path.join(root, file)
      
      print(file)
      parts = file.split('-')
    
      if parts[0] == old_parts[0] and parts[1] == old_parts[1] and parts[2] == old_parts[2] and parts[3] == old_parts[3]:
        document_array.append(file_path)
      else:
        if old_parts[0] != "primeiroValor":
          files_array.append(document_array)
          document_array = []
        document_array.append(file_path)

      old_parts = parts

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

    n_conta = re.findall(vivo_n_conta1, documento)
    if len(n_conta) == 0:
      n_conta = re.findall(vivo_n_conta2, documento)
      if len(n_conta) == 0:
        n_conta = re.findall(vivo_n_conta3, documento)
    if len(n_conta) > 0:
      n_conta = n_conta[0]
    
    mes_referencia = re.findall(vivo_mes_referencia, documento)
    if len(mes_referencia) > 0:
      mes_referencia = mes_referencia[0][0]

    vencimento = re.findall(vivo_vencimento, documento)
    if len(vencimento) > 0:
      vencimento = str(vencimento[0][1] + "/" + vencimento[0][2] + "/" + vencimento[0][3])

    emisao = re.findall(vivo_emisao, documento)
    if len(emisao) > 0:
      emisao = emisao[0][0]

    cpf = encontra_cpf_cnpj(documento)

    periodo = re.findall(vivo_periodo1, documento)
    if len(periodo) == 0:
      periodo = re.findall(vivo_periodo2, documento)
    if len(periodo) > 0: 
      periodo = str("de " + periodo[0][0] + " a " + periodo[0][4])

    valor_vencimento = re.findall(vivo_valor_vencimento, documento)
    if len(valor_vencimento) > 0:
      valor_vencimento = valor_vencimento[0]
  
  elif prestadora == 'Claro':
    tipo_conta = 'Telefonia'
    
    pre_n_conta = re.findall(claro_n_conta, documento)
    
    vencimento =  re.findall(claro_vencimento, documento)
    if len(vencimento) != 0:
      vencimento = vencimento[0][0]

    emisao = re.findall(claro_emisao, documento)
    if len(emisao) != 0:
      emisao = emisao[0][0]

    cpf =  re.findall(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b', documento)

    periodo = re.findall(claro_periodo1, documento)
    if len(periodo) == 0:
      periodo = re.findall(claro_periodo2, documento)
      if len(periodo) == 0:
        periodo = re.findall(claro_periodo3, documento)
    if len(periodo) != 0:
      periodo = periodo = str("de " + periodo[0][0] + " a " + periodo[0][4])
    
    # Numero conta
    for numero_conta in pre_n_conta:
       n_conta = numero_conta
    
    # Mes Referencia
    mes_referencia1 = re.findall(claro_mes_referencia1, documento)
    mes_referencia2 = re.findall(claro_mes_referencia2, documento)


    if mes_referencia2:
      mes_referencia = mes_referencia2
    if mes_referencia1:
      mes_referencia = mes_referencia1[0][4]
    
    # Valor vencimento
    valor_vencimento1 = re.findall(claro_valor_vencimento1, documento)
    valor_vencimento2 = re.findall(claro_valor_vencimento2, documento)
    valor_vencimento3 = re.findall(claro_valor_vencimento3, documento)

    vencimento_numerico1 = [float(elemento.replace(',', '.')) for elemento in valor_vencimento1]
    if vencimento_numerico1:
      valor_vencimento1 = max(vencimento_numerico1)

    vencimento_numerico2 = [float(elemento.replace(',', '.')) for elemento in valor_vencimento2]
    if vencimento_numerico2:
      valor_vencimento2 = max(vencimento_numerico2)

    vencimento_numerico3 = [float(elemento.replace(',', '.')) for elemento in valor_vencimento3]
    if vencimento_numerico3:
      valor_vencimento3 = max(vencimento_numerico3)


    if not valor_vencimento2:    
      if not valor_vencimento1:
        valor_vencimento = valor_vencimento3
      else:
        valor_vencimento = valor_vencimento1
    else:
       valor_vencimento = valor_vencimento2 
    

  elif prestadora == 'Tim':
    tipo_conta = 'Telefonia'
    n_conta = re.findall(r'FATURA: (\d{10})', documento, re.MULTILINE)
    if len(n_conta) != 0:
      n_conta = n_conta[0]

    mes_referencia = re.findall(r'(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)/(19|20)\d{2}', documento, re.MULTILINE)
    if len(mes_referencia) != 0:
      mes_referencia = mes_referencia[0][0]

    vencimento =  re.findall(r'VENCIMENTO\n((0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/(19|20)\d{2})', documento, re.MULTILINE)
    if len(vencimento) != 0:
      vencimento = vencimento[0][0]

    emisao = re.findall(r'EMISSÃO: ((0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/(19|20)\d{2})', documento, re.MULTILINE)
    if len(emisao) != 0:
      emisao = emisao[0][0]

    cpf = encontra_cpf_cnpj(documento)

    periodo = re.findall(r'PERÍODO: ((0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/(19|20)\d{2}) A ((0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/(19|20)\d{2})', documento, re.MULTILINE)
    if len(periodo) != 0:
      periodo = periodo = str("de " + periodo[0][0] + " a " + periodo[0][4])

    #valor_vencimento = None

  nome_conta = re.findall(r'\w+-\d{2}-\d{4}-\w+\.pdf', documento, re.MULTILINE)

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
  if len(dado) != 0:
    dado = dado[0][0]
  return dado

def main(arg):
  if os.name == 'nt': #WIN
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
  if os.name == 'posix': #UNIX LIKE
    pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

  path = arg
  paths = list_files_in_directory(path)
  documento = ''
  array_documento = []
  all_data = []
  infos = []

  for x in alive_it(paths, refresh_secs=0.1):
    teste = x[0].split('-')
    nome_arquivo = teste[0] + '-' + teste[1] + '-' + teste[2] + '-' + teste[3] + '.pdf' + ' '
    documento = str(nome_arquivo)
    for i, pdfs in enumerate(x):
      img = cv2.imread(x[i])
      convertido = pytesseract.image_to_string(img, lang = 'por', config='--psm 3')
      documento += convertido
      #print(documento)
    array_documento.append(documento)

  for documento in array_documento:
    prestadora = descobre_prestadora(documento)
    #print('+++++++++++++++++++++++++++++++++++++++')
    #print('+++++++++++++++++++++++++++++++++++++++')
    info = extrair_info(documento, prestadora)
    infos.append(info)

  nome_excel = input("Digite o nome do arquivo excel:")
  nome_excel+= '.xlsx'
  
  # Salvar o DataFrame em um arquivo Excel
  df = json_normalize(infos)
  df.to_excel(nome_excel, index=False)
  
  #FINALIZAÇÃO DA EXECUÇÃO
  print("Extração concluida!, o arquivo : " + str(nome_excel) + " encontra-se na mesma pasta que esse programa.")
  input("Digite qualquer coisa para continuar.............")


if __name__ == "__main__":
  path = str(input('Insira o caminho da pasta com os as contas convertidas: '))
  try:
    array_documento = main(path)
  except Exception as error:
    print(error)
    input()

  


  









