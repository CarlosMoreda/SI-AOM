export const MENU_ITEMS = [
  { key: 'dashboard', label: 'Dashboard', section: 'Geral' },
  { key: 'clientes', label: 'Clientes', section: 'Planeamento' },
  { key: 'projetos', label: 'Projetos', section: 'Planeamento' },
  { key: 'orcamentos', label: 'Orçamentos', section: 'Planeamento' },
  { key: 'materiais', label: 'Materiais', section: 'Catálogo' },
  { key: 'operacoes', label: 'Operações', section: 'Catálogo' },
  { key: 'servicos', label: 'Serviços', section: 'Catálogo' },
  { key: 'realizado', label: 'Realizado', section: 'Execução' },
  { key: 'comparacao', label: 'Comparação', section: 'Análise' },
  { key: 'ml', label: 'ML', section: 'Análise' },
  { key: 'utilizadores', label: 'Utilizadores', section: 'Admin' },
  { key: 'definicoes', label: 'Definições', section: 'Admin' },
]

export const SECTION_ORDER = ['Geral', 'Planeamento', 'Catálogo', 'Execução', 'Análise', 'Admin']

const ROLE_ALIASES = {
  admin: 'administrador',
  administrator: 'administrador',
  administracao: 'administrador',
  administrador: 'administrador',
  orcamentacao: 'orcamentista',
  orcamentista: 'orcamentista',
  producao: 'producao',
  gestao: 'gestor',
  gestor: 'gestor',
}

const MENU_PERMISSIONS = {
  administrador: MENU_ITEMS.map((item) => item.key),
  orcamentista: [
    'dashboard',
    'clientes',
    'projetos',
    'orcamentos',
    'materiais',
    'operacoes',
    'servicos',
    'comparacao',
    'ml',
    'definicoes',
  ],
  gestor: ['dashboard', 'clientes', 'projetos', 'orcamentos', 'comparacao', 'ml', 'definicoes'],
  producao: ['realizado', 'comparacao', 'definicoes'],
}

export function normalizePerfil(perfil) {
  const key = String(perfil || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase()
    .replaceAll('-', '_')
    .replaceAll(' ', '_')

  return ROLE_ALIASES[key] || key
}

export function getVisibleMenuItems(perfil) {
  const role = normalizePerfil(perfil)
  const allowed = MENU_PERMISSIONS[role] || ['definicoes']
  const allowedSet = new Set(allowed)
  return MENU_ITEMS.filter((item) => allowedSet.has(item.key))
}
