# Entrega do Reliability & Evaluation Lab

O case foi organizado em três experimentos reproduzíveis, aproveitando o código do TCC e os exports históricos. A entrega inclui dados desidentificados e versionados, dashboard Streamlit, relatório técnico em inglês, materiais de anotação humana e testes integrados do fluxo real com provedores simulados.

## O que os dados mostram

- **Reliability & Agreement:** no QA4 JSON, 36 correções de 12 casos apresentam divergência média de 0,344 ponto entre examinadores. As respostas fracas concentram a discordância: média de 1,014 ponto. A maior amplitude de nota final entre três runs é 0,625 ponto. O texto exato dessas respostas não foi salvo; a estabilidade é descritiva.
- **Segundo QA4, separado:** o notebook contém 12 correções de quatro respostas da questão Q2. A amplitude máxima registrada é 1,37 ponto. Há inconsistências nos campos de nota/divergência/consenso; esse resultado não foi misturado ao QA4 JSON.
- **Arbitragem:** no QA4 JSON, limiares estritos de 0,5 / 1,0 / 1,5 / 2,0 encaminhariam 8 / 3 / 1 / 0 correções. Outros experimentos contêm dez notas de árbitro observadas; o movimento médio absoluto da nota final frente à média C1/C2 é 1,9 ponto. Isso mede mudança de nota, sem demonstrar melhora de qualidade.
- **RAG:** quatro comparações têm 12 pares de material idêntico cada. Nenhuma satisfaz todos os controles de configuração necessários. Os JSONs não persistiram contextos; o notebook registra quatro trechos por caso, em escopo de questão. O dashboard permite inspecionar esses rastros. Variações de nota são descritivas e não provam benefício do RAG.

## O que foi preparado sem inventar evidência

Não foram encontradas notas humanas validadas nos materiais de estudo inspecionados. Por isso, não há acurácia, MAE contra humanos ou benefício humano-relativo atribuídos aos dados históricos.

Foram preparados 48 materiais distintos para anotação, com enunciado, rubrica e resposta, removendo notas dos modelos e nomes dos perfis. O protocolo prevê duas avaliações humanas independentes e adjudicação documentada. O pipeline valida procedência e identidade do material. Não há promessa de revisores humanos. Exemplos sintéticos ficam separados e não entram nas métricas de pesquisa.

Custo monetário, tokens e latência real de inferência permanecem indisponíveis quando não foram registrados. O tempo de rodar a análise offline não é apresentado como latência de LLM.

## Como apresentar o case

“Construí um laboratório de avaliação sobre um corretor multiagente existente. Congelei dados e rastros, medi concordância e instabilidade, encontrei lacunas que impedem conclusões de qualidade e implementei o caminho reproduzível para comparar arbitragem e RAG com referências humanas legítimas.”

O diferencial é demonstrar julgamento de pesquisa: saber quais comparações são válidas e quais conclusões os dados ainda não sustentam.

## Entrega e limites

O README contém os comandos para reproduzir a análise e abrir o dashboard local. O registro de validação apresenta os testes executados, resultados do CI e pendências. O scanner de segurança voltou a executar e seus achados continuam visíveis; o build fica bloqueado enquanto essa etapa falhar. Correções de segurança e deploy em produção ficaram fora do escopo. Nenhum merge na `main` foi realizado.
