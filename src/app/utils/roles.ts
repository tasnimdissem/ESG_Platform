export type Role = 'user' | 'metier' | 'decideur' | 'admin';

const ROLE_LABELS: Record<Role, string> = {
  user: 'Utilisateur métier',
  metier: 'Utilisateur métier',
  decideur: 'Décideur',
  admin: 'Administrateur',
};

const ADMIN_ROLE_ORDER: Role[] = ['metier', 'decideur', 'admin'];

export function getRoleLabel(role?: string | null): string {
  if (!role) return 'Utilisateur métier';
  return ROLE_LABELS[(role as Role)] ?? role;
}

export function getNextAdminRole(currentRole?: string | null): Role {
  const normalizedRole = currentRole === 'user' ? 'metier' : (currentRole as Role | undefined);
  const index = ADMIN_ROLE_ORDER.indexOf((normalizedRole as Role) ?? 'metier');
  const nextIndex = index === -1 ? 0 : (index + 1) % ADMIN_ROLE_ORDER.length;
  return ADMIN_ROLE_ORDER[nextIndex];
}

export const REGISTER_ROLE_OPTIONS: Array<{ value: Exclude<Role, 'user' | 'admin'>; label: string }> = [
  { value: 'metier', label: 'Utilisateur métier' },
  { value: 'decideur', label: 'Décideur' },
];
