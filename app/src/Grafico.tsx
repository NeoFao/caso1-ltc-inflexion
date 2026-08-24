import { createChart, type IChartApi, type ISeriesApi, type UTCTimestamp } from "lightweight-charts";
import { useEffect, useRef } from "react";

import { CLASE, type Punto } from "./api";

const NAVY = "#1b2a4a";
const MAXIMO = "#c0392b";
const MINIMO = "#1e8449";
const GRIS = "#5a6675";
const REJILLA = "#e3e8ef";

interface Props {
  puntos: Punto[];
  mostrarPredichas?: boolean;
}

/**
 * Serie de precio con los giros marcados encima.
 *
 * Los reales van como marcadores rellenos debajo/encima de la vela y los
 * predichos con una flecha. Superponerlos en el mismo eje es lo que hace visible
 * de un vistazo donde el modelo acierta y donde inventa; en una matriz de
 * confusion esa informacion existe pero no se ve.
 */
export default function Grafico({ puntos, mostrarPredichas = true }: Props) {
  const contenedor = useRef<HTMLDivElement>(null);
  const grafico = useRef<IChartApi | null>(null);
  const serie = useRef<ISeriesApi<"Line"> | null>(null);

  useEffect(() => {
    if (!contenedor.current) return;

    grafico.current = createChart(contenedor.current, {
      layout: { background: { color: "#ffffff" }, textColor: GRIS, fontSize: 12 },
      grid: { vertLines: { color: REJILLA }, horzLines: { color: REJILLA } },
      rightPriceScale: { borderColor: REJILLA },
      timeScale: { borderColor: REJILLA, timeVisible: false },
      crosshair: { mode: 1 },
      autoSize: true,
    });
    serie.current = grafico.current.addLineSeries({ color: NAVY, lineWidth: 2 });

    return () => {
      grafico.current?.remove();
      grafico.current = null;
      serie.current = null;
    };
  }, []);

  useEffect(() => {
    if (!serie.current || puntos.length === 0) return;

    // lightweight-charts exige tiempo estrictamente ascendente. La fuente de
    // datos puede, en algun caso, entregar dos velas con la misma marca de
    // tiempo (por ejemplo si el backend redondea la fecha a un dia y la
    // granularidad es de horas): se ordena y se descartan repetidos en vez de
    // dejar que la libreria truene y la vista quede en blanco.
    const ordenados = [...puntos].sort(
      (a, b) => Date.parse(a.fecha) - Date.parse(b.fecha),
    );
    const sinRepetidos = ordenados.filter(
      (p, i) => i === 0 || Date.parse(p.fecha) !== Date.parse(ordenados[i - 1].fecha),
    );

    serie.current.setData(
      sinRepetidos.map((p) => ({
        time: (Date.parse(p.fecha) / 1000) as UTCTimestamp,
        value: p.cierre,
      })),
    );

    const marcadores = sinRepetidos.flatMap((p) => {
      const salida = [];
      if (p.etiqueta === CLASE.MAXIMO || p.etiqueta === CLASE.MINIMO) {
        const esMaximo = p.etiqueta === CLASE.MAXIMO;
        salida.push({
          time: (Date.parse(p.fecha) / 1000) as UTCTimestamp,
          position: esMaximo ? ("aboveBar" as const) : ("belowBar" as const),
          color: esMaximo ? MAXIMO : MINIMO,
          shape: "circle" as const,
          text: esMaximo ? "max" : "min",
        });
      }
      if (
        mostrarPredichas &&
        (p.predicha === CLASE.MAXIMO || p.predicha === CLASE.MINIMO)
      ) {
        const esMaximo = p.predicha === CLASE.MAXIMO;
        salida.push({
          time: (Date.parse(p.fecha) / 1000) as UTCTimestamp,
          position: esMaximo ? ("aboveBar" as const) : ("belowBar" as const),
          color: esMaximo ? MAXIMO : MINIMO,
          shape: esMaximo ? ("arrowDown" as const) : ("arrowUp" as const),
        });
      }
      return salida;
    });

    serie.current.setMarkers(marcadores);
    grafico.current?.timeScale().fitContent();
  }, [puntos, mostrarPredichas]);

  return <div ref={contenedor} className="h-[420px] w-full" />;
}
