Muchachos, subí mi parte en la carpeta miguel/ (recuperación 5.5, versiones y licenciamiento 5.3, sitio alterno del B y el plan de 72 horas). Empiecen por README.md.

Lo que necesito de cada uno:

- David: respondí lo de D-2 en respuesta_a_david.md. Lo acepto con 2 condiciones (cómo saber qué sillas tenía un pago aprobado, y que la conciliación de desastre parta de la lista de la pasarela y no de gsi_pendientes). Necesito que tu alta_disponibilidad.md coincida con mi tabla de RTO y que me des el RPO de los escaneos del estadio.
- Jacobo: te revisé en revision_de_jacobo.md. El hallazgo importante: la conmutación de origen de CloudFront no funciona con POST/PUT, o sea que no sirve para la compra. Hay que corregirlo en arquitectura.md y en el diagrama del B. También te respondí lo de bya_audit.
- Juan Pablo: lista_componentes_para_juan_pablo.md tiene todo lo de respaldo y recuperación para costear, con volúmenes por tabla y año. No puse precios, son tuyos. Avísame pronto si algo no cabe en los 280 millones.
- Samuel: fichas_decision_miguel.md (R-1 y R-2) para el registro. Necesito de ti el plazo legal de retención, y confirmar que ningún respaldo guarde números de tarjeta.

Ojo: AWS no publica tiempos de restauración, así que los tiempos de mis runbooks son estimaciones y están marcados como supuestos. Nada de eso se pudo probar.

Pregunta al profesor (P-4): "pérdida total del sitio" ¿es zona, región o data center? Propongo mandarla junto con la P-1 de Escenario B.
