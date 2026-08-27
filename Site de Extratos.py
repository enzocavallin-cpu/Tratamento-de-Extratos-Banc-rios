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
from pypdf import PdfReader, PdfWriter

st.set_page_config(page_title="Gerenciador de Extratos Bancários e Unificador de PDFs", page_icon="📄")

#-----------------------------------------------------------------------------
# Function to Unite PDFs:
#-----------------------------------------------------------------------------
def unite_pdfs(ordered_files):
    if not ordered_files:
        return None
    
    writer = pypdf.PdfWriter()
    
    for file in ordered_files:
        writer.append(file)
        
    output_pdf = BytesIO()
    writer.write(output_pdf)
    output_pdf.seek(0)
    
    return output_pdf

#-----------------------------------------------------------------------------
# Function to Divide PDFs:
#-----------------------------------------------------------------------------

def interface_split_pdfs():
    uploaded_file = st.file_uploader(
        "Selecione o arquivo PDF que deseja dividir", type="pdf"
    )

    if uploaded_file:
        reader = PdfReader(uploaded_file)
        total_pages = len(reader.pages)
        st.info(f"O arquivo contém {total_pages} página(s).")

        modo = st.radio(
            "Selecione como deseja dividir:",
            ["Extrair Páginas Específicas", "Separar Todas as Páginas em Zip"],
        )

        if modo == "Extrair Páginas Específicas":
            paginas_str = st.text_input(
                "Digite as páginas a extrair (ex: 1, 3, 5-8):", value="1"
            )

            if st.button("✂️ Extrair Páginas"):
                # Lógica para ler e salvar as páginas selecionadas
                writer = PdfWriter()
                # Exemplo simples extraindo de um intervalo selecionado
                try:
                    # Exemplo extraindo página individual ou lista
                    pages_to_keep = [
                        int(p.strip()) - 1
                        for p in paginas_str.split(",")
                        if p.strip().isdigit()
                    ]
                    for p in pages_to_keep:
                        if 0 <= p < total_pages:
                            writer.add_page(reader.pages[p])

                    output_pdf = io.BytesIO()
                    writer.write(output_pdf)
                    output_pdf.seek(0)

                    st.download_button(
                        label="📥 Baixar PDF Dividido",
                        data=output_pdf,
                        file_name="pdf_dividido.pdf",
                        mime="application/pdf",
                    )
                except Exception as e:
                    st.error(f"Erro ao processar as páginas: {e}")

#-----------------------------------------------------------------------------
# Function of the Website Interface to Unite PDFs:
#-----------------------------------------------------------------------------
def interface_unite_pdfs():
    # Inicializa a chave do uploader se não existir
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0

    uploaded_files = st.file_uploader(
        "Selecione ou arraste os arquivos PDF que deseja unificar",
        type="pdf",
        accept_multiple_files=True,
        key=f"pdf_uploader_{st.session_state.uploader_key}",
    )

    if uploaded_files:
        st.success(f"{len(uploaded_files)} arquivos carregados com sucesso!")

        # Botão para limpar o upload e resetar a ordem dos arquivos
        if st.button("🗑️ Limpar arquivos carregados"):
            st.session_state.uploader_key += 1
            if "file_order" in st.session_state:
                del st.session_state["file_order"]
            st.rerun()

        # Mapeia os arquivos por nome
        files_dict = {f.name: f for f in uploaded_files}

        # Inicializa a ordem no session_state ou atualiza se novos arquivos forem adicionados
        if "file_order" not in st.session_state or set(
            st.session_state.file_order
        ) != set(files_dict.keys()):
            st.session_state.file_order = list(files_dict.keys())

        st.subheader("Ordene os arquivos:")

        # Cria a lista com botões de reordenação
        for idx, filename in enumerate(st.session_state.file_order):
            col_name, col_top, col_up, col_down, col_bottom = st.columns(
                [6, 1, 1, 1, 1]
            )

            total_files = len(st.session_state.file_order)
            is_first = idx == 0
            is_last = idx == total_files - 1

            with col_name:
                st.write(f"📄 **{idx + 1}.** {filename}")

            with col_top:
                if st.button(
                    "🔝",
                    key=f"top_{idx}",
                    disabled=is_first,
                    help="Mover para o topo",
                ):
                    item = st.session_state.file_order.pop(idx)
                    st.session_state.file_order.insert(0, item)
                    st.rerun()

            with col_up:
                if st.button(
                    "⬆️",
                    key=f"up_{idx}",
                    disabled=is_first,
                    help="Subir uma posição",
                ):
                    (
                        st.session_state.file_order[idx],
                        st.session_state.file_order[idx - 1],
                    ) = (
                        st.session_state.file_order[idx - 1],
                        st.session_state.file_order[idx],
                    )
                    st.rerun()

            with col_down:
                if st.button(
                    "⬇️",
                    key=f"down_{idx}",
                    disabled=is_last,
                    help="Descer uma posição",
                ):
                    (
                        st.session_state.file_order[idx],
                        st.session_state.file_order[idx + 1],
                    ) = (
                        st.session_state.file_order[idx + 1],
                        st.session_state.file_order[idx],
                    )
                    st.rerun()

            with col_bottom:
                if st.button(
                    "🔚",
                    key=f"bottom_{idx}",
                    disabled=is_last,
                    help="Mover para o fim",
                ):
                    item = st.session_state.file_order.pop(idx)
                    st.session_state.file_order.append(item)
                    st.rerun()

        st.divider()
        nome_arquivo = st.text_input(
            "Digite o nome para o arquivo final:", value="pdf_unificado"
        )

        if not nome_arquivo.endswith(".pdf"):
            nome_arquivo += ".pdf"

        # Pega a lista ordenada final
        ordered_files = [
            files_dict[name]
            for name in st.session_state.file_order
            if name in files_dict
        ]

        if st.button("🚀 Unificar PDFs"):
            with st.spinner("Processando..."):
                final_pdf = unite_pdfs(ordered_files)

            if final_pdf:
                st.download_button(
                    label="📥 Baixar PDF Unificado",
                    data=final_pdf.getvalue(),
                    file_name=nome_arquivo,
                    mime="application/pdf",
                )
    else:
        # Limpa o estado quando não houver arquivos
        if "file_order" in st.session_state:
            del st.session_state["file_order"]
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
        "RESGATE": "Resgate",
        "SALDO ANTERIOR": "Saldo Anterior",
        "APL AUTOM": "Aplicação Automática",
        "CRED TEV": "Crédito por Transferência Eletrônica de Valores",
        "CREDAUTOR": "Crédito Autorizado",
        "CRED TED": "Crédito por Transferência Eletrônica Disponível",
        "CRPCV POUP": "Crédito de Pagamento de Convênio via Poupança",
        "DBPCV POUP": "Débito de Pagamento de Convênio via Poupança",
        "DBPCV TED": "Débito de Pagamento de Convênio via Transferência Eletrônica Disponível",
        "DBPCV TV": "Débito de Pagamento de Convênio via Terminal Virtual",
        "DEVOL TED": "Devolução de Transferência Eletrônica Disponível",
        "EDPCV TV": "Estorno de Débito de Pagamento de Convênio via Terminal Virtual",
        "RESG AUTOM": "Resgate Automático"
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
        'Saldo Atual': 'Saldo Final',
        'RESGATE': 'Resgate',
        'COBRANÇA DE IR': 'Cobrança de IR',
        'APLICAÇÃO': 'Aplicação'
        
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
                        "Lote": match.group(2) if match.group(2) else "",
                        "Descrição": match.group(3).strip(),
                        "Documento": match.group(4) if match.group(4) else "",
                        "Valor": match.group(5),
                        "Natureza": match.group(6)
                    })
            elif len(matches_two) > 0:
                for match in matches_two:
                    data.append({
                        'Data': match.group(1),
                        'Lote': match.group(3) if match.group(3) else "",
                        'Descrição': match.group(2).strip(),
                        'Documento': match.group(4) if match.group(4) else "",
                        'Valor': match.group(5),
                        'Natureza': match.group(6),
                    })
            else:
                for match in matches_three:
                    data.append({
                                    'Data': match.group(1),
                                    'lote': match.group(3) if match.group(3) else "",
                                    'Descrição': match.group(2).strip(),
                                    'Documento': match.group(4) if match.group(4) else "",
                                    'Valor': match.group(5),
                                    'Natureza': match.group(6),
                                })
                        
    checking_account = pd.DataFrame(data)
    checking_account = checking_account.apply(adjust_description, axis=1)
    
    checking_account['Descrição'] = (
    checking_account['Descrição']
    .replace('', pd.NA)
    .groupby([checking_account['Data'], checking_account['Lote']])
    .transform(lambda s: s.ffill().bfill())
    .fillna('')
    )
    
    checking_account = normalize_columns(checking_account)
    checking_account['prioridade'] = checking_account.apply(define_priority, axis=1)
    
    checking_account = checking_account.sort_values(
        by=['Data', 'prioridade', 'Documento'], 
        ascending=[True, True, True]
    )
    
    checking_account = checking_account.drop(columns=['prioridade'])
    checking_account = checking_account.drop_duplicates()
    
    valores_sinalizados = np.where(checking_account['Natureza'] == 'C', checking_account['Valor'], - checking_account['Valor'])
    checking_account['Saldo'] = valores_sinalizados.cumsum()
    
    checking_account = checking_account[['Data', 'Documento', 'Lote', 'Descrição', 'Natureza', 'Valor', 'Saldo']]
    
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
# Function to Create CE_CC from united pdf:
#-----------------------------------------------------------------------------

def ce_cc(output_pdf):
    pattern_one = (
        r'(\d{2}\/\d{2}\/\d{4})\s+'
        r'(\d{1,20})\s+'                  # Removido \s+ interno para limpar o documento
        r'([A-Za-zÀ-ÿ0-9\s\-\.\/\?]+?)\s+'
        r'([\d\.]+[\,\.]\d{2})\s+'
        r'(D|C)\s+'
        r'([\d\.]+[\,\.]\d{2})\s+'
        r'(D|C)'
    )
    
    data = []
    
    with pdfplumber.open(output_pdf) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            if 'Lançamentos do Dia' in text:
                text = text.split('Lançamentos do Dia')[0]
            
            lines = text.split('\n')
            clean_text = ' '.join(lines)
            
            matches_one = list(re.finditer(pattern_one, clean_text))
            
            for match in matches_one:
                data.append({
                    "Data": match.group(1),
                    "Documento": match.group(2).strip(),
                    "Descrição": match.group(3).strip(),
                    "Valor": match.group(4),
                    "Natureza": match.group(5),
                    "Saldo": match.group(6),
                    "Natureza_Saldo": match.group(7) # 1. Nome unificado (com N e S maiúsculos)
                })
    
    # Tratamento para PDF sem correspondências
    if not data:
        return pd.DataFrame(columns=['Data', 'Documento', 'Descrição', 'Natureza', 'Valor', 'Saldo'])

    checking_account = pd.DataFrame(data)
    
    # 2. Converte o Saldo textual para numérico (float)
    checking_account['Saldo'] = (
        checking_account['Saldo']
        .astype(str)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
        .astype(float)
    )
    
    # 3. Aplica o sinal negativo no Saldo usando o nome correto da coluna
    checking_account['Saldo'] = np.where(
        checking_account['Natureza_Saldo'] == 'D',
        -checking_account['Saldo'],
        checking_account['Saldo']
    )
    
    # 4. Remove a coluna auxiliar do saldo
    checking_account = checking_account.drop(columns=['Natureza_Saldo'])
   
    # Funções customizadas
    checking_account = checking_account.apply(adjust_description, axis=1)
    checking_account = normalize_columns(checking_account)
    checking_account['prioridade'] = checking_account.apply(define_priority, axis=1)
    
    checking_account = checking_account.sort_values(
        by=['Data', 'prioridade', 'Documento'], 
        ascending=[True, True, True]
    )
    
    checking_account = checking_account.drop(columns=['prioridade']).drop_duplicates()
    
    # Reorganiza e escolhe as colunas finais
    checking_account = checking_account[['Data', 'Documento', 'Descrição', 'Natureza', 'Valor', 'Saldo']]
   
    return checking_account

#-----------------------------------------------------------------------------
# Function to Create CE_IF from united pdf:
#-----------------------------------------------------------------------------
def ce_if(output_pdf):
    
    pattern = (
    r'(\d{2}\s*\/\s*\d{2})\s+'
    r'([A-Za-zÀ-ÿ0-9\s\-\.\/\?]+?)\s+'
    r'([\d\.]+[\,\.]\d{2})\s*' 
    r'(D|C)'
    )
    pattern_year = r'\s\d{2}(\/\d{4})\s'

    data = []

    with pdfplumber.open(output_pdf) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if not page_text:
                continue
        
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
    investment_fund['Ano'] = investment_fund['Ano'].ffill(limit=1)
    investment_fund = investment_fund.dropna(subset=['Descrição'])
    investment_fund['Data'] = (
        investment_fund['Data'].astype(str).str.replace(' ', '') + 
        investment_fund['Ano'].astype(str).str.strip()
    )
    investment_fund = investment_fund.drop(columns=['Ano'])

    investment_fund['Data'] = pd.to_datetime(investment_fund['Data'].str.replace(' ', ''), format='%d/%m/%Y', errors='coerce')
    
    dic_fund = {'APLICACAO': 'Aplicação', 'RESGATE': 'Resgate'}
    
    investment_fund['Descrição'] = investment_fund['Descrição'].replace(dic_fund)
    
    investment_fund['Valor'] = investment_fund['Valor'].str.replace('.', '').str.replace(',', '.')
    investment_fund['Valor'] = pd.to_numeric(investment_fund['Valor'], errors='coerce')
    
    investment_fund = investment_fund.sort_values(by='Data', ascending=True)   
    
    return investment_fund
    
#-----------------------------------------------------------------------------
# Function to Exhibit DataFrame and Download Options:
#-----------------------------------------------------------------------------
def final_extract(df_dados: pd.DataFrame, titulo: str = "📋 Extrato Processado e Normalizado"):
    if df_dados is not None and not df_dados.empty:
        st.subheader(titulo)
        
        df_exibicao = df_dados.copy()
        
        if 'Data' in df_exibicao.columns:
            df_exibicao['Data'] = pd.to_datetime(
                df_exibicao['Data']
            ).dt.strftime('%d/%m/%Y')
        
        st.dataframe(
            df_exibicao,
            width='stretch'
        )
        
        st.metric(
            label="Total de Lançamentos Encontrados",
            value=len(df_dados)
        )
        
        st.divider()
        st.subheader("📥 Opções de Download")
        
        return df_dados
        
    return None


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
st.title("📄 Gerenciador de Extratos Bancários e Unificador de PDFs")

if st.session_state.step == 1:
    st.subheader("O que gostaria de fazer?")
    
    choice = st.radio(
        "Selecione uma opção para continuar:",
        ['Unir PDFs', "Dividir PDFs", 'Planilhar Extratos Bancários']
    )
    
    if st.button("Confirmar Escolha ➡️"):
        st.session_state.main_choice = choice
        st.session_state.step = 2
        st.rerun()

# -----------------------------------------------------------------------------
# Choosing the Bank and Type of Bank Extract or PDF tools:
# -----------------------------------------------------------------------------

if st.session_state.step == 2:

    if st.button("🔙 Voltar ao Menu Principal"):
        return_start()

    st.divider()

    if st.session_state.main_choice == "Unir PDFs":
        st.header("📄 Unificador de Arquivos PDF")
        interface_unite_pdfs()

    elif st.session_state.main_choice == "Dividir PDFs":
        st.header("✂️ Divisor de Arquivos PDF")
        # Chama a função de interface para dividir PDFs
        interface_split_pdfs()

    elif st.session_state.main_choice == "Planilhar Extratos Bancários":

        st.header("📊 Planilhador de Extratos")

        second_choice = st.selectbox(
            "Selecione o Banco:",
            ["Banco do Brasil", "Caixa Econômica Federal"],
        )

        third_choice = st.selectbox(
            "Selecione o tipo de extrato:",
            ["Conta Corrente", "Conta Poupança", "Fundo de Investimento"],
        )

        st.info(
            f"Configuração selecionada: {second_choice} ({third_choice})"
        )

        extract_files = st.file_uploader(
            f"Arraste os PDFs dos extratos de {third_choice} aqui",
            type="pdf",
            accept_multiple_files=True,
        )

        if extract_files:

            st.success(
                f"{len(extract_files)} arquivo(s) recebido(s)! "
                "Pronto para processar."
            )

            output_pdf = None
            account = None

            if (
                second_choice == "Banco do Brasil"
                and third_choice == "Conta Corrente"
            ):

                with st.spinner("Extraindo e normalizando dados do extrato..."):
                    output_pdf = unite_pdfs(extract_files)
                    account = bb_cc(output_pdf)

            elif (
                second_choice == "Banco do Brasil"
                and third_choice == "Conta Poupança"
            ):

                with st.spinner("Extraindo e normalizando dados do extrato..."):
                    output_pdf = unite_pdfs(extract_files)
                    account = bb_cp(output_pdf)

            elif (
                second_choice == "Banco do Brasil"
                and third_choice == "Fundo de Investimento"
            ):

                with st.spinner("Extraindo e normalizando dados do extrato..."):
                    output_pdf = unite_pdfs(extract_files)
                    account = bb_if(output_pdf)

            elif (
                second_choice == "Caixa Econômica Federal"
                and third_choice == "Conta Corrente"
            ):
                output_pdf = unite_pdfs(extract_files)
                account = ce_cc(output_pdf)

            elif (
                second_choice == "Caixa Econômica Federal"
                and third_choice == "Fundo de Investimento"
            ):

                with st.spinner("Extraindo e normalizando dados do extrato..."):
                    output_pdf = unite_pdfs(extract_files)
                    account = ce_if(output_pdf)

            else:

                st.warning(
                    f"Ainda não existe uma função de processamento "
                    f"para {second_choice} + {third_choice}."
                )

            if (
                isinstance(account, pd.DataFrame)
                and not account.empty
                and len(account.columns) > 0
            ):

                account = final_extract(account)

                nome_padrao = (
                    f"extrato_"
                    f"{second_choice.lower().replace(' ', '_')}_"
                    f"{third_choice.lower().replace(' ', '_')}_tratado"
                )

                nome_base = st.text_input(
                    "Digite o nome para o arquivo final (sem extensão):",
                    value=nome_padrao,
                )

                output_excel = BytesIO()

                with pd.ExcelWriter(
                    output_excel, engine="xlsxwriter"
                ) as writer:

                    account.to_excel(
                        writer, index=False, sheet_name="Extrato_Tratado"
                    )

                output_excel.seek(0)

                if output_pdf is not None:
                    output_pdf.seek(0)

                st.subheader("📥 Opções de Download")

                st.download_button(
                    label="📊 Baixar Extrato em Excel (.xlsx)",
                    data=output_excel,
                    file_name=f"{nome_base}.xlsx",
                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),
                )

                if output_pdf is not None:

                    st.download_button(
                        label="📄 Baixar Cópia do PDF Unificado (.pdf)",
                        data=output_pdf,
                        file_name=f"{nome_base}_unificado.pdf",
                        mime="application/pdf",
                    )

            elif account is not None:

                st.warning(
                    "⚠️ O processamento foi executado, "
                    "mas não foram encontrados dados válidos."
                )



        
        
        
