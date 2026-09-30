<script setup>
// Calculadoras sueltas para comprobar los ejercicios del libro con el mismo motor del backend.
import { ref } from 'vue'
import { api } from '../api'
import { dinero, fecha, PERIODOS, tasa as fTasa } from '../formato'
import Ayuda from './Ayuda.vue'
import CampoTasa from './CampoTasa.vue'

const T = (tipo, valor, periodo = 'ANUAL', capitalizacion = null) => ({ tipo, periodo, valor, capitalizacion })

// ---- Conversión de tasas
const conv = ref({ tasa: T('EFECTIVA', '12'), dias: 30, pedirNominal: false, nominal: { periodo: 'ANUAL', capitalizacion: 'MENSUAL' } })
const convR = ref(null)
const convE = ref('')
const ejemplosTasa = [
  ['4-14: TEA 12 % → TEM (0.9488793 %)', { tasa: T('EFECTIVA', '12'), dias: 30 }],
  ['4-10: TNA 28 % c.d. → TEM (2.359840157 %)', { tasa: T('NOMINAL', '28', 'ANUAL', 'DIARIA'), dias: 30 }],
  ['4-9: TNA 24 % c.q. → TEA (26.97346485 %)', { tasa: T('NOMINAL', '24', 'ANUAL', 'QUINCENAL'), dias: 360 }],
  ['4-19: TEM 4.5 % → TNA c.q. (53.40579602 %)', { tasa: T('EFECTIVA', '4.5', 'MENSUAL'), dias: 30, nominal: { periodo: 'ANUAL', capitalizacion: 'QUINCENAL' } }],
]
async function convertir() {
  try {
    convR.value = await api.tasa({ tasa: conv.value.tasa, dias: conv.value.dias, nominal: conv.value.pedirNominal ? conv.value.nominal : null })
    convE.value = ''
  } catch (e) { convE.value = e.message; convR.value = null }
}
function ejemploTasa(ej) {
  conv.value = { ...conv.value, tasa: { ...ej.tasa }, dias: ej.dias, pedirNominal: !!ej.nominal, nominal: ej.nominal || conv.value.nominal }
  convertir()
}

// ---- Interés entre fechas
const int = ref({ capital: '3000', tasa: T('NOMINAL', '18.5', 'ANUAL', 'DIARIA'), fecha_inicio: '2010-02-14', fecha_fin: '2011-09-13' })
const intR = ref(null)
const intE = ref('')
async function calcularInteres() {
  try { intR.value = await api.interes(int.value); intE.value = '' } catch (e) { intE.value = e.message; intR.value = null }
}

// ---- Cronograma
const cron = ref({ capital: '112000', tasa: T('EFECTIVA', '10'), numero_cuotas: 9, dias_periodo: 120, dias_gracia: 0 })
const cronR = ref(null)
const cronE = ref('')
const ejemplosCron = [
  ['8-1: US$ 112,000, TEA 10 %, 9 cuatrimestrales (14,537.95)', { capital: '112000', tasa: T('EFECTIVA', '10'), numero_cuotas: 9, dias_periodo: 120, dias_gracia: 0 }],
  ['7-13b: US$ 4,499.10, TEM 2.99 %, 6 meses de gracia + 36 (245.56)', { capital: '4499.10', tasa: T('EFECTIVA', '2.99', 'MENSUAL'), numero_cuotas: 36, dias_periodo: 30, dias_gracia: 180 }],
  ['7-6: S/ 32,800, TNS 8.4 % c.d., 15 bimestrales (2,715.63)', { capital: '32800', tasa: T('NOMINAL', '8.4', 'SEMESTRAL', 'DIARIA'), numero_cuotas: 15, dias_periodo: 60, dias_gracia: 0 }],
]
async function calcularCronograma() {
  try { cronR.value = await api.cronograma(cron.value); cronE.value = '' } catch (e) { cronE.value = e.message; cronR.value = null }
}
function ejemploCron(ej) { cron.value = JSON.parse(JSON.stringify(ej)); calcularCronograma() }

// ---- Mora
const mora = ref({ exigible: '20000', tasa_compensatoria: T('NOMINAL', '20', 'ANUAL', 'DIARIA'), tasa_moratoria: T('EFECTIVA', '60'), dias_mora: 7 })
const moraR = ref(null)
const moraE = ref('')
async function calcularMora() {
  try { moraR.value = await api.mora(mora.value); moraE.value = '' } catch (e) { moraE.value = e.message; moraR.value = null }
}

// ---- Ciclo
const ciclo = ref({ fecha_compra: '2026-09-15', dia_corte: 20, dia_pago: 26 })
const cicloR = ref(null)
const cicloE = ref('')
async function calcularCiclo() {
  try { cicloR.value = await api.ciclo(ciclo.value); cicloE.value = '' } catch (e) { cicloE.value = e.message; cicloR.value = null }
}
</script>

<template>
  <div class="calculadoras">
    <p class="aviso info">Estas calculadoras usan el mismo motor que el simulador. Los botones de ejemplo cargan ejercicios del libro del curso con su respuesta entre paréntesis.</p>

    <section class="panel">
      <h2>Conversión de tasas</h2>
      <div class="fila"><button v-for="[nombre, ej] in ejemplosTasa" :key="nombre" class="chico" @click="ejemploTasa(ej)">{{ nombre }}</button></div>
      <CampoTasa v-model="conv.tasa" titulo="Tasa dada" />
      <div class="grilla">
        <label class="campo"><span>Días de la tasa buscada <Ayuda texto="30 = mensual, 360 = anual, o cualquier número de días." /></span><input v-model.number="conv.dias" type="number" min="1" /></label>
      </div>
      <label class="check"><input v-model="conv.pedirNominal" type="checkbox" /> Calcular también la tasa nominal equivalente</label>
      <div v-if="conv.pedirNominal" class="grilla">
        <label class="campo"><span>Periodo de la nominal</span><select v-model="conv.nominal.periodo"><option v-for="[v, n] in PERIODOS" :key="v" :value="v">{{ n }}</option></select></label>
        <label class="campo"><span>Capitalización</span><select v-model="conv.nominal.capitalizacion"><option v-for="[v, n] in PERIODOS" :key="v" :value="v">{{ n }}</option></select></label>
      </div>
      <div class="fila"><button class="primario" @click="convertir">Convertir</button></div>
      <p v-if="convE" class="aviso">{{ convE }}</p>
      <table v-if="convR" class="resultado">
        <tbody>
          <tr><td>{{ convR.descripcion }} → efectiva de {{ convR.dias }} días</td><td class="num"><strong>{{ fTasa(convR.tasa_efectiva) }}</strong></td></tr>
          <tr><td>TEA</td><td class="num">{{ fTasa(convR.tea) }}</td></tr>
          <tr><td>TEM</td><td class="num">{{ fTasa(convR.tem) }}</td></tr>
          <tr><td>TED</td><td class="num">{{ fTasa(convR.ted) }}</td></tr>
          <tr v-if="convR.nominal"><td>Nominal equivalente</td><td class="num"><strong>{{ fTasa(convR.nominal) }}</strong></td></tr>
        </tbody>
      </table>
    </section>

    <section class="panel">
      <h2>Interés entre dos fechas</h2>
      <p class="chico suave">Ejemplo cargado: libro, ej. 3-3 (S/ 4,033.10).</p>
      <div class="grilla">
        <label class="campo"><span>Capital</span><input v-model="int.capital" inputmode="decimal" /></label>
        <label class="campo"><span>Desde</span><input v-model="int.fecha_inicio" type="date" /></label>
        <label class="campo"><span>Hasta</span><input v-model="int.fecha_fin" type="date" /></label>
      </div>
      <CampoTasa v-model="int.tasa" />
      <div class="fila"><button class="primario" @click="calcularInteres">Calcular</button></div>
      <p v-if="intE" class="aviso">{{ intE }}</p>
      <table v-if="intR" class="resultado">
        <tbody>
          <tr><td>Días calendario exactos</td><td class="num">{{ intR.dias }}</td></tr>
          <tr><td>Tasa efectiva del plazo</td><td class="num">{{ fTasa(intR.tasa_efectiva) }}</td></tr>
          <tr><td>Interés</td><td class="num">{{ dinero(intR.interes) }}</td></tr>
          <tr><td>Valor futuro</td><td class="num"><strong>{{ dinero(intR.valor_futuro) }}</strong></td></tr>
        </tbody>
      </table>
    </section>

    <section class="panel">
      <h2>Cronograma · método francés</h2>
      <div class="fila"><button v-for="[nombre, ej] in ejemplosCron" :key="nombre" class="chico" @click="ejemploCron(ej)">{{ nombre }}</button></div>
      <div class="grilla">
        <label class="campo"><span>Capital</span><input v-model="cron.capital" inputmode="decimal" /></label>
        <label class="campo"><span>N.° de cuotas</span><input v-model.number="cron.numero_cuotas" type="number" min="1" /></label>
        <label class="campo"><span>Días entre cuotas</span><input v-model.number="cron.dias_periodo" type="number" min="1" /></label>
        <label class="campo"><span>Días de gracia total <Ayuda texto="El interés de estos días se capitaliza antes de calcular la cuota." /></span><input v-model.number="cron.dias_gracia" type="number" min="0" /></label>
      </div>
      <CampoTasa v-model="cron.tasa" />
      <div class="fila"><button class="primario" @click="calcularCronograma">Calcular</button></div>
      <p v-if="cronE" class="aviso">{{ cronE }}</p>
      <template v-if="cronR">
        <p class="chico">
          Tasa del periodo {{ fTasa(cronR.tasa_periodo) }} · capital financiado {{ dinero(cronR.capital_financiado) }}
          <span v-if="cron.dias_gracia"> (gracia: TE {{ fTasa(cronR.tasa_gracia) }})</span>
        </p>
        <div class="tabla-scroll">
          <table>
            <thead><tr><th>N.°</th><th class="num">Saldo inicial</th><th class="num">Interés</th><th class="num">Cuota</th><th class="num">Amortización</th><th class="num">Saldo final</th></tr></thead>
            <tbody>
              <tr v-for="f in cronR.filas" :key="f.numero">
                <td>{{ f.numero }}</td>
                <td class="num">{{ dinero(f.saldo_inicial) }}</td>
                <td class="num">{{ dinero(f.interes) }}</td>
                <td class="num"><strong>{{ dinero(f.cuota) }}</strong></td>
                <td class="num">{{ dinero(f.amortizacion) }}</td>
                <td class="num">{{ dinero(f.saldo_final) }}</td>
              </tr>
            </tbody>
            <tfoot><tr><td colspan="2">Totales</td><td class="num">{{ dinero(cronR.total_interes) }}</td><td class="num">{{ dinero(cronR.total_pagado) }}</td><td colspan="2"></td></tr></tfoot>
          </table>
        </div>
      </template>
    </section>

    <section class="panel">
      <h2>Intereses por mora</h2>
      <p class="chico suave">Ejemplo cargado: libro, ej. 5-36 (compensatorio 77.91 y moratorio 183.62).</p>
      <div class="grilla">
        <label class="campo"><span>Monto exigible</span><input v-model="mora.exigible" inputmode="decimal" /></label>
        <label class="campo"><span>Días de mora</span><input v-model.number="mora.dias_mora" type="number" min="0" /></label>
      </div>
      <CampoTasa v-model="mora.tasa_compensatoria" titulo="Tasa compensatoria" />
      <CampoTasa v-model="mora.tasa_moratoria" titulo="Tasa moratoria" />
      <div class="fila"><button class="primario" @click="calcularMora">Calcular</button></div>
      <p v-if="moraE" class="aviso">{{ moraE }}</p>
      <table v-if="moraR" class="resultado">
        <tbody>
          <tr><td>Compensatorio por mora ({{ fTasa(moraR.tasa_compensatoria) }})</td><td class="num">{{ dinero(moraR.interes_compensatorio) }}</td></tr>
          <tr><td>Moratorio ({{ fTasa(moraR.tasa_moratoria) }})</td><td class="num">{{ dinero(moraR.interes_moratorio) }}</td></tr>
          <tr><td>Total a pagar</td><td class="num"><strong>{{ dinero(moraR.total_a_pagar) }}</strong></td></tr>
        </tbody>
      </table>
    </section>

    <section class="panel">
      <h2>Ciclo de una compra</h2>
      <div class="grilla">
        <label class="campo"><span>Fecha de compra</span><input v-model="ciclo.fecha_compra" type="date" /></label>
        <label class="campo"><span>Día de corte</span><input v-model.number="ciclo.dia_corte" type="number" min="1" max="28" /></label>
        <label class="campo"><span>Día de pago</span><input v-model.number="ciclo.dia_pago" type="number" min="1" max="28" /></label>
      </div>
      <div class="fila"><button class="primario" @click="calcularCiclo">Calcular</button></div>
      <p v-if="cicloE" class="aviso">{{ cicloE }}</p>
      <p v-if="cicloR">Corte {{ fecha(cicloR.fecha_corte) }} · pago {{ fecha(cicloR.fecha_pago) }} · {{ cicloR.dias_hasta_pago }} días hasta el pago</p>
    </section>
  </div>
</template>

<style scoped>
.calculadoras { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); align-items: start; }
.calculadoras > .aviso { grid-column: 1 / -1; }
.resultado td:first-child { color: var(--suave); }
@media (max-width: 500px) { .calculadoras { grid-template-columns: 1fr; } }
</style>
