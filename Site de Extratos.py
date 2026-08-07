#-----------------------------------------------------------------------------
# Libraries:
#----------------------------------------------------------------------------- 
import streamlit as st
import pypdf
from io import BytesIO
import re
import pdfplumber
import pandas as pd
import numpy as np
import hashlib

#-----------------------------------------------------------------------------
# Function to Unite PDFs:
#-----------------------------------------------------------------------------
def unite_pdfs(uploaded_files):
    if not uploaded_files:
        return None
    
    writer = pypdf.PdfWriter()
    
    sorted_files = sorted(uploaded_files, key=lambda x: x.name)
    
    for file in sorted_files:
        writer.append(file)
        
    output_pdf = BytesIO()
    writer.write(output_pdf)
    output_pdf.seek(0)
    
    return output_pdf

#-----------------------------------------------------------------------------
# Function of the Website Interface to Unite PDFs:
#-----------------------------------------------------------------------------
def interface_unite_pdfs():
    uploaded_files = st.file_uploader(
        "Selecione ou arraste os arquivos PDF que deseja unificar", 
        type="pdf", 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.success(f"{len(uploaded_files)} arquivos carregados com sucesso!")
        
        nome_arquivo = st.text_input("Digite o nome para o arquivo final:", value="pdf_unificado")
        
        if not nome_arquivo.endswith('.pdf'):
            nome_arquivo += '.pdf'
            
        with st.spinner("Processando..."):
            final_pdf = unite_pdfs(uploaded_files)
                
        if final_pdf:
            pdf_bytes = final_pdf.getvalue() if hasattr(final_pdf, 'getvalue') else final_pdf
            
            st.download_button(
                label="📥 Baixar PDF Unificado",
                data=pdf_bytes,
                file_name=nome_arquivo,
                mime="application/pdf"
            )
    else:
        st.info("Aguardando o upload de arquivos PDF para começar.")

#-----------------------------------------------------------------------------
# Function to Calculate Revenue:
#-----------------------------------------------------------------------------
def calculate_revenue(row):   
    row = row.sort_values("Data").reset_index(drop=True)

    row["Val_Aplicacao"] = np.where(
        row["Descrição"].str.contains("Aplicação", na=False), row["Valor"], 0
    )
    row["Val_Resgate"] = np.where(
        row["Descrição"].str.contains("Resgate", na=False), row["Valor"], 0
    )

    row["Ano_Mes"] = row["Data"].dt.to_period("M")

    totais_mes = row.groupby("Ano_Mes")[
        ["Val_Aplicacao", "Val_Resgate"]
    ].transform("sum")
    row["Val_Aplicacao_Mes"] = totais_mes["Val_Aplicacao"]
    row["Val_Resgate_Mes"] = totais_mes["Val_Resgate"]

    row["Saldo_Atual"] = np.where(
        row["Descrição"].str.contains("Saldo", na=False), row["Valor"], np.nan
    )

    row["Saldo_Anterior"] = row["Saldo_Atual"].ffill().shift(1)

    is_saldo_final = row["Descrição"] == "Saldo Final"

    row["Rendimento Mensal"] = np.where(
        is_saldo_final,
        row["Valor"]
        - row["Saldo_Anterior"]
        - row["Val_Aplicacao_Mes"]
        + row["Val_Resgate_Mes"],
        None,
    )

    cols_drop = [
        "Val_Aplicacao",
        "Val_Resgate",
        "Val_Aplicacao_Mes",
        "Val_Resgate_Mes",
        "Saldo_Atual",
        "Saldo_Anterior",
        "Ano_Mes",
    ]
    row = row.drop(columns=cols_drop)
    
    return row

#-----------------------------------------------------------------------------
# Function to Adjust Description:
#-----------------------------------------------------------------------------
def adjust_description(row):
    desc = str(row['Descrição']).strip()
    doc = str(row['Documento']).strip()
    
    if not doc and re.match(r'^\d[\d\.]+$', desc):
        row['Documento'] = desc
        row['Descrição'] = ''
        
    return row

#-----------------------------------------------------------------------------
# Function to Define Priorities:
#-----------------------------------------------------------------------------
def define_priority(row):
    hist = row['Descrição']
    
    if hist == 'Saldo Anterior':
        return 0
    if hist == 'BB CP Admin Supremo':
        return 2
    if hist == 'Saldo Final':
        return 3
    return 1

#-----------------------------------------------------------------------------
# Function to Define Priorities in Investment Fund:
#-----------------------------------------------------------------------------
def define_if_priority(row):
    hist = row['Descrição']
    
    if hist == 'Saldo Final':
        return 0
    if hist == 'Aplicação':
        return 2
    if hist == 'Saldo Anterior':
        return 3
    return 1

#-----------------------------------------------------------------------------
# Function to Normalize the columns:
#-----------------------------------------------------------------------------
def normalize_columns(extract):
    normalization_dic = {
        "BB CP Administrat Supremo": "BB CP Admin Supremo",
        "BB CP Admin Supremo": "BB CP Admin Supremo",
        "BB CP Automatico S P": "BB CP Automático SP",
        "OB  transferência voluntária": "Ordem Bancária Transferência Voluntária",
        "OB  transfvoluntaria": "Ordem Bancária Transferência Voluntária",
        "Ordem Bancária": "Ordem Bancária",
        "Ordem Bancria": "Ordem Bancária",
        "ORDEMBANCARIA": "Ordem Bancária",
        "Emissão de Ordem Bancária": "Emissão de Ordem Bancária",
        "Emissão Ordem Bancária": "Emissão de Ordem Bancária",
        "Emisso Ordem Bancria": "Emissão de Ordem Bancária",
        "Saldo anterior": "Saldo Anterior",
        "Saldo Anterior": "Saldo Anterior",
        "S A L D O": "Saldo Final",
        "SALDO": "Saldo Final",
        "Estorno de Dbito": "Estorno de Débito",
        "Estorno de Débito": "Estorno de Débito",
        "ESTORNODEBITO": "Estorno de Débito",
        "Estorno AcertoCrdito": "Estorno Acerto Crédito",
        "Resgate Poupança": "Resgate Poupança",
        "RESGATEPOUP": "Resgate Poupança",
        "TRFPOUPANCA": "Transferência Poupança",
        "IOF": "IOF",
        "Bloq JudicialBacen Jud": "Bloqueio Judicial",
        "Desbl JudicialBacen Jud": "Desbloqueio Judicial",
        "Transf Depósito Judicial": "Transferência Depósito Judicial",
        "ReajusteMonetárioBACEN": "Reajuste Monetário",
        "Saldo Anterior SSIAD": "Saldo Anterior",
        "SaldoAnterior î": "Saldo Anterior",
        "SaldoAnterior": "Saldo Anterior",
        "ResgateAutomático": "Resgate Automático",
        "TransferenciaParaConta": "Transferência Para Conta Corrente",
        "ResgatedePoupança": "Resgate de Poupança",
        "Saldo Atual": "Saldo Final",
        "SALDO ATUAL": "Saldo Final",
        "SALDO ANTERIOR": "Saldo Anterior",
        "Reajuste Monetrio BACEN": "Reajuste Monetário",
        "APLICACAO": "Aplicação",
        "": ""
    }
    
    extract['Descrição'] = (
        extract['Descrição']
        .str.replace(r'[^A-Za-zÀ-ÿ\s]', '', regex=True)
        .str.strip()
    )
    
    extract['Data'] = extract['Data'].str.replace('.', '/', regex=False)
    extract['Data'] = extract['Data'].str.replace(' ', '', regex=False)
    
    extract['Descrição'] = extract['Descrição'].map(normalization_dic).fillna(extract['Descrição'])
    
    extract['Data'] = pd.to_datetime(extract['Data'], format='%d/%m/%Y')
    
    extract['Valor'] = (
        extract['Valor']
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
    )
    extract['Valor'] = pd.to_numeric(extract['Valor'], errors='coerce')
    
    extract['Documento'] = extract['Documento'].str.replace('.', '', regex=False)
    extract['Documento'] = pd.to_numeric(extract['Documento'], errors='coerce').fillna(-1)
    extract.loc[extract['Descrição'] == 'Saldo Anterior', 'Documento'] = -2
    
    return extract

#-----------------------------------------------------------------------------
# Function to Normalize Investment Fund Extract:
#-----------------------------------------------------------------------------
def normalize_if_columns(extract):
    normalization_if_dic = {
        'SALDO ANTERIOR': 'Saldo Anterior',
        'SALDO ATUAL': 'Saldo Final',
        'Saldo Atual': 'Saldo Final'
        }
    
    extract['Descrição'] = (
        extract['Descrição']
        .str.replace(r'[^A-Za-zÀ-ÿ\s]', '', regex=True)
        .str.strip()
        )
    
    extract['Data'] = pd.to_datetime(extract['Data'], format='%d/%m/%Y')
    
    extract['Descrição'] = extract['Descrição'].map(normalization_if_dic).fillna(extract['Descrição'])
    extract['Valor'] = (
        extract['Valor']
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
    )
    
    extract['Valor'] = pd.to_numeric(extract['Valor'], errors='coerce')
    
    return extract

#-----------------------------------------------------------------------------
# Function to Create BB_CC from united pdf:
#-----------------------------------------------------------------------------
def bb_cc(output_pdf):
    pattern_one = (
        r'(\d{2}\/\d{2}\/\d{4})\s+'
        r'(?:\d{1,20}\s+)?'
        r'(?:(\d{1,20})\s+)?'
        r'([A-Za-zÀ-ÿ0-9\s\-\.\/\?]+?)\s+'
        r'(?:([\d\.]+)\s+)?'
        r'([\d\.]+[\,\.]\d{2})\s+'
        r'(D|C)'
    )

    pattern_two = (
    r'(\d{2}[./]\d{2}[./]\d{4})\s+'
    r'([A-Za-zÀ-ÿ0-9\s\-\.\/\?]+?)\s+'
    r'(?:(\d{1,20})\s+)?'
    r'(?:(\d{1,20})\s+)?'
    r'([\d\.]+[\,\.]\d{2})\s+' 
    r'(D|C)' 
    r'(?:\s+[\d\.]+[\,\.]\d{2}\s+[DC])?'
    )
    
    data = []
    
    with pdfplumber.open(output_pdf) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            lines = text.split('\n')
            inverted_lines = [line[::-1].strip() for line in lines]
            inverted_lines = inverted_lines[::-1]
            
            clean_text = ' '.join(lines)
            clean_inverted_text = ' '.join(inverted_lines)
            
            matches_one = list(re.finditer(pattern_one, clean_text))
            matches_two = list(re.finditer(pattern_two, clean_inverted_text))
            matches_three = list(re.finditer(pattern_two, clean_text))
            
            if len(matches_one) > 0:
                for match in matches_one:
                    data.append({
                        "Data": match.group(1),
                        "Codigo": match.group(2) if match.group(2) else "",
                        "Descrição": match.group(3).strip(),
                        "Documento": match.group(4) if match.group(4) else "",
                        "Valor": match.group(5),
                        "Natureza": match.group(6)
                    })
            elif len(matches_two) > 0:
                for match in matches_two:
                    data.append({
                        'Data': match.group(1),
                        'Codigo': match.group(3) if match.group(3) else "",
                        'Descrição': match.group(2).strip(),
                        'Documento': match.group(4) if match.group(4) else "",
                        'Valor': match.group(5),
                        'Natureza': match.group(6),
                    })
            else:
                for match in matches_three:
                    data.append({
                                    'Data': match.group(1),
                                    'Codigo': match.group(3) if match.group(3) else "",
                                    'Descrição': match.group(2).strip(),
                                    'Documento': match.group(4) if match.group(4) else "",
                                    'Valor': match.group(5),
                                    'Natureza': match.group(6),
                                })
                        
    checking_account = pd.DataFrame(data)
    checking_account = checking_account.apply(adjust_description, axis=1)
    
    mask_code = checking_account['Codigo'] != ''
    
    if mask_code.any():
        checking_account.loc[mask_code, 'Descrição'] = (
            checking_account.loc[mask_code, 'Descrição']
            .replace('', pd.NA)
            .groupby([checking_account.loc[mask_code, 'Data'], checking_account.loc[mask_code, 'Codigo']])
            .transform(lambda s: s.ffill().bfill())
            .fillna('')
        )
    
    checking_account = checking_account.drop(columns=['Codigo'])
    
    checking_account = normalize_columns(checking_account)
    checking_account['prioridade'] = checking_account.apply(define_priority, axis=1)
    
    checking_account = checking_account.sort_values(
        by=['Data', 'prioridade', 'Documento'], 
        ascending=[True, True, True]
    )
    
    checking_account = checking_account.drop(columns=['prioridade'])
    checking_account = checking_account.drop_duplicates()
    checking_account = checking_account.drop(columns=['Documento'])
    
    return checking_account

#-----------------------------------------------------------------------------
# Function to Create BB_CP from united pdf:
#-----------------------------------------------------------------------------
def bb_cp(output_pdf):
    pattern_one = (
        r"^(?P<data_mov>\d{2}/\d{2}/\d{4})\s+"
        r"(?:(?P<codigo>\d+)\s+)?"
        r"(?P<historico>[\w\-]+)\s+"
        r"(?:(?P<agencia>[\d\-]+)\s+)?"
        r"(?:(?P<documento>[\d\.]+)\s+)?"
        r"(?P<valor>\d{1,3}(?:\.\d{3})*,\d{2})\s*"
        r"(?P<natureza>[CD])$"
    )

    pattern_two = (
        r"^(?P<dt_mov>\d{2}/\d{2}/\d{4})\s+"
        r"(?:(?P<dt_bal>\d{2}/\d{2}/\d{4})\s+)?"
        r"(?:(?P<base>\d+/\d+)\s+)?"
        r"(?:(?P<codigo>\d+)\s+)?"
        r"(?P<historico>[\w\sÀ-ÿ\-\/]+?)\s+"
        r"(?:(?P<agencia>\d+-\d+)\s+)?"
        r"(?P<valor>\d{1,3}(?:\.\d{3})*,\d{2})\s*"
        r"(?P<tipo>[CD])$"
    )
    
    data = []
    
    with pdfplumber.open(output_pdf) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            
            if not texto:
                continue
            
            for linha in texto.split("\n"):
                linha_limpa = " ".join(linha.split()).strip()
                
                if not linha_limpa:
                    continue

                match1 = re.match(pattern_one, linha_limpa)
                if match1:
                    d = match1.groupdict()
                    data.append({
                        'Data': d['data_mov'],
                        'Descrição': d['historico'],
                        'Documento': d['documento'] or d['agencia'] or '',
                        'Valor': d['valor'],
                        'Natureza': d['natureza']
                    })
                    continue
                
                match2 = re.match(pattern_two, linha_limpa)
                if match2:
                    d = match2.groupdict()
                    data.append({
                        'Data': d['dt_mov'],
                        'Descrição': d['historico'].strip(),
                        'Documento': d['agencia'] or d['codigo'] or '',
                        'Valor': d['valor'],
                        'Natureza': d['tipo']
                    })

    saving_account = pd.DataFrame(data)
    
    
    
    return saving_account

#-----------------------------------------------------------------------------
# Function to Create BB_IF from united pdf:
#-----------------------------------------------------------------------------
def bb_if(output_pdf):
    pattern_one = (
        r'(\d{2}/\d{2}/\d{4})\s+'
        r'([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)\s+'
        r'([\d\.,]+)'
        )

    pattern_two = pattern_two = (
        r'(\d{2}/\d{2}/\d{4})\s+'
        r'([A-Za-zÀ-ÿ0-9\s\-\.\/\?]+?)\s+'
        r'([\d\.,]+)'  
    )


    data = []

    with pdfplumber.open(output_pdf) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            clean_text = " ".join(text.split())
            
            matches = list(re.finditer(pattern_one, clean_text))
            
            if matches:
                for match in matches:                
                    data.append({
                        'Data': match.group(1),
                        'Descrição': match.group(2),
                        'Valor': match.group(3)
                    })
            else:
                matches_two = re.finditer(pattern_two, clean_text)
                for match in matches_two:
                    data.append({
                        'Data': match.group(1),
                        'Descrição': match.group(2),
                        'Valor': match.group(3)
                    })
                
    investment_fund = pd.DataFrame(data)
    investment_fund['prioridade'] = investment_fund.apply(define_if_priority, axis=1)
    investment_fund = normalize_if_columns(investment_fund)
    investment_fund = investment_fund.sort_values(
        by=['Data', 'prioridade'], 
        ascending=[True, True]
    )
    investment_fund = investment_fund.drop(columns = ['prioridade'])
    investment_fund = investment_fund.drop_duplicates()
    investment_fund = calculate_revenue(investment_fund)
    
    return investment_fund

#-----------------------------------------------------------------------------
# Function to Create CE_IF from united pdf:
#-----------------------------------------------------------------------------
def ce_if(output_pdf):
    
    pattern = (
    r'(\d{2}\s*\/\s*\d{2})\s+'
    r'([A-Za-zÀ-ÿ0-9\s\-\.\/\?]+?)\s+'
    r'([\d\.]+[\,\.]\d{2})\s*+' 
    r'(D|C)'
    )
    pattern_year = r'\s\d{2}(\/\d{4})\s'

    data = []

    with pdfplumber.open(output_pdf) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if not page_text:
                continue
                
            # Busca apenas no texto extraído DA PÁGINA ATUAL
            matches_one = list(re.finditer(pattern, page_text))
            if matches_one:
                for match in matches_one:
                    data.append({
                        "Data": match.group(1),
                        "Descrição": match.group(2).strip(),
                        "Valor": match.group(3),
                        "Natureza": match.group(4)
                    })
                    

            matches_two = list(re.finditer(pattern_year, page_text))
            if matches_two:
                for match in matches_two:
                    data.append({
                        "Ano": match.group(1)
                    })

    investment_fund = pd.DataFrame(data)
    
    investment_fund['Ano'] = investment_fund['Ano'].bfill()
    investment_fund = investment_fund.dropna(subset=['Descrição'])
    investment_fund['Data'] = (
        investment_fund['Data'].astype(str).str.replace(' ', '') + 
        investment_fund['Ano'].astype(str).str.strip()
    )
    
    investment_fund = investment_fund.drop(columns=['Ano'])

    investment_fund['Data'] = pd.to_datetime(investment_fund['Data'].str.replace(' ', ''), format='%d/%m/%Y', errors='coerce')
    
    dic_fund = {'APLICACAO': 'Aplicação', 'RESGATE': 'Resgate'}
    
    investment_fund['Descrição'] = investment_fund['Descrição'].replace(dic_fund)
    
    investment_fund['Valor'] = pd.to_numeric(
        investment_fund['Valor']
        .astype(str)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
        .str.strip(),
        errors='coerce'
        ).fillna(0.0)
    
    investment_fund = calculate_revenue(investment_fund)
    
    return investment_fund
    
#-----------------------------------------------------------------------------
# Function to Exhibit DataFrame and Download Options:
#-----------------------------------------------------------------------------
def final_extract(df_dados: pd.DataFrame, titulo: str = "📋 Extrato Processado e Normalizado"):
    if df_dados is not None and not df_dados.empty:
        st.subheader(titulo)
        
        df_exibicao = df_dados.copy()
        
        if 'Data' in df_exibicao.columns:
            df_exibicao['Data'] = pd.to_datetime(df_exibicao['Data']).dt.strftime('%d/%m/%Y')
        
        st.dataframe(df_exibicao, use_container_width=True)
        st.metric(label="Total de Lançamentos Encontrados", value=len(df_dados))
        
        st.divider()
        st.subheader("📥 Opções de Download")
        
        return True
        
    return False


#-----------------------------------------------------------------------------
# Website:
#-----------------------------------------------------------------------------
# Initializes the step in Streamlit's memory if it doesn't exist
#-----------------------------------------------------------------------------

if 'step' not in st.session_state:
    st.session_state.step = 1
if 'main_choice' not in st.session_state:
    st.session_state.main_choice = None


def return_start():
    st.session_state.step = 1
    st.session_state.main_choice = None
    st.rerun()

#-----------------------------------------------------------------------------
# Main Interface:
#-----------------------------------------------------------------------------
    
st.set_page_config(page_title="Gerenciador de Extratos Bancários e Unificador de PDFs", page_icon="📄")
st.title("📄 Gerenciador de Extratos Bancários e Unificador de PDFs")

if st.session_state.step == 1:
    st.subheader("O que gostaria de fazer?")
    
    choice = st.radio(
        "Selecione uma opção para continuar:",
        ['Unir PDFs', 'Planilhar Extratos Bancários']
    )
    
    if st.button("Confirmar Escolha ➡️"):
        st.session_state.main_choice = choice
        st.session_state.step = 2
        st.rerun()

#-----------------------------------------------------------------------------
# Choosing the Bank and Type of Bank Extract:
#-----------------------------------------------------------------------------
    
if st.session_state.step == 2:
    
    if st.button("🔙 Voltar ao Menu Principal"):
        return_start()
        
    st.divider()

    if st.session_state.main_choice == 'Unir PDFs':
        st.header("📄 Unificador de Arquivos PDF")
        interface_unite_pdfs()

    elif st.session_state.main_choice == 'Planilhar Extratos Bancários':
        st.header("📊 Planilhador de Extratos")
        
        second_choice = st.selectbox(
            "Selecione o Banco:",
            ["Banco do Brasil", "Caixa Econômica Federal"]
        )
        
        third_choice = st.selectbox(
            'Selecione o tipo de extrato:',
            ['Conta Corrente', 'Conta Poupança', 'Fundo de Investimento']
        )
        
        st.info(f"Configuração selecionada: {second_choice} ({third_choice})")
        
        extract_files = st.file_uploader(
            f"Arraste os PDFs dos extratos de {third_choice} aqui", 
            type="pdf",
            accept_multiple_files=True
        )
        
        if extract_files:
            st.success("Arquivo recebido! Pronto para processar.")
            
            if second_choice == 'Banco do Brasil' and third_choice == 'Conta Corrente':
                with st.spinner("Extraindo e normalizando dados do extrato..."):
                    output_pdf = unite_pdfs(extract_files)
                    account = bb_cc(output_pdf)
                
                final_extract(account)
                    
                     
            elif second_choice == 'Banco do Brasil' and third_choice == 'Conta Poupança':
                with st.spinner("Extraindo e normalizando dados do extrato..."):
                    output_pdf = unite_pdfs(extract_files)
                    account = bb_cp(output_pdf)
                
                final_extract(account)
                    
            elif second_choice == 'Banco do Brasil' and third_choice == 'Fundo de Investimento':
                with st.spinner("Extraindo e normalizando dados do extrato..."):
                    output_pdf = unite_pdfs(extract_files)
                    account = bb_if(output_pdf)
                
                final_extract(account)

            elif second_choice == 'Caixa Econômica Federal' and third_choice == 'Fundo de Investimento':
                with st.spinner("Extraindo e normalizando dados do extrato..."):
                    output_pdf = unite_pdfs(extract_files)
                    account = ce_if(output_pdf)

                final_extract(account)
            
            nome_base = st.text_input("Digite o nome para o arquivo final (sem extensão):", value="extrato_bb_cc_tratado")
            
            output_excel = BytesIO()
            
            st.download_button(
                label="📊 Baixar Extrato em Excel (.xlsx)",
                data=output_excel,
                file_name=f"{nome_base}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.download_button(
                label="📄 Baixar Cópia do PDF Unificado (.pdf)",
                data=output_pdf,
                file_name=f"{nome_base}_unificado.pdf",
                mime="application/pdf"
            )
            
            with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                account.to_excel(writer, index=False, sheet_name='Extrato_Tratado')
            output_excel.seek(0)
            
            if output_pdf:
                output_pdf.seek(0)
            
            else:
                st.warning("⚠️ Não foi possível ler ou estruturar os dados do arquivo.")
        else:
            st.info(f"A lógica para {second_choice} - {third_choice} está aguardando suas funções de processamento.")



        
        
        
