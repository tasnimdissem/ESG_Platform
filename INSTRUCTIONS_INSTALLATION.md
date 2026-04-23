# 📦 Guide d'Installation - ESG Predictor Platform

## Méthode 1 : Export depuis Figma Make (RECOMMANDÉ)

1. Dans l'interface Figma Make, cherchez le bouton **"Export"** ou **"Download"** 
2. Téléchargez le fichier ZIP du projet
3. Décompressez-le sur votre ordinateur
4. Ouvrez le dossier dans VS Code
5. Dans le terminal VS Code :
   ```bash
   npm install
   npm run dev
   ```

## Méthode 2 : Création manuelle du projet

### Étape 1 : Créer le projet de base

```bash
npm create vite@latest esg-predictor -- --template react-ts
cd esg-predictor
```

### Étape 2 : Installer toutes les dépendances

```bash
npm install react-router lucide-react recharts clsx tailwind-merge class-variance-authority @radix-ui/react-slot
npm install -D tailwindcss@4.1.12 @tailwindcss/vite@4.1.12
```

### Étape 3 : Configuration Vite

Remplacez le contenu de `vite.config.ts` par :

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
})
```

### Étape 4 : Créer la structure des dossiers

```bash
mkdir -p src/app/components/figma
mkdir -p src/app/components/ui
mkdir -p src/app/contexts
mkdir -p src/app/pages
mkdir -p src/styles
```

### Étape 5 : Copier les fichiers

Vous devez maintenant copier tous les fichiers depuis Figma Make :

**Fichiers à copier depuis cette conversation :**

1. `/src/app/App.tsx`
2. `/src/app/routes.tsx`
3. `/src/app/contexts/AuthContext.tsx`
4. `/src/app/components/Sidebar.tsx`
5. `/src/app/components/Header.tsx`
6. `/src/app/components/ESGScoreCard.tsx`
7. `/src/app/components/Layout.tsx`
8. `/src/app/pages/Login.tsx`
9. `/src/app/pages/Dashboard.tsx`
10. `/src/app/pages/Analytics.tsx`
11. `/src/app/pages/Chatbot.tsx`
12. `/src/app/pages/Recommendations.tsx`

### Étape 6 : Créer les fichiers de style

**`src/styles/tailwind.css`**
```css
@import "tailwindcss";
@import "./theme.css";
@import "./fonts.css";
```

**`src/styles/theme.css`**
```css
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
  }
}
```

**`src/styles/fonts.css`**
```css
/* Fonts imports go here */
```

**`src/styles/index.css`**
```css
@import "./tailwind.css";

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

### Étape 7 : Créer le point d'entrée

**`src/main.tsx`**
```typescript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './app/App'
import './styles/index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

### Étape 8 : Créer ImageWithFallback (composant requis)

**`src/app/components/figma/ImageWithFallback.tsx`**
```typescript
import { useState } from 'react';

interface ImageWithFallbackProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src: string;
  alt: string;
}

export function ImageWithFallback({ src, alt, ...props }: ImageWithFallbackProps) {
  const [error, setError] = useState(false);

  if (error) {
    return (
      <div className="bg-gray-200 flex items-center justify-center" {...props}>
        <span className="text-gray-400 text-sm">{alt}</span>
      </div>
    );
  }

  return <img src={src} alt={alt} onError={() => setError(true)} {...props} />;
}
```

### Étape 9 : Lancer le projet

```bash
npm run dev
```

Ouvrez votre navigateur sur `http://localhost:5173`

## 🎯 Connexion à la plateforme

**Pour vous connecter :**
- Email : n'importe quel email (ex: `admin@esg.com`)
- Mot de passe : n'importe quel mot de passe

C'est une authentification de démonstration pour votre PFE.

## 📊 Fonctionnalités disponibles

✅ Dashboard avec scores ESG en temps réel
✅ Analytics détaillées et graphiques interactifs
✅ Chatbot IA pour questions ESG
✅ Système de recommandations ML
✅ Navigation multi-pages avec React Router
✅ Design moderne et responsive

## 🚀 Prochaines étapes (optionnel)

Pour ajouter une vraie base de données :
- Intégrer Supabase pour la persistance
- Connecter votre modèle ML via API
- Ajouter l'authentification sécurisée

Bon courage pour votre PFE ! 🎓
