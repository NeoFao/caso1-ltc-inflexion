// Primitivas de formato APA 7 compartidas por los generadores de entregables.
//
// Estan aqui y no duplicadas en cada script porque dos implementaciones del mismo
// formato divergen: se corrige el margen en una y en la otra no, y nadie lo nota
// hasta que el profesor compara dos entregas.
//
// Todo sale del Publication Manual 7.a ed.: Times New Roman 12, doble espacio,
// margenes de una pulgada, sangria de primera linea de media pulgada, numero de
// pagina arriba a la derecha, niveles de titulo, tablas sin lineas verticales y
// referencias con sangria francesa.
//
// Monocromo. Lo unico que no es negro son los avisos de contenido pendiente, en
// gris, para que sea imposible entregar uno sin verlo.

const {
  Paragraph, TextRun, ImageRun, AlignmentType, HeadingLevel,
  Table, TableRow, TableCell, WidthType, BorderStyle,
  Header, PageNumber, PageBreak, LineRuleType,
} = require('docx');
const fs = require('fs');

const FUENTE = 'Times New Roman';
const TAM = 24;            // 12 pt en medios puntos
const DOBLE = 480;         // 240 = simple, 480 = doble
const SANGRIA = 720;       // media pulgada
const NEGRO = '000000';
const GRIS = '595959';
const ANCHO_UTIL = 9360;   // 12240 (carta) menos dos margenes de 1440
const ANCHO_IMAGEN = 600;  // px a 96 dpi, ~6,25 pulgadas

const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];

/** "2020-08-11" -> "11 de agosto de 2020". En prosa castellana el ISO desentona. */
function fechaLarga(iso) {
  const [anio, mes, dia] = iso.slice(0, 10).split('-');
  return `${Number(dia)} de ${MESES[Number(mes) - 1]} de ${anio}`;
}

/**
 * Convierte marcado de linea en TextRun: **negrita**, *cursiva*, `codigo`,
 * [texto](url). Los enlaces se emiten como texto plano porque un documento
 * academico impreso no tiene donde hacer clic.
 */
function runs(texto, opciones = {}) {
  const base = {
    font: FUENTE,
    size: opciones.size || TAM,
    color: opciones.color || NEGRO,
  };
  const salida = [];
  const patron = /(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g;
  let ultimo = 0;
  let encontrado;

  const plano = (t, extra = {}) => {
    if (t) salida.push(new TextRun({
      ...base, text: t,
      bold: opciones.bold, italics: opciones.italics, ...extra,
    }));
  };

  while ((encontrado = patron.exec(texto)) !== null) {
    plano(texto.slice(ultimo, encontrado.index));
    const ficha = encontrado[0];
    if (ficha.startsWith('**')) {
      // Recursivo: dentro de una negrita puede haber codigo o cursiva, y sin
      // volver a analizar el interior los delimitadores se imprimen literales.
      salida.push(...runs(ficha.slice(2, -2), { ...opciones, bold: true }));
    } else if (ficha.startsWith('`')) {
      plano(ficha.slice(1, -1), { font: 'Courier New', size: base.size - 2 });
    } else if (ficha.startsWith('[')) {
      // El texto del enlace puede traer codigo o negrita dentro:
      // [`archivo.json`](url). Sin volver a analizarlo, los delimitadores se
      // imprimen literales en el documento.
      salida.push(...runs(ficha.slice(1, ficha.indexOf(']')), opciones));
    } else {
      salida.push(...runs(ficha.slice(1, -1), { ...opciones, italics: true }));
    }
    ultimo = patron.lastIndex;
  }
  plano(texto.slice(ultimo));
  return salida.length ? salida : [new TextRun({ ...base, text: '' })];
}

const parrafo = (texto, opciones = {}) => new Paragraph({
  spacing: { line: DOBLE, lineRule: LineRuleType.AUTO, after: 0 },
  indent: opciones.sinSangria ? opciones.indent : { firstLine: SANGRIA, ...opciones.indent },
  alignment: opciones.alineacion,
  keepNext: opciones.keepNext,
  children: runs(texto, opciones),
});

/** Cita en bloque: sangrada media pulgada y sin comillas, como pide APA 7. */
const citaEnBloque = (texto) => new Paragraph({
  spacing: { line: DOBLE, lineRule: LineRuleType.AUTO, after: 0 },
  indent: { left: SANGRIA },
  children: runs(texto),
});

/** Aviso de contenido sin redactar. En gris para que salte a la vista. */
const aviso = (texto) => new Paragraph({
  spacing: { line: DOBLE, lineRule: LineRuleType.AUTO, after: 0 },
  indent: { firstLine: SANGRIA },
  children: [new TextRun({ text: texto, font: FUENTE, size: TAM, color: GRIS, italics: true })],
});

// Niveles de titulo APA 7: el 1 centrado y en negrita, el 2 al margen izquierdo y
// en negrita, el 3 al margen izquierdo en negrita y cursiva.
function titulo(nivel, texto) {
  const encabezados = [HeadingLevel.HEADING_1, HeadingLevel.HEADING_2, HeadingLevel.HEADING_3];
  return new Paragraph({
    heading: encabezados[nivel - 1],
    alignment: nivel === 1 ? AlignmentType.CENTER : undefined,
    spacing: { line: DOBLE, lineRule: LineRuleType.AUTO, before: 0, after: 0 },
    keepNext: true,
    children: [new TextRun({
      text: texto, font: FUENTE, size: TAM, color: NEGRO,
      bold: true, italics: nivel === 3,
    })],
  });
}

/** Alto proporcional de un PNG a partir de su cabecera, sin cargar la imagen. */
function dimensiones(ruta) {
  const contenido = fs.readFileSync(ruta);
  return {
    ancho: contenido.readUInt32BE(16),
    alto: contenido.readUInt32BE(20),
    contenido,
  };
}

/**
 * Figura APA 7: numero en negrita, titulo en cursiva, la imagen, y la nota.
 * keepNext mantiene numero y titulo con la imagen en la misma pagina.
 */
function figura(numero, tituloFigura, rutaImagen, nota) {
  const { ancho, alto, contenido } = dimensiones(rutaImagen);
  const bloques = [
    new Paragraph({
      keepNext: true,
      spacing: { line: DOBLE, lineRule: LineRuleType.AUTO, before: 240, after: 0 },
      children: [new TextRun({
        text: `Figura ${numero}`, font: FUENTE, size: TAM, bold: true, color: NEGRO,
      })],
    }),
    new Paragraph({
      keepNext: true,
      spacing: { line: DOBLE, lineRule: LineRuleType.AUTO, after: 120 },
      children: runs(tituloFigura, { italics: true }),
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 120 },
      children: [new ImageRun({
        data: contenido, type: 'png',
        transformation: {
          width: ANCHO_IMAGEN,
          height: Math.round(ANCHO_IMAGEN * (alto / ancho)),
        },
      })],
    }),
  ];
  if (nota) bloques.push(notaDebajo(nota));
  return bloques;
}

function notaDebajo(texto) {
  return new Paragraph({
    spacing: { line: DOBLE, lineRule: LineRuleType.AUTO, after: 240 },
    children: [
      new TextRun({ text: 'Nota.', font: FUENTE, size: TAM, italics: true, color: NEGRO }),
      ...runs(` ${texto}`),
    ],
  });
}

const celda = (texto, opciones = {}) => new TableCell({
  width: { size: opciones.ancho, type: WidthType.DXA },
  margins: { top: 60, bottom: 60, left: 100, right: 100 },
  borders: {
    top: opciones.bordeArriba
      ? { style: BorderStyle.SINGLE, size: 6, color: NEGRO } : { style: BorderStyle.NONE },
    bottom: opciones.bordeAbajo
      ? { style: BorderStyle.SINGLE, size: 6, color: NEGRO } : { style: BorderStyle.NONE },
    left: { style: BorderStyle.NONE },
    right: { style: BorderStyle.NONE },
  },
  children: [new Paragraph({
    spacing: { line: 240, lineRule: LineRuleType.AUTO, after: 0 },
    alignment: opciones.alineacion,
    children: runs(texto, { size: TAM - 2 }),
  })],
});

/**
 * Tabla APA 7: sin lineas verticales, sin sombreados, y solo tres horizontales
 * — encima del encabezado, debajo del encabezado y al final.
 *
 * Los bordes hay que anularlos tambien a nivel de tabla: los de celda no bastan
 * porque la tabla dibuja los suyos por encima.
 */
function tabla(numero, tituloTabla, encabezados, filas, nota) {
  const columnas = encabezados.length;
  const ancho = Math.floor(ANCHO_UTIL / columnas);
  const anchos = Array(columnas).fill(ancho);
  anchos[columnas - 1] = ANCHO_UTIL - ancho * (columnas - 1);

  const alineacion = (i) => (i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER);

  const bloques = [
    new Paragraph({
      keepNext: true,
      spacing: { line: DOBLE, lineRule: LineRuleType.AUTO, before: 240, after: 0 },
      children: [new TextRun({
        text: `Tabla ${numero}`, font: FUENTE, size: TAM, bold: true, color: NEGRO,
      })],
    }),
    new Paragraph({
      keepNext: true,
      spacing: { line: DOBLE, lineRule: LineRuleType.AUTO, after: 60 },
      children: runs(tituloTabla, { italics: true }),
    }),
    new Table({
      columnWidths: anchos,
      width: { size: ANCHO_UTIL, type: WidthType.DXA },
      borders: {
        top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE },
        left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
        insideHorizontal: { style: BorderStyle.NONE },
        insideVertical: { style: BorderStyle.NONE },
      },
      rows: [
        new TableRow({
          tableHeader: true,
          children: encabezados.map((t, i) => celda(t, {
            ancho: anchos[i], bordeArriba: true, bordeAbajo: true, alineacion: alineacion(i),
          })),
        }),
        ...filas.map((fila, indice) => new TableRow({
          children: fila.map((t, i) => celda(t, {
            ancho: anchos[i],
            bordeAbajo: indice === filas.length - 1,
            alineacion: alineacion(i),
          })),
        })),
      ],
    }),
  ];
  if (nota) bloques.push(notaDebajo(nota));
  else bloques.push(new Paragraph({ text: '', spacing: { after: 240 } }));
  return bloques;
}

/** Referencia con sangria francesa de media pulgada. */
const referencia = (texto) => new Paragraph({
  spacing: { line: DOBLE, lineRule: LineRuleType.AUTO, after: 0 },
  indent: { left: SANGRIA, hanging: SANGRIA },
  children: runs(texto),
});

/** Encabezado APA 7 para trabajo de estudiante: solo el numero de pagina. */
const encabezadoPagina = () => new Header({
  children: [new Paragraph({
    alignment: AlignmentType.RIGHT,
    spacing: { after: 0 },
    children: [new TextRun({
      children: [PageNumber.CURRENT], font: FUENTE, size: TAM, color: NEGRO,
    })],
  })],
});

const estilosDocumento = () => ({
  default: {
    document: {
      run: { font: FUENTE, size: TAM, color: NEGRO },
      paragraph: { spacing: { line: DOBLE, lineRule: LineRuleType.AUTO } },
    },
    heading1: {
      run: { font: FUENTE, size: TAM, bold: true, color: NEGRO },
      paragraph: { alignment: AlignmentType.CENTER, spacing: { line: DOBLE, before: 0, after: 0 } },
    },
    heading2: {
      run: { font: FUENTE, size: TAM, bold: true, color: NEGRO },
      paragraph: { spacing: { line: DOBLE, before: 0, after: 0 } },
    },
    heading3: {
      run: { font: FUENTE, size: TAM, bold: true, italics: true, color: NEGRO },
      paragraph: { spacing: { line: DOBLE, before: 0, after: 0 } },
    },
  },
});

const propiedadesPagina = () => ({
  page: {
    size: { width: 12240, height: 15840 },
    margin: { top: 1440, right: 1440, bottom: 1440, left: 1440, header: 720, footer: 720 },
  },
});

module.exports = {
  FUENTE, TAM, DOBLE, SANGRIA, NEGRO, GRIS, ANCHO_UTIL,
  fechaLarga, runs, parrafo, citaEnBloque, aviso, titulo,
  figura, tabla, notaDebajo, referencia,
  encabezadoPagina, estilosDocumento, propiedadesPagina,
  PageBreak,
};
