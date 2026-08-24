import { useEffect, useState } from "react";

import Grafico from "./Grafico";
import {
  type Comparacion,
  type Configuracion,
  type Origen,
  type Respuesta,
  antiguedad,
  obtenerComparacion,
  obtenerConfiguracion,
  obtenerHistorico,
  obtenerSintetico,
} from "./api";

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
      "Últimas velas descargadas en vivo, sin etiqueta conocida todavía.",
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

  useEffect(() => {
    obtenerConfiguracion()
      .then((r) => setConfiguracion(r.datos))
      .catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    obtenerComparacion().catch(() => null).then((c) => c && setComparacion(c));
  }, []);

  useEffect(() => {
    if (modo === "tiempo-real") {
      setDatos(null);
      return;
    }
    setCargando(true);
    setError(null);
    const peticion =
      modo === "sintetico" ? obtenerSintetico(300) : obtenerHistorico(activo, desde, hasta);
    peticion
      .then((r) => {
        setDatos(r.datos);
        setOrigen(r.origen);
      })
      .catch((e) => setError(String(e)))
      .finally(() => setCargando(false));
  }, [modo, activo, desde, hasta]);

  const modoActual = MODOS.find((m) => m.id === modo)!;
  const edad = antiguedad(datos?.generado_utc ?? configuracion?.generado_utc);

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
          <p className="mt-1 text-sm text-slate-500">
            Alejandro Zamora · Jose Pablo Monestel · Isaac Morun · Fabrizio Espinoza Arce
          </p>
          {configuracion && (
            <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
              <Chip>
                ventana w={configuracion.w} · horizonte h={configuracion.h} ·{" "}
                {configuracion.granularidad}
              </Chip>
              <Chip>anticipación efectiva {configuracion.latencia_real} velas</Chip>
              {configuracion.provisional && (
                <Chip tono="ambar">parámetros provisionales, sin congelar</Chip>
              )}
              {origen === "snapshot" && (
                <Chip tono="ambar">
                  datos congelados{edad ? ` · ${edad}` : ""} · backend no disponible
                </Chip>
              )}
              {origen === "backend" && <Chip tono="verde">backend en vivo</Chip>}
            </div>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-6">
        {datos?.modelo === "baseline_trivial" && (
          <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            <strong>Todavía no hay modelo entrenado.</strong> Lo que se ve son las predicciones del{" "}
            <em>baseline trivial</em>, que responde siempre «Continuidad» y no detecta ningún giro.
            Está a propósito: es el piso obligatorio contra el que se compara todo, y demuestra por
            qué no reportamos exactitud como métrica principal.
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

          {modo === "historico" && configuracion && (
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

          {modo === "historico" && (
            <div className="flex items-center gap-2 text-sm text-slate-600">
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
        </div>

        {modo === "historico" && (desde || hasta) && origen === "snapshot" && (
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

        <section className="mt-4 rounded-xl border border-slate-200 bg-white p-4">
          {modo === "tiempo-real" ? (
            <div className="py-20 text-center">
              <p className="text-sm font-medium text-slate-500">Pendiente (RF-U3)</p>
              <p className="mx-auto mt-2 max-w-lg text-sm text-slate-400">
                Depende de definir qué se considera «tiempo real»: si el sistema confirma el giro w
                velas después de que ocurrió, o lo anuncia en el momento sin esperar confirmación.
                Es la consulta 3 al profesor.
              </p>
            </div>
          ) : cargando ? (
            <p className="py-20 text-center text-sm text-slate-400">Cargando…</p>
          ) : datos ? (
            <Grafico puntos={datos.serie} />
          ) : null}
        </section>

        {datos && (
          <section className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Metrica
              titulo="F1 macro"
              valor={datos.metricas.f1_macro}
              nota="Promedio de las tres clases, con igual peso"
            />
            <Metrica
              titulo="Precisión direccional"
              valor={datos.metricas.precision_direccional}
              nota="De los giros reales, cuántos se anunciaron bien"
            />
            <Metrica
              titulo="Exactitud"
              valor={datos.metricas.exactitud}
              nota="Engañosa con clases desbalanceadas"
            />
            <Metrica titulo="Observaciones" valor={datos.metricas.n} entero nota="Velas evaluadas" />
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
              {comparacion.particion.conjunto} ({comparacion.particion.intervalo}, w=
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
                      <td className="py-2 pr-3 font-medium text-slate-700">{m.etiqueta}</td>
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

function Chip({ children, tono }: { children: React.ReactNode; tono?: "ambar" | "verde" }) {
  const estilos =
    tono === "ambar"
      ? "bg-amber-100 text-amber-800"
      : tono === "verde"
        ? "bg-emerald-100 text-emerald-800"
        : "bg-slate-100 text-slate-600";
  return <span className={`rounded px-2 py-1 font-medium ${estilos}`}>{children}</span>;
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
}: {
  titulo: string;
  valor: number;
  entero?: boolean;
  nota?: string;
}) {
  const texto = Number.isNaN(valor)
    ? "—"
    : entero
      ? valor.toLocaleString("es-CR")
      : valor.toFixed(3);
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{titulo}</p>
      <p className="mt-1 text-2xl font-bold text-[#1b2a4a]">{texto}</p>
      {nota && <p className="mt-1 text-xs leading-snug text-slate-400">{nota}</p>}
    </div>
  );
}
