export type Role = 'user' | 'metier' | 'decideur' | 'admin' | 'non_attribue';

const ROLE_LABELS: Record<Role, string> = {
  user: 'Décideur',
  metier: 'Utilisateur métier',
  decideur: 'Décideur',
  admin: 'Administrateur',
  non_attribue: 'Rôle non attribué',
};

const ADMIN_ROLE_ORDER: Role[] = ['metier', 'decideur', 'admin'];

export function getRoleLabel(role?: string | null): string {
  if (!role) return 'Non attribué';
  return ROLE_LABELS[(role as Role)] ?? role;
}

export function getNextAdminRole(currentRole?: string | null): Role {
  const normalizedRole = currentRole === 'user' ? 'decideur' : (currentRole as Role | undefined);
  const index = ADMIN_ROLE_ORDER.indexOf((normalizedRole as Role) ?? 'metier');
  const nextIndex = index === -1 ? 0 : (index + 1) % ADMIN_ROLE_ORDER.length;
  return ADMIN_ROLE_ORDER[nextIndex];
}
