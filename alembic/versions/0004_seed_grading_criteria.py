"""seed grading criteria

Revision ID: e076ff9c7204
Revises: 0003_add_triggers
Create Date: 2026-02-06 18:00:33.357554

"""
from alembic import op

revision = "0004_seed_grading_criteria"
down_revision = "0003_add_triggers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    INSERT INTO public.grading_criteria (code, name, description, active)
    VALUES
      ('CLAREZA', 'Clareza e objetividade', 'Avalia se a resposta é clara, objetiva e fácil de compreender.', TRUE),
      ('COERENCIA', 'Coerência e coesão textual', 'Avalia a organização das ideias e a conexão lógica entre as partes do texto.', TRUE),
      ('COMPLETUDE', 'Completude da resposta', 'Avalia se todos os pontos solicitados foram abordados de forma adequada.', TRUE),
      ('CORRECAO_TECNICA', 'Correção técnica', 'Avalia a precisão conceitual e a ausência de erros técnicos.', TRUE),
      ('ARGUMENTACAO', 'Argumentação e justificativa', 'Avalia a qualidade das justificativas, fundamentação e consistência dos argumentos.', TRUE),
      ('ESTRUTURA', 'Estrutura e organização', 'Avalia a estrutura do texto e a organização geral da resposta.', TRUE),
      ('GRAMATICA', 'Ortografia e gramática', 'Avalia aspectos gramaticais e ortográficos (quando aplicável).', TRUE),
      ('EXEMPLOS', 'Uso de exemplos', 'Avalia se a resposta utiliza exemplos relevantes para sustentar a explicação (quando aplicável).', TRUE),

      ('ADEQUACAO_ENUNCIADO', 'Atendimento ao enunciado', 'Avalia se a resposta atende exatamente ao que foi pedido (comando, recortes, restrições e formato).', TRUE),
      ('TESE_IDEIA_CENTRAL', 'Tese / ideia central', 'Avalia se há uma ideia central ou tese claramente formulada, orientando o texto (quando aplicável).', TRUE),
      ('LINHA_DE_RACIOCINIO', 'Linha de raciocínio', 'Avalia se há encadeamento lógico consistente entre afirmações, passos e conclusões.', TRUE),
      ('EVIDENCIAS_FUNDAMENTACAO', 'Evidências e fundamentação', 'Avalia se sustenta afirmações com evidências (dados, conceitos, leis, teoremas, fontes) e explica a relevância delas (quando aplicável).', TRUE),
      ('INTERPRETACAO_INFORMACOES', 'Interpretação de informações', 'Avalia a capacidade de interpretar corretamente informações fornecidas (textos, gráficos, tabelas, enunciados, casos).', TRUE),
      ('REPERTORIO_CONTEXTUALIZACAO', 'Contextualização e repertório', 'Avalia a contextualização do tema e a mobilização pertinente de conhecimentos da área para desenvolver a resposta.', TRUE),

      ('PRECISAO_TERMINOLOGICA', 'Precisão terminológica', 'Avalia o uso correto de termos técnicos e definições, evitando ambiguidade ou imprecisão.', TRUE),
      ('CORRECAO_FATUAL', 'Correção factual', 'Avalia a veracidade de fatos, datas, conceitos e afirmações (quando verificável).', TRUE),
      ('CORRECAO_NUMERICA', 'Exatidão de cálculos e resultados', 'Avalia a correção de operações, unidades, estimativas e resultados numéricos (quando aplicável).', TRUE),

      ('METODOLOGIA_PROCEDIMENTOS', 'Metodologia / procedimentos', 'Avalia se o método, passos ou procedimento adotado são adequados e bem descritos (quando aplicável).', TRUE),
      ('ANALISE_CRITICA', 'Análise crítica e profundidade', 'Avalia se a resposta vai além do superficial, analisando causas, consequências, relações e implicações.', TRUE),
      ('CONTRAARGUMENTACAO', 'Consideração de contrapartes', 'Avalia se reconhece limitações, exceções ou perspectivas alternativas e as trata adequadamente (quando aplicável).', TRUE),

      ('SINTETIZACAO', 'Síntese', 'Avalia se consegue sintetizar as ideias essenciais sem perder precisão.', TRUE),
      ('CONCLUSAO_ENCAMINHAMENTO', 'Conclusão / encaminhamento', 'Avalia se fecha o raciocínio com conclusão coerente e/ou encaminhamentos (quando aplicável).', TRUE),
      ('SOLUCAO_VIABILIDADE', 'Solução e viabilidade', 'Avalia se propõe solução coerente e viável considerando restrições do problema (quando aplicável).', TRUE),

      ('ADEQUACAO_GENERO', 'Adequação ao gênero solicitado', 'Avalia se segue o gênero/formato pedido (parecer, relatório, estudo de caso, dissertação, resolução comentada etc.).', TRUE),
      ('REFERENCIAMENTO', 'Referências e atribuição de fontes', 'Avalia se cita/atribui fontes, normas ou obras quando a questão exigir (quando aplicável).', TRUE),
      ('ORIGINALIDADE_AUTENTICIDADE', 'Originalidade e autenticidade', 'Avalia se evita mera cópia/paráfrase do enunciado/material e apresenta elaboração própria (quando aplicável).', TRUE),
      ('LIMITACOES_ASSUNCOES', 'Limitações e suposições', 'Avalia se explicita suposições e limitações relevantes do raciocínio/modelo (quando aplicável).', TRUE),
      ('ETICA_E_SEGURANCA', 'Ética, segurança e conformidade', 'Avalia se respeita princípios éticos, segurança e normas/regulamentos do domínio (quando aplicável).', TRUE)

    ON CONFLICT (code) DO UPDATE
    SET
      name = EXCLUDED.name,
      description = EXCLUDED.description,
      active = EXCLUDED.active;

    """)


def downgrade() -> None:
    # opcional: remover apenas os seeded
    op.execute("""
    DELETE FROM public.grading_criteria
    WHERE code IN (
      'CLAREZA','COERENCIA','COMPLETUDE','CORRECAO_TECNICA',
      'ARGUMENTACAO','ESTRUTURA','GRAMATICA','EXEMPLOS',
      'ADEQUACAO_ENUNCIADO','TESE_IDEIA_CENTRAL','LINHA_DE_RACIOCINIO','EVIDENCIAS_FUNDAMENTACAO','INTERPRETACAO_INFORMACOES','REPERTORIO_CONTEXTUALIZACAO',
      'PRECISAO_TERMINOLOGICA','CORRECAO_FATUAL','CORRECAO_NUMERICA',
      'METODOLOGIA_PROCEDIMENTOS','ANALISE_CRITICA','CONTRAARGUMENTACAO',
      'SINTETIZACAO','CONCLUSAO_ENCAMINHAMENTO','SOLUCAO_VIABILIDADE',
      'ADEQUACAO_GENERO','REFERENCIAMENTO','ORIGINALIDADE_AUTENTICIDADE','LIMITACOES_ASSUNCOES','ETICA_E_SEGURANCA'
    );
    """)
