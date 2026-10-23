import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'Marketing Toolbox',
  description: 'Command-line tools for Google Analytics 4 and Google Tag Manager.',
  base: '/',
  cleanUrls: false,
  themeConfig: {
    sidebar: [
      { text: 'Marketing Toolbox', link: '/' },
      { text: 'Installation', link: '/install/' },
      {
        text: 'Authentication', link: '/auth/',
        items: [{ text: 'Desktop OAuth setup', link: '/auth/desktop-oauth/' }]
      },
      {
        text: 'Tool behavior', link: '/tools/',
        items: [
          { text: 'GA4 Data', link: '/tools/ga4-data/' },
          { text: 'GA4 Admin', link: '/tools/ga4-admin/' },
          { text: 'Tag Manager', link: '/tools/tag-manager/' }
        ]
      }
    ]
  }
})
