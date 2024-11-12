# Transformaciones aplicadas al catálogo bibliográfico

## ¿Qué columnas se procesan?
- Biblioteca
- Lugar de publicación
- Fecha de publicación
- Tema principal
- Autor
- Título
- Número Dewey
- Periodo cronológico

## ¿Qué se hace con cada columna?
### Detalle de las Transformaciones Normalizadas en Cada Columna

---

### 1. **Biblioteca**
   - **Verificación de biblioteca asignada**: Los registros se filtran para asegurar que al menos una biblioteca esté especificada. Si un registro carece de este dato, se considera incompleto y se guarda en un archivo separado.
   
---

### 2. **Lugar de Publicación**
   - **Estandarización de nombres**:
      - **Ciudades conocidas**: Se reemplazan las variantes comunes con el nombre estandarizado. Ejemplo: `"México"` se convierte en `"Ciudad de México"`; `"New York"` en `"Nueva York"`.
      - **Múltiples lugares**: Si el lugar de publicación incluye múltiples ubicaciones, se guardan únicamente las dos primeras.
      - **Paréntesis y espacios**: Se eliminan paréntesis y espacios superfluos. Por ejemplo, `"León ( España)"` se convierte en `"León"`.
   - **Lugar no identificado**: En casos de falta de datos o caracteres inválidos, se marca como `"Lugar no identificado"`.

---

### 3. **Fecha de Publicación**
   - **Extracción del año**: Se extrae únicamente el año de los datos de fecha, eliminando caracteres no numéricos y manteniendo únicamente los dígitos del año.
   - **Rango de fechas**: Si la fecha incluye un rango (por ejemplo, `"2019-2020"`), se selecciona el año más reciente.
   - **Símbolos y prefijos**: Se eliminan símbolos como `©`, `c.` (circa), y palabras como `"aprox."`. Si el valor no es numérico, como `"sin fecha"`, se asigna como `None`.

---

### 4. **Autor**
   - **Formato de Nombre**: Los nombres se organizan en formato `"Apellido, Nombre"`. Se ajustan mayúsculas y minúsculas para consistencia.
   - **Múltiples autores**: Si hay varios autores en un campo, se separan con punto y coma (`;`). Ejemplo: `"Süskind, Patrick,; Gambolini, Gerardo"` se convierte en `"Süskind, Patrick; Gambolini, Gerardo"`.
   - **Títulos académicos**: Se eliminan títulos como `"Dr."`, `"PhD"`, y partículas nobiliarias se mantienen, como en `"von Goethe"`.
   - **Autor desconocido**: Si el campo está vacío o contiene `np.nan`, se asigna `"Desconocido"`.

---

### 5. **Título**
   - **Eliminación de símbolos especiales**: Se eliminan símbolos no necesarios (por ejemplo, signos de exclamación, puntos) para mantener un formato limpio.
   - **Mantenimiento de acrónimos**: Siglas y acrónimos como `C++` se conservan tal como aparecen.
   - **Título desconocido**: Si el campo está vacío, se asigna `"Sin título"`.

---

### 6. **Número Dewey**
   - **Tres primeros dígitos**: Se extraen solo los primeros tres dígitos del número Dewey para facilitar la clasificación.
   - **Eliminación de prefijos y separadores**: Se eliminan prefijos no numéricos y caracteres adicionales como `;`, `/`, `-` y espacios.
   - **Casos especiales**: Si el número tiene menos de tres dígitos o no es numérico, se deja vacío (`""`).

---

### 7. **Periodo Cronológico**
   - **Conversión a siglos en números romanos**: Se traduce el formato de siglos a números romanos, por ejemplo, `"Siglo xx"` a `"XX"`, sin importar el caso o espacios.
   - **Rangos de siglos**: Si el periodo contiene un rango, se selecciona el siglo más reciente.
   - **Casos de siglos repetidos**: Si se repite el mismo siglo o el mismo rango, se retiene el último siglo.
   - **Asignación de siglo a años específicos**: Si se encuentran fechas en lugar de siglos, se asigna el siglo correspondiente (por ejemplo, `"1830-1990"` se convierte en `"XX"`).
   - **Sin siglo identificable**: Si no se encuentra un dato válido, se asigna `None`.

---

### 8. **Tema**
   - **Comparación con vocabulario controlado**: Cada tema se compara con un vocabulario estandarizado y se selecciona el tema más cercano en significado.
   - **Puntaje de confianza**: Se asigna un puntaje de confianza que mide la exactitud de la correspondencia entre el tema original y el tema controlado.

---

### 9. **Editorial**
   - **Separación de múltiples editoriales**:
     - Si el campo contiene múltiples editoriales separadas por coma (`,`) o punto y coma (`;`), se extraen las dos primeras.
     - Se eliminan espacios en exceso, puntuaciones innecesarias y símbolos especiales.
   - **Formato de nombre**:
     - Las palabras en el nombre de la editorial se capitalizan para mantener consistencia. Por ejemplo, `"universidad de antioquia"` se convierte en `"Universidad De Antioquia"`.
   - **Eliminación de información adicional**:
     - Se eliminan datos entre paréntesis que indican localización o ediciones específicas. Por ejemplo, `"Alfaguara (Colombia)"` se convierte en `"Alfaguara"`.
   - **Editorial no identificada**:
     - Si el campo está vacío, contiene caracteres inválidos (`##`, `np.nan`), o no se puede identificar correctamente, se asigna `"Editorial no identificada"`.

---

### **Archivos de Salida Actualizados**
1. **_procesado.csv**: Incluye registros con la columna de Editorial normalizada según los criterios mencionados.
2. **_descartados.csv**: Archiva los registros con editoriales no identificadas o datos incompletos.

Esta sección sigue la misma estructura de las demás columnas, asegurando una normalización completa del catálogo bibliográfico.
---

### **Archivos de Salida**
1. **_procesado.csv**: Contiene los registros con datos normalizados y clasificados según los criterios mencionados.
2. **_descartados.csv**: Archiva los registros que no cumplen con los requisitos de normalización, especialmente aquellos sin biblioteca asignada o sin suficientes datos de referencia para otras columnas.
