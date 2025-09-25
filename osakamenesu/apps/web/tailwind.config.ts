import type { Config } from 'tailwindcss'

export default {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-sans)', 'sans-serif'],
      },
      colors: {
        brand: {
          primary: 'var(--color-brand-primary)',
          primaryDark: 'var(--color-brand-primary-dark)',
          secondary: 'var(--color-brand-secondary)',
        },
        neutral: {
          surface: 'var(--color-surface)',
          surfaceAlt: 'var(--color-surface-alt)',
          borderLight: 'var(--color-border-light)',
          text: 'var(--color-text)',
          textMuted: 'var(--color-text-muted)',
        },
        state: {
          successBg: 'var(--color-success-bg)',
          successText: 'var(--color-success-text)',
          dangerBg: 'var(--color-danger-bg)',
          dangerText: 'var(--color-danger-text)',
        },
      },
      boxShadow: {
        card: 'var(--shadow-card)',
        cardHover: 'var(--shadow-card-hover)',
      },
      borderRadius: {
        card: 'var(--radius-card)',
        section: 'var(--radius-section)',
        badge: 'var(--radius-badge)',
      },
    },
  },
  plugins: [],
} satisfies Config
