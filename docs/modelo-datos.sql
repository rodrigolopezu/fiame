-- FiaMe — Modelo de datos (PostgreSQL)
-- Detalle y justificación de cada campo en docs/modelo-datos.md.
-- Dinero NUMERIC(12,2); tasas como fracción NUMERIC(12,9); tipo de cambio NUMERIC(8,3).

CREATE TABLE tasa (
    id              BIGSERIAL      PRIMARY KEY,
    tipo            VARCHAR(10)    NOT NULL CHECK (tipo IN ('EFECTIVA', 'NOMINAL')),
    periodo         VARCHAR(15)    NOT NULL,
    valor           NUMERIC(12,7)  NOT NULL CHECK (valor > 0),
    capitalizacion  VARCHAR(15),
    tea             NUMERIC(12,9)  NOT NULL,
    creado_en       TIMESTAMPTZ    NOT NULL DEFAULT now(),
    CHECK ((tipo = 'NOMINAL' AND capitalizacion IS NOT NULL)
        OR (tipo = 'EFECTIVA' AND capitalizacion IS NULL))
);

CREATE TABLE tienda (
    id          BIGSERIAL     PRIMARY KEY,
    nombre      VARCHAR(120)  NOT NULL,
    giro        VARCHAR(40)   NOT NULL,
    documento   VARCHAR(11)   UNIQUE,
    telefono    VARCHAR(15),
    direccion   VARCHAR(200),
    estado      VARCHAR(10)   NOT NULL DEFAULT 'ACTIVA' CHECK (estado IN ('ACTIVA', 'BAJA')),
    fecha_alta  TIMESTAMPTZ   NOT NULL DEFAULT now(),
    fecha_baja  TIMESTAMPTZ
);

CREATE TABLE configuracion_tienda (
    tienda_id              BIGINT         PRIMARY KEY,
    moneda                 CHAR(3)        NOT NULL CHECK (moneda IN ('PEN', 'USD')),
    limite_credito         NUMERIC(12,2)  NOT NULL CHECK (limite_credito > 0),
    max_meses              SMALLINT       NOT NULL CHECK (max_meses BETWEEN 1 AND 36),
    dia_corte              SMALLINT       NOT NULL CHECK (dia_corte BETWEEN 1 AND 28),
    dia_pago               SMALLINT       NOT NULL CHECK (dia_pago BETWEEN 1 AND 28),
    tasa_compensatoria_id  BIGINT         NOT NULL,
    tasa_moratoria_id      BIGINT         NOT NULL,
    bloquear_con_vencido   BOOLEAN        NOT NULL DEFAULT true,
    CONSTRAINT fk_config_tienda FOREIGN KEY (tienda_id) REFERENCES tienda (id),
    CONSTRAINT fk_config_tasa_comp FOREIGN KEY (tasa_compensatoria_id) REFERENCES tasa (id),
    CONSTRAINT fk_config_tasa_mora FOREIGN KEY (tasa_moratoria_id) REFERENCES tasa (id)
);

CREATE TABLE usuario (
    id             BIGSERIAL     PRIMARY KEY,
    usuario        VARCHAR(60)   NOT NULL UNIQUE,
    password_hash  VARCHAR(255)  NOT NULL,
    rol            VARCHAR(10)   NOT NULL CHECK (rol IN ('ADMIN', 'VENDEDOR')),
    tienda_id      BIGINT,
    activo         BOOLEAN       NOT NULL DEFAULT true,
    ultimo_acceso  TIMESTAMPTZ,
    creado_en      TIMESTAMPTZ   NOT NULL DEFAULT now(),
    CONSTRAINT fk_usuario_tienda FOREIGN KEY (tienda_id) REFERENCES tienda (id),
    CHECK ((rol = 'ADMIN' AND tienda_id IS NULL) OR (rol = 'VENDEDOR' AND tienda_id IS NOT NULL))
);

CREATE TABLE producto (
    id                  BIGSERIAL      PRIMARY KEY,
    tienda_id           BIGINT         NOT NULL,
    nombre              VARCHAR(120)   NOT NULL,
    descripcion         VARCHAR(500),
    marca               VARCHAR(60),
    proveedor           VARCHAR(120),
    unidad_medida       VARCHAR(20)    NOT NULL,
    imagen_url          VARCHAR(500),
    moneda              CHAR(3)        NOT NULL CHECK (moneda IN ('PEN', 'USD')),
    precio_contado      NUMERIC(12,2)  NOT NULL CHECK (precio_contado > 0),
    precio_lista        NUMERIC(12,2)  NOT NULL,
    permite_pago_unico  BOOLEAN        NOT NULL DEFAULT true,
    permite_cuotas      BOOLEAN        NOT NULL DEFAULT false,
    activo              BOOLEAN        NOT NULL DEFAULT true,
    CONSTRAINT fk_producto_tienda FOREIGN KEY (tienda_id) REFERENCES tienda (id),
    CHECK (precio_lista >= precio_contado),
    CHECK (permite_pago_unico OR permite_cuotas)
);

CREATE TABLE cliente (
    id                     BIGSERIAL      PRIMARY KEY,
    tienda_id              BIGINT         NOT NULL,
    nombres                VARCHAR(80)    NOT NULL,
    apellidos              VARCHAR(80)    NOT NULL,
    tipo_documento         VARCHAR(5)     NOT NULL CHECK (tipo_documento IN ('DNI', 'CE', 'RUC')),
    numero_documento       VARCHAR(12)    NOT NULL,
    telefono               VARCHAR(15),
    email                  VARCHAR(120),
    direccion              VARCHAR(200),
    moneda                 CHAR(3)        NOT NULL CHECK (moneda IN ('PEN', 'USD')),
    limite_credito         NUMERIC(12,2)  NOT NULL CHECK (limite_credito > 0),
    max_meses              SMALLINT       NOT NULL CHECK (max_meses BETWEEN 1 AND 36),
    dia_corte              SMALLINT       NOT NULL CHECK (dia_corte BETWEEN 1 AND 28),
    dia_pago               SMALLINT       NOT NULL CHECK (dia_pago BETWEEN 1 AND 28),
    tasa_compensatoria_id  BIGINT         NOT NULL,
    tasa_moratoria_id      BIGINT         NOT NULL,
    token_portal_hash      VARCHAR(255),
    estado                 VARCHAR(10)    NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'BAJA')),
    fecha_alta             TIMESTAMPTZ    NOT NULL DEFAULT now(),
    CONSTRAINT fk_cliente_tienda FOREIGN KEY (tienda_id) REFERENCES tienda (id),
    CONSTRAINT fk_cliente_tasa_comp FOREIGN KEY (tasa_compensatoria_id) REFERENCES tasa (id),
    CONSTRAINT fk_cliente_tasa_mora FOREIGN KEY (tasa_moratoria_id) REFERENCES tasa (id),
    CONSTRAINT uq_cliente_documento UNIQUE (tienda_id, numero_documento)
);

CREATE TABLE estado_cuenta (
    id                  BIGSERIAL      PRIMARY KEY,
    cliente_id          BIGINT         NOT NULL,
    periodo_desde       DATE           NOT NULL,
    fecha_corte         DATE           NOT NULL,
    fecha_pago          DATE           NOT NULL,
    moneda              CHAR(3)        NOT NULL,
    tasa_compensatoria_id  BIGINT      NOT NULL,
    tasa_moratoria_id   BIGINT         NOT NULL,
    total_capital       NUMERIC(12,2)  NOT NULL,
    total_interes       NUMERIC(12,2)  NOT NULL,
    total_a_pagar       NUMERIC(12,2)  NOT NULL,
    limite_credito      NUMERIC(12,2)  NOT NULL,
    credito_usado       NUMERIC(12,2)  NOT NULL,
    credito_disponible  NUMERIC(12,2)  NOT NULL,
    estado              VARCHAR(10)    NOT NULL DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'PAGADO')),
    generado_en         TIMESTAMPTZ    NOT NULL DEFAULT now(),
    CONSTRAINT fk_ec_cliente FOREIGN KEY (cliente_id) REFERENCES cliente (id),
    CONSTRAINT fk_ec_tasa_comp FOREIGN KEY (tasa_compensatoria_id) REFERENCES tasa (id),
    CONSTRAINT fk_ec_tasa_mora FOREIGN KEY (tasa_moratoria_id) REFERENCES tasa (id),
    CHECK (total_a_pagar > 0 OR estado = 'PAGADO'),
    CONSTRAINT uq_ec_cliente_corte UNIQUE (cliente_id, fecha_corte)
);

CREATE TABLE venta (
    id                     BIGSERIAL      PRIMARY KEY,
    cliente_id             BIGINT         NOT NULL,
    fecha_hora             TIMESTAMPTZ    NOT NULL DEFAULT now(),
    modalidad              VARCHAR(12)    NOT NULL CHECK (modalidad IN ('FIN_DE_MES', 'CUOTAS')),
    numero_cuotas          SMALLINT,
    moneda                 CHAR(3)        NOT NULL,
    tipo_cambio            NUMERIC(8,3),
    tasa_compensatoria_id  BIGINT         NOT NULL,
    tasa_moratoria_id      BIGINT         NOT NULL,
    fecha_corte            DATE           NOT NULL,
    fecha_pago             DATE           NOT NULL,
    capital                NUMERIC(12,2)  NOT NULL CHECK (capital > 0),
    dias                   SMALLINT       NOT NULL,
    tasa_periodo           NUMERIC(12,9)  NOT NULL,
    interes                NUMERIC(12,2)  NOT NULL,
    total                  NUMERIC(12,2)  NOT NULL,
    tem                    NUMERIC(12,9),
    estado                 VARCHAR(10)    NOT NULL DEFAULT 'VIGENTE' CHECK (estado IN ('VIGENTE', 'PAGADA', 'ANULADA')),
    registrado_por         BIGINT         NOT NULL,
    CONSTRAINT fk_venta_cliente FOREIGN KEY (cliente_id) REFERENCES cliente (id),
    CONSTRAINT fk_venta_tasa_comp FOREIGN KEY (tasa_compensatoria_id) REFERENCES tasa (id),
    CONSTRAINT fk_venta_tasa_mora FOREIGN KEY (tasa_moratoria_id) REFERENCES tasa (id),
    CONSTRAINT fk_venta_usuario FOREIGN KEY (registrado_por) REFERENCES usuario (id),
    CHECK ((modalidad = 'FIN_DE_MES' AND numero_cuotas IS NULL AND tem IS NULL)
        OR (modalidad = 'CUOTAS' AND numero_cuotas >= 1 AND tem IS NOT NULL))
);

-- El EC de una venta a fin de mes se identifica por (cliente_id, fecha_corte).
CREATE INDEX ix_venta_cliente_corte ON venta (cliente_id, fecha_corte);

CREATE TABLE venta_detalle (
    id               BIGSERIAL      PRIMARY KEY,
    venta_id         BIGINT         NOT NULL,
    producto_id      BIGINT         NOT NULL,
    descripcion      VARCHAR(120)   NOT NULL,
    cantidad         NUMERIC(10,3)  NOT NULL CHECK (cantidad > 0),
    precio_lista     NUMERIC(12,2)  NOT NULL,
    moneda_producto  CHAR(3)        NOT NULL,
    subtotal         NUMERIC(12,2)  NOT NULL,
    CONSTRAINT fk_detalle_venta FOREIGN KEY (venta_id) REFERENCES venta (id),
    CONSTRAINT fk_detalle_producto FOREIGN KEY (producto_id) REFERENCES producto (id)
);

CREATE TABLE cuota (
    id                 BIGSERIAL      PRIMARY KEY,
    venta_id           BIGINT         NOT NULL,
    numero             SMALLINT       NOT NULL,
    fecha_corte        DATE           NOT NULL,
    fecha_vencimiento  DATE           NOT NULL,
    saldo_inicial      NUMERIC(12,2)  NOT NULL,
    interes            NUMERIC(12,2)  NOT NULL,
    amortizacion       NUMERIC(12,2)  NOT NULL,
    monto              NUMERIC(12,2)  NOT NULL,
    saldo_final        NUMERIC(12,2)  NOT NULL,
    libera_linea       NUMERIC(12,2)  NOT NULL,
    estado             VARCHAR(10)    NOT NULL DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'PAGADA')),
    CONSTRAINT fk_cuota_venta FOREIGN KEY (venta_id) REFERENCES venta (id),
    CONSTRAINT uq_cuota_numero UNIQUE (venta_id, numero)
);

CREATE TABLE pago (
    id                BIGSERIAL      PRIMARY KEY,
    fecha_pago        DATE           NOT NULL,
    medio             VARCHAR(15)    NOT NULL CHECK (medio IN ('EFECTIVO', 'YAPE', 'PLIN', 'TRANSFERENCIA', 'OTRO')),
    total_mora        NUMERIC(12,2)  NOT NULL,
    total_interes     NUMERIC(12,2)  NOT NULL,
    total_capital     NUMERIC(12,2)  NOT NULL,
    total             NUMERIC(12,2)  NOT NULL,
    linea_liberada    NUMERIC(12,2)  NOT NULL,
    estado            VARCHAR(10)    NOT NULL DEFAULT 'VALIDO' CHECK (estado IN ('VALIDO', 'ANULADO')),
    motivo_anulacion  VARCHAR(200),
    anulado_en        TIMESTAMPTZ,
    registrado_por    BIGINT         NOT NULL,
    registrado_en     TIMESTAMPTZ    NOT NULL DEFAULT now(),
    CONSTRAINT fk_pago_usuario FOREIGN KEY (registrado_por) REFERENCES usuario (id),
    CHECK (total = total_mora + total_interes + total_capital),
    CHECK (estado = 'VALIDO' OR motivo_anulacion IS NOT NULL)
);

CREATE TABLE pago_detalle (
    id                          BIGSERIAL      PRIMARY KEY,
    pago_id                     BIGINT         NOT NULL,
    estado_cuenta_id            BIGINT         NOT NULL,
    exigible                    NUMERIC(12,2)  NOT NULL,
    dias_mora                   SMALLINT       NOT NULL CHECK (dias_mora >= 0),
    tasa_compensatoria_mora     NUMERIC(12,9)  NOT NULL,
    interes_compensatorio_mora  NUMERIC(12,2)  NOT NULL,
    tasa_moratoria              NUMERIC(12,9)  NOT NULL,
    interes_moratorio           NUMERIC(12,2)  NOT NULL,
    interes                     NUMERIC(12,2)  NOT NULL,
    capital                     NUMERIC(12,2)  NOT NULL,
    total                       NUMERIC(12,2)  NOT NULL,
    CONSTRAINT fk_pdet_pago FOREIGN KEY (pago_id) REFERENCES pago (id),
    CONSTRAINT fk_pdet_ec FOREIGN KEY (estado_cuenta_id) REFERENCES estado_cuenta (id)
);

CREATE TABLE auditoria (
    id          BIGSERIAL    PRIMARY KEY,
    usuario_id  BIGINT,
    tienda_id   BIGINT,
    accion      VARCHAR(40)  NOT NULL,
    entidad     VARCHAR(30)  NOT NULL,
    entidad_id  BIGINT,
    datos       JSONB,
    ip          VARCHAR(45),
    fecha_hora  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT fk_auditoria_usuario FOREIGN KEY (usuario_id) REFERENCES usuario (id),
    CONSTRAINT fk_auditoria_tienda FOREIGN KEY (tienda_id) REFERENCES tienda (id)
);

CREATE TABLE tipo_cambio (
    fecha   DATE          PRIMARY KEY,
    compra  NUMERIC(8,3)  NOT NULL,
    venta   NUMERIC(8,3)  NOT NULL,
    fuente  VARCHAR(40)   NOT NULL
);
