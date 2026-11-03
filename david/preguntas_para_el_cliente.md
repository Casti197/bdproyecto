# Preguntas para el cliente (BoletaYa SAS)

**Fecha:** 2026-11-03 · Redactadas en lenguaje de negocio: el profesor responde como dueño de la empresa. Cada pregunta dice, en una línea, **por qué la hacemos**. La versión técnica (con los números de pregunta P-xx del equipo) está en `preguntas_para_el_profesor.md`; la equivalencia va entre corchetes.
**Prioridad (★):** si solo hay tiempo para pocas, las marcadas son las que cambian el diseño.

## 1. Qué es el negocio y qué esperan de nosotros

1. ★ Cuando dicen que habrá "hasta 60.000 boletas" en una preventa y los estadios tienen 45.000 sillas, ¿se trata de varias fechas a la vez, de un festival, o es un número para el peor caso? *(Para saber cuánta gente compite por qué.)* [P-2]
2. ¿Cuántas preventas esperan hacer al año y de qué tamaño suele ser la típica, no solo la más grande? *(Para calcular costos reales y no solo del pico.)* [P-58]
3. ¿Qué es más grave para el negocio: que un cliente no pueda comprar unos minutos, o que dos clientes terminen con la misma silla? *(Define qué sacrificamos primero en una emergencia.)* [P-16, P-32]
4. ¿Qué entregables esperan exactamente de nuestro equipo y cómo se calificará cada uno? ¿Hay un ejemplo de una buena entrega? [P-10, P-14]
5. ¿Esperan un sistema funcionando o un diseño bien justificado? [P-12]
6. ¿Quieren que entreguemos las dos opciones (A y B) comparadas, o que recomendemos una? [P-9]
7. ¿Podemos usar una cuenta real de la nube para hacer pruebas y mediciones, o solo documentación? [P-13]
8. ¿Cómo debemos citar nuestras fuentes? ¿Solo documentos oficiales del proveedor o también casos de otras empresas? [P-15]

## 2. Dónde vive la plataforma

9. ★ En el escenario A, ¿es obligatorio que los servidores estén físicamente en su centro de datos de Bogotá, o les da igual mientras funcione bien y rápido? [P-3]
10. ★ Hemos elegido una base de datos que solo funciona en la nube del proveedor y no se puede instalar en su centro de datos. En el escenario B, ¿aceptan que la base esté en la nube y que en Bogotá quede el resto (la aplicación, la memoria rápida y el control del estadio)? [P-1]
11. ★ ¿Les molesta que los datos de sus compradores se guarden en un país distinto a Colombia (por ejemplo Estados Unidos)? ¿Su asesor legal ya opinó? [P-6]
12. ¿Tienen alguna restricción de proveedor, región o tecnología que debamos respetar desde el principio? [P-34, P-61]
13. ¿Podemos comparar con otras opciones para justificar nuestra elección, o la tecnología ya está decidida? [P-61]

## 3. Qué pasa cuando muchos compran a la vez

14. ★ Cuando alguien escoge una silla, ¿cuánto tiempo estarían dispuestos a "guardársela" mientras paga? Nosotros pensamos 8 minutos. ¿Les parece mucho, poco, o ya tienen una política? [P-17]
15. ¿Cuántas sillas puede comprar una persona por evento? Pensamos 10. ¿Eso lo decide la empresa, el artista o la ley? ¿Cómo identifican a "una persona": por cuenta, documento, tarjeta? [P-18]
16. Si alguien paga pero justo en ese momento su silla se vendió a otra persona porque se le acabó el tiempo, ¿prefieren devolverle el dinero o ofrecerle otra silla parecida? ¿En cuánto tiempo debe llegar el reembolso? [P-19]
17. ¿Está permitido vender más boletas que sillas (sobreventa), aunque sea un poco? [P-20]
18. ¿El cliente escoge su silla en un mapa, o a veces el sistema le asigna "la mejor disponible"? ¿Hay zonas sin silla numerada, de pie? [P-21]
19. ★ ¿Cuánto es una espera aceptable para el cliente? ¿Qué prefieren: una sala de espera ordenada donde la gente espera su turno, o que todos entren a la vez y algunos fallen? [P-24, P-5]
20. ¿Aceptan contratar un servicio de terceros para la fila virtual y para frenar a los programas que compran por bots? ¿Hay presupuesto? [P-5, P-26]
21. ¿Se vende también en taquilla física o por otros canales mientras corre la preventa online? ¿Quién manda si hay choque? [P-23]
22. ¿Cuánto les preocupa el costo de que el sistema sea más estricto (por ejemplo, que revise cada compra con más cuidado)? ¿Prefieren ahorrar o ir seguros? [P-25, P-29]

## 4. Pagos

23. ★ ¿Ya tienen un proveedor de pagos (por ejemplo PSE, Wompi, PayU)? ¿Lo podemos escoger nosotros? *(Nuestro plan de "no perder ni un pago" depende de lo que permita el proveedor.)* [P-22]
24. ¿El cliente paga dentro de su página o lo mandan a la del proveedor? [P-22]
25. ¿Guardan datos de tarjetas, o prefieren no guardarlos nunca? [P-53]
26. Si se cobra a un cliente y el sistema se cae justo antes de darle su boleta, ¿cuál es la regla: entregarle la boleta después, o devolverle el dinero? ¿En cuánto tiempo? [P-19, P-40]
27. ¿Hay pagos que no se puedan reembolsar, o reembolsos que deban aprobar personas? [P-40]
28. ¿Se emite factura electrónica por cada compra? ¿Con qué proveedor? [P-55]

## 5. Si algo se rompe (disponibilidad y recuperación)

29. ★ Cuando dicen "pérdida total del sitio", ¿qué imaginan: que se cae un edificio del proveedor, que se cae una ciudad o región entera, o que se pierde su centro de datos de Bogotá? [P-4]
30. ★ El tiempo máximo para volver a funcionar es de 15 minutos. ¿Cuenta desde que ocurre la falla o desde que ustedes la reconocen? ¿Se considera "recuperado" cuando ya se puede volver a vender, o cuando todo está revisado y cuadrado? [P-30]
31. ★ La regla de "no perder ningún dato": ¿aplica a todo, o solo a las compras ya pagadas y a las boletas entregadas? ¿Es aceptable que un cliente que apenas estaba escogiendo silla tenga que volver a empezar? [P-31]
32. En una falla grave del proveedor, ¿prefieren que dejemos de vender unos minutos para estar seguros de no perder pagos ni vender sillas dos veces, o que se siga vendiendo con algo de riesgo? [P-32]
33. Si la solución tarda más de lo prometido (por ejemplo 20 minutos en vez de 15), ¿qué consecuencia tiene para ustedes? ¿Hay multas o contratos con artistas? [P-30]
34. ¿Quién decide, por parte de la empresa, que se declara la emergencia y quién autoriza volver a vender? ¿Quién está de guardia? [P-38]
35. ¿Cada cuánto quieren que se ensaye un desastre y qué evidencia quieren ver de que funcionó? [P-33, P-38]
36. ¿Se exige poder volver al estado de ayer si alguien borra o daña datos por error o por un ataque? ¿Cuántos días hacia atrás? [P-36, P-37]
37. ¿Qué pasa con las preventas mientras se arregla todo: se avisa a los clientes, se compensa a alguien? [P-32]
38. Cuando el proveedor se recupera, ¿quieren volver al lugar original o se pueden quedar donde están? [P-39]
39. ¿Qué disponibilidad mínima prometen a sus clientes (por ejemplo "99,99 % del tiempo")? ¿Medida por mes o por año? [P-35]

## 6. Ingreso al estadio

40. ★ Cuando dicen "sin internet", ¿se refieren a que el estadio pierde la conexión con la nube, o también a que se cae la red del estadio? ¿Por cuánto tiempo tendría que seguir funcionando solo? [P-41]
41. ★ Para que nadie entre dos veces con la misma boleta aunque no haya internet, la forma más segura es que cada boleta solo sirva por una puerta asignada. ¿Es aceptable para el negocio? *(Si no, habría una pequeña ventana en la que alguien podría entrar dos veces por puertas distintas.)* [P-42, P-43]
42. Si no se puede limitar la puerta, ¿cuántos casos de doble ingreso tolerarían en un evento, con la revisión después? [P-43]
43. ¿Cuántas puertas y cuántos torniquetes tiene un estadio típico y cuánta gente por hora debe poder pasar? Nosotros suponemos 12 puertas con 4 torniquetes cada una. [P-44]
44. ¿Con qué se identifica la boleta: código QR en el celular, impreso, pulsera? ¿Podría alguien copiarlo? ¿Les preocupa? [P-45]
45. ¿Tienen ya equipos en los estadios (computadores, lectores) o debemos comprar todo? ¿Quién los instala y los cuida? [P-46, P-51]
46. ¿Hay energía de respaldo en los estadios? ¿Cuánto tiempo debe aguantar el control de acceso sin luz? [P-47]
47. Si la boleta ya fue usada o es falsa, ¿qué debe pasar en la puerta: bloquear, llamar a un supervisor, dejarlo pasar con registro? ¿Cuánto debe tardar cada persona en pasar? [P-48]
48. ¿Se permite que un supervisor deje entrar a alguien manualmente en una emergencia (por ejemplo con el documento)? ¿Cómo se registra? [P-49]
49. Los equipos del estadio, ¿deben tener soporte del fabricante por varios años? Nosotros proponemos al menos 5. [P-50]

## 7. Datos personales y legal

50. ¿Qué normas les exigen cumplir: la ley de datos personales, estándares de tarjetas, otras? ¿El análisis legal forma parte de la entrega o es un anexo? [P-52]
51. ¿Cuánto tiempo deben guardar las compras, los pagos y las facturas? [P-54]
52. Si un cliente pide que borren sus datos, ¿qué hacemos con sus boletas y facturas anteriores? [P-57]
53. ¿Qué acciones de sus empleados quieren que queden registradas (cambio de precios, reembolsos, accesos) y por cuánto tiempo? [P-56]

## 8. Costos

54. ¿Cuánto presupuesto tienen para tecnología por preventa y por año? ¿Hay un tope que no se puede pasar? [P-25, P-58]
55. ¿Qué tipo de cambio usamos para convertir dólares a pesos y cuenta el IVA? [P-59]
56. ¿Incluimos en el costo las licencias, la guardia técnica y las horas del administrador (estimamos 6 por preventa)? ¿Cuánto cuesta la hora? [P-60, P-62]
57. El equipo del estadio, ¿se cuenta como inversión inicial, como costo anual o por preventa? [P-51]
58. ¿Quieren ver la captura de la calculadora de precios del proveedor o basta con la lista oficial de precios? [P-8]
59. El enunciado pide el volumen de datos "por nivel de almacenamiento": ¿se refiere a datos recientes, antiguos y de archivo? [P-7]

## 9. Cómo trabajamos con ustedes

60. ¿Podemos usar herramientas de inteligencia artificial y un repositorio compartido? ¿Debemos declararlo? [P-63]
61. Nuestro repositorio está público: ¿prefieren que sea privado y compartido solo con usted? [P-64]
62. ¿La evaluación de cada integrante es individual, y cómo se valora que las partes encajen entre sí? [P-65]
63. ¿Cuáles son las fechas de entrega de avances y de la versión final? ¿Podemos corregir tras su retroalimentación? [P-66]
64. ¿Podemos agendar una reunión corta antes de la entrega para validar las decisiones más importantes? [P-67]

## Suposiciones que haremos si no hay respuesta
Se dejan escritas en cada documento: bloqueo de 8 minutos; máximo 10 sillas por usuario y evento; reembolso si la silla se perdió; una sola región escribe; ventas cerradas durante una conmutación regional hasta conciliar con el proveedor de pagos; una puerta asignada por boleta; 12 puertas con 4 torniquetes por estadio; equipos con soporte de 5 años.
