// 🧪 TESTE RÁPIDO - Delete este arquivo depois de testar

import apiClient from './apiClient';

console.log('✅ apiClient importado com sucesso:', apiClient);
console.log('✅ apiClient tem método get?', typeof apiClient.get === 'function');
console.log('✅ apiClient tem método post?', typeof apiClient.post === 'function');

export const testImport = () => {
  console.log('🟢 Test import funcionando!');
};
