import { useEffect, useState } from "react";

import Grafico, { MAXIMO, MINIMO } from "./Grafico";
import {
  type Comparacion,
  type Configuracion,
  type Origen,
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
    // Issue #149: decia "LTC al día" sobre un panel que termina el 05/08/2026. La
    // fecha real se muestra abajo, calculada del propio dato; aqui se describe el
    // comportamiento, que es lo que el modo demuestra y sí es cierto siempre.
    descripcion:
      "El modelo anuncia cada vela en el momento, con la información disponible hasta ese instante y nada más. La confirmación —si de verdad fue un giro— tarda lo que el sistema tarda en verla venir.",
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
  const [operacion, setOperacion] = useState<PuntoDeOperacion | null>(null);
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
    //
    // El orden de este encadenado importa y ya se equivocó una vez (#144). El
    // selector de modelo solo se dibuja en Historico, pero `modeloElegido` es
    // estado del componente y sobrevive al cambio de modo: si se preguntaba por
    // el antes que por el modo, el camino Historico -> Fundacional -> Tiempo
    // real servia el precalculado del fundacional, con su fecha vieja, bajo el
    // aviso de que los datos son de hoy. Y sin forma de volver, porque en Tiempo
    // real el selector no esta.
    //
    // Cada modo decide primero de donde saca el dato; el modelo elegido solo
    // interviene donde la interfaz deja elegirlo.
    const peticion =
      modo === "sintetico"
        ? obtenerSintetico(300)
        : modo === "tiempo-real"
          ? // Issue #149: este modo servia el panel del baseline trivial, que
            // responde siempre Continuidad -- la vista no dibujaba una sola flecha
            // mientras la pantalla decia que el modelo anuncia cada vela. Ahora
            // sirve las predicciones del clasico, con su confianza por vela.
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
  // El piso obligatorio (D7). Va debajo de cada metrica porque un numero suelto no
  // se puede leer: 0,390 no es bueno ni malo hasta saber que el azar da 0,337.
  const azar = comparacion?.modelos.find((m) => m.clave === "baseline_aleatorio");
  const clasico = comparacion?.modelos.find(
    (m) => m.clave === "bosque_aleatorio_rezagos_relativos",
  );
  const elegido: Umbral | undefined = operacion?.umbrales.reduce((mejor, u) =>
    Math.abs(u.umbral - umbral) < Math.abs(mejor.umbral - umbral) ? u : mejor,
  );
  // La ultima vela que el panel realmente trae, sacada del dato y no escrita a mano.
  const ultimaVela = datos?.ultima_vela ?? datos?.serie[datos.serie.length - 1]?.fecha;
  const diasDeAtraso = ultimaVela
    ? Math.floor((Date.now() - Date.parse(ultimaVela)) / 86_400_000)
    : null;
  const horasAnticipacion = configuracion
    ? configuracion.latencia_real * horasPorVela(configuracion.granularidad)
    : null;

  return (
    <div className="min-h-screen bg-papel text-tinta">
      {/* La cabecera es la unica superficie oscura de la pagina, y lleva el
          degradado y la regla de acento que la separan de "un div azul". El titulo
          va en serif: en una pagina que es toda dato, la voz editorial es lo que
          distingue el encabezado de una fila mas de la tabla. */}
      <header
        className="relative text-white"
        style={{
          background:
            "linear-gradient(160deg, #22355c 0%, #1b2a4a 48%, #16223c 100%)",
        }}
      >
        <div
          className="absolute inset-x-0 bottom-0 h-px"
          style={{
            background:
              "linear-gradient(90deg, transparent, rgba(52,93,157,0.85) 25%, rgba(52,93,157,0.85) 75%, transparent)",
          }}
        />
        <div className="mx-auto max-w-6xl px-6 py-9 sm:px-8">
          <p className="text-[10.5px] font-semibold uppercase tracking-[0.28em] text-[#8fa9d4]">
            Caso n.<sup>o</sup> 1 · Señales y sistemas · 3.<sup>er</sup> trimestre 2026
          </p>
          <h1
            className="mt-3 max-w-3xl text-[40px] font-semibold leading-[1.08] tracking-[-0.015em]"
            style={{ fontFamily: "var(--font-display)" }}
          >
            Puntos de inflexión en el precio de Litecoin
          </h1>
          <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-slate-300">
            Avisa cuándo el precio está por dar la vuelta —de subir a bajar, o al revés—
            {horasAnticipacion ? ` con ${horasAnticipacion} horas de anticipación.` : "."}
          </p>

          {/* La afirmacion central con su piso pegado al lado. Las dos cifras
              juntas son la unica forma de que "0,390" signifique algo. */}
          {clasico && azar && (
            <div
              className="mt-8 flex flex-wrap items-end gap-x-12 gap-y-6 border-t border-white/10 pt-7"
              data-testid="titular"
            >
              <div>
                <p className="text-[10.5px] font-semibold uppercase tracking-[0.18em] text-[#8fa9d4]">
                  F1 macro
                </p>
                <p className="cifra mt-2 text-[56px] font-medium leading-[0.85]">
                  {clasico.f1_macro.toFixed(3)}
                </p>
              </div>
              <div className="pb-1">
                <p className="text-[10.5px] font-semibold uppercase tracking-[0.18em] text-slate-400">
                  el azar
                </p>
                <p className="cifra mt-2 text-[32px] font-normal leading-[0.85] text-slate-400">
                  {azar.f1_macro.toFixed(3)}
                </p>
              </div>
              <p className="max-w-sm pb-1 text-[15px] leading-relaxed text-slate-300">
                De cada vela dice si el precio está por girar o va a seguir como está.
                Mejor que el azar,{" "}
                <span className="font-medium text-white">y lejos de ser resuelto</span>.
              </p>
            </div>
          )}

          <div className="mt-8 flex flex-wrap items-center gap-x-5 gap-y-2 text-[12.5px] text-slate-400">
            <span>Alejandro Zamora · Jose Pablo Monestel · Isaac Morun · Fabrizio Espinoza Arce</span>
          </div>

          {configuracion && (
            <div className="mt-4 flex flex-wrap items-center gap-2 text-[11.5px]">
              <Chip title="w: cuántas velas antes y después se miran para confirmar un giro. h: con cuánta anticipación se anuncia, antes de que el giro termine de confirmarse.">
                ventana w={configuracion.w} · horizonte h={configuracion.h} ·{" "}
                {configuracion.granularidad}
              </Chip>
              <Chip>
                anticipación efectiva {horasAnticipacion ?? "?"} horas (
                {configuracion.latencia_real} velas de {configuracion.granularidad})
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
              {!cargando && origen === "precalculado" && modo === "tiempo-real" && (
                <Chip>predicciones del clásico · sin backend</Chip>
              )}
              {!cargando && origen === "precalculado" && modo !== "tiempo-real" && (
                <Chip>ventana fija · precalculado sin backend</Chip>
              )}
            </div>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8 sm:px-8">
        {!cargando && datos?.modelo === "baseline_trivial" && (
          <div className="mb-5 rounded-lg border border-[#e8d6a8] bg-[#fdf8ec] px-4 py-3.5 text-[13.5px] leading-relaxed text-[#6b4c12]">
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
          <div className="mb-5 rounded-lg border border-[#c7dcef] bg-[#f2f8fd] px-4 py-3.5 text-[13.5px] leading-relaxed text-[#1a3f63]">
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
                className={`rounded-full px-5 py-2 text-sm font-medium transition ${
                  modo === m.id
                    ? "bg-navy text-white shadow-[0_1px_2px_rgba(28,26,23,0.25)]"
                    : "text-tinta-media ring-1 ring-linea hover:bg-papel-hundido"
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
                  className={`rounded-full px-4 py-2 font-medium transition ${
                    modeloElegido === m
                      ? "bg-acento text-white"
                      : "text-tinta-media ring-1 ring-linea hover:bg-papel-hundido"
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
              className="rounded-full border border-linea bg-white px-4 py-2 text-sm font-medium text-tinta"
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
                  className="rounded-lg border border-linea bg-white px-2.5 py-1.5 text-sm"
                  aria-label="Desde"
                />
              </label>
              <label className="flex items-center gap-1">
                hasta
                <input
                  type="date"
                  value={hasta}
                  onChange={(e) => setHasta(e.target.value)}
                  className="rounded-lg border border-linea bg-white px-2.5 py-1.5 text-sm"
                  aria-label="Hasta"
                />
              </label>
              {(desde || hasta) && (
                <button
                  onClick={() => {
                    setDesde("");
                    setHasta("");
                  }}
                  className="text-xs font-medium text-acento underline"
                >
                  limpiar rango
                </button>
              )}
            </div>
          )}

          {modo === "historico" && modeloElegido === "fundacional" && datos?.ventana && (
            <p className="text-[12px] text-tinta-suave">
              LTC · ventana de validación: {datos.ventana.desde.slice(0, 10)} –{" "}
              {datos.ventana.hasta.slice(0, 10)}
            </p>
          )}
        </div>

        {modo === "historico" &&
          modeloElegido === "baseline" &&
          (desde || hasta) &&
          origen === "snapshot" && (
            <p className="mt-2 text-xs text-[#a8541f]">
              El rango de fechas requiere el backend en vivo; el snapshot congelado solo trae las
              últimas velas y no puede filtrarse por fecha.
            </p>
          )}

        <p className="mt-5 max-w-3xl border-l-2 border-linea pl-4 text-[14.5px] leading-relaxed text-tinta-media">
          {modoActual.descripcion}
        </p>

        {error && (
          <div className="mt-5 rounded-lg border border-[#e6c6c1] bg-[#fdf4f2] p-4 text-sm text-[#8c2f22]">
            {error}
          </div>
        )}

        {/* Los dos avisos de Tiempo real iban como dos recuadros apilados a ancho
            completo: ocho lineas de prosa antes de ver el grafico, que es lo que la
            pantalla existe para mostrar. Van juntos, en dos columnas, sin perder una
            palabra de lo que dicen -- la D21 pide que se digan, no que se griten. */}
        {modo === "tiempo-real" && !cargando && datos && configuracion && (
          <div className="mb-5 grid gap-4 sm:grid-cols-2">
            <div
              className="rounded-lg border border-[#c7dcef] bg-[#f2f8fd] px-4 py-3.5 text-[13.5px] leading-relaxed text-[#1a3f63]"
              data-testid="vista-sin-confirmar"
            >
              <strong>
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
                className={`rounded-lg border px-4 py-3.5 text-[13.5px] leading-relaxed ${
                  (diasDeAtraso ?? 0) > 1
                    ? "border-[#e8d6a8] bg-[#fdf8ec] text-[#6b4c12]"
                    : "border-linea bg-papel-hundido text-tinta-media"
                }`}
                data-testid="ultima-vela"
              >
                <strong>
                  La última vela de este panel es del{" "}
                  {new Date(ultimaVela).toLocaleString("es-CR")}
                </strong>
                {(diasDeAtraso ?? 0) > 1 && <> — hace {diasDeAtraso} días.</>} Los datos son un
                snapshot congelado: <strong>esto no es el mercado de ahora mismo</strong>, es el
                comportamiento del sistema sobre las últimas velas que tiene.
              </div>
            )}
          </div>
        )}

        <section
          className="mt-5 overflow-hidden rounded-xl border border-linea bg-white shadow-[0_1px_2px_rgba(28,26,23,0.04)]"
          data-testid="vista"
        >
          <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-linea px-5 py-3">
            <h2 className="text-[13px] font-semibold uppercase tracking-[0.1em] text-tinta-media">
              {modo === "sintetico"
                ? "Serie construida, con los giros que plantamos"
                : modo === "tiempo-real"
                  ? "LTC, últimas velas del panel"
                  : `${activo}, precio de cierre`}
            </h2>
            <p className="cifra text-[11.5px] text-tinta-suave">
              {datos ? `${datos.serie.length.toLocaleString("es-CR")} velas` : ""}
              {datos && modo === "tiempo-real" ? ` · umbral ${umbral.toFixed(2)}` : ""}
            </p>
          </div>
          <div className="p-4">
          {cargando ? (
            <p className="py-24 text-center text-sm text-tinta-suave" data-testid="vista-cargando">
              Cargando…
            </p>
          ) : datos ? (
            <Grafico
              puntos={datos.serie}
              umbral={modo === "tiempo-real" ? umbral : undefined}
            />
          ) : null}
          </div>
        </section>

        {modo === "tiempo-real" && operacion && elegido && (
          <ControlDeUmbral
            operacion={operacion}
            umbral={umbral}
            elegido={elegido}
            onCambio={setUmbral}
          />
        )}

        {datos && <Leyenda balance={datos.balance} />}

        {datos && (
          <section
            className="mt-5 grid grid-cols-2 gap-4 sm:grid-cols-4"
            data-testid="metricas"
          >
            <Metrica
              titulo="F1 macro"
              valor={datos.metricas.f1_macro}
              piso={azar?.f1_macro}
              principal
              ancha
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
            <Metrica
              titulo="Observaciones"
              valor={datos.metricas.n}
              entero
              nota="Velas evaluadas"
              testId="observaciones"
            />
            {/* Issue #151.3: la exactitud salia con el mismo peso visual que el F1
                macro y no decide nada. Va atenuada y al final, con su piso al lado,
                que es lo que hace visible el problema: el azar ya saca 0,822. */}
            <Metrica
              titulo="Exactitud"
              valor={datos.metricas.exactitud}
              piso={azar?.exactitud}
              atenuada
              nota="No decide nada. Como la Continuidad domina los datos, un modelo que nunca avisa un giro ya saca exactitud alta"
              testId="exactitud"
            />
          </section>
        )}

        {comparacion && (
          <section className="mt-5 rounded-xl border border-linea bg-white p-5 shadow-[0_1px_2px_rgba(28,26,23,0.04)]">
            <h2 className="text-[15px] font-semibold tracking-tight text-tinta" style={{ fontFamily: "var(--font-display)" }}>Comparación de modelos</h2>
            <p className="mt-1.5 text-[12.5px] text-tinta-suave">
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
                  <tr className="text-[10px] font-semibold uppercase tracking-[0.12em] text-tinta-suave">
                    <th className="py-1 pr-3">Modelo</th>
                    <th className="py-1 pr-3">Papel</th>
                    <th className="py-1 pr-3 text-right">F1 macro</th>
                    <th className="py-1 pr-3 text-right">Precisión direc.</th>
                  </tr>
                </thead>
                <tbody>
                  {comparacion.modelos.map((m) => (
                    <tr key={m.clave} className="border-t border-linea">
                      <td className="py-3 pr-3 font-medium text-tinta">
                        {m.etiqueta}
                        {m.corrida_individual && (
                          <span
                            className="mt-1 block text-[11px] font-normal text-[#a8541f]"
                            data-testid={`${m.clave}-corrida-individual`}
                          >
                            corrida individual · media de 5 semillas {m.media_multisemilla?.toFixed(3)}{" "}
                            · rango {m.rango_semillas?.toFixed(3)}
                          </span>
                        )}
                      </td>
                      <td className="py-3 pr-3 text-[12.5px] text-tinta-suave">{m.papel}</td>
                      <td className="py-3 pr-3 text-right">
                        <BarraMetrica valor={m.f1_macro} piso={azar?.f1_macro} />
                      </td>
                      <td className="cifra py-3 pr-3 text-right text-tinta-media">
                        {m.precision_direccional.toFixed(3)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {comparacion.modelos.some((m) => m.corrida_individual) && (
              <p className="mt-2.5 text-[11px] leading-snug text-slate-500">
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

        <footer className="mt-12 border-t border-linea pt-6 text-[12px] leading-relaxed text-tinta-suave">
          <p>
            Las métricas provienen de <code>contracts/metrics.py</code>. Esta aplicación no calcula
            ninguna: si lo hiciera, tarde o temprano darían distinto que el informe.
          </p>
          {/* El logotipo de la esquina del grafico lo dibuja la propia libreria y es su
              atribucion obligatoria. Se deja donde esta -- quitarlo seria incumplir su
              licencia -- pero sin esta linea se lee como que los precios salen de ahi,
              que es lo primero que pregunto quien vio la aplicacion. */}
          <p className="mt-1">
            El gráfico se dibuja con <strong>Lightweight Charts™ de TradingView</strong>, y el
            logotipo de su esquina es la atribución que esa biblioteca exige.{" "}
            <strong>Los precios no vienen de TradingView:</strong> se descargan de la API pública de Binance
            (<code>api.binance.com/api/v3/klines</code>) con <code>src/panel/descarga.py</code>.
            TradingView aquí es solo cómo se dibuja, no de dónde salen los datos.
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
              className="text-acento underline"
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
  // Sobre la cabecera navy. El gris claro sobre blanco daba 2,56:1 y no pasaba AA;
  // aqui el chip es una superficie propia con su texto en blanco o casi.
  // Sobre la cabecera oscura. El gris claro sobre blanco daba 2,56:1 y no pasaba
  // AA; aqui cada chip es su propia superficie con un aro de un pixel.
  const estilos =
    tono === "ambar"
      ? "bg-amber-300/15 text-amber-100 ring-amber-200/25"
      : tono === "verde"
        ? "bg-emerald-300/15 text-emerald-100 ring-emerald-200/25"
        : "bg-white/[0.07] text-slate-300 ring-white/10";
  return (
    <span
      className={`rounded-full px-3 py-1.5 font-medium tracking-tight ring-1 ${estilos}`}
      title={title}
    >
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
function Leyenda({ balance }: { balance?: Respuesta["balance"] }) {
  const continuidad = balance?.find((b) => b.codigo === 3);
  return (
    <div
      className="mt-5 flex flex-wrap gap-x-6 gap-y-2.5 rounded-xl border border-linea bg-white px-5 py-4 text-[12.5px] text-tinta-media"
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
      <span className="flex items-center gap-1.5 text-slate-500">
        <span>●</span> relleno = ocurrió de verdad · <span>➜</span> flecha = lo que anunció el modelo
      </span>
      {/* Issue #151.4: la leyenda explicaba los colores pero no el problema. Esta es
          la razon de que esto sea dificil, y de que la metrica sea el F1 y no la
          exactitud. Sale del dato, no escrita a mano. */}
      {continuidad && (
        <span className="w-full border-t border-linea pt-2.5 text-tinta-media">
          <strong className="font-medium text-slate-700">
            El {continuidad.porcentaje.toFixed(1)} % de las velas son continuidad.
          </strong>{" "}
          Por eso esto es difícil: los giros son raros, y un modelo que no avisara ninguno
          acertaría igual ese {continuidad.porcentaje.toFixed(1)} % de las veces.
        </span>
      )}
    </div>
  );
}

/**
 * El punto de operación: hasta dónde tiene que estar seguro el sistema para avisar.
 *
 * Issue #150. Hoy el sistema **avisa en todas las velas** y nunca se calla; con ese
 * comportamiento acierta 8,1 de cada 100 avisos, y la frecuencia base de giros es
 * 9,4 % — o sea que como alarma es peor que reaccionar al azar con la misma
 * frecuencia. Dejándolo callarse cuando no está seguro, sí mejora.
 *
 * Las cifras **no se calculan aquí**: salen medidas sobre nueve tramos y llegan en
 * `punto-de-operacion.json`. Y la del azar va siempre al lado, porque «acierta el
 * 10 %» a secas no significa nada.
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

  // La curva se dibuja sobre el maximo medido, no sobre 1: comprimirla contra una
  // escala que nadie alcanza esconderia justamente la subida que hay que ver.
  const techo = Math.max(...operacion.umbrales.map((u) => u.precision)) * 1.15;
  // El recorrido del pulgar, en porcentaje del ancho, para que la marca de la curva
  // caiga justo encima de el. Antes la curva iba de 0 a 100 y el deslizador compartia
  // fila con su etiqueta: el marcador decia 0,40 en un sitio y el pulgar en otro.
  const n = operacion.umbrales.length;
  const indice = operacion.umbrales.findIndex((u) => u.umbral === elegido.umbral);
  const xDeIndice = (i: number) => (n > 1 ? (i / (n - 1)) * 100 : 50);
  const xDe = (umbral: number) =>
    xDeIndice(operacion.umbrales.findIndex((u) => u.umbral === umbral));
  const yDe = (v: number) => 34 - (v / techo) * 31;
  const trazo = (clave: "precision" | "precision_azar") =>
    operacion.umbrales
      .map((u, i) => `${i === 0 ? "M" : "L"}${xDeIndice(i)},${yDe(u[clave])}`)
      .join(" ");
  const lineaModelo = trazo("precision");
  const lineaAzar = trazo("precision_azar");
  const areaModelo = `${lineaModelo} L100,34 L0,34 Z`;
  return (
    <section
      className="mt-5 rounded-xl border border-linea bg-white p-5 shadow-[0_1px_2px_rgba(28,26,23,0.04)]"
      data-testid="control-umbral"
    >
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-[15px] font-semibold tracking-tight text-tinta" style={{ fontFamily: "var(--font-display)" }}>
          Cuánto tiene que estar seguro para avisar
        </h2>
        <span className="text-[11.5px] text-tinta-suave">
          medido sobre{" "}
          <span className="cifra">{operacion.n_observaciones.toLocaleString("es-CR")}</span>{" "}
          observaciones fuera de muestra, en {operacion.tramos} tramos
        </span>
      </div>

      {/* La curva entera, medida, detras del deslizador.
          Antes solo se veia el punto elegido: el numero cambiaba y no habia forma
          de saber si estabas en una meseta o en un pico. Con la curva se ve la
          FORMA -- que la precision sube al callarse y que la del azar no -- que es
          el argumento completo del #150 en una imagen. No se calcula aqui: son los
          once puntos que vienen medidos en punto-de-operacion.json. */}
      <div className="relative mt-5" style={{ margin: "0 8px" }}>
        <svg
          viewBox="0 0 100 34"
          preserveAspectRatio="none"
          className="h-[76px] w-full overflow-visible"
          aria-hidden="true"
        >
          <defs>
            <linearGradient id="bajoLaCurva" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#345d9d" stopOpacity="0.16" />
              <stop offset="100%" stopColor="#345d9d" stopOpacity="0" />
            </linearGradient>
          </defs>
          {[0, 1, 2, 3].map((i) => (
            <line
              key={i}
              x1="0"
              x2="100"
              y1={2 + i * 10}
              y2={2 + i * 10}
              stroke="#e7e3dc"
              strokeWidth="0.3"
              vectorEffect="non-scaling-stroke"
            />
          ))}
          <path d={areaModelo} fill="url(#bajoLaCurva)" />
          <path
            d={lineaAzar}
            fill="none"
            stroke="#a9a49b"
            strokeWidth="1.4"
            strokeDasharray="3 2.5"
            vectorEffect="non-scaling-stroke"
          />
          <path
            d={lineaModelo}
            fill="none"
            stroke="#345d9d"
            strokeWidth="2"
            strokeLinejoin="round"
            vectorEffect="non-scaling-stroke"
          />
          <line
            x1={xDe(elegido.umbral)}
            x2={xDe(elegido.umbral)}
            y1="0"
            y2="34"
            stroke="#1b2a4a"
            strokeWidth="1"
            vectorEffect="non-scaling-stroke"
          />
        </svg>
        <span
          className="pointer-events-none absolute block h-2.5 w-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-navy"
          style={{
            left: `${xDe(elegido.umbral)}%`,
            top: `${(yDe(elegido.precision) / 34) * 100}%`,
          }}
        />
      </div>

      <div className="mt-2 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <span className="flex items-center gap-4 text-[10.5px]">
          <span className="font-semibold uppercase tracking-[0.13em] text-tinta-suave">umbral</span>
          <span className="flex items-center gap-1.5 font-medium text-acento">
            <span className="inline-block h-0.5 w-4 bg-acento" /> acierta el modelo
          </span>
          <span className="flex items-center gap-1.5 text-tinta-suave">
            <span
              className="inline-block h-0.5 w-4"
              style={{
                backgroundImage:
                  "repeating-linear-gradient(90deg,#a9a49b 0 3px,transparent 3px 5px)",
              }}
            />
            acierta el azar
          </span>
        </span>
        <span className="cifra text-[18px] font-medium text-tinta">
          {elegido.umbral.toFixed(2)}
        </span>
      </div>
      <input
        type="range"
        min={0}
        max={n - 1}
        step={1}
        value={indice}
        onChange={(e) => onCambio(operacion.umbrales[Number(e.target.value)].umbral)}
        className="umbral mt-1 h-4 w-full"
        aria-label="Umbral de confianza para avisar"
      />

      <div className="mt-5 grid grid-cols-2 gap-px overflow-hidden rounded-lg bg-linea sm:grid-cols-4">
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

      <p className="mt-4 text-[12.5px] leading-relaxed text-tinta-media">
        {umbral === 0 ? (
          <>
            <strong className="text-amber-700">En 0,00 el sistema no se calla nunca.</strong> Avisa
            en todas las velas, y acierta menos que la frecuencia base de giros —{" "}
            {(operacion.frecuencia_base_de_giros * 100).toFixed(1)} %. Como alarma, avisar siempre
            es peor que reaccionar al azar con la misma frecuencia. Subí el umbral.
          </>
        ) : (
          <>
            Mover esto <strong>no cambia el modelo ni reentrena nada</strong>: es el punto donde se
            decide que un aviso vale la pena darlo. Las cifras del informe se miden con cobertura
            del 100 % y se quedan así.
          </>
        )}
      </p>
    </section>
  );
}

/** Una cifra del punto de operación, con su nota debajo. */
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
  // Sin bordes propios: las cuatro comparten una rejilla de un pixel, para que se
  // lean como una sola cifra de cuatro partes y no como cuatro tarjetas sueltas.
  return (
    <div className={`px-4 py-3.5 ${destacado ? "bg-[#f4f7fc]" : "bg-white"}`}>
      <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-tinta-suave">
        {titulo}
      </p>
      <p
        className={`cifra mt-2 text-[24px] font-medium leading-none ${
          destacado ? "text-acento" : "text-tinta"
        }`}
      >
        {valor}
      </p>
      <p className="mt-2 text-[11px] leading-snug text-tinta-suave">{nota}</p>
    </div>
  );
}

/** Barra horizontal proporcional al F1 macro, para comparar modelos de un vistazo. */
/** Barra del F1 macro con la marca del piso encima, no solo la longitud. */
function BarraMetrica({ valor, piso }: { valor: number; piso?: number }) {
  // La escala llega a 0,5 y no a 1: con todos los modelos entre 0,33 y 0,40, una
  // barra sobre 1 los deja indistinguibles y sugiere que falta poco para el techo.
  const escala = (v: number) => Math.max(0, Math.min(100, (v / 0.5) * 100));
  return (
    <div className="flex items-center justify-end gap-3">
      <div className="relative h-1.5 w-28 overflow-hidden rounded-full bg-[#efece6]">
        <div
          className="h-full rounded-full bg-acento"
          style={{ width: `${escala(valor)}%` }}
        />
        {piso !== undefined && (
          <div
            className="absolute top-0 h-full w-px bg-[#1c1a17]/45"
            style={{ left: `${escala(piso)}%` }}
            title={`piso del azar: ${piso.toFixed(3)}`}
          />
        )}
      </div>
      <span className="cifra w-12 text-right font-medium text-tinta">{valor.toFixed(3)}</span>
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
  ancha,
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
  /** Ocupa dos columnas. Con siete tarjetas en una rejilla de cuatro, la ultima
   *  fila quedaba con un hueco; la que decide es la que merece el ancho. */
  ancha?: boolean;
}) {
  const texto = Number.isNaN(valor)
    ? "—"
    : entero
      ? valor.toLocaleString("es-CR")
      : valor.toFixed(3);
  const supera = piso !== undefined && !Number.isNaN(valor) && valor > piso;
  return (
    <div
      className={`flex flex-col rounded-xl border p-5 ${ancha ? "sm:col-span-2" : ""} ${
        principal
          ? "border-navy/25 bg-white shadow-[0_1px_3px_rgba(28,26,23,0.07)]"
          : atenuada
            ? "border-linea bg-papel-hundido"
            : "border-linea bg-white shadow-[0_1px_2px_rgba(28,26,23,0.04)]"
      }`}
      data-testid={testId}
    >
      <p
        className={`flex items-center gap-2 text-[10.5px] font-semibold uppercase tracking-[0.13em] ${
          atenuada ? "text-tinta-suave" : "text-tinta-media"
        }`}
      >
        {titulo}
        {principal && (
          <span className="rounded-full bg-navy px-2 py-0.5 text-[9px] font-semibold uppercase tracking-[0.08em] text-white">
            decide
          </span>
        )}
        {atenuada && (
          <span className="rounded-full bg-[#e2ded6] px-2 py-0.5 text-[9px] font-semibold uppercase tracking-[0.08em] text-tinta-suave">
            no decide
          </span>
        )}
      </p>
      <p
        className={`cifra mt-3 font-medium leading-none ${
          atenuada
            ? "text-[26px] text-tinta-suave"
            : principal
              ? "text-[46px] text-tinta"
              : "text-[30px] text-tinta"
        }`}
        data-testid={testId && `${testId}-valor`}
      >
        {texto}
      </p>
      {/* El piso obligatorio. Sin el, el numero de arriba no se puede leer. */}
      {piso !== undefined && !Number.isNaN(piso) && (
        <p className="mt-3 flex items-baseline gap-2 text-[12px]">
          <span className="text-tinta-suave">
            azar <span className="cifra">{piso.toFixed(3)}</span>
          </span>
          <span
            className={`font-medium ${supera ? "text-[#1e8449]" : "text-[#a8541f]"}`}
          >
            {supera ? "lo supera" : "no lo supera"}
          </span>
        </p>
      )}
      {nota && (
        <p className="mt-auto pt-4 text-[12px] leading-relaxed text-tinta-suave">{nota}</p>
      )}
    </div>
  );
}
