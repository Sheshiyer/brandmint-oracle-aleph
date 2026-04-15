export type Locale = 'en' | 'fr';

export const LOCALES: Locale[] = ['en', 'fr'];

export function isLocale(value: string | undefined): value is Locale {
  return value === 'en' || value === 'fr';
}

export function normalizeLocale(value: string | undefined): Locale {
  return isLocale(value) ? value : 'en';
}

export function localizedPath(locale: Locale, path: string): string {
  if (!path || path === '/') return `/${locale}`;
  if (/^https?:\/\//.test(path)) return path;
  const normalized = path.startsWith('/') ? path : `/${path}`;
  return `/${locale}${normalized}`.replace(/\/+/g, '/');
}

export function switchLocalePath(pathname: string, targetLocale: Locale): string {
  const segments = pathname.split('/').filter(Boolean);
  if (segments[0] === 'en' || segments[0] === 'fr') {
    segments[0] = targetLocale;
    return `/${segments.join('/')}`;
  }
  if (segments.length === 0) return `/${targetLocale}`;
  return `/${targetLocale}/${segments.join('/')}`;
}

export const translations = {
  en: {
    shell: {
      portalHome: 'Portal Home',
      docsIndex: 'Docs Index',
      notebooklm: 'NotebookLM',
      portal: 'Portal',
      onThisPage: 'On this page',
      minRead: 'min read',
      launchReadyPortal: 'Launch-ready portal',
      freshBuild: 'Fresh build',
      openDocsIndex: 'Open docs index',
      openResearchHub: 'Open research hub',
      openSection: 'Open section →',
      reviewContext: 'Review the context →',
      openInWiki: 'Open in the wiki →',
    },
    home: {
      curatedLaunchTracks: 'Curated launch tracks',
      homeHeading: 'A brand portal first, but still a real wiki underneath',
      homeBlurb: 'Move through product, brand, research, and campaign work without losing deep document access.',
      visualWorld: 'Visual world',
      visualHeading: 'Use the actual brand surfaces, not just generic documentation cards',
      knowledgeMap: 'Knowledge map',
      knowledgeHeading: 'Browse the wiki by track',
      notebooklmSpotlight: 'NotebookLM spotlight',
      notebooklmHeading: 'Research and learning artifacts stay close to the story',
    },
    categories: {
      general: 'Portal & Research',
      product: 'Product',
      brand: 'Brand System',
      audience: 'Audience',
      marketing: 'Campaign',
    },
    featureCardLabels: {
      '/docs/product/overview': { title: 'Product Overview', eyebrow: 'Product', description: 'Hero product definition, positioning, and messaging stack for the current launch build.' },
      '/docs/brand/visual-guidelines': { title: 'Visual Guidelines', eyebrow: 'Brand System', description: 'Palette, typography, art direction, and brand-system guardrails for the current run.' },
      '/docs/marketing/campaign-copy': { title: 'Campaign Copy', eyebrow: 'Campaign', description: 'Campaign narratives, key copy assets, and launch-ready messaging organized for review.' },
      '/docs/research/notebooklm-artifacts': { title: 'NotebookLM Artifacts', eyebrow: 'Research', description: 'Surfaced reports, infographics, decks, audio, and research tables produced during Wave 7.' },
    },
    docTitles: {
      'index': 'Launch Dossier Index',
      'getting-started/quickstart': 'Quickstart',
      'product/overview': 'Product Overview',
      'product/features': 'Product Features',
      'product/specifications': 'Product Specifications',
      'brand/voice-tone': 'Voice & Tone',
      'brand/visual-guidelines': 'Visual Guidelines',
      'brand/visual-assets': 'Visual Assets Library',
      'audience/primary-persona': 'Primary Persona',
      'audience/secondary-personas': 'Secondary Personas',
      'market/competitive-landscape': 'Competitive Landscape',
      'marketing/campaign-copy': 'Campaign Copy',
      'marketing/email-templates': 'Email Templates',
      'marketing/social-content': 'Social Content',
      'marketing/video-scripts': 'Video Scripts',
      'marketing/ad-creative': 'Ad Creative',
      'research/notebooklm-artifacts': 'NotebookLM Artifacts',
    },
  },
  fr: {
    shell: {
      portalHome: 'Accueil du portail',
      docsIndex: 'Index du wiki',
      notebooklm: 'NotebookLM',
      portal: 'Portail',
      onThisPage: 'Sur cette page',
      minRead: 'min de lecture',
      launchReadyPortal: 'Portail prêt pour le lancement',
      freshBuild: 'Build récent',
      openDocsIndex: 'Ouvrir l’index du wiki',
      openResearchHub: 'Ouvrir le hub de recherche',
      openSection: 'Ouvrir la section →',
      reviewContext: 'Voir le contexte →',
      openInWiki: 'Ouvrir dans le wiki →',
    },
    home: {
      curatedLaunchTracks: 'Parcours de lancement',
      homeHeading: 'Un portail de marque d’abord, mais toujours un vrai wiki',
      homeBlurb: 'Parcourez le produit, la marque, la recherche et la campagne sans perdre l’accès profond aux documents.',
      visualWorld: 'Univers visuel',
      visualHeading: 'Utilisez les vraies surfaces de marque, pas seulement des cartes de documentation génériques',
      knowledgeMap: 'Carte des connaissances',
      knowledgeHeading: 'Parcourir le wiki par piste',
      notebooklmSpotlight: 'Focus NotebookLM',
      notebooklmHeading: 'Les artefacts de recherche restent proches du récit produit',
    },
    categories: {
      general: 'Portail & Recherche',
      product: 'Produit',
      brand: 'Système de marque',
      audience: 'Audience',
      marketing: 'Campagne',
    },
    featureCardLabels: {
      '/docs/product/overview': { title: 'Vue d’ensemble produit', eyebrow: 'Produit', description: 'Définition du produit hero, positionnement et socle de messaging pour le lancement actif.' },
      '/docs/brand/visual-guidelines': { title: 'Lignes directrices visuelles', eyebrow: 'Système de marque', description: 'Palette, typographie, direction artistique et garde-fous de la marque pour le run actuel.' },
      '/docs/marketing/campaign-copy': { title: 'Copy de campagne', eyebrow: 'Campagne', description: 'Narratifs de campagne, assets copy clés et messaging prêt pour le lancement.' },
      '/docs/research/notebooklm-artifacts': { title: 'Artefacts NotebookLM', eyebrow: 'Recherche', description: 'Rapports, infographies, decks, audio et tables de recherche issus de Wave 7.' },
    },
    docTitles: {
      'index': 'Index du dossier de lancement',
      'getting-started/quickstart': 'Démarrage rapide',
      'product/overview': 'Vue d’ensemble produit',
      'product/features': 'Fonctionnalités produit',
      'product/specifications': 'Spécifications produit',
      'brand/voice-tone': 'Voix & ton',
      'brand/visual-guidelines': 'Lignes directrices visuelles',
      'brand/visual-assets': 'Bibliothèque visuelle',
      'audience/primary-persona': 'Persona principal',
      'audience/secondary-personas': 'Personas secondaires',
      'market/competitive-landscape': 'Paysage concurrentiel',
      'marketing/campaign-copy': 'Copy de campagne',
      'marketing/email-templates': 'Templates email',
      'marketing/social-content': 'Contenu social',
      'marketing/video-scripts': 'Scripts vidéo',
      'marketing/ad-creative': 'Création publicitaire',
      'research/notebooklm-artifacts': 'Artefacts NotebookLM',
    },
  },
} as const;

export function t(locale: Locale) {
  return translations[locale];
}

export function localizedDocTitle(locale: Locale, slug: string, fallback: string): string {
  return translations[locale].docTitles[slug as keyof typeof translations.en.docTitles] || fallback;
}

export function localizedFeature(locale: Locale, href: string, fallback: { title: string; eyebrow: string; description: string }) {
  return translations[locale].featureCardLabels[href as keyof typeof translations.en.featureCardLabels] || fallback;
}
