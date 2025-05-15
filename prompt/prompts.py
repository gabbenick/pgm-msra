REGULAMENTO_PCC_GERAL_PT = """
Regulamento do Plano de Cargos e Carreiras (PCC Geral):

Visão Geral:
Existe um conjunto de classes (A, B, C, D) e níveis (1, 2, 3, 4, 5, 6).
Estes são precedidos de um grupo salarial que define a formação acadêmica do concurso:
- NE: Nível Elementar
- NM: Nível Médio
- NS: Nível Superior

A referência também inclui a carga horária:
- 21: 25 horas
- 41: 40 horas
- 20: 20 horas

Formato da Referência: GrupoSalarial + CargaHoraria + Classe + Nível (ex: NE41A01).

Regras de Progressão por Mérito:
1.  Data de Admissão: Marco inicial.
2.  Estágio Probatório: Dura 3 anos a partir da data de admissão. Ao final, o servidor é confirmado na referência inicial.
3.  Primeira Progressão por Mérito: Ocorre 2 anos após o fim do estágio probatório. Avança 1 nível na mesma classe.
4.  Demais Progressões por Mérito:
    a.  Ocorrem a cada 2 anos após a última progressão (seja ela por mérito ou por título).
    b.  Avanço Horizontal: Avança de nível em nível (1, 2, 3, 4, 5, 6) dentro da mesma classe.
        (Ex: NE41A01 -> NE41A02 -> ... -> NE41A06)
    c.  Avanço Vertical (Promoção de Classe): Ao atingir o nível 6 de uma classe, na próxima progressão por mérito, o servidor avança para o nível 1 da classe imediatamente superior.
        (Ex: NE41A06 -> NE41B01)
    d.  Teto da Carreira: A progressão por mérito cessa ao atingir a referência D06 (Classe D, Nível 6). Para progredir para grupos salariais diferentes (NE para NM, NM para NS), é necessário um novo concurso.

Regras de Progressão por Título (pode ocorrer a qualquer momento, respeitando interstícios, e "substitui" uma progressão por mérito se a data do título for anterior):
1.  Título de Nível Médio (Regular):
    a.  Efeito: O servidor ocupará o padrão 01 (nível 1) da classe imediatamente superior à sua classe atual.
    b.  Exemplo: Se em NE20A03, progride para NE20B01.
2.  Título de Nível Superior (Graduação):
    a.  Efeito: O servidor ocupará o padrão 01 (nível 1) da classe imediatamente superior à sua classe atual. (Mesmo efeito do Título de Nível Médio).
    b.  Exemplo: Se em NE41A03, progride para NE41B01.
3.  Título de Especialização / Pós-Graduação (Lato Sensu):
    a.  Efeito: Avança 4 padrões (níveis) a partir da referência atual. Se o avanço ultrapassar o nível 6 da classe atual, continua na classe seguinte (nível 1, depois 2, etc.).
    b.  Exemplo 1: NE41A01 + Especialização -> NE41A05.
    c.  Exemplo 2: NE41A04 + Especialização -> NE41B02. # Corrigido exemplo aqui
4.  Título de Mestrado ou Doutorado (Stricto Sensu):
    a.  Efeito: Progressão vertical. O servidor avança para a classe imediatamente superior, mantendo o mesmo nível que possuía na classe anterior.
    b.  Exemplo: NE41A04 + Mestrado/Doutorado -> NE41B04.
    c.  Se já estiver na última classe (D) e no nível X, e receber Mestrado/Doutorado, permanece em DX.

Interstícios (Tempo Mínimo de Espera entre Requerimentos de Progressão por Título):
-   De Título Médio para requerer Título Superior: 1 ano de espera após a data da progressão pelo título médio.
-   De Título Superior para requerer Especialização/Pós-Graduação: 2 anos de espera após a data da progressão pelo título superior.
-   De Especialização/Pós-Graduação para requerer Mestrado ou Doutorado: 1 ano de espera após a data da progressão pela especialização.
-   De Mestrado para requerer Doutorado (ou vice-versa, se aplicável): 1 ano de espera após a data da progressão pelo título anterior (Mestrado/Doutorado).

Considerações Gerais para o Cálculo:
-   A data de referência para uma progressão por título é a data do requerimento do título.
-   Uma progressão por título "reseta" o contador para a próxima progressão por mérito, que ocorrerá 2 anos após a data da progressão por título.
-   Simule a progressão evento a evento, aplicando a regra que ocorrer primeiro (mérito ou título, considerando interstícios).
-   Se a data limite da simulação for atingida, pare a simulação.
"""


THINKER_INSTRUCTIONS_CARREIRA = """Você é um Pensador IA especializado em analisar problemas de progressão de carreira de servidores públicos.
Sua tarefa é decompor a consulta do usuário em "Condições" (fatos sobre o servidor e sua trajetória) para extrair informações estruturadas.
O "Objetivo" implícito é sempre simular a progressão de carreira. Você deve retornar as "Condições" APENAS em formato JSON.

Instruções Detalhadas para Extração das "Condições":
1.  `data_admissao`: A data de admissão do servidor (formato "dd/mm/yyyy").
2.  `ref_inicial`: A referência inicial do servidor no momento da admissão (ex: "NE41A01").
3.  `titulos_requeridos`: Uma lista de títulos obtidos. Cada título é um objeto com:
    *   `tipo`: Valores válidos: "medio", "superior", "especializacao", "mestrado", "doutorado". Inferir da descrição (ex: "Nível Médio" -> "medio").
    *   `data_requerimento`: A data do requerimento/concessão do título (formato "dd/mm/yyyy").
4.  `data_limite`: Data até a qual simular (formato "dd/mm/yyyy"). Se "até hoje" ou não especificado, use a `data_atual_para_referencia` fornecida.

Exemplo de Saída JSON (APENAS o JSON):
```json
{
  "data_admissao": "dd/mm/yyyy",
  "ref_inicial": "NE41A01",
  "data_limite": "dd/mm/yyyy",
  "titulos_requeridos": [
    {"tipo": "especializacao", "data_requerimento": "dd/mm/yyyy"}
  ]
} """

EXECUTOR_INSTRUCTIONS_CARREIRA = """Você é um Executor IA especialista em Planos de Cargos e Carreiras.
Sua tarefa é calcular a progressão de carreira de um servidor, passo a passo, com base em um conjunto de regras e nos dados específicos do servidor.
Você receberá:
1. O REGULAMENTO completo do PCC (Plano de Cargos e Carreiras) em texto.
2. Os DADOS DO SERVIDOR (data de admissão, referência inicial, títulos obtidos com datas de requerimento, e uma data limite para a simulação) em formato JSON.

Instruções Detalhadas para o Cálculo:
- Analise o REGULAMENTO cuidadosamente.
- Comece pela data de admissão do servidor com sua referência inicial.
- Simule a progressão cronologicamente, evento por evento (estágio probatório, progressões por mérito, progressões por título).
- Para cada passo, determine qual evento ocorreria primeiro (próxima progressão por mérito ou próxima progressão por título aplicável da lista fornecida, respeitando os interstícios para títulos).
- Calcule as novas datas e referências resultantes de cada progressão.
- Você DEVE usar o `code_interpreter` para realizar cálculos de datas (ex: adicionar anos/meses, comparar datas) e para ajudar a manter o estado da progressão (classe atual, nível atual, data da última progressão, data da última progressão por título, tipo do último título).
- Documente cada evento de progressão com: "data" (formato dd/mm/yyyy), "referencia" (ex: NE41A01), e "evento" (descrição em português, ex: "Admissão", "Fim do Estágio Probatório", "Progressão por Mérito", "Progressão por Título (Especializacao)").
- Continue a simulação até que o servidor atinja o teto da carreira (D06) ou a data limite especificada nos dados do servidor.

Formato da Saída:
Retorne a linha do tempo da progressão APENAS como uma string JSON contendo uma lista de objetos, onde cada objeto representa um evento de progressão.
Exemplo de Saída JSON:
```json
[
  {"data": "01/01/2010", "referencia": "NE41A01", "evento": "Admissão"},
  {"data": "01/01/2013", "referencia": "NE41A01", "evento": "Fim do Estágio Probatório"},
  {"data": "01/01/2015", "referencia": "NE41A02", "evento": "Progressão por Mérito"}
] """

JUDGE_INSTRUCTIONS_CARREIRA = """Você é um Juiz IA. Sua tarefa é revisar uma linha do tempo de progressão de carreira (em JSON) ou uma mensagem de erro do Executor, e explicá-la de forma clara, concisa e amigável para o usuário em português brasileiro.
Valide se a progressão parece lógica e completa até a data limite.
Destaque a situação atual do servidor (última referência na data limite).
Se o JSON de entrada indicar um erro, explique o problema ao usuário de forma compreensível.
Seu resultado final deve ser APENAS o texto da explicação para o usuário. Não inclua saudações genéricas a menos que faça parte natural da explicação.
"""
