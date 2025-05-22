# PGM-MSRA: Agente de Raciocínio Multi-Etapa para Modelagem de Progressão de Carreira

## Descrição

O PGM-MSRA é um sistema baseado em Inteligência Artificial (OpenAI GPT) projetado para simular a progressão de carreira de servidores públicos com base em regulamentos específicos e histórico individual. Ele interpreta consultas em linguagem natural, aplica regras de progressão e calcula a trajetória de carreira, incluindo a referência final e o salário associado.

## Funcionalidades Principais

*   **Interpretação de Linguagem Natural:** Entende consultas de usuários sobre sua situação de carreira.
*   **Simulação de Progressão:** Calcula a progressão por mérito e por títulos (Nível Médio, Superior, Especialização, Mestrado, Doutorado) respeitando os interstícios.
*   **Suporte a Múltiplos Cargos/Planos:** Capacidade de adaptar a simulação com base no cargo específico do servidor, aplicando variações nas regras de progressão e estrutura de referência (ex: Magistério "MG" vs. Geral "NE/NS").
*   **Cálculo Salarial:** Determina o salário base associado à última referência de carreira alcançada, com base em tabelas salariais específicas do cargo.
*   **Explicação dos Resultados:** Fornece um resumo claro e compreensível da progressão de carreira e do salário.

## Arquitetura (Visão Geral)

O PGM-MSRA utiliza uma arquitetura de agentes especializados:

1.  **Pensador (Thinker):** Responsável por analisar a consulta do usuário em linguagem natural e extrair os dados estruturados necessários (data de admissão, referência inicial, tipo de cargo, títulos, data limite da simulação).
2.  **Executor (Executor):** O núcleo de raciocínio. Recebe o regulamento do PCC aplicável ao cargo do servidor e os dados extraídos pelo Pensador. Utiliza a ferramenta `code_interpreter` da OpenAI para simular a progressão da referência do servidor passo a passo, aplicando as regras de mérito e título.
3.  **Orquestrador Python (`main.py`):** Gerencia o fluxo entre os agentes. Após o Executor determinar a progressão da referência, o código Python consulta tabelas salariais para determinar o salário correspondente ao cargo e à última referência.
4.  **Juiz (Judge):** Recebe a linha do tempo da progressão (gerada pelo Executor) e as informações salariais (calculadas pelo Python) e apresenta um resumo consolidado e amigável para o usuário.

## Tecnologias Utilizadas

*   Python 3.x
*   OpenAI API (GPT-4 Turbo / GPT-3.5 Turbo, API de Assistants com `code_interpreter`)
*   Biblioteca `openai` para Python
*   Biblioteca `python-dotenv` para gerenciamento de chaves de API

## Configuração e Instalação

1.  **Clone o repositório:**
    ```bash
    git clone [URL_DO_SEU_REPOSITORIO]
    cd pgm-msra 
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # venv\Scripts\activate  # Windows
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure sua Chave da API OpenAI:**
    *   Crie um arquivo chamado `.env` na raiz do projeto.
    *   Adicione sua chave da API ao arquivo `.env`:
        ```
        OPENAI_API_KEY="sk-SUA_CHAVE_API_AQUI"
        ```
    *   **Importante:** Adicione `.env` ao seu arquivo `.gitignore` para não comitar sua chave.

## Como Usar/Executar

Para executar o pipeline principal de simulação de carreira:

```bash
python main.py
