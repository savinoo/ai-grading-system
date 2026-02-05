# Corretum AI - Frontend

Sistema de correção automática de provas com IA aplicada à educação.

## 🚀 Tecnologias

- **React** 18.2
- **TypeScript** 5.3
- **Vite** 5.0
- **Tailwind CSS** 3.4
- **React Router** 6.21
- **Zustand** (gerenciamento de estado)
- **Axios** (requisições HTTP)

## 🏗️ Arquitetura

Este projeto segue os princípios de **Clean Architecture** e **SOLID**:

```
src/
├── domain/              # Camada de Domínio (Entidades, Interfaces)
│   ├── entities/       # Entidades de negócio
│   ├── repositories/   # Interfaces de repositórios
│   └── services/       # Interfaces de serviços
│
├── application/        # Camada de Aplicação (Casos de Uso)
│   └── use-cases/     # Lógica de negócio
│
├── infrastructure/     # Camada de Infraestrutura
│   ├── http/          # Cliente HTTP
│   ├── repositories/  # Implementações de repositórios
│   └── services/      # Implementações de serviços
│
├── presentation/       # Camada de Apresentação (UI)
│   ├── components/    # Componentes React
│   ├── pages/         # Páginas
│   ├── hooks/         # Custom hooks
│   ├── store/         # Estado global
│   └── routes/        # Configuração de rotas
│
└── shared/            # Código compartilhado
    ├── constants/     # Constantes
    └── utils/         # Utilitários
```

## 📦 Instalação

```bash
# Instalar dependências
npm install

# Copiar arquivo de ambiente
cp .env.example .env

# Configurar a URL da API no .env
VITE_API_BASE_URL=http://localhost:8000/api
```

## 🔧 Desenvolvimento

```bash
# Rodar servidor de desenvolvimento
npm run dev

# Build para produção
npm run build

# Preview da build
npm run preview

# Lint
npm run lint
```

## 🎨 Princípios SOLID Aplicados

- **S**ingle Responsibility: Cada classe/módulo tem uma única responsabilidade
- **O**pen/Closed: Aberto para extensão, fechado para modificação
- **L**iskov Substitution: Implementações podem substituir abstrações
- **I**nterface Segregation: Interfaces específicas ao invés de genéricas
- **D**ependency Inversion: Dependência de abstrações, não de implementações

## 📝 Estrutura de Features

Cada feature segue o padrão:
1. **Entidade de Domínio** - Define a estrutura de dados
2. **Interface de Repositório** - Define o contrato de acesso aos dados
3. **Caso de Uso** - Implementa a lógica de negócio
4. **Repositório** - Implementa a comunicação com a API
5. **Hook/Store** - Gerencia estado e fornece interface para UI
6. **Componentes** - Interface visual

## 🔐 Autenticação

O sistema utiliza JWT tokens com refresh token automático. A autenticação é gerenciada pelo:
- `LoginUseCase` - Lógica de login
- `AuthRepository` - Comunicação com API
- `useAuth` hook - Interface para componentes
- `PrivateRoute` - Proteção de rotas

## 🎯 Próximos Passos

- [ ] Implementar Dashboard
- [ ] Criar módulo de Gestão de Provas
- [ ] Implementar módulo de Turmas
- [ ] Adicionar módulo de Correção com IA
- [ ] Implementar Relatórios e Analytics

## 📄 Licença

Este projeto está sob licença privada.
