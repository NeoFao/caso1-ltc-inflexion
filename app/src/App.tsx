import { useEffect, useMemo, useState } from "react";

import Grafico, { MAXIMO, MINIMO } from "./Grafico";
import {
  type Comparacion,
  type Configuracion,
  type Origen,
  type Punto,
  type PuntoDeOperacion,
  type Respuesta,
  type Umbral,
  antiguedad,
  obtenerComparacion,
  obtenerConfiguracion,
  obtenerHistorico,
  obtenerHistoricoFundacional,
  obtenerPuntoDeOperacion,
  obtenerSintetico,
  obtenerTiempoReal,
} from "./api";

type Modelo = "baseline" | "fundacional";
type Modo = "sintetico" | "historico" | "tiempo-real";

/**
 * Cuantas horas dura una vela, a partir de la granularidad del contrato
 * ("4h", "1d"...). Issue #99: los chips dicen "8 velas" y nadie de fuera sabe
 * cuanto es eso; convertirlo a horas es una conversion de unidades sobre un
 * numero que ya viene del backend, no una cifra nueva.
 */
function horasPorVela(granularidad: string): number {
  const m = /^(\d+)([hd])$/.exec(granularidad);
  if (!m) return NaN;
  const [, cantidad, unidad] = m;
  return Number(cantidad) * (unidad === "d" ? 24 : 1);
}

const MODOS: { id: Modo; etiqueta: string; descripcion: string }[] = [
  {
    id: "sintetico",
    etiqueta: "Sintético",
    descripcion:
      "Serie construida con giros conocidos por nosotros. Es la única prueba donde la verdad no está en discusión: sirve para detectar errores de implementación que en datos reales pasarían por «el modelo no acertó».",
  },
  {
    id: "historico",
    etiqueta: "Histórico",
    descripcion:
      "Precios reales, con las etiquetas verdaderas junto a las predichas sobre el mismo eje. Los marcadores rellenos son los giros que ocurrieron; las flechas, los que el modelo anunció.",
  },
  {
    id: "tiempo-real",
    etiqueta: "Tiempo real",
    // Issue #149: decia "LTC al día" sobre un panel que termina el 05/08/2026. La
    // fecha real se muestra abajo, calculada del propio dato; aqui se describe el
    // comportamiento, que es lo que el modo demuestra y sí es cierto siempre.
    descripcion:
      "El modelo anuncia cada vela en el momento, con la información disponible hasta ese instante y nada más. La confirmación —si de verdad fue un giro— tarda lo que el sistema tarda en verla venir.",
  },
];

const SECCIONES = [
  { id: "sistema", texto: "El sistema" },
  { id: "silencio", texto: "El silencio" },
  { id: "visor", texto: "El visor" },
  { id: "medida", texto: "La medida" },
  { id: "limites", texto: "Los límites" },
];

export default function App() {
  const [modo, setModo] = useState<Modo>("historico");
  const [activo, setActivo] = useState("LTC");
  const [configuracion, setConfiguracion] = useState<Configuracion | null>(null);
  const [datos, setDatos] = useState<Respuesta | null>(null);
  const [origen, setOrigen] = useState<Origen | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [comparacion, setComparacion] = useState<Comparacion | null>(null);
  const [modeloElegido, setModeloElegido] = useState<Modelo>("baseline");
  const [operacion, setOperacion] = useState<PuntoDeOperacion | null>(null);
  // La serie que dibuja la portada. Es el mismo panel de Tiempo real y se pide una
  // sola vez: la portada no cambia cuando cambias de modo, porque no es una vista,
  // es la presentacion del sistema.
  const [portada, setPortada] = useState<Punto[] | null>(null);
  // Issue #150. Arranca en 0,40 porque es el punto que la medicion respalda: acierta
  // el doble que el azar y gana en los nueve tramos. No es un default estetico.
  const [umbral, setUmbral] = useState(0.4);

  useEffect(() => {
    obtenerConfiguracion()
      .then((r) => setConfiguracion(r.datos))
      .catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    obtenerComparacion().catch(() => null).then((c) => c && setComparacion(c));
    obtenerPuntoDeOperacion().catch(() => null).then((o) => o && setOperacion(o));
    obtenerTiempoReal().catch(() => null).then((r) => r && setPortada(r.serie));
  }, []);

  useEffect(() => {
    // Cambiar de modo rapido (p. ej. Historico -> Sintetico) deja dos peticiones en
    // vuelo. Sin este guard, la que responde despues pisa el estado sin importar
    // cual es mas reciente: el panel de LTC completo (13 100 filas) tarda mas que
    // la sintetica (300), asi que Historico ganaba la carrera y Sintetico quedaba
    // mostrando sus numeros.
    let cancelado = false;
    setCargando(true);
    setError(null);
    // El orden de este encadenado importa y ya se equivocó una vez (#144). El
    // selector de modelo solo se dibuja en Historico, pero `modeloElegido` es
    // estado del componente y sobrevive al cambio de modo: si se preguntaba por
    // el antes que por el modo, el camino Historico -> Fundacional -> Tiempo
    // real servia el precalculado del fundacional, con su fecha vieja, bajo el
    // aviso de que los datos son de hoy.
    const peticion =
      modo === "sintetico"
        ? obtenerSintetico(300)
        : modo === "tiempo-real"
          ? // Issue #149: este modo servia el panel del baseline trivial, que
            // responde siempre Continuidad -- la vista no dibujaba una sola flecha
            // mientras la pantalla decia que el modelo anuncia cada vela.
            obtenerTiempoReal().then((datos) => ({
              datos,
              origen: "precalculado" as Origen,
            }))
          : modeloElegido === "fundacional"
            ? obtenerHistoricoFundacional().then((datos) => ({
                datos,
                origen: "precalculado" as Origen,
              }))
            : obtenerHistorico(activo, desde, hasta);
    peticion
      .then((r) => {
        if (cancelado) return;
        setDatos(r.datos);
        setOrigen(r.origen);
      })
      .catch((e) => {
        if (!cancelado) setError(String(e));
      })
      .finally(() => {
        if (!cancelado) setCargando(false);
      });
    return () => {
      cancelado = true;
    };
  }, [modo, activo, desde, hasta, modeloElegido]);

  const modoActual = MODOS.find((m) => m.id === modo)!;
  const edad = antiguedad(datos?.generado_utc ?? configuracion?.generado_utc);
  // El piso obligatorio (D7). Va junto a cada cifra porque un numero suelto no se
  // puede leer: 0,390 no es bueno ni malo hasta saber que el azar da 0,337.
  const azar = comparacion?.modelos.find((m) => m.clave === "baseline_aleatorio");
  const clasico = comparacion?.modelos.find(
    (m) => m.clave === "bosque_aleatorio_rezagos_relativos",
  );
  const elegido: Umbral | undefined = operacion?.umbrales.reduce((mejor, u) =>
    Math.abs(u.umbral - umbral) < Math.abs(mejor.umbral - umbral) ? u : mejor,
  );
  const ultimaVela = datos?.ultima_vela ?? datos?.serie[datos.serie.length - 1]?.fecha;
  const diasDeAtraso = ultimaVela
    ? Math.floor((Date.now() - Date.parse(ultimaVela)) / 86_400_000)
    : null;
  const horasAnticipacion = configuracion
    ? configuracion.latencia_real * horasPorVela(configuracion.granularidad)
    : null;
  const continuidad = datos?.balance?.find((b) => b.codigo === 3);

  return (
    <div className="min-h-screen bg-papel text-tinta">
      <BarraFija configuracion={configuracion} />

      {/* ------------------------------------------------------------ portada */}
      <header id="portada" className="relative overflow-hidden bg-noche">
        {/* Una sola luz, muy abierta, detras del titulo. No es adorno: separa el
            bloque de texto del trazo que viene abajo. */}
        <div
          className="pointer-events-none absolute -top-40 left-1/2 h-[42rem] w-[74rem] -translate-x-1/2 opacity-60"
          style={{
            background:
              "radial-gradient(52% 50% at 50% 42%, #22406B 0%, rgba(22,37,60,0.5) 44%, rgba(15,27,45,0) 76%)",
          }}
        />
        <div className="relative mx-auto max-w-6xl px-6 pt-24 sm:px-8 sm:pt-32">
          <p className="font-display text-[14.5px] italic text-claro-3">
            Caso n.<sup>o</sup> 1 · Señales y sistemas · Litecoin, velas de{" "}
            {configuracion?.granularidad ?? "4h"}
          </p>

          <h1 className="mt-5 max-w-[17ch] font-display text-[clamp(2.4rem,5.6vw,4.6rem)] font-semibold leading-[1.03] tracking-[-0.025em] text-claro">
            Avisa antes de que el precio dé la vuelta.
          </h1>

          <div
            className="mt-8 grid gap-x-16 gap-y-9 lg:grid-cols-[minmax(0,30rem)_minmax(0,1fr)]"
            data-testid="titular"
          >
            <p className="text-[16.5px] leading-[1.65] text-claro-2">
              De cada vela dice si el precio está por girar o va a seguir como está
              {horasAnticipacion ? `, con ${horasAnticipacion} horas de anticipación` : ""}. Le
              ganamos al azar por poco, y lo decimos con esa palabra:{" "}
              <span className="text-claro">por poco</span>. Todo lo que hay en esta página es una
              medición, y cada una viene con el listón que tenía que superar.
            </p>

            {clasico && azar && (
              <div className="flex flex-wrap items-end gap-x-14 gap-y-8">
                <CifraPortada
                  valor={clasico.f1_macro.toFixed(3)}
                  rotulo="F1 macro del clásico"
                  grande
                />
                <CifraPortada valor={azar.f1_macro.toFixed(3)} rotulo="lo mismo, el azar" />
                {continuidad && (
                  <CifraPortada
                    valor={`${continuidad.porcentaje.toFixed(1)} %`}
                    rotulo="de las velas no giran"
                  />
                )}
              </div>
            )}
          </div>

          <div className="mt-10 flex flex-wrap items-center gap-x-8 gap-y-4">
            <a
              href="#visor"
              className="inline-flex items-center gap-2.5 rounded-full bg-claro px-6 py-3 text-[14.5px] font-medium text-noche transition hover:bg-white"
            >
              Abrir el visor
              <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
                <path
                  d="M7 2v10M3 8l4 4 4-4"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.6"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </a>
            {configuracion?.panel && (
              <p className="cifra text-[12.5px] text-claro-3">
                panel de {configuracion.panel.filas_totales.toLocaleString("es-CR")} observaciones ·
                w={configuracion.w} · h={configuracion.h}
              </p>
            )}
          </div>
        </div>

        {/* El trazo: la serie real de LTC a sangre, con los giros confirmados. Es
            lo mas caracteristico que tiene este proyecto y por eso abre la pagina. */}
        <TrazoPortada puntos={portada} />
      </header>

      {/* ------------------------------------------------------------ sistema */}
      <Seccion
        id="sistema"
        rotulo="El sistema"
        titulo="Un giro no se ve hasta un rato después de que ocurrió."
        bajada={
          configuracion ? (
            <>
              Para confirmar que una vela fue un máximo hay que mirar las {configuracion.w} velas
              de antes y las {configuracion.w} de después. Esas de después todavía no ocurrieron,
              así que el sistema anuncia con lo que sabe hasta ese instante y espera. Esa espera no
              es una limitación técnica: es lo que tarda el problema en verificarse solo.
            </>
          ) : null
        }
      >
        <div className="grid gap-x-16 gap-y-12 lg:grid-cols-[minmax(0,1fr)_minmax(0,25rem)]">
          {configuracion && (
            <Ventana configuracion={configuracion} horasAnticipacion={horasAnticipacion} />
          )}
          <dl className="space-y-7">
            {[
              {
                t: "Tres respuestas, no dos",
                d: "Cada vela es Máximo, Mínimo o Continuidad. Las dos primeras son raras y son las que importan.",
              },
              {
                t: `${horasAnticipacion ?? "?"} horas de anticipación`,
                d: configuracion
                  ? `El aviso sale ${configuracion.latencia_real} velas de ${configuracion.granularidad} antes de que el giro termine de confirmarse.`
                  : "",
              },
              {
                t: "Nada se calcula en el navegador",
                d: "Las métricas vienen de contracts/metrics.py y llegan ya medidas. Si esta página las recalculara, tarde o temprano darían distinto que el informe.",
              },
            ].map((x) => (
              <div key={x.t} className="border-l-2 border-linea pl-5">
                <dt className="font-display text-[19px] font-semibold text-tinta">{x.t}</dt>
                <dd className="mt-1.5 text-[15px] leading-[1.6] text-tinta-2">{x.d}</dd>
              </div>
            ))}
          </dl>
        </div>
      </Seccion>

      {/* ----------------------------------------------------------- silencio */}
      {operacion && elegido && (
        <Seccion
          id="silencio"
          rotulo="El silencio"
          titulo="Lo más útil que hace el sistema es callarse."
          oscura
          bajada={
            <>
              Avisando en todas las velas acierta{" "}
              <span className="cifra text-claro">
                {operacion.umbrales[0].precision.toFixed(3)}
              </span>{" "}
              de sus avisos, por debajo de la frecuencia con que los giros ocurren solos (
              {(operacion.frecuencia_base_de_giros * 100).toFixed(1)} %). Como alarma, eso es peor
              que reaccionar al azar. Dejándolo callarse cuando no está seguro, mejora. Mové el
              umbral: el visor de abajo, en Tiempo real, dibuja exactamente el que elijas acá.
            </>
          }
        >
          <ControlDeUmbral
            operacion={operacion}
            umbral={umbral}
            elegido={elegido}
            onCambio={setUmbral}
          />
        </Seccion>
      )}

      {/* -------------------------------------------------------------- visor */}
      <Seccion
        id="visor"
        rotulo="El visor"
        titulo="La serie, con lo que ocurrió y lo que el sistema dijo."
        bajada={
          <>
            Los círculos son los giros que ocurrieron de verdad; las flechas, los que el modelo
            anunció. Superponerlos en el mismo eje es lo que hace visible de un vistazo dónde
            acierta y dónde inventa.
          </>
        }
      >
        <div className="flex flex-wrap items-center gap-x-4 gap-y-3">
          <nav className="flex overflow-hidden rounded-full border border-linea bg-blanco shadow-placa">
            {MODOS.map((m, i) => (
              <button
                key={m.id}
                onClick={() => setModo(m.id)}
                aria-pressed={modo === m.id}
                className={`px-5 py-2.5 text-[13.5px] font-medium transition ${
                  i > 0 ? "border-l border-linea" : ""
                } ${modo === m.id ? "bg-noche text-claro" : "text-tinta-2 hover:bg-papel"}`}
              >
                {m.etiqueta}
              </button>
            ))}
          </nav>

          {modo === "historico" && (
            <div className="flex overflow-hidden rounded-full border border-linea bg-blanco shadow-placa">
              {(["baseline", "fundacional"] as const).map((m, i) => (
                <button
                  key={m}
                  onClick={() => setModeloElegido(m)}
                  aria-pressed={modeloElegido === m}
                  className={`px-4 py-2.5 text-[13px] font-medium transition ${
                    i > 0 ? "border-l border-linea" : ""
                  } ${
                    modeloElegido === m ? "bg-acento text-white" : "text-tinta-2 hover:bg-papel"
                  }`}
                >
                  {m === "baseline" ? "Baseline" : "Fundacional"}
                </button>
              ))}
            </div>
          )}

          {modo === "historico" && modeloElegido === "baseline" && configuracion && (
            <select
              value={activo}
              onChange={(e) => setActivo(e.target.value)}
              className="rounded-full border border-linea bg-blanco px-4 py-2.5 text-[13px] font-medium text-tinta shadow-placa"
              aria-label="Criptomoneda"
            >
              {configuracion.activos.map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </select>
          )}

          {modo === "historico" && modeloElegido === "baseline" && (
            <div className="flex flex-wrap items-center gap-2 text-[13px] text-tinta-2">
              <label className="flex items-center gap-1.5">
                desde
                <input
                  type="date"
                  value={desde}
                  onChange={(e) => setDesde(e.target.value)}
                  className="rounded-lg border border-linea bg-blanco px-2.5 py-1.5 text-[13px] text-tinta"
                  aria-label="Desde"
                />
              </label>
              <label className="flex items-center gap-1.5">
                hasta
                <input
                  type="date"
                  value={hasta}
                  onChange={(e) => setHasta(e.target.value)}
                  className="rounded-lg border border-linea bg-blanco px-2.5 py-1.5 text-[13px] text-tinta"
                  aria-label="Hasta"
                />
              </label>
              {(desde || hasta) && (
                <button
                  onClick={() => {
                    setDesde("");
                    setHasta("");
                  }}
                  className="text-[12.5px] font-medium text-acento underline underline-offset-2"
                >
                  limpiar rango
                </button>
              )}
            </div>
          )}

          {modo === "historico" && modeloElegido === "fundacional" && datos?.ventana && (
            <p className="font-display text-[13.5px] italic text-tinta-3">
              LTC, ventana de validación {datos.ventana.desde.slice(0, 10)} –{" "}
              {datos.ventana.hasta.slice(0, 10)}
            </p>
          )}
        </div>

        {/* Los chips dicen de donde viene el panel que se esta mirando. Van aca y no
            en la portada porque describen la vista, no el sistema. */}
        {configuracion && (
          <div className="mt-3 flex flex-wrap gap-2">
            {configuracion.provisional && (
              <Chip tono="ambar">parámetros provisionales, sin congelar</Chip>
            )}
            {!cargando && origen === "snapshot" && (
              <Chip tono="ambar">
                datos congelados{edad ? ` · ${edad}` : ""} · backend no disponible
              </Chip>
            )}
            {!cargando && origen === "backend" && <Chip tono="verde">backend en vivo</Chip>}
            {!cargando && origen === "precalculado" && modo === "tiempo-real" && (
              <Chip>predicciones del clásico · sin backend</Chip>
            )}
            {!cargando && origen === "precalculado" && modo !== "tiempo-real" && (
              <Chip>ventana fija · precalculado sin backend</Chip>
            )}
          </div>
        )}

        {modo === "historico" &&
          modeloElegido === "baseline" &&
          (desde || hasta) &&
          origen === "snapshot" && (
            <p className="mt-2.5 text-[12.5px] text-oro">
              El rango de fechas requiere el backend en vivo; el snapshot congelado solo trae las
              últimas velas y no puede filtrarse por fecha.
            </p>
          )}

        <p className="mt-5 max-w-3xl border-l-2 border-linea-fuerte pl-4 text-[14.5px] leading-[1.65] text-tinta-2">
          {modoActual.descripcion}
        </p>

        {error && (
          <div className="mt-5 rounded-xl border-l-2 border-[#9c3a2a] bg-blanco p-4 text-[13.5px] text-[#8c2f22] shadow-placa">
            {error}
          </div>
        )}

        {!cargando && datos?.modelo === "baseline_trivial" && (
          <Nota tono="ambar">
            <strong className="font-semibold text-tinta">
              Este gráfico usa el baseline trivial.
            </strong>{" "}
            Responde siempre «Continuidad» y no detecta ningún giro. Está a propósito: es el piso
            obligatorio contra el que se compara todo, y demuestra por qué no reportamos exactitud
            como métrica principal.{" "}
            {modo === "historico" ? (
              <>Para ver el modelo fundacional, usá el selector de arriba.</>
            ) : modo === "sintetico" ? (
              <>
                El modo sintético todavía no tiene selector de modelo; en histórico sí podés
                alternar a Fundacional.
              </>
            ) : (
              <>
                Tiempo real todavía no tiene selector de modelo; en histórico sí podés alternar a
                Fundacional.
              </>
            )}
          </Nota>
        )}

        {!cargando && datos?.modelo === "chronos_bolt" && (
          <Nota>
            <strong className="font-semibold text-tinta">
              Predicciones precalculadas del modelo fundacional (Chronos-Bolt).
            </strong>{" "}
            Correrlo en vivo tarda del orden de minutos sobre el panel completo (~12,6 ms/vela
            medido), así que esta vista muestra una ventana fija —la misma partición de validación
            que usa la comparación de modelos de abajo— en vez de un rango libre. Para otro activo
            o rango, usá Baseline.
          </Nota>
        )}

        {/* Los dos avisos de Tiempo real van juntos, en dos columnas, sin perder una
            palabra: la D21 pide que se digan, no que se griten. */}
        {modo === "tiempo-real" && !cargando && datos && configuracion && (
          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            <div
              className="rounded-xl border-l-2 border-acento bg-blanco px-5 py-4 text-[13px] leading-[1.6] text-tinta-2 shadow-placa"
              data-testid="vista-sin-confirmar"
            >
              <strong className="font-semibold text-tinta">
                Las últimas {configuracion.latencia_real} velas ({horasAnticipacion} horas) todavía
                no tienen confirmación.
              </strong>{" "}
              El modelo ya anunció qué cree que va a pasar —son las flechas—, pero saber si de
              verdad hubo un giro exige ver las {configuracion.w} velas posteriores, y esas todavía
              no ocurrieron. No es una limitación técnica: es lo que tarda el problema en
              verificarse solo.
            </div>

            {ultimaVela && (
              <div
                className={`rounded-xl border-l-2 bg-blanco px-5 py-4 text-[13px] leading-[1.6] text-tinta-2 shadow-placa ${
                  (diasDeAtraso ?? 0) > 1 ? "border-oro" : "border-linea-fuerte"
                }`}
                data-testid="ultima-vela"
              >
                <strong className="font-semibold text-tinta">
                  La última vela de este panel es del{" "}
                  {new Date(ultimaVela).toLocaleString("es-CR")}
                </strong>
                {(diasDeAtraso ?? 0) > 1 && <> — hace {diasDeAtraso} días.</>} Los datos son un
                snapshot congelado:{" "}
                <strong className="font-semibold text-tinta">
                  esto no es el mercado de ahora mismo
                </strong>
                , es el comportamiento del sistema sobre las últimas velas que tiene.
              </div>
            )}
          </div>
        )}

        <section className="placa mt-5 overflow-hidden" data-testid="vista">
          <div className="flex flex-wrap items-baseline justify-between gap-3 border-b border-linea px-6 py-4">
            <h3 className="font-display text-[19px] font-semibold tracking-[-0.01em] text-tinta">
              {modo === "sintetico"
                ? "Serie construida, con los giros que plantamos"
                : modo === "tiempo-real"
                  ? "LTC, últimas velas del panel"
                  : `${activo}, precio de cierre`}
            </h3>
            <div className="flex flex-wrap items-center gap-5">
              {modo === "tiempo-real" && operacion && elegido && (
                <label className="flex items-center gap-3 text-[13px] text-tinta-2">
                  umbral
                  <input
                    type="range"
                    min={0}
                    max={operacion.umbrales.length - 1}
                    step={1}
                    value={operacion.umbrales.findIndex((u) => u.umbral === elegido.umbral)}
                    onChange={(e) =>
                      setUmbral(operacion.umbrales[Number(e.target.value)].umbral)
                    }
                    className="umbral-claro w-32"
                    aria-label="Umbral en el visor"
                  />
                  <span className="cifra w-9 text-tinta">{elegido.umbral.toFixed(2)}</span>
                </label>
              )}
              <p className="cifra text-[12.5px] text-tinta-3">
                {datos ? `${datos.serie.length.toLocaleString("es-CR")} velas` : ""}
              </p>
            </div>
          </div>
          <div className="px-3 py-4">
            {cargando ? (
              <p
                className="py-24 text-center font-display text-[15px] italic text-tinta-3"
                data-testid="vista-cargando"
              >
                Cargando…
              </p>
            ) : datos ? (
              <Grafico
                puntos={datos.serie}
                umbral={modo === "tiempo-real" ? umbral : undefined}
              />
            ) : null}
          </div>
          {datos && <Leyenda balance={datos.balance} />}
        </section>
      </Seccion>

      {/* ------------------------------------------------------------- medida */}
      <Seccion
        id="medida"
        rotulo="La medida"
        titulo="Ningún número solo. Cada uno con el listón que tenía que pasar."
        bajada={
          azar ? (
            <>
              El baseline aleatorio es el piso obligatorio del proyecto (D7). Va junto a cada cifra
              sobre el mismo eje, porque un número suelto no se puede leer hasta saber que el azar
              saca <span className="cifra text-tinta">{azar.f1_macro.toFixed(3)}</span>.
            </>
          ) : null
        }
      >
        {datos && (
          <div className="placa overflow-hidden" data-testid="metricas">
            <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-linea px-6 py-4">
              <h3 className="font-display text-[19px] font-semibold tracking-[-0.01em] text-tinta">
                Lo que mide la vista que tenés arriba
              </h3>
              <p className="font-display text-[13.5px] italic text-tinta-3">
                barra, lo medido · muesca, el azar · eje de 0 a 1
              </p>
            </div>
            <Metrica
              titulo="F1 macro"
              valor={datos.metricas.f1_macro}
              piso={azar?.f1_macro}
              principal
              nota="El número que decide: pesa igual las tres clases, así que si el modelo ignora los giros (la clase rara), esto baja"
              testId="f1-macro"
            />
            <Metrica
              titulo="Precisión direccional"
              valor={datos.metricas.precision_direccional}
              piso={azar?.precision_direccional}
              nota="De los giros reales, cuántos se anunciaron bien"
              testId="precision-direccional"
            />
            <Metrica
              titulo="F1 Máximo"
              valor={datos.metricas.f1_maximo}
              piso={azar?.f1_maximo}
              nota="Clase minoritaria: giros al alza"
            />
            <Metrica
              titulo="F1 Mínimo"
              valor={datos.metricas.f1_minimo}
              piso={azar?.f1_minimo}
              nota="Clase minoritaria: giros a la baja"
            />
            <Metrica
              titulo="F1 Continuidad"
              valor={datos.metricas.f1_continuidad}
              piso={azar?.f1_continuidad}
              nota="Clase mayoritaria: sin giro"
            />
            {/* Issue #151.3: la exactitud salia con el mismo peso visual que el F1
                macro y no decide nada. Va atenuada y al final, con su piso al lado. */}
            <Metrica
              titulo="Exactitud"
              valor={datos.metricas.exactitud}
              piso={azar?.exactitud}
              atenuada
              nota="No decide nada. Como la Continuidad domina los datos, un modelo que nunca avisa un giro ya saca exactitud alta"
              testId="exactitud"
            />
            <Metrica
              titulo="Observaciones"
              valor={datos.metricas.n}
              entero
              nota="Velas evaluadas en esta vista"
              testId="observaciones"
            />
          </div>
        )}

        {comparacion && (
          <div className="placa mt-8 overflow-hidden">
            <div className="border-b border-linea px-6 py-4">
              <h3 className="font-display text-[19px] font-semibold tracking-[-0.01em] text-tinta">
                Los {comparacion.modelos.length} modelos, sobre la misma partición
              </h3>
              <p className="mt-1 text-[12.5px] text-tinta-3">
                {/* La evidencia de M3 trae "validacion" sin tilde; se corrige solo en la
                    vista, sin tocar docs/evidencias/, que no es mio y se regenera por script. */}
                {comparacion.particion.conjunto === "validacion"
                  ? "validación"
                  : comparacion.particion.conjunto}{" "}
                ({comparacion.particion.intervalo}, w={comparacion.particion.w}, h=
                {comparacion.particion.h}, n={comparacion.n}). Fuente:{" "}
                <code className="cifra text-[12px]">{comparacion.fuente}</code>.
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[560px] text-left">
                <tbody>
                  {comparacion.modelos.map((m) => (
                    <tr key={m.clave} className="border-b border-linea last:border-0">
                      <td className="px-6 py-4 align-middle">
                        <p className="font-display text-[17px] font-semibold text-tinta">
                          {m.etiqueta}
                        </p>
                        <p className="mt-0.5 text-[12.5px] text-tinta-3">{m.papel}</p>
                        {m.corrida_individual && (
                          <p
                            className="mt-1 text-[12px] text-oro"
                            data-testid={`${m.clave}-corrida-individual`}
                          >
                            corrida individual · media de 5 semillas{" "}
                            {m.media_multisemilla?.toFixed(3)} · rango{" "}
                            {m.rango_semillas?.toFixed(3)}
                          </p>
                        )}
                      </td>
                      <td className="w-[42%] px-6 py-4 align-middle">
                        <Regla valor={m.f1_macro} piso={azar?.f1_macro} />
                      </td>
                      <td className="cifra px-6 py-4 text-right align-middle text-[19px] font-medium text-tinta">
                        {m.f1_macro.toFixed(3)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {comparacion.modelos.some((m) => m.corrida_individual) && (
              <p className="border-t border-linea px-6 py-4 text-[12px] leading-[1.6] text-tinta-3">
                «Corrida individual»: ese modelo se entrena con una semilla aleatoria, y la cifra de
                arriba es una sola corrida, no el promedio — puede caer en cualquier punto del rango
                mostrado. En los dos casos la corrida publicada acá resultó ser la más alta de las
                medidas, así que la ventaja de un modelo sobre otro en esta tabla puede estar
                exagerada frente al promedio declarado. Baseline aleatorio usa semilla fija y el
                modelo fundacional es determinista: a esos dos no les aplica (issue #92).
              </p>
            )}
          </div>
        )}
      </Seccion>

      {/* ------------------------------------------------------------ limites */}
      <Seccion
        id="limites"
        rotulo="Los límites"
        titulo="Lo que no sabemos, en la misma página que lo que sí."
        bajada="Un demo que solo enseña sus mejores cifras no es un demo, es publicidad. Esto sale de las mismas mediciones que todo lo demás."
      >
        <div className="grid gap-x-14 gap-y-9 sm:grid-cols-2">
          {[
            clasico && azar
              ? {
                  t: "Le ganamos al azar por poco",
                  d: `El F1 macro del clásico es ${clasico.f1_macro.toFixed(3)} y el del azar ${azar.f1_macro.toFixed(3)}. La diferencia existe y está medida, pero nadie debería leer esto como un sistema resuelto.`,
                }
              : null,
            datos && azar
              ? {
                  t: "La clase rara sigue siendo difícil",
                  d: `Sobre la vista que estás mirando, el F1 de la clase Máximo es ${datos.metricas.f1_maximo.toFixed(3)} y el piso del azar ${azar.f1_maximo?.toFixed(3)}. Se muestra igual: si una cifra es mala, va con su contexto.`,
                }
              : null,
            ultimaVela
              ? {
                  t: "El panel está congelado",
                  d: `La última vela es del ${new Date(ultimaVela).toLocaleDateString("es-CR")}. Esto no es el mercado de ahora mismo, es el comportamiento del sistema sobre las últimas velas que tiene.`,
                }
              : null,
            {
              t: "Una corrida no es un promedio",
              d: "Los modelos que se entrenan con semilla aleatoria varían entre corridas, y la que se publicó resultó ser la más alta de las cinco medidas (issue #92).",
            },
          ]
            .filter((x): x is { t: string; d: string } => x !== null)
            .map((p, i) => (
              <div key={p.t} className="border-t border-linea pt-5">
                <p className="cifra text-[12.5px] text-tinta-3">{String(i + 1).padStart(2, "0")}</p>
                <h3 className="mt-2 font-display text-[21px] font-semibold leading-snug text-tinta">
                  {p.t}
                </h3>
                <p className="mt-2.5 text-[15px] leading-[1.65] text-tinta-2">{p.d}</p>
              </div>
            ))}
        </div>
      </Seccion>

      <Pie configuracion={configuracion} />
    </div>
  );
}

/* -------------------------------------------------------------------- piezas */

function BarraFija({ configuracion }: { configuracion: Configuracion | null }) {
  const [bajado, setBajado] = useState(false);
  useEffect(() => {
    const alScroll = () => setBajado(window.scrollY > 140);
    alScroll();
    window.addEventListener("scroll", alScroll, { passive: true });
    return () => window.removeEventListener("scroll", alScroll);
  }, []);
  return (
    <div
      className={`fixed inset-x-0 top-0 z-50 transition-colors duration-500 ${
        bajado ? "border-b border-white/10 bg-noche/85 backdrop-blur-md" : "border-b border-transparent"
      }`}
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-6 py-3.5 sm:px-8">
        <a
          href="#portada"
          className="font-display text-[17px] font-semibold tracking-[-0.01em] text-claro"
        >
          Inflexión<span className="text-azul-claro">.</span>LTC
        </a>
        <nav className="hidden items-center gap-7 md:flex">
          {SECCIONES.map((s) => (
            <a
              key={s.id}
              href={`#${s.id}`}
              className="text-[13.5px] text-claro-2 transition-colors hover:text-claro"
            >
              {s.texto}
            </a>
          ))}
        </nav>
        {configuracion && (
          <span className="cifra hidden text-[12px] text-claro-3 sm:block">
            {configuracion.granularidad} · w{configuracion.w} · h{configuracion.h}
          </span>
        )}
      </div>
    </div>
  );
}

function Seccion({
  id,
  rotulo,
  titulo,
  bajada,
  oscura,
  children,
}: {
  id: string;
  rotulo: string;
  titulo: string;
  bajada?: React.ReactNode;
  oscura?: boolean;
  children: React.ReactNode;
}) {
  return (
    <section
      id={id}
      className={`scroll-mt-16 py-20 sm:py-28 ${oscura ? "bg-noche" : "bg-papel"}`}
    >
      <div className="mx-auto max-w-6xl px-6 sm:px-8">
        <p
          className={`font-display text-[15px] italic ${oscura ? "text-azul-claro" : "text-acento"}`}
        >
          {rotulo}
        </p>
        <h2
          className={`mt-3 max-w-[22ch] font-display text-[clamp(1.8rem,3.4vw,2.8rem)] font-semibold leading-[1.1] tracking-[-0.02em] ${
            oscura ? "text-claro" : "text-tinta"
          }`}
        >
          {titulo}
        </h2>
        {bajada && (
          <div
            className={`mt-5 max-w-[62ch] text-[16px] leading-[1.7] ${
              oscura ? "text-claro-2" : "text-tinta-2"
            }`}
          >
            {bajada}
          </div>
        )}
        <div className="mt-11">{children}</div>
      </div>
    </section>
  );
}

function CifraPortada({
  valor,
  rotulo,
  grande,
}: {
  valor: string;
  rotulo: string;
  grande?: boolean;
}) {
  return (
    <div>
      <p
        className={`font-display font-semibold leading-[0.85] tracking-[-0.02em] text-claro [font-variant-numeric:tabular-nums] ${
          grande ? "text-[72px]" : "text-[38px] text-claro-2"
        }`}
      >
        {valor}
      </p>
      <p className="mt-3 font-display text-[14px] italic text-claro-3">{rotulo}</p>
    </div>
  );
}

/** La serie real de LTC, a sangre, cerrando la portada. */
function TrazoPortada({ puntos }: { puntos: Punto[] | null }) {
  const dibujo = useMemo(() => {
    if (!puntos || puntos.length < 2) return null;
    const cierres = puntos.map((p) => p.cierre);
    const min = Math.min(...cierres);
    const max = Math.max(...cierres);
    if (!(max > min)) return null;
    const x = (i: number) => (i / (puntos.length - 1)) * 1000;
    const y = (v: number) => 150 - ((v - min) / (max - min)) * 120;
    const d = puntos
      .map((p, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(2)},${y(p.cierre).toFixed(2)}`)
      .join(" ");
    const giros = puntos
      .map((p, i) => ({ p, i }))
      .filter(({ p }) => p.etiqueta === 1 || p.etiqueta === 2)
      .map(({ p, i }) => ({ x: x(i), y: y(p.cierre), maximo: p.etiqueta === 1 }));
    return { linea: d, area: `${d} L1000,170 L0,170 Z`, giros };
  }, [puntos]);

  return (
    <div className="relative mt-14 h-[180px] w-full sm:h-[230px]">
      {dibujo && (
        <>
          <svg
            viewBox="0 0 1000 170"
            preserveAspectRatio="none"
            className="absolute inset-0 h-full w-full"
            aria-label="Precio de cierre de Litecoin en el panel exportado, con los giros confirmados"
          >
            <defs>
              <linearGradient id="bajoTrazo" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#8FB6F0" stopOpacity="0.20" />
                <stop offset="100%" stopColor="#8FB6F0" stopOpacity="0" />
              </linearGradient>
            </defs>
            <path d={dibujo.area} fill="url(#bajoTrazo)" />
            <path
              d={dibujo.linea}
              fill="none"
              stroke="#8FB6F0"
              strokeWidth="1.6"
              vectorEffect="non-scaling-stroke"
              className="traza"
            />
          </svg>
          {/* Los giros van como elementos posicionados y no como <circle>: con
              preserveAspectRatio="none" un circulo se deforma en elipse. */}
          <div className="absolute inset-0">
            {dibujo.giros.map((g, i) => (
              <span
                key={i}
                className="absolute block h-[5px] w-[5px] -translate-x-1/2 -translate-y-1/2 rounded-full"
                style={{
                  left: `${(g.x / 1000) * 100}%`,
                  top: `${(g.y / 170) * 100}%`,
                  background: g.maximo ? "#E8705F" : "#4FBF87",
                  opacity: 0.85,
                }}
              />
            ))}
          </div>
        </>
      )}
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-24 bg-gradient-to-b from-transparent to-papel" />
    </div>
  );
}

/** El diagrama de la ventana: dónde sale el aviso y dónde se confirma el giro. */
function Ventana({
  configuracion,
  horasAnticipacion,
}: {
  configuracion: Configuracion;
  horasAnticipacion: number | null;
}) {
  // A la izquierda hay que dibujar al menos `latencia` velas, que son mas que la
  // ventana: si no, el aviso cae fuera del diagrama y no se ve.
  const izquierda = Math.max(configuracion.w, configuracion.latencia_real) + 2;
  const total = izquierda + 1 + configuracion.w;
  const centro = izquierda;
  const aviso = centro - configuracion.latencia_real;
  return (
    <figure className="placa p-8">
      <div className="flex items-end gap-[3px]">
        {Array.from({ length: total }, (_, i) => {
          const esCentro = i === centro;
          const esAviso = i === aviso;
          const enVentana = Math.abs(i - centro) <= configuracion.w;
          const altura = 20 + Math.round(30 * Math.sin(((i + 1) / (total + 1)) * Math.PI));
          return (
            <div key={i} className="flex flex-1 flex-col items-center gap-2">
              <div
                className="w-full rounded-[2px]"
                style={{
                  height: esCentro ? 78 : esAviso ? 56 : altura,
                  background: esCentro
                    ? MAXIMO
                    : esAviso
                      ? "#345D9D"
                      : enVentana
                        ? "#D8DDE4"
                        : "#ECEEF1",
                }}
              />
              <span className="h-[7px] w-px bg-linea" />
            </div>
          );
        })}
      </div>

      <div className="mt-2 flex" aria-hidden="true">
        <span style={{ flex: aviso }} />
        <span className="relative border-t border-acento" style={{ flex: configuracion.latencia_real }}>
          <span className="absolute -top-[5px] left-0 h-[9px] w-px bg-acento" />
          <span className="absolute -top-[5px] right-0 h-[9px] w-px bg-acento" />
          <span className="mt-1.5 block text-center text-[12.5px] text-acento">
            {horasAnticipacion ?? "?"} h de anticipación
          </span>
        </span>
        <span style={{ flex: configuracion.w }} />
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-x-7 gap-y-2 border-t border-linea pt-4 text-[13px] text-tinta-2">
        <span className="flex items-center gap-2">
          <span className="inline-block h-2.5 w-2.5 rounded-[2px]" style={{ background: "#345D9D" }} />
          aquí sale el aviso
        </span>
        <span className="flex items-center gap-2">
          <span className="inline-block h-2.5 w-2.5 rounded-[2px]" style={{ background: MAXIMO }} />
          aquí se confirma el giro
        </span>
        <span className="flex items-center gap-2 text-tinta-3">
          <span className="inline-block h-2.5 w-2.5 rounded-[2px] bg-[#D8DDE4]" />
          las {configuracion.w} velas de cada lado que confirman
        </span>
      </div>
      <figcaption className="mt-4 text-[13.5px] leading-[1.6] text-tinta-3">
        Ventana de {configuracion.w} velas a cada lado (w={configuracion.w}), horizonte h=
        {configuracion.h}. Entre el aviso y la confirmación pasan {configuracion.latencia_real}{" "}
        velas de {configuracion.granularidad}.
      </figcaption>
    </figure>
  );
}

/**
 * La regla: una cifra medida y su piso, sobre el mismo eje de 0 a 1.
 *
 * El eje llega a 1 y no al maximo de cada fila a proposito: recortarlo haria que
 * 0,390 se viera "lleno", y esa es justo la lectura que el informe no autoriza.
 */
function Regla({ valor, piso }: { valor: number; piso?: number }) {
  if (Number.isNaN(valor)) return <span className="cifra text-tinta-3">—</span>;
  const pct = (v: number) => `${Math.max(0, Math.min(100, v * 100))}%`;
  return (
    <div className="relative h-[11px] w-full rounded-full bg-[#ECEAE4]">
      <div
        className="absolute inset-y-0 left-0 rounded-full bg-noche-3"
        style={{ width: pct(valor) }}
      />
      {piso !== undefined && !Number.isNaN(piso) && (
        <span
          className="absolute -top-[5px] h-[21px] w-[2px] rounded-full bg-[#A8541F]"
          style={{ left: pct(piso) }}
          title={`piso del azar: ${piso.toFixed(3)}`}
        />
      )}
    </div>
  );
}

function Nota({ children, tono }: { children: React.ReactNode; tono?: "ambar" }) {
  return (
    <div
      className={`mt-5 rounded-xl border-l-2 bg-blanco px-5 py-4 text-[13px] leading-[1.6] text-tinta-2 shadow-placa ${
        tono === "ambar" ? "border-oro" : "border-acento"
      }`}
    >
      {children}
    </div>
  );
}

function Chip({
  children,
  tono,
  title,
}: {
  children: React.ReactNode;
  tono?: "ambar" | "verde";
  title?: string;
}) {
  const estilos =
    tono === "ambar"
      ? "border-[#d8b45c] bg-[#fdf6e6] text-[#7a530f]"
      : tono === "verde"
        ? "border-[#8fc3a4] bg-[#eff8f2] text-[#14603a]"
        : "border-linea bg-blanco text-tinta-2";
  return (
    <span
      className={`rounded-full border px-3 py-1.5 text-[11.5px] font-medium ${estilos}`}
      title={title}
    >
      {children}
    </span>
  );
}

/**
 * Issue #99, puntos 3 y 4: el grafico dibuja marcadores en un <canvas>, sin
 * texto que los explique. Usa los mismos colores que Grafico.tsx (importados de
 * ahi, no copiados) para que nunca puedan desincronizarse.
 */
function Leyenda({ balance }: { balance?: Respuesta["balance"] }) {
  const continuidad = balance?.find((b) => b.codigo === 3);
  return (
    <div className="border-t border-linea px-6 py-4" data-testid="leyenda">
      <div className="flex flex-wrap gap-x-7 gap-y-2 text-[12.5px] text-tinta-2">
        <span className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: MAXIMO }} />
          <strong className="font-semibold text-tinta">Máximo</strong> el precio deja de subir y
          empieza a bajar
        </span>
        <span className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: MINIMO }} />
          <strong className="font-semibold text-tinta">Mínimo</strong> el precio deja de bajar y
          empieza a subir
        </span>
        <span className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full border-2 border-linea-fuerte" />
          <strong className="font-semibold text-tinta">Continuidad</strong> sigue como estaba, sin
          giro (sin marcador en el gráfico)
        </span>
        <span className="text-tinta-3">
          círculo = ocurrió de verdad · flecha = lo que anunció el modelo
        </span>
      </div>
      {/* Issue #151.4: la leyenda explicaba los colores pero no el problema. */}
      {continuidad && (
        <p className="mt-3 border-t border-linea pt-3 text-[12.5px] leading-[1.6] text-tinta-2">
          <strong className="font-semibold text-tinta">
            El {continuidad.porcentaje.toFixed(1)} % de las velas son continuidad.
          </strong>{" "}
          Por eso esto es difícil: los giros son raros, y un modelo que no avisara ninguno
          acertaría igual ese {continuidad.porcentaje.toFixed(1)} % de las veces.
        </p>
      )}
    </div>
  );
}

/**
 * El punto de operación (issue #150). Las cifras **no se calculan aquí**: salen
 * medidas sobre nueve tramos y llegan en `punto-de-operacion.json`. Y la del azar
 * va siempre al lado, porque «acierta el 10 %» a secas no significa nada.
 */
function ControlDeUmbral({
  operacion,
  umbral,
  elegido,
  onCambio,
}: {
  operacion: PuntoDeOperacion;
  umbral: number;
  elegido: Umbral;
  onCambio: (v: number) => void;
}) {
  const veces = elegido.precision_azar > 0 ? elegido.precision / elegido.precision_azar : NaN;
  const gana = elegido.tramos_a_favor === elegido.tramos_medidos;

  // El techo cubre las DOS curvas: tomando solo la del modelo, en el umbral mas
  // alto la del azar se salia del marco, y esa es justo la que hay que comparar.
  const techo =
    Math.max(
      ...operacion.umbrales.map((u) => u.precision),
      ...operacion.umbrales.map((u) => u.precision_azar),
    ) * 1.1;
  const n = operacion.umbrales.length;
  const indice = operacion.umbrales.findIndex((u) => u.umbral === elegido.umbral);
  const xDe = (i: number) => (n > 1 ? (i / (n - 1)) * 100 : 50);
  const yDe = (v: number) => 40 - (v / techo) * 36;
  const trazo = (clave: "precision" | "precision_azar") =>
    operacion.umbrales.map((u, i) => `${i === 0 ? "M" : "L"}${xDe(i)},${yDe(u[clave])}`).join(" ");

  return (
    <div
      className="rounded-2xl border border-white/10 bg-noche-2 p-6 shadow-alta sm:p-9"
      data-testid="control-umbral"
    >
      {/* La curva entera, medida, detras del deslizador: con ella se ve la FORMA
          --que la precision sube al callarse y que la del azar no--, que es el
          argumento completo del #150 en una imagen. Son los once puntos medidos. */}
      <div className="relative">
        <svg
          viewBox="0 0 100 40"
          preserveAspectRatio="none"
          className="h-[150px] w-full overflow-hidden sm:h-[190px]"
          aria-hidden="true"
        >
          <defs>
            <linearGradient id="bajoPrecision" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#8FB6F0" stopOpacity="0.26" />
              <stop offset="100%" stopColor="#8FB6F0" stopOpacity="0" />
            </linearGradient>
          </defs>
          {[0, 1, 2, 3].map((i) => (
            <line
              key={i}
              x1="0"
              x2="100"
              y1={i * 13.3}
              y2={i * 13.3}
              stroke="rgba(233,240,250,0.10)"
              strokeWidth="0.3"
              vectorEffect="non-scaling-stroke"
            />
          ))}
          <path d={`${trazo("precision")} L100,40 L0,40 Z`} fill="url(#bajoPrecision)" />
          <path
            d={trazo("precision_azar")}
            fill="none"
            stroke="rgba(233,240,250,0.45)"
            strokeWidth="1.3"
            strokeDasharray="3 3"
            vectorEffect="non-scaling-stroke"
          />
          <path
            d={trazo("precision")}
            fill="none"
            stroke="#8FB6F0"
            strokeWidth="2.4"
            strokeLinejoin="round"
            vectorEffect="non-scaling-stroke"
          />
          <line
            x1={xDe(indice)}
            x2={xDe(indice)}
            y1="0"
            y2="40"
            stroke="rgba(233,240,250,0.55)"
            strokeWidth="1"
            vectorEffect="non-scaling-stroke"
          />
        </svg>
        <span
          className="pointer-events-none absolute block h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-noche-2 bg-claro"
          style={{ left: `${xDe(indice)}%`, top: `${(yDe(elegido.precision) / 40) * 100}%` }}
        />
      </div>

      <div className="mt-5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-6 text-[13px]">
          <span className="flex items-center gap-2 text-azul-claro">
            <span className="inline-block h-[2px] w-5 bg-azul-claro" /> acierta el modelo
          </span>
          <span className="flex items-center gap-2 text-claro-3">
            <span
              className="inline-block h-[2px] w-5"
              style={{
                backgroundImage:
                  "repeating-linear-gradient(90deg,rgba(233,240,250,.5) 0 3px,transparent 3px 6px)",
              }}
            />
            acierta el azar
          </span>
        </div>
        <p className="flex items-baseline gap-3">
          <span className="font-display text-[14px] italic text-claro-3">umbral</span>
          <span className="cifra text-[26px] font-medium text-claro">
            {elegido.umbral.toFixed(2)}
          </span>
        </p>
      </div>

      <input
        type="range"
        min={0}
        max={n - 1}
        step={1}
        value={indice}
        onChange={(e) => onCambio(operacion.umbrales[Number(e.target.value)].umbral)}
        className="umbral mt-2 h-7 w-full"
        aria-label="Umbral de confianza para avisar"
      />

      <div className="mt-7 grid gap-px overflow-hidden rounded-xl bg-white/10 sm:grid-cols-4">
        <Dato
          titulo="Avisa en"
          valor={`${(elegido.cobertura * 100).toFixed(1)} %`}
          nota="de las velas"
        />
        <Dato
          titulo="Acierta"
          valor={elegido.precision.toFixed(3)}
          nota="de los avisos que da"
          destacado
        />
        <Dato
          titulo="El azar, igual de hablador"
          valor={elegido.precision_azar.toFixed(3)}
          nota="avisando en el mismo % de velas"
        />
        <Dato
          titulo="Veces el azar"
          valor={Number.isNaN(veces) ? "—" : `${veces.toFixed(2)}×`}
          nota={`${elegido.tramos_a_favor} de ${elegido.tramos_medidos} tramos a favor`}
          destacado={gana}
        />
      </div>

      <p className="mt-6 max-w-[74ch] text-[13.5px] leading-[1.65] text-claro-2">
        {umbral === 0 ? (
          <>
            <strong className="font-semibold text-amber-200">
              En 0,00 el sistema no se calla nunca.
            </strong>{" "}
            Avisa en todas las velas, y acierta menos que la frecuencia base de giros —{" "}
            {(operacion.frecuencia_base_de_giros * 100).toFixed(1)} %. Como alarma, avisar siempre
            es peor que reaccionar al azar con la misma frecuencia. Subí el umbral.
          </>
        ) : (
          <>
            Mover esto{" "}
            <strong className="font-semibold text-claro">
              no cambia el modelo ni reentrena nada
            </strong>
            : es el punto donde se decide que un aviso vale la pena darlo. Medido sobre{" "}
            <span className="cifra">
              {operacion.n_observaciones.toLocaleString("es-CR").replace(/ /g, " ")}
            </span>{" "}
            observaciones fuera de muestra, en {operacion.tramos} tramos. Las cifras del informe se
            miden con cobertura del 100 % y se quedan así.
          </>
        )}
      </p>
    </div>
  );
}

function Dato({
  titulo,
  valor,
  nota,
  destacado,
}: {
  titulo: string;
  valor: string;
  nota: string;
  destacado?: boolean;
}) {
  return (
    <div className={`px-5 py-4 ${destacado ? "bg-noche-3" : "bg-noche-2"}`}>
      <p className="font-display text-[13.5px] italic text-claro-3">{titulo}</p>
      <p
        className={`cifra mt-2 text-[28px] font-medium leading-none ${
          destacado ? "text-azul-claro" : "text-claro"
        }`}
      >
        {valor}
      </p>
      <p className="mt-2 text-[12px] leading-[1.45] text-claro-3">{nota}</p>
    </div>
  );
}

function Metrica({
  titulo,
  valor,
  entero,
  nota,
  testId,
  piso,
  principal,
  atenuada,
}: {
  titulo: string;
  valor: number;
  entero?: boolean;
  nota?: string;
  testId?: string;
  /** El baseline aleatorio en esta misma métrica (D7). Issue #151.2. */
  piso?: number;
  principal?: boolean;
  atenuada?: boolean;
}) {
  const texto = Number.isNaN(valor)
    ? "—"
    : entero
      ? valor.toLocaleString("es-CR")
      : valor.toFixed(3);
  const supera = piso !== undefined && !Number.isNaN(valor) && valor > piso;
  return (
    <div
      className={`grid items-center gap-x-8 gap-y-3 border-b border-linea px-6 py-5 last:border-0 sm:grid-cols-[minmax(0,17rem)_minmax(0,1fr)_8rem] ${
        atenuada ? "bg-papel" : ""
      }`}
      data-testid={testId}
    >
      <div>
        <p className="flex flex-wrap items-baseline gap-x-2.5 gap-y-1">
          <span
            className={`font-display font-semibold tracking-[-0.01em] ${
              principal ? "text-[23px]" : "text-[19px]"
            } ${atenuada ? "text-tinta-2" : "text-tinta"}`}
          >
            {titulo}
          </span>
          {principal && (
            <span className="rounded-full bg-noche px-2.5 py-0.5 text-[11px] font-medium text-claro">
              decide
            </span>
          )}
          {atenuada && (
            <span className="rounded-full border border-linea-fuerte px-2.5 py-0.5 text-[11px] text-tinta-3">
              no decide
            </span>
          )}
        </p>
        {nota && (
          <p className="mt-1.5 max-w-[36ch] text-[12.5px] leading-[1.5] text-tinta-3">{nota}</p>
        )}
      </div>

      <div className="min-w-0">
        {entero ? (
          <p className="text-[12.5px] text-tinta-3">
            no es una proporción: no tiene piso contra el que compararse
          </p>
        ) : (
          <Regla valor={valor} piso={piso} />
        )}
      </div>

      <div className="sm:text-right">
        <p
          className={`cifra font-medium leading-none ${
            principal ? "text-[36px]" : "text-[24px]"
          } ${atenuada ? "text-tinta-2" : "text-tinta"}`}
          data-testid={testId && `${testId}-valor`}
        >
          {texto}
        </p>
        {piso !== undefined && !Number.isNaN(piso) && (
          <p className="mt-2 text-[12px] leading-[1.45] text-tinta-3">
            <span className="cifra">azar {piso.toFixed(3)}</span>
            <br />
            <span className={`font-medium ${supera ? "text-[#16653a]" : "text-[#A8541F]"}`}>
              {supera ? "lo supera" : "no lo supera"}
            </span>
          </p>
        )}
      </div>
    </div>
  );
}

function Pie({ configuracion }: { configuracion: Configuracion | null }) {
  return (
    <footer className="bg-noche pb-14 pt-20">
      <div className="mx-auto max-w-6xl px-6 sm:px-8">
        <p className="max-w-[26ch] font-display text-[clamp(1.5rem,2.8vw,2.2rem)] font-semibold leading-[1.15] tracking-[-0.02em] text-claro">
          Caso n.<sup>o</sup> 1 — Detección de puntos de inflexión en criptomonedas
        </p>
        <div className="mt-12 grid gap-10 border-t border-white/10 pt-10 sm:grid-cols-3">
          <div>
            <p className="font-display text-[14px] italic text-claro-3">Equipo</p>
            <p className="mt-2.5 text-[14.5px] leading-[1.8] text-claro-2">
              Alejandro Zamora
              <br />
              Jose Pablo Monestel
              <br />
              Isaac Morun
              <br />
              Fabrizio Espinoza Arce
            </p>
          </div>
          <div>
            <p className="font-display text-[14px] italic text-claro-3">De dónde salen los datos</p>
            <p className="mt-2.5 text-[14.5px] leading-[1.7] text-claro-2">
              Precios de la API pública de Binance (
              <code className="cifra text-[12.5px] text-claro">api.binance.com/api/v3/klines</code>
              ) con <code className="cifra text-[12.5px] text-claro">src/panel/descarga.py</code>.
              Métricas de <code className="cifra text-[12.5px] text-claro">contracts/metrics.py</code>.
              {configuracion?.panel && (
                <>
                  {" "}
                  El panel va de {configuracion.panel.desde.slice(0, 10)} a{" "}
                  {configuracion.panel.hasta.slice(0, 10)}, y esta vista muestra las últimas{" "}
                  {configuracion.panel.velas_exportadas_por_activo.toLocaleString("es-CR")} velas
                  por activo.
                </>
              )}
            </p>
          </div>
          <div>
            {/* El logotipo de la esquina del grafico lo dibuja la propia libreria y es
                su atribucion obligatoria. Se deja donde esta --quitarlo seria incumplir
                su licencia-- pero sin esta linea se lee como que los precios salen de
                ahi, que es lo primero que pregunto quien vio la aplicacion. */}
            <p className="font-display text-[14px] italic text-claro-3">El gráfico</p>
            <p className="mt-2.5 text-[14.5px] leading-[1.7] text-claro-2">
              Se dibuja con Lightweight Charts™ de TradingView, y el logotipo de su esquina es la
              atribución que esa biblioteca exige. Los precios no vienen de TradingView.
            </p>
          </div>
        </div>
        <div className="mt-10 flex flex-wrap items-center justify-between gap-4 border-t border-white/10 pt-6">
          <a
            className="text-[14px] text-azul-claro underline underline-offset-4"
            href="https://github.com/NeoFao/caso1-ltc-inflexion"
          >
            Código y documentación
          </a>
          <p className="cifra text-[12px] text-claro-3">
            esta aplicación no calcula ninguna métrica
          </p>
        </div>
      </div>
    </footer>
  );
}
