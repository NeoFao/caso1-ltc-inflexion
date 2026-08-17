const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, TabStopType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle, VerticalAlign,
  PageBreak, TableOfContents, Header, Footer, PageNumber, LevelFormat,
  convertInchesToTwip, PageOrientation,
} = require('docx');
const fs = require('fs');

// Litecoin brand blue as the accent so the document, the report figures and the
// application end up sharing one palette instead of three unrelated ones.
const NAVY = '1B2A4A';
const ACCENT = '345D9D';
const MUTED = '5A6675';
const RULE = 'C9D3E0';
const BAND = 'EEF2F8';
const BAND2 = 'F7F9FC';
const WHITE = 'FFFFFF';

const BODY_FONT = 'Calibri';
const MONO_FONT = 'Consolas';

const CONTENT_W = 9360; // 12240 letter - 2*1440 margins

// ---------------------------------------------------------------------------
// inline markup: **bold**, `code`
function runs(text, opts = {}) {
  const base = { font: BODY_FONT, size: opts.size || 21, color: opts.color || '20242B' };
  const out = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`)/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(new TextRun({ ...base, text: text.slice(last, m.index), bold: opts.bold, italics: opts.italics }));
    const tok = m[0];
    if (tok.startsWith('**')) {
      out.push(new TextRun({ ...base, text: tok.slice(2, -2), bold: true, italics: opts.italics }));
    } else {
      out.push(new TextRun({ ...base, text: tok.slice(1, -1), font: MONO_FONT, size: (opts.size || 21) - 2, color: ACCENT }));
    }
    last = re.lastIndex;
  }
  if (last < text.length) out.push(new TextRun({ ...base, text: text.slice(last), bold: opts.bold, italics: opts.italics }));
  return out;
}

const p = (text, opts = {}) => new Paragraph({
  children: runs(text, opts),
  spacing: { after: opts.after ?? 140, line: 276 },
  alignment: opts.align,
  indent: opts.indent,
});

const h1 = (text) => new Paragraph({ text, heading: HeadingLevel.HEADING_1 });
const h2 = (text) => new Paragraph({ text, heading: HeadingLevel.HEADING_2 });
const h3 = (text) => new Paragraph({ text, heading: HeadingLevel.HEADING_3 });

const bullet = (text, instance = 0) => new Paragraph({
  children: runs(text),
  numbering: { reference: 'vinetas', level: 0, instance },
  spacing: { after: 80, line: 276 },
});

const num = (text, instance) => new Paragraph({
  children: runs(text),
  numbering: { reference: 'numeros', level: 0, instance },
  spacing: { after: 80, line: 276 },
});

// shaded emphasis box with an accent bar on the left
const callout = (lines, tone = BAND) => new Table({
  columnWidths: [CONTENT_W],
  width: { size: CONTENT_W, type: WidthType.DXA },
  borders: {
    top: { style: BorderStyle.SINGLE, size: 2, color: tone },
    bottom: { style: BorderStyle.SINGLE, size: 2, color: tone },
    right: { style: BorderStyle.SINGLE, size: 2, color: tone },
    left: { style: BorderStyle.SINGLE, size: 18, color: ACCENT },
    insideHorizontal: { style: BorderStyle.NONE },
    insideVertical: { style: BorderStyle.NONE },
  },
  rows: [new TableRow({
    children: [new TableCell({
      width: { size: CONTENT_W, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: tone },
      margins: { top: 160, bottom: 160, left: 220, right: 220 },
      children: lines.map((l, i) => new Paragraph({
        children: runs(l, { size: 20 }),
        spacing: { after: i === lines.length - 1 ? 0 : 100, line: 264 },
      })),
    })],
  })],
  spacing: { before: 120, after: 200 },
});

const calloutBlock = (lines, tone) => [callout(lines, tone), new Paragraph({ text: '', spacing: { after: 120 } })];

// data table: header row on navy, zebra body
function table(headers, rows, widths, opts = {}) {
  const total = widths.reduce((a, b) => a + b, 0);
  const scaled = widths.map((w) => Math.round((w / total) * CONTENT_W));
  const diff = CONTENT_W - scaled.reduce((a, b) => a + b, 0);
  scaled[scaled.length - 1] += diff;

  const headRow = new TableRow({
    tableHeader: true,
    children: headers.map((t, i) => new TableCell({
      width: { size: scaled[i], type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: NAVY },
      margins: { top: 90, bottom: 90, left: 130, right: 130 },
      verticalAlign: VerticalAlign.CENTER,
      children: [new Paragraph({
        children: [new TextRun({ text: t, bold: true, color: WHITE, font: BODY_FONT, size: 19 })],
        spacing: { after: 0 },
      })],
    })),
  });

  const bodyRows = rows.map((cells, r) => new TableRow({
    children: cells.map((t, i) => new TableCell({
      width: { size: scaled[i], type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: r % 2 ? WHITE : BAND2 },
      margins: { top: 90, bottom: 90, left: 130, right: 130 },
      verticalAlign: VerticalAlign.TOP,
      children: [new Paragraph({
        children: runs(String(t), { size: 19 }),
        spacing: { after: 0, line: 252 },
      })],
    })),
  }));

  return new Table({
    columnWidths: scaled,
    width: { size: CONTENT_W, type: WidthType.DXA },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: NAVY },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: NAVY },
      left: { style: BorderStyle.NONE },
      right: { style: BorderStyle.NONE },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: RULE },
      insideVertical: { style: BorderStyle.NONE },
    },
    rows: [headRow, ...bodyRows],
  });
}

const tableBlock = (headers, rows, widths) => [
  table(headers, rows, widths),
  new Paragraph({ text: '', spacing: { after: 240 } }),
];

// caption under a table or figure
const caption = (text) => new Paragraph({
  children: [new TextRun({ text, font: BODY_FONT, size: 17, color: MUTED, italics: true })],
  spacing: { after: 260 },
});

// ---------------------------------------------------------------------------
// architecture diagram, built from table cells so it renders as boxes, not ASCII
function box(text, fill, color, span) {
  return new TableCell({
    columnSpan: span,
    width: { size: Math.round(CONTENT_W / 3) * (span || 1), type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill },
    margins: { top: 120, bottom: 120, left: 100, right: 100 },
    verticalAlign: VerticalAlign.CENTER,
    borders: {
      top: { style: BorderStyle.SINGLE, size: 6, color: WHITE },
      bottom: { style: BorderStyle.SINGLE, size: 6, color: WHITE },
      left: { style: BorderStyle.SINGLE, size: 6, color: WHITE },
      right: { style: BorderStyle.SINGLE, size: 6, color: WHITE },
    },
    children: text.split('|').map((line, i, all) => new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: i === all.length - 1 ? 0 : 40, line: 240 },
      children: runs(line, { size: 18, color }),
    })),
  });
}

function arrowRow(cols) {
  return new TableRow({
    children: Array.from({ length: cols }, () => new TableCell({
      width: { size: Math.round(CONTENT_W / cols), type: WidthType.DXA },
      borders: {
        top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE },
        left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
      },
      margins: { top: 20, bottom: 20 },
      children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 0 },
        children: [new TextRun({ text: '↓', font: BODY_FONT, size: 20, color: ACCENT, bold: true })],
      })],
    })),
  });
}

function diagram() {
  const third = Math.round(CONTENT_W / 3);
  const rows = [
    new TableRow({ children: [box('Fuente de datos — API pública', BAND, NAVY, 3)] }),
    arrowRow(1),
    new TableRow({ children: [box('**M0** · descarga y consolidación', NAVY, WHITE, 3)] }),
    arrowRow(1),
    new TableRow({ children: [box('**panel_v1.parquet** — artefacto congelado, idéntico para los cuatro', ACCENT, WHITE, 3)] }),
    arrowRow(3),
    new TableRow({
      children: [
        box('**M1**|EDA y diagnóstico', BAND, NAVY, 1),
        box('**M2**|etiquetas y características', BAND, NAVY, 1),
        box('**M3**|modelo fundacional y avanzado', BAND, NAVY, 1),
      ],
    }),
    arrowRow(3),
    new TableRow({ children: [box('**M0** · arnés de evaluación', NAVY, WHITE, 3)] }),
    arrowRow(1),
    new TableRow({ children: [box('**M0** · API del backend', NAVY, WHITE, 3)] }),
    arrowRow(1),
    new TableRow({ children: [box('**M1** · aplicación web', ACCENT, WHITE, 3)] }),
  ];
  return new Table({
    columnWidths: [third, third, CONTENT_W - 2 * third],
    width: { size: CONTENT_W, type: WidthType.DXA },
    borders: {
      top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE },
      left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
      insideHorizontal: { style: BorderStyle.NONE }, insideVertical: { style: BorderStyle.NONE },
    },
    rows,
  });
}

// ---------------------------------------------------------------------------
// cover page
function cover() {
  const meta = [
    ['Versión', '1.0'],
    ['Fecha', '5 de agosto de 2026'],
    ['Autor', 'Fabrizio Espinoza Arce — Project Manager'],
    ['Equipo', 'Alejandro Zamora · Jose Pablo Monestel · Isaac Morun · Fabrizio Espinoza Arce'],
    ['Dirigido a', 'Roberto Calvo Arias'],
    ['Curso', 'Señales y Sistemas — 3.er Trimestre 2026'],
    ['Programa', 'Tecnologías de la Información y Comunicación Empresarial'],
    ['Institución', 'Universidad Invenio'],
    ['Entrega final', '8 de septiembre de 2026'],
    ['Estado', 'Borrador para revisión del equipo'],
  ];

  const metaTable = new Table({
    columnWidths: [2400, CONTENT_W - 2400],
    width: { size: CONTENT_W, type: WidthType.DXA },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 2, color: RULE },
      bottom: { style: BorderStyle.SINGLE, size: 2, color: RULE },
      left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: RULE },
      insideVertical: { style: BorderStyle.NONE },
    },
    rows: meta.map(([k, v]) => new TableRow({
      children: [
        new TableCell({
          width: { size: 2400, type: WidthType.DXA },
          margins: { top: 110, bottom: 110, left: 0, right: 120 },
          children: [new Paragraph({
            spacing: { after: 0 },
            children: [new TextRun({ text: k.toUpperCase(), bold: true, size: 16, color: MUTED, font: BODY_FONT, characterSpacing: 20 })],
          })],
        }),
        new TableCell({
          width: { size: CONTENT_W - 2400, type: WidthType.DXA },
          margins: { top: 110, bottom: 110, left: 0, right: 0 },
          children: [new Paragraph({ spacing: { after: 0 }, children: runs(v, { size: 20 }) })],
        }),
      ],
    })),
  });

  return [
    new Paragraph({ text: '', spacing: { after: 1400 } }),
    new Paragraph({
      spacing: { after: 60 },
      children: [new TextRun({ text: 'DOCUMENTO DE REQUISITOS DE PRODUCTO', bold: true, size: 19, color: ACCENT, font: BODY_FONT, characterSpacing: 60 })],
    }),
    new Paragraph({
      spacing: { after: 40 },
      children: [new TextRun({ text: 'Sistema de Pronóstico de Puntos', size: 56, bold: true, color: NAVY, font: BODY_FONT })],
    }),
    new Paragraph({
      spacing: { after: 40 },
      children: [new TextRun({ text: 'de Inflexión en el Precio de Litecoin', size: 56, bold: true, color: NAVY, font: BODY_FONT })],
    }),
    new Paragraph({
      spacing: { after: 260 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: ACCENT, space: 10 } },
      children: [new TextRun({ text: '', size: 8 })],
    }),
    new Paragraph({
      spacing: { after: 900 },
      children: [new TextRun({
        text: 'Análisis multivariante de series temporales mediante aprendizaje automático supervisado · Caso N.º 1',
        size: 24, color: MUTED, font: BODY_FONT,
      })],
    }),
    metaTable,
    new Paragraph({ children: [new PageBreak()] }),
  ];
}

// ---------------------------------------------------------------------------
const body = [];
const push = (...xs) => xs.forEach((x) => body.push(x));

// --- table of contents
push(
  new Paragraph({
    spacing: { after: 240 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: ACCENT, space: 8 } },
    children: [new TextRun({ text: 'Contenido', bold: true, size: 34, color: NAVY, font: BODY_FONT })],
  }),
  new TableOfContents('Contenido', { hyperlink: true, headingStyleRange: '1-2' }),
  new Paragraph({ children: [new PageBreak()] }),
);

// --- cómo leer
push(h1('Cómo leer este documento'));
push(p('No hace falta leerlo entero de una sentada. Está ordenado así:'));
push(bullet('**Secciones 1 a 4** — qué estamos construyendo y por qué. Léanlas todos.', 1));
push(bullet('**Secciones 5 a 8** — cómo está partido el trabajo y qué le toca a cada uno. Lean la suya con cuidado y las demás por encima, para saber a quién preguntarle qué.', 1));
push(bullet('**Secciones 9 a 12** — cómo se trabaja semana a semana y cuándo algo cuenta como terminado.', 1));
push(bullet('**Secciones 13 a 15** — lo que todavía no está decidido, lo que puede salir mal y lo que estamos suponiendo sin haber verificado.', 1));
push(p('Si algo no se entiende, no es culpa de quien lee. Escríbanlo en el grupo y lo corrijo en la versión siguiente.'));

// --- 1
push(h1('1. Qué estamos construyendo'));
push(p('Un sistema que mira el precio de Litecoin y avisa cuándo está por dar la vuelta.'));
push(p('Más preciso: un modelo de aprendizaje automático que, para cada momento del tiempo, clasifica el precio de LTC en una de tres etiquetas — **Máximo**, **Mínimo** o **Zona de Continuidad** — usando como información de apoyo el comportamiento de Bitcoin, Ethereum, Solana, XRP y Cardano.'));
push(p('Alrededor del modelo construimos tres cosas más:'));
push(num('Una **aplicación web** que permite ver el modelo funcionando sobre datos sintéticos, históricos y en vivo.', 1));
push(num('Un **informe técnico** que documenta el diseño, el rendimiento medido y las limitaciones del enfoque.', 1));
push(num('Una **presentación semanal** del avance.', 1));

// --- 2
push(h1('2. Por qué existe el problema'));
push(p('Los precios de criptomonedas son series difíciles: no son estacionarias — sus propiedades estadísticas cambian con el tiempo —, son muy volátiles, y su volatilidad tampoco es constante, lo que se llama heterocedasticidad. Los modelos estadísticos clásicos como ARIMA o GARCH asumen estructuras lineales y estables, y por eso rinden mal acá.'));
push(p('Además, LTC no se mueve solo. Su precio responde al mercado general de criptomonedas, y en particular a los activos de mayor capitalización, que funcionan como transmisores de riesgo y de sentimiento. Un modelo que ignore eso está tirando información útil.'));
push(p('De ahí el planteamiento: **problema multivariante** — seis series, no una — y **enfoque de aprendizaje profundo**, no estadística clásica.'));

// --- 3
push(h1('3. Objetivos y criterios de éxito'));
push(p('Hay dos tipos de éxito y conviene no confundirlos.'));

push(h2('3.1 Éxito académico'));
push(p('El trabajo se califica con seis criterios, todos del mismo peso — 16,66 % cada uno:'));
push(...tableBlock(
  ['Criterio', 'Qué mide'],
  [
    ['Contenido', 'Profundidad y precisión en la descripción de equipos, tecnologías y sistemas'],
    ['Análisis', 'Capacidad de relacionar los conceptos técnicos con su aplicación, con ejemplos prácticos'],
    ['Calidad de las fuentes', 'Uso de referencias académicas y cumplimiento del formato APA'],
    ['Estructura y redacción', 'Organización clara, coherencia y uso correcto del idioma'],
    ['Calidad de la exposición', 'Que la presentación sea clara, dinámica y mantenga la atención'],
    ['Comunicación efectiva', 'Que la comunicación sea clara, concisa y adaptada al público'],
  ],
  [30, 70],
));
push(...calloutBlock([
  'Léanlo dos veces: **cuatro de los seis criterios no hablan del modelo.** Hablan de cómo escribimos, cómo citamos y cómo exponemos. Eso es el 66 % de la nota.',
  'Un modelo brillante con un documento apurado saca menos que un modelo decente con un documento impecable. Por eso, en este proyecto, **escribir la sección del documento es parte de terminar la tarea**, no algo que se hace después.',
]));

push(h2('3.2 Éxito técnico'));
push(p('El proyecto es exitoso técnicamente si:'));
push(num('El modelo supera de forma medible a un **baseline trivial**. El baseline trivial es un modelo que siempre responde “Zona de Continuidad”. Como las clases van a estar desbalanceadas, ese modelo tonto va a tener buena exactitud, y si no lo superamos en F1 no tenemos nada.', 2));
push(num('Existen **dos modelos** funcionando y comparados con la misma métrica y la misma partición de datos: uno fundacional de Hugging Face y uno avanzado.', 2));
push(num('Todo resultado del informe se puede **regenerar con un comando**. Si un número no se puede volver a producir, no entra al informe.', 2));

push(h2('3.3 Criterio de decisión, fijado de antemano'));
push(p('Para no terminar justificando lo que ya queríamos hacer, dejamos escrito ahora — antes de medir nada — cómo se elige el modelo que va al reporte final:'));
push(...calloutBlock([
  'Gana el modelo con mayor **F1 macro** sobre el conjunto de prueba. Si la diferencia entre el fundacional y el avanzado es **menor a 0,02 absoluto**, se recomienda el fundacional por ser más simple, y el avanzado se documenta igual con su resultado.',
]));
push(p('El umbral de 0,02 es una propuesta del PM, no un número sacado de un artículo académico. Si alguien tiene un criterio mejor, se cambia **ahora**. Después de ver los resultados ya no se puede cambiar sin decirlo explícitamente en el informe.'));

// --- 4
push(h1('4. Alcance'));
push(h2('4.1 Dentro del alcance'));
[
  'Descarga y limpieza de series históricas de las seis criptomonedas.',
  'Análisis exploratorio y diagnóstico estadístico de las series.',
  'Definición operativa del punto de inflexión y generación de etiquetas.',
  'Ingeniería de características: indicadores técnicos, rezagos, ventanas, volatilidad y correlación.',
  'Un modelo fundacional de Hugging Face.',
  'Un modelo avanzado — iTransformer, CryptoMamba, Informer, VTA o FinLSPM.',
  'Arnés de evaluación con métricas comunes y partición temporal fija.',
  'Generador de series sintéticas con puntos de inflexión conocidos.',
  'Aplicación web con tres modos de prueba.',
  'Cinco documentos semanales y cinco presentaciones.',
].forEach((t) => push(bullet(t, 2)));

push(h2('4.2 Fuera del alcance'));
push(p('Esto no se construye, y si a alguien se le ocurre a mitad de camino, se discute antes de escribir una línea:'));
[
  'Ejecución de operaciones reales, conexión a un exchange o gestión de órdenes.',
  'Recomendaciones de inversión de cualquier tipo.',
  'Autenticación, usuarios, base de datos o despliegue en producción.',
  'Reentrenamiento automático o pipelines de MLOps.',
  'Más criptomonedas que las seis del enunciado.',
  'Análisis de sentimiento, noticias o redes sociales.',
].forEach((t) => push(bullet(t, 3)));

// --- 5
push(h1('5. El producto'));
push(h2('5.1 Quién lo usa'));
push(p('Seamos honestos sobre esto, porque cambia las decisiones de diseño: **el usuario real es quien evalúa el proyecto, y nosotros mismos.** No hay un inversionista esperando esta herramienta. Diseñar para un usuario imaginario nos llevaría a construir cosas que nadie va a mirar.'));
push(p('Por eso la aplicación tiene una sola misión: **hacer visible y comprensible, en segundos, lo que el modelo hace bien y lo que hace mal.**'));

push(h2('5.2 Los tres modos'));
push(p('El enunciado exige pruebas de detección “con datos sintéticos, de entrenamiento y tiempo real”. La aplicación tiene exactamente esos tres modos, ni uno más.'));
push(...tableBlock(
  ['Modo', 'Qué muestra', 'Por qué existe'],
  [
    ['Sintético', 'Serie generada con giros que nosotros mismos pusimos, así que sabemos con certeza absoluta dónde están. El modelo la analiza y se ve si los encuentra.', 'Es la única prueba donde la verdad no está en discusión. Detecta errores de implementación que en datos reales pasarían desapercibidos.'],
    ['Histórico', 'Un rango de fechas del panel real, con las etiquetas verdaderas y las predichas sobre el mismo gráfico, más las métricas del período.', 'Es la evaluación formal del enunciado, hecha visible.'],
    ['Tiempo real', 'Las velas más recientes descargadas en vivo; el modelo predice sobre datos que todavía no tienen etiqueta conocida. Muestra siempre la fecha y hora del dato.', 'Es lo que el enunciado llama “tiempo real”.'],
  ],
  [16, 44, 40],
));
push(p('Además: selector de criptomoneda, comparación lado a lado del modelo fundacional contra el avanzado, y un panel de métricas.'));

push(h2('5.3 Requisitos funcionales'));
push(p('Numerados para poder rastrearlos después. Cada tarea del backlog va a apuntar a uno de estos.'));

push(h3('Datos'));
push(...tableBlock(
  ['ID', 'Requisito'],
  [
    ['RF-D1', 'El sistema obtiene velas OHLCV de las seis criptomonedas desde una única fuente documentada.'],
    ['RF-D2', 'Cada descarga queda registrada con fuente, fecha y hora, rango de fechas y hash del archivo. Sin ese registro, el dato no se usa.'],
    ['RF-D3', 'Los huecos y valores anómalos se tratan con una regla escrita y auditable. Nada se corrige “a ojo”.'],
    ['RF-D4', 'El panel combinado se guarda versionado y es idéntico para las cuatro personas.'],
  ],
  [12, 88],
));

push(h3('Etiquetado'));
push(...tableBlock(
  ['ID', 'Requisito'],
  [
    ['RF-E1', 'Una única función pura asigna las tres clases a partir del precio de cierre, `w` y `h`. Ningún módulo implementa su propia versión.'],
    ['RF-E2', 'Ninguna característica usa información posterior al instante de predicción. Se verifica con una prueba automática, no con buena fe.'],
    ['RF-E3', 'La partición entrenamiento / validación / prueba es temporal y está fija. Nunca aleatoria.'],
  ],
  [12, 88],
));

push(h3('Características'));
push(...tableBlock(
  ['ID', 'Requisito'],
  [
    ['RF-F1', 'Se generan características de al menos cuatro familias: indicadores técnicos, rezagos, ventana deslizante y volatilidad.'],
    ['RF-F2', 'Se generan características de correlación cruzada entre LTC y las otras cinco criptomonedas.'],
    ['RF-F3', 'Todas las características se calculan sobre la misma escala documentada, y el escalado se ajusta solo con datos de entrenamiento.'],
    ['RF-F4', 'Se documenta qué características quedaron y por qué, con una medición de importancia.'],
  ],
  [12, 88],
));

push(h3('Modelos'));
push(...tableBlock(
  ['ID', 'Requisito'],
  [
    ['RF-M1', 'Un modelo fundacional de Hugging Face, con su elección justificada según las características medidas de los datos, no por popularidad.'],
    ['RF-M2', 'Un modelo avanzado de la lista del enunciado, con código disponible públicamente.'],
    ['RF-M3', 'Ambos modelos exponen la misma interfaz de predicción, para que el arnés de evaluación y la aplicación no sepan cuál están usando.'],
    ['RF-M4', 'Ambos entrenan con semilla fija y el proceso es reproducible.'],
  ],
  [12, 88],
));

push(h3('Evaluación'));
push(...tableBlock(
  ['ID', 'Requisito'],
  [
    ['RF-V1', 'Todas las métricas salen de una única función compartida: Precisión Direccional, F1 macro, F1 por clase y matriz de confusión.'],
    ['RF-V2', 'Todo reporte de resultados incluye el baseline trivial como punto de comparación obligatorio.'],
    ['RF-V3', 'Los resultados se guardan en un archivo versionado con la fecha de ejecución.'],
  ],
  [12, 88],
));

push(h3('Aplicación'));
push(...tableBlock(
  ['ID', 'Requisito'],
  [
    ['RF-U1', 'Modo sintético operativo.'],
    ['RF-U2', 'Modo histórico operativo, con selección de rango de fechas.'],
    ['RF-U3', 'Modo tiempo real operativo, mostrando siempre la fecha del dato.'],
    ['RF-U4', 'Comparación de los dos modelos sobre el mismo período.'],
    ['RF-U5', 'La aplicación arranca y es usable **sin conexión a internet**, con el último dato cacheado, indicando su antigüedad.'],
    ['RF-U6', 'La aplicación no contiene lógica de negocio. Ninguna métrica, etiqueta o predicción se calcula dentro de ella.'],
  ],
  [12, 88],
));

push(h3('Documentación'));
push(...tableBlock(
  ['ID', 'Requisito'],
  [
    ['RF-I1', 'Cada módulo entrega su sección del documento en la misma semana en que entrega su código.'],
    ['RF-I2', 'Toda figura lleva número, pie, y está referenciada en el texto.'],
    ['RF-I3', 'Toda cita sigue formato APA.'],
    ['RF-I4', 'Toda figura y toda tabla se regenera con un script commiteado. Nada de capturas pegadas.'],
  ],
  [12, 88],
));

push(h2('5.4 Requisitos no funcionales'));
push(...tableBlock(
  ['ID', 'Requisito'],
  [
    ['RNF-1', '**Todo corre en CPU.** Si algo exige GPU, tiene que existir un camino en CPU aunque sea más lento. Todavía no sabemos qué máquinas tiene el equipo.'],
    ['RNF-2', '**Reproducibilidad.** Cualquier número del informe se regenera con un comando. Semillas fijas en todo.'],
    ['RNF-3', '**Entorno idéntico.** Las cuatro máquinas instalan exactamente las mismas versiones desde un archivo de bloqueo.'],
    ['RNF-4', '**Presupuesto de entrenamiento.** El tiempo de entrenamiento del modelo avanzado se mide en la semana 3. Si supera dos horas en la máquina más lenta del equipo, se reduce el alcance del modelo en vez de aceptar que solo una persona pueda entrenarlo.'],
  ],
  [13, 87],
));

// --- 6
push(h1('6. Arquitectura'));
push(diagram());
push(caption('Figura 1. Flujo del sistema. Los contratos y el artefacto de datos se congelan primero; a partir de ahí, M1, M2 y M3 trabajan en paralelo sin esperarse.'));
push(...calloutBlock([
  '**La idea central:** el artefacto de datos y los contratos se congelan primero. A partir de ahí, los tres módulos trabajan en paralelo sin esperarse entre sí, porque todos dependen del contrato y ninguno depende del trabajo en curso de otro.',
]));

push(h2('6.1 Pila tecnológica'));
push(...tableBlock(
  ['Capa', 'Elección', 'Por qué'],
  [
    ['Lenguaje', 'Python 3.14', 'Ultima estable. Se midio que resuelve identico a 3.13 con torch 2.13 y transformers 5.14; 3.15 se descarta porque ningun torch publica ruedas para esa version'],
    ['Entorno', '`uv` con archivo de bloqueo', 'Un solo comando instala todo, incluido el intérprete. Elimina los cuatro puntos de falla habituales del setup'],
    ['Datos', 'pandas + parquet', 'El dataset son miles de filas, no millones. pandas es lo que van a encontrar en cualquier tutorial cuando se traben'],
    ['Modelos', 'PyTorch (CPU) + transformers', 'Requisito del enunciado'],
    ['Backend', 'FastAPI', 'Expone las funciones que ya existen como JSON. Delgado, sin lógica propia'],
    ['Frontend', 'Vite + React + TypeScript + Tailwind', 'El equipo ya entregó un producto con esta pila'],
    ['Gráficos', 'TradingView Lightweight Charts', 'Es la librería que hace que un gráfico de cripto se vea profesional, con marcadores sobre puntos concretos'],
    ['Figuras del informe', 'matplotlib con estilo compartido', 'Consistencia entre los cinco documentos'],
  ],
  [17, 30, 53],
));
push(p('**Lo que deliberadamente no usamos:** MLflow, DVC, Weights & Biases ni Docker. Cada una es una semana de aprendizaje que no tenemos, y el problema que resuelven — trazabilidad de experimentos — lo cubrimos con un parquet versionado y un archivo de resultados commiteado.'));

// --- 7
push(h1('7. Módulos y responsables'));
push(...calloutBlock([
  '**Regla base: nadie comparte tarea con nadie.** Cada persona tiene sus carpetas, y nadie edita archivos ajenos sin avisar por escrito.',
]));

push(h2('M0 · Infraestructura, contratos y evaluación — Fabrizio Espinoza'));
push(p('Monta el repositorio, el entorno, la integración continua y las guías. Produce el dataset canónico. Define y congela los contratos. Construye el arnés de evaluación y el backend. Ensambla los documentos semanales y los decks. Es quien une todo.'));
push(p('**Carpetas:** `contracts/`, `src/evaluacion/`, `src/api/`, `data/`, `.github/`'));
push(p('**Su marco teórico:** métricas de evaluación para puntos de inflexión.'));

push(h2('M1 · Datos, diagnóstico y aplicación — Jose Pablo Monestel'));
push(p('**Semanas 1 y 2:** análisis exploratorio y diagnóstico estadístico de las seis series — estacionariedad, volatilidad, autocorrelación y correlación cruzada. Es el módulo que responde “¿cómo son realmente estos datos?”.'));
push(p('**Semanas 3 a 5:** la aplicación web completa, con los tres modos.'));
push(p('Arranca el frontend en la semana 2 contra datos falsos. **No espera a que exista el modelo.**'));
push(p('**Carpetas:** `src/datos/`, `src/visual/`, `app/`'));
push(p('**Su marco teórico:** definición y componentes de una serie temporal, estacionariedad, no estacionariedad, heterocedasticidad, volatilidad, autocorrelación y correlación cruzada.'));

push(h2('M2 · Etiquetado y características — Alejandro Zamora'));
push(p('Implementa la función de etiquetado según la definición que congele el equipo. Construye el generador de series sintéticas con giros conocidos. Diseña y mide las características. Reporta cuáles aportan y cuáles no.'));
push(p('**Carpetas:** `src/features/`, `src/sintetico/`'));
push(p('**Su marco teórico:** criptoactivos, sus características y tipos, factores que afectan el precio, correlación y dependencia entre activos, definición de punto de inflexión y cómo encontrarlos.'));

push(h2('M3 · Modelado — Isaac Morun'));
push(p('**Semanas 1 y 2:** estudio comparado de los modelos candidatos y montaje del entorno de entrenamiento. **Semana 3:** modelo fundacional de Hugging Face funcionando y evaluado. **Semana 4:** modelo avanzado funcionando y evaluado.'));
push(p('Es el módulo con más riesgo del proyecto. Si en la semana 4 el modelo avanzado no arranca, el PM entra a apoyar. Eso está previsto y no es un fracaso: es el plan.'));
push(p('**Carpetas:** `src/modelos/`'));
push(p('**Su marco teórico:** modelos fundacionales de series de tiempo, VTA, FinLSPM y CryptoMamba.'));

push(h2('7.1 Por qué este reparto'));
push(p('No es al azar. Cada quien está donde ya demostró que rinde: en el proyecto anterior del equipo, Jose Pablo llevó interfaz y visualización, Isaac llevó la parte de inteligencia artificial, y Alejandro llevó el núcleo y la integración — que acá corresponde a los contratos de etiquetado.'));

push(h2('7.2 Sobre exponer'));
push(p('Cada semana, **cada persona expone el módulo de otro**, rotando. Esto no es trabajo compartido: cada quien sigue construyendo solo lo suyo. Es un ensayo.'));
push(p('La razón es concreta: dos de los seis criterios de la rúbrica evalúan la exposición y la comunicación, y suman lo mismo que contenido y análisis juntos. Si llegamos a la semana 5 con cuatro especialistas que solo saben defender su parte, perdemos ahí. Además, si alguien falta el día de la presentación, no se cae el avance.'));

// --- 8
push(h1('8. Los contratos congelados'));
push(p('Un contrato es una definición que varios módulos usan y que **nadie cambia por su cuenta**. Son la razón por la que se puede trabajar en paralelo sin pisarse. Se congelan al cierre de la Semana 1 y viven en `contracts/`.'));
push(...tableBlock(
  ['Contrato', 'Qué fija', 'Quién lo consume'],
  [
    ['`schema.py`', 'Columnas exactas del panel, tipos y zona horaria', 'M1, M2, M3'],
    ['`labeling.py`', 'La función que asigna Máximo / Mínimo / Continuidad', 'M2, M3, M0'],
    ['`splits.py`', 'Las fechas exactas de entrenamiento, validación y prueba', 'M3, M0'],
    ['`metrics.py`', 'Las firmas de todas las métricas', 'M3, M0, M1'],
  ],
  [22, 53, 25],
));
push(p('**Cómo se cambia un contrato:** se propone por escrito, con la razón y qué se rompe. Lo aprueban el PM y quien lo consume. Se cambia en un solo lugar y se vuelve a correr todo. Nunca se parcha en cuatro archivos distintos.'));
push(...calloutBlock([
  '**Por qué esto importa tanto:** si en la semana 3 Alejandro está etiquetando con una ventana de 5 e Isaac entrenó con una de 10, los resultados no son comparables entre sí y no hay forma de saber cuál modelo es mejor. Peor: no nos vamos a dar cuenta hasta que los números no cuadren, probablemente en la semana 4, cuando ya no hay tiempo para rehacer.',
]));

push(h2('8.1 Estándar de figuras'));
push(p('`src/visual/estilo.py` contiene la paleta, la hoja de estilo y las funciones de ayuda. **Cada módulo genera sus propias figuras llamando a eso.** Nadie espera a nadie, y salen consistentes porque comparten el código, no porque alguien se acuerde de una convención.'));
push(p('La aplicación web usa la misma paleta que las figuras del informe. El demo y el documento tienen que parecer el mismo proyecto.'));

// --- 9
push(h1('9. Plan por semanas'));
push(p('Las fechas de cierre están **por confirmar con el profesor**.'));
push(...tableBlock(
  ['Semana', 'Cierre estimado', 'Entregable del enunciado', 'Qué se construye en paralelo'],
  [
    ['1', '~11/08', 'Marco teórico: series temporales y criptoactivos', 'Repositorio, entorno, dataset canónico, contratos congelados'],
    ['2', '~18/08', 'Marco teórico: modelos y definición del pipeline', 'Características, entorno de entrenamiento, esqueleto de la app contra datos falsos'],
    ['3', '~25/08', 'Modelo fundacional y pruebas de detección', 'App conectada al modelo real, modos sintético e histórico'],
    ['4', '~01/09', 'Modelo avanzado y pruebas de detección', 'Modo tiempo real, comparación de modelos'],
    ['5', '08/09', 'Reporte final y presentación', 'Cierre, ensayo, evidencias'],
  ],
  [9, 14, 38, 39],
));
push(...calloutBlock([
  '**Decisión clave del plan:** el enunciado pide que las semanas 1 y 2 sean solo teoría. No lo hacemos así. Escribimos la teoría **y** construimos el pipeline en paralelo desde la primera semana.',
  'Si esperamos a la semana 3 para tocar código, las semanas 4 y 5 se convierten en una carrera y no queda margen para probar de verdad ni para ensayar la presentación. El entregable semanal se respeta tal cual lo pide el enunciado; el código adicional es nuestro colchón, no un cambio de alcance.',
]));

// --- 10
push(h1('10. Cadencia semanal'));
push(...tableBlock(
  ['Cuándo', 'Qué'],
  [
    ['Lunes', 'Reunión de 30 minutos. Cada uno dice qué entrega esta semana y qué lo puede bloquear. Se cierra el alcance de la semana.'],
    ['Todos los días', 'Cada quien sube su trabajo a su rama, aunque esté incompleto. Un día sin subir nada es una señal de alarma, no un problema de disciplina.'],
    ['Jueves', 'Corte. Cada módulo entrega su sección del documento y sus figuras.'],
    ['Viernes', 'El PM ensambla el documento y el deck. Ensayo con exposición cruzada.'],
  ],
  [18, 82],
));
push(p('**Regla de desbloqueo:** si alguien está trabado más de un día, lo dice. No hay premio por sufrir en silencio, y en un proyecto de cinco semanas un día perdido es el 3 % del tiempo total.'));
push(p('**Regla de datos que no existen:** si alguien va a construir algo que depende de datos, de una API o de un archivo que todavía no existe, lo avisa **antes de empezar**. Esa es la forma más cara de perder tiempo en este tipo de proyecto.'));

// --- 11
push(h1('11. Cuándo una tarea está terminada'));
push(p('Una tarea no está terminada cuando el código corre. Está terminada cuando existen estas cuatro cosas:'));
push(num('**Código** en la rama, con sus pruebas pasando.', 3));
push(num('**Evidencia medida** — un número que salió de ejecutar algo, no de estimarlo. Si no se ejecutó, se dice “no lo he medido”.', 3));
push(num('**Sección del documento** escrita, con sus figuras numeradas y referenciadas.', 3));
push(num('**Slide** con lo esencial de ese avance.', 3));
push(p('Las cuatro. Una tarea con código y sin documento no cuenta como avance, porque el 66 % de la nota está en el documento y la presentación.'));

push(h2('11.1 Cómo se escriben las tareas'));
push(p('Cada tarea del backlog cumple estos seis criterios, conocidos como INVEST:'));
push(...tableBlock(
  ['Criterio', 'Qué significa acá'],
  [
    ['Independiente', 'Se puede hacer sin esperar a que otro termine. Los contratos existen justamente para esto.'],
    ['Negociable', 'El **qué** está fijo; el **cómo** lo decide quien la hace.'],
    ['Valiosa', 'Produce algo que se puede mostrar: un número, una figura, una pantalla. No “avanzar en el módulo”.'],
    ['Estimable', 'Quien la hace puede decir si le toma horas o días. Si no puede, está mal descrita.'],
    ['Pequeña', 'Cabe en una semana. Si no cabe, se parte.'],
    ['Testeable', 'Hay una forma clara de saber si quedó bien, escrita antes de empezar.'],
  ],
  [20, 80],
));

// --- 12
push(h1('12. Reglas de honestidad'));
push(p('Estas no son formalismos. Cada una evita un error concreto que en un proyecto así se paga caro.'));
[
  '**Ningún número que no se haya obtenido ejecutando.** Ni conteos, ni porcentajes, ni tiempos. Si no se corrió, se escribe “no lo he medido”. Un número inventado en un documento entregado es peor que un espacio en blanco.',
  '**Ninguna conclusión a partir de una salida cortada.** Si un log o un archivo se truncó, se pide de nuevo. No se completa con suposiciones.',
  '**Verificar la fecha de todo artefacto generado** antes de usarlo como evidencia — figuras, archivos de datos, resultados. Es fácil pasar horas mirando un resultado viejo que no se regeneró.',
  '**Distinguir lo medido de lo construido.** Si alguien arma un caso sintético para ilustrar un riesgo, lo dice. No se presenta como algo que está pasando en los datos reales.',
  '**Decir en la misma frase lo que no está verificado.** “Compila” y “funciona” no son lo mismo. “Las pruebas pasan” y “lo probé de verdad” tampoco.',
  '**Fijar el criterio antes de mirar el resultado.** Si hay que elegir entre dos opciones, se define primero qué número decide. Al revés se llama justificar lo que ya se quería hacer.',
  '**Desconfiar de las listas de estado.** Se desactualizan en las dos direcciones. La fuente de verdad es el código y lo que se ejecuta.',
].forEach((t) => push(num(t, 4)));

// --- 13
push(h1('13. Decisiones abiertas'));
push(...tableBlock(
  ['#', 'Decisión', 'Quién decide', 'Cuándo'],
  [
    ['D1', 'Granularidad de las velas: diaria, 4 horas u horaria', 'Equipo, con la medición del spike de datos en la mano', 'Semana 1'],
    ['D2', 'Valor de la ventana `w`', 'Equipo', 'Semana 1'],
    ['D3', 'Valor del horizonte `h`', 'Equipo', 'Semana 1'],
    ['D4', 'Qué se considera “tiempo real”: detección con retraso confirmado o predicción en el momento', 'Profesor', 'Pendiente'],
    ['D5', 'Cómo interpretar la Precisión Direccional en un problema de tres clases', 'Profesor', 'Pendiente'],
    ['D6', 'Qué máquina tiene cada integrante', 'Equipo', 'Esta semana'],
    ['D7', 'Qué modelo fundacional y qué modelo avanzado', 'Isaac, justificado con datos medidos', 'Semanas 2 y 3'],
    ['D8', 'Pila del frontend: React/Vite o Streamlit', 'PM — propuesta React/Vite', 'Esta semana'],
  ],
  [6, 46, 32, 16],
));
push(p('El contexto completo de D1 a D5 está en el documento **Definición operativa del punto de inflexión**, que además contiene la consulta al profesor redactada para enviarse.'));

// --- 14
push(h1('14. Riesgos'));
push(p('Ordenados del más grave al menos grave.'));
push(...tableBlock(
  ['#', 'Riesgo', 'Impacto', 'Qué hacemos'],
  [
    ['R1', '**Los datos no alcanzan.** La ventana histórica común de las seis criptomonedas puede dar pocas filas, y las clases de interés van a ser raras por construcción', 'Puede invalidar la elección de modelo y obligar a rediseñar', 'Spike de datos esta semana, antes de repartir tareas. Si en velas diarias no alcanza, se pasa a granularidad menor'],
    ['R2', '**El modelo avanzado no arranca.** Es el módulo más pesado y está sobre una sola persona', 'Se cae el entregable de la semana 4', 'Punto de decisión explícito el lunes de la semana 4. El PM entra a apoyar. Está previsto'],
    ['R3', '**Cómputo insuficiente.** Todavía no sabemos qué máquinas hay. CryptoMamba puede depender de CUDA — hay que verificarlo', 'Elimina modelos de la lista del enunciado', 'Confirmar máquinas esta semana. Verificar la dependencia antes de que alguien elija ese modelo'],
    ['R4', '**Fuga de información.** Como la etiqueta de un instante requiere ver el futuro, es fácil contaminar las características sin darse cuenta', 'Resultados excelentes y falsos. Es el peor caso porque no se nota', 'Prueba automática obligatoria (RF-E2). Se implementa antes que las características'],
    ['R5', '**La aplicación consume el tiempo del modelado.** Ahora es un módulo completo', 'Se llega a la semana 5 con la app linda y el informe flojo', 'El alcance está cerrado en tres modos. La app no lleva lógica de negocio'],
    ['R6', '**Carga documental.** Cinco documentos y cinco exposiciones en cinco semanas, con la rúbrica pesando 66 % en forma', 'Documentos apurados, que es exactamente donde más se pierde nota', 'La sección del documento es parte de la definición de terminado, no una tarea aparte'],
    ['R7', '**La respuesta del profesor cambia el alcance.** En particular D4, sobre qué es tiempo real', 'Puede redefinir la app y las pruebas de las semanas 3 y 4', 'Enviar la consulta ya, no la semana que viene'],
  ],
  [5, 35, 27, 33],
));

// --- 15
push(h1('15. Supuestos no verificados'));
push(...calloutBlock([
  'Esta sección existe porque es más honesto que dejarlos escondidos en el texto. **Nada de lo que sigue está medido.**',
]));
[
  'Que existe una fuente pública y gratuita con velas OHLCV de las seis criptomonedas, accesible desde Costa Rica. No se ha probado.',
  'Que la ventana histórica común arranca alrededor de 2020, limitada por Solana, que es la de listado más reciente. Es una creencia, no una verificación.',
  'Que en velas diarias hay alrededor de 2.000 observaciones desde 2020. Es aritmética sobre días transcurridos, no un conteo sobre datos reales.',
  'Que las clases Máximo y Mínimo van a estar por debajo del 17 % cada una con una ventana de 5. Esto sí es una cota aritmética demostrable, pero el valor real será menor y no se ha medido.',
  'Que existe un modelo fundacional en Hugging Face que corre en CPU en tiempo razonable para este problema. No se ha probado ninguno.',
  'Que CryptoMamba depende de CUDA y es problemático en Windows. Es una sospecha, no una verificación.',
  'Que las fechas de cierre semanal son los martes. Está por confirmar con el profesor.',
].forEach((t) => push(num(t, 5)));
push(p('**Cada uno de estos supuestos se convierte en una medición o se retira del documento antes del cierre de la Semana 1.**'));

// --- 16
push(h1('16. Glosario'));
const glosario = [
  ['Vela (candle)', 'Una observación de precio agrupada en un intervalo de tiempo — un día, una hora. Trae apertura, máximo, mínimo, cierre y volumen. Nosotros usamos el cierre.'],
  ['OHLCV', 'Apertura, máximo, mínimo, cierre y volumen. Los cinco campos de una vela.'],
  ['Etiqueta', 'La respuesta correcta que el modelo debe aprender a dar. Acá: Máximo, Mínimo o Continuidad.'],
  ['Serie estacionaria', 'Una serie cuyas propiedades estadísticas no cambian con el tiempo. Los precios de cripto no lo son, y ese es parte del problema.'],
  ['Heterocedasticidad', 'Que la volatilidad no sea constante. Hay períodos tranquilos y períodos agitados.'],
  ['Clases desbalanceadas', 'Cuando una etiqueta aparece muchísimo más que las otras. Rompe la exactitud como medida de calidad.'],
  ['F1-Score', 'Medida que combina cuántos de los giros anunciados eran de verdad giros con cuántos de los giros reales logramos anunciar. No se deja engañar por el desbalance.'],
  ['F1 macro', 'El promedio del F1 de las tres clases, dando a cada una el mismo peso. Es duro con los modelos que ignoran las clases raras, que es justo lo que queremos.'],
  ['Baseline trivial', 'Un modelo tonto que siempre responde lo mismo. Sirve como piso: si no lo superamos, no tenemos nada.'],
  ['Fuga de información', 'Cuando el modelo recibe sin querer información del futuro que en la práctica no tendría. Produce resultados excelentes y falsos.'],
  ['Modelo fundacional', 'Un modelo grande preentrenado sobre muchísimas series de tiempo, que se puede usar sin entrenarlo desde cero.'],
  ['Contrato congelado', 'Una definición acordada que varios módulos consumen y que nadie cambia por su cuenta.'],
  ['Mock (dato falso)', 'Una versión simulada de algo que todavía no existe, para poder trabajar sin esperar a que exista.'],
];
push(...tableBlock(['Término', 'Significado'], glosario, [22, 78]));

push(new Paragraph({
  spacing: { before: 300 },
  border: { top: { style: BorderStyle.SINGLE, size: 6, color: RULE, space: 10 } },
  children: [new TextRun({ text: 'Este documento se actualiza. Si algo cambia, cambia acá primero y después en el código.', italics: true, size: 19, color: MUTED, font: BODY_FONT })],
}));

// ---------------------------------------------------------------------------
const heading = (size, color, before, after, extra = {}) => ({
  run: { font: BODY_FONT, size, bold: true, color },
  paragraph: { spacing: { before, after }, ...extra },
});

const doc = new Document({
  creator: 'Fabrizio Espinoza Arce',
  title: 'PRD — Sistema de Pronóstico de Puntos de Inflexión en LTC',
  description: 'Documento de Requisitos de Producto — Caso N.º 1, Señales y Sistemas',
  features: { updateFields: true },
  styles: {
    default: {
      document: { run: { font: BODY_FONT, size: 21, color: '20242B' }, paragraph: { spacing: { line: 276, after: 140 } } },
      heading1: heading(32, NAVY, 400, 180, { border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: ACCENT, space: 6 } } }),
      heading2: heading(25, ACCENT, 300, 120),
      heading3: heading(22, NAVY, 240, 100),
    },
  },
  numbering: {
    config: [
      {
        reference: 'vinetas',
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 420, hanging: 220 } }, run: { color: ACCENT } },
        }],
      },
      {
        reference: 'numeros',
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 460, hanging: 260 } }, run: { color: ACCENT, bold: true } },
        }],
      },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440, header: 720, footer: 620 },
      },
      titlePage: true,
    },
    headers: {
      first: new Header({ children: [new Paragraph('')] }),
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: RULE, space: 6 } },
          children: [new TextRun({ text: 'PRD · Pronóstico de Puntos de Inflexión en LTC · v1.0', size: 17, color: MUTED, font: BODY_FONT })],
        })],
      }),
    },
    footers: {
      first: new Footer({ children: [new Paragraph('')] }),
      default: new Footer({
        children: [new Paragraph({
          tabStops: [{ type: TabStopType.RIGHT, position: CONTENT_W }],
          children: [
            new TextRun({ text: 'Caso N.º 1 — Señales y Sistemas', size: 17, color: MUTED, font: BODY_FONT }),
            new TextRun({ text: '\t', size: 17 }),
            new TextRun({ text: 'Página ', size: 17, color: MUTED, font: BODY_FONT }),
            new TextRun({ children: [PageNumber.CURRENT], size: 17, color: NAVY, bold: true, font: BODY_FONT }),
            new TextRun({ text: ' de ', size: 17, color: MUTED, font: BODY_FONT }),
            new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 17, color: MUTED, font: BODY_FONT }),
          ],
        })],
      }),
    },
    children: [...cover(), ...body],
  }],
});

const out = process.argv[2];
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(out, buf);
  console.log('escrito:', out, buf.length, 'bytes');
});
