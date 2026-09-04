import { useEffect, useState } from "react";

import Grafico, { MAXIMO, MINIMO } from "./Grafico";
import {
  type Comparacion,
  type Configuracion,
  type Origen,
  type Respuesta,
  antiguedad,
  obtenerComparacion,
  obtenerConfiguracion,
  obtenerHistorico,
  obtenerHistoricoFundacional,
  obtenerSintetico,
} from "./api";

type Modelo = "baseline" | "fundacional";

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

type Modo = "sintetico" | "historico" | "tiempo-real";

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
    descripcion:
      "LTC al día. El modelo anuncia cada vela en el momento, con la información disponible hasta ese instante; la confirmación —si de verdad fue un giro— tarda lo que el sistema tarda en verla venir.",
  },
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

  useEffect(() => {
    obtenerConfiguracion()
      .then((r) => setConfiguracion(r.datos))
      .catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    obtenerComparacion().catch(() => null).then((c) => c && setComparacion(c));
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
    // Fundacional no tiene ruta de backend ni acepta rango (ver api.ts): correrlo
    // en vivo tarda minutos sobre el panel completo. Se envuelve en la misma forma
    // ConOrigen que las demas peticiones para que el resto del efecto no distinga
    // de donde viene el dato.
    //
    // Tiempo real (D21, issue #28) reutiliza exactamente el mismo historico de
    // LTC: no hace falta un endpoint nuevo. La distincion "confirmado / sin
    // confirmar" ya viene en el dato -- etiquetar() deja las ultimas w velas con
    // etiqueta null porque no tienen ventana completa para confirmar un giro, y
    // predicha esta presente igual, porque el modelo si predice con lo que sabe
    // hasta ese instante. Grafico.tsx ya distingue las dos cosas sin cambios: sin
    // etiqueta no hay circulo (no hay giro confirmado que marcar), pero la flecha
    // de la prediccion se dibuja igual.
    const peticion =
      modo === "sintetico"
        ? obtenerSintetico(300)
        : modeloElegido === "fundacional"
          ? obtenerHistoricoFundacional().then((datos) => ({
              datos,
              origen: "precalculado" as Origen,
            }))
          : modo === "tiempo-real"
            ? obtenerHistorico("LTC")
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
  const horasAnticipacion = configuracion
    ? configuracion.latencia_real * horasPorVela(configuracion.granularidad)
    : null;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-5">
          <p className="text-xs font-semibold tracking-[0.2em] text-[#345d9d]">
            CASO N.º 1 · SEÑALES Y SISTEMAS · 3.<sup>ER</sup> TRIMESTRE 2026
          </p>
          <h1 className="mt-1 text-2xl font-bold text-[#1b2a4a]">
            Puntos de inflexión en el precio de Litecoin
          </h1>
          <p className="mt-1 max-w-2xl text-sm text-slate-600">
            Avisa cuándo el precio está por dar la vuelta —de subir a bajar, o al revés—
            {horasAnticipacion ? ` con ${horasAnticipacion} horas de anticipación.` : "."}
          </p>
          <p className="mt-1 text-sm text-slate-500">
            Alejandro Zamora · Jose Pablo Monestel · Isaac Morun · Fabrizio Espinoza Arce
          </p>
          {configuracion && (
            <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
              <Chip title="w: cuántas velas antes y después se miran para confirmar un giro. h: con cuánta anticipación se anuncia, antes de que el giro termine de confirmarse.">
                ventana w={configuracion.w} · horizonte h={configuracion.h} ·{" "}
                {configuracion.granularidad}
              </Chip>
              <Chip>
                anticipación efectiva {horasAnticipacion ?? "?"} horas ({configuracion.latencia_real}{" "}
                velas de {configuracion.granularidad})
              </Chip>
              {configuracion.provisional && (
                <Chip tono="ambar">parámetros provisionales, sin congelar</Chip>
              )}
              {!cargando && origen === "snapshot" && (
                <Chip tono="ambar">
                  datos congelados{edad ? ` · ${edad}` : ""} · backend no disponible
                </Chip>
              )}
              {!cargando && origen === "backend" && <Chip tono="verde">backend en vivo</Chip>}
              {!cargando && origen === "precalculado" && (
                <Chip>ventana fija · precalculado sin backend</Chip>
              )}
            </div>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-6">
        {!cargando && datos?.modelo === "baseline_trivial" && (
          <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            <strong>Este gráfico usa el baseline trivial.</strong> Responde siempre «Continuidad» y
            no detecta ningún giro. Está a propósito: es el piso obligatorio contra el que se compara
            todo, y demuestra por qué no reportamos exactitud como métrica principal.{" "}
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
          </div>
        )}

        {!cargando && datos?.modelo === "chronos_bolt" && (
          <div className="mb-4 rounded-lg border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-900">
            <strong>Predicciones precalculadas del modelo fundacional (Chronos-Bolt).</strong>{" "}
            Correrlo en vivo tarda del orden de minutos sobre el panel completo (~12,6 ms/vela
            medido), así que esta vista muestra una ventana fija —la misma partición de validación
            que usa la comparación de modelos de abajo— en vez de un rango libre. Para otro activo o
            rango, usá Baseline.
          </div>
        )}

        <div className="flex flex-wrap items-center gap-3">
          <nav className="flex gap-2">
            {MODOS.map((m) => (
              <button
                key={m.id}
                onClick={() => setModo(m.id)}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
                  modo === m.id
                    ? "bg-[#1b2a4a] text-white"
                    : "bg-white text-slate-600 hover:bg-slate-100"
                }`}
              >
                {m.etiqueta}
              </button>
            ))}
          </nav>

          {modo === "historico" && (
            <div className="flex items-center gap-1 text-xs">
              {(["baseline", "fundacional"] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => setModeloElegido(m)}
                  aria-pressed={modeloElegido === m}
                  className={`rounded-lg px-3 py-2 font-medium transition ${
                    modeloElegido === m
                      ? "bg-[#345d9d] text-white"
                      : "bg-white text-slate-600 hover:bg-slate-100 border border-slate-200"
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
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700"
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
            <div className="flex flex-wrap items-center gap-2 text-sm text-slate-600">
              <label className="flex items-center gap-1">
                desde
                <input
                  type="date"
                  value={desde}
                  onChange={(e) => setDesde(e.target.value)}
                  className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-sm"
                  aria-label="Desde"
                />
              </label>
              <label className="flex items-center gap-1">
                hasta
                <input
                  type="date"
                  value={hasta}
                  onChange={(e) => setHasta(e.target.value)}
                  className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-sm"
                  aria-label="Hasta"
                />
              </label>
              {(desde || hasta) && (
                <button
                  onClick={() => {
                    setDesde("");
                    setHasta("");
                  }}
                  className="text-xs font-medium text-[#345d9d] underline"
                >
                  limpiar rango
                </button>
              )}
            </div>
          )}

          {modo === "historico" && modeloElegido === "fundacional" && datos?.ventana && (
            <p className="text-xs text-slate-500">
              LTC · ventana de validación: {datos.ventana.desde.slice(0, 10)} –{" "}
              {datos.ventana.hasta.slice(0, 10)}
            </p>
          )}
        </div>

        {modo === "historico" &&
          modeloElegido === "baseline" &&
          (desde || hasta) &&
          origen === "snapshot" && (
            <p className="mt-2 text-xs text-amber-700">
              El rango de fechas requiere el backend en vivo; el snapshot congelado solo trae las
              últimas velas y no puede filtrarse por fecha.
            </p>
          )}

        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-500">
          {modoActual.descripcion}
        </p>

        {error && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
            {error}
          </div>
        )}

        {modo === "tiempo-real" && !cargando && datos && configuracion && (
          <div
            className="mb-4 rounded-lg border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-900"
            data-testid="vista-sin-confirmar"
          >
            <strong>
              Las últimas {configuracion.latencia_real} velas ({horasAnticipacion} horas) todavía no
              tienen confirmación.
            </strong>{" "}
            El modelo ya anunció qué cree que va a pasar —son las flechas del gráfico—, pero saber si
            de verdad hubo un giro exige ver las {configuracion.w} velas posteriores, y esas todavía
            no ocurrieron. No es una limitación técnica: es lo que tarda el problema en verificarse
            solo. Última vela disponible:{" "}
            {new Date(datos.serie[datos.serie.length - 1]?.fecha ?? "").toLocaleString("es-CR")}.
          </div>
        )}

        <section className="mt-4 rounded-xl border border-slate-200 bg-white p-4" data-testid="vista">
          {cargando ? (
            <p className="py-20 text-center text-sm text-slate-400" data-testid="vista-cargando">
              Cargando…
            </p>
          ) : datos ? (
            <Grafico puntos={datos.serie} />
          ) : null}
        </section>

        {datos && modo !== "tiempo-real" && <Leyenda />}

        {datos && (
          <section className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4" data-testid="metricas">
            <Metrica
              titulo="F1 macro"
              valor={datos.metricas.f1_macro}
              nota="El número principal: pesa igual las tres clases, así que si el modelo ignora los giros (la clase rara), esto baja"
              testId="f1-macro"
            />
            <Metrica
              titulo="Precisión direccional"
              valor={datos.metricas.precision_direccional}
              nota="De los giros reales, cuántos se anunciaron bien"
              testId="precision-direccional"
            />
            <Metrica
              titulo="Exactitud"
              valor={datos.metricas.exactitud}
              nota="No es el número principal: como la Continuidad domina los datos, hasta un modelo que nunca avisa un giro saca exactitud alta"
              testId="exactitud"
            />
            <Metrica
              titulo="Observaciones"
              valor={datos.metricas.n}
              entero
              nota="Velas evaluadas"
              testId="observaciones"
            />
            <Metrica
              titulo="F1 Máximo"
              valor={datos.metricas.f1_maximo}
              nota="Clase minoritaria: giros al alza"
            />
            <Metrica
              titulo="F1 Mínimo"
              valor={datos.metricas.f1_minimo}
              nota="Clase minoritaria: giros a la baja"
            />
            <Metrica
              titulo="F1 Continuidad"
              valor={datos.metricas.f1_continuidad}
              nota="Clase mayoritaria: sin giro"
            />
          </section>
        )}

        {comparacion && (
          <section className="mt-6 rounded-xl border border-slate-200 bg-white p-4">
            <h2 className="text-sm font-semibold text-[#1b2a4a]">Comparación de modelos</h2>
            <p className="mt-1 text-xs text-slate-500">
              Los {comparacion.modelos.length} modelos evaluados sobre la misma partición de{" "}
              {/* La evidencia de M3 trae "validacion" sin tilde; se corrige solo en la
                  vista, sin tocar docs/evidencias/, que no es mio y se regenera por script. */}
              {comparacion.particion.conjunto === "validacion"
                ? "validación"
                : comparacion.particion.conjunto}{" "}
              ({comparacion.particion.intervalo}, w=
              {comparacion.particion.w}, h={comparacion.particion.h}, n={comparacion.n}). Fuente:{" "}
              <code>{comparacion.fuente}</code>.
            </p>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full min-w-[480px] text-left text-sm">
                <thead>
                  <tr className="text-xs uppercase tracking-wide text-slate-400">
                    <th className="py-1 pr-3">Modelo</th>
                    <th className="py-1 pr-3">Papel</th>
                    <th className="py-1 pr-3 text-right">F1 macro</th>
                    <th className="py-1 pr-3 text-right">Precisión direc.</th>
                  </tr>
                </thead>
                <tbody>
                  {comparacion.modelos.map((m) => (
                    <tr key={m.clave} className="border-t border-slate-100">
                      <td className="py-2 pr-3 font-medium text-slate-700">
                        {m.etiqueta}
                        {m.corrida_individual && (
                          <span
                            className="mt-0.5 block text-[11px] font-normal text-amber-700"
                            data-testid={`${m.clave}-corrida-individual`}
                          >
                            corrida individual · media de 5 semillas {m.media_multisemilla?.toFixed(3)}{" "}
                            · rango {m.rango_semillas?.toFixed(3)}
                          </span>
                        )}
                      </td>
                      <td className="py-2 pr-3 text-slate-400">{m.papel}</td>
                      <td className="py-2 pr-3 text-right">
                        <BarraMetrica valor={m.f1_macro} />
                      </td>
                      <td className="py-2 pr-3 text-right text-slate-600">
                        {m.precision_direccional.toFixed(3)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {comparacion.modelos.some((m) => m.corrida_individual) && (
              <p className="mt-2 text-[11px] leading-snug text-slate-400">
                «Corrida individual»: ese modelo se entrena con una semilla aleatoria, y la cifra de
                arriba es una sola corrida, no el promedio — puede caer en cualquier punto del rango
                mostrado. En los dos casos la corrida publicada acá resultó ser la más alta de las
                medidas, así que la ventaja de un modelo sobre otro en esta tabla puede estar
                exagerada frente al promedio declarado. Baseline aleatorio usa semilla fija y el
                modelo fundacional es determinista: a esos dos no les aplica (issue #92).
              </p>
            )}
          </section>
        )}

        <footer className="mt-8 border-t border-slate-200 pt-4 text-xs leading-relaxed text-slate-400">
          <p>
            Las métricas provienen de <code>contracts/metrics.py</code>. Esta aplicación no calcula
            ninguna: si lo hiciera, tarde o temprano darían distinto que el informe.
          </p>
          {configuracion?.panel && (
            <p className="mt-1">
              Panel completo: {configuracion.panel.filas_totales.toLocaleString("es-CR")}{" "}
              observaciones desde {configuracion.panel.desde.slice(0, 10)} hasta{" "}
              {configuracion.panel.hasta.slice(0, 10)}. En esta vista se muestran las últimas{" "}
              {configuracion.panel.velas_exportadas_por_activo.toLocaleString("es-CR")} por activo.
            </p>
          )}
          <p className="mt-1">
            <a
              className="text-[#345d9d] underline"
              href="https://github.com/NeoFao/caso1-ltc-inflexion"
            >
              Código y documentación
            </a>
          </p>
        </footer>
      </main>
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
      ? "bg-amber-100 text-amber-800"
      : tono === "verde"
        ? "bg-emerald-100 text-emerald-800"
        : "bg-slate-100 text-slate-600";
  return (
    <span className={`rounded px-2 py-1 font-medium ${estilos}`} title={title}>
      {children}
    </span>
  );
}

/**
 * Issue #99, puntos 3 y 4: el grafico dibuja marcadores en un <canvas>, sin
 * texto que los explique, y las tres clases del proyecto no se definen en
 * ningun lado de la pagina. Usa los mismos colores que Grafico.tsx (importados
 * de ahi, no copiados) para que nunca puedan desincronizarse.
 */
function Leyenda() {
  return (
    <div
      className="mt-3 flex flex-wrap gap-x-5 gap-y-2 rounded-lg border border-slate-200 bg-white px-4 py-3 text-xs text-slate-600"
      data-testid="leyenda"
    >
      <span className="flex items-center gap-1.5">
        <span
          className="inline-block h-2.5 w-2.5 rounded-full"
          style={{ backgroundColor: MAXIMO }}
        />
        <strong className="font-medium text-slate-700">Máximo</strong> — el precio deja de subir y
        empieza a bajar
      </span>
      <span className="flex items-center gap-1.5">
        <span
          className="inline-block h-2.5 w-2.5 rounded-full"
          style={{ backgroundColor: MINIMO }}
        />
        <strong className="font-medium text-slate-700">Mínimo</strong> — el precio deja de bajar y
        empieza a subir
      </span>
      <span className="flex items-center gap-1.5">
        <span className="inline-block h-2.5 w-2.5 rounded-full border-2 border-slate-300" />
        <strong className="font-medium text-slate-700">Continuidad</strong> — sigue como estaba, sin
        giro (sin marcador en el gráfico)
      </span>
      <span className="flex items-center gap-1.5 text-slate-400">
        <span>●</span> relleno = ocurrió de verdad · <span>➜</span> flecha = lo que anunció el modelo
      </span>
    </div>
  );
}

/** Barra horizontal proporcional al F1 macro, para comparar modelos de un vistazo. */
function BarraMetrica({ valor }: { valor: number }) {
  const ancho = Math.max(0, Math.min(100, valor * 100));
  return (
    <div className="flex items-center justify-end gap-2">
      <div className="h-2 w-24 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-[#345d9d]" style={{ width: `${ancho}%` }} />
      </div>
      <span className="w-12 text-right font-medium text-slate-700">{valor.toFixed(3)}</span>
    </div>
  );
}

function Metrica({
  titulo,
  valor,
  entero,
  nota,
  testId,
}: {
  titulo: string;
  valor: number;
  entero?: boolean;
  nota?: string;
  testId?: string;
}) {
  const texto = Number.isNaN(valor)
    ? "—"
    : entero
      ? valor.toLocaleString("es-CR")
      : valor.toFixed(3);
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4" data-testid={testId}>
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{titulo}</p>
      <p className="mt-1 text-2xl font-bold text-[#1b2a4a]" data-testid={testId && `${testId}-valor`}>
        {texto}
      </p>
      {nota && <p className="mt-1 text-xs leading-snug text-slate-400">{nota}</p>}
    </div>
  );
}
