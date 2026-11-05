# Ecosistema DO: Servicios de datos

## El problema

El 80% del tiempo de análisis se pierde buscando y limpiando datos. Ese trabajo se repite en cada equipo y rara vez se comparte: la misma fuente, depurada de diez formas distintas por diez equipos distintos. Y cuando los datos sí están disponibles, con frecuencia no pueden cruzarse entre sí: cada fuente usa sus propios nombres, unidades, formatos y esquemas.

Data Observatory existe para cambiar eso. Operamos tres servicios complementarios: uno para encontrar datos que ya existen, uno para alojar datos que no tienen dónde vivir, y uno para acceder a datos que ya fueron procesados y están listos para usarse.

## Nuestros servicios

| Servicio | ¿Qué hace? | ¿Quién aloja los datos? | Úsalo cuando… |
|---|---|---|---|
| **Catálogo DO** | Encuentra y describe datasets relevantes | La fuente original (mayoritariamente) | Buscas datos que ya existen en algún lugar |
| **Repositorio DO** | Aloja datasets que no tienen infraestructura propia | Data Observatory | Tienes datos pero no dónde publicarlos |
| **Datopia** | Acceso directo a datos procesados, citables y (cuando es posible) combinables | Data Observatory | Quieres analizar datos listos para usar |

El punto de entrada al ecosistema es **[www.dataobservatory.net](https://www.dataobservatory.net)**.

## Catálogo DO

**[catalogo.dataobservatory.net](https://catalogo.dataobservatory.net)**

*Para el investigador o analista que sabe que los datos existen, pero no sabe dónde buscarlos o cómo evaluarlos.*

Buscador curado de datos abiertos relevantes para Chile y Latinoamérica. No solo "qué hay", sino "para qué sirve, qué contiene, con qué se puede combinar".

- Los metadatos son enriquecidos y curados con herramientas de inteligencia artificial.
- La mayoría de los datos siguen en su fuente original — DO no interfiere con la cadena de custodia. Algunos datasets sí están alojados directamente por DO (los del Repositorio), pero el acceso desde el Catálogo se ve igual.
- En mejora continua: el motor de búsqueda, la cobertura de datasets, las funcionalidades disponibles y la forma de visualizar y acceder a la información evolucionan de forma permanente.


## Repositorio DO

*Para el equipo que ya procesó datos valiosos y quiere que ese trabajo sea citable, visible y reutilizable — sin montar infraestructura propia.*

Si tienes datos pero no infraestructura para publicarlos: nosotros los alojamos.

- Generación de DOI para citabilidad académica.
- Misma visibilidad que el Catálogo — tus datos, accesibles para la comunidad.
- Depuración disponible bajo demanda.


## Datopia

*Para el analista o equipo que necesita trabajar con datos complejos — múltiples archivos, formatos poco ágiles, actualizaciones periódicas — sin montar infraestructura ni descargar gigabytes antes de poder hacer la primera consulta.*

Datos que **ya fueron procesados** para que sean fáciles de usar desde el primer día.

- Sin descargas masivas: consulta solo lo que necesitas.
- Cada dataset tendrá un DOI asignado (en proceso).
- Cuando los datasets lo permiten, están diseñados para combinarse: como enchufes del mismo estándar, dos fuentes distintas que comparten dimensiones comunes se conectan sin adaptadores. Ejemplos: nombres de comunas, unidades de medición, códigos de servicio.

Datopia está evolucionando para ser accesible a cualquier usuario, no solo a equipos técnicos:

- **Hoy:** acceso vía código (Python, DuckDB) con credenciales propias.
- **Próximamente:** registro autogestionado — cualquier persona con un correo válido puede crear su cuenta.
- **En exploración:** interfaz web para explorar, filtrar y descargar datos sin escribir código.
- **Visión:** portal de consulta en lenguaje natural — preguntarle a los datos directamente, en español.


## La invitación

El arduo trabajo de depurar un dataset no debería quedar guardado en un cajón. Si ya lo hiciste, podemos ayudarte a compartirlo para que el próximo equipo no repita el mismo esfuerzo.

- ¿Tienes datos que depuraste? Podemos publicarlos en el Repositorio o Catálogo.
- ¿Tienes un proceso de procesamiento que automatizaste? Podemos dejarlo corriendo.
- ¿Tienes datos pero no infraestructura? Hablemos.

