import React from 'react';
import { Student } from '@domain/entities/Student';
import { Button } from '../ui/Button';

interface StudentListProps {
  students: Student[];
  onRemove: (studentUuid: string) => void;
  isLoading?: boolean;
}

export const StudentList: React.FC<StudentListProps> = ({ students, onRemove, isLoading }) => {
  if (students.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        Nenhum aluno cadastrado nesta turma.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {students.map((student) => (
        <div
          key={student.uuid}
          className="bg-white border border-gray-200 rounded-lg p-4 flex items-center justify-between hover:shadow-md transition-shadow"
        >
          <div className="flex-1">
            <h4 className="font-semibold text-gray-900">{student.full_name}</h4>
            <p className="text-sm text-gray-600">
              {student.email || 'Sem email cadastrado'}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Matriculado em: {new Date(student.enrolled_at).toLocaleDateString('pt-BR')}
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <span
              className={`px-3 py-1 rounded-full text-xs font-medium ${
                student.active
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
              }`}
            >
              {student.active ? 'Ativo' : 'Inativo'}
            </span>
            
            <Button
              onClick={() => onRemove(student.uuid)}
              variant="secondary"
              className="px-4 py-2 text-sm"
              disabled={isLoading}
            >
              Remover
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
};
