-- =====================================================================
-- Proyecto final SGI, ciclo 02/2026
-- Tiendas minoristas y Centro de Distribución (CD)
-- Motor: MySQL 8 (XAMPP / MariaDB y Clever Cloud)
-- Basado en el ER corregido (tablas venta y movimiento_inventario)
-- =====================================================================
-- En Clever Cloud NO ejecutar CREATE DATABASE ni USE: se importa sobre
-- la base que asigna Clever Cloud. En XAMPP, descomentar las dos líneas.
-- CREATE DATABASE IF NOT EXISTS bd_tiendas CHARACTER SET utf8mb4;
-- USE bd_tiendas;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS movimiento_inventario, detalle_compra, compra, detalle_venta, venta,
  producto_proveedor, proveedor, lote, inventario, producto, unidad_medida, categoria,
  usuario, tienda, rol;
SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------------------
-- Catálogos y seguridad
-- ---------------------------------------------------------------------
CREATE TABLE rol (
  id_rol INT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(50) NOT NULL,
  PRIMARY KEY (id_rol),
  UNIQUE KEY uq_rol_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE tienda (
  id_tienda INT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(100) NOT NULL,
  direccion VARCHAR(255),
  tipo ENUM('TIENDA','CD') NOT NULL DEFAULT 'TIENDA',
  estado BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (id_tienda)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE usuario (
  id_usuario INT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(100) NOT NULL,
  usuario VARCHAR(50) NOT NULL,
  contrasena_hash VARCHAR(255) NOT NULL,   -- SHA-256 en hexadecimal
  id_rol INT NOT NULL,
  id_tienda INT NOT NULL,
  PRIMARY KEY (id_usuario),
  UNIQUE KEY uq_usuario_usuario (usuario),
  CONSTRAINT fk_usuario_rol FOREIGN KEY (id_rol) REFERENCES rol (id_rol),
  CONSTRAINT fk_usuario_tienda FOREIGN KEY (id_tienda) REFERENCES tienda (id_tienda)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE categoria (
  id_categoria INT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(100) NOT NULL,
  PRIMARY KEY (id_categoria),
  UNIQUE KEY uq_categoria_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE unidad_medida (
  id_unidad INT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(50) NOT NULL,
  abreviatura VARCHAR(10) NOT NULL,
  PRIMARY KEY (id_unidad),
  UNIQUE KEY uq_unidad_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- Productos e inventario
-- ---------------------------------------------------------------------
CREATE TABLE producto (
  id_producto INT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(150) NOT NULL,
  id_categoria INT NOT NULL,
  id_unidad INT NOT NULL,
  requiere_vencimiento BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (id_producto),
  CONSTRAINT fk_producto_categoria FOREIGN KEY (id_categoria) REFERENCES categoria (id_categoria),
  CONSTRAINT fk_producto_unidad FOREIGN KEY (id_unidad) REFERENCES unidad_medida (id_unidad)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Existencia actual por tienda y producto
CREATE TABLE inventario (
  id_tienda INT NOT NULL,
  id_producto INT NOT NULL,
  existencia DECIMAL(12,2) NOT NULL DEFAULT 0,
  stock_minimo DECIMAL(12,2) NOT NULL DEFAULT 0,
  precio_venta DECIMAL(12,2),
  PRIMARY KEY (id_tienda, id_producto),
  CONSTRAINT fk_inventario_tienda FOREIGN KEY (id_tienda) REFERENCES tienda (id_tienda),
  CONSTRAINT fk_inventario_producto FOREIGN KEY (id_producto) REFERENCES producto (id_producto),
  CONSTRAINT ck_inventario_existencia CHECK (existencia >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE lote (
  id_lote INT NOT NULL AUTO_INCREMENT,
  id_tienda INT NOT NULL,
  id_producto INT NOT NULL,
  fecha_vencimiento DATE,
  cantidad_disponible DECIMAL(12,2) NOT NULL DEFAULT 0,
  PRIMARY KEY (id_lote),
  CONSTRAINT fk_lote_tienda FOREIGN KEY (id_tienda) REFERENCES tienda (id_tienda),
  CONSTRAINT fk_lote_producto FOREIGN KEY (id_producto) REFERENCES producto (id_producto)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- Proveedores (por tienda) y relación muchos a muchos con productos
-- ---------------------------------------------------------------------
CREATE TABLE proveedor (
  id_proveedor INT NOT NULL AUTO_INCREMENT,
  id_tienda INT NOT NULL,
  nombre VARCHAR(150) NOT NULL,
  dui_nit VARCHAR(30) NULL,                 -- opcional; MySQL permite varios NULL en UNIQUE
  telefono VARCHAR(30),
  PRIMARY KEY (id_proveedor),
  UNIQUE KEY uq_proveedor_dui_nit (dui_nit),
  CONSTRAINT fk_proveedor_tienda FOREIGN KEY (id_tienda) REFERENCES tienda (id_tienda)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE producto_proveedor (
  id_producto INT NOT NULL,
  id_proveedor INT NOT NULL,
  ultimo_precio DECIMAL(12,2),
  fecha_ultima_compra DATE,
  PRIMARY KEY (id_producto, id_proveedor),
  CONSTRAINT fk_pp_producto FOREIGN KEY (id_producto) REFERENCES producto (id_producto),
  CONSTRAINT fk_pp_proveedor FOREIGN KEY (id_proveedor) REFERENCES proveedor (id_proveedor)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- Ventas (incluye despachos del CD a tiendas)
-- ---------------------------------------------------------------------
CREATE TABLE venta (
  id_venta INT NOT NULL AUTO_INCREMENT,     -- único en todo el sistema
  id_tienda INT NOT NULL,
  id_tienda_destino INT NULL,               -- solo en despachos del CD
  id_usuario INT NOT NULL,
  tipo_venta ENUM('VENTA_CLIENTE','DESPACHO_CD') NOT NULL DEFAULT 'VENTA_CLIENTE',
  estado ENUM('EN_TRANSITO','RECIBIDO') NULL, -- solo en despachos del CD
  fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  fecha_envio DATETIME NULL,
  fecha_recepcion DATETIME NULL,
  total DECIMAL(12,2) NOT NULL DEFAULT 0,
  PRIMARY KEY (id_venta),
  CONSTRAINT fk_venta_tienda FOREIGN KEY (id_tienda) REFERENCES tienda (id_tienda),
  CONSTRAINT fk_venta_destino FOREIGN KEY (id_tienda_destino) REFERENCES tienda (id_tienda),
  CONSTRAINT fk_venta_usuario FOREIGN KEY (id_usuario) REFERENCES usuario (id_usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE detalle_venta (
  id_detalle_venta INT NOT NULL AUTO_INCREMENT,
  id_venta INT NOT NULL,
  id_producto INT NOT NULL,
  id_lote INT NULL,
  cantidad DECIMAL(12,2) NOT NULL,
  precio_unitario DECIMAL(12,2) NOT NULL,
  PRIMARY KEY (id_detalle_venta),
  CONSTRAINT fk_dv_venta FOREIGN KEY (id_venta) REFERENCES venta (id_venta),
  CONSTRAINT fk_dv_producto FOREIGN KEY (id_producto) REFERENCES producto (id_producto),
  CONSTRAINT fk_dv_lote FOREIGN KEY (id_lote) REFERENCES lote (id_lote),
  CONSTRAINT ck_dv_cantidad CHECK (cantidad > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- Compras
-- ---------------------------------------------------------------------
CREATE TABLE compra (
  id_compra INT NOT NULL AUTO_INCREMENT,
  id_tienda INT NOT NULL,
  id_proveedor INT NULL,                    -- nulo si viene del CD
  id_venta_origen INT NULL,                 -- nulo si es compra externa
  id_usuario INT NOT NULL,
  fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  total DECIMAL(12,2) NOT NULL DEFAULT 0,
  PRIMARY KEY (id_compra),
  CONSTRAINT fk_compra_tienda FOREIGN KEY (id_tienda) REFERENCES tienda (id_tienda),
  CONSTRAINT fk_compra_proveedor FOREIGN KEY (id_proveedor) REFERENCES proveedor (id_proveedor),
  CONSTRAINT fk_compra_venta FOREIGN KEY (id_venta_origen) REFERENCES venta (id_venta),
  CONSTRAINT fk_compra_usuario FOREIGN KEY (id_usuario) REFERENCES usuario (id_usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE detalle_compra (
  id_detalle_compra INT NOT NULL AUTO_INCREMENT,
  id_compra INT NOT NULL,
  id_producto INT NOT NULL,
  id_lote INT NULL,
  cantidad DECIMAL(12,2) NOT NULL,
  precio_compra DECIMAL(12,2) NOT NULL,
  precio_venta_sugerido DECIMAL(12,2),
  PRIMARY KEY (id_detalle_compra),
  CONSTRAINT fk_dc_compra FOREIGN KEY (id_compra) REFERENCES compra (id_compra),
  CONSTRAINT fk_dc_producto FOREIGN KEY (id_producto) REFERENCES producto (id_producto),
  CONSTRAINT fk_dc_lote FOREIGN KEY (id_lote) REFERENCES lote (id_lote),
  CONSTRAINT ck_dc_cantidad CHECK (cantidad > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- Kardex: historial de movimientos (trazabilidad)
-- ---------------------------------------------------------------------
CREATE TABLE movimiento_inventario (
  id_movimiento INT NOT NULL AUTO_INCREMENT,
  id_tienda INT NOT NULL,
  id_producto INT NOT NULL,
  id_lote INT NULL,
  id_usuario INT NOT NULL,
  id_detalle_compra INT NULL,
  id_detalle_venta INT NULL,
  tipo ENUM('COMPRA','VENTA','ENVIO','AJUSTE') NOT NULL,
  cantidad DECIMAL(12,2) NOT NULL,
  fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_movimiento),
  CONSTRAINT fk_mov_tienda FOREIGN KEY (id_tienda) REFERENCES tienda (id_tienda),
  CONSTRAINT fk_mov_producto FOREIGN KEY (id_producto) REFERENCES producto (id_producto),
  CONSTRAINT fk_mov_lote FOREIGN KEY (id_lote) REFERENCES lote (id_lote),
  CONSTRAINT fk_mov_usuario FOREIGN KEY (id_usuario) REFERENCES usuario (id_usuario),
  CONSTRAINT fk_mov_dc FOREIGN KEY (id_detalle_compra) REFERENCES detalle_compra (id_detalle_compra),
  CONSTRAINT fk_mov_dv FOREIGN KEY (id_detalle_venta) REFERENCES detalle_venta (id_detalle_venta)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================================
-- DATOS DE PRUEBA
-- Contraseñas de prueba (cambiarlas antes de la defensa si se desea):
--   admin / admin123      encargado1 / tienda123      encargado_cd / cd123
-- =====================================================================
INSERT INTO rol (nombre) VALUES ('Administrador'), ('Encargado'), ('Vendedor');

INSERT INTO tienda (nombre, direccion, tipo) VALUES
  ('Centro de Distribución', 'San Salvador', 'CD'),
  ('Tienda Santa Ana', 'Santa Ana', 'TIENDA'),
  ('Tienda Sonsonate', 'Sonsonate', 'TIENDA');

INSERT INTO usuario (nombre, usuario, contrasena_hash, id_rol, id_tienda) VALUES
  ('Administrador general', 'admin',        SHA2('admin123', 256),  1, 1),
  ('Encargado CD',          'encargado_cd', SHA2('cd123', 256),     2, 1),
  ('Encargada Santa Ana',   'encargado1',   SHA2('tienda123', 256), 2, 2),
  ('Vendedora Sonsonate',   'vendedor1',    SHA2('tienda123', 256), 3, 3);

INSERT INTO categoria (nombre) VALUES ('Granos básicos'), ('Lácteos'), ('Bebidas'), ('Limpieza');
INSERT INTO unidad_medida (nombre, abreviatura) VALUES ('Unidad', 'u'), ('Libra', 'lb'), ('Litro', 'l');

INSERT INTO producto (nombre, id_categoria, id_unidad, requiere_vencimiento) VALUES
  ('Frijol rojo', 1, 2, FALSE),
  ('Arroz', 1, 2, FALSE),
  ('Leche entera', 2, 3, TRUE),
  ('Jugo de naranja', 3, 3, TRUE),
  ('Detergente', 4, 1, FALSE);

INSERT INTO inventario (id_tienda, id_producto, existencia, stock_minimo, precio_venta) VALUES
  (1, 1, 500, 100, 0.90), (1, 2, 400, 100, 0.70), (1, 3, 200, 50, 1.20),
  (2, 1,  40,  20, 1.00), (2, 3,  15,  20, 1.35),
  (3, 2,  60,  30, 0.80);

INSERT INTO lote (id_tienda, id_producto, fecha_vencimiento, cantidad_disponible) VALUES
  (1, 3, '2026-12-15', 200),
  (2, 3, '2026-11-30', 15);

INSERT INTO proveedor (id_tienda, nombre, dui_nit, telefono) VALUES
  (1, 'Distribuidora Occidente', '0614-010190-101-1', '2222-0001'),
  (2, 'Lácteos del Valle', NULL, '2444-0002');

INSERT INTO producto_proveedor (id_producto, id_proveedor, ultimo_precio, fecha_ultima_compra) VALUES
  (1, 1, 0.70, '2026-11-01'),
  (2, 1, 0.55, '2026-11-01'),
  (3, 2, 0.95, '2026-11-05');
