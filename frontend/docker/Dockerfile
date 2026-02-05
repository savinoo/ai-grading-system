FROM node:20-alpine

WORKDIR /app

# Copia apenas manifests primeiro (cache)
COPY package*.json ./
# Se você usa pnpm/yarn, me avisa que ajusto
RUN npm ci

# Agora copia o resto
COPY . .

# Vite precisa expor a porta (padrão 5173)
EXPOSE 5173

# Importante: host 0.0.0.0 para aceitar conexões fora do container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
