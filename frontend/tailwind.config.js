/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        // 主题特征色：映射到全局 CSS 变量 --theme-color（由 store.js 动态注入）
        primary: 'var(--theme-color)',
      },
    },
  },
  plugins: [],
}
