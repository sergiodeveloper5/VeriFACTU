# Nuevas Funcionalidades Implementadas - Veri*FACTU Odoo 18

## 🚀 Funcionalidades Añadidas

### 1. **Códigos QR EPC**
- ✅ Generación automática de códigos QR EPC para facturas
- ✅ Integración con datos de Veri*FACTU
- ✅ Visualización en facturas y reportes
- ✅ Cumplimiento con estándares ISO 20022

### 2. **Plantillas de Factura Mejoradas**
- ✅ Plantilla personalizada con referencia "Veri*factu"
- ✅ Integración visual del código QR en facturas
- ✅ Información de hash y verificación
- ✅ Diseño moderno y profesional

### 3. **Sistema de Colas de Envío**
- ✅ Cola automática para envío a AEAT
- ✅ Procesamiento asíncrono con reintentos
- ✅ Gestión de errores y estados
- ✅ Trabajos cron para procesamiento automático

### 4. **Actualización a Odoo 18**
- ✅ Manifest actualizado a versión 18.0.1.0.0
- ✅ Dependencias actualizadas (qrcode, Pillow, queue_job)
- ✅ Compatibilidad con nuevas APIs de Odoo 18

## 📋 Nuevos Campos y Modelos

### Modelo `account.move` (Facturas)
- `verifactu_qr_code`: Código QR EPC en formato base64
- `verifactu_qr_string`: Datos utilizados para generar el QR
- `verifactu_reference`: Referencia única Veri*FACTU
- `verifactu_hash`: Hash SHA256 calculado

### Nuevo Modelo `verifactu.queue`
- Gestión de cola de envío a AEAT
- Estados: pendiente, procesando, enviado, error, cancelado
- Sistema de reintentos automáticos
- Priorización de envíos

## 🔧 Configuración

### Dependencias Python Requeridas
```bash
pip install qrcode[pil] Pillow zeep requests
```

### Configuración de Empresa
1. Ir a **Configuración > Compañías**
2. Activar **Veri*FACTU habilitado**
3. Configurar **Modo de prueba** si es necesario

### Configuración de Posición Fiscal
1. Ir a **Contabilidad > Configuración > Posiciones Fiscales**
2. Activar **Veri*FACTU habilitado** en las posiciones relevantes

## 📊 Uso del Sistema

### Envío Manual
1. Abrir una factura validada
2. Ir a la pestaña **Veri*FACTU**
3. Hacer clic en **Enviar a Veri*FACTU**
4. La factura se añade a la cola de procesamiento

### Envío Automático
- Las facturas se envían automáticamente al validarlas
- Solo si Veri*FACTU está habilitado en empresa y posición fiscal
- Procesamiento cada 5 minutos via cron

### Monitoreo de Cola
1. Ir a **Contabilidad > AEAT > Cola Veri*FACTU**
2. Ver estado de envíos: pendiente, procesando, enviado, error
3. Reintentar envíos fallidos si es necesario

## 🎨 Características Visuales

### Código QR en Facturas
- Se muestra automáticamente en facturas con Veri*FACTU
- Tamaño optimizado (200x200px)
- Información de verificación incluida

### Estilos CSS Personalizados
- Colores distintivos para estados Veri*FACTU
- Diseño coherente con interfaz Odoo
- Responsive y accesible

## 🔄 Trabajos Automáticos (Cron)

### Procesamiento de Cola
- **Frecuencia**: Cada 5 minutos
- **Función**: Procesa elementos pendientes en cola
- **Límite**: 10 elementos por ejecución

### Limpieza de Cola
- **Frecuencia**: Diaria
- **Función**: Elimina registros antiguos (>30 días)
- **Estados**: Enviados, errores, cancelados

## 🛡️ Seguridad y Permisos

### Grupos de Acceso
- **Usuarios Contabilidad**: Solo lectura de cola
- **Facturación**: Lectura, escritura y creación
- **Gestores Contabilidad**: Acceso completo

## 🔍 Funcionalidades Técnicas

### Generación de Hash
- Algoritmo SHA256
- Incluye datos de emisor, receptor, factura
- Formato estándar Veri*FACTU

### Código QR EPC
- Formato ISO 20022
- Incluye información bancaria y de pago
- Referencia a hash Veri*FACTU

### Sistema de Reintentos
- Máximo 3 intentos por defecto
- Delay incremental (5, 10, 15 minutos)
- Gestión automática de errores

## 📈 Mejoras de Rendimiento

- Procesamiento asíncrono via colas
- Generación de QR optimizada
- Limpieza automática de datos antiguos
- Índices de base de datos optimizados

## 🔮 Próximas Mejoras

- [ ] Conexión WSDL real con AEAT
- [ ] Validación avanzada de documentos
- [ ] Dashboard de estadísticas
- [ ] Exportación de reportes
- [ ] Integración con firma digital

---

**Versión**: 18.0.1.0.0  
**Fecha**: 2024  
**Compatibilidad**: Odoo 18.0+  
**Licencia**: AGPL-3.0