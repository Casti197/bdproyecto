Actualización 3-nov (Miguel):

- Decidimos Jacobo, David y yo usar el listado de transacciones de la pasarela por rango de fechas como punto de partida de la conciliación de desastre. Ya está en miguel/ (README, carta, fichas). Falta confirmarlo con la pasarela concreta.
- Gracias Jacobo y David: vi las correcciones de CloudFront, la cola virtual en AWS, el pre-calentamiento y el RTO de 7 a 13 / 7 a 16 min. Quedamos alineados.
- Pendiente de los tres: fijar la pasarela con llave de idempotencia y metadatos en el cobro (sillas, evento, usuario). Sin metadatos las sillas de un pago no se pueden reconstruir y se reembolsa, o se activa el libro de pagos (bya_ledger).
- Juan Pablo: la lista de componentes está en miguel/lista_componentes_para_juan_pablo.md (con PostgreSQL del estadio y Ubuntu Pro sin precio). Avísame si algo no cabe en los 280 millones del año 1.
- Samuel: falta tu conformidad con D-2, el plazo legal de retención y confirmar que ningún respaldo guarda números de tarjeta.
- Profesor: falta enviar P-1, P-3, P-4, P-6, P-16, P-30 y P-41. David, ¿las envías tú?
