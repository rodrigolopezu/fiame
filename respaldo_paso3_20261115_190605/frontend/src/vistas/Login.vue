<script setup>
import { CircleCheck } from 'lucide-vue-next'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { vendedor } from '../api'
import Logo from '../components/Logo.vue'
import { iniciar } from '../sesion'

const ruta = useRoute()
const router = useRouter()
const usuario = ref('')
const clave = ref('')
const error = ref('')
const enviando = ref(false)

async function entrar() {
  enviando.value = true
  error.value = ''
  try {
    iniciar(await vendedor.login(usuario.value, clave.value))
    router.push(ruta.query.siguiente || '/vendedor')
  } catch (e) {
    error.value = e.message
  } finally {
    enviando.value = false
  }
}
</script>

<template>
  <main class="login">
    <div class="tarjeta-login">
      <aside class="marca">
        <RouterLink to="/"><Logo :tamano="36" claro /></RouterLink>
        <h2>El cuaderno de fiados, ahora con las cuentas claras.</h2>
        <ul>
          <li><CircleCheck :size="18" /> Tasas y cuotas calculadas al céntimo</li>
          <li><CircleCheck :size="18" /> Estados de cuenta automáticos en cada corte</li>
          <li><CircleCheck :size="18" /> Tus clientes consultan su deuda con un código</li>
        </ul>
      </aside>
      <form @submit.prevent="entrar">
        <h1>Ingreso del vendedor</h1>
        <label class="campo">
          <span>Usuario</span>
          <input v-model="usuario" autocomplete="username" required autofocus />
        </label>
        <label class="campo">
          <span>Contraseña</span>
          <input v-model="clave" type="password" autocomplete="current-password" required />
        </label>
        <p v-if="error" class="aviso">{{ error }}</p>
        <button class="primario" :disabled="enviando">{{ enviando ? 'Ingresando…' : 'Ingresar' }}</button>
        <p class="chico suave">Entorno local de prueba: usuario <code>vendedor</code>, contraseña <code>fiame2026</code>.</p>
      </form>
    </div>
  </main>
</template>

<style scoped>
.login {
  min-height: 100vh; display: grid; place-items: center; padding: 20px;
  background:
    radial-gradient(600px 400px at 90% 0%, rgb(108 77 255 / 0.16), transparent 70%),
    radial-gradient(500px 360px at 0% 100%, rgb(62 224 174 / 0.14), transparent 70%),
    var(--fondo);
}
.tarjeta-login {
  width: min(860px, 100%); display: grid; grid-template-columns: 1fr 1fr; overflow: hidden;
  background: var(--panel); border-radius: 22px; box-shadow: var(--sombra-alta); border: 1px solid var(--borde);
}
.marca { background: var(--marca-degradado); color: #fff; padding: 36px 32px; display: flex; flex-direction: column; gap: 22px; }
.marca h2 { font-size: 24px; line-height: 1.2; font-weight: 800; letter-spacing: -0.02em; }
.marca ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 12px; }
.marca li { display: flex; gap: 10px; align-items: center; color: #e2dcff; }
.marca li svg { color: #3ee0ae; flex: none; }
form { padding: 36px 32px; display: flex; flex-direction: column; gap: 14px; justify-content: center; }
h1 { font-size: 22px; }
button.primario { padding: 11px; }
@media (max-width: 720px) {
  .tarjeta-login { grid-template-columns: 1fr; }
  .marca { padding: 24px; }
}
</style>
