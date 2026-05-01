export const MENU_ITEMS = [
  { key: 'dashboard', label: 'Dashboard', section: 'Geral' },
  { key: 'clientes', label: 'Clientes', section: 'Planeamento' },
  { key: 'projetos', label: 'Projetos', section: 'Planeamento' },
  { key: 'orcamentos', label: 'Orcamentos', section: 'Planeamento' },
  { key: 'materiais', label: 'Materiais', section: 'Catalogo' },
  { key: 'operacoes', label: 'Operacoes', section: 'Catalogo' },
  { key: 'servicos', label: 'Servicos', section: 'Catalogo' },
  { key: 'realizado', label: 'Realizado', section: 'Execucao' },
  { key: 'comparacao', label: 'Comparacao', section: 'Analise' },
  { key: 'ml', label: 'ML', section: 'Analise' },
  { key: 'utilizadores', label: 'Utilizadores', section: 'Admin' },
  { key: 'definicoes', label: 'Definicoes', section: 'Admin' },
]

export const SECTION_ORDER = ['Geral', 'Planeamento', 'Catalogo', 'Execucao', 'Analise', 'Admin']

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
