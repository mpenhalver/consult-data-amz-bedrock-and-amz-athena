import json
import boto3
import time
import gradio as gr


sts = boto3.client('sts')
caller_identity = sts.get_caller_identity()
account_id = caller_identity['Account']

# Funções do Lambda original
def load_table_structures_from_s3():
    s3 = boto3.client('s3')
    bucket_name = f'{account_id}-poc-config-data'
    file_key = 'table_structures.json'
    
    response = s3.get_object(Bucket=bucket_name, Key=file_key)
    file_content = response['Body'].read().decode('utf-8')
    return json.loads(file_content)

def generate_sql_with_bedrock(prompt, table_structures):
    bedrock_runtime = boto3.client('bedrock-runtime')
    system_prompt = "Você é um assistente de IA que gera consultas SQL com base em questões de linguagem natural e estruturas de tabela fornecidas. Retorne apenas a consulta SQL sem qualquer explicação adicional."

    messages = [
        {"role": "user", "content": f"""
         Dadas as seguintes estruturas de tabela:
         {json.dumps(table_structures, indent=2)}
         
        Gere uma query SQL para responder à seguinte pergunta:
         {prompt}
         
        Retorne apenas a query SQL, sem qualquer explicação adicional.
         """}
    ]
    
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 300,
        "system": system_prompt,
        "messages": messages
    })
    
    response = bedrock_runtime.invoke_model(
        body=body,
        modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',
        contentType='application/json',
        accept='application/json'
    )
    
    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text'].strip()

def process_results(results):
    headers = [col['Label'] for col in results['ResultSet']['ResultSetMetadata']['ColumnInfo']]
    rows = results['ResultSet']['Rows'][1:]
    formatted_data = []
    for row in rows:
        formatted_row = {}
        for i, value in enumerate(row['Data']):
            formatted_row[headers[i]] = value.get('VarCharValue', '')
        formatted_data.append(formatted_row)
    return {'headers': headers, 'data': formatted_data}

def generate_nlp_response(prompt, formatted_results, sql_query):
    bedrock_runtime = boto3.client('bedrock-runtime')
    
    messages = [
        {"role": "user", "content": f"""
    Pergunta original: {prompt}

    Consulta SQL executada: {sql_query}

    Resultados da consulta:
    {json.dumps(formatted_results, indent=2)}

    Com base nos resultados acima, forneça uma resposta em linguagem natural para a pergunta original.
    A resposta deve ser clara, concisa e diretamente relacionada à pergunta feita.
    Inclua números específicos e detalhes relevantes dos resultados.
    """}
    ]

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "system": "Você é um assistente de IA que fornece respostas claras e concisas com base nos resultados da consulta SQL. Inclua números específicos e detalhes relevantes dos resultados em sua resposta.",    
        "messages": messages,
        "temperature": 0.7,
        "top_p": 0.95,
    })
    
    response = bedrock_runtime.invoke_model(
        body=body,
        modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',
        contentType='application/json',
        accept='application/json'
    )
    response_body = json.loads(response['body'].read())
    nlp_response = response_body['content'][0]['text'].strip()
    return {
        'nlp_response': nlp_response,
        'sql_query': sql_query,
        'raw_results': formatted_results
    }

# Função para processar a consulta
def process_query(prompt, history):
    try:
        # Carregar a estrutura das tabelas do S3
        table_structures = load_table_structures_from_s3()
        
        # Gerar consulta SQL
        sql_query = generate_sql_with_bedrock(prompt, table_structures)
        
        # Executar consulta no Athena
        athena_client = boto3.client('athena')
        query_execution = athena_client.start_query_execution(
            QueryString=sql_query,
            QueryExecutionContext={'Database': 'poc-db'},
            ResultConfiguration={'OutputLocation': f's3://{account_id}-poc-config-data/athena-results/'}
        )
        
        # Aguardar a conclusão da consulta
        while True:
            query_status = athena_client.get_query_execution(QueryExecutionId=query_execution['QueryExecutionId'])
            status = query_status['QueryExecution']['Status']['State']
            if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                break
            time.sleep(1)
        
        if status == 'SUCCEEDED':
            results = athena_client.get_query_results(QueryExecutionId=query_execution['QueryExecutionId'])
            formatted_results = process_results(results)
            nlp_response = generate_nlp_response(prompt, formatted_results, sql_query)
            return nlp_response['nlp_response']
        else:
            return f"Erro: A consulta falhou com o status: {status}"
    
    except Exception as e:
        return f"Erro ao processar a consulta: {str(e)}"

# Interface Gradio
iface = gr.Blocks()

with iface:
    # Adicione a imagem no topo
    gr.Image("download.png", show_label=False, container=False)
    
    # Adicione um espaço em branco para separação (opcional)
    gr.Markdown("---")  # Isso cria uma linha horizontal para separação

    chatbot = gr.Chatbot(height=500)
    msg = gr.Textbox()
    clear = gr.Button("Limpar")

    def user(user_message, history):
        return "", history + [[user_message, None]]

    def bot(history):
        user_message = history[-1][0]
        bot_response = process_query(user_message, history)
        history[-1][1] = bot_response
        return history

    msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot, chatbot, chatbot
    )
    clear.click(lambda: None, None, chatbot, queue=False)

if __name__ == "__main__":
    iface.launch()
