# Como Adicionar Novas Features

Este guia mostra como adicionar novas funcionalidades ao projeto seguindo Clean Architecture e SOLID.

## 📋 Checklist para Nova Feature

- [ ] 1. Definir entidades de domínio
- [ ] 2. Criar interfaces de repositório
- [ ] 3. Implementar casos de uso
- [ ] 4. Implementar repositórios
- [ ] 5. Criar hooks/stores
- [ ] 6. Criar componentes UI
- [ ] 7. Adicionar rotas (se necessário)

## 🎯 Exemplo Prático: Adicionar Gestão de Provas

### Passo 1: Entidades de Domínio

```typescript
// src/domain/entities/Exam.ts
export interface Exam {
  id: string;
  title: string;
  classId: string;
  createdAt: Date;
  totalScore: number;
  status: 'draft' | 'active' | 'completed';
  questions: Question[];
}

export interface Question {
  id: string;
  examId: string;
  text: string;
  maxScore: number;
  rubric: string;
}
```

### Passo 2: Interface de Repositório

```typescript
// src/domain/repositories/IExamRepository.ts
import { Exam } from '@domain/entities/Exam';

export interface IExamRepository {
  getAll(): Promise<Exam[]>;
  getById(id: string): Promise<Exam>;
  create(exam: Omit<Exam, 'id'>): Promise<Exam>;
  update(id: string, exam: Partial<Exam>): Promise<Exam>;
  delete(id: string): Promise<void>;
}
```

### Passo 3: Casos de Uso

```typescript
// src/application/use-cases/exam/CreateExamUseCase.ts
import { IExamRepository } from '@domain/repositories/IExamRepository';
import { Exam } from '@domain/entities/Exam';

export class CreateExamUseCase {
  constructor(private examRepository: IExamRepository) {}

  async execute(examData: Omit<Exam, 'id'>): Promise<Exam> {
    // Validações
    this.validateExamData(examData);

    // Lógica de negócio
    const exam = await this.examRepository.create(examData);
    
    return exam;
  }

  private validateExamData(data: Omit<Exam, 'id'>): void {
    if (!data.title || data.title.trim().length === 0) {
      throw new Error('Título da prova é obrigatório');
    }

    if (data.totalScore <= 0) {
      throw new Error('Pontuação total deve ser maior que zero');
    }

    if (!data.questions || data.questions.length === 0) {
      throw new Error('Prova deve ter pelo menos uma questão');
    }
  }
}
```

```typescript
// src/application/use-cases/exam/GetAllExamsUseCase.ts
import { IExamRepository } from '@domain/repositories/IExamRepository';
import { Exam } from '@domain/entities/Exam';

export class GetAllExamsUseCase {
  constructor(private examRepository: IExamRepository) {}

  async execute(): Promise<Exam[]> {
    return await this.examRepository.getAll();
  }
}
```

### Passo 4: Implementação do Repositório

```typescript
// src/infrastructure/repositories/ExamRepository.ts
import { IExamRepository } from '@domain/repositories/IExamRepository';
import { Exam } from '@domain/entities/Exam';
import { HttpClient } from '@infrastructure/http/HttpClient';

export class ExamRepository implements IExamRepository {
  constructor(private httpClient: HttpClient) {}

  async getAll(): Promise<Exam[]> {
    const response = await this.httpClient.getClient().get<Exam[]>('/exams');
    return response.data;
  }

  async getById(id: string): Promise<Exam> {
    const response = await this.httpClient.getClient().get<Exam>(`/exams/${id}`);
    return response.data;
  }

  async create(exam: Omit<Exam, 'id'>): Promise<Exam> {
    const response = await this.httpClient.getClient().post<Exam>('/exams', exam);
    return response.data;
  }

  async update(id: string, exam: Partial<Exam>): Promise<Exam> {
    const response = await this.httpClient.getClient().put<Exam>(`/exams/${id}`, exam);
    return response.data;
  }

  async delete(id: string): Promise<void> {
    await this.httpClient.getClient().delete(`/exams/${id}`);
  }
}
```

### Passo 5: Store/Hook

```typescript
// src/presentation/store/examStore.ts
import { create } from 'zustand';
import { Exam } from '@domain/entities/Exam';

interface ExamState {
  exams: Exam[];
  currentExam: Exam | null;
  isLoading: boolean;
  error: string | null;
  setExams: (exams: Exam[]) => void;
  setCurrentExam: (exam: Exam | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useExamStore = create<ExamState>((set) => ({
  exams: [],
  currentExam: null,
  isLoading: false,
  error: null,
  setExams: (exams) => set({ exams }),
  setCurrentExam: (exam) => set({ currentExam: exam }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
}));
```

```typescript
// src/presentation/hooks/useExam.ts
import { useCallback } from 'react';
import { useExamStore } from '@presentation/store/examStore';
import { CreateExamUseCase } from '@application/use-cases/exam/CreateExamUseCase';
import { GetAllExamsUseCase } from '@application/use-cases/exam/GetAllExamsUseCase';
import { ExamRepository } from '@infrastructure/repositories/ExamRepository';
import { HttpClient } from '@infrastructure/http/HttpClient';
import { LocalStorageService } from '@infrastructure/services/LocalStorageService';
import { Exam } from '@domain/entities/Exam';

// Dependency Injection
const storageService = new LocalStorageService();
const httpClient = new HttpClient(storageService);
const examRepository = new ExamRepository(httpClient);

const createExamUseCase = new CreateExamUseCase(examRepository);
const getAllExamsUseCase = new GetAllExamsUseCase(examRepository);

export const useExam = () => {
  const { exams, currentExam, isLoading, error, setExams, setCurrentExam, setLoading, setError } = useExamStore();

  const loadExams = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const exams = await getAllExamsUseCase.execute();
      setExams(exams);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro ao carregar provas';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [setExams, setLoading, setError]);

  const createExam = useCallback(async (examData: Omit<Exam, 'id'>) => {
    try {
      setLoading(true);
      setError(null);
      const exam = await createExamUseCase.execute(examData);
      setExams([...exams, exam]);
      return exam;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro ao criar prova';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [exams, setExams, setLoading, setError]);

  return {
    exams,
    currentExam,
    isLoading,
    error,
    loadExams,
    createExam,
    setCurrentExam,
  };
};
```

### Passo 6: Componentes UI

```typescript
// src/presentation/pages/exam/ExamListPage.tsx
import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useExam } from '@presentation/hooks/useExam';
import { Button } from '@presentation/components/ui/Button';

export const ExamListPage: React.FC = () => {
  const navigate = useNavigate();
  const { exams, isLoading, error, loadExams } = useExam();

  useEffect(() => {
    loadExams();
  }, [loadExams]);

  if (isLoading) {
    return <div>Carregando...</div>;
  }

  if (error) {
    return <div>Erro: {error}</div>;
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Gestão de Provas</h1>
        <Button onClick={() => navigate('/exams/create')}>
          <span className="material-symbols-outlined">add</span>
          Nova Prova
        </Button>
      </div>

      <div className="grid gap-4">
        {exams.map((exam) => (
          <div key={exam.id} className="border rounded-lg p-4">
            <h3 className="font-bold">{exam.title}</h3>
            <p className="text-sm text-gray-500">
              Status: {exam.status}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
```

### Passo 7: Adicionar Rotas

```typescript
// src/presentation/routes/index.tsx
import { ExamListPage } from '@presentation/pages/exam/ExamListPage';
import { CreateExamPage } from '@presentation/pages/exam/CreateExamPage';

// Adicionar nas rotas privadas
<Route element={<PrivateRoute />}>
  <Route path="/dashboard" element={<DashboardPage />} />
  <Route path="/exams" element={<ExamListPage />} />
  <Route path="/exams/create" element={<CreateExamPage />} />
</Route>
```

## 🎨 Padrão de Nomenclatura

### Entidades
- PascalCase
- Singular
- Exemplo: `User`, `Exam`, `Question`

### Interfaces
- PascalCase com prefixo `I`
- Exemplo: `IAuthRepository`, `IExamRepository`

### Use Cases
- PascalCase + sufixo `UseCase`
- Verbo + Substantivo
- Exemplo: `CreateExamUseCase`, `GetAllExamsUseCase`

### Repositories
- PascalCase + sufixo `Repository`
- Exemplo: `AuthRepository`, `ExamRepository`

### Hooks
- camelCase com prefixo `use`
- Exemplo: `useAuth`, `useExam`

### Stores
- camelCase com sufixo `Store`
- Exemplo: `authStore`, `examStore`

### Componentes
- PascalCase
- Sufixo indica tipo: `Page`, `Layout`, `Modal`, etc.
- Exemplo: `LoginPage`, `AuthLayout`, `ConfirmModal`

## 🔍 Validações

### No Use Case (lógica de negócio)
```typescript
class CreateExamUseCase {
  private validateExamData(data: Omit<Exam, 'id'>): void {
    if (!data.title || data.title.trim().length === 0) {
      throw new Error('Título da prova é obrigatório');
    }
  }
}
```

### No Componente (validação de formulário)
```typescript
const [errors, setErrors] = useState({});

const validate = () => {
  const newErrors = {};
  if (!formData.title) {
    newErrors.title = 'Título é obrigatório';
  }
  setErrors(newErrors);
  return Object.keys(newErrors).length === 0;
};
```

## 🧪 Testabilidade

### Testando Use Cases
```typescript
describe('CreateExamUseCase', () => {
  it('should create exam with valid data', async () => {
    const mockRepository = {
      create: jest.fn().mockResolvedValue(mockExam),
    };
    const useCase = new CreateExamUseCase(mockRepository);
    
    const result = await useCase.execute(validExamData);
    
    expect(result).toEqual(mockExam);
    expect(mockRepository.create).toHaveBeenCalledWith(validExamData);
  });
});
```

## 📝 Checklist de Qualidade

Antes de considerar a feature completa:

- [ ] Entidades bem definidas com tipos TypeScript
- [ ] Interface de repositório criada
- [ ] Use cases implementados com validações
- [ ] Repositório implementa a interface corretamente
- [ ] Hook criado para uso nos componentes
- [ ] Componentes seguem padrão do projeto
- [ ] Rotas configuradas (se necessário)
- [ ] Tratamento de erros implementado
- [ ] Loading states implementados
- [ ] Código documentado (comentários quando necessário)
- [ ] Código segue princípios SOLID
- [ ] Não há dependências circulares
- [ ] Types são exportados e reutilizados

## 🚀 Dicas Importantes

1. **Sempre comece pelo domínio**: Defina entidades primeiro
2. **Use Cases são independentes**: Não devem depender de framework
3. **Repositories implementam interfaces**: Facilita testes e troca de implementação
4. **Hooks são a ponte**: Conectam UI com casos de uso
5. **Componentes são burros**: Apenas renderizam e disparam ações
6. **Valide em múltiplas camadas**: UI (UX) e Use Case (Regras de negócio)
7. **Trate erros apropriadamente**: Diferentes camadas, diferentes tratamentos
8. **Mantenha a separação**: Camadas não devem se misturar

## 🎯 Próximas Features Sugeridas

1. **Gestão de Turmas**
   - Criar turma
   - Listar alunos
   - Importar alunos (CSV)

2. **Correção com IA**
   - Upload de respostas
   - Análise automática
   - Feedback personalizado

3. **Relatórios**
   - Dashboard de estatísticas
   - Exportação de dados
   - Gráficos de desempenho

4. **Perfil do Usuário**
   - Editar dados
   - Trocar senha
   - Configurações
