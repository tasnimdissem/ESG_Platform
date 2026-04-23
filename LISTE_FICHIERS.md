# 📁 Liste complète des fichiers du projet ESG Predictor

## Structure du projet

```
esg-predictor/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── index.html
├── src/
│   ├── main.tsx
│   ├── styles/
│   │   ├── index.css
│   │   ├── tailwind.css
│   │   ├── theme.css
│   │   └── fonts.css
│   └── app/
│       ├── App.tsx
│       ├── routes.tsx
│       ├── contexts/
│       │   └── AuthContext.tsx
│       ├── components/
│       │   ├── figma/
│       │   │   └── ImageWithFallback.tsx
│       │   ├── ESGScoreCard.tsx
│       │   ├── Header.tsx
│       │   ├── Layout.tsx
│       │   └── Sidebar.tsx
│       └── pages/
│           ├── Login.tsx
│           ├── Dashboard.tsx
│           ├── Analytics.tsx
│           ├── Chatbot.tsx
│           └── Recommendations.tsx
```

## 📄 Fichiers à copier depuis Figma Make

### Configuration racine

1. **package.json** - Déjà présent dans Figma Make
2. **vite.config.ts** - À créer/modifier
3. **tsconfig.json** - Généralement auto-généré

### Fichiers source principaux

#### Point d'entrée
- ✅ `src/main.tsx` - À créer

#### Styles
- ✅ `src/styles/index.css` - À créer
- ✅ `src/styles/tailwind.css` - À créer
- ✅ `src/styles/theme.css` - À créer
- ✅ `src/styles/fonts.css` - À créer (peut être vide)

#### Application
- ✅ `src/app/App.tsx` - **CRÉÉ** ✓
- ✅ `src/app/routes.tsx` - **CRÉÉ** ✓

#### Contextes
- ✅ `src/app/contexts/AuthContext.tsx` - **CRÉÉ** ✓

#### Composants
- ✅ `src/app/components/ESGScoreCard.tsx` - **CRÉÉ** ✓
- ✅ `src/app/components/Header.tsx` - **CRÉÉ** ✓
- ✅ `src/app/components/Layout.tsx` - **CRÉÉ** ✓
- ✅ `src/app/components/Sidebar.tsx` - **CRÉÉ** ✓
- ✅ `src/app/components/figma/ImageWithFallback.tsx` - À créer

#### Pages
- ✅ `src/app/pages/Login.tsx` - **CRÉÉ** ✓
- ✅ `src/app/pages/Dashboard.tsx` - **CRÉÉ** ✓
- ✅ `src/app/pages/Analytics.tsx` - **CRÉÉ** ✓
- ✅ `src/app/pages/Chatbot.tsx` - **CRÉÉ** ✓
- ✅ `src/app/pages/Recommendations.tsx` - **CRÉÉ** ✓

## 🔍 Comment récupérer les fichiers

### Méthode la plus simple

Dans Figma Make, utilisez la fonction **Export** ou **Download** pour télécharger tout le projet en un clic.

### Sinon, copiez manuellement

Tous les fichiers marqués **CRÉÉ** ✓ sont disponibles dans cette conversation. Vous pouvez :

1. Cliquer sur chaque fichier dans l'interface Figma Make
2. Copier le code
3. Le coller dans VS Code

## 📦 Dépendances à installer

```bash
npm install react-router lucide-react recharts clsx tailwind-merge class-variance-authority @radix-ui/react-slot
npm install -D tailwindcss@4.1.12 @tailwindcss/vite@4.1.12
```

## ✅ Checklist de vérification

Avant de lancer `npm run dev`, assurez-vous d'avoir :

- [ ] Créé le projet Vite avec React + TypeScript
- [ ] Installé toutes les dépendances
- [ ] Copié tous les fichiers listés ci-dessus
- [ ] Configuré vite.config.ts avec Tailwind
- [ ] Créé les fichiers de styles
- [ ] Créé src/main.tsx
- [ ] Créé ImageWithFallback.tsx

Puis lancez :
```bash
npm install
npm run dev
```
