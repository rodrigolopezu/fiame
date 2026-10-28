import { createApp } from 'vue'
import App from './App.vue'
import { router } from './router'
import '@fontsource-variable/plus-jakarta-sans'
import './estilos.css'

createApp(App).use(router).mount('#app')
