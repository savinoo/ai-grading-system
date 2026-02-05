import React from 'react';
import { Class } from '@domain/entities/Class';
import { Button } from '../ui/Button';

interface ClassCardProps {
  classData: Class;
  onView: (classUuid: string) => void;
  onDeactivate?: (classUuid: string) => void;
}

export const ClassCard: React.FC<ClassCardProps> = ({ classData, onView, onDeactivate }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="mb-4">
        <h3 className="text-xl font-semibold text-gray-900 mb-2">{classData.name}</h3>
        <p className="text-gray-600 text-sm">{classData.description}</p>
      </div>
      
      <div className="flex items-center gap-4 mb-4 text-sm text-gray-500">
        <div className="flex items-center gap-1">
          <span className="font-medium">Ano:</span>
          <span>{classData.year}</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="font-medium">Semestre:</span>
          <span>{classData.semester}º</span>
        </div>
      </div>

      <div className="flex gap-2">
        <Button
          onClick={() => onView(classData.uuid)}
          variant="primary"
          className="flex-1"
        >
          Ver Detalhes
        </Button>
        {onDeactivate && (
          <Button
            onClick={() => onDeactivate(classData.uuid)}
            variant="secondary"
            className="px-4"
          >
            Desativar
          </Button>
        )}
      </div>
    </div>
  );
};
