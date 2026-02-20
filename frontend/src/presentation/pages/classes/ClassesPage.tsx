import React, { useEffect, useState } from 'react';
import { DashboardLayout } from '@presentation/components/layout/DashboardLayout';

import { useClasses } from '@presentation/hooks/useClasses';
import { ClassCard } from '@presentation/components/classes/ClassCard';
import { CreateClassModal } from '@presentation/components/classes/CreateClassModal';
import { StudentList } from '@presentation/components/classes/StudentList';
import { AddStudentsModal } from '@presentation/components/classes/AddStudentsModal';
import { Button } from '@presentation/components/ui/Button';
import { ErrorAlert } from '@presentation/components/ui/ErrorAlert';

export const ClassesPage: React.FC = () => {
  const {
    classes,
    currentClass,
    isLoading,
    error,
    createClass,
    loadTeacherClasses,
    loadClassDetails,
    addStudents,
    removeStudent,
    deactivateClass,
    clearError,
    setCurrentClass,
  } = useClasses();

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isAddStudentsModalOpen, setIsAddStudentsModalOpen] = useState(false);
  const [viewMode, setViewMode] = useState<'list' | 'details'>('list');

  useEffect(() => {
    loadTeacherClasses().catch(err => {
      console.error('Erro ao carregar turmas:', err);
    });
  }, [loadTeacherClasses]);

  const handleViewClass = async (classUuid: string) => {
    try {
      await loadClassDetails(classUuid);
      setViewMode('details');
    } catch (error) {
      console.error('Erro ao visualizar turma:', error);
    }
  };

  const handleBackToList = () => {
    setCurrentClass(null);
    setViewMode('list');
  };

  const handleDeactivate = async (classUuid: string) => {
    if (window.confirm('Tem certeza que deseja desativar esta turma?')) {
      try {
        await deactivateClass(classUuid);
        if (viewMode === 'details') {
          handleBackToList();
        }
      } catch (error) {
        // Error is handled by the hook
      }
    }
  };

  const handleRemoveStudent = async (studentUuid: string) => {
    if (window.confirm('Tem certeza que deseja remover este aluno da turma?')) {
      if (currentClass) {
        try {
          await removeStudent(currentClass.uuid, studentUuid);
        } catch (error) {
          // Error is handled by the hook
        }
      }
    }
  };

  return (
    <DashboardLayout>
      <div className="p-8 max-w-7xl mx-auto">
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Gerenciar Turmas</h1>
              <p className="text-slate-500 dark:text-slate-400">Crie e gerencie suas turmas de alunos</p>
            </div>
            {viewMode === 'list' && (
              <Button onClick={() => setIsCreateModalOpen(true)} variant="primary">
                + Nova Turma
              </Button>
            )}
          </div>
        </div>
        {error && <ErrorAlert message={error} onClose={clearError} />}

        {viewMode === 'list' ? (
          // Lista de turmas
          <div>

            {isLoading ? (
              <div className="text-center py-12">
                <p className="text-gray-500 dark:text-slate-400">Carregando turmas...</p>
              </div>
            ) : classes.length === 0 ? (
              <div className="bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 p-12 text-center">
                <span className="material-symbols-outlined text-6xl text-gray-300 dark:text-slate-600 mb-4">
                  groups
                </span>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                  Nenhuma turma cadastrada
                </h3>
                <p className="text-gray-500 dark:text-slate-400 mb-4">
                  Comece criando sua primeira turma
                </p>
                <Button onClick={() => setIsCreateModalOpen(true)} variant="primary">
                  Criar Primeira Turma
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {classes.map((classData) => (
                  <ClassCard
                    key={classData.uuid}
                    classData={classData}
                    onView={handleViewClass}
                    onDeactivate={handleDeactivate}
                  />
                ))}
              </div>
            )}
          </div>
        ) : (
          // Detalhes da turma
          currentClass && (
            <div>
              <div className="mb-6">
                <Button
                  onClick={handleBackToList}
                  variant="secondary"
                  className="mb-4"
                >
                  ← Voltar para Turmas
                </Button>

                <div className="bg-white dark:bg-slate-800 border border-transparent dark:border-slate-700 rounded-lg shadow-md p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                        {currentClass.name}
                      </h2>
                      <p className="text-gray-600 dark:text-slate-400">{currentClass.description}</p>
                    </div>
                    <Button
                      onClick={() => handleDeactivate(currentClass.uuid)}
                      variant="secondary"
                    >
                      Desativar Turma
                    </Button>
                  </div>

                  <div className="flex gap-6 text-sm text-gray-600 dark:text-slate-400 mb-6">
                    <div>
                      <span className="font-medium">Ano:</span> {currentClass.year}
                    </div>
                    <div>
                      <span className="font-medium">Semestre:</span> {currentClass.semester}º
                    </div>
                    <div>
                      <span className="font-medium">Total de Alunos:</span>{' '}
                      {currentClass.total_students}
                    </div>
                  </div>

                  <div className="border-t border-slate-200 dark:border-slate-700 pt-6">
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="text-xl font-semibold text-gray-900 dark:text-white">Alunos</h3>
                      <Button
                        onClick={() => setIsAddStudentsModalOpen(true)}
                        variant="primary"
                      >
                        + Adicionar Alunos
                      </Button>
                    </div>

                    <StudentList
                      students={currentClass.students}
                      onRemove={handleRemoveStudent}
                      isLoading={isLoading}
                    />
                  </div>
                </div>
              </div>
            </div>
          )
        )}
      </div>

      <CreateClassModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={createClass}
      />

      {currentClass && (
        <AddStudentsModal
          isOpen={isAddStudentsModalOpen}
          onClose={() => setIsAddStudentsModalOpen(false)}
          onSubmit={(data) => addStudents(currentClass.uuid, data)}
          classUuid={currentClass.uuid}
        />
      )}
    </DashboardLayout>
  );
};
