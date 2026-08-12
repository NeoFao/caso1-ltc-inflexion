# Marco teórico: criptoactivos y sus características

**Autor:** Alejandro Zamora · **Issue:** [S1-M2-05](https://github.com/NeoFao/caso1-ltc-inflexion/issues/13)

> **Esqueleto.** Los puntos 1 a 5 son sobre todo bibliográficos; los puntos 6, 7 y 8 tienen
> evidencia nuestra ya generada. Borrá los bloques `> ESCRIBÍ ACÁ` al completarlos.
> El noveno punto del enunciado — métricas de evaluación — va en [`m2-metricas.md`](m2-metricas.md).

---

## 1. Definición de criptoactivo

> **ESCRIBÍ ACÁ.** Qué es un criptoactivo, qué lo distingue de un activo financiero tradicional, y qué papel juega el registro distribuido. Bibliográfico, con citas en APA.

## 2. Características principales

> **ESCRIBÍ ACÁ.** Descentralización, disponibilidad continua, divisibilidad, transparencia del registro, ausencia de un cierre diario.
>
> **Conectá con nuestros datos:** que el mercado opere 24/7 explica por qué la estacionalidad semanal que midió M1 es prácticamente nula (0,426 % de la variación total). En un mercado con horario habría efecto fin de semana; acá no lo hay. Es una característica del activo que se ve en la serie.

## 3. Principales tipos

> **ESCRIBÍ ACÁ.** Monedas de pago, plataformas de contratos inteligentes, stablecoins, tokens de utilidad. Ubicá dónde cae cada una de nuestras seis: LTC como moneda de pago, ETH y ADA y SOL como plataformas de capa 1, BTC como reserva de valor, XRP orientada a pagos transfronterizos.

## 4. Mercado cripto

> **ESCRIBÍ ACÁ.** Estructura del mercado, exchanges centralizados, capitalización y liquidez, operación continua.
>
> **Dato nuestro:** los precios los tomamos de la API pública de Binance. Eso es una decisión con consecuencia y hay que declararla: los precios son de un exchange, no un promedio de mercado. La ventana común a las seis criptomonedas arranca el 11 de agosto de 2020 porque es cuando Solana empieza a cotizar; todo lo anterior se descarta por ser incompleto.

## 5. Factores que afectan el precio

> **ESCRIBÍ ACÁ.** Oferta y demanda, halvings, regulación, sentimiento, flujos institucionales, contagio entre activos.
>
> El enunciado ya trae la justificación de por qué BTC, ETH, SOL, XRP y ADA: BTC como transmisor sistémico, ETH como segundo motor, SOL como indicador de actividad especulativa, XRP sensible a lo regulatorio, ADA como reflejo de rotación de capital entre capas 1. Podés apoyarte en eso, pero citalo.

---

## 6. Correlación y dependencia entre activos

![Figura](../../evidencias/mt-07-correlacion.png)

**Medido sobre retornos:** todas las parejas entre 0,475 y 0,806. LTC se correlaciona más con **ETH (0,740)** y con **BTC (0,715)**, y menos con **SOL (0,524)**.

Sobre precios en nivel el rango se dispara a 0,126 – 0,888 y el orden deja de tener sentido económico.

> **ESCRIBÍ ACÁ.** M1 desarrolla la mecánica estadística de la correlación cruzada; **vos desarrollá la interpretación económica**, que es lo tuyo. Por qué tiene sentido que ETH y BTC sean los más correlacionados con LTC, y por qué SOL lo es menos. Qué significa un mercado donde todo se mueve junto con correlaciones de 0,5 a 0,8: poca diversificación, contagio rápido, sentimiento compartido.
>
> Evitá repetir lo que escribe M1. Coordiná con él: una sección explica el método, la otra el significado.

---

## 7. Definición de punto de inflexión

![Figura](../../evidencias/mt-08a-giros-construidos.png)

**Figura.** Serie construida por nosotros. Los giros marcados son exactamente los vértices que colocamos al generarla; no son datos de mercado.

> **ESCRIBÍ ACÁ.** Esta sección tiene material propio y extenso: [`docs/00-definicion-punto-inflexion.md`](../../00-definicion-punto-inflexion.md).
>
> Lo esencial que hay que transmitir: **un máximo no existe en absoluto, existe respecto de una ventana**. La misma vela puede ser un giro con `w=2` y no serlo con `w=10`, y las dos lecturas son correctas. No estamos buscando "la definición verdadera": estamos eligiendo a qué escala trabajar, y esa elección hay que justificarla.
>
> Incluí la propiedad aritmética, que es demostrable y da solidez: dos máximos no pueden estar a menos de `w+1` velas, porque cada uno caería en la ventana del otro y cada uno tendría que ser mayor que el otro. De ahí que como mucho 1 de cada `w+1` velas pueda ser máximo.

## 8. Encontrar puntos de inflexión

![Figura](../../evidencias/mt-08b-giros-ltc.png)

**Figura.** Últimas 250 velas de LTC con los giros detectados por el criterio de ventana.

**Medido:** sobre la serie construida, el detector encontró **18 de 18** vértices, exactamente y sin falsos positivos.

> **ESCRIBÍ ACÁ.** Dos enfoques, y conviene contrastarlos:
>
> 1. **Estructura de mercado (HH, HL, LH, LL).** Es la figura del enunciado y la forma clásica de identificarlos a ojo. Explicá qué significan y cómo una ruptura marca el cambio de tendencia.
> 2. **Criterio automático de ventana.** El nuestro. Reproducible y sin criterio del observador, pero exige elegir `w`.
>
> El argumento que cierra la sección: el detector encuentra 18 de 18 en la serie donde nosotros pusimos la respuesta. Eso valida el método **antes** de aplicarlo a datos donde nadie sabe la verdad.
>
> Mencioná también la limitación honesta: para saber si la vela `t` fue un máximo hay que ver las `w` velas siguientes, así que la etiqueta se conoce con retraso. Es una propiedad del problema, no un defecto de la implementación, y condiciona qué se puede prometer en tiempo real.

---

## Referencias

> **ESCRIBÍ ACÁ.** APA. Mínimo una fuente académica por concepto principal.
