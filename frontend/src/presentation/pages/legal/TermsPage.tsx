import React from 'react';
import { Link } from 'react-router-dom';
import { AuthLayout } from '@presentation/components/layout/AuthLayout';

export const TermsPage: React.FC = () => {
  return (
    <AuthLayout>
      <div className="w-full max-w-4xl">
        <div className="bg-white dark:bg-slate-900/50 backdrop-blur-sm border border-slate-200 dark:border-slate-800 rounded-xl shadow-xl shadow-slate-200/50 dark:shadow-none p-8 md:p-12">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-slate-900 dark:text-white text-4xl font-extrabold leading-tight mb-3">
              Termos de Serviço
            </h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm">
              Última atualização: {new Date().toLocaleDateString('pt-BR')}
            </p>
          </div>

          {/* Content */}
          <div className="prose prose-slate dark:prose-invert max-w-none space-y-6 text-slate-700 dark:text-slate-300">
            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">1. Aceitação dos Termos</h2>
              <p>
                Ao acessar e usar o Corretum AI, você concorda em cumprir e estar vinculado aos seguintes termos e condições de uso. 
                Se você não concordar com alguma parte destes termos, não deve usar nossa plataforma.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">2. Descrição do Serviço</h2>
              <p>
                O Corretum AI é uma plataforma de correção automática de provas utilizando inteligência artificial, 
                destinada a instituições educacionais, professores e estudantes. O serviço inclui:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Criação e gerenciamento de provas</li>
                <li>Correção automática usando IA</li>
                <li>Gestão de turmas e alunos</li>
                <li>Geração de relatórios e análises</li>
                <li>Feedback personalizado para estudantes</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">3. Registro e Conta de Usuário</h2>
              <p>Para usar nossos serviços, você deve:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Fornecer informações verdadeiras, precisas e completas durante o registro</li>
                <li>Manter a segurança de sua senha e conta</li>
                <li>Notificar-nos imediatamente sobre qualquer uso não autorizado de sua conta</li>
                <li>Ser responsável por todas as atividades que ocorrem sob sua conta</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">4. Uso Aceitável</h2>
              <p>Você concorda em NÃO:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Usar o serviço para qualquer propósito ilegal ou não autorizado</li>
                <li>Violar qualquer lei local, estadual, nacional ou internacional</li>
                <li>Transmitir vírus, malware ou qualquer código malicioso</li>
                <li>Interferir ou interromper o serviço ou servidores conectados ao serviço</li>
                <li>Coletar ou armazenar dados pessoais de outros usuários sem autorização</li>
                <li>Usar o serviço para fins comerciais sem autorização expressa</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">5. Propriedade Intelectual</h2>
              <p>
                Todo o conteúdo da plataforma, incluindo mas não limitado a texto, gráficos, logotipos, ícones, 
                imagens, clipes de áudio, downloads digitais e software, é propriedade do Corretum AI ou de seus 
                fornecedores de conteúdo e está protegido por leis de direitos autorais.
              </p>
              <p className="mt-4">
                Você mantém todos os direitos sobre o conteúdo que enviar para a plataforma (provas, respostas, etc.), 
                mas concede ao Corretum AI uma licença não exclusiva para processar e analisar esse conteúdo para 
                fornecer os serviços.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">6. Privacidade e Proteção de Dados</h2>
              <p>
                O uso de suas informações pessoais é regido por nossa{' '}
                <Link to="/privacy" className="text-primary dark:text-primary-light font-bold hover:underline">
                  Política de Privacidade
                </Link>
                . Estamos comprometidos com a proteção de dados conforme a Lei Geral de Proteção de Dados (LGPD).
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">7. Limitação de Responsabilidade</h2>
              <p>
                O Corretum AI é fornecido "como está" e "conforme disponível". Não garantimos que o serviço será 
                ininterrupto, livre de erros ou completamente seguro. Em nenhuma circunstância seremos responsáveis por:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Danos diretos, indiretos, incidentais ou consequenciais</li>
                <li>Perda de dados ou lucros</li>
                <li>Interrupção de negócios</li>
                <li>Resultados da análise de IA (as avaliações devem ser revisadas por humanos)</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">8. Modificações do Serviço</h2>
              <p>
                Reservamo-nos o direito de modificar ou descontinuar, temporária ou permanentemente, o serviço 
                (ou qualquer parte dele) com ou sem aviso prévio. Não seremos responsáveis perante você ou terceiros 
                por qualquer modificação, suspensão ou descontinuação do serviço.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">9. Rescisão</h2>
              <p>
                Podemos rescindir ou suspender sua conta e acesso ao serviço imediatamente, sem aviso prévio, 
                por conduta que acreditamos violar estes Termos de Serviço ou ser prejudicial a outros usuários, 
                a nós ou a terceiros, ou por qualquer outro motivo.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">10. Lei Aplicável</h2>
              <p>
                Estes Termos serão regidos e interpretados de acordo com as leis do Brasil, sem considerar 
                conflitos de disposições legais.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">11. Alterações aos Termos</h2>
              <p>
                Reservamo-nos o direito de modificar estes termos a qualquer momento. Notificaremos você sobre 
                quaisquer alterações publicando os novos Termos de Serviço nesta página e atualizando a data de 
                "Última atualização" acima.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">12. Contato</h2>
              <p>
                Se você tiver alguma dúvida sobre estes Termos de Serviço, entre em contato conosco através do 
                email: <a href="mailto:suporte@corretum.ai" className="text-primary dark:text-primary-light font-bold hover:underline">suporte@corretum.ai</a>
              </p>
            </section>
          </div>

          {/* Footer */}
          <div className="mt-12 pt-8 border-t border-slate-200 dark:border-slate-800">
            <Link
              to="/login"
              className="inline-flex items-center gap-2 text-primary dark:text-primary-light font-bold hover:underline"
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
