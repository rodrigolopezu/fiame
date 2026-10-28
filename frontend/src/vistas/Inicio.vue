<script setup>
import { ArrowRight, Calculator, FileText, Store } from 'lucide-vue-next'
import Logo from '../components/Logo.vue'
</script>

<template>
  <main class="inicio">
    <div class="fondo" aria-hidden="true" />
    <header>
      <Logo :tamano="44" />
      <h1>Tus fiados,<br /><span>con las cuentas claras.</span></h1>
      <p class="suave">El crédito de la tienda del barrio, ordenado y transparente: tasas, cuotas y estados de cuenta calculados al céntimo.</p>
    </header>
    <div class="opciones">
      <RouterLink to="/vendedor" class="opcion principal">
        <span class="icono"><Store :size="24" :stroke-width="1.8" /></span>
        <strong>Soy vendedor</strong>
        <span>Registra clientes, ventas al crédito, cobros y estados de cuenta.</span>
        <span class="ir">Ingresar <ArrowRight :size="16" /></span>
      </RouterLink>
      <RouterLink to="/portal" class="opcion">
        <span class="icono"><FileText :size="24" :stroke-width="1.8" /></span>
        <strong>Soy cliente</strong>
        <span class="suave">Consulta tu estado de cuenta con el código que te dio la tienda.</span>
        <span class="ir">Consultar <ArrowRight :size="16" /></span>
      </RouterLink>
      <RouterLink to="/simulador" class="opcion secundaria">
        <span class="icono"><Calculator :size="24" :stroke-width="1.8" /></span>
        <strong>Simulador y calculadoras</strong>
        <span class="suave">Herramienta de verificación de los cálculos financieros.</span>
        <span class="ir">Abrir <ArrowRight :size="16" /></span>
      </RouterLink>
    </div>
  </main>
</template>

<style scoped>
.inicio { position: relative; max-width: 980px; margin: 0 auto; padding: 72px 20px; display: flex; flex-direction: column; gap: 40px; }
.fondo {
  position: fixed; inset: 0; z-index: -1;
  background:
    radial-gradient(600px 400px at 85% 10%, rgb(108 77 255 / 0.18), transparent 70%),
    radial-gradient(500px 360px at 5% 90%, rgb(62 224 174 / 0.16), transparent 70%),
    var(--fondo);
}
header { display: flex; flex-direction: column; gap: 18px; max-width: 620px; }
h1 { font-size: clamp(32px, 5vw, 48px); line-height: 1.08; font-weight: 800; letter-spacing: -0.035em; }
h1 span { background: var(--marca-degradado); -webkit-background-clip: text; background-clip: text; color: transparent; }
header p { font-size: 16px; line-height: 1.5; }
.opciones { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }
.opcion {
  display: flex; flex-direction: column; gap: 8px; padding: 22px; border-radius: 18px;
  border: 1px solid var(--borde); background: var(--panel); color: inherit; text-decoration: none;
  box-shadow: var(--sombra); transition: border-color 0.15s, transform 0.15s, box-shadow 0.15s;
}
.opcion:hover { border-color: var(--marca); transform: translateY(-3px); box-shadow: var(--sombra-alta); }
.opcion strong { font-size: 17px; }
.icono { display: grid; place-items: center; width: 46px; height: 46px; border-radius: 14px; background: var(--marca-suave); color: var(--marca); margin-bottom: 4px; }
.ir { margin-top: auto; padding-top: 8px; display: inline-flex; align-items: center; gap: 4px; font-weight: 700; color: var(--marca); }
.principal { background: var(--marca-degradado); border-color: transparent; color: #fff; box-shadow: 0 12px 32px rgb(91 61 245 / 0.3); }
.principal .icono { background: rgb(255 255 255 / 0.18); color: #fff; }
.principal .ir { color: #fff; }
.secundaria .icono { background: var(--gris-suave); color: var(--suave); }
</style>
