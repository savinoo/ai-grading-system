import React from 'react';
import { Link } from 'react-router-dom';
import { AuthLayout } from '@presentation/components/layout/AuthLayout';

export const PrivacyPage: React.FC = () => {
  return (
    <AuthLayout>
      <div className="w-full max-w-4xl">
        <div className="bg-white dark:bg-slate-900/50 backdrop-blur-sm border border-slate-200 dark:border-slate-800 rounded-xl shadow-xl shadow-slate-200/50 dark:shadow-none p-8 md:p-12">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-slate-900 dark:text-white text-4xl font-extrabold leading-tight mb-3">
              Política de Privacidade
            </h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm">
              Última atualização: {new Date().toLocaleDateString('pt-BR')}
            </p>
          </div>

          {/* Content */}
          <div className="prose prose-slate dark:prose-invert max-w-none space-y-6 text-slate-700 dark:text-slate-300">
            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">1. Introdução</h2>
              <p>
                A Corretum AI está comprometida com a proteção da privacidade e dos dados pessoais de seus usuários. 
                Esta Política de Privacidade descreve como coletamos, usamos, armazenamos e protegemos suas informações 
                pessoais em conformidade com a Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018).
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">2. Informações que Coletamos</h2>
              
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mt-6 mb-3">2.1 Dados Pessoais Fornecidos por Você</h3>
              <ul className="list-disc pl-6 space-y-2">
                <li><strong>Dados de Cadastro:</strong> nome, email institucional, tipo de usuário (professor/aluno)</li>
                <li><strong>Dados Acadêmicos:</strong> informações sobre turmas, disciplinas e instituição de ensino</li>
                <li><strong>Conteúdo de Provas:</strong> perguntas, respostas e critérios de avaliação</li>
                <li><strong>Respostas de Alunos:</strong> conteúdo das respostas enviadas para correção</li>
              </ul>

              <h3 className="text-xl font-bold text-slate-900 dark:text-white mt-6 mb-3">2.2 Dados Coletados Automaticamente</h3>
              <ul className="list-disc pl-6 space-y-2">
                <li><strong>Dados de Uso:</strong> páginas visitadas, funcionalidades utilizadas, tempo de uso</li>
                <li><strong>Dados Técnicos:</strong> endereço IP, tipo de navegador, sistema operacional</li>
                <li><strong>Cookies:</strong> preferências do usuário, sessão de login</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">3. Como Usamos Suas Informações</h2>
              <p>Utilizamos suas informações pessoais para:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Fornecer, operar e manter nossos serviços de correção automática</li>
                <li>Processar e analisar respostas de provas usando inteligência artificial</li>
                <li>Gerar feedback personalizado e relatórios de desempenho</li>
                <li>Gerenciar sua conta e autenticação</li>
                <li>Comunicar atualizações, mudanças nos serviços e suporte técnico</li>
                <li>Melhorar nossos serviços e desenvolver novos recursos</li>
                <li>Garantir a segurança e prevenir fraudes</li>
                <li>Cumprir obrigações legais e regulatórias</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">4. Base Legal para Processamento</h2>
              <p>Processamos seus dados pessoais com base nas seguintes bases legais da LGPD:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li><strong>Execução de Contrato:</strong> necessário para fornecer os serviços contratados</li>
                <li><strong>Consentimento:</strong> para processamento de dados sensíveis e comunicações de marketing</li>
                <li><strong>Legítimo Interesse:</strong> para melhoria dos serviços e segurança da plataforma</li>
                <li><strong>Obrigação Legal:</strong> quando exigido por lei</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">5. Compartilhamento de Dados</h2>
              <p>Podemos compartilhar suas informações nas seguintes circunstâncias:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li><strong>Com sua Instituição:</strong> compartilhamos dados acadêmicos com a instituição de ensino vinculada</li>
                <li><strong>Provedores de Serviço:</strong> empresas que nos ajudam a operar a plataforma (hospedagem, IA, analytics)</li>
                <li><strong>Conformidade Legal:</strong> quando necessário para cumprir leis ou responder a processos legais</li>
                <li><strong>Proteção de Direitos:</strong> para proteger nossos direitos, propriedade ou segurança</li>
              </ul>
              <p className="mt-4">
                <strong>Importante:</strong> Nunca vendemos seus dados pessoais para terceiros.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">6. Armazenamento e Segurança</h2>
              <p>Implementamos medidas de segurança técnicas e organizacionais adequadas para proteger seus dados:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Criptografia de dados em trânsito (HTTPS/TLS) e em repouso</li>
                <li>Controles de acesso rigorosos e autenticação multifator</li>
                <li>Monitoramento contínuo de segurança</li>
                <li>Backups regulares e planos de recuperação de desastres</li>
                <li>Auditorias de segurança periódicas</li>
              </ul>
              <p className="mt-4">
                Seus dados são armazenados em servidores seguros no Brasil, em conformidade com a LGPD.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">7. Retenção de Dados</h2>
              <p>
                Mantemos seus dados pessoais apenas pelo tempo necessário para cumprir as finalidades descritas nesta política, 
                a menos que um período de retenção mais longo seja exigido ou permitido por lei.
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li><strong>Dados de Conta:</strong> enquanto sua conta estiver ativa</li>
                <li><strong>Dados Acadêmicos:</strong> conforme política da instituição de ensino</li>
                <li><strong>Logs de Acesso:</strong> até 6 meses</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">8. Seus Direitos (LGPD)</h2>
              <p>Você tem os seguintes direitos em relação aos seus dados pessoais:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li><strong>Confirmação e Acesso:</strong> saber se processamos seus dados e acessá-los</li>
                <li><strong>Correção:</strong> corrigir dados incompletos, inexatos ou desatualizados</li>
                <li><strong>Anonimização, Bloqueio ou Eliminação:</strong> de dados desnecessários ou excessivos</li>
                <li><strong>Portabilidade:</strong> receber seus dados em formato estruturado e interoperável</li>
                <li><strong>Eliminação:</strong> dos dados tratados com seu consentimento</li>
                <li><strong>Informação:</strong> sobre compartilhamento de dados com terceiros</li>
                <li><strong>Revogação do Consentimento:</strong> a qualquer momento</li>
                <li><strong>Oposição:</strong> ao tratamento de dados em certas circunstâncias</li>
              </ul>
              <p className="mt-4">
                Para exercer seus direitos, entre em contato através de:{' '}
                <a href="mailto:privacidade@corretum.ai" className="text-primary font-bold hover:underline">
                  privacidade@corretum.ai
                </a>
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">9. Cookies e Tecnologias Similares</h2>
              <p>Utilizamos cookies e tecnologias similares para:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Manter você conectado à sua conta</li>
                <li>Lembrar suas preferências</li>
                <li>Analisar o uso da plataforma</li>
                <li>Melhorar a experiência do usuário</li>
              </ul>
              <p className="mt-4">
                Você pode gerenciar cookies através das configurações do seu navegador.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">10. Menores de Idade</h2>
              <p>
                Nossa plataforma pode ser usada por alunos menores de 18 anos, mas apenas através de suas instituições 
                de ensino. Os pais ou responsáveis legais devem consentir com o uso da plataforma por menores.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">11. Transferência Internacional de Dados</h2>
              <p>
                Nossos dados são armazenados principalmente em servidores no Brasil. Caso seja necessária alguma 
                transferência internacional, garantimos que medidas adequadas de proteção sejam implementadas.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">12. Alterações a Esta Política</h2>
              <p>
                Podemos atualizar esta Política de Privacidade periodicamente. Notificaremos você sobre quaisquer 
                alterações significativas por email ou através de um aviso em nossa plataforma.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">13. Encarregado de Dados (DPO)</h2>
              <p>
                Para questões relacionadas à proteção de dados, entre em contato com nosso Encarregado de Proteção de Dados:
              </p>
              <ul className="list-none space-y-1 mt-4">
                <li><strong>Email:</strong> <a href="mailto:dpo@corretum.ai" className="text-primary font-bold hover:underline">dpo@corretum.ai</a></li>
                <li><strong>Endereço:</strong> [Endereço da empresa]</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">14. Contato</h2>
              <p>
                Para dúvidas sobre esta Política de Privacidade ou sobre o tratamento de seus dados pessoais:
              </p>
              <ul className="list-none space-y-1 mt-4">
                <li><strong>Email:</strong> <a href="mailto:privacidade@corretum.ai" className="text-primary font-bold hover:underline">privacidade@corretum.ai</a></li>
                <li><strong>Suporte:</strong> <a href="mailto:suporte@corretum.ai" className="text-primary font-bold hover:underline">suporte@corretum.ai</a></li>
              </ul>
            </section>
          </div>

          {/* Footer */}
          <div className="mt-12 pt-8 border-t border-slate-200 dark:border-slate-800">
            <Link
              to="/login"
              className="inline-flex items-center gap-2 text-primary font-bold hover:underline"
            >
              <span className="material-symbols-outlined text-lg">arrow_back</span>
              Voltar para o Login
            </Link>
          </div>
        </div>
      </div>
    </AuthLayout>
  );
};
