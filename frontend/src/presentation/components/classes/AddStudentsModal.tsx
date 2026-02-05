import React, { useState } from 'react';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { AddStudentsDTO } from '@domain/entities/Class';

interface AddStudentsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: AddStudentsDTO) => Promise<void>;
  classUuid: string;
}

interface StudentInput {
  id: number;
  full_name: string;
  email: string;
}

export const AddStudentsModal: React.FC<AddStudentsModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [students, setStudents] = useState<StudentInput[]>([
    { id: 1, full_name: '', email: '' },
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  if (!isOpen) return null;

  const addStudentField = () => {
    const newId = Math.max(...students.map(s => s.id)) + 1;
    setStudents([...students, { id: newId, full_name: '', email: '' }]);
  };

  const removeStudentField = (id: number) => {
    if (students.length > 1) {
      setStudents(students.filter(s => s.id !== id));
    }
  };

  const updateStudent = (id: number, field: 'full_name' | 'email', value: string) => {
    setStudents(students.map(s => 
      s.id === id ? { ...s, [field]: value } : s
    ));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    // Validação de email no frontend
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    for (const student of students) {
      if (student.email.trim() && !emailRegex.test(student.email.trim())) {
        setValidationError(`Email inválido: ${student.email}. Use um formato válido como exemplo@dominio.com`);
        return;
      }
    }

    setIsSubmitting(true);

    try {
      const data: AddStudentsDTO = {
        students: students
          .filter(s => s.full_name.trim() !== '')
          .map(s => ({
            full_name: s.full_name.trim(),
            ...(s.email.trim() && { email: s.email.trim() }),
          })),
      };

      await onSubmit(data);
      setStudents([{ id: 1, full_name: '', email: '' }]);
      setValidationError(null);
      onClose();
    } catch (error) {
      // Error is handled by the parent component
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Adicionar Alunos</h2>

        {validationError && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
            {validationError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-3">
            {students.map((student, index) => (
              <div key={student.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-medium text-gray-700">Aluno {index + 1}</h3>
                  {students.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeStudentField(student.id)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      Remover
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <Input
                    label="Nome Completo"
                    type="text"
                    value={student.full_name}
                    onChange={(e) => updateStudent(student.id, 'full_name', e.target.value)}
                    placeholder="Ex: João Silva"
                    required
                  />

                  <Input
                    label="Email (opcional)"
                    type="email"
                    value={student.email}
                    onChange={(e) => updateStudent(student.id, 'email', e.target.value)}
                    placeholder="Ex: joao@exemplo.com"
                    pattern="[^\s@]+@[^\s@]+\.[^\s@]+"
                    title="Digite um email válido (ex: nome@dominio.com)"
                  />
                </div>
              </div>
            ))}
          </div>

          <Button
            type="button"
            onClick={addStudentField}
            variant="secondary"
            className="w-full"
          >
            + Adicionar Outro Aluno
          </Button>

          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              onClick={onClose}
              variant="secondary"
              className="flex-1"
              disabled={isSubmitting}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              variant="primary"
              className="flex-1"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Adicionando...' : 'Adicionar Alunos'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
